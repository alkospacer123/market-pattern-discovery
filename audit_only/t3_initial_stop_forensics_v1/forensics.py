"""Retrospective observations only; no data from here enters replay decisions."""
import io,subprocess,math
from bisect import bisect_right
from collections import defaultdict
from datetime import timedelta
import pandas as pd
from common import *

def identity(t):
 return '|'.join(str(t[k]) for k in ('system','lifecycle','fold_id','instrument'))+'|'+t.get('signal_time',t['entry_time']).isoformat()+'|'+t['direction']
def stream_key(t):return tuple(t[k] for k in ('system','lifecycle','fold_id','instrument'))
def dt_minutes(system):return 60 if system=='H1' else 15

def excursions(t,bars,trace):
 side=1 if t['direction']=='LONG' else -1;e=t['entry_price'];r=t['initial_risk_price'];step=timedelta(minutes=dt_minutes(t['system']))
 index={b['at']:i for i,b in enumerate(bars)};start=index[t['entry_time']]+1;end=index[t['exit_time']] if t['status']=='CLOSED' else len(bars)-1
 obs=[];mfe=mae=observed_mfe=observed_mae=0.;firstfav=firstadv=None;events=[];ambiguities=[]
 first_adv_open=False;first_adv_close=False;early_half=False
 traces={x['at']:x for x in trace if x['trade_id']==t['trade_id']}
 for i in range(start,end+1):
  b=bars[i];at=b['at'];ev=traces[at];exitbar=t['status']=='CLOSED' and at==t['exit_time']
  favorable=max(0.,side*((b['High'] if side==1 else b['Low'])-e)/r)
  adverse=max(0.,-side*((b['Low'] if side==1 else b['High'])-e)/r)
  openr=side*(b['Open']-e)/r
  observed_mfe=max(observed_mfe,favorable);observed_mae=max(observed_mae,adverse)
  mfebefore=mfe;maebefore=mae
  mfe=max(mfe,max(0.,openr),0. if exitbar else favorable)
  mae=max(mae,max(0.,-openr),max(0.,-t['gross_R']) if exitbar else adverse)
  if firstfav is None and (openr>0 or (not exitbar and favorable>0)):
   firstfav=(at-step if openr>0 else at);events.append('FAVORABLE_OPEN' if openr>0 else 'FAVORABLE_BAR_INTERVAL')
  if firstadv is None and (openr<0 or (adverse>0 and not exitbar) or (exitbar and t['gross_R']<0)):
   firstadv=(at-step if openr<0 else at);events.append('ADVERSE_OPEN' if openr<0 else 'ADVERSE_BAR_INTERVAL')
  if i==start:
   first_adv_open=openr<0;first_adv_close=not exitbar and side*(b['Close']-e)<0
  if i<start+4 and (max(0.,-openr)>=.5 or (not exitbar and adverse>=.5) or (exitbar and t['gross_R']<=-.5)):early_half=True
  if exitbar:
   ambiguities=[q for q in (.5,1.,1.5,2.) if mfe<q<=favorable]
  obs.append(dict(signal_id=identity(t),system=t['system'],variant=t['variant'],lifecycle=t['lifecycle'],fold_id=t['fold_id'],symbol=t['instrument'],trade_id=t['trade_id'],bar_close=at,bar_open=at-step,held_bar_number=i-start+1,
   High=b['High'],Low=b['Low'],high_R0=side*(b['High']-e)/r,low_R0=side*(b['Low']-e)/r,open_R0=openr,
   gap_from_previous_close_R0=side*(b['Open']-bars[i-1]['Close'])/r,unobserved_minutes=max(0.,(at-bars[i-1]['at']-step).total_seconds()/60),
   active_stop=ev['stop_entering'],active_stop_R0=side*(ev['stop_entering']-e)/r,next_stop=ev.get('stop_after'),candidate=ev.get('candidate'),triggered=ev.get('triggered'),activated=ev.get('activated'),stop_hit=ev['stop_hit'],
   guaranteed_MFE_R0=mfe,guaranteed_MAE_R0=mae,observed_MFE_upper_R0=observed_mfe,observed_MAE_upper_R0=observed_mae,
   intrabar_order='EXIT_BAR_UNKNOWN_STOP_FIRST' if exitbar else 'SURVIVED_HL_ORDER_UNKNOWN',stop_changed=ev.get('stop_after',ev['stop_entering'])!=ev['stop_entering']))
 held=max(0,end-start+1);last=t.get('exit_time',t.get('last_mark_time'))
 exitr=t['gross_R'] if t['status']=='CLOSED' else None
 categories=[]
 if t['variant']=='CONTROL' and t.get('exit_reason')=='INITIAL_STOP' and mfe<.5:categories.append('LOW_FOLLOW_THROUGH' if .5 not in ambiguities else 'AMBIGUOUS')
 if first_adv_open or first_adv_close or early_half:categories.append('EARLY_ADVERSE_MOVE')
 if t.get('exit_reason')=='ATR_TRAILING_STOP' and mfe>exitr:categories.append('TRAILING_GIVEBACK')
 if ambiguities and 'AMBIGUOUS' not in categories:categories.append('AMBIGUOUS')
 if t['status']=='OPEN':categories.append('INSUFFICIENT_DATA')
 result={k:v for k,v in t.items() if not k.startswith('part') and k not in ('target_price','part1_quantity','part2_quantity')}
 result.update(signal_id=identity(t),signal_time=t.get('signal_time',t['entry_time']),ATR=bars[start-1]['ATR'],stop_atr=abs(e-t['initial_stop_price'])/bars[start-1]['ATR'],
  MFE_pre_stop_R0=mfe,MAE_executable_R0=mae,MFE_observed_upper_R0=observed_mfe,MAE_observed_upper_R0=observed_mae,
  first_favorable_time_bound=firstfav,first_adverse_time_bound=firstadv,excursion_time_precision='Open exact else bar interval (bar Close upper bound)',
  held_execution_bars=held,wall_clock_minutes=(last-t['entry_time']).total_seconds()/60,observed_trading_minutes=held*dt_minutes(t['system']),
  immediate_adverse_open=first_adv_open,immediate_adverse_survived_close=first_adv_close,adverse_half_R_first4=early_half,
  duration_bucket='1' if held==1 else '2-4' if held<=4 else '5-8' if held<=8 else '9-16' if held<=16 else '>16',
  negative_shifted_trailing=t.get('exit_reason')=='ATR_TRAILING_STOP' and exitr<0 if exitr is not None else None,
  giveback_R0=max(0.,mfe-exitr) if exitr is not None else None,positive_MFE_surrendered_R0=max(0.,mfe-max(0.,exitr)) if exitr is not None else None,loss_below_entry_R0=max(0.,-exitr) if exitr is not None else None,LOW_FOLLOW_THROUGH_scope='CONTROL_ONLY',categories='|'.join(categories))
 # Open-labelled trading day, not midnight Close-date.
 entryday=t['entry_time'].date();exitday=(last-step).date();days=sorted({(b['at']-step).date() for b in bars if b['at']>t['entry_time']})
 nextday=next((d for d in days if d>entryday),None)
 result.update(frozen_exit_label_time=last,actual_exit_time_lower=last-step if t['status']=='CLOSED' else None,actual_exit_time_upper=(last-step if t.get('exit_at_open') else last) if t['status']=='CLOSED' else None,wall_clock_precision='Frozen Close-labelled upper bound; Open gap exit exact at exit label minus timeframe',observed_exposure_minutes_lower=max(0,held-1)*dt_minutes(t['system']),observed_exposure_minutes_upper=(max(0,held-1) if t.get('exit_at_open') else held)*dt_minutes(t['system']))
 result['exit_day_bucket']='ENTRY_DAY' if exitday==entryday else 'NEXT_OBSERVED_TRADING_DAY' if exitday==nextday else 'LATER'
 for q in (.5,1.,1.5,2.):result[f'MFE_before_stop_ge_{str(q).replace(".","p")}R']='HIT_BEFORE_STOP' if mfe>=q else 'AMBIGUOUS_EXIT_BAR' if q in ambiguities else 'NOT_OBSERVED'
 nextsignal=next((b for b in bars[end:] if b['Signal'] and b['at']>=last and (t['system']=='H1' or 600<=b['at'].hour*60+b['at'].minute<1080)),None)
 result['next_eligible_raw_signal_time']=nextsignal['at'] if nextsignal else None
 result['occupancy_after_exit']='FREE_TO_EVALUATE_SAME_CLOSE' if t['status']=='CLOSED' else 'OCCUPIED_END_OF_LIFECYCLE'
 return result,obs

