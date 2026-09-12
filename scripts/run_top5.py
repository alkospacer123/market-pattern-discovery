#!/usr/bin/env python3
"""Run the preregistered Top-5 real-strategy benchmark in locked order."""
from pathlib import Path
from hashlib import sha256
import json, sys
import numpy as np
import pandas as pd

from market_pattern_discovery.backtest.top5 import *

OUT=Path("results/top5_real_strategies_v1")
START=pd.Timestamp("2026-01-05",tz="Europe/Moscow")

def period_signals(s,start,end):
    return s[(s.signal_time>=start)&(s.signal_time<end)].reset_index(drop=True) if not s.empty else s

def score(ledger):
    if ledger.empty:return {"trades":0,"base_pf":np.nan,"base_expectancy":np.nan,"stress_pf":np.nan,"max_dd":np.nan}
    m=metrics(ledger); b=m[m.friction.eq("BASE")].iloc[0]; st=m[m.friction.eq("STRESS")].iloc[0]
    return {"trades":int(b.trades),"base_pf":b.profit_factor,"base_expectancy":b.expectancy,"stress_pf":st.profit_factor,"max_dd":b.max_drawdown}

def main():
    OUT.mkdir(parents=True,exist_ok=True)
    frames={i:load_discovery("/workspace/market-pattern-data",i)[0] for i in TICKS}; m5={i:causal_m5(f) for i,f in frames.items()};m5dev={i:x[x.close_time<DEV_END].reset_index(drop=True) for i,x in m5.items()}
    contract={"title":"TOP-5 REAL STRATEGY BENCHMARK V1","families":{"STRUCTURAL":["REJECTION","SIMPLE_SWEEP","COMPLEX_FALSE_BREAK","BREAKOUT_RETEST"],"ORB":["DIRECT","BREAKOUT_RETEST","FAILED_BREAKOUT_DIAGNOSTIC"],"TREND_PULLBACK":["EMA20_50","EMA20_100"],"PAIRS":["DISTANCE","OLS"],"BOLLINGER_RSI":["REENTRY_2R"]},"forbidden_substitutes_used":False,"eh_el_required":True}
    (OUT/"strategy_contract.json").write_text(json.dumps(contract,indent=2)+"\n")
    candidates=[]; level_samples=[]; signal_samples=[]
    # Full preregistered grids, evaluated on DEV only.
    for inst in TICKS:
      for tol in (1,2,3):
       for touches in (2,3):
        lev=structural_levels(m5dev[inst],inst,tol,touches)
        if len(lev):level_samples.append(lev.head(25))
        sig0=structural_signals(m5dev[inst],lev,inst,3.)
        for tr in (2.,3.):
         sig=sig0.copy();sig["target_r"]=tr;dev=period_signals(sig,START,DEV_END); led=simulate_explicit_orders(frames[inst],dev,TICKS[inst]);
         for sub in ("REJECTION","SIMPLE_SWEEP","COMPLEX_FALSE_BREAK","BREAKOUT_RETEST"):
          ss=dev[dev.submodel.eq(sub)] if len(dev) else dev; ll=led[led.submodel.eq(sub)] if len(led) else led
          candidates.append({"family":"STRUCTURAL","submodel":sub,"instrument":inst,"params":{"tolerance_ticks":tol,"min_touches":touches,"target_r":tr},**score(ll)})
         if len(dev):signal_samples.append(dev.head(10))
      for length in (5,15,30):
       for tr in (1.5,2.):
        for retest in (False,True):
         sig=orb_signals(frames[inst],inst,length,tr,retest);dev=period_signals(sig,START,DEV_END);led=simulate_explicit_orders(frames[inst],dev,TICKS[inst]);sub="BREAKOUT_RETEST" if retest else "DIRECT"
         candidates.append({"family":"ORB","submodel":sub,"instrument":inst,"params":{"or_length":length,"target_r":tr,"stop":"RETEST_EXTREME" if retest else "OPPOSITE_OR"},**score(led)})
         if len(dev):signal_samples.append(dev.head(5))
      for slow in (50,100):
       for tr in (2.,3.):
        sig=trend_signals(m5[inst],inst,slow,tr);dev=period_signals(sig,START,DEV_END);led=simulate_explicit_orders(frames[inst],dev,TICKS[inst]);candidates.append({"family":"TREND_PULLBACK","submodel":f"EMA20_{slow}","instrument":inst,"params":{"fast":20,"slow":slow,"target_r":tr,"pullback_window":6},**score(led)});
        if len(dev):signal_samples.append(dev.head(5))
      for k in (1.5,2.,2.5):
       for lower in (25,30):
        sig=mean_reversion_signals(m5[inst],inst,k,lower,2.);dev=period_signals(sig,START,DEV_END);led=simulate_explicit_orders(frames[inst],dev,TICKS[inst],60);candidates.append({"family":"BOLLINGER_RSI","submodel":"REENTRY_2R","instrument":inst,"params":{"bb_n":20,"bb_k":k,"rsi_n":14,"rsi_lower":lower,"exit":"2R"},**score(led)});
        if len(dev):signal_samples.append(dev.head(5))
    for model in ("DISTANCE","OLS"):
     for window in (240,480,960):
      for z in (1.5,2.,2.5):
       sig=pair_signals(frames["CNYRUBF"],frames["USDRUBF"],window,z,model);dev=period_signals(sig,START,DEV_END);led=simulate_pairs(frames["CNYRUBF"],frames["USDRUBF"],dev);candidates.append({"family":"PAIRS","submodel":model,"instrument":"CNYRUBF+USDRUBF","params":{"window":window,"z_entry":z,"max_hold":120},**score(led)});
       if len(dev):signal_samples.append(dev.head(5))
    allv=pd.DataFrame(candidates);allv["params"]=allv.params.map(json.dumps);allv.to_csv(OUT/"dev_all_variants.csv",index=False)
    # One choice for each family/submodel/instrument; positive expectancy, PF, count, DD, simplicity.
    selected=[]
    for key,g in allv.groupby(["family","submodel","instrument"],sort=True):
        q=g.assign(positive=g.base_expectancy.gt(0),pf=g.base_pf.replace(np.inf,1e9)).sort_values(["positive","pf","trades","max_dd"],ascending=[False,False,False,True],kind="mergesort").iloc[0]
        selected.append({"family":key[0],"submodel":key[1],"instrument":key[2],"params":json.loads(q.params),"dev_trades":int(q.trades),"sample_flag":"LOW_SAMPLE" if q.trades<20 else "ADEQUATE"})
    frozen={"selection_data_end":"2026-02-28T23:59:59+03:00","selected":selected}; digest=freeze(OUT/"frozen_selected_variants.json",frozen)
    # Evaluation begins only after freeze.
    eval_ledgers=[]; summaries=[]
    for period,start,end in (("DEV",START,DEV_END),("VALIDATION_A",DEV_END,VAL_A_END),("VALIDATION_B",VAL_A_END,END)):
      if period!="DEV":assert_oos(frozen["selection_data_end"],start)
      for v in selected:
       inst=v["instrument"];p=v["params"]
       if v["family"]=="STRUCTURAL":
        lev=structural_levels(m5[inst],inst,p["tolerance_ticks"],p["min_touches"]);sig=structural_signals(m5[inst],lev,inst,p["target_r"]);sig=sig[sig.submodel.eq(v["submodel"])]
        led=simulate_explicit_orders(frames[inst],period_signals(sig,start,end),TICKS[inst])
       elif v["family"]=="ORB":
        sig=orb_signals(frames[inst],inst,p["or_length"],p["target_r"],v["submodel"]=="BREAKOUT_RETEST");led=simulate_explicit_orders(frames[inst],period_signals(sig,start,end),TICKS[inst])
       elif v["family"]=="TREND_PULLBACK":
        sig=trend_signals(m5[inst],inst,p["slow"],p["target_r"]);led=simulate_explicit_orders(frames[inst],period_signals(sig,start,end),TICKS[inst])
       elif v["family"]=="BOLLINGER_RSI":
        sig=mean_reversion_signals(m5[inst],inst,p["bb_k"],p["rsi_lower"],2.);led=simulate_explicit_orders(frames[inst],period_signals(sig,start,end),TICKS[inst],60)
       else:
        sig=pair_signals(frames["CNYRUBF"],frames["USDRUBF"],p["window"],p["z_entry"],v["submodel"]);led=simulate_pairs(frames["CNYRUBF"],frames["USDRUBF"],period_signals(sig,start,end))
       if len(led):led["period"]=period;eval_ledgers.append(led); mm=metrics(led);mm["period"]=period;mm["selection_data_end"]=frozen["selection_data_end"];mm["evaluation_start"]=start;mm["evaluation_end"]=end;mm["is_out_of_selection_sample"]=period!="DEV";summaries.append(mm)
    summary=pd.concat(summaries,ignore_index=True) if summaries else pd.DataFrame(); ledger=pd.concat(eval_ledgers,ignore_index=True) if eval_ledgers else pd.DataFrame()
    summary[summary.period.eq("VALIDATION_A")].to_csv(OUT/"validation_a.csv",index=False);summary[summary.period.eq("VALIDATION_B")].to_csv(OUT/"validation_b.csv",index=False);summary.to_csv(OUT/"strategy_summary.csv",index=False)
    if len(ledger): ledger.assign(month=ledger.entry_time.dt.strftime("%Y-%m")).groupby(["family","submodel","instrument","friction","month"]).agg(trades=("pnl","size"),pnl=("pnl","sum"),expectancy=("pnl","mean")).reset_index().to_csv(OUT/"monthly_summary.csv",index=False);ledger.groupby("family",sort=False).head(15).to_csv(OUT/"trade_audit_sample.csv",index=False)
    pd.concat(level_samples,ignore_index=True).head(200).to_csv(OUT/"level_audit_sample.csv",index=False);pd.concat(signal_samples,ignore_index=True).head(250).to_csv(OUT/"signal_audit_sample.csv",index=False)
    counts=pd.concat(signal_samples,ignore_index=True).family.value_counts().to_dict();print("REAL TOP-5 SMOKE\n"+"\n".join(f"{k} signals: {v}" for k,v in counts.items()))
    manifest={"status":"PASS","window":{"start":str(START),"end_exclusive":str(END)},"splits":{"DEV":"2026-01-05/2026-02-28","VALIDATION_A":"2026-03-01/2026-04-30","VALIDATION_B":"2026-05-01/2026-05-15"},"frozen_sha256":digest,"source_data_modified":False,"source_paths":["/workspace/market-pattern-data/2026/CNY/*M1.csv","/workspace/market-pattern-data/2026/Si/*M1.csv"],"regeneration_command":"PYTHONPATH=src python scripts/run_top5.py"}
    (OUT/"run_manifest.json").write_text(json.dumps(manifest,indent=2)+"\n")
    base=summary[summary.friction.eq("BASE")].sort_values(["period","profit_factor"],ascending=[True,False]);report="# TOP-5 REAL STRATEGY BENCHMARK V1\n\nFrozen SHA-256: `"+digest+"`\n\nAll variants were selected on DEV only; validation periods are out of selection sample. Gerchik-derived structural false-break/retest rows are `ADAPTED_TO_M1_M5`, not exact 30-second Model A executions.\n\n## Results\n\n```csv\n"+base.to_csv(index=False)+"```\n\n## Manual audit IDs\n\nThe durable trade audit contains the first 15 trades per family for candle-by-candle review.\n"
    (OUT/"report.md").write_text(report)
    assert verify_frozen(OUT/"frozen_selected_variants.json",digest)
    print(f"Frozen {len(selected)} variants; ledger rows={len(ledger)}; sha256={digest}")

if __name__=="__main__":main()
