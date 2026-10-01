"""Causal implementations for the Top-5 real-strategy benchmark.

All feature rows are stamped at their closed-bar availability time.  Strategy
selection is deliberately kept separate from evaluation by :func:`assert_oos`.
"""
from __future__ import annotations

from hashlib import sha256
from pathlib import Path
import json
from decimal import Decimal, ROUND_HALF_UP
import numpy as np
import pandas as pd

from market_pattern_discovery.backtest.phase6b import load_discovery
from market_pattern_discovery.backtest.phase6b import add_wilder_atr14
from market_pattern_discovery.features.core import canonical_trading_date
from market_pattern_discovery.data.finam import load_finam_window

DEV_END = pd.Timestamp("2026-03-01", tz="Europe/Moscow")
DEV_START = pd.Timestamp("2026-01-05", tz="Europe/Moscow")
VAL_A_END = pd.Timestamp("2026-05-01", tz="Europe/Moscow")
END = pd.Timestamp("2026-05-16", tz="Europe/Moscow")
TICKS = {"CNYRUBF": .001, "USDRUBF": .01}
ROUNDS = {"CNYRUBF": .05, "USDRUBF": .10}

MANDATORY_CONTRACT = {
    "families": {
        "STRUCTURAL": ["REJECTION", "SIMPLE_SWEEP", "COMPLEX_FALSE_BREAK", "BREAKOUT_RETEST", "GERCHIK_A_M5_PROXY"],
        "ORB": ["DIRECT", "BREAKOUT_RETEST", "FAILED_BREAKOUT_DIAGNOSTIC"],
        "TREND_PULLBACK": ["EMA20_50", "EMA20_100"],
        "PAIRS": ["DISTANCE", "OLS"],
        "BOLLINGER_RSI": ["REENTRY_2R", "REENTRY_FIXED_MID"],
    },
    "requirements": {"EH_EL": "REQUIRED", "MIRROR_LEVEL": "REQUIRED", "HISTORICAL_FLAG": "REQUIRED", "ROUND_NUMBER": "CONFLUENCE_ONLY"},
    "source_mappings": {
        "GERCHIK_SIMPLE_FALSE_BREAK": {"source_mapping": "SIMPLE_SWEEP", "source_fidelity": "ADAPTED_TO_M1_M5"},
        "GERCHIK_COMPLEX_FALSE_BREAK": {"source_mapping": "COMPLEX_FALSE_BREAK", "source_fidelity": "ADAPTED_TO_M1_M5"},
        "GERCHIK_BREAKOUT_RETEST": {"source_mapping": "BREAKOUT_RETEST", "source_fidelity": "ADAPTED_TO_M1_M5"},
        "GERCHIK_A_M5_PROXY": {"source_fidelity": "PROXY_NOT_EXACT_SOURCE_REPLICATION"},
    },
}

def validate_contract(contract):
    if "contract_version" in contract:
        keys={"periods","instruments","ticks","timeframes","friction","commission_model","execution","position_exclusivity","simultaneous_signal_policy","tick_rounding","families","parameter_grids","max_holding","pair_alignment","pair_exit_rules","selection_policy","validation_status_policy","source_fidelity","true_oos_policy","manual_audit_policy"}
        missing=keys-set(contract)
        if missing: raise ValueError(f"missing contract keys: {sorted(missing)}")
        expected_periods={"DEV":["2026-01-05T00:00:00+03:00","2026-03-01T00:00:00+03:00"],"VALIDATION_A":["2026-03-01T00:00:00+03:00","2026-05-01T00:00:00+03:00"],"VALIDATION_B":["2026-05-01T00:00:00+03:00","2026-05-16T00:00:00+03:00"]}
        if contract["periods"]!=expected_periods: raise ValueError("period boundary mutation")
        if contract["commission_model"]!="NOT_INCLUDED" or contract["tick_rounding"]!="ROUND_HALF_UP_NEAREST_TICK": raise ValueError("execution policy mutation")
        required={"STRUCTURAL":{"REJECTION","SIMPLE_SWEEP","COMPLEX_FALSE_BREAK","BREAKOUT_RETEST","GERCHIK_A_M5_PROXY"},"ORB":{"DIRECT","BREAKOUT_RETEST","FAILED_BREAKOUT_DIAGNOSTIC"},"TREND_PULLBACK":{"EMA20_50","EMA20_100"},"PAIRS":{"DISTANCE","OLS"},"BOLLINGER_RSI":{"REENTRY_2R","REENTRY_FIXED_MID"}}
        for family,subs in required.items():
            if set(contract["families"].get(family,[]))!=subs: raise ValueError(f"family semantic mutation: {family}")
        if contract["selection_policy"].get("minimum_base_trades")!=20 or contract["validation_status_policy"].get("insufficient_sample_below")!=10: raise ValueError("policy threshold mutation")
        if contract["manual_audit_policy"]!={"manual_audit_required":True,"minimum_per_family_where_available":5,"status":"MANUAL_AUDIT_PENDING"}: raise ValueError("manual audit policy mutation")
        if contract["source_fidelity"].get("GERCHIK_A_M5_PROXY",{}).get("source_fidelity")!="PROXY_NOT_EXACT_SOURCE_REPLICATION": raise ValueError("source fidelity mutation")
        return True
    for family, required in MANDATORY_CONTRACT["families"].items():
        if not set(required).issubset(contract.get("families", {}).get(family, [])):
            raise ValueError(f"incomplete strategy contract: {family}")
    if contract.get("requirements") != MANDATORY_CONTRACT["requirements"]: raise ValueError("incomplete requirements")
    for key,value in MANDATORY_CONTRACT["source_mappings"].items():
        if contract.get("source_mappings",{}).get(key)!=value: raise ValueError(f"incomplete source mapping: {key}")
    return True

