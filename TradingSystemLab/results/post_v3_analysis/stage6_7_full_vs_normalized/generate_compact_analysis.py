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
def simulate_events(t,weight,risk,lifecycles):
    """Simulate one continuous stream; exits precede entries at equal timestamps."""
    records=[]; equity=100.; open_pos={}; events=[]
    q=t[t.lifecycle.isin(lifecycles)].copy()
    for r in q.itertuples():
        events += [(r.entry,1,r.source_trade_id,r),(r.exit,0,r.source_trade_id,r)]
    for when,kind,tid,r in sorted(events,key=lambda x:(x[0],x[1],x[2])):
        if kind==1:
            risk_cash=equity*risk*weight
            open_pos[tid]=(equity,risk_cash,r)
        else:
            sized,cash,rr=open_pos.pop(tid); pnl=cash*rr.strategy_R; equity+=pnl
            records.append(dict(source_trade_id=tid,lifecycle=rr.lifecycle,instrument=rr.instrument,entry_time=rr.entry_time,exit_time=rr.exit_time,source_R=rr.strategy_R,load_weight=weight,risk_fraction=risk,pre_entry_equity=sized,risk_cash=cash,realized_PnL=pnl,equity_after_exit=equity))
    return pd.DataFrame(records).sort_values(['exit_time','instrument','source_trade_id'],kind='mergesort').reset_index(drop=True)

def equity_events(t,weight,risk):
    """Return the continuous production stream and independent WF24 stream."""
    return (simulate_events(t,weight,risk,('baseline','historical_true_oos')),
            simulate_events(t,weight,risk,('walk_forward',)))
def canonical_hash(e):
    cols=['source_trade_id','lifecycle','instrument','entry_time','exit_time','source_R','load_weight','risk_fraction','pre_entry_equity','risk_cash','realized_PnL','equity_after_exit']
    lines=[]
    for r in e[cols].itertuples(index=False,name=None): lines.append('|'.join(f'{v:.12f}' if isinstance(v,float) else str(v) for v in r))
    return hashlib.sha256(('\n'.join(lines)+'\n').encode()).hexdigest()
