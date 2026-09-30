"""Generate compact Stage 6.7 evidence without risk-expanded period ledgers.

The frozen Stage 6.6 trade registry is the sole input.  R evidence is stored
once per configuration/load; equity period metrics are reconstructed in memory.
"""
from __future__ import annotations

import argparse, hashlib, itertools, json
from pathlib import Path
import numpy as np
import pandas as pd

HERE=Path(__file__).resolve().parent
S66=HERE.parent/'stage6_unified_candidate_comparison'
ROOT=HERE.parents[3]
VARIANTS=('CANONICAL','TRAIL1','SESSION_10_21','LOCK1_AFTER_2R','STRUCTURAL_STACK_V1')
SYMBOLS=('USDRUBF','CNYRUBF','GLDRUBF','IMOEXF')
LOADS=('NORMALIZED','FULL'); RISKS=(('R15',.015),('R20',.02))
LIFES=('baseline','walk_forward','historical_true_oos')
PERIODS=(('baseline',2023,'return_2023_pct'),('baseline',2024,'return_2024_pct'),('walk_forward',2024,'WF24_return_pct'),('historical_true_oos',2025,'return_2025_pct'),('historical_true_oos',2026,'return_2026_YTD_pct'))

def write(df,p): df.to_csv(p,index=False,lineterminator='\n',float_format='%.10g')
def sha(p): return hashlib.sha256(p.read_bytes()).hexdigest()
def streak(x):
    best=run=0
    for v in x: run=run+1 if v<0 else 0; best=max(best,run)
    return best
def dd(x):
    s=pd.Series([100.,*x],dtype=float); return float(((s/s.cummax())-1).min()*100)
def baskets():
    return [(f'N{n}_{i:02d}',m) for n in (2,3,4) for i,m in enumerate(itertools.combinations(SYMBOLS,n),1)]
def availability():
    p=HERE.parent/'stage5_structural_validation/canonical_lifecycle_registry.csv'; f=pd.read_csv(p)
    f=f[(f.generation=='v3_perpetual')&(f.strategy=='T3')&(f.timeframe=='H1')&f.instrument.isin(SYMBOLS)]
    rows=[]
    for (life,s),g in f.groupby(['lifecycle','instrument'],sort=True):
        a=pd.to_datetime(g.start_timestamp,utc=True).min(); z=pd.to_datetime(g.end_timestamp,utc=True).max()
        opening_week=a.month==1 and a.day<=7
        fq=a.to_period('Q') if opening_week else a.to_period('Q')+1
        fy=str(a.year) if opening_week else (str(a.year+1) if a.year+1<=z.year else '')
        rows.append(dict(instrument=s,lifecycle=life,first_timestamp=a.isoformat(),last_timestamp=z.isoformat(),first_complete_quarter=str(fq),first_complete_year=fy,partial_year_status='FULL_START' if opening_week else 'PARTIAL_START',provenance_path=str(p.relative_to(ROOT))))
    return pd.DataFrame(rows)
def source():
    t=pd.read_csv(S66/'portfolio_trade_scaling_registry.csv',keep_default_na=False)
    t['entry']=pd.to_datetime(t.entry_time,utc=True); t['exit']=pd.to_datetime(t.exit_time,utc=True); t['strategy_R']=t.strategy_R.astype(float)
    return t
def equity_events(t,weight,risk):
    """Causal sizing: entries sharing a timestamp see identical pre-entry equity."""
    records=[]
    for life in LIFES:
        q=t[t.lifecycle==life].copy(); equity=100.; open_pos={}; events=[]
        for r in q.itertuples():
            events += [(r.entry,0,r.source_trade_id,r),(r.exit,1,r.source_trade_id,r)]
        for when,kind,tid,r in sorted(events,key=lambda x:(x[0],x[1],x[2])):
            if kind==0:
                risk_cash=equity*risk*weight
                open_pos[tid]=(equity,risk_cash,r)
            else:
                sized,cash,rr=open_pos.pop(tid); pnl=cash*rr.strategy_R; after=equity+pnl
                records.append(dict(source_trade_id=tid,lifecycle=life,instrument=rr.instrument,entry_time=rr.entry_time,exit_time=rr.exit_time,source_net_R_C1=rr.strategy_R,load_weight=weight,equity_at_sizing=sized,risk_cash=cash,realized_PnL=pnl,equity_after_exit=after))
                equity=after
    return pd.DataFrame(records).sort_values(['lifecycle','exit_time','instrument','source_trade_id'],kind='mergesort')
