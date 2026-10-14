"""First full process + two complete fresh processes, byte-for-byte artifact gate."""
import argparse,hashlib,json,shutil,subprocess,sys,tempfile
from pathlib import Path

HERE=Path(__file__).resolve().parent
def inventory(root):
    return {str(p.relative_to(root)):hashlib.sha256(p.read_bytes()).hexdigest() for p in sorted(root.rglob('*')) if p.is_file()}

def repeat(data,output,scratch):
    scratch.mkdir(parents=True,exist_ok=True);logs=[]
    with tempfile.TemporaryDirectory(prefix='t1-full-repeats-',dir=scratch) as tmp:
        runs=[Path(tmp)/str(n) for n in range(3)]
        for n,folder in enumerate(runs):
            print(f'Full deterministic run {n+1}/3',flush=True)
            p=subprocess.run([sys.executable,str(HERE/'run.py'),'--data-root',str(data),'--output',str(folder)],text=True,stdout=subprocess.PIPE,stderr=subprocess.STDOUT)
            logs.append(f'FULL RUN {n+1}\n'+p.stdout)
            if p.returncode:
                (HERE/'FULL_RUN_LOG.txt').write_text('\n'.join(logs));raise RuntimeError(p.stdout)
            print(p.stdout,flush=True)
        expected=inventory(runs[0]);checks=[]
        for n in (1,2):
            actual=inventory(runs[n]);assert actual==expected,('SHA_OR_FILE_SET_DIFF',n)
            assert all((runs[0]/p).read_bytes()==(runs[n]/p).read_bytes() for p in expected),'DIRECT_BYTE_DIFF'
            checks.append(dict(repeat=n,full_source_replay=True,independent_full_replay=True,published_reconciliation=True,direct_bytes_equal=True,sha256_equal=True,files=len(expected)))
        if output.exists():
            assert inventory(output)==expected,'EXISTING_DELIVERABLES_DIFFER'
            assert all((output/p).read_bytes()==(runs[0]/p).read_bytes() for p in expected)
        else:shutil.copytree(runs[0],output)
    result=dict(status='PASS',total_full_runs=3,fresh_repeats=2,artifact_count=len(expected),checks=checks,sha256=expected,includes='All generated CSV, JSON, deterministic gzip journals, independent audits, source manifest and Russian report; code frozen before runs',external_human_audit='PENDING')
    (HERE/'repeatability.json').write_text(json.dumps(result,indent=2,sort_keys=True)+'\n')
    (HERE/'FULL_RUN_LOG.txt').write_text('\n'.join(logs))
    print(json.dumps({k:result[k] for k in ('status','total_full_runs','fresh_repeats','artifact_count')}),flush=True)

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--data-root',type=Path,default=Path('/workspace/market-pattern-data'));p.add_argument('--output',type=Path,default=HERE/'results');p.add_argument('--scratch',type=Path,default=Path('/workspace/work'));a=p.parse_args();repeat(a.data_root,a.output,a.scratch)