def full_history(data):
 result={}
 for system,commit,tf in [('H1',H1_DATA,'H1'),('M15',M15_DATA,'M15')]:
  step=timedelta(minutes=dt_minutes(system))
  for s in SYMBOLS:
   raw=subprocess.check_output(['git','-C',str(data),'show',commit+f':forever/{s}/{s}_{tf}.csv'])
   f=pd.read_csv(io.BytesIO(raw),sep=';',float_precision='round_trip' if system=='M15' else None)
   times=pd.DatetimeIndex(pd.to_datetime(f.Datetime)).tz_localize('Europe/Moscow')+step
   result[(system,s)]=[dict(at=at.to_pydatetime(),Open=float(b.Open),High=float(b.High),Low=float(b.Low),Close=float(b.Close)) for at,b in zip(times,f.itertuples())]
 return result

def post_stop(t,bars,days_count):
 step=timedelta(minutes=dt_minutes(t['system']));side=1 if t['direction']=='LONG' else -1;e=t['entry_price'];r=t['initial_risk_price'];stop=t['exit_time'];stopday=(stop-step).date()
 stamps=[b['at'] for b in bars];start=bisect_right(stamps,stop)
 days=sorted({(b['at']-step).date() for b in bars});future=[d for d in days if d>stopday]
 full=len(future)>days_count;targetday=future[days_count-1] if len(future)>=days_count else None
 after=[b for b in bars[start:] if targetday is None or (b['at']-step).date()<=targetday]
 levels={0.:'RECOVERY_ENTRY',.5:'FAVORABLE_0p5R',1.:'FAVORABLE_1R',1.5:'FAVORABLE_1p5R',2.:'FAVORABLE_2R',-1.5:'ADVERSE_1p5R',-2.:'ADVERSE_2R'}
 first={};event_order={};touches=0;closecross=0;previous=side*(bars[start-1]['Close']-e)/r if start else 0.;priorat=None;gaps=0
 for ordinal,b in enumerate(after):
  at=b['at'];o=side*(b['Open']-e)/r;low=min(side*(b['Low']-e)/r,side*(b['High']-e)/r);high=max(side*(b['Low']-e)/r,side*(b['High']-e)/r)
  if low<=0<=high:touches+=1
  close=side*(b['Close']-e)/r
  if (previous<0<=close) or (previous>0>=close):closecross+=1
  previous=close
  if priorat and at-priorat>step:gaps+=1
  priorat=at
  for q,name in levels.items():
   if name in first:continue
   reached=high>=q if q>=0 else low<=q
   if reached:
    openhit=o>=q if q>=0 else o<=q
    first[name]=(at-step if openhit else at,'OPEN' if openhit else 'BAR_INTERVAL');event_order[name]=(ordinal,0 if openhit else 1)
 rec=first.get('RECOVERY_ENTRY');adv=first.get('ADVERSE_1p5R');order='NEITHER_OBSERVED'
 if rec and adv:
  # Compare event intervals; Open event can establish order in common candle.
  if event_order['RECOVERY_ENTRY']<event_order['ADVERSE_1p5R']:order='RECOVERY_FIRST'
  elif event_order['ADVERSE_1p5R']<event_order['RECOVERY_ENTRY']:order='ADVERSE_FIRST'
  else:order='AMBIGUOUS_SAME_BAR'
 elif rec:order='RECOVERY_ONLY_OBSERVED'
 elif adv:order='ADVERSE_ONLY_OBSERVED'
 cats=[]
 if rec:cats.append('RECOVERY_AFTER_STOP')
 if adv:cats.append('ADVERSE_CONTINUATION_AFTER_STOP')
 if not full:cats.append('INSUFFICIENT_DATA')
 if order.startswith('AMBIGUOUS'):cats.append('AMBIGUOUS')
 row=dict(signal_id=identity(t),system=t['system'],lifecycle=t['lifecycle'],fold_id=t['fold_id'],symbol=t['instrument'],trade_id=t['trade_id'],direction=t['direction'],stop_time=stop,CONTROL_R0=r,window_full_next_trading_days=days_count,
  window_start=after[0]['at']-step if after else None,window_last_bar=after[-1]['at'] if after else None,target_trading_date=targetday,status='COMPLETE_OBSERVED_DATE_WINDOW' if full else 'CENSORED',
  observed_bars=len(after),observed_gaps=gaps,entry_touch_or_cross_bars=touches,completed_close_crossings=closecross,intrabar_actual_crossings='UNKNOWN',recovery_vs_adverse_1p5R_order=order,categories='|'.join(cats),
  coverage_limitation='Observed dates only; no exchange calendar proof of every expected bar')
 for name in levels.values():
  event=first.get(name);row[name+'_status']='OBSERVED' if event else 'NOT_OBSERVED' if full else 'CENSORED';row[name+'_first_time_bound']=event[0] if event else None;row[name+'_time_precision']=event[1] if event else None
 return row

