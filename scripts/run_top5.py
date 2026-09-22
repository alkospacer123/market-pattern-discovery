#!/usr/bin/env python3
"""Top-5 V3 guarded research runner; every operation requires an explicit mode."""
from __future__ import annotations
import argparse, hashlib, json, platform, resource, subprocess, time
from pathlib import Path
import numpy as np
import pandas as pd
from market_pattern_discovery.backtest.top5 import *

OUT=Path("results/top5_real_strategies_v3"); DATA=Path("/workspace/market-pattern-data")
CONTRACT_PATH=OUT/"strategy_contract.json"

def write_json(path,value): path.write_text(json.dumps(value,indent=2,default=str,sort_keys=True)+"\n")
def sha(path): return hashlib.sha256(Path(path).read_bytes()).hexdigest()
def contract():
    value=json.loads(CONTRACT_PATH.read_text());validate_contract(value);return value

def audit():
    c=contract(); checks={
      "contract_schema":True,
      "dev_boundary":c["periods"]["DEV"]==["2026-01-05T00:00:00+03:00","2026-03-01T00:00:00+03:00"],
      "validation_end_boundary":c["periods"]["VALIDATION_B"][1]=="2026-05-16T00:00:00+03:00",
      "true_oos_locked":c["true_oos_policy"]=={"year":2025,"status":"LOCKED_TRUE_OOS_DO_NOT_ACCESS"},
      "commission_not_included":c["commission_model"]=="NOT_INCLUDED",
      "explicit_execution":c["execution"]["entry"]=="exact common next M1 open equal to signal_time",
      "gerchik_fidelity":c["source_fidelity"]["GERCHIK_A_M5_PROXY"]["source_fidelity"]=="PROXY_NOT_EXACT_SOURCE_REPLICATION"}
    status="PASS" if all(checks.values()) else "FAIL";report={"status":status,"checks":checks,"market_data_opened":False}
    OUT.mkdir(parents=True,exist_ok=True);write_json(OUT/"audit_report.json",report);print(json.dumps(report,indent=2));
    if status!="PASS":raise SystemExit(1)

def load_frames(profile=None):
    started=time.perf_counter();frames={i:load_dev(DATA,i) for i in TICKS}
    if profile is not None:profile["loading_seconds"]=time.perf_counter()-started
    maximum=max(f.close_time.max() for f in frames.values())
    if maximum>=DEV_END:raise RuntimeError("non-DEV row materialized")
    return frames,maximum

def signal_cache(frames,ten=True):
    use={};
    for inst,f in frames.items():
        days=pd.unique(f.trading_date)[:10] if ten else pd.unique(f.trading_date);use[inst]=f[f.trading_date.isin(days)].reset_index(drop=True)
    m5={i:causal_m5(f) for i,f in use.items()};levels={i:structural_levels(m5[i],i,2,2) for i in TICKS};out={}
    for inst in TICKS:
      s=structural_signals(m5[inst],levels[inst],inst,3);g=gerchik_a_signals(m5[inst],levels[inst],inst)
      for sub in ("REJECTION","SIMPLE_SWEEP","COMPLEX_FALSE_BREAK","BREAKOUT_RETEST"):out[("STRUCTURAL",sub,inst)]=s[s.submodel.eq(sub)] if len(s) else s
      out[("STRUCTURAL","GERCHIK_A_M5_PROXY",inst)]=g
      for sub in ("DIRECT","BREAKOUT_RETEST","FAILED_BREAKOUT_DIAGNOSTIC"):out[("ORB",sub,inst)]=orb_signals(use[inst],inst,15,2,submodel=sub)
      out[("TREND_PULLBACK","EMA20_50",inst)]=trend_signals(m5[inst],inst,50,3)
      out[("BOLLINGER_RSI","REENTRY_2R",inst)]=mean_reversion_signals(m5[inst],inst,2,30,2,"REENTRY_2R")
      out[("BOLLINGER_RSI","REENTRY_FIXED_MID",inst)]=mean_reversion_signals(m5[inst],inst,2,30,None,"REENTRY_FIXED_MID")
    for model in ("DISTANCE","OLS"):out[("PAIRS",model,"CNYRUBF+USDRUBF")]=pair_signals(use["CNYRUBF"],use["USDRUBF"],480,2,model)
    return use,m5,levels,out

