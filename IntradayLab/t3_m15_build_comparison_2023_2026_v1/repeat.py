"""Two fresh full repeats after PASS; direct bytes and SHA256 of every result."""
import argparse,concurrent.futures,json,os,subprocess,sys
from pathlib import Path
from io_utils import write_json,hash_file
from registry import HERE
def files(d):return {str(p.relative_to(d)):p for p in sorted(d.rglob('*')) if p.is_file() and p.suffix in ('.json','.csv','.gz','.md','.svg')}
def check(first,other):
 a=files(first);b=files(other);assert a.keys()==b.keys(),('ARTIFACT_SET_CHANGED',set(a)^set(b));details=[]
 for k,p in a.items():
  q=b[k];same=p.read_bytes()==q.read_bytes();assert same,('BYTE_MISMATCH',k)
  ha,hb=hash_file(p),hash_file(q);assert ha==hb
  details.append(dict(path=k,bytes=p.stat().st_size,sha256=ha,direct_bytes_equal=same))
 return dict(status='PASS',artifact_count=len(details),direct_bytes_and_SHA256=True,artifacts=details)
def run(first,data_root,pr513_root,output):
 assert json.loads((first/'AUDIT.json').read_text())['status']=='PASS'
 repeats=[first.parent/(first.name+'-repeat2'),first.parent/(first.name+'-repeat3')]
 def once(d):
  with d.with_suffix('.log').open('w') as f:subprocess.run([sys.executable,str(HERE/'run.py'),'--data-root',str(data_root),'--pr513-root',str(pr513_root),'--output',str(d),'--jobs','2'],check=True,stdout=f,stderr=subprocess.STDOUT,env=os.environ|{'PYTHONDONTWRITEBYTECODE':'1'})
  return check(first,d)
 with concurrent.futures.ThreadPoolExecutor(max_workers=2) as pool:results=list(pool.map(once,repeats))
 write_json(output,dict(status='PASS',first_run_plus_two_full_repeats=True,each_run='Canonical CONTROL 2023-2026 + 51 causal rule replays + independent scalar comparison + independent arithmetic + source immutability check',repeats=results,stdout_logs='Preserved separately; output-path-bearing runtime logs are not deterministic result artifacts'))
if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('--first',type=Path,required=True);p.add_argument('--data-root',type=Path,required=True);p.add_argument('--pr513-root',type=Path,required=True);p.add_argument('--output',type=Path,required=True);a=p.parse_args();run(a.first,a.data_root,a.pr513_root,a.output)
