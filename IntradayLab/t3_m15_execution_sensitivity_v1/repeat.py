"""Two fresh processes for replay and independent audit; direct byte equality."""
import json,subprocess,sys
from pathlib import Path
import common as C

def files(root):return {str(p.relative_to(root)):p for p in sorted(root.rglob('*')) if p.is_file()}

def main():
    evidence=[]
    for i in (1,2):
        folder=Path(f'/workspace/work/execution_repeat_{i}');assert not folder.exists(),'REPEAT_MUST_BE_FRESH'
        folder.mkdir()
        subprocess.run([sys.executable,str(C.HERE/'run.py'),'--output',str(folder/'results')],check=True)
        subprocess.run([sys.executable,str(C.HERE/'audit.py'),'--primary',str(folder/'results'),'--output',str(folder/'audit')],check=True,stdout=subprocess.DEVNULL)
        for name in ('results','audit'):
            original=files(C.HERE/name);repeated=files(folder/name);assert set(original)==set(repeated)
            rows=[]
            for path,p in original.items():
                assert p.read_bytes()==repeated[path].read_bytes(),(i,name,path,'BYTE_MISMATCH')
                digest=C.file_sha(p);assert digest==C.file_sha(repeated[path])
                rows.append({'path':name+'/'+path,'sha256':digest,'direct_bytes_identical':True})
            evidence.append({'repeat':i,'group':name,'files':rows,'status':'PASS'})
    C.write_json(C.HERE/'REPEATABILITY.json',{'status':'PASS','fresh_processes':True,'two_fresh_repeats':True,'evidence':evidence})
    print(json.dumps({'repeat_status':'PASS','groups':len(evidence)}))

if __name__=='__main__':main()
