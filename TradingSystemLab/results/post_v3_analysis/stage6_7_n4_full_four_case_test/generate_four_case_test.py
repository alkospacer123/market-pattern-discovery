"""Reproduce the Stage 6.7 N4/FULL focused comparison from frozen trades.

This is analysis, not selection: the four-case universe is an immutable constant.
Production is one baseline -> TRUE-OOS event stream; WF24 is reconstructed alone.
"""
from __future__ import annotations

import argparse, hashlib, json, math
from pathlib import Path
import numpy as np
import pandas as pd

HERE=Path(__file__).resolve().parent
S66=HERE.parent/'stage6_unified_candidate_comparison'
S67=HERE.parent/'stage6_7_full_vs_normalized'
LIFE=HERE.parent/'stage5_structural_validation/canonical_lifecycle_registry.csv'
SOURCE=S66/'portfolio_trade_scaling_registry.csv'
SYMS=('USDRUBF','CNYRUBF','GLDRUBF','IMOEXF'); VARS=('CANONICAL','TRAIL1'); RISKS=(('R15',.015),('R20',.02))
TOL=1e-9; RECON_TOL=5e-7; CORE=('four_case_registry.csv','availability_registry.csv','production_yearly_metrics.csv','production_quarterly_metrics.csv','production_monthly_metrics.csv','trade_metrics.csv','instrument_year_metrics.csv','instrument_summary.csv','direction_summary.csv','open_risk_summary.csv','wf24_summary.csv','wf24_open_risk_summary.csv','pairwise_comparison.csv','risk_efficiency_comparison.csv','headline_comparison.csv','reconciliation_with_stage6_7.csv')

def write(x,p): x.to_csv(p,index=False,lineterminator='\n',float_format='%.12g')
def sha(p): return hashlib.sha256(p.read_bytes()).hexdigest()
def streak(a, nonpositive=False):
    best=run=0
    for x in a:
        run=run+1 if (x<=TOL if nonpositive else x<-TOL) else 0; best=max(best,run)
    return best
def maxdd(a):
    x=np.array([100.,*a]); return float(np.min((x/np.maximum.accumulate(x)-1)*100))
def source():
    t=pd.read_csv(SOURCE,keep_default_na=False); t=t[t.variant.isin(VARS)&t.instrument.isin(SYMS)].copy()
    t['entry']=pd.to_datetime(t.entry_time,utc=True); t['exit']=pd.to_datetime(t.exit_time,utc=True); return t
def availability():
    a=pd.read_csv(LIFE); a=a[(a.generation=='v3_perpetual')&(a.strategy=='T3')&(a.timeframe=='H1')&a.instrument.isin(SYMS)].copy()
    return a[['lifecycle','fold_id','instrument','start_timestamp','end_timestamp','source_market_data_identity','cost_contract']].sort_values(['lifecycle','fold_id','instrument'],na_position='first')
def simulate(t,risk,lives):
    eq=100.; opened={}; rows=[]; events=[]
    for r in t[t.lifecycle.isin(lives)].itertuples():
        events += [(r.entry,1,r.source_trade_id,r),(r.exit,0,r.source_trade_id,r)]
    for tm,kind,tid,r in sorted(events,key=lambda z:(z[0],z[1],z[2])): # EXIT(0) before ENTRY(1)
        if kind: opened[tid]=(eq*risk,r)
        else:
            cash,rr=opened.pop(tid); eq+=cash*rr.strategy_R
            rows.append(dict(source_trade_id=tid,variant=rr.variant,instrument=rr.instrument,direction=rr.direction,lifecycle=rr.lifecycle,entry=rr.entry,exit=rr.exit,R=rr.strategy_R,risk_cash=cash,equity=eq))
    return pd.DataFrame(rows).sort_values(['exit','source_trade_id'],kind='mergesort').reset_index(drop=True)
