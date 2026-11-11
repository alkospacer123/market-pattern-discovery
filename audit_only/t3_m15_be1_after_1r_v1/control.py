"""Isolated full-period retrospective CONTROL gate. No candidate computation."""
import argparse,math
from support import *
from io_utils import read_csv,write_json

def compare(a,b,fields=None):
 assert len(a)==len(b),(len(a),len(b));n=0
 for x,y in zip(a,b):
  for k in fields or y:
   n+=1;v=x.get(k);w=y[k]
   if isinstance(v,float):assert abs(v-float(w))<1e-8,(k,v,w)
   else:assert ('' if v is None else v.isoformat() if hasattr(v,'isoformat') else str(v))==w,(k,v,w)
 return n

def run(out):
 out.mkdir(parents=True,exist_ok=True);manifest=authenticate();p=frozen();v=scalar()
 models={k:[] for k in ('trades','signals','stops','snapshots','OPEN','occupancy')};check=v.Check()
 for s in SYMBOLS:
  path=DATA/f'forever/{s}/{s}_M15.csv';bars=p.features(p.load(path));actual=p.replay(bars,s,'NEXT_OPEN')
  independent=v.simulate(list(v.feature_stream(v.parse(path))),s,'NEXT_OPEN')
  from io_utils import clean
  for k,rows in actual.items():
   rows=[rows] if k=='occupancy' else rows;other=independent[k];other=[other] if k=='occupancy' else other
   # Compare using independent checker and its own serialization contract.
   encoded=[{f:('' if val is None else str(val)) for f,val in clean(r).items()} for r in rows]
   check.compare(other,encoded,s+' '+k);models[k].extend(rows)
 fields=0
 for k,rows in models.items():
  path=FROZEN/'results'/('next_open_'+k+'.csv'+('.gz' if k in ('signals','stops') else ''))
  fields+=compare(rows,read_csv(path))
 prior=[r for r in read_csv(archive('pr560','M15_TRADES.csv')) if r['variant']=='CONTROL']
 mapping={'initial_stop_price':'initial_stop','initial_risk_price':'initial_risk'}
 for t,r in zip(models['trades'],prior):
  assert len(models['trades'])==len(prior)
  for field in ('trade_id','instrument','direction','entry_time','entry_price','initial_stop_price','initial_risk_price','signal_time','signal_close','ATR','H1AvailableAt','breakout_level','exit_time','exit_price','gross_R','exit_type','bars_held','trailing_updates','MFE_R','MAE_R'):
   fields+=compare([{field:t[mapping.get(field,field)]}],[{field:r[field]}])
 assert len(models['trades'])==1114 and sum(t['exit_type']=='INITIAL_STOP' for t in models['trades'])==356
 assert not check.diffs,check.diffs[:5]
 write_json(out/'SOURCE_MANIFEST.json',manifest)
 write_json(out/'CONTROL_RECONCILIATION.json',dict(status='PASS',CLOSED=1114,INITIAL_STOP=356,PR518_and_PR560_compared_fields=fields,independent_full_replay_fields=check.fields,independent_full_replay_rows=check.rows,mismatches=0,scope='2023–2026 RETROSPECTIVE_CONTROL_ONLY; not new independent OOS',no_alternative=True))
 print('CONTROL PASS',fields,check.fields,flush=True)
if __name__=='__main__':
 a=argparse.ArgumentParser();a.add_argument('--output',type=Path,required=True);run(a.parse_args().output)
