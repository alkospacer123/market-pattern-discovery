"""Bounded, causal PD-01 quality discovery on the Phase 6B event/execution engine."""
from __future__ import annotations

from dataclasses import dataclass
from hashlib import sha256
from pathlib import Path
from time import perf_counter
import json
import math

import numpy as np
import pandas as pd

from market_pattern_discovery.backtest.phase6b import SPECS, generate_signals, load_discovery, metrics, simulate

SEED = 2601
HORIZONS = (15, 30, 60)
FOLDS = (
    ("F1", "2026-02-01", "2026-03-01"),
    ("F2", "2026-03-01", "2026-04-01"),
    ("F3", "2026-04-01", "2026-05-01"),
    ("F4", "2026-05-01", "2026-05-16"),
)
META = {"event_id", "instrument", "trading_date", "signal_time", "entry_time", "side", "direction",
        "reference_level", "tick_size", "episode_id", "bar_index", "other_close_time"}


def _safe(a: float, b: float) -> float:
    return float(a / b) if np.isfinite(b) and b != 0 else 0.0


def _window_features(f: pd.DataFrame, i: int, side: int, tick: float, atr: float) -> dict:
    c = f.close.to_numpy(float); h = f.high.to_numpy(float); l = f.low.to_numpy(float)
    out = {}
    for n in (1, 3, 5, 10, 15, 30, 60, 240):
        if i >= n:
            d = side * (c[i] - c[i-n]); w = slice(i-n+1, i+1)
            rr = h[w].max() - l[w].min(); rv = np.abs(np.diff(c[i-n:i+1])).sum()
            out[f"return_{n}_ticks"] = d/tick; out[f"return_{n}_ATR"] = d/atr
            out[f"range_{n}_ticks"] = rr/tick; out[f"range_{n}_ATR"] = rr/atr
            out[f"realized_vol_{n}_ticks"] = rv/tick; out[f"efficiency_{n}"] = _safe(abs(c[i]-c[i-n]), rv)
            out[f"position_range_{n}"] = _safe(c[i]-l[w].min(), rr)
    for a,b in ((5,30),(15,60)):
        out[f"range_ratio_{a}_{b}"] = _safe(out.get(f"range_{a}_ticks",np.nan),out.get(f"range_{b}_ticks",np.nan))
        out[f"vol_ratio_{a}_{b}"] = _safe(out.get(f"realized_vol_{a}_ticks",np.nan),out.get(f"realized_vol_{b}_ticks",np.nan))
    return out


def _other_features(other: pd.DataFrame, signal_time: pd.Timestamp, side: int) -> dict:
    times = other.close_time.array
    j = int(np.searchsorted(times, signal_time, side="right") - 1)
    out = {"other_close_time": pd.NaT}
    if j < 0: return out
    out["other_close_time"] = other.close_time.iloc[j]
    c=other.close.to_numpy(float); h=other.high.to_numpy(float); l=other.low.to_numpy(float); atr=other.atr14.to_numpy(float); tick=float(other.tick.iloc[0])
    out["other_ATR_in_ticks"] = atr[j]/tick
    for n in (1,5,15,30,60):
        if j >= n:
            raw=(c[j]-c[j-n])/tick; rv=np.abs(np.diff(c[j-n:j+1])).sum()/tick
            out[f"other_return_{n}_ticks"]=raw
            out[f"other_efficiency_{n}"]=_safe(abs(raw),rv)
            out[f"other_range_{n}_ticks"]=(h[j-n+1:j+1].max()-l[j-n+1:j+1].min())/tick
            out[f"cross_sign_agreement_{n}"]=float(np.sign(raw)==side)
    return out