def round_to_tick(price, tick):
    p,t=Decimal(str(price)),Decimal(str(tick))
    if not p.is_finite() or not t.is_finite() or t<=0: raise ValueError("finite price and positive finite tick required")
    return float((p/t).quantize(Decimal("1"),rounding=ROUND_HALF_UP)*t)

def load_dev(data_root, instrument):
    """Read only Q1 rows strictly before DEV_END; never opens Q2 or 2025."""
    folder="CNY" if instrument=="CNYRUBF" else "Si";path=Path(data_root)/"2026"/folder/f'{folder}_2026_Q1_M1.csv'
    f=load_finam_window(path,instrument,"M1",DEV_START,DEV_END).frame
    f["trading_date"]=canonical_trading_date(f.open_time);f=add_wilder_atr14(f);f["tick"]=TICKS[instrument]
    if f.empty or f.open_time.max()>=DEV_END or f.open_time.dt.year.ne(2026).any():raise ValueError("DEV-only boundary violation")
    return f.reset_index(drop=True)

def sample_tier(n): return "VERY_LOW" if n<20 else "LOW" if n<50 else "MODERATE" if n<100 else "BETTER"
def select_variant(frame):
    rank={"VERY_LOW":0,"LOW":1,"MODERATE":2,"BETTER":3};x=frame.copy();x["positive"]=x.base_expectancy.gt(0);x["sample_tier"]=x.trades.map(sample_tier);x["tier_rank"]=x.sample_tier.map(rank)
    return x.sort_values(["positive","tier_rank","base_pf","max_dd","complexity"],ascending=[False,False,False,True,True],kind="mergesort").iloc[0]


def causal_m5(m1: pd.DataFrame) -> pd.DataFrame:
    """Aggregate complete five-minute candles; labels are their close times."""
    if m1.open_time.duplicated().any(): raise ValueError("duplicate M1 timestamp")
    pieces=[]
    for _,day in m1.sort_values("open_time",kind="mergesort").groupby("trading_date",sort=False):
        out=day.set_index("open_time").resample("5min",label="right",closed="left",origin="start_day").agg(
            open=("open","first"),high=("high","max"),low=("low","min"),close=("close","last"),volume=("volume","sum"),count=("close","size"),trading_date=("trading_date","first"))
        pieces.append(out[out["count"].eq(5)])
    if not pieces:return pd.DataFrame()
    out = pd.concat(pieces).sort_index(kind="mergesort").drop(columns="count").reset_index(names="close_time")
    out["open_time"] = out.close_time - pd.Timedelta(minutes=5)
    return out


def indicators(m5: pd.DataFrame, fast=20, slow=50, bb_k=2., rsi_n=14) -> pd.DataFrame:
    x=m5.copy(); c=x.close.astype(float)
    x["ema_fast"]=c.ewm(span=fast,adjust=False).mean(); x["ema_slow"]=c.ewm(span=slow,adjust=False).mean()
    x["bb_mid"]=c.rolling(20).mean(); sd=c.rolling(20).std(ddof=0)
    x["bb_upper"]=x.bb_mid+bb_k*sd; x["bb_lower"]=x.bb_mid-bb_k*sd
    d=c.diff(); gain=d.clip(lower=0); loss=-d.clip(upper=0)
    ag=gain.ewm(alpha=1/rsi_n,adjust=False,min_periods=rsi_n).mean(); al=loss.ewm(alpha=1/rsi_n,adjust=False,min_periods=rsi_n).mean()
    x["rsi"]=100-100/(1+ag/al.replace(0,np.nan)); x.loc[(al.eq(0))&(ag.gt(0)),"rsi"]=100
    return x


def confirmed_pivots(m5: pd.DataFrame) -> pd.DataFrame:
    """Pivots are emitted at j+2, never at pivot bar j."""
    rows=[]; h=m5.high.to_numpy(); l=m5.low.to_numpy()
    for j in range(2,len(m5)-2):
        known=j+2
        if h[j]>h[j-2:j].max() and h[j]>=h[j+1:j+3].max(): rows.append({"side":"HIGH","pivot_index":j,"known_index":known,"pivot_time":m5.close_time.iloc[j],"known_time":m5.close_time.iloc[known],"price":h[j]})
        if l[j]<l[j-2:j].min() and l[j]<=l[j+1:j+3].min(): rows.append({"side":"LOW","pivot_index":j,"known_index":known,"pivot_time":m5.close_time.iloc[j],"known_time":m5.close_time.iloc[known],"price":l[j]})
    return pd.DataFrame(rows)


