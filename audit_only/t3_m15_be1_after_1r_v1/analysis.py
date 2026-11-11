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
   sa,sb=sign(a[basis]),sign(b[basis]);transitions.append(dict(month=month,basis=basis,CONTROL_R=a[basis],BE1_R=b[basis],delta_R=b[basis]-a[basis],CONTROL_sign=sa,BE1_sign=sb,sign_changed=sa!=sb,transition=f'{sa}_TO_{sb}'))
 for name,rows in [('SUMMARY',summary),('MONTHLY',monthly),('MONTH_SIGN_TRANSITIONS',transitions),('COVERAGE',coverage),('PORTFOLIO_CURVES',curves)]:write_csv(out/(name+'.csv'+('.gz' if name=='PORTFOLIO_CURVES' else '')),rows)
 sensitivity=[]
 for mode,r in models.items():
  rs=[t|{'gross_R':t['gross_R']-cost-slippage} for t in r['trades']]
  sensitivity.append(dict(variant=mode,round_trip_cost_R=cost,round_trip_slippage_R=slippage,scope='NORMALIZED_R_SENSITIVITY_NOT_EXECUTABLE_NET',**statistics(rs)))
 write_csv(out/'NORMALIZED_COST_SENSITIVITY.csv',sensitivity)
 return summary,monthly,transitions