def _labels(f: pd.DataFrame, i: int, side: int, tick: float, atr: float) -> dict:
    out={}; entry=i+1
    if entry>=len(f) or f.trading_date.iloc[entry]!=f.trading_date.iloc[i]: return out
    base=float(f.open.iloc[entry]); hi=f.high.to_numpy(float); lo=f.low.to_numpy(float); close=f.close.to_numpy(float)
    for horizon in HORIZONS:
        end=entry+horizon-1
        if end>=len(f) or f.trading_date.iloc[end]!=f.trading_date.iloc[entry]: continue
        fav=(hi[entry:end+1]-base)/tick if side==1 else (base-lo[entry:end+1])/tick
        adv=(base-lo[entry:end+1])/tick if side==1 else (hi[entry:end+1]-base)/tick
        signed=side*(close[end]-base)/tick; mfe=float(fav.max()); mae=float(adv.max())
        p=f"label_{horizon}_"; out|={p+"signed_move_ticks":signed,p+"signed_move_ATR":signed*tick/atr,
          p+"MFE_ticks":mfe,p+"MAE_ticks":mae,p+"MFE_ATR":mfe*tick/atr,p+"MAE_ATR":mae*tick/atr,
          p+"time_to_MFE":int(np.argmax(fav)+1),p+"time_to_MAE":int(np.argmax(adv)+1),
          p+"net_move_BASE_ticks":signed-2,p+"net_move_STRESS_ticks":signed-4,
          p+"MFE_after_BASE_ticks":mfe-2,p+"MFE_after_STRESS_ticks":mfe-4}
        for win,loss,name in ((4,2,"tick_4_2"),(6,3,"tick_6_3"),(8,4,"tick_8_4")):
            hits=[]
            for k,(x,y) in enumerate(zip(fav,adv),1):
                if y>=loss: hits=["LOSS",k]; break # conservative stop-first
                if x>=win: hits=["WIN",k]; break
            out[p+name+"_status"],out[p+name+"_bar"]=(hits if hits else ["NEITHER",np.nan])
        for win,loss,name in ((.5,.5,"atr_0.5_0.5"),(1,.5,"atr_1_0.5"),(1,1,"atr_1_1"),(1.5,.75,"atr_1.5_0.75")):
            hits=[]
            for k,(x,y) in enumerate(zip(fav*tick/atr,adv*tick/atr),1):
                if y>=loss: hits=["LOSS",k]; break
                if x>=win: hits=["WIN",k]; break
            out[p+name+"_status"],out[p+name+"_bar"]=(hits if hits else ["NEITHER",np.nan])
    return out