def structural_levels(m5: pd.DataFrame, instrument: str, tolerance_ticks=2, min_touches=2) -> pd.DataFrame:
    """Create immutable causal versions whenever a confirmed touch qualifies."""
    piv=confirmed_pivots(m5)
    if piv.empty:return pd.DataFrame()
    piv=piv.sort_values(["known_index","side"],kind="mergesort").reset_index(drop=True)
    tick=TICKS[instrument];tol=tolerance_ticks*tick;families=[];rows=[]
    dates=list(pd.unique(m5.trading_date)); date_rank={d:i for i,d in enumerate(dates)}
    for pid,p in piv.iterrows():
        pdate=m5.trading_date.iloc[int(p.pivot_index)]
        compatible=[f for f in families if date_rank[pdate]-f["last_date_rank"]<=5 and abs(p.price-f["anchor_price"])<=tol]
        if compatible:
            f=min(compatible,key=lambda x:(abs(p.price-x["anchor_price"]),x["id"]))
            if p.pivot_index-f["last_index"]<2: continue
        else:
            f={"id":len(families),"touches":[],"anchor_price":float(p.price),"last_index":-10,"last_date_rank":date_rank[pdate]};families.append(f)
        f["touches"].append({**p.to_dict(),"pivot_id":int(pid)});f["last_index"]=int(p.pivot_index);f["price"]=float(np.mean([q["price"] for q in f["touches"]]))
        f["last_date_rank"]=date_rank[pdate]
        highs=[q for q in f["touches"] if q["side"]=="HIGH"];lows=[q for q in f["touches"] if q["side"]=="LOW"]
        mirror=bool(highs and lows and len(f["touches"])>=min_touches); qualifying=mirror or len(highs)>=min_touches or len(lows)>=min_touches
        if not qualifying:continue
        version=1+sum(r["level_family_id"]==f'{instrument}-L{f["id"]}' for r in rows)
        typ="MIRROR" if mirror else "EH" if len(highs)>=min_touches else "EL";q=f["touches"];price=round_to_tick(float(np.median([z["price"] for z in q])),tick);valid=pd.Timestamp(p.known_time)
        rows.append({"level_family_id":f'{instrument}-L{f["id"]}',"level_snapshot_id":f'{instrument}-L{f["id"]}-V{version}',"snapshot_version":version,"instrument":instrument,"level_type":typ,"anchor_price":f["anchor_price"],"level_price":price,"valid_from":valid,"valid_trading_date":m5.trading_date.iloc[int(p.known_index)],"first_touch":q[0]["pivot_time"],"last_touch":q[-1]["pivot_time"],"touch_count":len(q),"touch_times":"|".join(str(z["pivot_time"]) for z in q),"tolerance_ticks":tolerance_ticks,"min_touches":min_touches,"round_confluence":abs(price-round_to_tick(price,ROUNDS[instrument]))<=tick+1e-12,"historical":pd.Timestamp(q[0]["pivot_time"]).date()<valid.date(),"mirror":mirror,"source_pivot_ids":"|".join(str(z["pivot_id"]) for z in q),"source_sides":"|".join(z["side"] for z in q),"known_index":int(p.known_index)})
    out=pd.DataFrame(rows)
    if not out.empty:
        # Compatibility aliases are read-only copies, never cluster state.
        out["level_id"]=out.level_snapshot_id;out["price"]=out.level_price;out["known_time"]=out.valid_from
    return out