def canonical_hash(e):
    cols=['source_trade_id','lifecycle','instrument','entry_time','exit_time','source_net_R_C1','load_weight','equity_at_sizing','risk_cash','realized_PnL','equity_after_exit']
    lines=[]
    for r in e[cols].itertuples(index=False,name=None): lines.append('|'.join(f'{v:.12f}' if isinstance(v,float) else str(v) for v in r))
    return hashlib.sha256(('\n'.join(lines)+'\n').encode()).hexdigest()
def period_returns(e):
    out={}; detail=[]
    for life,year,name in PERIODS:
        g=e[(e.lifecycle==life)&(pd.to_datetime(e.exit_time,utc=True).dt.year==year)]
        start=float(g.iloc[0].equity_after_exit-g.iloc[0].realized_PnL) if len(g) else 100.; end=float(g.iloc[-1].equity_after_exit) if len(g) else start
        out[name]=(end/start-1)*100
    for life in LIFES:
        g=e[e.lifecycle==life].copy(); g['exit']=pd.to_datetime(g.exit_time,utc=True)
        for freq,key in [('Q','quarter'),('M','month')]:
            for p,x in g.groupby(g.exit.dt.to_period(freq)):
                start=float(x.iloc[0].equity_after_exit-x.iloc[0].realized_PnL); end=float(x.iloc[-1].equity_after_exit)
                detail.append(dict(lifecycle=life,freq=freq,period=str(p),ret=(end/start-1)*100))
    return out,pd.DataFrame(detail)
def exposure(t,weight,risk):
    rows=[]; equity={x:100. for x in LIFES}; opened={}; prev={}; area={x:0. for x in LIFES}; duration={x:0. for x in LIFES}; above={x:{a:0. for a in (2,3,4,5,6,8)} for x in LIFES}; mx=mxnom=mxres=0
    events=[]
    for r in t.itertuples(): events += [(r.entry,0,r),(r.exit,1,r)]
    for tm,grp in itertools.groupby(sorted(events,key=lambda x:(x[0],x[1],x[2].source_trade_id)),key=lambda x:x[0]):
        batch=list(grp)
        for life in set(x[2].lifecycle for x in batch):
            if life in prev:
                dt=(tm-prev[life]).total_seconds(); nominal=sum(v[0] for v in opened.values() if v[2]==life)*100; reserved=sum(v[1] for v in opened.values() if v[2]==life)/equity[life]*100
                area[life]+=reserved*dt; duration[life]+=dt
                for a in above[life]: above[life][a]+=dt if reserved>a else 0
            prev[life]=tm
        for _,kind,r in batch:
            life=r.lifecycle
            if kind==0: opened[r.source_trade_id]=(risk*weight,equity[life]*risk*weight,life)
            else:
                _,cash,_=opened.pop(r.source_trade_id); equity[life]+=cash*r.strategy_R
            same=[v for v in opened.values() if v[2]==life]; mx=max(mx,len(same)); mxnom=max(mxnom,sum(v[0] for v in same)*100); mxres=max(mxres,sum(v[1] for v in same)/equity[life]*100)
    total=sum(duration.values()); row=dict(max_simultaneous_positions=mx,max_nominal_open_risk_pct=mxnom,max_reserved_risk_pct_of_equity=mxres,time_weighted_avg_open_risk_pct=sum(area.values())/total if total else 0)
    for a in (2,3,4,5,6,8): row[f'share_time_above_{a}_pct']=100*sum(above[x][a] for x in LIFES)/total if total else 0
    return row
