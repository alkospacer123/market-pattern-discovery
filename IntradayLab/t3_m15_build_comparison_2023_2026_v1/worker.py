"""Run unchanged frozen primary and separate scalar engines in a fresh process.

Only in-memory time ceilings/known configuration maps are extended. No frozen
file is edited. The worker never invents an execution/filter combination.
"""
import argparse,importlib.util,sys,math,json,hashlib
from datetime import datetime,timedelta
from zoneinfo import ZoneInfo
from pathlib import Path
from dataclasses import asdict
import pandas as pd
from registry import HERE,ROOT,SYMBOLS,CUTOFF,folder,builds,PIN
from io_utils import write_csv,write_json,plain,read_csv
TZ=ZoneInfo('Europe/Moscow');END=datetime.fromisoformat(CUTOFF);STEP=timedelta(minutes=15)
def load(path,name):
 spec=importlib.util.spec_from_file_location(name,path);m=importlib.util.module_from_spec(spec);sys.modules[name]=m;spec.loader.exec_module(m);return m
def source(path,scalar=False):
 rows=[];digest=hashlib.sha256();last=None
 with open(path,'rb',buffering=0) as f:
  header=f.readline();assert header.rstrip()==b'Ticker;Datetime;Open;High;Low;Close;Volume';digest.update(header)
  while True:
   prefix=bytearray();n=0
   while n<2:
    ch=f.read(1)
    if not ch:break
    prefix.extend(ch);n+=ch==b';'
   if not prefix:break
   assert n==2
   stamp=prefix.decode().split(';')[1]
   at=(datetime.fromisoformat(stamp) if scalar else datetime.strptime(stamp,'%Y-%m-%d %H:%M:%S')).replace(tzinfo=TZ)+STEP
   if at>=END:break
   tail=f.readline();values=list(map(float,tail.decode().strip().split(';'))) if scalar else [float(x) for x in tail.rstrip().split(b';')]
   assert len(values)==5 and all(math.isfinite(x) for x in values)
   o,h,l,c,v=values;assert h>=max(o,l,c) and l<=min(o,h,c) and (last is None or at>last)
   assert at.minute%15==0 and at.second==0
   last=at;digest.update(prefix+tail)
   rows.append(dict(at=at,o=o,h=h,l=l,c=c,v=v) if scalar else (at,*values))
  receipt=dict(prefix_sha256=digest.hexdigest(),rows=len(rows),first_close=rows[0]['at'] if scalar else rows[0][0],last_close=last,EOF=not prefix,cutoff=CUTOFF,excluded_suffix_read=False)
 if scalar:return rows,receipt
 return pd.DataFrame([x[1:] for x in rows],index=pd.DatetimeIndex([x[0] for x in rows],name='CloseTime'),columns=['Open','High','Low','Close','Volume']),receipt

class Check:
 def __init__(self):self.fields=0;self.rows=0;self.max_delta=0.;self.tables={}
 def value(self,a,b,label):
  a=plain(a);b=plain(b);b=None if b=='' else b;self.fields+=1
  if a is None or b is None:assert a==b,(label,a,b);return
  if isinstance(a,bool) or isinstance(b,bool):assert str(a)==str(b),(label,a,b);return
  if isinstance(a,(int,float)):
   delta=abs(float(a)-float(b));assert delta<=1e-8,(label,a,b,delta);self.max_delta=max(self.max_delta,delta)
  elif isinstance(a,str) and ('T' in a or ' ' in a) and ('+03:00' in a):
   assert datetime.fromisoformat(a)==datetime.fromisoformat(str(b)),(label,a,b)
  else:assert str(a)==str(b),(label,a,b)
 def rows_check(self,a,b,label,exclude=()):
  assert len(a)==len(b),(label,'count',len(a),len(b))
  common=sorted(set(k for r in a for k in r)&set(k for r in b for k in r)-set(exclude))
  assert common or not a,label
  for i,(x,y) in enumerate(zip(a,b)):
   for k in common:self.value(x.get(k),y.get(k),(label,i,k))
  self.rows+=len(a);self.tables[label]=dict(rows=len(a),fields=common)