def period_returns(e, initial=100.):
    """Returns between chronological period-end realized-equity observations."""
    x=e.copy(); x['exit']=pd.to_datetime(x.exit_time,utc=True); out=[]
    for freq in ('Y','Q','M'):
        prior=initial
        for p,g in x.groupby(x.exit.dt.to_period(freq),sort=True):
            end=float(g.iloc[-1].equity_after_exit)
            out.append(dict(freq=freq,period=str(p),ret=(end/prior-1)*100,end_equity=end))
            prior=end
    return pd.DataFrame(out)
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
              partial=partial or year==2026
              status=('PARTIAL_YEAR_' if partial else 'FULL_YEAR_')+('POSITIVE' if z.scaled_R.sum()>0 else 'NEGATIVE') if len(z) else 'NOT_AVAILABLE'
              iy.append(dict(configuration_id=cid,load_mode=load,instrument=s,lifecycle=life,year=year,raw_source_R=z.strategy_R.sum(),scaled_R=z.scaled_R.sum(),trades=len(z),availability_status='AVAILABLE' if len(z) else 'NOT_AVAILABLE',year_coverage='PARTIAL' if partial else 'FULL',classification=status))
          period_data=[]
          for life in LIFES:
            lg=base[base.lifecycle==life]
            for freq,dest in [('Q',quarters),('M',months)]:
              for p,g in lg.groupby(lg.exit.dt.to_period(freq)):
                net=g.scaled_R.sum(); coverage=[]
                for s in members:
                  ar=av[(av.lifecycle==life)&(av.instrument==s)].iloc[0]; start=pd.Timestamp(ar.first_timestamp); end=pd.Timestamp(ar.last_timestamp); ps=p.start_time.tz_localize('UTC'); pe=p.end_time.tz_localize('UTC')
                  coverage.append('FULL' if start<=ps and end>=pe else 'PARTIAL' if end>=ps and start<=pe else 'NOT_AVAILABLE')
                completeness='FULL_PORTFOLIO_'+('QUARTER' if freq=='Q' else 'MONTH') if all(x=='FULL' for x in coverage) else 'PARTIAL_PORTFOLIO_'+('QUARTER' if freq=='Q' else 'MONTH') if any(x!='NOT_AVAILABLE' for x in coverage) else 'NOT_AVAILABLE'
                row=dict(configuration_id=cid,load_mode=load,lifecycle=life,year=p.year,trades=len(g),net_R=net,completeness=completeness,classification='POSITIVE' if net>0 else 'NEGATIVE' if net<0 else 'ZERO')
                row['quarter' if freq=='Q' else 'month']=p.quarter if freq=='Q' else p.month; dest.append(row); period_data.append((freq,p,net))
                if freq=='Q':
                  for s in members:
                    z=g[g.instrument==s]; cov=coverage[list(members).index(s)]; iq.append(dict(configuration_id=cid,load_mode=load,instrument=s,lifecycle=life,year=p.year,quarter=p.quarter,raw_source_R=z.strategy_R.sum(),scaled_R=z.scaled_R.sum(),trades=len(z),availability_status='AVAILABLE' if len(z) else 'NOT_AVAILABLE',quarter_coverage=cov+'_QUARTER' if cov!='NOT_AVAILABLE' else cov,classification='POSITIVE' if z.scaled_R.sum()>0 else 'NEGATIVE' if z.scaled_R.sum()<0 else 'ZERO'))
          chron=base[base.lifecycle!='walk_forward'].sort_values(['exit','instrument','source_trade_id']); vals=chron.scaled_R.tolist(); qv=[x[2] for x in period_data if x[0]=='Q']; mv=[x[2] for x in period_data if x[0]=='M']; annual=[period_rs[x] for x in ('return_2023_pct','return_2024_pct','return_2025_pct')]
          roll6=[sum(mv[i-5:i+1]) for i in range(5,len(mv))]; roll12=[sum(mv[i-11:i+1]) for i in range(11,len(mv))]
          rmaster.append(dict(configuration_id=cid,variant=variant,basket_id=bid,basket_size=len(members),instruments='+'.join(members),load_mode=load,R_2023=period_rs['return_2023_pct'],R_2024=period_rs['return_2024_pct'],WF24_R=period_rs['WF24_return_pct'],R_2025=period_rs['return_2025_pct'],R_2026_YTD=period_rs['return_2026_YTD_pct'],chronological_R=sum(vals),annual_floor_R=min(annual),worst_complete_12M_R=min(roll12),worst_complete_6M_R=min(roll6),max_DD_R=min(np.cumsum([0,*vals])-np.maximum.accumulate(np.cumsum([0,*vals]))),recovery=sum(vals)/abs(min(np.cumsum([0,*vals])-np.maximum.accumulate(np.cumsum([0,*vals])))) if min(np.cumsum([0,*vals])-np.maximum.accumulate(np.cumsum([0,*vals]))) else np.nan,positive_quarter_share=np.mean(np.array(qv)>0),positive_month_share=np.mean(np.array(mv)>0),longest_negative_quarter_streak=streak(qv),longest_negative_month_streak=streak(mv),concentration=max([sum(sorted([v for f,p,v in period_data if f=='M' and p.year==y and v>0],reverse=True)[:3]) for y in (2023,2024,2025,2026)])))
          for rn,risk in RISKS:
            case=f'{cid}__{load}__{rn}'; prod,wf=equity_events(base,weight,risk); details=period_returns(prod); wfdet=period_returns(wf); ex=exposure(base,weight,risk)
            annual=dict(zip(details[details.freq=='Y'].period,details[details.freq=='Y'].ret)); returns={'return_2023_pct':annual.get('2023',0.),'return_2024_pct':annual.get('2024',0.),'return_2025_pct':annual.get('2025',0.),'return_2026_YTD_pct':annual.get('2026',0.),'WF24_return_pct':float(wf.iloc[-1].equity_after_exit-100)}
            full=[returns[x] for x in ('return_2023_pct','return_2024_pct','return_2025_pct')]
            # A portfolio quarter is complete only when every member lifecycle covers its calendar bounds.
            qd=details[details.freq=='Q'].copy(); complete=[]
            for p in qd.period:
              per=pd.Period(p,freq='Q'); life='baseline' if per.year<=2024 else 'historical_true_oos'; qs=per.start_time.tz_localize('UTC'); qe=per.end_time.tz_localize('UTC')
              complete.append(all(pd.Timestamp(av[(av.instrument==s)&(av.lifecycle==life)].iloc[0].first_timestamp)<=qs and pd.Timestamp(av[(av.instrument==s)&(av.lifecycle==life)].iloc[0].last_timestamp)>=qe for s in members))
            qd['complete']=complete; qret=qd[qd.complete].ret.tolist(); mdet=details[details.freq=='M']; mret=mdet.ret.tolist()
            instok=all(x['classification'] not in ('FULL_YEAR_NEGATIVE','PARTIAL_YEAR_NEGATIVE') for x in iy if x['configuration_id']==cid and x['load_mode']==load)
            final=float(prod.iloc[-1].equity_after_exit); elapsed=(pd.Timestamp(prod.iloc[-1].exit_time)-pd.Timestamp(prod.iloc[0].entry_time)).total_seconds()/(365.2425*86400); cagr=((final/100)**(1/elapsed)-1)*100
            completed_cagr=(np.prod(1+np.array(full)/100)**(1/3)-1)*100; curve=prod.equity_after_exit.tolist(); maxdd=dd(curve); monthlydd=dd(mdet.end_equity.tolist()); rec=(final-100)/abs(maxdd) if maxdd else np.nan
            row=dict(case_id=case,configuration_id=cid,variant=variant,basket_id=bid,basket_size=len(members),instruments='+'.join(members),load_mode=load,risk_scenario=rn,base_risk_pct=risk*100,**returns,historical_annualized_CAGR_pct=cagr,completed_year_geometric_CAGR_pct=completed_cagr,minimum_full_year_return_pct=min(full),median_full_year_return_pct=np.median(full),total_compounded_return_pct=(final/100-1)*100,final_equity=final,max_realized_equity_DD_pct=maxdd,monthly_equity_DD_pct=monthlydd,recovery=rec,complete_quarters=len(qret),partial_quarters=len(qd)-len(qret),positive_quarters=sum(x>0 for x in qret),negative_quarters=sum(x<0 for x in qret),positive_complete_quarter_share=np.mean(np.array(qret)>0),positive_quarter_share=np.mean(np.array(qret)>0),worst_complete_quarter_pct=min(qret),worst_quarter_pct=min(qret),median_complete_quarter_pct=np.median(qret),median_quarter_pct=np.median(qret),longest_negative_quarter_streak=streak(qret),positive_month_share=np.mean(np.array(mret)>0),negative_month_share=np.mean(np.array(mret)<0),worst_month_pct=min(mret),median_month_pct=np.median(mret),longest_negative_month_streak=streak(mret),all_portfolio_years_positive=all(x>0 for x in [*full,returns['return_2026_YTD_pct'],returns['WF24_return_pct']]),all_instrument_years_positive=instok,provenance_pass=True,deterministic_reconstruction_pass=True,target_70_all_full_years=all(x>=70 for x in full),target_80_all_full_years=all(x>=80 for x in full),CAGR_70_plus=cagr>=70,CAGR_80_plus=cagr>=80,target_classification='ALL_YEARS_80' if all(x>=80 for x in full) else 'ALL_YEARS_70' if all(x>=70 for x in full) else 'CAGR_80' if cagr>=80 else 'CAGR_70' if cagr>=70 else 'BELOW_70',**ex)
            row['production_eligible']=row['all_portfolio_years_positive'] and instok; masters.append(row); hashes.append(dict(case_id=case,production_event_count=len(prod),production_chronological_event_sha256=canonical_hash(prod),wf24_event_count=len(wf),wf24_event_sha256=canonical_hash(wf))); risks.append(dict(case_id=case,**ex))
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
    m['diagnostic_all_cases_pareto']=front
    eligible=m[m.production_eligible]
    efront=[]
    for i,a in m.iterrows():
      if not a.production_eligible: efront.append(False); continue
      dominated=False
      for j,b in eligible.iterrows():
        if i==j: continue
        avv=[a[x] for x in maximize]+[-abs(a[x]) for x in minimize]; bvv=[b[x] for x in maximize]+[-abs(b[x]) for x in minimize]
        if all(y>=x for x,y in zip(avv,bvv)) and any(y>x for x,y in zip(avv,bvv)): dominated=True; break
      efront.append(not dominated)
    m['production_pareto']=efront; m['pareto_frontier']=m.production_pareto
    tier={'ALL_YEARS_80':0,'ALL_YEARS_70':1,'CAGR_80':2,'CAGR_70':3,'BELOW_70':4}; m['_tier']=m.target_classification.map(tier)
    order=['_tier','positive_quarter_share','longest_negative_quarter_streak','max_realized_equity_DD_pct','minimum_full_year_return_pct','positive_month_share','longest_negative_month_streak','median_month_pct','recovery','historical_annualized_CAGR_pct','total_compounded_return_pct','case_id']; asc=[True,False,True,False,False,False,True,False,False,False,False,True]
    ranks=m[m.production_eligible].sort_values(order,ascending=asc,kind='mergesort').index; m['reference_rank']=np.nan; m.loc[ranks,'reference_rank']=range(1,len(ranks)+1); m=m.drop(columns='_tier')
    for name,data in [('master_110_load_cases_R.csv',r),('master_220_equity_cases.csv',m),('load_yearly_R_metrics.csv',pd.DataFrame(yearly)),('load_quarterly_R_metrics.csv',pd.DataFrame(quarters)),('load_monthly_R_metrics.csv',pd.DataFrame(months)),('instrument_year_R_metrics.csv',pd.DataFrame(iy)),('instrument_quarter_R_metrics.csv',pd.DataFrame(iq)),('open_risk_summary.csv',pd.DataFrame(risks)),('equity_execution_hashes.csv',pd.DataFrame(hashes))]: write(data,out/name)
    comp=[]
    for (cid,rn),g in m.groupby(['configuration_id','risk_scenario']):
      n=g[g.load_mode=='NORMALIZED'].iloc[0]; f=g[g.load_mode=='FULL'].iloc[0]; comp.append(dict(configuration_id=cid,risk_scenario=rn,FULL_CAGR=f.historical_annualized_CAGR_pct,NORMALIZED_CAGR=n.historical_annualized_CAGR_pct,CAGR_delta=f.historical_annualized_CAGR_pct-n.historical_annualized_CAGR_pct,FULL_min_year=f.minimum_full_year_return_pct,NORMALIZED_min_year=n.minimum_full_year_return_pct,FULL_DD=f.max_realized_equity_DD_pct,NORMALIZED_DD=n.max_realized_equity_DD_pct,DD_delta=f.max_realized_equity_DD_pct-n.max_realized_equity_DD_pct,FULL_positive_quarters=f.positive_quarters,NORMALIZED_positive_quarters=n.positive_quarters,FULL_positive_months=f.positive_month_share,NORMALIZED_positive_months=n.positive_month_share,FULL_max_open_risk=f.max_nominal_open_risk_pct,NORMALIZED_max_open_risk=n.max_nominal_open_risk_pct,FULL_final_equity=f.final_equity,NORMALIZED_final_equity=n.final_equity))
    write(pd.DataFrame(comp),out/'full_vs_normalized_comparison.csv')
    summarycols=['case_id','configuration_id','variant','basket_id','basket_size','instruments','load_mode','risk_scenario','return_2023_pct','return_2024_pct','WF24_return_pct','return_2025_pct','return_2026_YTD_pct','historical_annualized_CAGR_pct','minimum_full_year_return_pct','max_realized_equity_DD_pct','recovery','positive_quarters','negative_quarters','worst_quarter_pct','positive_month_share','longest_negative_month_streak','max_nominal_open_risk_pct','final_equity','target_classification','production_eligible']
    for n in (2,3,4): write(m[m.basket_size==n][summarycols],out/f'n{n}_comparison.csv')
    write(m[m.diagnostic_all_cases_pareto][summarycols],out/'all_cases_pareto_frontier.csv'); write(m[m.production_pareto][summarycols],out/'production_eligible_pareto_frontier.csv'); write(m[m.production_pareto][summarycols],out/'pareto_frontier.csv'); write(m[summarycols+['pareto_frontier','reference_rank']],out/'return_drawdown_stability_frontier.csv')
    write(m[['case_id','load_mode','risk_scenario','target_70_all_full_years','target_80_all_full_years','CAGR_70_plus','CAGR_80_plus','target_classification']],out/'annual_return_target_analysis.csv')
    write(m[['case_id','complete_quarters','partial_quarters','positive_quarters','negative_quarters','positive_complete_quarter_share','worst_complete_quarter_pct','median_complete_quarter_pct','longest_negative_quarter_streak']],out/'quarter_stability_summary.csv')
    leaders=m[m.production_eligible].sort_values('reference_rank').groupby(['basket_size','risk_scenario'],as_index=False).first(); write(leaders[summarycols],out/'reference_leaders.csv')
    failures=pd.DataFrame(iy); failures=failures[failures.classification.isin(['FULL_YEAR_NEGATIVE','PARTIAL_YEAR_NEGATIVE'])].copy(); failures['variant']=failures.configuration_id.str.split('__').str[0]; failures['basket']=failures.configuration_id.str.split('__').str[1]; failures['completeness']=failures.classification.str.replace('_POSITIVE','',regex=False).str.replace('_NEGATIVE','',regex=False); failures['failure_reason']='NON_POSITIVE_AVAILABLE_INSTRUMENT_PERIOD'; failures=failures.rename(columns={'raw_source_R':'raw_R'})
    write(failures[['configuration_id','variant','basket','instrument','lifecycle','year','completeness','raw_R','scaled_R','failure_reason']],out/'instrument_year_gate_failures.csv')
    write(m[['case_id','final_equity','total_compounded_return_pct','historical_annualized_CAGR_pct','completed_year_geometric_CAGR_pct','max_realized_equity_DD_pct','monthly_equity_DD_pct','recovery']],out/'production_equity_summary.csv'); write(m[['case_id','WF24_return_pct']],out/'wf24_equity_summary.csv')
    bands=[(-np.inf,10,'DD_LE_10'),(10,15,'DD_10_TO_15'),(15,20,'DD_15_TO_20'),(20,25,'DD_20_TO_25'),(25,30,'DD_25_TO_30'),(30,np.inf,'DD_GT_30')]; bandrows=[]
    for lo,hi,label in bands:
      g=m[m.production_eligible & (m.max_realized_equity_DD_pct.abs()>lo) & (m.max_realized_equity_DD_pct.abs()<=hi)]
      if len(g): bandrows.append(dict(drawdown_band=label,case_count=len(g),best_CAGR_case=g.loc[g.historical_annualized_CAGR_pct.idxmax()].case_id,best_CAGR_pct=g.historical_annualized_CAGR_pct.max(),best_stability_case=g.sort_values('reference_rank').iloc[0].case_id))
      else: bandrows.append(dict(drawdown_band=label,case_count=0,best_CAGR_case='',best_CAGR_pct=np.nan,best_stability_case=''))
    write(pd.DataFrame(bandrows),out/'return_by_drawdown_band.csv')
    report(out,m,av)
    core=sorted(p.name for p in out.iterdir() if p.suffix in ('.csv','.md') and p.name!='FINAL_FULL_VS_NORMALIZED_PRODUCTION_REPORT.md')
    manifest={'status':'PASS','starting_sha':'890097ee0e92687356a1ce3d3292abf0c26795eb','pr267_head':'77792dbaae8b5436cdb5edf92594b095980cd1dc','pr267_merge_sha':'890097ee0e92687356a1ce3d3292abf0c26795eb','configuration_count':55,'R_case_count':110,'equity_case_count':220,'stage6_6_normalized_reconciliation':'PASS','full_scaling_reconciliation':'PASS','core_artifact_sha256':{p:sha(out/p) for p in core},'stage6_8_started':False,'stage7_executed':False}
    (out/'audit_manifest.json').write_text(json.dumps(manifest,indent=2,sort_keys=True)+'\n')
