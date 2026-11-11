"""Separate scalar execution algorithm; event agenda rather than primary pending state.
Uses PR518's independent streaming indicators, never primary features/engine imports.
Same author: algorithmic verification, no external human/agent signoff.
"""
import csv,gzip,io,json,math
from datetime import datetime,timedelta
from zoneinfo import ZoneInfo
from pathlib import Path
from collections import defaultdict
from decimal import Decimal
STEP=timedelta(minutes=15)

def parse_development(path):
 with open(path) as f:
  previous=None
  for r in csv.DictReader(f,delimiter=';'):
   at=datetime.fromisoformat(r['Datetime']).replace(tzinfo=ZoneInfo('Europe/Moscow'))+STEP
   if at>=datetime(2025,1,1,tzinfo=ZoneInfo('Europe/Moscow')):break
   assert previous is None or at>previous;previous=at
   yield {'at':at}|{k:float(r[k]) for k in ('Open','High','Low','Close','Volume')}

def replay(bars,symbol,variant):
 output={k:[] for k in ('trades','OPEN','snapshots','stops','signals','marks')}
 agenda={};p=None;booked=0.;closed=0;prior=None;checks=0
 def side_name(n):return 'LONG' if n==1 else 'SHORT'
 def identity(s):return symbol+'|'+s['at'].isoformat()+'|'+side_name(s['Signal'])
 def base(pos):
  s=pos['s']
  return dict(instrument=symbol,trade_id=pos['id'],direction=side_name(pos['d']),signal_time=s['at'],entry_time=s['at'],signal_close=s['Close'],entry_price=pos['entry'],initial_stop=pos['initial'],initial_risk=pos['risk'],ATR=s['ATR'],H1AvailableAt=s['H1AvailableAt'],breakout_level=s['PriorHigh'] if pos['d']==1 else s['PriorLow'],actual_entry_time=pos['actual_entry'],execution_bar_close=pos['execution_close'],confirmed=pos['confirmed'])
 def snap(pos,b):return base(pos)|dict(month=b['at'].strftime('%Y-%m'),last_close=b['at'],last_close_price=b['Close'],active_stop=pos['stop'],unrealized_gross_R=pos['d']*(b['Close']-pos['entry'])/pos['risk'],status='OPEN_NOT_LIQUIDATED')
 for i,b in enumerate(bars):
  t=b['at'];exited=None;reserve=None
  if p and prior['at'].strftime('%Y-%m')!=t.strftime('%Y-%m'):output['snapshots'].append(snap(p,prior))
  task=agenda.pop(i,None)
  if task and task['stage']=='OPEN':
   s=task['s'];event=task['event']
   if t==task['due']:
    d=s['Signal'];entry=b['Open'];initial=entry-d*2*s['ATR']
    p=dict(s=s,id=event['trade_id'],d=d,entry=entry,initial=initial,risk=abs(entry-initial),stop=initial,extreme=entry,hi=entry,lo=entry,index=task['index'],updates=0,gaps=0,actual_entry=t-STEP,execution_close=t,confirmed=event['stretched_delay'])
    event.update(reason='EXECUTED_CONFIRMED_OPEN' if event['stretched_delay'] else 'EXECUTED_NEXT_OPEN',entry_accepted=True,entry_price=entry,initial_stop=initial,execution_bar_close=t,actual_entry_time=t-STEP)
   else:event.update(reason='MISSING_ADJACENT_OPEN',next_observed_close=t)
  if p:
   checks+=1;d=p['d'];old=p['stop'];gap=prior is not None and t>prior['at']+STEP;p['gaps']+=int(gap)
   opening=(b['Open']<=old if d==1 else b['Open']>=old)
   touched=opening or (b['Low']<=old if d==1 else b['High']>=old)
   event=dict(instrument=symbol,trade_id=p['id'],bar_close=t,active_stop=old,extreme_before=p['extreme'],ATR=b['ATR'],stop_hit=touched,observed_gap=gap,exit_price=None,next_stop=None,extreme_after=None,proposal=None)
   if touched:
    fill=b['Open'] if opening else old;profit=d*(fill-p['entry'])/p['risk'];booked+=profit
    trade=base(p)|dict(exit_time=t,exit_bar_open_time=t-STEP,exit_price=fill,gross_R=profit,active_stop_at_exit=old,exit_at_open=opening,gap_exit=fill!=old,exit_type='INITIAL_STOP' if old==p['initial'] else 'RATCHETED_STOP',trailing_updates=p['updates'],bars_held=i-p['index'],holding_minutes=(t-p['s']['at']).total_seconds()/60,observed_gaps_exposed=p['gaps'],MFE_R=max(0.,p['hi']-p['entry'] if d==1 else p['entry']-p['lo'])/p['risk'],MAE_R=max(0.,p['entry']-p['lo'] if d==1 else p['hi']-p['entry'],d*(p['entry']-fill))/p['risk'])
    output['trades'].append(trade);closed+=1;exited=p['id'];p=None;event['exit_price']=fill
   else:
    p['hi']=max(p['hi'],b['High']);p['lo']=min(p['lo'],b['Low']);p['extreme']=p['hi'] if d==1 else p['lo']
    proposal=p['extreme']-d*3.5*b['ATR'];new=max(old,proposal) if d==1 else min(old,proposal)
    p['updates']+=int(new!=old);p['stop']=new;event.update(next_stop=new,proposal=proposal,extreme_after=p['extreme'])
   output['stops'].append(event)
  if task and task['stage']=='CONFIRM':
   s=task['s'];event=task['event'];d=s['Signal'];level=s['PriorHigh'] if d==1 else s['PriorLow']
   adjacent=t==task['due'];session=10<=t.hour<18
   price=(b['Close']>s['Close'] and b['Close']>level) if d==1 else (b['Close']<s['Close'] and b['Close']<level)
   event.update(confirmation_time=t,confirmation_close=b['Close'],confirmation_adjacent=adjacent,confirmation_in_T1=session,confirmation_price_pass=price)
   if not adjacent:event['reason']='MISSING_ADJACENT_CONFIRMATION'
   elif not session:event['reason']='CONFIRMATION_OUTSIDE_T1'
   elif not price:event['reason']='CONFIRMATION_FAILED'
   else:
    event.update(reason='PENDING_CONFIRMED_OPEN',ready_time=t)
    reserve=task|dict(stage='OPEN',due=t+STEP);agenda[i+1]=reserve
  if b['Signal'] and math.isfinite(b['ATR']):
   d=b['Signal'];allowed=10<=t.hour<18;occupied=p is not None;reserved=reserve is not None;take=allowed and not occupied and not reserved
   ident=f'T3-M15-{{}}-{closed+1:06d}'.format({'USDRUBF':'Si','CNYRUBF':'CNY'}.get(symbol,symbol)) if take else None
   reason='ACCEPTED' if take else 'CONFIRMATION_ENTRY_RESERVED' if reserved else 'OUTSIDE_T1_AND_OCCUPIED' if occupied and not allowed else 'POSITION_OCCUPIED' if occupied else 'OUTSIDE_T1'
   distance=d*(b['Close']-(b['PriorHigh'] if d==1 else b['PriorLow']))/b['ATR'];delay=variant=='CONFIRM' and distance>=.5
   event=dict(instrument=symbol,signal_id=identity(b),signal_time=t,direction=side_name(d),signal_close=b['Close'],ATR=b['ATR'],H1AvailableAt=b['H1AvailableAt'],PriorHigh=b['PriorHigh'],PriorLow=b['PriorLow'],rule_pass=allowed,position_occupied=occupied,occupied_trade_id=p['id'] if occupied else None,same_close_exit_trade_id=exited,entry_accepted=False,reason=reason,trade_id=ident,entry_price=None,initial_stop=None,execution_bar_close=None,next_observed_close=None,breakout_ATR=distance,pending_reserved=reserved,stretched_delay=delay,ready_time=t,confirmation_time=None,confirmation_close=None,confirmation_adjacent=None,confirmation_in_T1=None,confirmation_price_pass=None,actual_entry_time=None)
   output['signals'].append(event)
   if take:
    event['reason']='PENDING_CONFIRMATION' if delay else 'PENDING_NEXT_OPEN'
    agenda[i+1]=dict(stage='CONFIRM' if delay else 'OPEN',due=t+STEP,s=b,index=i,event=event)
  waiting=agenda.get(i+1)
  un=p['d']*(b['Close']-p['entry'])/p['risk'] if p else 0.
  output['marks'].append(dict(instrument=symbol,variant=variant,at=t,gross_realized_R=booked,gross_unrealized_R=un,gross_MTM_R=booked+un,position_trade_id=p['id'] if p else None,waiting_signal_id=waiting['event']['signal_id'] if waiting else None,waiting_stage=('ENTRY_OPEN' if waiting['stage']=='OPEN' else 'CONFIRMATION_CLOSE') if waiting else None))
  prior=b
 for task in agenda.values():task['event']['reason']='UNRESOLVED_END_OF_DATA' if task['stage']=='OPEN' else 'UNRESOLVED_CONFIRMATION_END_OF_DATA'
 if p:output['OPEN'].append(snap(p,bars[-1]));output['snapshots'].extend(output['OPEN'])
 output['occupancy']=[dict(instrument=symbol,observed_bars=len(bars),stop_checked_bars=checks,denominator=len(bars)-1,occupancy=checks/(len(bars)-1) if len(bars)>1 else None)]
 return output