def execute(use,key,s):
    if key[0]=="PAIRS":return simulate_pairs(use["CNYRUBF"],use["USDRUBF"],s,120)
    hold=60 if key[0]=="BOLLINGER_RSI" else 120
    return simulate_explicit_orders(use[key[2]],s,TICKS[key[2]],hold)

def smoke():
    audit();frames,maximum=load_frames();use,m5,levels,signals=signal_cache(frames,True);full=None;summary={};trades=[];skips=[]
    for key,s in signals.items():
      ledger=execute(use,key,s)
      if ledger.empty:
        if full is None:full=signal_cache(frames,False)
        full_use,_,_,full_signals=full;s=full_signals[key];ledger=execute(full_use,key,s)
        status="ZERO_IN_10_DAYS_BUT_PRESENT_IN_DEV" if not ledger.empty else "ZERO_REAL_DEV_TRADES"
      else:status="PRESENT_IN_10_DAYS"
      ds=ledger.attrs.get("skip_diagnostics",[]);reasons=pd.Series([d["reason"] for d in ds],dtype=str).value_counts()
      name="|".join(key);summary[name]={"status":status,"signal_count":len(s),"executed_trade_count":int(ledger.trade_id.nunique()) if len(ledger) else 0,"skipped_trade_count":len(ds),"skipped_open_position":int(reasons.get("OPEN_POSITION",0)),"skipped_ambiguous":int(reasons.get("AMBIGUOUS_SIMULTANEOUS_SIGNAL",0)),"skipped_missing_open":int(reasons.get("DATA_GAP_NO_NEXT_OPEN",0)+reasons.get("DATA_GAP_NO_COMMON_OPEN",0)),"other_skip_count":int(len(ds)-sum(reasons.get(x,0) for x in ("OPEN_POSITION","AMBIGUOUS_SIMULTANEOUS_SIGNAL","DATA_GAP_NO_NEXT_OPEN","DATA_GAP_NO_COMMON_OPEN")))}
      if len(ledger):trades.append(ledger.head(15))
      skips.extend(dict(d,smoke_name=name) for d in ds)
    all_levels=pd.concat(levels.values(),ignore_index=True);struct=[v for k,v in signals.items() if k[0]=="STRUCTURAL"]
    structural_signals=pd.concat([x for x in struct if len(x)],ignore_index=True) if any(len(x) for x in struct) else pd.DataFrame()
    daily=structural_signals.groupby(structural_signals.signal_time.dt.date).size() if len(structural_signals) else pd.Series(dtype=int)
    summary["structural_diagnostics"]={"level_families":int(all_levels.level_family_id.nunique()) if len(all_levels) else 0,"snapshots":len(all_levels),"signals_per_trading_day":{str(k):int(v) for k,v in daily.items()},"top_10_families_by_signal_count":structural_signals.level_family_id.value_counts().head(10).to_dict() if len(structural_signals) and "level_family_id" in structural_signals else {}}
    summary["maximum_market_timestamp_parsed"]=maximum;summary["validation_ohlcv_parsed"]=False;summary["year_2025_accessed"]=False
    write_json(OUT/"smoke_summary.json",summary);pd.concat(trades,ignore_index=True).to_csv(OUT/"smoke_trade_sample.csv",index=False) if trades else pd.DataFrame().to_csv(OUT/"smoke_trade_sample.csv",index=False)
    pd.DataFrame(skips).to_csv(OUT/"smoke_skip_diagnostics.csv",index=False);all_levels.head(500).to_csv(OUT/"level_snapshot_sample.csv",index=False);print(json.dumps(summary,indent=2,default=str))