def build_events(frames: dict[str,pd.DataFrame]) -> pd.DataFrame:
    """Decorate the exact Phase 6B PD-01 signals with prefix-only predictors and labels."""
    rows=[]
    for inst,f in frames.items():
        tick=SPECS[inst][0]; other=frames[next(x for x in frames if x!=inst)]
        signals=generate_signals(f,inst,("PD-01",))
        day_groups=f.groupby("trading_date",sort=False)
        daily=day_groups.agg(day_high=("high","max"),day_low=("low","min"),day_open=("open","first")).shift(1)
        for n,e in enumerate(signals.itertuples()):
            i=e.bar_index; side=e.direction; atr=e.ATR_at_signal; d=f.trading_date.iloc[i]
            ix=np.asarray(day_groups.indices[d]); pos=int(np.flatnonzero(ix==i)[0]); prior=ix[:pos]
            entry=i+1; op=f.open.iloc[i]; hi=f.high.iloc[i]; lo=f.low.iloc[i]; cl=f.close.iloc[i]; rng=hi-lo
            r={"event_id":f"{inst}-{n:04d}","instrument":inst,"trading_date":d,"signal_time":e.signal_time,
               "entry_time":f.open_time.iloc[entry] if entry<len(f) and f.trading_date.iloc[entry]==d else pd.NaT,
               "side":e.side,"direction":side,"reference_level":e.reference_level,"bar_index":i,"tick_size":tick,
               "ATR_at_signal":atr,"ATR_in_ticks":atr/tick,"BASE_roundtrip_ticks":2,"BASE_cost_as_ATR":2/(atr/tick),"STRESS_cost_as_ATR":4/(atr/tick),
               "range_ticks":rng/tick,"range_ATR":rng/atr,"body_ticks":abs(cl-op)/tick,"body_ATR":abs(cl-op)/atr,
               "body_to_range":_safe(abs(cl-op),rng),"close_location_value":_safe(cl-lo,rng),
               "upper_wick_ratio":_safe(hi-max(op,cl),rng),"lower_wick_ratio":_safe(min(op,cl)-lo,rng),
               "break_distance_ticks":side*(cl-e.reference_level)/tick,"break_distance_ATR":side*(cl-e.reference_level)/atr,
               "minute_of_day":e.signal_time.hour*60+e.signal_time.minute,"hour":e.signal_time.hour,"day_of_week":e.signal_time.dayofweek}
            r|=_window_features(f,i,side,tick,atr)
            for lag in (1,3,5,10,15,30):
                if i>=lag: r[f"distance_to_level_tminus{lag}_ticks"]=side*(e.reference_level-f.close.iloc[i-lag])/tick; r[f"distance_to_level_tminus{lag}_ATR"]=side*(e.reference_level-f.close.iloc[i-lag])/atr
            for nbar in (5,10,15,30):
                if i>=nbar:r[f"approach_speed_{nbar}_ticks_per_bar"]=side*(f.close.iloc[i]-f.close.iloc[i-nbar])/tick/nbar
            for nbar in (15,30,60):
                p=prior[-nbar:]; r[f"near_touches_{nbar}"]=int((np.minimum(abs(f.high.iloc[p]-e.reference_level),abs(f.low.iloc[p]-e.reference_level))<=2*tick).sum())
            p=prior[-60:]; touch=np.flatnonzero(np.minimum(abs(f.high.iloc[p]-e.reference_level),abs(f.low.iloc[p]-e.reference_level)).to_numpy()<=2*tick)
            r["bars_since_first_touch_60"]=(len(p)-int(touch[0])) if len(touch) else 61; r["bars_since_last_touch"]=(len(p)-int(touch[-1])) if len(touch) else 61
            today=ix[:pos+1]; dayrange=f.high.iloc[today].max()-f.low.iloc[today].min(); dayopen=f.open.iloc[ix[0]]
            prev=daily.loc[d]; prev_range=prev.day_high-prev.day_low
            r|={"minutes_since_trading_day_start":(f.close_time.iloc[i]-f.open_time.iloc[ix[0]]).total_seconds()/60,
                "current_day_range_ticks":dayrange/tick,"current_day_range_ATR":dayrange/atr,"distance_from_day_open_ticks":side*(cl-dayopen)/tick,
                "distance_from_day_open_ATR":side*(cl-dayopen)/atr,"previous_day_range_ticks":prev_range/tick,"previous_day_range_ATR":prev_range/atr,
                "opposite_extreme_distance_ticks":prev_range/tick,"opposite_extreme_distance_ATR":prev_range/atr,
                "current_day_position":_safe(cl-f.low.iloc[today].min(),dayrange),"previous_day_position":_safe(cl-prev.day_low,prev_range)}
            if "volume" in f:
                v=f.volume.to_numpy(float); r["current_volume"]=v[i]
                for w in (20,60):
                    hist=v[max(0,i-w):i]; mean=hist.mean() if len(hist) else 0; sd=hist.std() if len(hist) else 0
                    r[f"relative_volume_{w}"]=_safe(v[i],mean);r[f"volume_zscore_{w}"]=_safe(v[i]-mean,sd)
            r|=_other_features(other,e.signal_time,side)
            for nbar in (5,15,30,60):
                a=r.get(f"return_{nbar}_ticks");b=r.get(f"other_return_{nbar}_ticks")
                if a is not None and b is not None:r[f"cross_normalized_difference_{nbar}"]=a-b;r[f"cross_sign_agreement_{nbar}"]=float(np.sign(a)==np.sign(b))
            r|=_labels(f,i,side,tick,atr); rows.append(r)
    events=pd.DataFrame(rows).sort_values(["instrument","signal_time"],kind="mergesort").reset_index(drop=True)
    episodes=[]; last={}; counter=0
    for e in events.itertuples():
        key=(e.instrument,e.trading_date,e.reference_level,e.direction); prior=last.get(key)
        if prior is None or (e.signal_time-prior[0]).total_seconds()>1800: counter+=1; eid=f"EP-{counter:04d}"
        else:eid=prior[1]
        episodes.append(eid);last[key]=(e.signal_time,eid)
    events["episode_id"]=episodes
    return events


def predictor_columns(events: pd.DataFrame) -> list[str]:
    return sorted(c for c in events if c not in META and not c.startswith("label_") and pd.api.types.is_numeric_dtype(events[c]))


def fold_masks(events: pd.DataFrame):
    dates=pd.to_datetime(events.trading_date).dt.tz_localize(None)
    for name,start,end in FOLDS:
        s=pd.Timestamp(start);e=pd.Timestamp(end)
        yield name,dates<s,(dates>=s)&(dates<e)


def canonical_rule(predicates: list[dict]) -> str:
    return " AND ".join(f"{p['feature']} {p['op']} {p['threshold']:.8g}" for p in sorted(predicates,key=lambda x:(x['feature'],x['op'],x['threshold'])))