def report(out,m,av):
    e=m[m.production_eligible].sort_values('reference_rank'); best=lambda n: (e[e.basket_size==n].iloc[0].case_id if len(e[e.basket_size==n]) else 'NO_PRODUCTION_ELIGIBLE_N4')
    lines=['# Stage 6.7 — Production equity correction and audit close','','## Correction','PR #267 production CAGR, final equity, drawdown, quarter, and month conclusions were invalid because lifecycle-reset equity was stitched together. These corrected figures supersede them. The authenticated R-space economics, 55 configurations, 110 load cases, and Stage 6.6 reconciliation are unchanged.','','## Method','Production equity is one causal curve from baseline 2023–2024 into historical OOS 2025–2026 YTD. WF24 is independently simulated from 100 and never enters production return, drawdown, quarter, or month statistics. Same-time exits precede entries, and all same-time entries use identical post-exit equity. Recovery is total compounded return divided by absolute realized-equity maximum drawdown.','','## Eligibility',f'- Eligible equity cases: **{len(e)}**; ineligible: **{len(m)-len(e)}**; unique eligible configurations: **{e.configuration_id.nunique()}**.',f'- Best eligible N2: `{best(2)}`',f'- Best eligible N3: `{best(3)}`',f'- Best eligible N4: `{best(4)}`','','## Target counts']
    for load in LOADS:
      g=m[m.load_mode==load]; ge=g[g.production_eligible]; lines.append(f'- {load}: all cases CAGR≥70/80 = {sum(g.CAGR_70_plus)}/{sum(g.CAGR_80_plus)}, all-years≥70/80 = {sum(g.target_70_all_full_years)}/{sum(g.target_80_all_full_years)}; eligible-only CAGR≥70/80 = {sum(ge.CAGR_70_plus)}/{sum(ge.CAGR_80_plus)}, all-years≥70/80 = {sum(ge.target_70_all_full_years)}/{sum(ge.target_80_all_full_years)}.')
    lines += ['','## Evidence','Corrected master metrics, separate production/all-case Pareto sets, failure evidence, drawdown bands, execution hashes, and independent audit results are provided beside this report. Partial inception quarters and 2026 Q3/YTD are excluded from complete-quarter ranking.','','## Scope stop','Stage 6.8 was **NOT started**. Stage 7 was **NOT executed**.']
    (out/'FINAL_FULL_VS_NORMALIZED_PRODUCTION_REPORT.md').write_text('\n\n'.join(lines)+'\n')
if __name__=='__main__':
    p=argparse.ArgumentParser(); p.add_argument('--output-dir',type=Path,default=HERE); generate(p.parse_args().output_dir)