def structural_signals(m5, levels, instrument, target_r=3.):
    """Causal per-snapshot/per-role interaction state machine."""
    rows=[];tick=TICKS[instrument]
    if levels.empty:return pd.DataFrame()
    levels=levels.copy();aliases={"level_family_id":"level_id","level_snapshot_id":"level_id","level_price":"price","valid_from":"known_time"}
    for new,old in aliases.items():
        if new not in levels and old in levels:levels[new]=levels[old]
    for col,value in {"snapshot_version":1,"historical":False,"mirror":False}.items():
        if col not in levels:levels[col]=value
    dates=list(pd.unique(m5.trading_date));rank={d:i for i,d in enumerate(dates)}
    ordered=levels.sort_values(["level_family_id","snapshot_version"],kind="mergesort").reset_index(drop=True)
    for n,L in ordered.iterrows():
        start=pd.Timestamp(L.valid_from);start_ix=int(m5.close_time.searchsorted(start,side="left"))
        if start_ix>=len(m5):continue
        start_rank=rank[m5.trading_date.iloc[start_ix]];next_time=ordered.loc[n+1,"valid_from"] if n+1<len(ordered) and ordered.loc[n+1,"level_family_id"]==L.level_family_id else None
        active=[i for i in range(start_ix,len(m5)) if rank[m5.trading_date.iloc[i]]-start_rank<5 and (next_time is None or m5.close_time.iloc[i]<next_time)]
        states={"support":{"armed":True,"pending":None},"resistance":{"armed":True,"pending":None}}
        lev=float(L.level_price);tol=float(L.tolerance_ticks)*tick
        for i in active:
            b=m5.iloc[i];prev=m5.iloc[i-1] if i else None
            if L.level_type=="EL":roles=["support"]
            elif L.level_type=="EH":roles=["resistance"]
            elif prev is None:roles=[]
            elif prev.close>lev+tol:roles=["support"]
            elif prev.close<lev-tol:roles=["resistance"]
            else:roles=[]
            for role in roles:
                st=states[role];support=role=="support";d=1 if support else -1
                clearly_away=b.close>lev+2*tol if support else b.close<lev-2*tol
                if clearly_away and st["pending"] is None:st["armed"]=True
                touch=b.low<=lev+tol if support else b.high>=lev-tol
                reclaim=b.close>lev if support else b.close<lev
                sweep=b.low<=lev-tick if support else b.high>=lev+tick
                if st["armed"] and touch and reclaim:
                    subtype="SIMPLE_SWEEP" if sweep else "REJECTION";stop=b.low-tick if support else b.high+tick
                    rows.append(_signal("STRUCTURAL",subtype,instrument,b.close_time,d,lev,stop,target_r,L.level_snapshot_id,level_type=L.level_type,level_family_id=L.level_family_id,snapshot_version=L.snapshot_version,historical=L.historical,mirror=L.mirror,round_confluence=getattr(L,"round_confluence",False)))
                    st["armed"]=False
                beyond=b.close<lev-tick if support else b.close>lev+tick
                if beyond and st["pending"] is None and st["armed"]:
                    st["pending"]={"i":i,"lo":b.low,"hi":b.high};st["armed"]=False
                pending=st["pending"]
                if pending is not None and i>pending["i"]:
                    pending["lo"]=min(pending["lo"],b.low);pending["hi"]=max(pending["hi"],b.high);age=i-pending["i"]
                    false_break=b.close>lev if support else b.close<lev
                    breakout_d=-1 if support else 1
                    retest=(b.high>=lev-tol and b.close<lev) if breakout_d==-1 else (b.low<=lev+tol and b.close>lev)
                    if 1<=age<=3 and false_break:
                        stop=pending["lo"]-tick if support else pending["hi"]+tick
                        rows.append(_signal("STRUCTURAL","COMPLEX_FALSE_BREAK",instrument,b.close_time,d,lev,stop,target_r,L.level_snapshot_id,level_type=L.level_type,level_family_id=L.level_family_id,snapshot_version=L.snapshot_version,historical=L.historical,mirror=L.mirror,round_confluence=getattr(L,"round_confluence",False)));st["pending"]=None
                    elif 1<=age<=5 and retest:
                        stop=b.high+tick if breakout_d==-1 else b.low-tick
                        rows.append(_signal("STRUCTURAL","BREAKOUT_RETEST",instrument,b.close_time,breakout_d,lev,stop,target_r,L.level_snapshot_id,level_type=L.level_type,level_family_id=L.level_family_id,snapshot_version=L.snapshot_version,historical=L.historical,mirror=L.mirror,round_confluence=getattr(L,"round_confluence",False),breakout_level_snapshot_id=L.level_snapshot_id));st["pending"]=None
                    elif age>5:st["pending"]=None
    return pd.DataFrame(rows)

def gerchik_a_signals(m5, levels, instrument):
    """Strict M1/M5-executable proxy; never an exact Gerchik replication."""
    x=indicators(m5,20,50);tick=TICKS[instrument];rows=[]
    for L in levels.itertuples():
        if L.level_type=="MIRROR":continue
        d=1 if L.level_type=="EL" else -1;level_tick=round(L.level_price/tick)*tick
        bsu=pd.Timestamp(L.first_touch); start=max(int(L.known_index),3)
        later=levels[(levels.level_family_id==L.level_family_id)&(levels.snapshot_version>L.snapshot_version)]
        finish=int(later.known_index.iloc[0]) if len(later) else len(x)
        for i in range(start,min(finish,len(x)-1)):
            b1=x.iloc[i];b2=x.iloc[i+1]
            trend=(d==1 and b2.ema_fast>b2.ema_slow and b2.ema_slow>x.ema_slow.iloc[i-2]) or (d==-1 and b2.ema_fast<b2.ema_slow and b2.ema_slow<x.ema_slow.iloc[i-2])
            hit=np.isclose(b1.low if d==1 else b1.high,level_tick,atol=tick/10); no_pierce=b2.low>=level_tick if d==1 else b2.high<=level_tick
            stop=level_tick-d*tick;risk=abs(b2.close-stop);luft=max(tick,.2*risk);near=level_tick<=b2.low<=level_tick+luft if d==1 else level_tick-luft<=b2.high<=level_tick
            if trend and hit and no_pierce and near:
                rows.append(_signal("STRUCTURAL","GERCHIK_A_M5_PROXY",instrument,b2.close_time,d,level_tick,stop,3.,L.level_snapshot_id,BSU_time=bsu,BPU1_time=b1.close_time,BPU2_time=b2.close_time,level_tick=level_tick,luft_price=luft,local_trend="LONG" if d==1 else "SHORT",source_fidelity="PROXY"));break
    return pd.DataFrame(rows)


