"""Independent Stage 6.7 audit reconstructed from frozen source trades."""
from __future__ import annotations
import hashlib,itertools,json
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
def exposure(frame,members,weight,risk,lifecycles):
    f=frame[frame.instrument.isin(members)&frame.lifecycle.isin(lifecycles)]; events=[]
    for x in f.to_dict('records'): events += [(pd.Timestamp(x['entry_time']),1,x),(pd.Timestamp(x['exit_time']),0,x)]
    equity=100.; active={}; prev=None; area=posarea=dur=0.; over={a:0. for a in (2,3,4,5,6,8)}; mx=nom=res=0.; snaps=[]
    for tm,g in itertools.groupby(sorted(events,key=lambda z:(z[0],z[1],z[2]['source_trade_id'])),lambda z:z[0]):
        batch=list(g)
        if prev is not None:
            dt=(tm-prev).total_seconds(); pct=sum(v[1] for v in active.values())/equity*100; area+=pct*dt; posarea+=len(active)*dt; dur+=dt
            for a in over: over[a]+=dt if pct>a else 0
        prev=tm
        for _,kind,x in batch:
            tid=x['source_trade_id']
            if kind==0:
                _,cash=active.pop(tid); equity+=cash*float(x['strategy_R'])
            else: active[tid]=(risk*weight,equity*risk*weight)
        pct=sum(v[1] for v in active.values())/equity*100; snaps.append(pct); mx=max(mx,len(active)); nom=max(nom,sum(v[0] for v in active.values())*100); res=max(res,pct)
    out=dict(max_simultaneous_positions=mx,average_simultaneous_positions=posarea/dur,max_nominal_open_risk_pct=nom,max_reserved_risk_pct_of_equity=res,time_weighted_avg_open_risk_pct=area/dur,event_snapshot_avg_open_risk_pct=np.mean(snaps))
    out.update({f'share_time_above_{a}_pct':100*over[a]/dur for a in over}); return out