def primary(E,low,b,s):
 p=E.E.Parameters(trail_atr=b['trail']) if hasattr(E,'E') else None
 if p is not None:
  result=E.execute(low,s,b['version'],p,b['rule']);return dict(zip(('trades','OPEN','stops','entries','snapshots') if b['group']=='initial_stop' else ('trades','OPEN','stops','entries','gaps','snapshots') if b['group']=='session_entry' else ('trades','OPEN','stops','entries'),result))
 result=E.replay(low,s,b['version'],b['rule']) if b['group']=='t1_s1' else E.replay(low,s,b['version'],b['rule'],b['mode'])
 return dict(zip(('trades','OPEN','stops','entries','gaps','snapshots'),result))
def independent(A,bars,b,s,p):
 g=b['group']
 if g in ('entry_regime','stop_exit','combined'):res=A.simulate(bars,p,b['rule']);names=('trades','OPEN','stops','entries')
 elif g=='initial_stop':res=A.simulate(bars,p,b['rule'],s,b['version']);names=('trades','OPEN','stops','entries','snapshots')
 elif g=='session_entry':res=A.simulate(bars,p,b['rule'],s,b['version']);names=('trades','OPEN','stops','entries','gaps','snapshots')
 else:
  res=A.simulate(bars,s,b['version'],b['rule']) if g=='t1_s1' else A.simulate(bars,s,b['version'],b['rule'],b['mode']);names=('trades','OPEN','stops','entries','gaps','snapshots')
 return dict(zip(names,res))

def causality(result,b):
 count=0;last_stop={};byid={r['trade_id']:r for r in result['trades']}
 if result.get('OPEN'):byid[result['OPEN']['trade_id']]=result['OPEN']
 for r in result['trades']:
  s=1 if r['direction']=='LONG' else -1
  assert abs(r['gross_R']-s*(r['exit_price']-r['entry_price'])/r['initial_risk'])<=1e-12
  assert r['entry_time']<=r['exit_time']<END
  assert r['H1AvailableAt']<=r.get('signal_time',r['entry_time']);count+=1
 for r in result['entries']:
  if r.get('H1AvailableAt') is not None and not pd.isna(r['H1AvailableAt']):assert r['H1AvailableAt']<=r['signal_time']
  if b['mode']=='NEXT_OPEN' and r.get('entry_accepted'):
   assert r['execution_open_time']==r['signal_time'] and r['execution_bar_close']==r['signal_time']+STEP
   assert abs(abs(r['entry_price']-r['candidate_initial_stop'])-2*r['ATR'])<=1e-8
  count+=1
 for r in result['stops']:
  if 'bar_close_time' not in r:continue  # A1/A2 publish decision rather than Stop journals.
  assert r['bar_close_time']<END and r['bar_open_time']+STEP==r['bar_close_time'];key=r['trade_id'];q=byid[key];s=1 if q['direction']=='LONG' else -1
  assert abs(r['active_stop']-last_stop.get(key,q['initial_stop']))<=1e-8
  if r.get('phase')=='SURVIVED':
   assert not r['stop_hit'] and s*(r['active_stop_next_bar']-r['active_stop'])>=-1e-8
   last_stop[key]=r['active_stop_next_bar']
   if r.get('threshold_activated_now'):assert r['activation_time_after']==r['bar_close_time']
  if r.get('phase')=='EXIT':assert r['stop_hit'] and r['active_stop_next_bar'] is None
  count+=1
 return count