def _signal(family,submodel,instrument,time,direction,ref,stop,target_r=None,level_id=None,**audit):
    variant=audit.pop("variant_id",f"{family}|{submodel}|{instrument}|target={target_r}")
    return {"family":family,"submodel":submodel,"instrument":instrument,"variant_id":variant,"signal_time":time,"direction":direction,"side":"LONG" if direction==1 else "SHORT","reference_level":ref,"stop_price":stop,"target_r":target_r,"level_id":level_id,**audit}


def orb_signals(m1,instrument,length=15,target_r=2.,retest=False,submodel=None,stop_mode="STOP_OPPOSITE_OR"):
    if stop_mode not in {"STOP_OPPOSITE_OR","STOP_MIDPOINT"}: raise ValueError(f"unknown stop_mode: {stop_mode}")
    submodel=submodel or ("BREAKOUT_RETEST" if retest else "DIRECT")
    if submodel=="FAILED_BREAKOUT": submodel="FAILED_BREAKOUT_DIAGNOSTIC" # V2 call compatibility only
    rows=[]; tick=TICKS[instrument]
    for date,g in m1.groupby("trading_date",sort=False):
        start=pd.Timestamp(date,tz="Europe/Moscow")+pd.Timedelta(hours=10); end=start+pd.Timedelta(minutes=length)
        opening=g[(g.open_time>=start)&(g.open_time<end)]
        if len(opening)!=length:continue
        oh,ol=opening.high.max(),opening.low.min(); later=g[g.open_time>=end]; broke=None;exc_lo=np.inf;exc_hi=-np.inf
        for b in later.itertuples():
            d=1 if b.close>oh+tick-1e-12 else -1 if b.close<ol-tick+1e-12 else 0
            if broke is None and d:
                broke=(b,d,oh if d==1 else ol);exc_lo=b.low;exc_hi=b.high
                if submodel=="DIRECT":
                    mid=round_to_tick((oh+ol)/2,tick);stop=(ol if d==1 else oh) if stop_mode=="STOP_OPPOSITE_OR" else mid
                    rows.append(_signal("ORB","DIRECT",instrument,b.close_time,d,broke[2],stop,target_r,or_high=oh,or_low=ol,or_mid=mid,or_length=length,stop_mode=stop_mode))
            elif broke is not None and submodel in ("BREAKOUT_RETEST","FAILED_BREAKOUT_DIAGNOSTIC"):
                bb,d,lev=broke; age=int((b.open_time-bb.open_time)/pd.Timedelta(minutes=1))
                exc_lo=min(exc_lo,b.low);exc_hi=max(exc_hi,b.high)
                if submodel=="BREAKOUT_RETEST":
                    hit=(b.low<=lev+tick and b.close>lev) if d==1 else (b.high>=lev-tick and b.close<lev)
                    if 1<=age<=5 and hit:
                        stop=b.low-tick if d==1 else b.high+tick; rows.append(_signal("ORB","BREAKOUT_RETEST",instrument,b.close_time,d,lev,stop,target_r,or_high=oh,or_low=ol,or_length=length)); break
                else:
                    inside=ol<b.close<oh
                    if 1<=age<=5 and inside:
                        rd=-d;stop=exc_lo-tick if rd==1 else exc_hi+tick;rows.append(_signal("ORB","FAILED_BREAKOUT_DIAGNOSTIC",instrument,b.close_time,rd,lev,stop,target_r,or_high=oh,or_low=ol,failed_excursion_low=exc_lo,failed_excursion_high=exc_hi,or_length=length));break
                if age>5:break
    return pd.DataFrame(rows)


def trend_signals(m5,instrument,slow=50,target_r=3.):
    x=indicators(m5,20,slow); rows=[]; tick=TICKS[instrument]
    for _,idx in x.groupby("trading_date",sort=False).indices.items():
        pull=None
        for pos,i in enumerate(idx):
            if i<slow+3:continue
            b=x.loc[i]; d=1 if b.ema_fast>b.ema_slow and b.ema_slow>x.ema_slow.iloc[i-3] else -1 if b.ema_fast<b.ema_slow and b.ema_slow<x.ema_slow.iloc[i-3] else 0
            if pull:
                age=pos-pull["pos"]; invalid=b.close<b.ema_slow if pull["d"]==1 else b.close>b.ema_slow
                if invalid or age>6:pull=None
                else:
                    pull["lo"]=min(pull["lo"],b.low);pull["hi"]=max(pull["hi"],b.high)
                    resume=(b.close>b.ema_fast and b.close>x.close.iloc[i-1]) if pull["d"]==1 else (b.close<b.ema_fast and b.close<x.close.iloc[i-1])
                    if resume:
                        dd=pull["d"]; stop=pull["lo"]-tick if dd==1 else pull["hi"]+tick
                        rows.append(_signal("TREND_PULLBACK",f"EMA20_{slow}",instrument,b.close_time,dd,b.ema_fast,stop,target_r,pullback_start=x.close_time.iloc[pull["i"]],pullback_bars=age+1,ema_fast=b.ema_fast,ema_slow=b.ema_slow));pull=None;continue
            if pull is None and d and ((d==1 and b.low<=b.ema_fast and b.close>=b.ema_slow) or (d==-1 and b.high>=b.ema_fast and b.close<=b.ema_slow)):
                pull={"pos":pos,"i":i,"d":d,"lo":b.low,"hi":b.high}
    return pd.DataFrame(rows)


