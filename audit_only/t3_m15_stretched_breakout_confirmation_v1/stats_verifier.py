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
 for mode in ('CONTROL','CONFIRM'):
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
 # Audit every signal-matched cohort row and requested preservation/loss counts.
 def key(t):return (t['instrument'],t['signal_time'],t['direction'])
 indices=[]
 for mode in ('CONTROL','CONFIRM'):
  tt,op=data[mode];indices.append({key(t):t|{'status':'CLOSED'} for t in tt}|{key(t):t|{'status':'OPEN'} for t in op})
 aa,bb=indices;rows=read(out/'TRADE_COMPARISON.csv');assert len(rows)==len(aa.keys()|bb.keys())
 counts=defaultdict(int);sums=defaultdict(lambda:ZERO)
 for r in rows:
  k=key(r);a,b=aa.get(k),bb.get(k);ar=D(a['gross_R']) if a and a['status']=='CLOSED' else None;br=D(b['gross_R']) if b and b['status']=='CLOSED' else None
  match='COMMON_SIGNAL' if a and b else 'MISSED_CONTROL_ENTRY' if a else 'NEW_CONFIRM_ENTRY';eq(match,r['match'],'match')
  eq(ar,r['CONTROL_R'],'CONTROL_R');eq(br,r['CONFIRM_R'],'CONFIRM_R')
  for x,prefix in [(a,'CONTROL'),(b,'CONFIRM')]:eq(x['status'] if x else None,r[prefix+'_status'],'status')
  flags=dict(CONTROL_winner=ar is not None and ar>0,CONTROL_large_winner=ar is not None and ar>=2,missed_profitable=ar is not None and ar>0 and b is None,profitable_to_nonpositive=ar is not None and ar>0 and br is not None and br<=0,profitable_to_OPEN=ar is not None and ar>0 and b is not None and b['status']=='OPEN',profitable_reduced=ar is not None and ar>0 and br is not None and ZERO<br<ar-EPS)
  for f,x in flags.items():eq(str(x),r[f],f)
  counts[match]+=1
  for f in ('missed_profitable','profitable_to_nonpositive','profitable_to_OPEN','profitable_reduced'):counts[f]+=int(flags[f])
  if flags['missed_profitable']:sums['missed_profitable_CONTROL_R']+=ar
  if match=='MISSED_CONTROL_ENTRY' and ar is not None:sums['missed_entries_CONTROL_R']+=ar
  if match=='NEW_CONFIRM_ENTRY' and br is not None:sums['new_entries_R']+=br
  if flags['CONTROL_large_winner']:
   counts['original_ge2R_count']+=1;sums['original_ge2R_R']+=ar
   counts['original_ge2R_still_ge2R']+=int(br is not None and br>=2);counts['original_ge2R_skipped']+=int(b is None);counts['original_ge2R_OPEN']+=int(b is not None and b['status']=='OPEN');counts['original_ge2R_to_nonpositive']+=int(br is not None and br<=0)
   if br is not None:sums['original_ge2R_CONFIRMED_CLOSED_contribution_R']+=br
  if ar is not None and br is not None:
   side=1 if k[2]=='LONG' else -1;entry=D(side)*(D(b['entry_price'])-D(a['entry_price']))/D(a['initial_risk']);exit=D(side)*(D(b['exit_price'])-D(a['exit_price']))/D(a['initial_risk']);pnl=D(side)*(D(b['exit_price'])-D(b['entry_price']))/D(a['initial_risk'])
   for f,x in [('entry_penalty_CONTROL_R0',entry),('exit_delta_CONTROL_R0',exit),('CONFIRM_PNL_in_CONTROL_R0',pnl),('delta_PNL_CONTROL_R0',pnl-ar)]:eq(x,r[f],f)
 import json
 receipt=json.loads((out/'COMPARISON.json').read_text());counts['common_signals']=counts.pop('COMMON_SIGNAL');counts['missed_control_entries']=counts.pop('MISSED_CONTROL_ENTRY');counts['new_confirm_entries']=counts.pop('NEW_CONFIRM_ENTRY')
 for name in receipt:
  value=counts[name] if name in counts else sums[name];eq(value,str(receipt[name]),name)
 for row in read(out/'ORIGINAL_GE_2R_BY_YEAR.csv'):
  year=row['signal_year'];cohort=[(k,a,bb.get(k)) for k,a in aa.items() if a['status']=='CLOSED' and D(a['gross_R'])>=2 and (year=='2023_2024' or a['signal_time'].startswith(year))]
  alt=[D(b['gross_R']) for _,a,b in cohort if b and b['status']=='CLOSED']
  values=dict(original_ge2R_count=len(cohort),CONTROL_R=sum((D(a['gross_R']) for _,a,b in cohort),ZERO),retained_ge2R=sum(x>=2 for x in alt),skipped=sum(b is None for _,a,b in cohort),to_nonpositive=sum(x<=0 for x in alt),OPEN=sum(b is not None and b['status']=='OPEN' for _,a,b in cohort),CONFIRM_CLOSED_contribution_R=sum(alt,ZERO))
  for name,x in values.items():eq(x,row[name],'year cohort '+name)
 signals=read(out/'CONFIRM_signals.csv.gz')
 for row in read(out/'MECHANISM_SUMMARY.csv'):
  year=row['signal_year'];attempts=[x for x in signals if x['trade_id'] and (year=='2023_2024' or x['signal_time'].startswith(year))];delayed=[x for x in attempts if x['stretched_delay']=='True']
  values=dict(eligible_attempts=len(attempts),stretched_attempts=len(delayed),executed_confirmed=sum(x['reason']=='EXECUTED_CONFIRMED_OPEN' for x in delayed),failed_price=sum(x['reason']=='CONFIRMATION_FAILED' for x in delayed),outside_T1=sum(x['reason']=='CONFIRMATION_OUTSIDE_T1' for x in delayed),missing_confirmation=sum(x['reason']=='MISSING_ADJACENT_CONFIRMATION' for x in delayed),missing_entry=sum(x['reason']=='MISSING_ADJACENT_OPEN' for x in delayed),unstretched_executed=sum(x['reason']=='EXECUTED_NEXT_OPEN' for x in attempts))
  for name,x in values.items():eq(x,row[name],'mechanism '+name)
 return dict(status='PASS',fresh_CSV_Decimal_fields=checked,scope='all requested aggregate/year/month metrics, drawdowns, every cohort row, lost and >=2R winners, new/missed entries, CONTROL_R0 decomposition')