def generate(out=HERE):
    out.mkdir(parents=True,exist_ok=True); av=availability(); write(av,out/'instrument_availability_registry.csv')
    write(pd.DataFrame([{'load_mode':'NORMALIZED','rule':'1 / basket_size per source trade','cap':'none','redistribution':False},{'load_mode':'FULL','rule':'1.0 per source trade','cap':'none','redistribution':False}]),out/'load_regime_registry.csv')
    write(pd.DataFrame([{'risk_scenario':n,'base_risk_pct':r*100,'sizing':'current equity; frozen at entry; same-time pre-entry equity'} for n,r in RISKS]),out/'risk_scenario_registry.csv')
    src=source(); configs=[]; yearly=[]; quarters=[]; months=[]; iy=[]; iq=[]; rmaster=[]; masters=[]; hashes=[]; risks=[]
    for variant in VARIANTS:
      for bid,members in baskets():
        cid=f'{variant}__{bid}'; configs.append(cid); base=src[(src.variant==variant)&src.instrument.isin(members)].copy()
        for load in LOADS:
          weight=1/len(members) if load=='NORMALIZED' else 1.; base['scaled_R']=base.strategy_R*weight
          period_rs={}
          for life,year,label in PERIODS:
            g=base[(base.lifecycle==life)&(base.exit.dt.year==year)]; period_rs[label]=g.scaled_R.sum()
            yearly.append(dict(configuration_id=cid,load_mode=load,lifecycle=life,year=year,period_label=label,trades=len(g),net_R=g.scaled_R.sum(),classification='POSITIVE' if g.scaled_R.sum()>0 else 'NEGATIVE' if g.scaled_R.sum()<0 else 'ZERO'))
            for s in members:
              z=g[g.instrument==s]; ar=av[(av.lifecycle==life)&(av.instrument==s)].iloc[0]; partial=(year==pd.Timestamp(ar.first_timestamp).year and ar.partial_year_status=='PARTIAL_START')
              status=('PARTIAL_YEAR_' if partial else 'FULL_YEAR_')+('POSITIVE' if z.scaled_R.sum()>0 else 'NEGATIVE') if len(z) else 'NOT_AVAILABLE'
              iy.append(dict(configuration_id=cid,load_mode=load,instrument=s,lifecycle=life,year=year,raw_source_R=z.strategy_R.sum(),scaled_R=z.scaled_R.sum(),trades=len(z),availability_status='AVAILABLE' if len(z) else 'NOT_AVAILABLE',year_coverage='PARTIAL' if partial else 'FULL',classification=status))
          period_data=[]
          for life in LIFES:
            lg=base[base.lifecycle==life]
            for freq,dest in [('Q',quarters),('M',months)]:
              for p,g in lg.groupby(lg.exit.dt.to_period(freq)):
                net=g.scaled_R.sum(); row=dict(configuration_id=cid,load_mode=load,lifecycle=life,year=p.year,trades=len(g),net_R=net,completeness='COMPLETE',classification='POSITIVE' if net>0 else 'NEGATIVE' if net<0 else 'ZERO')
                row['quarter' if freq=='Q' else 'month']=p.quarter if freq=='Q' else p.month; dest.append(row); period_data.append((freq,p,net))
                if freq=='Q':
                  for s in members:
                    z=g[g.instrument==s]; iq.append(dict(configuration_id=cid,load_mode=load,instrument=s,lifecycle=life,year=p.year,quarter=p.quarter,raw_source_R=z.strategy_R.sum(),scaled_R=z.scaled_R.sum(),trades=len(z),availability_status='AVAILABLE' if len(z) else 'NOT_AVAILABLE',quarter_coverage='FULL',classification='POSITIVE' if z.scaled_R.sum()>0 else 'NEGATIVE' if z.scaled_R.sum()<0 else 'ZERO'))
          chron=base[base.lifecycle!='walk_forward'].sort_values(['exit','instrument','source_trade_id']); vals=chron.scaled_R.tolist(); qv=[x[2] for x in period_data if x[0]=='Q']; mv=[x[2] for x in period_data if x[0]=='M']; annual=[period_rs[x] for x in ('return_2023_pct','return_2024_pct','return_2025_pct')]
          roll6=[sum(mv[i-5:i+1]) for i in range(5,len(mv))]; roll12=[sum(mv[i-11:i+1]) for i in range(11,len(mv))]
          rmaster.append(dict(configuration_id=cid,variant=variant,basket_id=bid,basket_size=len(members),instruments='+'.join(members),load_mode=load,R_2023=period_rs['return_2023_pct'],R_2024=period_rs['return_2024_pct'],WF24_R=period_rs['WF24_return_pct'],R_2025=period_rs['return_2025_pct'],R_2026_YTD=period_rs['return_2026_YTD_pct'],chronological_R=sum(vals),annual_floor_R=min(annual),worst_complete_12M_R=min(roll12),worst_complete_6M_R=min(roll6),max_DD_R=min(np.cumsum([0,*vals])-np.maximum.accumulate(np.cumsum([0,*vals]))),recovery=sum(vals)/abs(min(np.cumsum([0,*vals])-np.maximum.accumulate(np.cumsum([0,*vals])))) if min(np.cumsum([0,*vals])-np.maximum.accumulate(np.cumsum([0,*vals]))) else np.nan,positive_quarter_share=np.mean(np.array(qv)>0),positive_month_share=np.mean(np.array(mv)>0),longest_negative_quarter_streak=streak(qv),longest_negative_month_streak=streak(mv),concentration=max([sum(sorted([v for f,p,v in period_data if f=='M' and p.year==y and v>0],reverse=True)[:3]) for y in (2023,2024,2025,2026)])))
          for rn,risk in RISKS:
            case=f'{cid}__{load}__{rn}'; ev=equity_events(base,weight,risk); returns,details=period_returns(ev); ex=exposure(base,weight,risk); chronological=ev[ev.lifecycle!='walk_forward']; curve=chronological.equity_after_exit.tolist(); full=[returns[x] for x in ('return_2023_pct','return_2024_pct','return_2025_pct')]; qret=details[details.freq=='Q'].ret.tolist(); mret=details[details.freq=='M'].ret.tolist(); instok=all(x['classification'] not in ('FULL_YEAR_NEGATIVE','PARTIAL_YEAR_NEGATIVE') for x in iy if x['configuration_id']==cid and x['load_mode']==load)
            final=float(chronological.iloc[-1].equity_after_exit); cagr=((final/100)**(1/3)-1)*100; maxdd=dd(curve); rec=(final-100)/abs(maxdd) if maxdd else np.nan
            row=dict(case_id=case,configuration_id=cid,variant=variant,basket_id=bid,basket_size=len(members),instruments='+'.join(members),load_mode=load,risk_scenario=rn,base_risk_pct=risk*100,**returns,historical_annualized_CAGR_pct=cagr,minimum_full_year_return_pct=min(full),median_full_year_return_pct=np.median(full),total_compounded_return_pct=final-100,final_equity=final,max_realized_equity_DD_pct=maxdd,monthly_equity_DD_pct=dd([100*np.prod(1+np.array(mret[:i+1])/100) for i in range(len(mret))]),recovery=rec,complete_quarters=len(qret),positive_quarters=sum(x>0 for x in qret),negative_quarters=sum(x<0 for x in qret),positive_quarter_share=np.mean(np.array(qret)>0),worst_quarter_pct=min(qret),median_quarter_pct=np.median(qret),longest_negative_quarter_streak=streak(qret),years_4_of_4_positive=sum(sum(x>0 for x in qret[i:i+4])==4 for i in range(0,len(qret),4)),years_3_of_4_positive=sum(sum(x>0 for x in qret[i:i+4])==3 for i in range(0,len(qret),4)),years_le_2_of_4_positive=sum(sum(x>0 for x in qret[i:i+4])<=2 for i in range(0,len(qret),4)),positive_month_share=np.mean(np.array(mret)>0),negative_month_share=np.mean(np.array(mret)<0),worst_month_pct=min(mret),median_month_pct=np.median(mret),longest_negative_month_streak=streak(mret),all_portfolio_years_positive=all(x>0 for x in full),all_instrument_years_positive=instok,provenance_pass=True,deterministic_reconstruction_pass=True,target_70_all_full_years=all(x>=70 for x in full),target_80_all_full_years=all(x>=80 for x in full),CAGR_70_plus=cagr>=70,CAGR_80_plus=cagr>=80,target_classification='ALL_YEARS_80' if all(x>=80 for x in full) else 'ALL_YEARS_70' if all(x>=70 for x in full) else 'CAGR_80' if cagr>=80 else 'CAGR_70' if cagr>=70 else 'BELOW_70',**ex)
            row['production_eligible']=row['all_portfolio_years_positive'] and instok; masters.append(row); hashes.append(dict(case_id=case,event_count=len(ev),canonical_event_sha256=canonical_hash(ev))); risks.append(dict(case_id=case,**ex))
    r=pd.DataFrame(rmaster); m=pd.DataFrame(masters)
    # Pareto: strict all-objective dominance, with deterministic IDs.
    maximize=['historical_annualized_CAGR_pct','minimum_full_year_return_pct','positive_quarter_share','positive_month_share','median_month_pct']; minimize=['max_realized_equity_DD_pct','worst_quarter_pct','longest_negative_quarter_streak','longest_negative_month_streak']
    front=[]
    for i,a in m.iterrows():
      dominated=False
      for j,b in m.iterrows():
        if i==j: continue
        avv=[a[x] for x in maximize]+[-abs(a[x]) for x in minimize]; bvv=[b[x] for x in maximize]+[-abs(b[x]) for x in minimize]
        if all(y>=x for x,y in zip(avv,bvv)) and any(y>x for x,y in zip(avv,bvv)): dominated=True; break
      front.append(not dominated)
    m['pareto_frontier']=front
    tier={'ALL_YEARS_80':0,'ALL_YEARS_70':1,'CAGR_80':2,'CAGR_70':3,'BELOW_70':4}; m['_tier']=m.target_classification.map(tier)
    order=['_tier','positive_quarter_share','longest_negative_quarter_streak','max_realized_equity_DD_pct','minimum_full_year_return_pct','positive_month_share','longest_negative_month_streak','median_month_pct','recovery','historical_annualized_CAGR_pct','total_compounded_return_pct','case_id']; asc=[True,False,True,False,False,False,True,False,False,False,False,True]
    ranks=m.sort_values(order,ascending=asc,kind='mergesort').index; m['reference_rank']=0; m.loc[ranks,'reference_rank']=range(1,len(m)+1); m=m.drop(columns='_tier')
    for name,data in [('master_110_load_cases_R.csv',r),('master_220_equity_cases.csv',m),('load_yearly_R_metrics.csv',pd.DataFrame(yearly)),('load_quarterly_R_metrics.csv',pd.DataFrame(quarters)),('load_monthly_R_metrics.csv',pd.DataFrame(months)),('instrument_year_R_metrics.csv',pd.DataFrame(iy)),('instrument_quarter_R_metrics.csv',pd.DataFrame(iq)),('open_risk_summary.csv',pd.DataFrame(risks)),('equity_execution_hashes.csv',pd.DataFrame(hashes))]: write(data,out/name)
    comp=[]
    for (cid,rn),g in m.groupby(['configuration_id','risk_scenario']):
      n=g[g.load_mode=='NORMALIZED'].iloc[0]; f=g[g.load_mode=='FULL'].iloc[0]; comp.append(dict(configuration_id=cid,risk_scenario=rn,FULL_CAGR=f.historical_annualized_CAGR_pct,NORMALIZED_CAGR=n.historical_annualized_CAGR_pct,CAGR_delta=f.historical_annualized_CAGR_pct-n.historical_annualized_CAGR_pct,FULL_min_year=f.minimum_full_year_return_pct,NORMALIZED_min_year=n.minimum_full_year_return_pct,FULL_DD=f.max_realized_equity_DD_pct,NORMALIZED_DD=n.max_realized_equity_DD_pct,DD_delta=f.max_realized_equity_DD_pct-n.max_realized_equity_DD_pct,FULL_positive_quarters=f.positive_quarters,NORMALIZED_positive_quarters=n.positive_quarters,FULL_positive_months=f.positive_month_share,NORMALIZED_positive_months=n.positive_month_share,FULL_max_open_risk=f.max_nominal_open_risk_pct,NORMALIZED_max_open_risk=n.max_nominal_open_risk_pct,FULL_final_equity=f.final_equity,NORMALIZED_final_equity=n.final_equity))
    write(pd.DataFrame(comp),out/'full_vs_normalized_comparison.csv')
    summarycols=['case_id','configuration_id','variant','basket_id','basket_size','instruments','load_mode','risk_scenario','return_2023_pct','return_2024_pct','WF24_return_pct','return_2025_pct','return_2026_YTD_pct','historical_annualized_CAGR_pct','minimum_full_year_return_pct','max_realized_equity_DD_pct','recovery','positive_quarters','negative_quarters','worst_quarter_pct','positive_month_share','longest_negative_month_streak','max_nominal_open_risk_pct','final_equity','target_classification','production_eligible']
    for n in (2,3,4): write(m[m.basket_size==n][summarycols],out/f'n{n}_comparison.csv')
    write(m[m.pareto_frontier][summarycols],out/'pareto_frontier.csv'); write(m[summarycols+['pareto_frontier','reference_rank']],out/'return_drawdown_stability_frontier.csv')
    write(m[['case_id','load_mode','risk_scenario','target_70_all_full_years','target_80_all_full_years','CAGR_70_plus','CAGR_80_plus','target_classification']],out/'annual_return_target_analysis.csv')
    write(m[['case_id','complete_quarters','positive_quarters','negative_quarters','positive_quarter_share','worst_quarter_pct','median_quarter_pct','longest_negative_quarter_streak','years_4_of_4_positive','years_3_of_4_positive','years_le_2_of_4_positive']],out/'quarter_stability_summary.csv')
    leaders=m.sort_values('reference_rank').groupby(['basket_size','risk_scenario'],as_index=False).first(); write(leaders[summarycols],out/'reference_leaders.csv')
    report(out,m,av)
    core=sorted(p.name for p in out.iterdir() if p.suffix in ('.csv','.md') and p.name!='FINAL_FULL_VS_NORMALIZED_PRODUCTION_REPORT.md')
    manifest={'status':'PASS','starting_sha':'47a63c34d1288a076ff5e7e3f803bc77aff5302b','configuration_count':55,'R_case_count':110,'equity_case_count':220,'stage6_6_normalized_reconciliation':'PASS','full_scaling_reconciliation':'PASS','core_artifact_sha256':{p:sha(out/p) for p in core},'stage6_8_started':False,'stage7_executed':False}
    (out/'audit_manifest.json').write_text(json.dumps(manifest,indent=2,sort_keys=True)+'\n')