def mean_reversion_signals(m5,instrument,k=2.,lower=30,target_r=2.,exit_mode="REENTRY_2R"):
    x=indicators(m5,bb_k=k); rows=[]; tick=TICKS[instrument]; pending=None
    prior_date=None
    for i,b in x.iterrows():
        if prior_date is not None and b.trading_date!=prior_date: pending=None
        prior_date=b.trading_date
        if pending:
            age=i-pending["i"]; pending["lo"]=min(pending["lo"],b.low);pending["hi"]=max(pending["hi"],b.high)
            inside=b.close>x.bb_lower.iloc[i] if pending["d"]==1 else b.close<x.bb_upper.iloc[i]
            if 1<=age<=3 and inside:
                d=pending["d"];stop=pending["lo"]-tick if d==1 else pending["hi"]+tick
                sub=exit_mode;tr=target_r if sub=="REENTRY_2R" else None;target=float(b.bb_mid) if sub=="REENTRY_FIXED_MID" else None
                rows.append(_signal("BOLLINGER_RSI",sub,instrument,b.close_time,d,b.bb_mid,stop,tr,extreme_time=x.close_time.iloc[pending["i"]],reentry_time=b.close_time,band=pending["band"],rsi=pending["rsi"],bb_k=k,rsi_threshold=lower,target_price=target));pending=None
            elif age>=3:pending=None
        if pending is None and np.isfinite(b.rsi):
            if b.close<b.bb_lower and b.rsi<=lower:pending={"i":i,"d":1,"lo":b.low,"hi":b.high,"band":b.bb_lower,"rsi":b.rsi}
            elif b.close>b.bb_upper and b.rsi>=100-lower:pending={"i":i,"d":-1,"lo":b.low,"hi":b.high,"band":b.bb_upper,"rsi":b.rsi}
    return pd.DataFrame(rows)


def pair_features(cny,si,window=480,model="DISTANCE"):
    a=cny[["close_time","open_time","close","open","trading_date"]].merge(si[["close_time","open_time","close","open"]],on="close_time",suffixes=("_cny","_si"))
    if not (a.open_time_cny==a.open_time_si).all(): raise ValueError("misaligned corresponding open timestamps")
    lc=np.log(a.close_cny); ls=np.log(a.close_si)
    if model=="OLS":
        # Coefficients at t use [t-window,t), implemented by shift(1).
        mx=ls.shift(1).rolling(window).mean();my=lc.shift(1).rolling(window).mean()
        cov=(ls*lc).shift(1).rolling(window).mean()-mx*my;var=(ls*ls).shift(1).rolling(window).mean()-mx*mx
        beta=cov/var;alpha=my-beta*mx;spread=lc-alpha-beta*ls
        # Historical residual standard deviation under the coefficients known at t.
        ey2=(lc*lc).shift(1).rolling(window).mean();ex2=(ls*ls).shift(1).rolling(window).mean();exy=(ls*lc).shift(1).rolling(window).mean()
        variance=(ey2 + alpha*alpha + beta*beta*ex2 - 2*alpha*my - 2*beta*exy + 2*alpha*beta*mx).clip(lower=0)
        mean=pd.Series(0.,index=a.index);sd=np.sqrt(variance*window/(window-2))
    else:
        # Exact Gatev normalized distance.  Rolling moments are divided by the
        # first observation in [t-window,t), which is shift(window).
        c=a.close_cny.astype(float);s=a.close_si.astype(float);c0=c.shift(window);s0=s.shift(window)
        mc=c.shift(1).rolling(window).mean()/c0;ms=s.shift(1).rolling(window).mean()/s0
        mean=mc-ms
        second=(c*c).shift(1).rolling(window).sum()/(c0*c0)+(s*s).shift(1).rolling(window).sum()/(s0*s0)-2*(c*s).shift(1).rolling(window).sum()/(c0*s0)
        variance=(second-window*mean*mean)/(window-1);sd=np.sqrt(variance.clip(lower=0));spread=c/c0-s/s0;beta=pd.Series(1.,index=a.index)
    a["spread"]=spread;a["z"]=(spread-mean)/sd;a["beta"]=beta;return a


def pair_signals(cny,si,window=480,z_entry=2.,model="DISTANCE"):
    x=pair_features(cny,si,window,model); rows=[];prior_inside=True
    for i,b in x.iterrows():
        if not np.isfinite(b.z): prior_inside=True;continue
        inside=abs(b.z)<z_entry
        if not inside and prior_inside:
            beta=float(b.beta);d=-1 if b.z>0 else 1
            if model=="OLS" and (not np.isfinite(beta) or beta==0): prior_inside=inside;continue
            dsi=-d*(1 if beta>0 else -1) if model=="OLS" else -d
            wc=.5 if model=="DISTANCE" else 1/(1+abs(beta));ws=1-wc
            rows.append({"family":"PAIRS","submodel":model,"instrument":"CNYRUBF+USDRUBF","variant_id":f"PAIRS|{model}|window={window}|z={z_entry}|hold=120","signal_time":b.close_time,"direction_cny":d,"direction_si":dsi,"z":float(b.z),"entry_z":float(b.z),"beta":beta,"beta_at_entry":beta,"w_cny":wc,"w_si":ws,"window":window,"z_entry":z_entry,"feature_index":i})
        prior_inside=inside
    result=pd.DataFrame(rows);result.attrs["feature_frame"]=x;return result