def build_forensics(streams,results,data,out):
 index={stream_key(s):s for s in streams};rows=[];paths=[]
 for result in results:
  for t in result['trades']:
   a,b=excursions(t,index[stream_key(t)]['bars'],result['trace'])
   future=[u for u in result['trades'] if u is not t and u['entry_time']>=t.get('exit_time',t.get('last_mark_time'))] if t['status']=='CLOSED' else []
   nextentry=min(future,key=lambda u:u['entry_time']) if future else None
   a['next_actual_entry_time']=nextentry['entry_time'] if nextentry else None;a['next_actual_entry_trade_id']=nextentry['trade_id'] if nextentry else None
   rows.append(a);paths.extend(b)
 for system in ('H1','M15'):
  csvout(out/f'{system}_TRADE_FORENSICS.csv',[r for r in rows if r['system']==system]);csvout(out/f'{system}_BAR_PATH.csv.gz',[r for r in paths if r['system']==system])
 history=full_history(data);post=[]
 for result in results:
  for t in result['trades']:
   if t['variant']=='CONTROL' and t.get('exit_reason')=='INITIAL_STOP':
    for days in (1,2):post.append(post_stop(t,history[(t['system'],t['instrument'])],days))
 csvout(out/'POST_STOP_1D_2D.csv',post)
 return rows,post