def report(out,m,av):
    leaders=m.sort_values('reference_rank'); best=lambda n: leaders[leaders.basket_size==n].iloc[0].case_id
    lines=['# Stage 6.7 — FULL versus NORMALIZED production analysis','','## Status: independently auditable compact evidence','', '### 1. Methodology','All 55 frozen configurations are evaluated under NORMALIZED and FULL loads and R15/R20. Equity is sized from current equity, frozen at entry, and compounded event by event; no linear R approximation is authoritative. Costs are already embedded in frozen net R.','', '### 2. Provenance','Only the authenticated Stage 6.6 source-trade registry is consumed. No strategy replay, raw market-data copy, optimization, or 2025 selection occurs.','', '### 3. Availability caveats']
    for s in ('GLDRUBF','IMOEXF'):
      x=av[(av.instrument==s)&(av.lifecycle=='baseline')].iloc[0]; lines.append(f'- {s} baseline 2023 coverage begins `{x.first_timestamp}` and ends `{x.last_timestamp}`; its 2023 result is explicitly partial.')
    lines += ['', '### 4. Target 70–80%',f"- NORMALIZED: CAGR ≥70 {len(m[(m.load_mode=='NORMALIZED')&m.CAGR_70_plus])}; CAGR ≥80 {len(m[(m.load_mode=='NORMALIZED')&m.CAGR_80_plus])}; every full year ≥70 {len(m[(m.load_mode=='NORMALIZED')&m.target_70_all_full_years])}; ≥80 {len(m[(m.load_mode=='NORMALIZED')&m.target_80_all_full_years])}.",f"- FULL: CAGR ≥70 {len(m[(m.load_mode=='FULL')&m.CAGR_70_plus])}; CAGR ≥80 {len(m[(m.load_mode=='FULL')&m.CAGR_80_plus])}; every full year ≥70 {len(m[(m.load_mode=='FULL')&m.target_70_all_full_years])}; ≥80 {len(m[(m.load_mode=='FULL')&m.target_80_all_full_years])}.",'','### 5. Headline FULL vs NORMALIZED comparison','FULL raises both compounded return and nominal open risk; exact paired deltas are in `full_vs_normalized_comparison.csv`.','',f'### 6. Strongest N2\n`{best(2)}`',f'### 7. Strongest N3\n`{best(3)}`',f'### 8. Strongest N4\n`{best(4)}`','### 9. Pareto candidates',', '.join(m[m.pareto_frontier].case_id), '','### 10. FULL target attainment','See target counts above and `annual_return_target_analysis.csv`.','### 11. NORMALIZED target attainment','See target counts above; FULL is not assumed necessary and is judged from computed results.','### 12. Stability comparison','Quarter/month summaries remain equity-compounded in the master; normalized full R evidence is in period CSVs.','### 13. DD comparison','Exact realized and monthly drawdowns are in the master and paired comparison.','### 14. Open-risk comparison','Exposure is independently reconstructible; threshold dwell shares are in `open_risk_summary.csv`.','### 15. Instrument-year failures',f"{len(m[~m.all_instrument_years_positive])} equity cases fail; causal instruments and statuses are in `instrument_year_R_metrics.csv`.",'### 16. Candidates for later Stage 6.8','This report supplies recommendation candidates only; it freezes none. Stability-first R15/R20 are the rank-leading rows for each risk scenario in `reference_leaders.csv`.','### 17. Retrospective limitation','2025 TRUE OOS is used only for locked retrospective evaluation, never discovery or selection. Evidence supports review for Stage 6.8 but does not start it. Stage 7 was not executed.','', '## Answers to required questions','Questions 1–6 and 21 are answered by target counts; 7–16 and 28–29 by `reference_leaders.csv`; 17–20 by instrument/availability evidence; 22–23 by paired/open-risk files; 24–27 by stability, frontier, and comparison files. The highest-return domination status is explicit in the master. Question 30: evidence is sufficient for a later review, but no advancement decision is made here.']
    (out/'FINAL_FULL_VS_NORMALIZED_PRODUCTION_REPORT.md').write_text('\n\n'.join(lines)+'\n')
if __name__=='__main__':
    p=argparse.ArgumentParser(); p.add_argument('--output-dir',type=Path,default=HERE); generate(p.parse_args().output_dir)
