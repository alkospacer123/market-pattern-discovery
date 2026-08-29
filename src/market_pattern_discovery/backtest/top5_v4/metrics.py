from __future__ import annotations
from typing import Any,Iterable
import math
import numpy as np
import pandas as pd
from .common import DEV_START,DEV_END,VAL_A_END,VALIDATION_END,SCENARIOS

def sample_tier(n):return "VERY_LOW" if n<20 else "LOW" if n<50 else "MODERATE" if n<100 else "BETTER"
def _pf(p):
    wins=p[p>0].sum();losses=-p[p<0].sum()
    if wins==0 and losses==0:return None
    if losses==0:return math.inf
    return float(wins/losses)
def realized_closed_trade_dd_bps(g):
    if g.empty:return 0.
    q=g.sort_values(["exit_time","trade_id"],kind="mergesort");eq=q.pnl_bps.astype(float).cumsum().to_numpy();peaks=np.maximum.accumulate(np.r_[0.,eq])[1:];return float(max(0.,np.max(peaks-eq)))
def metrics(ledger):
    if "pnl_bps" not in ledger.columns:raise ValueError("pnl_bps is mandatory")
    rows=[];group_cols=["candidate_id","family","submodel","instrument","friction"]+(["period"] if "period" in ledger else [])
    for key,g in ledger.groupby(group_cols,dropna=False,sort=False):
        p=g.pnl_bps.astype(float).to_numpy();row=dict(zip(group_cols,key if isinstance(key,tuple) else (key,)));row.update({"trades":len(g),"profit_factor":_pf(p),"expectancy_bps":float(np.mean(p)) if len(p) else None,"median_bps":float(np.median(p)) if len(p) else None,"win_rate":float(np.mean(p>0)) if len(p) else None,"realized_closed_trade_dd_bps":realized_closed_trade_dd_bps(g),"sample_tier":sample_tier(len(g))});rows.append(row)
    return pd.DataFrame(rows)
def pooled_single_leg_ledger(ledger):
    if ledger.empty:return ledger.copy()
    x=ledger[ledger.instrument.isin(["CNYRUBF","USDRUBF"])].copy();x["instrument"]="POOLED";return x
def registry_metrics(registry,ledger):
    all_ledgers=[ledger];pooled=pooled_single_leg_ledger(ledger)
    if not pooled.empty:all_ledgers.append(pooled)
    combined=pd.concat(all_ledgers,ignore_index=True) if all_ledgers else pd.DataFrame();m=metrics(combined) if not combined.empty else pd.DataFrame();rows=[]
    for c in registry:
        instruments=["CNYRUBF+USDRUBF"] if c["family"]=="PAIRS" else ["CNYRUBF","USDRUBF","POOLED"]
        for inst in instruments:
            for fr in SCENARIOS:
                g=m[(m.candidate_id==c["candidate_id"])&(m.instrument==inst)&(m.friction==fr)] if not m.empty else pd.DataFrame()
                if g.empty:rows.append({"candidate_id":c["candidate_id"],"family":c["family"],"submodel":c["submodel"],"instrument":inst,"friction":fr,"trades":0,"profit_factor":None,"expectancy_bps":None,"median_bps":None,"win_rate":None,"realized_closed_trade_dd_bps":0.,"sample_tier":"VERY_LOW","complexity":c["complexity"],"selection_eligible":c["selection_eligible"]})
                else:r=g.iloc[0].to_dict();r.update({"complexity":c["complexity"],"selection_eligible":c["selection_eligible"]});rows.append(r)
    return pd.DataFrame(rows)
def select_primaries(registry,metric_table):
    selected=[]
    for family in ("STRUCTURAL","ORB","TREND_PULLBACK","PAIRS","BOLLINGER_RSI"):
        scored=[]
        for c in [c for c in registry if c["family"]==family and c["selection_eligible"]]:
            inst="CNYRUBF+USDRUBF" if family=="PAIRS" else "POOLED";base=metric_table[(metric_table.candidate_id==c["candidate_id"])&(metric_table.instrument==inst)&(metric_table.friction=="BASE")];stress=metric_table[(metric_table.candidate_id==c["candidate_id"])&(metric_table.instrument==inst)&(metric_table.friction=="STRESS")]
            if base.empty or stress.empty:continue
            b=base.iloc[0];st=stress.iloc[0];pf=b.profit_factor;eligible=int(b.trades)>=20 and b.expectancy_bps is not None and b.expectancy_bps>0 and pf is not None and pf>1
            if not eligible:continue
            tier={"VERY_LOW":0,"LOW":1,"MODERATE":2,"BETTER":3}[b.sample_tier];scored.append({"candidate_id":c["candidate_id"],"family":family,"submodel":c["submodel"],"sample_tier_rank":tier,"base_pf":float(pf),"stress_pf":-math.inf if st.profit_factor is None else float(st.profit_factor),"base_expectancy_bps":float(b.expectancy_bps),"base_dd":float(b.realized_closed_trade_dd_bps),"complexity":c["complexity"]})
        if scored:selected.append(pd.DataFrame(scored).sort_values(["sample_tier_rank","base_pf","stress_pf","base_expectancy_bps","base_dd","complexity","candidate_id"],ascending=[False,False,False,False,True,True,True],kind="mergesort").iloc[0].to_dict())
    n=len(selected);status="NO_DEV_SURVIVOR" if n==0 else "DEV_SELECTION_COMPLETE" if n==5 else "PARTIAL_DEV_SURVIVORS";return pd.DataFrame(selected),status
def parameter_plateau_report(metric_table):
    cols=[c for c in ["candidate_id","family","submodel","instrument","friction","trades","profit_factor","expectancy_bps"] if c in metric_table];return metric_table[cols].copy().sort_values(cols[:5],kind="mergesort") if cols else pd.DataFrame()
def validation_status(a_base,b_base,combined_base,combined_stress):
    trades=int(combined_base["trades"]);pf=combined_base.get("profit_factor");ex=combined_base.get("expectancy_bps")
    if trades<10:return "INSUFFICIENT"
    if ex is None or ex<=0 or pf is None or pf<=1:return "REJECTED"
    robust=a_base.get("expectancy_bps") is not None and a_base["expectancy_bps"]>0 and b_base.get("expectancy_bps") is not None and b_base["expectancy_bps"]>0 and pf>1 and ex>0 and combined_stress.get("expectancy_bps") is not None and combined_stress["expectancy_bps"]>=0 and trades>=20
    return "ROBUST" if robust else "WEAK"
def assign_period(entry_time):
    t=pd.to_datetime(entry_time);out=pd.Series(index=t.index,dtype=object);out[(t>=DEV_START)&(t<DEV_END)]="DEV";out[(t>=DEV_END)&(t<VAL_A_END)]="VALIDATION_A";out[(t>=VAL_A_END)&(t<VALIDATION_END)]="VALIDATION_B";return out
def assert_oos(selection_end,evaluation_start):
    if pd.Timestamp(evaluation_start)<pd.Timestamp(selection_end):raise ValueError("evaluation overlaps parameter-selection period")
def future_prefix_equal(before,after,cutoff,time_col,compare_cols:Iterable[str]):
    a=before[before[time_col]<=cutoff].sort_values(time_col).reset_index(drop=True);b=after[after[time_col]<=cutoff].sort_values(time_col).reset_index(drop=True);return a[list(compare_cols)].equals(b[list(compare_cols)])