def exposure(t,risk,lives):
    eq=100.; opened={}; events=[]; prev=None; dur=area=posarea=0.; above={x:0. for x in (2,3,4,5,6,8)}; snaps=[]; mx=mxnom=mxres=0.
    for r in t[t.lifecycle.isin(lives)].itertuples(): events += [(r.entry,1,r.source_trade_id,r),(r.exit,0,r.source_trade_id,r)]
    for tm,group in __import__('itertools').groupby(sorted(events,key=lambda z:(z[0],z[1],z[2])),lambda z:z[0]):
        batch=list(group)
        if prev is not None:
            dt=(tm-prev).total_seconds(); res=sum(v[0] for v in opened.values())/eq*100
            dur+=dt; area+=res*dt; posarea+=len(opened)*dt
            for x in above: above[x]+=dt*(res>x)
        prev=tm
        for _,kind,tid,r in batch:
            if kind: opened[tid]=(eq*risk,r)
            else:
                cash,rr=opened.pop(tid); eq+=cash*rr.strategy_R
        res=sum(v[0] for v in opened.values())/eq*100; snaps.append(res)
        mx=max(mx,len(opened)); mxnom=max(mxnom,len(opened)*risk*100); mxres=max(mxres,res)
    z=dict(max_simultaneous_positions=mx,average_simultaneous_positions=posarea/dur,max_nominal_open_risk_pct=mxnom,max_reserved_risk_pct_of_equity=mxres,time_weighted_avg_open_risk_pct=area/dur,event_snapshot_avg_open_risk_pct=np.mean(snaps))
    z.update({f'share_time_above_{x}_pct':100*above[x]/dur for x in above}); return z
def spine(e,freq,start,end):
    periods=pd.period_range(start,end,freq=freq); prior=100.; out=[]; grouped={p:g for p,g in e.groupby(e.exit.dt.to_period(freq))}
    for p in periods:
        g=grouped.get(p); endeq=prior if g is None else float(g.iloc[-1].equity); ret=(endeq/prior-1)*100
        out.append((p,len(g) if g is not None else 0,ret,endeq)); prior=endeq
    return out
def pf(x):
    win=x[x>0].sum(); loss=-x[x<0].sum(); return win/loss if loss else math.inf