def simulate_explicit_orders(m1,signals,tick,max_hold=120):
    """Explicit structural prices; next-open, same-day, stop-first, gap-aware."""
    rows=[]; diagnostics=[]; busy_until={}
    if signals.empty:return pd.DataFrame()
    open_ns=m1.open_time.astype("int64").to_numpy(); unit=m1.open_time.dtype.unit; divisor={"ns":1,"us":1_000,"ms":1_000_000,"s":1_000_000_000}[unit]
    op=m1.open.to_numpy(float);hi=m1.high.to_numpy(float);lo=m1.low.to_numpy(float);cl=m1.close.to_numpy(float);dates=m1.trading_date.to_numpy();ot=m1.open_time.array;ct=m1.close_time.array
    day_end=np.empty(len(m1),int)
    for ix in m1.groupby("trading_date",sort=False).indices.values():day_end[np.asarray(ix)]=max(ix)
    if "variant_id" not in signals:
        signals=signals.assign(variant_id=signals.family.astype(str)+"|"+signals.submodel.astype(str)+"|"+signals.instrument.astype(str))
    ordered=signals.sort_values(["signal_time","variant_id"],kind="mergesort")
    ambiguous=set(ordered.groupby(["instrument","variant_id","signal_time"]).size().loc[lambda x:x>1].index)
    for tid,s in enumerate(ordered.itertuples(),1):
        key=(s.instrument,s.variant_id)
        if (s.instrument,s.variant_id,s.signal_time) in ambiguous: diagnostics.append({"signal_time":s.signal_time,"variant_id":s.variant_id,"reason":"AMBIGUOUS_SIMULTANEOUS_SIGNAL"});continue
        if key in busy_until and pd.Timestamp(s.signal_time)<busy_until[key]: diagnostics.append({"signal_time":s.signal_time,"variant_id":s.variant_id,"reason":"OPEN_POSITION"});continue
        stamp=pd.Timestamp(s.signal_time).value//divisor; entry_i=int(np.searchsorted(open_ns,stamp,side="left"))
        if entry_i>=len(m1) or open_ns[entry_i]!=stamp:diagnostics.append({"signal_time":s.signal_time,"variant_id":s.variant_id,"reason":"DATA_GAP_NO_NEXT_OPEN"});continue
        signal_day=pd.Timestamp(s.signal_time).date()
        if dates[entry_i]!=signal_day:continue
        entry=op[entry_i]; d=s.direction; stop=round_to_tick(s.stop_price,tick); risk=d*(entry-stop)
        if risk<=0:continue
        tr=getattr(s,"target_r",None);explicit=getattr(s,"target_price",None)
        tr=None if pd.isna(tr) else tr;explicit=None if pd.isna(explicit) else explicit
        if tr is not None and explicit is not None:raise ValueError("exactly one target definition is allowed")
        if tr is None and explicit is None:raise ValueError("target_r or target_price required")
        target=round_to_tick(entry+d*risk*tr if tr is not None else float(explicit),tick)
        if d*(target-entry)<=0:continue
        end_i=min(entry_i+max_hold-1,day_end[entry_i]);price=cl[end_i];reason="TIME" if end_i==entry_i+max_hold-1 else "DAY_END";exit_i=end_i
        po=op[entry_i:end_i+1];ph=hi[entry_i:end_i+1];pl=lo[entry_i:end_i+1]
        gs=po<=stop if d==1 else po>=stop;hs=pl<=stop if d==1 else ph>=stop;ht=ph>=target if d==1 else pl<=target;hit=gs|hs|ht
        if hit.any():
            off=int(np.flatnonzero(hit)[0]);exit_i=entry_i+off
            if gs[off]:price=op[exit_i];reason="STOP_GAP"
            elif hs[off]:price=stop;reason="STOP_FIRST_TIE" if ht[off] else "STOP"
            else:price=target;reason="TARGET"
        for fr,ticks in (("GROSS",0),("BASE",1),("STRESS",2)):
            net=d*((price-d*ticks*tick)-(entry+d*ticks*tick))
            rows.append({"trade_id":tid,"family":s.family,"submodel":s.submodel,"instrument":s.instrument,"variant_id":s.variant_id,"signal_time":s.signal_time,"entry_time":ot[entry_i],"exit_time":ct[exit_i],"side":s.side,"raw_entry_price":entry,"entry_price":entry+d*ticks*tick,"stop_price":stop,"target_price":target,"exit_price":price-d*ticks*tick,"exit_reason":reason,"friction":fr,"pnl_native":net,"pnl":net,"pnl_R":net/risk,"pnl_bps":net/entry*10000,"bars_held":exit_i-entry_i+1})
        busy_until[key]=pd.Timestamp(ct[exit_i])
    result=pd.DataFrame(rows);result.attrs["skip_diagnostics"]=diagnostics;return result