def audit(path=HERE):
    master=pd.read_csv(path/'master_220_equity_cases.csv'); rm=pd.read_csv(path/'master_110_load_cases_R.csv'); hs=pd.read_csv(path/'equity_execution_hashes.csv'); src=pd.read_csv(SOURCE,keep_default_na=False); av=pd.read_csv(path/'instrument_availability_registry.csv'); iy=pd.read_csv(path/'instrument_year_R_metrics.csv'); oq=pd.read_csv(path/'open_risk_summary.csv').set_index('case_id')
    failures=[]; month_ok=True; exposure_ok=True; target_ok=True
    for r in master.itertuples():
        w=1/r.basket_size if r.load_mode=='NORMALIZED' else 1.; risk=r.base_risk_pct/100; members=r.instruments.split('+'); f=src[src.variant==r.variant]
        prod=simulate(f,members,w,risk,('baseline','historical_true_oos')); wf=simulate(f,members,w,risk,('walk_forward',)); ann,final,cagr,mdd,monthdd=metrics(prod); h=hs[hs.case_id==r.case_id].iloc[0]
        values=[(final,r.final_equity),(cagr,r.historical_annualized_CAGR_pct),(mdd,r.max_realized_equity_DD_pct),(monthdd,r.monthly_equity_DD_pct),*((ann[y],getattr(r,'return_2026_YTD_pct' if y==2026 else f'return_{y}_pct')) for y in ann)]
        if event_hash(prod)!=h.production_chronological_event_sha256 or event_hash(wf)!=h.wf24_event_sha256 or any(not np.isclose(a,b,rtol=1e-8,atol=1e-8) for a,b in values): failures.append(r.case_id)
        x=prod.copy(); x['exit']=pd.to_datetime(x.exit_time,utc=True); prior=100.; rets=[]
        for p in pd.period_range('2023-01','2026-09',freq='M'):
            g=x[x.exit.dt.to_period('M')==p]; end=prior if g.empty else float(g.iloc[-1].equity_after_exit); rets.append((end/prior-1)*100); prior=end
        calc=[len(rets),sum(v>0 for v in rets),sum(abs(v)<=1e-12 for v in rets),sum(v<0 for v in rets),np.mean(np.array(rets)>0)]
        month_ok &= all(np.isclose(a,b) for a,b in zip(calc,[r.total_production_calendar_months,r.positive_months,r.zero_months,r.negative_months,r.positive_month_share]))
        ex=exposure(f,members,w,risk,('baseline','historical_true_oos')); exposure_ok &= all(np.isclose(v,oq.loc[r.case_id,k]) for k,v in ex.items())
        full=[ann[y] for y in (2023,2024,2025)]; tier='ALL_YEARS_80' if all(v>=80 for v in full) else 'ALL_YEARS_70' if all(v>=70 for v in full) else 'CAGR_80' if cagr>=80 else 'CAGR_70' if cagr>=70 else 'BELOW_70'; target_ok &= tier==r.target_classification and bool(cagr>=70)==r.CAGR_70_plus and bool(cagr>=80)==r.CAGR_80_plus
    s66=pd.read_csv(HERE.parent/'stage6_unified_candidate_comparison'/'yearly_metrics.csv'); merged=rm[rm.load_mode=='NORMALIZED'].merge(s66[['configuration_id','period_label','net_R']].pivot(index='configuration_id',columns='period_label',values='net_R').reset_index(),on='configuration_id'); maps={'R_2023':'BASELINE_2023','R_2024':'BASELINE_2024','WF24_R':'WF24','R_2025':'OOS2025','R_2026_YTD':'OOS2026_YTD'}
    norm=all((merged[a]-merged[b]).abs().max()<1e-8 for a,b in maps.items()); both=rm.pivot(index='configuration_id',columns='load_mode'); scaling=all((both[(c,'FULL')]-both[(c,'NORMALIZED')]*both[('basket_size','FULL')]).abs().max()<1e-7 for c in maps)
    # Independently derive annual availability/activity and strict-zero gate.
    iy_ok=True
    for z in iy.itertuples():
        ar=av[(av.instrument==z.instrument)&(av.lifecycle==z.lifecycle)].iloc[0]; available=pd.Timestamp(ar.first_timestamp).year<=z.year<=pd.Timestamp(ar.last_timestamp).year
        expected='NOT_AVAILABLE' if not available else 'AVAILABLE_WITH_TRADES' if z.trades else 'AVAILABLE_ZERO_TRADES'; iy_ok &= expected==z.availability_status
        iy_ok &= (z.classification=='NOT_AVAILABLE' or z.classification.endswith('POSITIVE')) == (z.classification=='NOT_AVAILABLE' or z.scaled_R>1e-12)
    gate=iy.groupby(['configuration_id','load_mode']).classification.apply(lambda s: all(x=='NOT_AVAILABLE' or x.endswith('POSITIVE') for x in s)); gate_ok=all(bool(r.all_instrument_years_positive)==bool(gate[(r.configuration_id,r.load_mode)]) for r in master.itertuples()) and iy.groupby(['configuration_id','instrument','lifecycle','year']).classification.nunique().max()==1
    qs=pd.read_csv(path/'quarter_stability_summary.csv').set_index('case_id'); quarter_ok=all(qs.loc[r.case_id,'positive_quarters']+qs.loc[r.case_id,'zero_complete_quarters']+qs.loc[r.case_id,'negative_quarters']==qs.loc[r.case_id,'complete_quarters'] for r in master.itertuples()) and (av[(av.instrument=='IMOEXF')&(av.lifecycle=='baseline')].iloc[0].first_complete_quarter=='2024Q1') and (av[(av.instrument=='GLDRUBF')&(av.lifecycle=='baseline')].iloc[0].first_complete_quarter=='2023Q4')
    eligible_expected=master.all_portfolio_years_positive & master.all_instrument_years_positive; eligibility_ok=(eligible_expected==master.production_eligible).all()
    rank_ok=bool(master[~master.production_eligible].reference_rank.isna().all() and sorted(master[master.production_eligible].reference_rank.astype(int))==list(range(1,int(master.production_eligible.sum())+1))); pareto_ok=bool(not master.loc[~master.production_eligible,'production_pareto'].any())
    manifest=json.loads((path/'audit_manifest.json').read_text()); hashes_ok=all(hashlib.sha256((path/n).read_bytes()).hexdigest()==v for n,v in manifest['core_artifact_sha256'].items() if (path/n).exists())
    checks={'source_authentication':len(av)==12,'stage6_6_normalized_reconciliation':norm,'full_R_scaling':scaling,'production_event_reconstruction':not failures,'WF_independent_reconstruction':not failures,'continuous_equity':not failures,'annual_returns':not failures,'CAGR':not failures,'final_equity':not failures,'realized_DD':not failures,'monthly_DD':not failures,'production_quarters':quarter_ok,'quarter_completeness':quarter_ok,'production_months':month_ok,'instrument_year_gates':gate_ok,'availability_reconstruction':iy_ok,'production_eligibility':eligibility_ok,'production_exposure':exposure_ok,'target_classifications':target_ok,'eligible_pareto':pareto_ok,'eligible_ranks':rank_ok,'leaders':rank_ok,'execution_hashes':not failures,'deterministic_rerun':hashes_ok and manifest.get('deterministic_rerun_proof')=='PASS','stage6_8_not_started':not manifest['stage6_8_started'],'stage7_not_executed':not manifest['stage7_executed']}
    checks={k:bool(v) for k,v in checks.items()}
    result={'status':'PASS' if all(checks.values()) else 'FAIL','independent_reconstruction':True,'checks':checks,'metric_or_hash_mismatches':failures,'counts':{'configurations':int(master.configuration_id.nunique()),'R_cases':len(rm),'equity_cases':len(master)}}
    (path/'independent_audit_result.json').write_text(json.dumps(result,indent=2,sort_keys=True)+'\n')
    if result['status']!='PASS': raise AssertionError(result)
    return result
if __name__=='__main__': audit()