def generate(out=HERE, determinism=None):
    out=Path(out); out.mkdir(parents=True,exist_ok=True); t=source(); av=availability(); write(av,out/'availability_registry.csv')
    registry=pd.DataFrame([dict(case_id=f'{v}__N4_01__FULL__{rn}',variant=v,basket='N4_01',load='FULL',risk=rn) for rn,_ in RISKS for v in VARS]); write(registry,out/'four_case_registry.csv')
    yearly=[]; monthly=[]; quarterly=[]; trades=[]; iyears=[]; isum=[]; dsum=[]; opens=[]; wfrows=[]; wfopens=[]; headlines=[]
    sims={}; wfs={}
    endpoint=pd.to_datetime(av[av.lifecycle=='historical_true_oos'].end_timestamp,utc=True).min(); endmonth=endpoint.to_period('M'); endquarter=endpoint.to_period('Q')
    for row in registry.itertuples():
        risk=dict(RISKS)[row.risk]; base=t[t.variant==row.variant].copy(); prod=simulate(base,risk,('baseline','historical_true_oos')); wf=simulate(base,risk,('walk_forward',)); sims[row.case_id]=prod; wfs[row.case_id]=wf
        ys={}
        prior=100.
        for y in (2023,2024,2025,2026):
            g=prod[prod.exit.dt.year==y]; endeq=prior if g.empty else g.iloc[-1].equity; ret=(endeq/prior-1)*100; prior=endeq; ys[y]=ret
            yearly.append(dict(case_id=row.case_id,year=y,return_pct=ret,trades=len(g),coverage_status='PARTIAL_N4_DIAGNOSTIC_YEAR' if y==2023 else ('YTD' if y==2026 else 'COMPLETE'),hard_gate_used=False))
        ms=spine(prod,'M','2023-01',endmonth); qs=spine(prod,'Q','2023Q1',endquarter)
        m24=[x for x in ms if x[0]>=pd.Period('2024-01','M')]; q24=[x for x in qs if x[0]>=pd.Period('2024Q1','Q')]
        for p,n,r,e in m24: monthly.append(dict(case_id=row.case_id,month=str(p),trades=n,return_pct=r,sign='POSITIVE' if r>TOL else 'NEGATIVE' if r<-TOL else 'ZERO',completeness='PARTIAL' if p==endmonth else 'FULL'))
        for p,n,r,e in q24: quarterly.append(dict(case_id=row.case_id,quarter=str(p),trades=n,return_pct=r,sign='POSITIVE' if r>TOL else 'NEGATIVE' if r<-TOL else 'ZERO',completeness='PARTIAL' if p==endquarter else 'COMPLETE'))
        start_eq=float(prod[prod.exit<pd.Timestamp('2024-01-01',tz='UTC')].iloc[-1].equity); p24=prod[prod.exit>=pd.Timestamp('2024-01-01',tz='UTC')].copy(); rebased=(p24.equity/start_eq*100).tolist(); total=rebased[-1]-100
        elapsed=(endpoint-pd.Timestamp('2024-01-01',tz='UTC')).total_seconds()/(365.2425*86400); cagr=((rebased[-1]/100)**(1/elapsed)-1)*100
        dd24=maxdd(rebased); fulldd=maxdd(prod.equity.tolist()); comp=(np.prod([1+ys[2024]/100,1+ys[2025]/100])**.5-1)*100
        wfret=float(wf.iloc[-1].equity-100); wfdd=maxdd(wf.equity.tolist()); qcomplete=[x[2] for x in q24 if x[0]!=endquarter]; mrets=[x[2] for x in m24]; month_eq=[x[3]/start_eq*100 for x in m24]
        peak=rebased[0]; peakday=p24.iloc[0].exit; longest=0.
        for e,dt in zip(rebased,p24.exit):
            if e>=peak-TOL: peak=e; peakday=dt
            else: longest=max(longest,(dt-peakday).total_seconds()/86400)
        roll6=[(month_eq[i]/month_eq[i-6]-1)*100 for i in range(6,len(month_eq))]; roll12=[(month_eq[i]/month_eq[i-12]-1)*100 for i in range(12,len(month_eq))]
        h=dict(case_id=row.case_id,variant=row.variant,risk=row.risk,return_2023_pct=ys[2023],coverage_2023='PARTIAL_N4_DIAGNOSTIC_YEAR',return_2024_pct=ys[2024],WF24_return_pct=wfret,return_2025_pct=ys[2025],return_2026_YTD_pct=ys[2026],CAGR_2024_plus_pct=cagr,completed_years_CAGR_pct=comp,minimum_complete_year_return_pct=min(ys[2024],ys[2025]),median_complete_year_return_pct=np.median([ys[2024],ys[2025]]),compounded_return_2024_plus_pct=total,final_rebased_equity=rebased[-1],continuous_full_history_final_equity=prod.iloc[-1].equity,full_history_CAGR_pct=((prod.iloc[-1].equity/100)**(1/((prod.iloc[-1].exit-prod.iloc[0].entry).total_seconds()/(365.2425*86400)))-1)*100,max_realized_equity_DD_2024_plus_pct=dd24,full_history_max_DD_pct=fulldd,monthly_equity_DD_pct=maxdd(month_eq),recovery_factor=total/abs(dd24),longest_drawdown_days=longest,worst_rolling_12M_pct=min(roll12),worst_rolling_6M_pct=min(roll6),complete_quarters=len(qcomplete),partial_quarters=1,positive_complete_quarters=sum(x>TOL for x in qcomplete),zero_complete_quarters=sum(abs(x)<=TOL for x in qcomplete),negative_complete_quarters=sum(x<-TOL for x in qcomplete),positive_quarter_share=sum(x>TOL for x in qcomplete)/len(qcomplete),worst_complete_quarter_pct=min(qcomplete),best_complete_quarter_pct=max(qcomplete),median_complete_quarter_pct=np.median(qcomplete),mean_complete_quarter_pct=np.mean(qcomplete),longest_negative_quarter_streak=streak(qcomplete),longest_nonpositive_quarter_streak=streak(qcomplete,True),total_months=len(mrets),full_months=len(mrets)-1,partial_months=1,positive_months=sum(x>TOL for x in mrets),zero_months=sum(abs(x)<=TOL for x in mrets),negative_months=sum(x<-TOL for x in mrets),positive_month_share=sum(x>TOL for x in mrets)/len(mrets),zero_month_share=sum(abs(x)<=TOL for x in mrets)/len(mrets),negative_month_share=sum(x<-TOL for x in mrets)/len(mrets),nonpositive_month_share=sum(x<=TOL for x in mrets)/len(mrets),worst_month_pct=min(mrets),best_month_pct=max(mrets),mean_month_pct=np.mean(mrets),median_month_pct=np.median(mrets),monthly_std_pct=np.std(mrets),longest_negative_month_streak=streak(mrets),longest_nonpositive_month_streak=streak(mrets,True))
        ex=exposure(base,risk,('baseline','historical_true_oos')); opens.append(dict(case_id=row.case_id,**ex)); wfex=exposure(base,risk,('walk_forward',)); wfopens.append(dict(case_id=row.case_id,**wfex)); h.update(ex); headlines.append(h)
        wfrows.append(dict(case_id=row.case_id,return_pct=wfret,max_DD_pct=wfdd,trades=len(wf)))
        for life,label in [(('baseline','historical_true_oos'),'production'),(('walk_forward',),'WF24')]:
            g=base[base.lifecycle.isin(life)]; rr=g.strategy_R
            if label=='production':
                trades.append(dict(variant=row.variant,trades_2023=sum((g.exit.dt.year==2023)&(g.lifecycle=='baseline')),trades_2024=sum((g.exit.dt.year==2024)&(g.lifecycle=='baseline')),WF24_trades=sum(base.lifecycle=='walk_forward'),trades_2025=sum(g.exit.dt.year==2025),trades_2026_YTD=sum(g.exit.dt.year==2026),total_production_trades_2024_plus=sum(g.exit.dt.year>=2024),total_full_history_production_trades=len(g),PF=pf(rr),expectancy_R=rr.mean(),win_rate=(rr>0).mean(),median_trade_R=rr.median(),average_holding_hours=((g.exit-g.entry).dt.total_seconds()/3600).mean(),MAE='NOT_AVAILABLE',MFE='NOT_AVAILABLE'))
        for direction,g in base[base.lifecycle.isin(('baseline','historical_true_oos'))].groupby('direction'): dsum.append(dict(variant=row.variant,direction=direction,trades=len(g),net_R=g.strategy_R.sum()))
        for s,g in base[base.lifecycle.isin(('baseline','historical_true_oos'))].groupby('instrument'):
            vals={y:g[g.exit.dt.year==y].strategy_R.sum() for y in (2023,2024,2025,2026)}; totalr=sum(vals[y] for y in (2024,2025,2026))
            for y in (2023,2024,2025,2026): iyears.append(dict(variant=row.variant,instrument=s,year=y,net_R=vals[y],trades=sum(g.exit.dt.year==y),diagnostic_only=True))
            isum.append(dict(variant=row.variant,instrument=s,R_2023=vals[2023],R_2024=vals[2024],R_2025=vals[2025],R_2026_YTD=vals[2026],total_2024_plus_R=totalr,trade_count=len(g),PF=pf(g.strategy_R),expectancy_R=g.strategy_R.mean(),win_rate=(g.strategy_R>0).mean(),contribution_share=totalr/base[(base.lifecycle.isin(('baseline','historical_true_oos')))&(base.exit.dt.year>=2024)].strategy_R.sum(),contribution_sign='POSITIVE' if totalr>0 else 'NEGATIVE'))
    # variant-level diagnostics do not vary by risk
    tm=pd.DataFrame(trades).drop_duplicates('variant'); iy=pd.DataFrame(iyears).drop_duplicates(['variant','instrument','year']); ins=pd.DataFrame(isum).drop_duplicates(['variant','instrument']); ds=pd.DataFrame(dsum).drop_duplicates(['variant','direction'])
    H=pd.DataFrame(headlines); O=pd.DataFrame(opens); W=pd.DataFrame(wfrows)
    pairs=[]
    specs=[('TRAIL1_vs_CANONICAL_R15','TRAIL1__N4_01__FULL__R15','CANONICAL__N4_01__FULL__R15'),('TRAIL1_vs_CANONICAL_R20','TRAIL1__N4_01__FULL__R20','CANONICAL__N4_01__FULL__R20'),('R20_vs_R15_CANONICAL','CANONICAL__N4_01__FULL__R20','CANONICAL__N4_01__FULL__R15'),('R20_vs_R15_TRAIL1','TRAIL1__N4_01__FULL__R20','TRAIL1__N4_01__FULL__R15')]
    metrics=['return_2024_pct','WF24_return_pct','return_2025_pct','return_2026_YTD_pct','CAGR_2024_plus_pct','max_realized_equity_DD_2024_plus_pct','recovery_factor','positive_complete_quarters','worst_complete_quarter_pct','positive_months','worst_month_pct','max_nominal_open_risk_pct','time_weighted_avg_open_risk_pct']
    for name,a,b in specs:
        aa=H.set_index('case_id').loc[a]; bb=H.set_index('case_id').loc[b]
        for m in metrics: pairs.append(dict(comparison=name,left_case=a,right_case=b,metric=m,left_value=aa[m],right_value=bb[m],delta=aa[m]-bb[m]))
    eff=[]
    for r in H.itertuples(): eff.append(dict(case_id=r.case_id,CAGR_to_abs_MaxDD=r.CAGR_2024_plus_pct/abs(r.max_realized_equity_DD_2024_plus_pct),total_return_to_abs_MaxDD=r.compounded_return_2024_plus_pct/abs(r.max_realized_equity_DD_2024_plus_pct),recovery=r.recovery_factor,CAGR_per_1pct_max_nominal_risk=r.CAGR_2024_plus_pct/r.max_nominal_open_risk_pct,CAGR_per_1pct_time_weighted_open_risk=r.CAGR_2024_plus_pct/r.time_weighted_avg_open_risk_pct))
    E=pd.DataFrame(eff)
    for v in VARS:
        a=H.set_index('case_id').loc[f'{v}__N4_01__FULL__R15']; b=H.set_index('case_id').loc[f'{v}__N4_01__FULL__R20']; mask=E.case_id.str.startswith(v)
        E.loc[mask,'incremental_CAGR_R20_minus_R15']=b.CAGR_2024_plus_pct-a.CAGR_2024_plus_pct; E.loc[mask,'incremental_DD_R20_minus_R15']=abs(b.max_realized_equity_DD_2024_plus_pct)-abs(a.max_realized_equity_DD_2024_plus_pct); E.loc[mask,'incremental_CAGR_per_incremental_DD']=E.loc[mask,'incremental_CAGR_R20_minus_R15']/E.loc[mask,'incremental_DD_R20_minus_R15']
    # Existing Stage 6.7 is only a reconciliation control.
    old=pd.read_csv(S67/'master_220_equity_cases.csv').set_index('case_id'); rec=[]
    mapping={'return_2023_pct':'return_2023_pct','return_2024_pct':'return_2024_pct','WF24_return_pct':'WF24_return_pct','return_2025_pct':'return_2025_pct','return_2026_YTD_pct':'return_2026_YTD_pct','full_history_CAGR_pct':'historical_annualized_CAGR_pct','full_history_max_DD_pct':'max_realized_equity_DD_pct'}
    for r in H.itertuples():
        for new,oldcol in mapping.items():
            expected=float(old.loc[r.case_id,oldcol]); actual=float(getattr(r,new)); rec.append(dict(case_id=r.case_id,metric=new,reconstructed=actual,stage6_7_control=expected,absolute_delta=abs(actual-expected),pass_tolerance=abs(actual-expected)<=RECON_TOL))
    R=pd.DataFrame(rec); assert R.pass_tolerance.all(),R[~R.pass_tolerance]
    outputs={'production_yearly_metrics.csv':pd.DataFrame(yearly),'production_quarterly_metrics.csv':pd.DataFrame(quarterly),'production_monthly_metrics.csv':pd.DataFrame(monthly),'trade_metrics.csv':tm,'instrument_year_metrics.csv':iy,'instrument_summary.csv':ins,'direction_summary.csv':ds,'open_risk_summary.csv':O,'wf24_summary.csv':W,'wf24_open_risk_summary.csv':pd.DataFrame(wfopens),'pairwise_comparison.csv':pd.DataFrame(pairs),'risk_efficiency_comparison.csv':E,'headline_comparison.csv':H,'reconciliation_with_stage6_7.csv':R}
    for n,d in outputs.items(): write(d,out/n)
    leaders={'return':H.loc[H.CAGR_2024_plus_pct.idxmax(),'case_id'],'drawdown':H.loc[H.max_realized_equity_DD_2024_plus_pct.abs().idxmin(),'case_id'],'quarter_stability':H.sort_values(['positive_quarter_share','worst_complete_quarter_pct','longest_negative_quarter_streak','case_id'],ascending=[False,False,True,True]).iloc[0].case_id,'month_stability':H.sort_values(['positive_month_share','worst_month_pct','longest_negative_month_streak','case_id'],ascending=[False,False,True,True]).iloc[0].case_id,'recovery':H.loc[H.recovery_factor.idxmax(),'case_id'],'risk_efficiency':E.loc[E.CAGR_to_abs_MaxDD.idxmax(),'case_id'],'oos_2025':H.loc[H.return_2025_pct.idxmax(),'case_id'],'ytd_2026':H.loc[H.return_2026_YTD_pct.idxmax(),'case_id']}
    report(out,H,E,leaders,endpoint)
    hashes={n:sha(out/n) for n in CORE}; manifest=dict(status='PASS',source=str(SOURCE),availability_source=str(LIFE),comparison_tolerance=TOL,event_order='timestamp; EXIT before ENTRY; source_trade_id',latest_authenticated_endpoint=endpoint.isoformat(),case_count=4,determinism=determinism or {'runs':1,'status':'PENDING_EXTERNAL_RERUN'},artifacts={n:{'sha256':hashes[n],'rows':sum(1 for _ in open(out/n,encoding='utf8'))-1 if n.endswith('.csv') else None} for n in CORE})
    (out/'audit_manifest.json').write_text(json.dumps(manifest,indent=2,sort_keys=True)+'\n'); return hashes

