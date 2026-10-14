"""One full comparison run; outputs must be in a new directory."""
import argparse,concurrent.futures,csv,hashlib,json,os,subprocess,sys,shutil
from datetime import datetime,timedelta
from pathlib import Path
from registry import *
from io_utils import *
from worker import source

def git(root,*args):return subprocess.check_output(['git','-C',str(root),*args],text=True).strip()
def seal(data_root,pr513_root):
 prs=json.loads((HERE/'PR_SOURCES.json').read_text());inventory=[]
 for d in sorted((ROOT/'IntradayLab').glob('t3_m15_*')):
  if d==HERE:continue
  tree=git(ROOT,'rev-parse',MAIN+':'+str(d.relative_to(ROOT)))
  files=[]
  for name in git(ROOT,'ls-tree','-r','--name-only',MAIN,str(d.relative_to(ROOT))).splitlines():
   p=ROOT/name;files.append(dict(path=name,blob=git(ROOT,'rev-parse',MAIN+':'+name),sha256=hash_file(p)))
  inventory.append(dict(directory=str(d.relative_to(ROOT)),tree_sha=tree,files=files))
 # PR513 is an exact detached read-only checkout, never the task branch base.
 assert git(pr513_root,'rev-parse','HEAD')==PR513
 extra=pr513_root/'IntradayLab/t3_m15_a6_s1_true_oos_2026_ytd_v1'
 inventory.append(dict(directory='IntradayLab/t3_m15_a6_s1_true_oos_2026_ytd_v1',commit=PR513,files=[dict(path=str(p.relative_to(pr513_root)),sha256=hash_file(p)) for p in sorted(extra.rglob('*')) if p.is_file() and '__pycache__' not in str(p)]))
 assert git(data_root,'rev-parse','HEAD')==PIN
 receipts=[];times={}
 for s in SYMBOLS:
  rel=f'forever/{s}/{s}_M15.csv';p=data_root/rel;bars,rec=source(p,True)
  assert rec['EOF'],'Pinned source extends beyond cutoff; closed suffix must not be hashed'
  expected=git(data_root,'rev-parse',PIN+':'+rel);assert git(data_root,'hash-object',str(p))==expected
  receipts.append(dict(instrument=s,path=rel,blob=expected,sha256=hash_file(p),**plain(rec)));times[s]=[b['at'].isoformat() for b in bars]
 shared=set.intersection(*(set(v) for v in times.values()))
 start=max(v[0] for v in times.values());last=min(v[-1] for v in times.values())
 # Endpoints are inclusive observed completions expressed as exclusive +1us.
 end=(datetime.fromisoformat(last)+timedelta(microseconds=1)).isoformat()
 views={
  'FULL_AVAILABLE':dict(start='2023-01-01T00:00:00+03:00',end_exclusive=CUTOFF),
  'COMMON_ENVELOPE':dict(start=start,end_exclusive=end),
  'COMMON_OBSERVED':dict(start=start,end_exclusive=end),
  'JAN_JUL_2026':dict(start='2026-01-01T00:00:00+03:00',end_exclusive='2026-08-01T00:00:00+03:00'),
  'REMAINING_2026_PREFIX':dict(start='2026-08-01T00:00:00+03:00',end_exclusive=CUTOFF)}
 return dict(base_main=MAIN,data_pin=PIN,PR513_source_pin=PR513,PR513_draft=True,source_receipts=receipts,historical_inventory=inventory,PRs=prs,
   raw_data_copied=False,costs='GROSS_ONLY',classification='POST_HOC_COMPARISON',cutoff_exclusive=CUTOFF),dict(times=times,common_set=sorted(shared),views=views)

def registry_rows(manifest):
 prs=manifest['PRs'];rows=[]
 for b in builds():
  d=ROOT/b['source_path'];r={k:v for k,v in b.items() if k not in ('config','aliases')};r['config_json']=json.dumps(b['config'],sort_keys=True)
  r.update(code_commit=prs[str(b['source_PR'])]['head_sha'],code_sha256=hash_file(d/'engine.py'),spec_sha256=hash_file(ROOT/b['spec_path']),
   code_git_blob=git(ROOT,'rev-parse',MAIN+':'+b['source_path']+'/engine.py'),source_repo='alkospacer123/market-pattern-discovery',data_pin=PIN,
   audit_paths=';'.join(str(p.relative_to(ROOT)) for p in sorted(d.rglob('*AUDIT*.json')) if 'correction_history' not in str(p)),status='FROZEN_RULES_REPLAYED_AND_SCALAR_VERIFIED',audit_status='HISTORICAL_INDEPENDENT_IMPLEMENTATION_PRESENT;CURRENT_REPLAY_PASS;EXTERNAL_REVIEW_PENDING')
  rows.append(r)
 return rows+MISSING+DIAGNOSTIC

