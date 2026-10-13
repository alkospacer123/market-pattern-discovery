"""Two fresh full process chains; exact bytes and SHA256, no timing fields."""
import hashlib,json,os,subprocess,sys
from pathlib import Path
HERE=Path(__file__).resolve().parent

def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def command(name,args,log):
    env=os.environ.copy();env['PYTHONDONTWRITEBYTECODE']='1';env['MPLCONFIGDIR']=str(HERE/'work/mplconfig')
    r=subprocess.run([sys.executable,str(HERE/name),*map(str,args)],capture_output=True,text=True,env=env)
    log.write_text(r.stdout+r.stderr);assert r.returncode==0,(name,r.stdout,r.stderr)
def run(data):
    all_results=[]
    for i in [1,2]:
        base=HERE/f'work/repeat_{i}';base.mkdir(parents=True,exist_ok=True);results=base/'results';audit=base/'audit'
        command('diagnose.py',['--data-root',data,'--output',results],base/'execution.txt')
        command('audit.py',['--data-root',data,'--target',results,'--output',audit],base/'audit.txt')
        command('render_report.py',['--source',results,'--audit',audit,'--output',results],base/'presentation.txt')
        command('audit_presentation.py',['--source',results,'--output',audit/'PRESENTATION_AUDIT.json'],base/'presentation_audit.txt')
        record={'repeat':i,'status':'PASS','files':{}}
        for directory in ['results','audit']:
            current=base/directory;original=HERE/directory
            assert sorted(p.name for p in current.iterdir() if p.is_file())==sorted(p.name for p in original.iterdir() if p.is_file())
            for p in sorted(current.iterdir()):
                if p.is_file():
                    ref=original/p.name;assert p.read_bytes()==ref.read_bytes(),('BYTE_DIFFERENCE',i,directory,p.name)
                    digest=sha(p);assert digest==sha(ref)
                    record['files'][f'{directory}/{p.name}']=digest
        all_results.append(record)
        print(json.dumps({'repeat':i,'status':'PASS','direct_byte_equal':True,'files':len(record['files'])}),flush=True)
    (HERE/'REPEATABILITY.json').write_text(json.dumps({'status':'PASS','fresh_process_repeats':2,'direct_byte_equality':True,'SHA256_equality':True,'chains':'primary unchanged replay / diagnostics + scalar audit + Russian report/standalone SVG + presentation reconciliation','repeats':all_results},indent=2,sort_keys=True)+'\n')

if __name__=='__main__':run(Path(sys.argv[1]))