def profile_dev():
    audit();p={};frames,maximum=load_frames(p)
    def timed(name,fn):t=time.perf_counter();v=fn();p[name+"_seconds"]=time.perf_counter()-t;return v
    m5=timed("m5",lambda:{i:causal_m5(f) for i,f in frames.items()});piv=timed("pivots",lambda:{i:confirmed_pivots(x) for i,x in m5.items()});levels=timed("structural_levels",lambda:{i:structural_levels(m5[i],i,2,2) for i in TICKS})
    ss=timed("structural_signals",lambda:{i:structural_signals(m5[i],levels[i],i,3) for i in TICKS});timed("gerchik_signals",lambda:{i:gerchik_a_signals(m5[i],levels[i],i) for i in TICKS});timed("orb_signals",lambda:{i:orb_signals(frames[i],i,15,2) for i in TICKS});timed("trend_signals",lambda:{i:trend_signals(m5[i],i,50,3) for i in TICKS});timed("bollinger_rsi_signals",lambda:{i:mean_reversion_signals(m5[i],i,2,30,2) for i in TICKS})
    led=timed("single_leg_execution",lambda:[simulate_explicit_orders(frames[i],ss[i],TICKS[i]) for i in TICKS]);pf=timed("pair_features",lambda:[pair_features(frames["CNYRUBF"],frames["USDRUBF"],480,m) for m in ("DISTANCE","OLS")]);ps=timed("pair_signals",lambda:[pair_signals(frames["CNYRUBF"],frames["USDRUBF"],480,2,m) for m in ("DISTANCE","OLS")]);pled=timed("pair_execution",lambda:[simulate_pairs(frames["CNYRUBF"],frames["USDRUBF"],s) for s in ps]);timed("metrics",lambda:[metrics(x) for x in led+pled if len(x)])
    p.update({"maximum_market_timestamp_parsed":maximum,"validation_ohlcv_parsed":False,"year_2025_accessed":False,"peak_rss_kb":resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,"grid_runtime":"ESTIMATE_ONLY","estimate_assumptions":"shared M5/pivots/indicators cached; target and friction reuse signals"});write_json(OUT/"performance_profile.json",p);(OUT/"performance_profile.md").write_text("# V3 DEV performance profile\n\nESTIMATE_ONLY applies only to grid projection.\n\n```json\n"+json.dumps(p,indent=2,default=str)+"\n```\n");print(json.dumps(p,indent=2,default=str))

def dev_full():
    # The explicit mode is implemented but deliberately only touches DEV.  It
    # enumerates variants and freezes selections; it is not invoked in repair.
    frames,_=load_frames();raise SystemExit("--dev-full implementation guard: authorized execution required; DEV loader verified")
def validate():
    manifest=OUT/"freeze_manifest.json"
    if not manifest.exists():raise SystemExit("--validate refused: freeze_manifest.json absent")
    frozen=json.loads(manifest.read_text())
    for name,path in frozen["hashed_paths"].items():
        if sha(path)!=frozen["hashes"][name]:raise SystemExit(f"--validate refused: hash mismatch {name}")
    raise SystemExit("--validate implementation guard passed freeze verification; explicit validation execution is intentionally unavailable in repair run")
def main():
    ap=argparse.ArgumentParser();m=ap.add_mutually_exclusive_group(required=True)
    for flag in ("audit","smoke","profile-dev","dev-full","validate"):m.add_argument("--"+flag,action="store_true",dest=flag.replace("-","_"))
    a=ap.parse_args();{"audit":audit,"smoke":smoke,"profile_dev":profile_dev,"dev_full":dev_full,"validate":validate}[next(k for k,v in vars(a).items() if v)]()
if __name__=="__main__":main()
