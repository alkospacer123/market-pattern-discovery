"""Independent event-agenda scalar replay. Same author; no external signoff.
Streaming indicators from PR518 scalar verifier; no primary feature/replay imports.
"""
import csv,gzip,io,math
from datetime import datetime,timedelta
from zoneinfo import ZoneInfo
from pathlib import Path
STEP=timedelta(minutes=15)

def parse_development(path):
 previous=None
 with open(path) as f:
  for row in csv.DictReader(f,delimiter=';'):
   t=datetime.fromisoformat(row['Datetime']).replace(tzinfo=ZoneInfo('Europe/Moscow'))+STEP
   if t>=datetime(2025,1,1,tzinfo=ZoneInfo('Europe/Moscow')):break
   assert previous is None or t>previous;previous=t
   assert row['Ticker']==Path(path).parent.name
   b={'at':t}|{k:float(row[k]) for k in ('Open','High','Low','Close','Volume')}
   assert all(math.isfinite(b[k]) for k in ('Open','High','Low','Close','Volume'))
   assert b['Low']<=min(b['Open'],b['Close'])<=max(b['Open'],b['Close'])<=b['High']
   yield b

def replay(bars,symbol,variant):
 out={k:[] for k in ('trades','OPEN','snapshots','stops','signals','marks')}
 agenda={};p=None;booked=0.;closed=0;prior=None;checks=0
 def side(d):return 'LONG' if d==1 else 'SHORT'
 def base(p):
  s=p['signal']
  return dict(instrument=symbol,trade_id=p['id'],direction=side(p['d']),signal_time=s['at'],entry_time=s['at'],signal_close=s['Close'],entry_price=p['entry'],initial_stop=p['initial'],initial_risk=p['risk'],ATR=s['ATR'],H1AvailableAt=s['H1AvailableAt'],breakout_level=s['PriorHigh'] if p['d']==1 else s['PriorLow'],actual_entry_time=s['at'],execution_bar_close=s['at']+STEP,BE1_reached=p['reached'],BE1_raised=p['raised'],BE1_activation_time=p['activation'],stop_source=p['source'])
 def snap(p,b):return base(p)|dict(month=b['at'].strftime('%Y-%m'),last_close=b['at'],last_close_price=b['Close'],active_stop=p['stop'],unrealized_gross_R=p['d']*(b['Close']-p['entry'])/p['risk'],status='OPEN_NOT_LIQUIDATED')
 for i,b in enumerate(bars):
  t=b['at'];exited=None
  if p and prior['at'].strftime('%Y-%m')!=t.strftime('%Y-%m'):out['snapshots'].append(snap(p,prior))
  task=agenda.pop(i,None)
  if task:
   signal,index,event=task
   assert p is None
   if t==signal['at']+STEP:
    d=signal['Signal'];price=b['Open'];initial=price-d*2*signal['ATR']
    p=dict(signal=signal,id=event['trade_id'],d=d,entry=price,initial=initial,risk=abs(price-initial),stop=initial,extreme=price,hi=price,lo=price,index=index,updates=0,gaps=0,reached=False,raised=False,activation=None,source='INITIAL')
    event.update(reason='EXECUTED_NEXT_OPEN',entry_accepted=True,entry_price=price,initial_stop=initial,execution_bar_close=t)
   else:event.update(reason='MISSING_ADJACENT_OPEN',next_observed_close=t)
  if p:
   checks+=1;d=p['d'];old=p['stop'];gap=prior is not None and t>prior['at']+STEP;p['gaps']+=int(gap)
   opening=b['Open']<=old if d==1 else b['Open']>=old
   touched=opening or (b['Low']<=old if d==1 else b['High']>=old)
   event=dict(instrument=symbol,trade_id=p['id'],bar_close=t,active_stop=old,extreme_before=p['extreme'],ATR=b['ATR'],stop_hit=touched,observed_gap=gap,exit_price=None,next_stop=None,extreme_after=None,proposal=None,BE1_reached_now=False,BE1_raised_now=False,BE1_eligible_next_observed=False,stop_source_before=p['source'],stop_source_after=None)
   if touched:
    fill=b['Open'] if opening else old;profit=d*(fill-p['entry'])/p['risk'];booked+=profit
    out['trades'].append(base(p)|dict(exit_time=t,exit_bar_open_time=t-STEP,exit_price=fill,gross_R=profit,active_stop_at_exit=old,exit_at_open=opening,gap_exit=fill!=old,exit_type='INITIAL_STOP' if old==p['initial'] else 'RATCHETED_STOP',trailing_updates=p['updates'],bars_held=i-p['index'],holding_minutes=(t-p['signal']['at']).total_seconds()/60,observed_gaps_exposed=p['gaps'],MFE_R=max(0.,p['hi']-p['entry'] if d==1 else p['entry']-p['lo'])/p['risk'],MAE_R=max(0.,p['entry']-p['lo'] if d==1 else p['hi']-p['entry'],d*(p['entry']-fill))/p['risk']))
    closed+=1;exited=p['id'];p=None;event['exit_price']=fill
   else:
    p['hi']=max(p['hi'],b['High']);p['lo']=min(p['lo'],b['Low']);p['extreme']=p['hi'] if d==1 else p['lo']
    proposal=p['extreme']-d*3.5*b['ATR'];new=max(old,proposal) if d==1 else min(old,proposal)
    if new!=old:p['updates']+=1;p['source']='TRAIL'
    reached=(p['hi']>=p['entry']+p['risk']) if d==1 else (p['lo']<=p['entry']-p['risk'])
    event['BE1_reached_now']=reached and not p['reached']
    if reached and not p['reached']:p['activation']=t;p['reached']=True
    protected=max(new,p['entry']) if d==1 else min(new,p['entry'])
    if variant=='BE1' and reached and protected!=new:
     new=protected;p['raised']=True;p['source']='BE1';event['BE1_raised_now']=True
    p['stop']=new
    event.update(next_stop=new,extreme_after=p['extreme'],proposal=proposal,BE1_eligible_next_observed=variant=='BE1' and reached,stop_source_after=p['source'])
   out['stops'].append(event)
  if b['Signal'] and math.isfinite(b['ATR']):
   d=b['Signal'];allowed=10<=t.hour<18;occupied=p is not None;take=allowed and not occupied
   ident=f'T3-M15-{{}}-{closed+1:06d}'.format({'USDRUBF':'Si','CNYRUBF':'CNY'}.get(symbol,symbol)) if take else None
   reason='ACCEPTED' if take else 'OUTSIDE_T1_AND_OCCUPIED' if occupied and not allowed else 'POSITION_OCCUPIED' if occupied else 'OUTSIDE_T1'
   event=dict(instrument=symbol,signal_time=t,direction=side(d),signal_close=b['Close'],ATR=b['ATR'],H1AvailableAt=b['H1AvailableAt'],PriorHigh=b['PriorHigh'],PriorLow=b['PriorLow'],rule_pass=allowed,position_occupied=occupied,occupied_trade_id=p['id'] if occupied else None,same_close_exit_trade_id=exited,entry_accepted=False,reason=reason,trade_id=ident,entry_price=None,initial_stop=None,execution_bar_close=None,next_observed_close=None)
   out['signals'].append(event)
   if take:event['reason']='PENDING_NEXT_OPEN';agenda[i+1]=(b,i,event)
  waiting=agenda.get(i+1);un=p['d']*(b['Close']-p['entry'])/p['risk'] if p else 0.
  out['marks'].append(dict(instrument=symbol,variant=variant,at=t,gross_realized_R=booked,gross_unrealized_R=un,gross_MTM_R=booked+un,position_trade_id=p['id'] if p else None,waiting_signal_id=symbol+'|'+waiting[0]['at'].isoformat()+'|'+side(waiting[0]['Signal']) if waiting else None))
  prior=b
 for task in agenda.values():task[2]['reason']='UNRESOLVED_END_OF_DATA'
 if p:out['OPEN'].append(snap(p,bars[-1]));out['snapshots'].extend(out['OPEN'])
 out['occupancy']=[dict(instrument=symbol,observed_bars=len(bars),stop_checked_bars=checks,denominator=len(bars)-1,occupancy=checks/(len(bars)-1) if len(bars)>1 else None)]
 return out

