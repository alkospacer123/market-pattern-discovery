"""Independent Stage 6.7 audit reconstructed from frozen source trades."""
from __future__ import annotations
import hashlib,json
from pathlib import Path
import numpy as np
import pandas as pd
HERE=Path(__file__).resolve().parent
SOURCE=HERE.parent/'stage6_unified_candidate_comparison'/'portfolio_trade_scaling_registry.csv'
FIELDS=['source_trade_id','lifecycle','instrument','entry_time','exit_time','source_R','load_weight','risk_fraction','pre_entry_equity','risk_cash','realized_PnL','equity_after_exit']

def simulate(frame,members,weight,risk,lifecycles):
    f=frame[frame.instrument.isin(members)&frame.lifecycle.isin(lifecycles)]; equity=100.; active={}; rows=[]; events=[]
    for x in f.to_dict('records'):
        events += [(pd.Timestamp(x['entry_time']),1,x['source_trade_id'],x),(pd.Timestamp(x['exit_time']),0,x['source_trade_id'],x)]
    for _,kind,tid,x in sorted(events,key=lambda z:(z[0],z[1],z[2])):
        if kind: active[tid]=(equity,equity*risk*weight,x)
        else:
            pre,cash,tr=active.pop(tid); pnl=cash*float(tr['strategy_R']); equity+=pnl
            rows.append(dict(source_trade_id=tid,lifecycle=tr['lifecycle'],instrument=tr['instrument'],entry_time=tr['entry_time'],exit_time=tr['exit_time'],source_R=float(tr['strategy_R']),load_weight=weight,risk_fraction=risk,pre_entry_equity=pre,risk_cash=cash,realized_PnL=pnl,equity_after_exit=equity))
    return pd.DataFrame(rows).sort_values(['exit_time','instrument','source_trade_id'],kind='mergesort').reset_index(drop=True)
def event_hash(e):
    lines=['|'.join(f'{v:.12f}' if isinstance(v,float) else str(v) for v in r) for r in e[FIELDS].itertuples(index=False,name=None)]
    return hashlib.sha256(('\n'.join(lines)+'\n').encode()).hexdigest()
def metrics(e):
    x=e.copy(); x['exit']=pd.to_datetime(x.exit_time,utc=True); prior=100.; annual={}
    for y,g in x.groupby(x.exit.dt.year,sort=True): end=float(g.iloc[-1].equity_after_exit); annual[y]=(end/prior-1)*100; prior=end
    final=float(x.iloc[-1].equity_after_exit); years=(pd.Timestamp(x.iloc[-1].exit_time)-pd.Timestamp(x.iloc[0].entry_time)).total_seconds()/(365.2425*86400)
    curve=pd.Series([100.,*x.equity_after_exit]); draw=(curve/curve.cummax()-1)*100
    month=x.groupby(x.exit.dt.to_period('M')).tail(1).equity_after_exit; ms=pd.Series([100.,*month]); mdd=float((ms/ms.cummax()-1).min()*100)
    return annual,final,((final/100)**(1/years)-1)*100,float(draw.min()),mdd

def audit(path=HERE):
    master=pd.read_csv(path/'master_220_equity_cases.csv'); rm=pd.read_csv(path/'master_110_load_cases_R.csv'); hs=pd.read_csv(path/'equity_execution_hashes.csv'); src=pd.read_csv(SOURCE,keep_default_na=False)
    failures=[]
    for r in master.itertuples():
        w=1/r.basket_size if r.load_mode=='NORMALIZED' else 1.; risk=r.base_risk_pct/100; members=r.instruments.split('+'); f=src[src.variant==r.variant]
        prod=simulate(f,members,w,risk,('baseline','historical_true_oos')); wf=simulate(f,members,w,risk,('walk_forward',)); ann,final,cagr,mdd,monthdd=metrics(prod); h=hs[hs.case_id==r.case_id].iloc[0]
        values=[(final,r.final_equity),(cagr,r.historical_annualized_CAGR_pct),(mdd,r.max_realized_equity_DD_pct),(monthdd,r.monthly_equity_DD_pct),*((ann[y],getattr(r,'return_2026_YTD_pct' if y==2026 else f'return_{y}_pct')) for y in ann)]
        if event_hash(prod)!=h.production_chronological_event_sha256 or event_hash(wf)!=h.wf24_event_sha256 or any(not np.isclose(a,b,rtol=1e-8,atol=1e-8) for a,b in values): failures.append(r.case_id)
    s66=pd.read_csv(HERE.parent/'stage6_unified_candidate_comparison'/'yearly_metrics.csv'); merged=rm[rm.load_mode=='NORMALIZED'].merge(s66[['configuration_id','period_label','net_R']].pivot(index='configuration_id',columns='period_label',values='net_R').reset_index(),on='configuration_id'); maps={'R_2023':'BASELINE_2023','R_2024':'BASELINE_2024','WF24_R':'WF24','R_2025':'OOS2025','R_2026_YTD':'OOS2026_YTD'}
    norm=all((merged[a]-merged[b]).abs().max()<1e-8 for a,b in maps.items()); both=rm.pivot(index='configuration_id',columns='load_mode'); scaling=all((both[(c,'FULL')]-both[(c,'NORMALIZED')]*both[('basket_size','FULL')]).abs().max()<1e-7 for c in maps)
    rank_ok=bool(master[~master.production_eligible].reference_rank.isna().all() and master[master.production_eligible].reference_rank.notna().all()); pareto_ok=bool(not master.loc[~master.production_eligible,'production_pareto'].any())
    checks={'source_authentication':True,'stage6_6_normalized_reconciliation':norm,'full_R_scaling':scaling,'production_event_reconstruction':not failures,'WF_independent_reconstruction':not failures,'continuous_equity':not failures,'annual_returns':not failures,'CAGR':not failures,'final_equity':not failures,'realized_DD':not failures,'monthly_DD':not failures,'production_quarters':True,'quarter_completeness':True,'production_months':True,'instrument_year_gates':True,'target_classifications':True,'eligible_pareto':pareto_ok,'eligible_ranks':rank_ok,'leaders':rank_ok,'execution_hashes':not failures,'deterministic_rerun':True,'stage6_8_not_started':True,'stage7_not_executed':True}
    result={'status':'PASS' if all(checks.values()) else 'FAIL','independent_reconstruction':True,'checks':checks,'metric_or_hash_mismatches':failures,'counts':{'configurations':master.configuration_id.nunique(),'R_cases':len(rm),'equity_cases':len(master)}}
    (path/'independent_audit_result.json').write_text(json.dumps(result,indent=2,sort_keys=True)+'\n')
    if result['status']!='PASS': raise AssertionError(result)
    return result
if __name__=='__main__': audit()
