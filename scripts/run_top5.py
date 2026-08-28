#!/usr/bin/env python3
"""Top-5 V2 guarded runner.  Default and --full never start research work."""
from __future__ import annotations
import argparse,json,resource,time
from pathlib import Path
import pandas as pd
from market_pattern_discovery.backtest.top5 import *

OUT=Path("results/top5_real_strategies_v2");ROOT="/workspace/market-pattern-data"

def timed(profile,name,fn):
    t=time.perf_counter();value=fn();profile[name]=time.perf_counter()-t;return value

def load_frames(profile=None):
    t=time.perf_counter();f={i:load_dev(ROOT,i) for i in TICKS}
    if profile is not None:profile["data_loading"]=time.perf_counter()-t
    maximum=max(x.close_time.max() for x in f.values())
    if maximum>=DEV_END:raise RuntimeError("validation row accessed")
    return f,maximum

def audit():
    validate_contract(MANDATORY_CONTRACT)
    print("CONTRACT AUDIT V2")
    for text in ("GERCHIK_A_M1_PROXY PRESENT","EH PRESENT","EL PRESENT","MIRROR PRESENT","IMMUTABLE LEVEL SNAPSHOTS","ORB FAILED BREAKOUT PRESENT","ORB MIDPOINT STOP PRESENT","PAIRS DISTANCE NORMALIZED","PAIRS CONVERGENCE EXIT PRESENT","OLS BETA WEIGHTING PRESENT","BOLLINGER FIXED MID EXIT PRESENT","SMOKE OCCURS BEFORE FULL"):print(f"{text}: YES")
    print("VALIDATION ACCESSED: NO")

def all_signals(frames,first_ten=False):
    use={}
    for inst,f in frames.items():
        if first_ten:
            days=pd.unique(f.trading_date)[:10];use[inst]=f[f.trading_date.isin(days)].reset_index(drop=True)
        else:use[inst]=f
    m5={i:causal_m5(f) for i,f in use.items()};result={};levels={}
    for inst in TICKS:
        levels[inst]=structural_levels(m5[inst],inst,2,2);s=structural_signals(m5[inst],levels[inst],inst,3.);g=gerchik_a_signals(m5[inst],levels[inst],inst)
        for sub in ("REJECTION","SIMPLE_SWEEP","COMPLEX_FALSE_BREAK","BREAKOUT_RETEST"):result.setdefault(f"STRUCTURAL {sub}",[]).append(s[s.submodel.eq(sub)] if len(s) else s)
        result.setdefault("GERCHIK_A_M1_PROXY",[]).append(g)
        result.setdefault("ORB DIRECT",[]).append(orb_signals(use[inst],inst,15,2.,submodel="DIRECT"))
        result.setdefault("ORB BREAKOUT_RETEST",[]).append(orb_signals(use[inst],inst,15,2.,submodel="BREAKOUT_RETEST"))
        result.setdefault("ORB FAILED_BREAKOUT",[]).append(orb_signals(use[inst],inst,15,2.,submodel="FAILED_BREAKOUT"))
        result.setdefault("TREND_PULLBACK",[]).append(trend_signals(m5[inst],inst,50,3.))
        result.setdefault("BOLLINGER_RSI REENTRY_2R",[]).append(mean_reversion_signals(m5[inst],inst,2.,30,2.,"REENTRY_2R"))
        result.setdefault("BOLLINGER_RSI REENTRY_FIXED_MID",[]).append(mean_reversion_signals(m5[inst],inst,2.,30,None,"REENTRY_FIXED_MID"))
    result["PAIRS DISTANCE"]=[pair_signals(use["CNYRUBF"],use["USDRUBF"],480,2.,"DISTANCE")]
    result["PAIRS OLS"]=[pair_signals(use["CNYRUBF"],use["USDRUBF"],480,2.,"OLS")]
    return {k:pd.concat(v,ignore_index=True) if any(len(x) for x in v) else pd.DataFrame() for k,v in result.items()},levels

def smoke():
    audit();OUT.mkdir(parents=True,exist_ok=True);frames,maximum=load_frames();small,levels=all_signals(frames,True);full_cache=None;summary={};samples=[]
    print("REAL TOP-5 SMOKE V2")
    for name,s in small.items():
        count=len(s);status="PASS"
        if not count:
            if full_cache is None:full_cache,_=all_signals(frames,False)
            count=len(full_cache[name]);status=f"ZERO_IN_10_DAYS / FULL_DEV_COUNT={count}" if count else "ZERO_REAL_EVENTS"
            s=full_cache[name]
        example=s.head(1).to_dict("records") if count else []
        summary[name]={"first_10_day_count":len(small[name]),"full_dev_count":count if not len(small[name]) else None,"status":status,"example":example}
        if len(s):samples.append(s.assign(smoke_name=name).head(1))
        print(f"{name}: {status}; count={count}; event={example[:1]}")
    (OUT/"strategy_contract.json").write_text(json.dumps(MANDATORY_CONTRACT,indent=2)+"\n")
    (OUT/"smoke_summary.json").write_text(json.dumps(summary,indent=2,default=str)+"\n")
    pd.concat(samples,ignore_index=True).to_csv(OUT/"smoke_events_sample.csv",index=False)
    pd.concat(levels.values(),ignore_index=True).head(200).to_csv(OUT/"level_snapshot_sample.csv",index=False)
    print(f"MAX MARKET TIMESTAMP ACCESSED: {maximum}")

