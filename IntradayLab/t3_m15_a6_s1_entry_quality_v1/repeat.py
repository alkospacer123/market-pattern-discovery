"""Two additional fresh-process whole pipelines; direct bytes plus SHA256."""
import json,subprocess,sys,tempfile
from pathlib import Path
import common as C


def inventory(root):return {str(p.relative_to(root)):C.file_sha(p) for p in sorted(root.rglob('*')) if p.is_file()}

def run():
    first=json.loads((C.HERE/'FIRST_COMPUTATION_SHA256.json').read_text())
    original_audit=json.loads((C.HERE/'FIRST_AUDIT_SHA256.json').read_text())
    for folder,hashes in [('results',first),('audit',original_audit)]:
        for p,h in hashes.items():assert C.file_sha(C.HERE/folder/p)==h,('FIRST_ARTIFACT_CHANGED',folder,p)
    expected={folder:inventory(C.HERE/folder) for folder in ('results','audit')}
    C.write_json(C.HERE/'FIRST_FULL_PIPELINE_SHA256.json',expected)
    receipts=[]
    for number in (1,2):
        with tempfile.TemporaryDirectory(prefix=f'entry-quality-repeat-{number}-',dir='/workspace/work') as tmp:
            root=Path(tmp);results=root/'results';audit=root/'audit'
            jobs=[('run.py',['--output',str(results)]),('audit.py',['--primary',str(results),'--output',str(audit)]),('report.py',['--results',str(results),'--audit',str(audit)]),('audit_presentation.py',['--results',str(results),'--audit',str(audit)])]
            for name,args in jobs:
                process=subprocess.run([sys.executable,str(C.HERE/name),*args],capture_output=True,text=True)
                assert process.returncode==0,process.stdout+process.stderr
            checks=[]
            for folder in ('results','audit'):
                actual=inventory(root/folder);assert actual==expected[folder],('REPEAT_SHA_MISMATCH',number,folder)
                for path in actual:
                    identical=(root/folder/path).read_bytes()==(C.HERE/folder/path).read_bytes();assert identical,('REPEAT_BYTES_MISMATCH',number,folder,path)
                    checks.append({'path':folder+'/'+path,'sha256':actual[path],'direct_bytes_identical':identical})
            receipts.append({'repeat':number,'status':'PASS','fresh_processes':4,'files':len(checks),'checks':checks})
            print(json.dumps({'repeat':number,'status':'PASS','direct_bytes_and_sha256_files':len(checks)}),flush=True)
    C.write_json(C.HERE/'REPEATABILITY.json',{'status':'PASS','additional_fresh_full_repeats':2,'primary_files_each':len(expected['results']),'audit_files_each':len(expected['audit']),'direct_bytes_and_sha256_checks':sum(r['files'] for r in receipts),'frozen_control_features_full_diagnostics_scalar_audit_russian_reports_presentation_repeated':True,'receipts':receipts})

if __name__=='__main__':run()
