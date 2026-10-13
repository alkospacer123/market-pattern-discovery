"""Two fresh complete runs/audits, direct bytes and SHA256 of every artifact."""
import json,subprocess,sys
from pathlib import Path
import common as C

def inventory(root):return {str(p.relative_to(root)):p for p in sorted(root.rglob('*')) if p.is_file()}

def main():
    evidence=[]
    for i in (1,2):
        folder=Path(f'/workspace/work/plateau_v2_repeat_{i}');assert not folder.exists(),'REPEAT_MUST_BE_FRESH';folder.mkdir()
        subprocess.run([sys.executable,str(C.HERE/'run.py'),'--output',str(folder/'results')],check=True,stdout=subprocess.DEVNULL)
        subprocess.run([sys.executable,str(C.HERE/'audit.py'),'--primary',str(folder/'results'),'--output',str(folder/'audit')],check=True,stdout=subprocess.DEVNULL)
        for group in ('results','audit'):
            original=inventory(C.HERE/group);repeated=inventory(folder/group);assert set(original)==set(repeated)
            for name,p in original.items():
                assert p.read_bytes()==repeated[name].read_bytes(),(i,group,name,'BYTE_MISMATCH')
                sha=C.file_sha(p);assert sha==C.file_sha(repeated[name]);evidence.append({'repeat':i,'path':group+'/'+name,'sha256':sha,'direct_bytes_identical':True})
        print(f'Repeat {i}: all generated primary/control/scalar/audit/presentation artifacts byte-identical',flush=True)
    C.write_json(C.HERE/'REPEATABILITY.json',{'status':'PASS','two_fresh_repeats':True,'fresh_processes':True,'evidence':evidence})

if __name__=='__main__':main()