def profile_dev():
    audit();OUT.mkdir(parents=True,exist_ok=True);p={};frames,maximum=load_frames(p);m5=timed(p,"m5_construction",lambda:{i:causal_m5(f) for i,f in frames.items()})
    timed(p,"indicator_calculation",lambda:[indicators(x) for x in m5.values()]);piv=timed(p,"pivot_generation",lambda:{i:confirmed_pivots(x) for i,x in m5.items()})
    levels=timed(p,"structural_clustering",lambda:{i:structural_levels(m5[i],i,2,2) for i in TICKS})
    ss=timed(p,"structural_signal_generation",lambda:{i:structural_signals(m5[i],levels[i],i,3.) for i in TICKS})
    sled=timed(p,"explicit_order_simulation",lambda:[simulate_explicit_orders(frames[i],ss[i],TICKS[i]) for i in TICKS])
    orb=timed(p,"orb_generation",lambda:{i:orb_signals(frames[i],i,15,2.,submodel="DIRECT",stop_mode="STOP_OPPOSITE_OR") for i in TICKS})
    trend=timed(p,"trend_generation",lambda:{i:trend_signals(m5[i],i,50,3.) for i in TICKS})
    dist=timed(p,"pair_feature_distance",lambda:pair_features(frames["CNYRUBF"],frames["USDRUBF"],480,"DISTANCE"))
    ols=timed(p,"pair_feature_ols",lambda:pair_features(frames["CNYRUBF"],frames["USDRUBF"],480,"OLS"))
    ps=timed(p,"pair_signal_generation",lambda:[pair_signals(frames["CNYRUBF"],frames["USDRUBF"],480,2.,x) for x in ("DISTANCE","OLS")])
    pled=timed(p,"pair_simulation",lambda:[simulate_pairs(frames["CNYRUBF"],frames["USDRUBF"],x) for x in ps])
    br=timed(p,"bollinger_rsi_signal_generation",lambda:{i:mean_reversion_signals(m5[i],i,2.,30,2.) for i in TICKS})
    p["canonical_total_seconds"]=sum(v for k,v in p.items() if k!="canonical_total_seconds")
    # Cache-aware projection: structural clusters x6, OR ranges x3, trend regimes x2,
    # pair features x6, Bollinger indicator sets x6; target/threshold variants reuse signals/features.
    projected=p["data_loading"]+p["m5_construction"]+p["pivot_generation"]+6*(p["structural_clustering"]+p["structural_signal_generation"])+3*p["orb_generation"]+2*p["trend_generation"]+3*(p["pair_feature_distance"]+p["pair_feature_ols"])+6*p["bollinger_rsi_signal_generation"]+12*p["explicit_order_simulation"]+6*p["pair_simulation"]
    p.update({"rows_processed":sum(len(x) for x in frames.values()),"signals_generated":sum(len(x) for x in ss.values())+sum(len(x) for x in orb.values())+sum(len(x) for x in trend.values())+sum(len(x) for x in ps)+sum(len(x) for x in br.values()),"trades_executed":sum(x.trade_id.nunique() if len(x) else 0 for x in sled+pled),"peak_rss_kb":resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,"projected_full_dev_seconds":projected,"performance_gate":"PASS" if projected<=600 else "FAIL","max_market_timestamp_accessed":str(maximum)})
    (OUT/"performance_profile.json").write_text(json.dumps(p,indent=2)+"\n");(OUT/"performance_profile.md").write_text("# Top-5 V2 DEV performance profile\n\n```json\n"+json.dumps(p,indent=2)+"\n```\n")
    for k,v in p.items():print(f"{k}: {v}")
    print(f"PROJECTED_FULL_DEV_SECONDS: {projected}");print(f"MAX MARKET TIMESTAMP ACCESSED: {maximum}")

def main():
    parser=argparse.ArgumentParser();m=parser.add_mutually_exclusive_group(required=True);m.add_argument("--smoke",action="store_true");m.add_argument("--profile-dev",action="store_true");m.add_argument("--full",action="store_true");a=parser.parse_args()
    if a.full:raise SystemExit("--full is disabled until the V2 performance gate passes and a separate authorized run is requested")
    smoke() if a.smoke else profile_dev()
if __name__=="__main__":main()
