"""Authenticate archived research and source blobs; fresh CONTROL only."""
import sys,subprocess,hashlib,json,io
from pathlib import Path
sys.dont_write_bytecode=True
from common import *
from engines import h1_inputs,m15_inputs,replay
from reconcile import reconcile
ARCHIVE=HERE/'work/pr557'
DATA=Path('/workspace/market-pattern-data')
PR557='5836971e7ff8e472d8128c675c4f837b40a036ef'

def authenticate(out):
 # Rebuild only an ignored scratch cache; all bytes are authenticated below.
 if not ARCHIVE.exists():
  ARCHIVE.mkdir(parents=True)
  prefix='audit_only/t3_h1_m15_partial_tp_2r_50/'
  paths=subprocess.check_output(['git','-C',str(ROOT),'ls-tree','-r','--name-only',PR557,prefix],text=True).splitlines()
  assert len(paths)==44,'PINNED_PR557_OBJECTS_REQUIRED: git fetch origin '+PR557
  for rel in paths:(ARCHIVE/Path(rel).name).write_bytes(subprocess.check_output(['git','-C',str(ROOT),'show',PR557+':'+rel]))
 manifest=json.loads((ARCHIVE/'SOURCE_MANIFEST.json').read_text());checks=[]
 for row in (ARCHIVE/'SHA256SUMS').read_text().splitlines():
  expected,name=row.split(None,1);name=name.strip();assert sha(ARCHIVE/name)==expected,('PR557_HASH',name)
  raw=subprocess.check_output(['git','-C',str(ROOT),'show',PR557+':audit_only/t3_h1_m15_partial_tp_2r_50/'+name]);assert raw==(ARCHIVE/name).read_bytes()
  checks.append(dict(scope='PR557',path=name,sha256=expected,status='PASS'))
 for rel,x in manifest['source_files'].items():
  assert sha(ROOT/rel)==x['sha256'],('FROZEN_SOURCE_CHANGED',rel)
  checks.append(dict(scope='FROZEN_MAIN_SOURCE',path=rel,sha256=x['sha256'],status='PASS'))
 for line in (ROOT/'IntradayLab/t3_m15_t1_entry_retest_v1/SHA256SUMS').read_text().splitlines():
  expected,rel=line.split(None,1);rel=rel.strip();p=ROOT/'IntradayLab/t3_m15_t1_entry_retest_v1'/rel
  assert sha(p)==expected,('PR518_HASH',rel)
  checks.append(dict(scope='PR518',path=rel,sha256=expected,status='PASS'))
 assert git('rev-parse','HEAD',root=DATA)==M15_DATA and not git('status','--porcelain',root=DATA)
 for x in manifest['data']:
  raw=subprocess.check_output(['git','-C',str(DATA),'show',x['commit']+':'+x['path']]);assert hashlib.sha256(raw).hexdigest()==x['sha256']
  if x['system']=='M15':assert sha(DATA/x['path'])==x['sha256']
  f=__import__('pandas').read_csv(io.BytesIO(raw),sep=';');assert f.Datetime.is_monotonic_increasing and not f.Datetime.duplicated().any()
  checks.append(dict(scope='DATA_BLOB',**x,status='PASS'))
 assert manifest['h1_identity']['strategy']['parameter_sha256']=='4e73cdb77246cb07b5953160b9fc0ab36bfd4bd6d9a7f7faaae7e6e392ee340a'
 receipt=dict(status='PASS',main_at_start=BASE,pr557_head=PR557,pr518_head='d85cf85083d6fea047a1a960c9ead441f7b4a6ed',checks=checks,data=manifest['data'],H1_read_mode='pinned git blob in memory; current checkout H1 is NOT used',M15_read_mode='clean pinned checkout',source_files_copied=False,forensic_HL='Authorized per-trade source-derived High/Low observations retained, not raw OHLCV file copies',runtime=dict(python=__import__('platform').python_version(),pandas=__import__('pandas').__version__,numpy=__import__('numpy').__version__),authority='Archived research only; no production application imported or run')
 js(out/'SOURCE_MANIFEST.json',receipt);return receipt

def controls(out):
 out.mkdir(parents=True,exist_ok=True);authenticate(out)
 ss=h1_inputs(DATA)+m15_inputs(DATA);print('Frozen features ready',flush=True)
 cc=[replay(s,'CONTROL') for s in ss];gate=reconcile(ss,cc,out)
 if gate['status']!='PASS':raise RuntimeError('STOP_CONTROL_MISMATCH')
 # Also full per-bar trace/signals/trades/marks byte-value reconciliation with PR557 CONTROL.
 fields=0
 for system in ('H1','M15'):
  for name in ('trades','trace','signals','marks'):
   suffix='.csv' if name=='trades' else '.csv.gz';ref=[r for r in csvin(ARCHIVE/f'{system}_{name.upper()}{suffix}') if r['variant']=='CONTROL'];act=[r for c in cc for r in c[name] if r['system']==system]
   assert len(ref)==len(act),(system,name,len(ref),len(act))
   for a,e in zip(act,ref):
    for k,v in e.items():
     av=a.get(k);observed='' if av is None else str(av.isoformat() if hasattr(av,'isoformat') else av)
     assert observed==v,('ARCHIVE_CONTROL_DIFFERENCE',system,name,k,observed,v)
     fields+=1
 counts={}
 for system in ('H1','M15'):
  ts=[t for c in cc for t in c['trades'] if t['system']==system and t['status']=='CLOSED' and t['lifecycle']!='walk_forward'];rs=[t['gross_R'] for t in ts]
  counts[system]=dict(CLOSED=len(ts),INITIAL_STOP=sum(t['exit_reason']=='INITIAL_STOP' for t in ts),gross_R=__import__('math').fsum(rs),gross_PF=sum(x for x in rs if x>0)/-sum(x for x in rs if x<0))
 for s,n,st,r,pf in [('H1',355,141,172.416620,2.206747),('M15',1114,356,390.442918,1.778435)]:
  a=counts[s];assert a['CLOSED']==n and a['INITIAL_STOP']==st and abs(a['gross_R']-r)<.0000005 and abs(a['gross_PF']-pf)<.0000005
 gate.update(archive_all_state_fields=fields,headline=counts);js(out/'CONTROL_RECONCILIATION.json',gate)
 print(json.dumps(gate),flush=True);return ss,cc
if __name__=='__main__':controls(HERE/'work/control')