def report(out,H,E,L,endpoint):
    ix=H.set_index('case_id'); lines=['# Stage 6.7 N4 FULL — focused four-case test','','**Status: `STAGE_6_7_N4_FULL_FOUR_CASE_TEST_COMPLETE`**','','## Contract',f'- Frozen equality tolerance: `{TOL}`.','- Exactly N4_01 / FULL / CANONICAL+TRAIL1 / R15+R20; no optimizer or annual sign gate.','- 2023 is retained as `PARTIAL_N4_DIAGNOSTIC_YEAR`; headline window is 2024 through '+endpoint.isoformat()+'.','- Production is continuous baseline → historical TRUE OOS and merely rebased at 2024; WF24 is isolated.','- Same-time events use EXIT before ENTRY. Stage 6.8 is NOT STARTED; Stage 7 is NOT EXECUTED.','','## Headline metrics',H[['case_id','return_2024_pct','WF24_return_pct','return_2025_pct','return_2026_YTD_pct','CAGR_2024_plus_pct','compounded_return_2024_plus_pct','max_realized_equity_DD_2024_plus_pct','recovery_factor','positive_quarter_share','positive_month_share']].to_markdown(index=False,floatfmt='.6f'),'','## Direct answers',f"1. **R15:** TRAIL1 has the higher CAGR ({ix.loc['TRAIL1__N4_01__FULL__R15','CAGR_2024_plus_pct']:.3f}% vs {ix.loc['CANONICAL__N4_01__FULL__R15','CAGR_2024_plus_pct']:.3f}%), with a larger drawdown.",f"2. **R20:** TRAIL1 has the higher CAGR ({ix.loc['TRAIL1__N4_01__FULL__R20','CAGR_2024_plus_pct']:.3f}% vs {ix.loc['CANONICAL__N4_01__FULL__R20','CAGR_2024_plus_pct']:.3f}%), with a larger drawdown."]
    for v in VARS:
        a=ix.loc[f'{v}__N4_01__FULL__R15']; b=ix.loc[f'{v}__N4_01__FULL__R20']; lines.append(f"3–4. **{v} R20 vs R15:** compounded return {b.compounded_return_2024_plus_pct-a.compounded_return_2024_plus_pct:+.3f} pp, CAGR {b.CAGR_2024_plus_pct-a.CAGR_2024_plus_pct:+.3f} pp, absolute DD {abs(b.max_realized_equity_DD_2024_plus_pct)-abs(a.max_realized_equity_DD_2024_plus_pct):+.3f} pp, max nominal exposure {b.max_nominal_open_risk_pct-a.max_nominal_open_risk_pct:+.3f} pp.")
    lines += ['', '5. **Leaders:** '+ '; '.join(f'{k}: `{v}`' for k,v in L.items())+'.','6. TRAIL1 provides economically material extra return/CAGR at both risks, but not for free: drawdown rises; this is a trade-off rather than dominance.','7. R20 adds substantial return and also drawdown/exposure. Incremental CAGR/DD is reported explicitly; whether it compensates is a risk-budget decision, not an optimizer verdict.','8. Removing the partial-2023 sign gate keeps all four cases visible and moves the headline to comparable 2024+ history; it does not alter any frozen trade.','9. **Transparent production-consideration view:** TRAIL1 R15 is the more balanced growth/risk profile when return and risk efficiency are considered together; CANONICAL R15 remains the minimum-DD choice, while both R20 profiles require accepting the documented 8% nominal ceiling. No composite score was used.','','## Provenance and limitations','MAE/MFE are unavailable in the frozen registry. Trade statistics are variant-level because risk changes sizing, not the trade path. Instrument-year signs are diagnostic only. Transaction costs are inherited from frozen Stage 6.6 strategy-R evidence and the lifecycle `C1` contract; no trades or strategy parameters were changed.','']
    (out/'FINAL_N4_FULL_FOUR_CASE_REPORT.md').write_text('\n'.join(lines))

if __name__=='__main__':
    p=argparse.ArgumentParser(); p.add_argument('--output',type=Path,default=HERE); a=p.parse_args(); generate(a.output)