def read(path):
 raw=Path(path).read_bytes();raw=gzip.decompress(raw) if str(path).endswith('.gz') else raw
 return list(csv.DictReader(io.StringIO(raw.decode())))

def verify(data,out,scalar):
 counts=dict(rows=0,fields=0);max_error=0.;fresh={m:{k:[] for k in ('trades','OPEN','snapshots','stops','signals','marks','occupancy')} for m in ('CONTROL','CONFIRM')}
 def compare(actual,expected,label):
  nonlocal max_error
  assert len(actual)==len(expected),(label,len(actual),len(expected));counts['rows']+=len(actual)
  for j,(a,e) in enumerate(zip(actual,expected)):
   for k,x in a.items():
    counts['fields']+=1;y=e[k]
    if x is None or isinstance(x,float) and not math.isfinite(x):assert y=='',(label,j,k,x,y)
    elif isinstance(x,bool):assert str(x)==y,(label,j,k,x,y)
    elif isinstance(x,(int,float)):
     err=abs(x-float(y));max_error=max(err,max_error);assert err<1e-8,(label,j,k,x,y)
    else:assert (x.isoformat() if hasattr(x,'isoformat') else str(x))==y,(label,j,k,x,y)
 for s in ('USDRUBF','CNYRUBF','GLDRUBF','IMOEXF'):
  bars=list(scalar.feature_stream(parse_development(data/f'forever/{s}/{s}_M15.csv')))
  derived=[{k:v for k,v in b.items() if k not in ('Open','High','Low','Close','Volume','H1Close')} for b in bars]
  compare(derived,read(out/'features'/f'{s}.csv.gz'),'features '+s)
  for mode in fresh:
   result=replay(bars,s,mode)
   for table,rows in result.items():fresh[mode][table].extend(rows)
 for mode,tables in fresh.items():
  for table,rows in tables.items():compare(rows,read(out/(mode+'_'+table+'.csv'+('.gz' if table in ('signals','stops','marks') else ''))),mode+' '+table)
 # Fresh CSV / Decimal calendar arithmetic, independent of report functions and floats.
 arithmetic=0
 for mode in fresh:
  trades=read(out/(mode+'_trades.csv'));marks=read(out/(mode+'_marks.csv.gz'))
  grouped=defaultdict(list)
  for r in trades:grouped[r['exit_time'][:7]].append(Decimal(r['gross_R']))
  ends={}
  for r in marks:ends[(r['instrument'],r['at'][:7])]=Decimal(r['gross_MTM_R'])
  previous=Decimal(0)
  for r in [r for r in read(out/'MONTHLY.csv') if r['variant']==mode]:
   closed=sum(grouped[r['month']],Decimal(0));mtm=sum((ends[(s,r['month'])] for s in ('USDRUBF','CNYRUBF','GLDRUBF','IMOEXF') if (s,r['month']) in ends),Decimal(0))
   assert abs(closed-Decimal(r['CLOSED_R']))<Decimal('1e-8');assert abs((mtm-previous)-Decimal(r['MTM_R']))<Decimal('1e-8');previous=mtm;arithmetic+=2
  rs=[Decimal(r['gross_R']) for r in trades];total=sum(rs,Decimal(0));pos=sum((x for x in rs if x>0),Decimal(0));neg=-sum((x for x in rs if x<0),Decimal(0))
  r=next(r for r in read(out/'SUMMARY.csv') if r['variant']==mode and r['period']=='2023_2024')
  for field,x in [('gross_R',total),('gross_PF',pos/neg),('expectancy_R',total/len(rs))]:assert abs(x-Decimal(r[field]))<Decimal('1e-8');arithmetic+=1
 import stats_verifier
 extra=stats_verifier.audit(out)
 return dict(independent_statistics=extra,status='PASS',**counts,max_abs_error=max_error,Decimal_calendar_and_aggregate_fields=arithmetic,external_review='NOT_PERFORMED',independence='Separate event-agenda scalar execution and PR518 streaming EWM; same author; no primary engine/features or report imports')