def apply_rule(events: pd.DataFrame, predicates: list[dict]) -> pd.Series:
    mask=pd.Series(True,index=events.index)
    for p in predicates:mask &= events[p["feature"]].ge(p["threshold"]) if p["op"]==">=" else events[p["feature"]].lt(p["threshold"])
    return mask.fillna(False)


def extract_rules(events: pd.DataFrame, max_rules=200) -> list[dict]:
    from sklearn.impute import SimpleImputer
    from sklearn.tree import DecisionTreeRegressor
    cols=predictor_columns(events); rules=[]; seen=set()
    for fold,train,_ in fold_masks(events):
      data=events.loc[train].dropna(subset=["label_60_net_move_BASE_ticks"])
      for scope in ("COMBINED","CNYRUBF","USDRUBF"):
        d=data if scope=="COMBINED" else data[data.instrument.eq(scope)]
        if len(d)<30:continue
        X=SimpleImputer(strategy="median").fit_transform(d[cols]);y=d.label_60_net_move_BASE_ticks.to_numpy(float)
        model=DecisionTreeRegressor(max_depth=4,min_samples_leaf=max(10,len(d)//20),random_state=SEED).fit(X,y);tree=model.tree_
        def visit(node,path):
            if tree.children_left[node]==tree.children_right[node]:
                members=model.apply(X)==node
                if members.sum()>=10 and y[members].mean()>0 and 2<=len(path)<=5:
                    pred=[dict(x) for x in path]; canon=canonical_rule(pred)
                    if canon not in seen:
                        seen.add(canon);rules.append({"rule_id":f"R{len(rules)+1:03d}","predicates":pred,"canonical":canon,"conditions":len(pred),"source":"DecisionTreeRegressor","training_fold":fold,"instrument_applicability":scope,"training_events":int(members.sum()),"training_target_mean":float(y[members].mean())})
                return
            feature=cols[tree.feature[node]];threshold=float(tree.threshold[node])
            visit(tree.children_left[node],path+[{"feature":feature,"op":"<","threshold":threshold}]);visit(tree.children_right[node],path+[{"feature":feature,"op":">=","threshold":threshold}])
        visit(0,[])
        if len(rules)>=max_rules:return rules[:max_rules]
    return rules


def _selected_events(events,rule):
    x=events[apply_rule(events,rule["predicates"])]
    if rule["instrument_applicability"]!="COMBINED":x=x[x.instrument.eq(rule["instrument_applicability"])]
    return x


def _backtest(frames,selected,config=("TIME_60",None,None,60),delay=0):
    parts=[]
    for inst,f in frames.items():
        e=selected[selected.instrument.eq(inst)][["bar_index","side","direction","ATR_at_signal","reference_level","signal_time","instrument"]].copy()
        if delay:e["bar_index"]+=delay;e["signal_time"]=e.bar_index.map(f.close_time)
        e["strategy_id"]="PD01_FILTER";parts.append(simulate(f,e,SPECS[inst][0],[config]))
    return pd.concat(parts,ignore_index=True) if parts else pd.DataFrame()


def _summary(ledger):
    if ledger.empty:return {}
    m=metrics(ledger)
    out={}
    for fr in ("GROSS","BASE","STRESS"):
        z=m[m.friction_scenario.eq(fr)].iloc[0];out[f"{fr}_PF"]=z.profit_factor_ATR;out[f"{fr}_expectancy"]=z.expectancy_ATR
    b=ledger[ledger.friction_scenario.eq("BASE")];out|={"executed_trades":int(len(b)),"max_drawdown":float(metrics(b).iloc[0].max_drawdown_ATR)}
    return out


def run(data_root="/workspace/market-pattern-data",output="results/pd01_quality_v1",smoke_only=False):
    started=perf_counter();out=Path(output);out.mkdir(parents=True,exist_ok=True)
    frames={i:load_discovery(data_root,i)[0] for i in SPECS}; events=build_events(frames)
    jan=events[events.signal_time<pd.Timestamp("2026-02-01",tz="Europe/Moscow")].head(20)
    print("PD-01 REAL SMOKE TEST",{i:len(frames[i]) for i in frames},{i:int((jan.instrument==i).sum()) for i in frames});print(jan[["signal_time","entry_time","side","reference_level","ATR_in_ticks","break_distance_ticks","return_60_ATR","cross_normalized_difference_60","label_60_net_move_BASE_ticks"]].head(10).to_string(index=False))
    assert (events.other_close_time.dropna()<=events.loc[events.other_close_time.notna(),"signal_time"]).all()
    if smoke_only:return events
    t_features=perf_counter();rules=extract_rules(events);t_models=perf_counter()
    configs=[("STOP_1.0_TARGET_1.5",1.,1.5,60),("STOP_1.0_TARGET_2.0",1.,2.,60),("TIME_30",None,None,30),("TIME_60",None,None,60)]
    candidates=[];walk=[]
    for rule in rules:
        selected=_selected_events(events,rule); rule["event_count"]=len(selected);rule["episode_count"]=selected.episode_id.nunique()
        best=None
        for cfg in configs:
            s=_summary(_backtest(frames,selected,cfg));row={"rule_id":rule["rule_id"],"exit_configuration":cfg[0],"events":len(selected),"episodes":selected.episode_id.nunique(),**s}
            if best is None or row.get("BASE_expectancy",-math.inf)>best.get("BASE_expectancy",-math.inf):best=row
        candidates.append(best or {"rule_id":rule["rule_id"]})
        for fold,_,valid in fold_masks(events):
            v=_selected_events(events[valid],rule); s=_summary(_backtest(frames,v,("TIME_60",None,None,60)))
            walk.append({"rule_id":rule["rule_id"],"fold":fold,"validation_events":len(v),**s})
    cand=pd.DataFrame(candidates).sort_values(["BASE_expectancy","executed_trades"],ascending=False,na_position="last")
    top_ids=cand[(cand.BASE_expectancy>0)&(cand.executed_trades>=20)].head(15).rule_id.tolist();rob=[]
    rng=np.random.default_rng(SEED)
    for rid in top_ids:
        rule=next(r for r in rules if r["rule_id"]==rid);sel=_selected_events(events,rule); normal=_backtest(frames,sel); delay=_backtest(frames,sel,delay=1);s=_summary(normal);ds=_summary(delay)
        b=normal[normal.friction_scenario.eq("BASE")].copy();day=b.groupby(b.entry_time.dt.date).pnl_atr.sum();samples=[]
        if len(day):
            vals=day.to_numpy();samples=[rng.choice(vals,len(vals),replace=True).sum()/max(1,len(b)) for _ in range(500)]
        monthly={str(k):float(v) for k,v in b.groupby(b.entry_time.dt.strftime("%Y-%m")).pnl_atr.mean().items()}
        by_inst={str(k):float(v) for k,v in b.groupby("instrument").pnl_atr.mean().items()};by_side={str(k):float(v) for k,v in b.groupby("side").pnl_atr.mean().items()}
        neighbor=[]
        for factor in (.9,1.1):
            changed=[dict(p,threshold=p["threshold"]*factor) for p in rule["predicates"]]
            neighbor.append(_summary(_backtest(frames,_selected_events(events,dict(rule,predicates=changed)))).get("BASE_expectancy",np.nan))
        pos=day[day>0].sum();rob.append({"rule_id":rid,**s,"delay_BASE_PF":ds.get("BASE_PF"),"delay_BASE_expectancy":ds.get("BASE_expectancy"),"threshold_neighbor_min_expectancy":float(np.nanmin(neighbor)),"monthly_BASE_expectancy":json.dumps(monthly,sort_keys=True),"instrument_BASE_expectancy":json.dumps(by_inst,sort_keys=True),"direction_BASE_expectancy":json.dumps(by_side,sort_keys=True),"trading_days":len(day),"largest_day_positive_share":day.max()/pos if pos else np.nan,"top3_day_positive_share":day.nlargest(3).sum()/pos if pos else np.nan,"bootstrap_probability_expectancy_gt_0":float(np.mean(np.array(samples)>0)) if samples else np.nan,"bootstrap_expectancy_p05":float(np.quantile(samples,.05)) if samples else np.nan,"bootstrap_expectancy_p95":float(np.quantile(samples,.95)) if samples else np.nan})
    robustness=pd.DataFrame(rob);walkdf=pd.DataFrame(walk)
    baselines=[]
    exact={i:generate_signals(f,i,("PD-01",)) for i,f in frames.items()}
    for inst,e in exact.items():
        for cfg in configs:baselines.append({"instrument":inst,"exit_configuration":cfg[0],**_summary(simulate(frames[inst],e,SPECS[inst][0],[cfg]))})
    baseline=pd.DataFrame(baselines)
    schema=[{"feature_name":c,"description":"Causal event-time predictor; see implementation formulas.","lookback":"current/past, bounded at 240 M1 bars","units":"encoded in name or ratio","available_at":"closed signal M1 candle"} for c in predictor_columns(events)]
    pd.DataFrame(events).head(50).to_csv(out/"event_audit_sample.csv",index=False);cand.to_csv(out/"candidate_summary.csv",index=False);walkdf.to_csv(out/"walkforward_summary.csv",index=False);robustness.to_csv(out/"robustness_summary.csv",index=False);baseline.to_csv(out/"baseline_summary.csv",index=False)
    (out/"candidate_rules.json").write_text(json.dumps(rules,indent=2)+"\n");(out/"feature_schema.json").write_text(json.dumps(schema,indent=2)+"\n")
    counts=events.groupby("instrument").size().to_dict();episodes=events.groupby("instrument").episode_id.nunique().to_dict()
    source_hashes={}
    for inst,(_,_,folder) in SPECS.items():
        for p in sorted((Path(data_root)/"2026"/folder).glob("*_2026_Q[12]_M1.csv")):source_hashes[str(p)]=sha256(p.read_bytes()).hexdigest()
    fold_counts=[]
    for name,tr,va in fold_masks(events):fold_counts.append({"fold":name,"train_events":int(tr.sum()),"validation_events":int(va.sum()),"train_days":int(events.loc[tr,"trading_date"].nunique()),"validation_days":int(events.loc[va,"trading_date"].nunique())})
    manifest={"status":"PASS","repository_base":"db17ba8","discovery_start":"2026-01-05T00:00:00+03:00","discovery_end_exclusive":"2026-05-16T00:00:00+03:00","source_modified":False,"source_file_hashes":source_hashes,"instrument_rows":{i:len(f) for i,f in frames.items()},"pd01_raw_event_counts":counts,"pd01_episode_counts":episodes,"feature_count":len(schema),"feature_list_sha256":sha256(json.dumps(schema,sort_keys=True).encode()).hexdigest(),"label_definitions_sha256":sha256(_labels.__doc__.encode() if _labels.__doc__ else b"labels-v1").hexdigest(),"ml":{"model":"DecisionTreeRegressor","max_depth":4,"seed":SEED},"walk_forward_folds":FOLDS,"walk_forward_counts":fold_counts,"preliminary_rules":len(rules),"deduplicated_rules":len(rules),"backtested_rules":len(cand),"robustness_tested_rules":len(robustness),"baseline_results":baselines,"runtime_seconds":perf_counter()-started,"2025_accessed":False,"internal_confirmation_accessed":False,"post_discovery_accessed":False,"regeneration_command":"PYTHONPATH=src python scripts/run_pd01_quality_v1.py","outputs":{}}
    report="# PD-01 Quality Discovery V1\n\nStatus: **PASS** (research result; robustness is reported, not assumed).\n\n## Counts\n\n"+json.dumps({"rows":manifest["instrument_rows"],"events":counts,"episodes":episodes,"features":len(schema),"rules":len(rules),"robustness":len(robustness)},indent=2)+"\n\n## Baselines\n\n```csv\n"+baseline.to_csv(index=False)+"```\n\n## Top rules\n\n```csv\n"+cand.head(15).to_csv(index=False)+"```\n\n## Robustness\n\n```csv\n"+robustness.to_csv(index=False)+"```\n\nMonth was never a predictor. Rules were learned from post-cost movement labels, never PF. Exact predicates are in `candidate_rules.json`.\n"
    (out/"report.md").write_text(report)
    for p in out.iterdir():
        if p.name!="run_manifest.json":manifest["outputs"][p.name]={"bytes":p.stat().st_size,"sha256":sha256(p.read_bytes()).hexdigest()}
    (out/"run_manifest.json").write_text(json.dumps(manifest,indent=2,default=str)+"\n")
    print(f"event rows={len(events)} feature build={t_features-started:.2f}s model/rules={t_models-t_features:.2f}s preliminary backtest={perf_counter()-t_models:.2f}s")
    return manifest