def run(group,data_root,output):
 d=ROOT/'IntradayLab'/folder(group);sys.path.insert(0,str(d))
 modern=group not in ('entry_regime','stop_exit','combined','initial_stop','session_entry')
 if modern:
  cname='independent' if group=='t1_s1' else 'common';C=load(d/(cname+'.py'),cname);C.END=END
  if hasattr(C,'VERSIONS'):
   C.VERSIONS.update({b['version']:b['trail'] for b in builds() if b['group']==group})
  E=load(d/'engine.py','frozen_primary_'+group)
  A=load(d/('independent_combination.py' if group=='t1_s1' else 'scalar.py'),'frozen_scalar_'+group);A.END=END
 else:
  E=load(d/'engine.py','frozen_primary_'+group);E.E.END=pd.Timestamp(END)
  A=load(d/'audit.py','frozen_scalar_'+group)
 configs=[b for b in builds() if b['group']==group];p=asdict(E.E.Parameters()) if not modern else None
 totals={b['build_id']:{k:[] for k in ('trades','OPEN','stops','entries','gaps','snapshots')} for b in configs};checker=Check();receipts=[];causal_count=0
 for s in SYMBOLS:
  raw,rec=source(data_root/f'forever/{s}/{s}_M15.csv');bars,srec=source(data_root/f'forever/{s}/{s}_M15.csv',True)
  assert plain(rec)==plain(srec);receipts.append(dict(rec,instrument=s))
  low=E.features(raw) if modern else E.features(raw,E.E.Parameters())[0]
  sb=C.build_features(bars) if modern else A.derive(bars,p)
  for j,(r,q) in enumerate(zip(low.itertuples(),sb)):
   for col,key in [('ATR','atr'),('PreviousATR','previous_atr'),('PriorHigh','upper'),('PriorLow','lower'),('Signal','signal')]:checker.value(getattr(r,col),q[key],('feature',s,j,col))
   for pre,h in [('H1',q['h1']),('H1Previous',q['previous_h1'])]:
    for col,key in [('ADX','adx'),('Slope','slope'),('ATRRatio','ratio'),('AvailableAt','at')]:checker.value(getattr(r,pre+col),h[key] if h else None,('feature',s,j,pre+col))
  for b in configs:
   a=primary(E,low,b,s);v=independent(A,sb,b,s,(p|dict(trail_atr=b['trail'])) if p else None)
   causal_count+=causality(a,b)
   for name in ('trades','entries','stops','gaps','snapshots'):
    if name in a and name in v:checker.rows_check(a[name],v[name],b['build_id']+'_'+s+'_'+name,('version','rule','mode','instrument','trade_id','ordinal'))
   # Old scalar position structures expose internal keys; all economic state
   # is checked through trades and the available normalized terminal fields.
   if not modern and group in ('entry_regime','stop_exit','combined'):
    aq,vq=a['OPEN'],v['OPEN'];assert (aq is None)==(vq is None)
    if aq:
     for k,vk in [('entry_price','entry'),('initial_stop','initial'),('active_stop','stop'),('entry_time','at'),('breakout_level','level')]:checker.value(aq[k],vq[vk],('OPEN',s,k))
   else:checker.rows_check([a['OPEN']] if a.get('OPEN') else [],[v['OPEN']] if v.get('OPEN') else [],b['build_id']+'_'+s+'_OPEN')
   for name,rs in a.items():
    if name=='OPEN':rs=[rs] if rs else []
    for i,r in enumerate(rs):
     r=dict(r,instrument=s,build_id=b['build_id'])
     if name=='trades' and 'trade_id' not in r:r['trade_id']=f'T3-M15-{s}-{i+1:06d}'
     totals[b['build_id']][name].append(r)
   print('REPLAY_PASS',b['build_id'],s,len(a['trades']),flush=True)
 for b in configs:
  result=totals[b['build_id']];dest=output/'journals'/b['build_id']
  for name,rows in result.items():write_csv(dest/(name+'.csv.gz'),rows)
  # Existing trade artifacts are compared at the historical ceiling, including
  # every common economic/execution field; unrelated metadata is preserved.
  path=d/'results'/('trades_'+b['rule']+'.csv')
  if path.exists():
   ref=[r for r in read_csv(path) if r['version']==b['version']]
   act=[r for r in result['trades'] if r['exit_time']<datetime(2025,1,1,tzinfo=TZ)]
   act.sort(key=lambda r:(r['instrument'],r['entry_time']));ref.sort(key=lambda r:(r['instrument'],r['entry_time']))
   checker.rows_check(act,ref,'HISTORICAL_'+b['build_id'],('build_id','mode'))
 write_json(output/'group_audits'/(group+'.json'),dict(status='PASS',group=group,fields_compared=checker.fields,rows_compared=checker.rows,causal_rows_checked=causal_count,max_numeric_delta=checker.max_delta,tolerance=1e-8,tables=checker.tables,sources=receipts,independence='Frozen separate stdlib features and position machines; same author; external review pending'))

if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('--group',required=True);p.add_argument('--data-root',type=Path,required=True);p.add_argument('--output',type=Path,required=True);a=p.parse_args();run(a.group,a.data_root,a.output)
