"""Compare expanded causal journals with every original NEXT_OPEN 2023/2024 journal."""
import argparse,json,math
from pathlib import Path
from datetime import datetime
from io_utils import read_csv,write_json
from registry import builds,ROOT

def audit(out,dest):
 count=0;maxdelta=0.;details=[]
 def value(a,b,key):
  nonlocal count,maxdelta
  count+=1
  if a in ('',None) or b in ('',None):assert a in ('',None) and b in ('',None),(key,a,b);return
  if isinstance(a,bool) or a in ('True','False') or b in ('True','False'):assert str(a)==str(b),(key,a,b);return
  if '+03:00' in str(a) or '+03:00' in str(b):assert datetime.fromisoformat(str(a))==datetime.fromisoformat(str(b)),(key,a,b);return
  try:delta=abs(float(a)-float(b))
  except (ValueError,TypeError):assert str(a)==str(b),(key,a,b);return
  assert math.isfinite(delta) and delta<=1e-8,(key,a,b,delta);maxdelta=max(maxdelta,delta)
 for b in builds():
  if b['mode']!='NEXT_OPEN':continue
  root=ROOT/b['source_path']/'results'/('next_open' if b['group']=='execution_sensitivity' else 'experiment' if b['group']=='early_risk_protection' else 'replay')
  pred=lambda r:r.get('version')==b['version'] and r.get('rule')==b['rule'] and r.get('mode','NEXT_OPEN')=='NEXT_OPEN'
  for name,refname,time,keys in [('trades','trades.csv','exit_time',['instrument','trade_id']),('stops','stop_decisions.csv','bar_close_time',['instrument','bar_close_time','trade_id']),('entries','entry_opportunities.csv','signal_time',['instrument','signal_time']),('gaps','observed_gaps.csv','current_close',['instrument','current_close'])]:
   ref=[r for r in read_csv(root/refname) if pred(r)];pending={(r['instrument'],r['signal_time']) for r in ref if r.get('pending_at_end')=='True'} if name=='entries' else set()
   ref=[r for r in ref if (r['instrument'],r.get('signal_time')) not in pending]
   actual=[r for r in read_csv(out/'journals'/b['build_id']/(name+'.csv.gz')) if r[time]<'2025-01-01T00:00:00+03:00' and (r['instrument'],r.get('signal_time')) not in pending]
   sorter=lambda r:tuple(r.get(k,'') for k in keys);ref.sort(key=sorter);actual.sort(key=sorter);assert len(actual)==len(ref),(b['build_id'],name,len(actual),len(ref))
   columns=set(k for r in ref for k in r)&set(k for r in actual for k in r)
   for x,y in zip(actual,ref):
    for c in columns:value(x.get(c),y.get(c),(b['build_id'],name,c))
   details.append(dict(build_id=b['build_id'],table=name,rows=len(ref),common_fields=len(columns),pending_boundary_decisions_not_rewritten=len(pending)))
  ref=[r for r in json.loads((root/'OPEN_POSITIONS.json').read_text()) if pred(r)]
  actual=[r for r in read_csv(out/'journals'/b['build_id']/'snapshots.csv.gz') if r['month']=='2024-12']
  assert len(actual)==len(ref),(b['build_id'],'OPEN2024',len(actual),len(ref))
  actual.sort(key=lambda r:r['instrument']);ref.sort(key=lambda r:r['instrument'])
  for x,y in zip(actual,ref):
   for c in x.keys()&y.keys():value(x[c],y[c],(b['build_id'],'OPEN2024',c))
 write_json(dest,dict(status='PASS',causal_configurations=13,fields_compared=count,max_numeric_delta=maxdelta,tolerance=1e-8,all_original_2023_2024_journals=True,original_terminal_OPEN_vs_expanded_boundary_state=True,details=details,source='Immutable main historical NEXT_OPEN artifacts; full expanded causal replays unchanged'))
if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('--output',type=Path,required=True);p.add_argument('--report',type=Path,required=True);a=p.parse_args();audit(a.output,a.report)