def simulate_pairs(cny,si,signals,max_hold=120):
    rows=[]; diagnostics=[]; features=signals.attrs.get("feature_frame")
    common=cny.merge(si,on="open_time",suffixes=("_cny","_si"),how="inner").sort_values("open_time").reset_index(drop=True)
    for tid,s in enumerate(signals.itertuples(),1):
        matches=common.index[common.open_time.eq(s.signal_time)]
        if len(matches)!=1: diagnostics.append({"signal_time":s.signal_time,"reason":"DATA_GAP_NO_COMMON_OPEN"});continue
        i=int(matches[0]);day=common.trading_date_cny.iloc[i];same=common.index[(common.index>=i)&common.trading_date_cny.eq(day)]
        end=int(same[min(max_hold-1,len(same)-1)]);reason="TIME" if len(same)>=max_hold else "DAY_END";exit_z=np.nan
        if features is not None:
            fi=int(s.feature_index)
            for j in range(fi+1,len(features)):
                q=features.iloc[j]
                if q.trading_date!=day: break
                if q.z==0 or np.sign(q.z)!=np.sign(s.entry_z):
                    nxt=common.index[common.open_time.eq(q.close_time)]
                    if len(nxt) and int(nxt[0])<=same[-1]:end=int(nxt[0]);reason="CONVERGENCE";exit_z=float(q.z)
                    break
        ec,es=common.close_cny.iloc[end],common.close_si.iloc[end]
        beta=float(getattr(s,"beta_at_entry",getattr(s,"beta",1.)));wc=float(getattr(s,"w_cny",.5 if s.submodel=="DISTANCE" else 1/(1+abs(beta))));ws=1-wc
        for fr,t in (("GROSS",0),("BASE",1),("STRESS",2)):
            oc,os=common.open_cny.iloc[i],common.open_si.iloc[i];pc=wc*(s.direction_cny*(ec-oc)/oc-2*t*TICKS["CNYRUBF"]/oc);ps=ws*(s.direction_si*(es-os)/os-2*t*TICKS["USDRUBF"]/os)
            rows.append({"trade_id":tid,"family":"PAIRS","submodel":s.submodel,"instrument":"CNYRUBF+USDRUBF","variant_id":getattr(s,"variant_id",f"PAIRS|{s.submodel}"),"signal_time":s.signal_time,"entry_time":common.open_time.iloc[i],"exit_time":common.close_time_cny.iloc[end],"exit_reason":reason,"entry_z":getattr(s,"entry_z",np.nan),"exit_z":exit_z,"side":"SPREAD","friction":fr,"w_cny":wc,"w_si":ws,"beta_at_entry":beta,"entry_price_cny":oc,"entry_price_si":os,"exit_price_cny":ec,"exit_price_si":es,"pnl_cny":pc,"pnl_si":ps,"total_pnl":pc+ps,"pnl":pc+ps,"pnl_bps":(pc+ps)*10000,"bars_held":end-i+1})
    result=pd.DataFrame(rows);result.attrs["skip_diagnostics"]=diagnostics;return result


def metrics(ledger):
    rows=[]
    if ledger.empty:return pd.DataFrame()
    ledger=ledger.sort_values("entry_time",kind="mergesort").copy() if "entry_time" in ledger else ledger.copy()
    if "variant_id" not in ledger:ledger["variant_id"]=ledger.family.astype(str)+"|"+ledger.submodel.astype(str)
    if "period" not in ledger:ledger["period"]="UNSPECIFIED"
    if "pnl_bps" not in ledger:ledger["pnl_bps"]=ledger.pnl
    for key,g in ledger.groupby(["family","submodel","instrument","variant_id","friction","period"],dropna=False):
        p=g.pnl_bps.to_numpy(float); w=p[p>0]; l=p[p<0]; eq=p.cumsum();peak=np.maximum.accumulate(np.r_[0,eq])[1:]
        row=dict(zip(["family","submodel","instrument","variant_id","friction","period"],key))|{"trades":len(p),"profit_factor":w.sum()/-l.sum() if len(l) else np.inf,"expectancy_bps":p.mean(),"median_bps":np.median(p),"max_drawdown_bps":max(0,float(np.max(peak-eq))),"win_rate":np.mean(p>0),"payoff_ratio":w.mean()/-l.mean() if len(w) and len(l) else np.nan,"average_holding_bars":g.bars_held.mean()}
        if "pnl_R" in g:row|={"mean_pnl_R":g.pnl_R.mean(),"median_pnl_R":g.pnl_R.median()}
        rows.append(row)
    return pd.DataFrame(rows)


def assert_oos(selection_end,evaluation_start):
    if pd.Timestamp(evaluation_start)<=pd.Timestamp(selection_end):raise ValueError("evaluation overlaps parameter-selection period")


def freeze(path,variants):
    data=json.dumps(variants,sort_keys=True,indent=2)+"\n";Path(path).write_text(data);return sha256(data.encode()).hexdigest()


def verify_frozen(path,digest):
    return sha256(Path(path).read_bytes()).hexdigest()==digest
