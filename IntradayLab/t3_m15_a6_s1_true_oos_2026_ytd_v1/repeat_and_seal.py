"""Three complete independent-process runs; compare immutable result bytes.

Run with real pinned OHLC checkout, only after synthetic pre-read tests.
Copies one full output into results/; keeps repeat SHA/strict status, not raw
duplicate artifacts. Does not touch prior studies, data checkout or robot.
"""
import argparse
import hashlib
import json
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile

HERE=Path(__file__).resolve().parent
def inventory(path):
    found={}
    for p in sorted(path.rglob('*')):
        if p.is_file():
            found[str(p.relative_to(path))]=hashlib.sha256(p.read_bytes()).hexdigest()
    return found

def main():
    p=argparse.ArgumentParser()
    p.add_argument('--data-root',type=Path,required=True)
    p.add_argument('--output',type=Path,default=HERE/'results')
    p.add_argument('--end-exclusive',default="2026-10-13T00:00:00+03:00")
    a=p.parse_args()
    assert a.data_root.exists(),'MISSING_SOURCE_CHECKOUT'
    assert not a.output.exists(),'OUTPUT_MUST_BE_NEW_NO_OVERWRITE'
    subprocess.run([sys.executable,'-m','unittest','-v','test_ytd'],cwd=HERE,check=True)
    with tempfile.TemporaryDirectory(prefix='intradaylab-oos-2026-ytd-') as temp:
        base=Path(temp)
        runs=[]
        for i in range(3):
            dest=base/('full_run_'+str(i+1))
            cmd=[sys.executable,str(HERE/'run_ytd_oos.py'),
                 '--data-root',str(a.data_root.resolve()),
                 '--output',str(dest),
                 '--end-exclusive',a.end_exclusive]
            with (base/('RUN_'+str(i+1)+'.log')).open('w') as log:
                process=subprocess.run(cmd,cwd=HERE,stdout=log,stderr=subprocess.STDOUT)
            if process.returncode:
                a.output.mkdir(parents=True,exist_ok=False)
                shutil.copytree(dest,a.output/'failure_evidence',dirs_exist_ok=True)
                shutil.copy2(base/('RUN_'+str(i+1)+'.log'),a.output/'FAILED_RUN.log')
                raise RuntimeError('FULL_RUN_FAILED_STOP: '+str(process.returncode))
            runs.append(inventory(dest))
            if i:
                assert runs[i].keys()==runs[0].keys(),'FULL_REPEAT_FILE_SET_MISMATCH_STOP'
                for name in runs[0]:
                    assert (base/'full_run_1'/name).read_bytes()==(dest/name).read_bytes(),('DIRECT_BYTE_MISMATCH_STOP',i,name)
            print('COMPLETE_FULL_RUN_'+str(i+1)+'_PASS',flush=True)
        assert runs[0]==runs[1]==runs[2], 'FULL_REPEAT_BYTE_MISMATCH_STOP'
        a.output.mkdir(parents=True,exist_ok=False)
        for src in sorted((base/'full_run_1').rglob('*')):
            if src.is_file():
                dst=a.output/src.relative_to(base/'full_run_1')
                dst.parent.mkdir(parents=True,exist_ok=True)
                shutil.copy2(src,dst)
        seal={'status':'PASS','test_suite':'test_ytd',
              'three_independent_full_runs_byte_identical':True,
              'full_runs':3,'repeats_after_first':2,
              'file_count':len(runs[0]),
              'files_SHA256':runs[0],
              'data_cutoff_end_exclusive':a.end_exclusive,
              'cost_policy':'GROSS_ONLY',
              'canonical_wf_prefix_revalidated_on_each_run':True,
              'direct_bytes_compared':True,
              'independent_audit_on_each_full_run':True,
              'LIVE_authorized':False}
        (a.output/'REPEATABILITY.json').write_text(json.dumps(seal,sort_keys=True,indent=2)+'\n')
        for i in range(3):shutil.copy2(base/('RUN_'+str(i+1)+'.log'),a.output/('RUN_'+str(i+1)+'.log'))
        print(json.dumps({'status':'PASS','files':len(runs[0]),
                          'output':str(a.output),'full_runs':3}))
if __name__=='__main__':
    main()
