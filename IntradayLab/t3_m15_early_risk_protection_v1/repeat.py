"""Two fresh end-to-end raw-source repetitions, direct bytes AND SHA256."""
import json,os,subprocess,sys
from pathlib import Path
import common as C

def snapshot(root):return {str(p.relative_to(root)):C.file_sha(p) for p in sorted(root.rglob('*')) if p.is_file()}
def run():
    first={folder:snapshot(C.HERE/folder) for folder in ['results','audit']};C.write_json(C.HERE/'FIRST_FULL_PIPELINE_SHA256.json',first)
    rounds=[]
    for i in [1,2]:
        root=Path('/workspace/work')/('early_risk_repeat_'+str(i));assert not root.exists(),('FRESH_DIRECTORY_REQUIRED',root);root.mkdir()
        env=dict(os.environ,PYTHONDONTWRITEBYTECODE='1');log=[]
        for cmd in [ ['run.py','--output',str(root/'results')],['audit.py','--primary',str(root/'results'),'--output',str(root/'audit')],['report.py','--results',str(root/'results')],['audit_presentation.py','--primary',str(root/'results'),'--audit',str(root/'audit')]]:
            r=subprocess.run([sys.executable,str(C.HERE/cmd[0]),*cmd[1:]],env=env,capture_output=True,text=True);log.append(r.stdout+r.stderr);assert r.returncode==0,r.stdout+r.stderr
        checks=[]
        for folder in first:
            got=snapshot(root/folder);assert got.keys()==first[folder].keys()
            for name,h in got.items():
                equal=(root/folder/name).read_bytes()==(C.HERE/folder/name).read_bytes();checks.append({'folder':folder,'path':name,'sha256':h,'sha_equal':h==first[folder][name],'direct_bytes_equal':equal});assert equal and h==first[folder][name],('REPEAT_CHANGED',folder,name)
        (C.HERE/'logs'/f'REPEAT_{i}.txt').write_text('\n'.join(log));rounds.append({'round':i,'status':'PASS','checks':checks})
        print(json.dumps({'round':i,'status':'PASS','files':len(checks)}),flush=True)
    C.write_json(C.HERE/'REPEATABILITY.json',{'status':'PASS','repetitions':2,'fresh_full_primary_and_scalar_replay':True,'direct_byte_and_sha_checks':sum(len(r['checks']) for r in rounds),'rounds':rounds})
if __name__=='__main__':run()