def run(data_root,pr513_root,out,jobs=3):
 assert not out.exists(),'OUTPUT_ALREADY_EXISTS';out.mkdir(parents=True)
 manifest,coverage=seal(data_root,pr513_root);write_json(out/'SOURCE_MANIFEST.json',manifest);write_json(out/'COVERAGE_TIMESTAMPS.json',coverage)
 coverage_rows=[]
 for s,ts in coverage['times'].items():
  for y in (2023,2024,2025,2026):
   for mo in range(1,13 if y<2026 else 11):
    m=f'{y}-{mo:02d}';v=[t for t in ts if t[:7]==m]
    coverage_rows.append(dict(instrument=s,month=m,bars=len(v),first_close=v[0] if v else None,last_close=v[-1] if v else None,status='NO_COVERAGE' if not v else 'INCOMPLETE_ENDPOINT_MONTH' if m in ('2026-08','2026-09') or (s=='GLDRUBF' and m=='2023-07') or (s=='IMOEXF' and m=='2023-11') else 'AVAILABLE_SOURCE_HISTORY_NOT_CALENDAR_CERTIFICATION'))
 write_csv(out/'COVERAGE.csv',coverage_rows)
 # Full original CONTROL + fresh independent audit on every full repeat.
 ctl=out/'canonical_control';log=open(out/'CONTROL.log','w')
 subprocess.run([sys.executable,str(pr513_root/'IntradayLab/t3_m15_a6_s1_true_oos_2026_ytd_v1/run_ytd_oos.py'),'--data-root',str(data_root),'--output',str(ctl),'--end-exclusive',CUTOFF],check=True,stdout=log,stderr=subprocess.STDOUT,env=os.environ|{'PYTHONDONTWRITEBYTECODE':'1'});log.close()
 expected=[(2.207277631364274,90.39067237690145,165),(1.7721337045362484,122.13198384679372,315),(1.5813075953333784,86.8766134312305,300)]
 history=json.loads((ctl/'control/HISTORICAL_CONTROL.json').read_text())['history']['years']
 for r,(pf,rr,n) in zip(history,expected):assert abs(r['gross_PF']-pf)<1e-12 and abs(r['gross_R']-rr)<1e-9 and r['closed']==n
 summary=json.loads((ctl/'SUMMARY.json').read_text());ref=json.loads((pr513_root/'IntradayLab/t3_m15_a6_s1_true_oos_2026_ytd_v1/results/SUMMARY.json').read_text());assert summary['calendar_CLOSED']==ref['calendar_CLOSED']
 print('CANONICAL_CONTROL_ALL_FOUR_YEARS_PASS',flush=True)
 def worker(g):
  with (out/(g+'.log')).open('w') as f:subprocess.run([sys.executable,str(HERE/'worker.py'),'--group',g,'--data-root',str(data_root),'--output',str(out)],check=True,stdout=f,stderr=subprocess.STDOUT,env=os.environ|{'PYTHONDONTWRITEBYTECODE':'1'})
  print('GROUP_COMPLETE',g,flush=True)
 with concurrent.futures.ThreadPoolExecutor(max_workers=jobs) as pool:list(pool.map(worker,CATALOG))
 finish(data_root,pr513_root,out)

def finish(data_root,pr513_root,out,rebuild=True):
 manifest=json.loads((out/'SOURCE_MANIFEST.json').read_text());coverage=json.loads((out/'COVERAGE_TIMESTAMPS.json').read_text());ctl=out/'canonical_control'
 assert len(list((out/'group_audits').glob('*.json')))==10
 if rebuild:
  write_csv(out/'BUILD_REGISTRY.csv',registry_rows(manifest));write_csv(out/'CONFIG_FILTER_MATRIX.csv',[{k:v for k,v in b.items() if k in ('build_id','entry','exit','initial','mode','trail','config_identity')}|b['config'] for b in builds()])
  coverage['common_set']=set(coverage['common_set'])
  from compare import run as compare
  compare(out,coverage)
 with (out/'ARITHMETIC.log').open('w') as f:subprocess.run([sys.executable,str(HERE/'audit_metrics.py'),'--output',str(out),'--coverage',str(out/'COVERAGE_TIMESTAMPS.json')],check=True,stdout=f,stderr=subprocess.STDOUT)
 # Only compact audited canonical receipts retained; full equivalent canonical
 # journals are available at pinned PR513 and among comparison journals.
 keep=[ctl/'control/HISTORICAL_CONTROL.json',ctl/'SUMMARY.json',ctl/'AUDIT.json',ctl/'INDEPENDENT_AUDIT.json',ctl/'SOURCE_RECEIPTS.json',ctl/'primary_causality.json',ctl/'scalar_causality.json']
 if ctl.exists():
  for p in keep:shutil.copyfile(p,out/('CANONICAL_'+p.name))
  shutil.rmtree(ctl)
 current,_=seal(data_root,pr513_root);assert current==manifest,'SOURCE_OR_HISTORICAL_ARTIFACT_CHANGED'
 groups=[json.loads(p.read_text()) for p in sorted((out/'group_audits').glob('*.json'))]
 write_json(out/'AUDIT.json',dict(status='PASS',canonical_control_2023_2026='PASS',full_replay_groups=len(groups),unique_frozen_configurations=51,
  replay_fields_compared=sum(x['fields_compared'] for x in groups),max_replay_numeric_delta=max(x['max_numeric_delta'] for x in groups),arithmetic=json.loads((out/'ARITHMETIC_AUDIT.json').read_text()),
  source_pin='PASS',frozen_artifact_bytes_unchanged='PASS',PR513_readonly_exact_SHA=PR513,forced_year_liquidation=False,independent_implementations=True,external_human_review='PENDING',classification='POST_HOC_COMPARISON',GROSS_ONLY=True))
 write_json(out/'REPORTING_CORRECTION.json',dict(arithmetic='Stable fsum accumulation before near-zero signed-R concentration division',first_diagnostic_failure='Absolute concentration delta 1.4029865269549191e-08 under unstable numpy/linear summation; tolerance remains 1e-8',strategy_rules_changed=False,trades_changed=False,thresholds_changed=False,primary_and_independent_arithmetic_rebuilt=True))
 print('FULL_COMPARISON_PASS',flush=True)

if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('--data-root',type=Path,required=True);p.add_argument('--pr513-root',type=Path,required=True);p.add_argument('--output',type=Path,required=True);p.add_argument('--jobs',type=int,default=3);a=p.parse_args();run(a.data_root,a.pr513_root,a.output,a.jobs)