def comparisons(models,out):
 def key(t):return (t['instrument'],t['signal_time'],t['direction'])
 indices=[{key(t):t|{'status':status} for table,status in [('trades','CLOSED'),('OPEN','OPEN')] for t in r[table]} for r in models.values()]
 aa,bb=indices;rows=[]
 for k in sorted(aa.keys()|bb.keys()):
  a,b=aa.get(k),bb.get(k);x,y=a or {},b or {};ar=x.get('gross_R');br=y.get('gross_R')
  common=a is not None and b is not None
  if common:
   assert a['entry_price']==b['entry_price'] and a['initial_risk']==b['initial_risk'] and a['initial_stop']==b['initial_stop']
  both=ar is not None and br is not None
  early=bool(both and b['exit_time']<a['exit_time'])
  negative_trail=bool(ar is not None and ar<0 and a['exit_type']=='RATCHETED_STOP')
  row=dict(instrument=k[0],signal_time=k[1],direction=k[2],match='COMMON_SIGNAL' if common else 'MISSED_CONTROL_ENTRY' if a else 'NEW_BE1_ENTRY',CONTROL_status=x.get('status'),BE1_status=y.get('status'),CONTROL_trade_id=x.get('trade_id'),BE1_trade_id=y.get('trade_id'),CONTROL_R=ar,BE1_R=br,delta_R=br-ar if both else None,CONTROL_entry=x.get('entry_price'),BE1_entry=y.get('entry_price'),CONTROL_R0=x.get('initial_risk'),BE1_R0=y.get('initial_risk'),CONTROL_exit_time=x.get('exit_time'),BE1_exit_time=y.get('exit_time'),CONTROL_exit_type=x.get('exit_type'),BE1_stop_source=y.get('stop_source'),BE1_raised=y.get('BE1_raised'),CONTROL_winner=ar is not None and ar>0,CONTROL_large_winner=ar is not None and ar>=2,closed_earlier=early,profitable_closed_earlier=bool(ar is not None and ar>0 and early),missed_profitable=bool(ar is not None and ar>0 and not b),profitable_to_nonpositive=bool(ar is not None and ar>0 and br is not None and br<=0),profitable_to_OPEN=bool(ar is not None and ar>0 and b and b['status']=='OPEN'),profitable_reduced=bool(ar is not None and ar>0 and br is not None and 0<br<ar-EPS),CONTROL_negative_trailing=negative_trail,negative_trailing_prevented=bool(negative_trail and br is not None and br>=0),negative_trailing_missed=bool(negative_trail and not b),negative_trailing_still_negative=bool(negative_trail and br is not None and br<0),negative_trailing_OPEN=bool(negative_trail and b and b['status']=='OPEN'))
  rows.append(row)
 write_csv(out/'TRADE_COMPARISON.csv',rows)
 for name,predicate in [('NEW_AND_MISSED_ENTRIES',lambda r:r['match']!='COMMON_SIGNAL'),('EARLY_PROFITABLE_EXITS',lambda r:r['profitable_closed_earlier']),('ORIGINAL_GE_2R_WINNERS',lambda r:r['CONTROL_large_winner']),('NEGATIVE_TRAILING_COHORT',lambda r:r['CONTROL_negative_trailing'])]:write_csv(out/(name+'.csv'),[r for r in rows if predicate(r)],fields=list(rows[0]))
 cohort=[]
 for year in ('2023_2024','2023','2024'):
  rr=[r for r in rows if year=='2023_2024' or str(r['signal_time'].year)==year];large=[r for r in rr if r['CONTROL_large_winner']]
  cohort.append(dict(signal_year=year,original_ge2R_count=len(large),CONTROL_R=math.fsum(r['CONTROL_R'] for r in large),retained_ge2R=sum(r['BE1_R'] is not None and r['BE1_R']>=2 for r in large),skipped=sum(r['BE1_status'] is None for r in large),OPEN=sum(r['BE1_status']=='OPEN' for r in large),to_nonpositive=sum(r['BE1_R'] is not None and r['BE1_R']<=0 for r in large),closed_earlier=sum(r['closed_earlier'] for r in large),BE1_CLOSED_contribution_R=math.fsum(r['BE1_R'] for r in large if r['BE1_R'] is not None)))
 write_csv(out/'ORIGINAL_GE_2R_BY_YEAR.csv',cohort)
 receipt={}
 for year in ('2023_2024','2023','2024'):
  rr=[r for r in rows if year=='2023_2024' or str(r['signal_time'].year)==year]
  fields=('profitable_closed_earlier','missed_profitable','profitable_to_nonpositive','profitable_to_OPEN','profitable_reduced','CONTROL_negative_trailing','negative_trailing_prevented','negative_trailing_missed','negative_trailing_still_negative','negative_trailing_OPEN')
  d={f:sum(r[f] for r in rr) for f in fields}
  d.update(common_signals=sum(r['match']=='COMMON_SIGNAL' for r in rr),missed_control_entries=sum(r['match']=='MISSED_CONTROL_ENTRY' for r in rr),new_BE1_entries=sum(r['match']=='NEW_BE1_ENTRY' for r in rr),new_entries_R=math.fsum(r['BE1_R'] for r in rr if r['match']=='NEW_BE1_ENTRY' and r['BE1_R'] is not None),missed_entries_CONTROL_R=math.fsum(r['CONTROL_R'] for r in rr if r['match']=='MISSED_CONTROL_ENTRY' and r['CONTROL_R'] is not None),matched_delta_R=math.fsum(r['delta_R'] for r in rr if r['delta_R'] is not None),early_profitable_CONTROL_R=math.fsum(r['CONTROL_R'] for r in rr if r['profitable_closed_earlier']),early_profitable_BE1_R=math.fsum(r['BE1_R'] for r in rr if r['profitable_closed_earlier']),prevented_trailing_CONTROL_R=math.fsum(r['CONTROL_R'] for r in rr if r['negative_trailing_prevented']),prevented_trailing_BE1_R=math.fsum(r['BE1_R'] for r in rr if r['negative_trailing_prevented']))
  receipt[year]=d
 write_json(out/'COMPARISON.json',receipt)
 mechanism=[]
 for mode,r in models.items():
  for year in ('2023_2024','2023','2024'):
   trades=[t for t in r['trades'] if year=='2023_2024' or str(t['exit_time'].year)==year]
   events=[s for s in r['stops'] if year=='2023_2024' or str(s['bar_close'].year)==year]
   mechanism.append(dict(variant=mode,exit_or_event_year=year,CLOSED=len(trades),negative_trailing_count=sum(t['gross_R']<0 and t['exit_type']=='RATCHETED_STOP' for t in trades),negative_trailing_R=math.fsum(t['gross_R'] for t in trades if t['gross_R']<0 and t['exit_type']=='RATCHETED_STOP'),negative_initial_count=sum(t['gross_R']<0 and t['exit_type']=='INITIAL_STOP' for t in trades),negative_trades=sum(t['gross_R']<0 for t in trades),zero_trades=sum(t['gross_R']==0 for t in trades),BE1_reached_events=sum(s['BE1_reached_now'] for s in events),BE1_stop_raises=sum(s['BE1_raised_now'] for s in events),BE1_source_exits=sum(t['stop_source']=='BE1' for t in trades),BE1_source_negative_gap_exits=sum(t['stop_source']=='BE1' and t['gross_R']<0 for t in trades)))
 write_csv(out/'MECHANISM_SUMMARY.csv',mechanism)
 return receipt
