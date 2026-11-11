"""Three fresh complete processes and direct-byte/SHA256 comparisons."""
import argparse,json,subprocess,sys
from pathlib import Path
sys.dont_write_bytecode=True
from common import HERE,sha,js

def repeat(h1,m15,scratch):
    scratch.mkdir(parents=True,exist_ok=True);runs=[]
    for number in range(3):
        out=scratch/f'run_{number+1}'
        assert not out.exists(),'REPEAT_REQUIRES_NEW_DIRECTORY'
        command=[sys.executable,str(HERE/'run.py'),'--h1-data',str(h1),'--m15-data',str(m15),'--output',str(out)]
        subprocess.run(command,check=True)
        runs.append(out)
    listing=[{p.name:sha(p) for p in sorted(r.iterdir()) if p.is_file()} for r in runs]
    assert listing[0]==listing[1]==listing[2],'SHA256_REPEAT_MISMATCH'
    for name in listing[0]:assert (runs[0]/name).read_bytes()==(runs[1]/name).read_bytes()==(runs[2]/name).read_bytes(),name
    result=dict(status='PASS',fresh_full_processes=3,initial_full_run=1,additional_fresh_full_repeats=2,
        every_output_direct_bytes_equal=True,every_output_sha256_equal=True,files_per_run=len(listing[0]),
        output_sha256=listing,code_freeze_sha256=sha(HERE/'CODE_FREEZE.json'),
        scope='Each process reauthenticates sources, recalculates frozen features, CONTROL and PARTIAL, tests, scalar execution audit and fresh CSV/Decimal arithmetic; no cache',
        independently_authored_algorithms=['primary causal replay','scalar position verifier','CSV Decimal arithmetic'],external_human_audit='PENDING')
    js(scratch/'REPEATABILITY.json',result);print('REPEATABILITY PASS',len(listing[0]),flush=True)
    return result
if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--h1-data',type=Path,required=True);p.add_argument('--m15-data',type=Path,required=True);p.add_argument('--scratch',type=Path,required=True)
    a=p.parse_args();repeat(a.h1_data.resolve(),a.m15_data.resolve(),a.scratch.resolve())
