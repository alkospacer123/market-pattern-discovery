"""Descriptive R arithmetic and signal-cohort comparison; never feeds replay."""
import math
from collections import Counter
import pandas as pd
from io_utils import write_csv,write_json
EPS=1e-8

def sign(x):return 1 if x>EPS else -1 if x< -EPS else 0

def dd(values):
 peak=worst=0.
 for v in values:peak=max(peak,v);worst=max(worst,peak-v)
 return worst

def statistics(trades):
 rows=sorted(trades,key=lambda r:(r['exit_time'],r['instrument'],r['trade_id']));rs=[t['gross_R'] for t in rows]
 wins=math.fsum(x for x in rs if x>0);loss=-math.fsum(x for x in rs if x<0);total=math.fsum(rs)
 eq=[];acc=[]
 for x in rs:acc.append(x);eq.append(math.fsum(acc))
 return dict(CLOSED=len(rs),gross_R=total,gross_positive_R=wins,gross_negative_R=-loss,gross_PF=wins/loss if loss else None,expectancy_R=total/len(rs) if rs else None,CLOSED_R_DD=dd(eq),winner_ge_2R_count=sum(x>=2 for x in rs),winner_ge_2R_R=math.fsum(x for x in rs if x>=2))

def calendar(models,bars,out,cost,slippage):
 months=[f'{y}-{m:02d}' for y in (2023,2024) for m in range(1,13)];monthly=[];summary=[];curves=[];coverage=[]
 for symbol,bs in bars.items():
  for month in months:
   ss=[b for b in bs if b['at'].strftime('%Y-%m')==month]
   coverage.append(dict(instrument=symbol,month=month,bars=len(ss),first_close=ss[0]['at'] if ss else None,last_close=ss[-1]['at'] if ss else None,coverage='OBSERVED' if ss else 'NO_DATA',observed_gaps=sum(b['at']-a['at']>pd.Timedelta(minutes=15) for a,b in zip(ss,ss[1:]))))
 for mode,r in models.items():
  frames={s:pd.DataFrame([x for x in r['marks'] if x['instrument']==s]).set_index('at') for s in bars}
  clock=sorted({t for f in frames.values() for t in f.index});curve=pd.DataFrame(index=clock)
  for field in ('gross_realized_R','gross_unrealized_R','gross_MTM_R'):
   curve[field]=pd.DataFrame({s:f[field].reindex(clock).ffill().fillna(0) for s,f in frames.items()}).sum(axis=1)
  for at,row in curve.iterrows():curves.append(dict(variant=mode,at=at,**row.to_dict()))
  previous=0.;mm=[]
  for month in months:
   sub=curve.loc[curve.index.strftime('%Y-%m')==month];active=[x['instrument'] for x in coverage if x['month']==month and x['bars']]
   tt=[t for t in r['trades'] if t['exit_time'].strftime('%Y-%m')==month];gross=math.fsum(t['gross_R'] for t in tt);last=float(sub.gross_MTM_R.iloc[-1]);mtm=last-previous
   row=dict(variant=mode,month=month,timezone='Europe/Moscow',coverage='N4_OBSERVED' if len(active)==4 else 'PARTIAL_N4',observed_instruments='|'.join(active),CLOSED_R=gross,MTM_R=mtm,CLOSED_sign=sign(gross),MTM_sign=sign(mtm),CLOSED_trades=len(tt),unrealized_R_end=float(sub.gross_unrealized_R.iloc[-1]),MTM_intramonth_DD_R=dd([0]+(sub.gross_MTM_R-previous).tolist()))
   previous=last;mm.append(row);monthly.append(row)
  for period in ('2023_2024','2023','2024'):
   tt=r['trades'] if period=='2023_2024' else [t for t in r['trades'] if str(t['exit_time'].year)==period]
   m=mm if period=='2023_2024' else [x for x in mm if x['month'].startswith(period)]
   c=curve if period=='2023_2024' else curve.loc[curve.index.strftime('%Y')==period]
   c_values=c.gross_MTM_R-float(curve.loc[curve.index<c.index[0]].gross_MTM_R.iloc[-1]) if c.index[0]!=curve.index[0] else c.gross_MTM_R
   row=dict(variant=mode,period=period,**statistics(tt),OPEN_at_period_end=sum(x['month']==m[-1]['month'] for x in r['snapshots']),MTM_R_DD=dd(c_values.tolist()))
   for basis in ('CLOSED_R','MTM_R'):
    worst=min(m,key=lambda x:x[basis]);row.update({basis+'_negative_months':sum(x[basis]<-EPS for x in m),basis+'_negative_sum':math.fsum(x[basis] for x in m if x[basis]<-EPS),basis+'_worst_month':worst['month'],basis+'_worst_R':worst[basis]})
   summary.append(row)
 transitions=[]
 for month in months:
  a,b=[next(x for x in monthly if x['month']==month and x['variant']==v) for v in models]
  for basis in ('CLOSED_R','MTM_R'):
   sa,sb=sign(a[basis]),sign(b[basis]);transitions.append(dict(month=month,basis=basis,CONTROL_R=a[basis],CONFIRM_R=b[basis],delta_R=b[basis]-a[basis],CONTROL_sign=sa,CONFIRM_sign=sb,sign_changed=sa!=sb,transition=f'{sa}_TO_{sb}'))
 for name,rows in [('SUMMARY',summary),('MONTHLY',monthly),('MONTH_SIGN_TRANSITIONS',transitions),('COVERAGE',coverage),('PORTFOLIO_CURVES',curves)]:write_csv(out/(name+'.csv'+('.gz' if name=='PORTFOLIO_CURVES' else '')),rows)
 sensitivity=[]
 for mode,r in models.items():
  rs=[t|{'gross_R':t['gross_R']-cost-slippage} for t in r['trades']]
  sensitivity.append(dict(variant=mode,round_trip_cost_R=cost,round_trip_slippage_R=slippage,scope='NORMALIZED_R_SENSITIVITY_NOT_EXECUTABLE_NET',**statistics(rs)))
 write_csv(out/'NORMALIZED_COST_SENSITIVITY.csv',sensitivity)
 return summary,monthly,transitions