def read(path):
 raw=Path(path).read_bytes();raw=gzip.decompress(raw) if str(path).endswith('.gz') else raw
 return list(csv.DictReader(io.StringIO(raw.decode())))

def verify(data,out,scalar):
 counts=dict(rows=0,fields=0);max_error=0.
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
 fresh={m:{k:[] for k in ('trades','OPEN','snapshots','stops','signals','marks','occupancy')} for m in ('CONTROL','BE1')}
 for s in ('USDRUBF','CNYRUBF','GLDRUBF','IMOEXF'):
  bars=list(scalar.feature_stream(parse_development(data/f'forever/{s}/{s}_M15.csv')))
  derived=[{k:v for k,v in b.items() if k not in ('Open','High','Low','Close','Volume','H1Close')} for b in bars]
  compare(derived,read(out/'features'/f'{s}.csv.gz'),'features '+s)
  for mode in fresh:
   result=replay(bars,s,mode)
   for table,rows in result.items():fresh[mode][table].extend(rows)
 for mode,tables in fresh.items():
  for table,rows in tables.items():compare(rows,read(out/(mode+'_'+table+'.csv'+('.gz' if table in ('signals','stops','marks') else ''))),mode+' '+table)
 import stats_verifier
 return dict(status='PASS',**counts,max_abs_error=max_error,independent_statistics=stats_verifier.audit(out),external_review='NOT_PERFORMED',independence='Separate event-agenda scalar execution and PR518 streaming indicators; same author; no primary engine/features/report imports')
