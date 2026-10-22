"""Independent fresh-CSV Decimal metrics/cohort audit, no report/analysis imports."""
import csv,gzip,io
from collections import defaultdict
from decimal import Decimal
D=Decimal;ZERO=D(0);EPS=D('1e-8')

def read(p):
 b=p.read_bytes();b=gzip.decompress(b) if str(p).endswith('.gz') else b
 return list(csv.DictReader(io.StringIO(b.decode())))

def drawdown(values):
 peak=ZERO;worst=ZERO
 for v in values:
  if v>peak:peak=v
  if peak-v>worst:worst=peak-v
 return worst

def audit(out):
 checked=0
 def eq(a,b,label):
  nonlocal checked
  checked+=1
  if a is None:assert b=='',(label,a,b)
  elif isinstance(a,(int,Decimal)):assert abs(D(a)-D(b))<EPS,(label,a,b)
  else:assert str(a)==b,(label,a,b)
 monthly=read(out/'MONTHLY.csv');summaries=read(out/'SUMMARY.csv');data={}
 for mode in ('CONTROL','BE1'):
  tt=read(out/(mode+'_trades.csv'));op=read(out/(mode+'_OPEN.csv'));marks=read(out/(mode+'_marks.csv.gz'));snaps=read(out/(mode+'_snapshots.csv'));data[mode]=(tt,op)
  indexed=defaultdict(dict)
  for x in marks:indexed[x['at']][x['instrument']]=D(x['gross_MTM_R'])
  state=defaultdict(lambda:ZERO);curve=[];end={}
  for t,changes in sorted(indexed.items()):
   state.update(changes);v=sum(state.values(),ZERO);curve.append((t,v));end[t[:7]]=v
  prev=ZERO;ind_month={}
  for m in sorted(end):
   closed=sum((D(t['gross_R']) for t in tt if t['exit_time'].startswith(m)),ZERO);mtm=end[m]-prev;prev=end[m]
   ind_month[m]=(closed,mtm)
  for r in [x for x in monthly if x['variant']==mode]:
   a,b=ind_month[r['month']];eq(a,r['CLOSED_R'],mode+' monthly closed');eq(b,r['MTM_R'],mode+' monthly MTM')
   eq(1 if a>EPS else -1 if a< -EPS else 0,r['CLOSED_sign'],'closed sign');eq(1 if b>EPS else -1 if b< -EPS else 0,r['MTM_sign'],'MTM sign')
  for row in [x for x in summaries if x['variant']==mode]:
   period=row['period'];trades=tt if period=='2023_2024' else [t for t in tt if t['exit_time'].startswith(period)]
   ordered=sorted(trades,key=lambda t:(t['exit_time'],t['instrument'],t['trade_id']));rs=[D(t['gross_R']) for t in ordered];total=sum(rs,ZERO);pos=sum((r for r in rs if r>0),ZERO);neg=-sum((r for r in rs if r<0),ZERO)
   equity=[];running=ZERO
   for r in rs:running+=r;equity.append(running)
   selected=curve if period=='2023_2024' else [(t,v) for t,v in curve if t.startswith(period)]
   before=[v for t,v in curve if t<selected[0][0]];initial=before[-1] if before else ZERO
   fields=dict(CLOSED=len(rs),gross_R=total,gross_positive_R=pos,gross_negative_R=-neg,gross_PF=pos/neg if neg else None,expectancy_R=total/len(rs),CLOSED_R_DD=drawdown(equity),MTM_R_DD=drawdown([v-initial for _,v in selected]),winner_ge_2R_count=sum(r>=2 for r in rs),winner_ge_2R_R=sum((r for r in rs if r>=2),ZERO),OPEN_at_period_end=sum(s['month']==selected[-1][0][:7] for s in snaps))
   for name,x in fields.items():eq(x,row[name],mode+' '+period+' '+name)
   months=[(m,vals) for m,vals in ind_month.items() if period=='2023_2024' or m.startswith(period)]
   for col,i in [('CLOSED_R',0),('MTM_R',1)]:
    worst=min(months,key=lambda x:x[1][i]);eq(sum(vals[i]<-EPS for _,vals in months),row[col+'_negative_months'],'negative months');eq(sum((vals[i] for _,vals in months if vals[i]<-EPS),ZERO),row[col+'_negative_sum'],'negative sum');eq(worst[0],row[col+'_worst_month'],'worst month');eq(worst[1][i],row[col+'_worst_R'],'worst R')
 def key(t):return (t['instrument'],t['signal_time'],t['direction'])
 indices=[]
 for mode in ('CONTROL','BE1'):
  tt,op=data[mode];indices.append({key(t):t|{'status':'CLOSED'} for t in tt}|{key(t):t|{'status':'OPEN'} for t in op})
 aa,bb=indices;rows=read(out/'TRADE_COMPARISON.csv');assert len(rows)==len(aa.keys()|bb.keys())
 derived=[]
 for r in rows:
  k=key(r);a,b=aa.get(k),bb.get(k);ar=D(a['gross_R']) if a and a['status']=='CLOSED' else None;br=D(b['gross_R']) if b and b['status']=='CLOSED' else None
  match='COMMON_SIGNAL' if a and b else 'MISSED_CONTROL_ENTRY' if a else 'NEW_BE1_ENTRY';eq(match,r['match'],'match')
  eq(ar,r['CONTROL_R'],'CONTROL_R');eq(br,r['BE1_R'],'BE1_R');eq(br-ar if ar is not None and br is not None else None,r['delta_R'],'delta')
  early=ar is not None and br is not None and b['exit_time']<a['exit_time'];nt=ar is not None and ar<0 and a['exit_type']=='RATCHETED_STOP'
  flags=dict(CONTROL_winner=ar is not None and ar>0,CONTROL_large_winner=ar is not None and ar>=2,closed_earlier=early,profitable_closed_earlier=ar is not None and ar>0 and early,missed_profitable=ar is not None and ar>0 and b is None,profitable_to_nonpositive=ar is not None and ar>0 and br is not None and br<=0,profitable_to_OPEN=ar is not None and ar>0 and b is not None and b['status']=='OPEN',profitable_reduced=ar is not None and ar>0 and br is not None and ZERO<br<ar-EPS,CONTROL_negative_trailing=nt,negative_trailing_prevented=nt and br is not None and br>=0,negative_trailing_missed=nt and b is None,negative_trailing_still_negative=nt and br is not None and br<0,negative_trailing_OPEN=nt and b is not None and b['status']=='OPEN')
  for name,x in flags.items():eq(str(x),r[name],name)
  if a and b:
   for name in ('entry_price','initial_risk','initial_stop'):eq(D(a[name]),b[name],'immutable common '+name)
  derived.append(dict(signal_year=k[1][:4],ar=ar,br=br,match=match,**flags))
 import json
 receipts=json.loads((out/'COMPARISON.json').read_text())
 for year,receipt in receipts.items():
  rr=[r for r in derived if year=='2023_2024' or r['signal_year']==year]
  values={name:sum(r[name] for r in rr) for name in ('profitable_closed_earlier','missed_profitable','profitable_to_nonpositive','profitable_to_OPEN','profitable_reduced','CONTROL_negative_trailing','negative_trailing_prevented','negative_trailing_missed','negative_trailing_still_negative','negative_trailing_OPEN')}
  values.update(common_signals=sum(r['match']=='COMMON_SIGNAL' for r in rr),missed_control_entries=sum(r['match']=='MISSED_CONTROL_ENTRY' for r in rr),new_BE1_entries=sum(r['match']=='NEW_BE1_ENTRY' for r in rr),new_entries_R=sum((r['br'] for r in rr if r['match']=='NEW_BE1_ENTRY' and r['br'] is not None),ZERO),missed_entries_CONTROL_R=sum((r['ar'] for r in rr if r['match']=='MISSED_CONTROL_ENTRY' and r['ar'] is not None),ZERO),matched_delta_R=sum((r['br']-r['ar'] for r in rr if r['ar'] is not None and r['br'] is not None),ZERO),early_profitable_CONTROL_R=sum((r['ar'] for r in rr if r['profitable_closed_earlier']),ZERO),early_profitable_BE1_R=sum((r['br'] for r in rr if r['profitable_closed_earlier']),ZERO),prevented_trailing_CONTROL_R=sum((r['ar'] for r in rr if r['negative_trailing_prevented']),ZERO),prevented_trailing_BE1_R=sum((r['br'] for r in rr if r['negative_trailing_prevented']),ZERO))
  assert values.keys()==receipt.keys()
  for name,x in values.items():eq(x,str(receipt[name]),year+' receipt '+name)
 for row in read(out/'ORIGINAL_GE_2R_BY_YEAR.csv'):
  year=row['signal_year'];rr=[r for r in derived if r['CONTROL_large_winner'] and (year=='2023_2024' or r['signal_year']==year)];alt=[r['br'] for r in rr if r['br'] is not None]
  values=dict(original_ge2R_count=len(rr),CONTROL_R=sum((r['ar'] for r in rr),ZERO),retained_ge2R=sum(x>=2 for x in alt),skipped=sum(r['match']=='MISSED_CONTROL_ENTRY' for r in rr),OPEN=sum(r['br'] is None and r['match']=='COMMON_SIGNAL' for r in rr),to_nonpositive=sum(x<=0 for x in alt),closed_earlier=sum(r['closed_earlier'] for r in rr),BE1_CLOSED_contribution_R=sum(alt,ZERO))
  for name,x in values.items():eq(x,row[name],'year cohort '+name)
 for row in read(out/'MECHANISM_SUMMARY.csv'):
  mode=row['variant'];year=row['exit_or_event_year'];tt=[t for t in data[mode][0] if year=='2023_2024' or t['exit_time'].startswith(year)];events=[e for e in read(out/(mode+'_stops.csv.gz')) if year=='2023_2024' or e['bar_close'].startswith(year)]
  nt=[t for t in tt if D(t['gross_R'])<0 and t['exit_type']=='RATCHETED_STOP']
  values=dict(CLOSED=len(tt),negative_trailing_count=len(nt),negative_trailing_R=sum((D(t['gross_R']) for t in nt),ZERO),negative_initial_count=sum(D(t['gross_R'])<0 and t['exit_type']=='INITIAL_STOP' for t in tt),negative_trades=sum(D(t['gross_R'])<0 for t in tt),zero_trades=sum(D(t['gross_R'])==0 for t in tt),BE1_reached_events=sum(e['BE1_reached_now']=='True' for e in events),BE1_stop_raises=sum(e['BE1_raised_now']=='True' for e in events),BE1_source_exits=sum(t['stop_source']=='BE1' for t in tt),BE1_source_negative_gap_exits=sum(t['stop_source']=='BE1' and D(t['gross_R'])<0 for t in tt))
  for name,x in values.items():eq(x,row[name],'mechanism '+name)
 return dict(status='PASS',fresh_CSV_Decimal_fields=checked,scope='all requested aggregate/year/month metrics, drawdowns, every cohort row, early profitable exits, >=2R winners, negative trailing prevention and new/missed entries')