def comparisons(models,out):
 def key(t):return (t['instrument'],t['signal_time'],t['direction'])
 aa,bb=[{key(t):t|{'status':status} for table,status in [('trades','CLOSED'),('OPEN','OPEN')] for t in r[table]} for r in models.values()]
 signals=[{key(t):t for t in r['signals']} for r in models.values()];rows=[]
 for k in sorted(aa.keys()|bb.keys()):
  a,b=aa.get(k),bb.get(k);x,y=(a or {}),(b or {});ar=x.get('gross_R');br=y.get('gross_R');d=1 if k[2]=='LONG' else -1;both_closed=a and b and a['status']==b['status']=='CLOSED'
  category='COMMON_SIGNAL' if a and b else 'MISSED_CONTROL_ENTRY' if a else 'NEW_CONFIRM_ENTRY'
  row=dict(instrument=k[0],signal_time=k[1],direction=k[2],match=category,CONTROL_status=x.get('status'),CONFIRM_status=y.get('status'),CONTROL_trade_id=x.get('trade_id'),CONFIRM_trade_id=y.get('trade_id'),CONTROL_R=ar,CONFIRM_R=br,CONTROL_reason=signals[0].get(k,{}).get('reason'),CONFIRM_reason=signals[1].get(k,{}).get('reason'),CONTROL_entry=x.get('entry_price'),CONFIRM_entry=y.get('entry_price'),CONTROL_entry_time=x.get('actual_entry_time'),CONFIRM_entry_time=y.get('actual_entry_time'),CONTROL_exit_time=x.get('exit_time'),CONFIRM_exit_time=y.get('exit_time'),CONTROL_R0=x.get('initial_risk'),CONFIRM_R0=y.get('initial_risk'),confirmed=y.get('confirmed'),CONTROL_winner=ar is not None and ar>0,CONTROL_large_winner=ar is not None and ar>=2,missed_profitable=ar is not None and ar>0 and not b,profitable_to_nonpositive=ar is not None and ar>0 and br is not None and br<=0,profitable_to_OPEN=ar is not None and ar>0 and b is not None and b['status']=='OPEN',profitable_reduced=ar is not None and ar>0 and br is not None and 0<br<ar-EPS)
  if both_closed:
   entry_penalty=d*(b['entry_price']-a['entry_price'])/a['initial_risk'];exit_delta=d*(b['exit_price']-a['exit_price'])/a['initial_risk'];alt_pnl=d*(b['exit_price']-b['entry_price'])/a['initial_risk']
   row.update(entry_penalty_CONTROL_R0=entry_penalty,exit_delta_CONTROL_R0=exit_delta,CONFIRM_PNL_in_CONTROL_R0=alt_pnl,delta_PNL_CONTROL_R0=alt_pnl-ar)
  rows.append(row)
 write_csv(out/'TRADE_COMPARISON.csv',rows)
 write_csv(out/'NEW_AND_MISSED_ENTRIES.csv',[r for r in rows if r['match']!='COMMON_SIGNAL'],fields=list(rows[0]))
 write_csv(out/'LOST_AND_REDUCED_WINNERS.csv',[r for r in rows if any(r[k] for k in ('missed_profitable','profitable_to_nonpositive','profitable_to_OPEN','profitable_reduced'))],fields=list(rows[0]))
 write_csv(out/'ORIGINAL_GE_2R_WINNERS.csv',[r for r in rows if r['CONTROL_large_winner']],fields=list(rows[0]))
 large=[r for r in rows if r['CONTROL_large_winner']]
 receipt=dict(common_signals=sum(r['match']=='COMMON_SIGNAL' for r in rows),missed_control_entries=sum(r['match']=='MISSED_CONTROL_ENTRY' for r in rows),new_confirm_entries=sum(r['match']=='NEW_CONFIRM_ENTRY' for r in rows),missed_profitable=sum(r['missed_profitable'] for r in rows),missed_profitable_CONTROL_R=math.fsum(r['CONTROL_R'] for r in rows if r['missed_profitable']),profitable_to_nonpositive=sum(r['profitable_to_nonpositive'] for r in rows),profitable_to_OPEN=sum(r['profitable_to_OPEN'] for r in rows),profitable_reduced=sum(r['profitable_reduced'] for r in rows),original_ge2R_count=len(large),original_ge2R_R=math.fsum(r['CONTROL_R'] for r in large),original_ge2R_still_ge2R=sum(r['CONFIRM_R'] is not None and r['CONFIRM_R']>=2 for r in large),original_ge2R_skipped=sum(r['CONFIRM_status'] is None for r in large),original_ge2R_OPEN=sum(r['CONFIRM_status']=='OPEN' for r in large),original_ge2R_to_nonpositive=sum(r['CONFIRM_R'] is not None and r['CONFIRM_R']<=0 for r in large),original_ge2R_CONFIRMED_CLOSED_contribution_R=math.fsum(r['CONFIRM_R'] for r in large if r['CONFIRM_R'] is not None),new_entries_R=math.fsum(r['CONFIRM_R'] for r in rows if r['match']=='NEW_CONFIRM_ENTRY' and r['CONFIRM_R'] is not None),missed_entries_CONTROL_R=math.fsum(r['CONTROL_R'] for r in rows if r['match']=='MISSED_CONTROL_ENTRY' and r['CONTROL_R'] is not None))
 write_json(out/'COMPARISON.json',receipt)
 reasons=[]
 for mode,r in models.items():
  for reason,n in sorted(Counter(s['reason'] for s in r['signals']).items()):reasons.append(dict(variant=mode,reason=reason,count=n))
 write_csv(out/'SIGNAL_REASON_COUNTS.csv',reasons)
 # Mechanism and original winner preservation by original signal year.
 cohorts=[]
 for year in ('2023','2024','2023_2024'):
  cohort=[r for r in rows if r['CONTROL_large_winner'] and (year=='2023_2024' or str(r['signal_time'].year)==year)]
  cohorts.append(dict(signal_year=year,original_ge2R_count=len(cohort),CONTROL_R=math.fsum(r['CONTROL_R'] for r in cohort),retained_ge2R=sum(r['CONFIRM_R'] is not None and r['CONFIRM_R']>=2 for r in cohort),skipped=sum(r['CONFIRM_status'] is None for r in cohort),to_nonpositive=sum(r['CONFIRM_R'] is not None and r['CONFIRM_R']<=0 for r in cohort),OPEN=sum(r['CONFIRM_status']=='OPEN' for r in cohort),CONFIRM_CLOSED_contribution_R=math.fsum(r['CONFIRM_R'] for r in cohort if r['CONFIRM_R'] is not None)))
 write_csv(out/'ORIGINAL_GE_2R_BY_YEAR.csv',cohorts)
 mechanism=[]
 for year in ('2023','2024','2023_2024'):
  events=[s for s in models['CONFIRM']['signals'] if s['trade_id'] is not None and (year=='2023_2024' or str(s['signal_time'].year)==year)]
  delayed=[s for s in events if s['stretched_delay']]
  mechanism.append(dict(signal_year=year,eligible_attempts=len(events),stretched_attempts=len(delayed),executed_confirmed=sum(s['reason']=='EXECUTED_CONFIRMED_OPEN' for s in delayed),failed_price=sum(s['reason']=='CONFIRMATION_FAILED' for s in delayed),outside_T1=sum(s['reason']=='CONFIRMATION_OUTSIDE_T1' for s in delayed),missing_confirmation=sum(s['reason']=='MISSING_ADJACENT_CONFIRMATION' for s in delayed),missing_entry=sum(s['reason']=='MISSING_ADJACENT_OPEN' for s in delayed),unstretched_executed=sum(s['reason']=='EXECUTED_NEXT_OPEN' for s in events)))
 write_csv(out/'MECHANISM_SUMMARY.csv',mechanism)
 return receipt
