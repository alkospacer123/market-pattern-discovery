"""Two additional fresh full pipelines, direct bytes AND SHA256 for every result/audit file."""
import argparse,json,subprocess,sys
from pathlib import Path
import common as C,integrity as F

def inventory(path):
    return {p.relative_to(path).as_posix():C.file_sha(p) for p in sorted(path.rglob('*')) if p.is_file()}

def main(root):
    F.freeze_guard();baseline={'results':inventory(C.HERE/'results'),'audit':inventory(C.HERE/'audit')}
    C.write_json(C.HERE/'FIRST_PIPELINE_SHA256.json',baseline)
    checks=[]
    for number in (1,2):
        work=C.HERE/'work'/('repeat_'+str(number));assert not work.exists(),'REPEAT_DESTINATION_MUST_BE_FRESH'
        work.mkdir()
        for script,args in [('run.py',['--output',str(work/'results')]),('audit.py',['--primary',str(work/'results'),'--output',str(work/'audit')])]:
            call=subprocess.run([sys.executable,str(C.HERE/script),'--data-root',str(root)]+args,capture_output=True,text=True)
            (work/(script+'.txt')).write_text(call.stdout+call.stderr)
            assert call.returncode==0,call.stdout+call.stderr
        count=0
        for folder,initial in baseline.items():
            new=inventory(work/folder);assert new.keys()==initial.keys(),('FILE_SET_DIFFERENT',number,folder)
            for name,digest in initial.items():
                direct=(C.HERE/folder/name).read_bytes()==(work/folder/name).read_bytes()
                identical=digest==new[name];assert direct and identical,('NONDETERMINISTIC',number,folder,name)
                checks.append({'repeat':number,'path':folder+'/'+name,'direct_bytes_equal':direct,'sha256_equal':identical,'sha256':digest});count+=1
        print(json.dumps({'repeat':number,'status':'PASS','files':count,'fresh_full_CONTROL_and_audit':True}),flush=True)
    C.write_csv(C.HERE/'REPEAT_FILES.csv',checks)
    C.write_json(C.HERE/'REPEATABILITY.json',{'status':'PASS','additional_fresh_pipelines':2,'baseline_file_count':sum(map(len,baseline.values())),
        'direct_byte_checks':len(checks),'sha256_checks':len(checks),'every_result_and_audit_file_checked':True,
        'metadata_excluded':'outer execution logs/receipts only; none within results or audit','files':checks})

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--data-root',type=Path,default=Path('/workspace/market-pattern-data'));main(p.parse_args().data_root)
