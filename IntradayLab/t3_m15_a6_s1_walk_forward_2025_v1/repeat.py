"""Two fresh full pipelines plus fresh audits; compare original files by bytes+SHA."""
import json,subprocess,sys
from pathlib import Path
import common as C

def files(root):return {p.relative_to(root).as_posix():p for p in root.rglob('*') if p.is_file()}
def run(root,first,scratch):
    initial=files(first/'results')|{ 'audit/'+k:v for k,v in files(first/'audit').items() }
    original={(('results/'+k) if not k.startswith('audit/') else k):p for k,p in initial.items()}
    before={k:C.file_sha(p) for k,p in original.items()};runs=[]
    for name in ('repeat_1','repeat_2'):
        folder=scratch/name;folder.mkdir(parents=True,exist_ok=False)
        subprocess.run([sys.executable,str(C.HERE/'pipeline.py'),'--data-root',str(root),'--output',str(folder/'results')],check=True)
        subprocess.run([sys.executable,str(C.HERE/'audit.py'),'--data-root',str(root),'--primary',str(folder/'results'),'--output',str(folder/'audit')],check=True)
        replay={**{'results/'+k:v for k,v in files(folder/'results').items()},**{'audit/'+k:v for k,v in files(folder/'audit').items()}}
        assert set(replay)==set(original),'FILE_SET_MISMATCH'
        checks=[]
        for key,path in original.items():
            identical=path.read_bytes()==replay[key].read_bytes();digest=C.file_sha(replay[key]);assert identical and digest==before[key],('REPEAT_MISMATCH',name,key)
            checks.append({'path':key,'bytes_identical':identical,'sha256':digest,'original_sha256':before[key]})
        runs.append({'run':name,'status':'PASS','files_compared':len(checks),'direct_byte_and_SHA256_checks':checks})
    assert all(C.file_sha(original[k])==v for k,v in before.items()),'ORIGINAL_RESULTS_CHANGED'
    C.write_json(C.HERE/'FIRST_PIPELINE_SHA256.json',before)
    C.write_json(C.HERE/'REPEATABILITY.json',{'status':'PASS','two_fresh_full_runs':True,'original_files_unchanged':True,'runs':runs,'method':'fresh processes, fresh safe raw prefix reads, CONTROL then sequential W1-W4, fresh scalar auditor, direct bytes AND SHA256'})
if __name__=='__main__':run(Path('/workspace/market-pattern-data'),C.HERE,Path('/workspace/work/wf-task'))
