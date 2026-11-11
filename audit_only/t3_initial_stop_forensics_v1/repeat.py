"""Three isolated full processes after code freeze, exact bytes and SHA checks."""
import argparse,hashlib,json,shutil,subprocess,sys
from pathlib import Path
sys.dont_write_bytecode=True
HERE=Path(__file__).resolve().parent
ROOT=HERE.parents[1]
def digest(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def main(prefix,publish):
 assert prefix.replace('_','').replace('-','').isalnum()
 assert (HERE/'CODE_FREEZE.json').exists(),'FREEZE_REQUIRED'
 outputs=[];processes=[]
 for index in range(3):
  out=HERE/'work'/f'{prefix}_{index}';assert not out.exists(),'FRESH_PREFIX_REQUIRED';log=HERE/'work'/f'{prefix}_{index}.log'
  command=[sys.executable,'-B',str(HERE/'run.py'),'--output',str(out)]
  with log.open('w') as f:completed=subprocess.run(command,cwd=ROOT,stdout=f,stderr=subprocess.STDOUT)
  assert completed.returncode==0,('FULL_RUN_FAILED',index,str(log))
  files={str(p.relative_to(out)):digest(p) for p in sorted(out.rglob('*')) if p.is_file()};assert files
  if outputs:
   assert files==processes[0]['files_sha256'],('SHA256_DIFFERENCE',index)
   for name in files:assert (out/name).read_bytes()==(outputs[0]/name).read_bytes(),('DIRECT_BYTES_DIFFERENCE',index,name)
  outputs.append(out);processes.append(dict(run=index,fresh_python_process=True,status='PASS',files_sha256=files))
  print(f'Full fresh process {index+1}/3 PASS; {len(files)} files',flush=True)
 receipt=dict(status='PASS',phase='AFTER_CODE_FREEZE',first_plus_fresh_repeats=3,fresh_repeats=2,all_files_direct_bytes_equal=True,all_files_SHA256_equal=True,generated_files_per_run=len(processes[0]['files_sha256']),code_freeze_sha256=digest(HERE/'CODE_FREEZE.json'),processes=processes,logs='Ignored work/; no timestamps or elapsed time in deterministic artifacts',scope='Every generated CSV/JSON/MD/gzip including reports and all independent audits; REPEATABILITY itself excluded to avoid self-reference')
 (HERE/'work'/f'{prefix}_REPEATABILITY.json').write_text(json.dumps(receipt,indent=2,sort_keys=True)+'\n')
 if publish:
  for name in processes[0]['files_sha256']:
   target=HERE/name;target.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(outputs[0]/name,target)
  shutil.copyfile(HERE/'work'/f'{prefix}_REPEATABILITY.json',HERE/'REPEATABILITY.json')
  print('Published verified artifacts only inside authorized audit directory',flush=True)
if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('--prefix',default='repro');p.add_argument('--publish',action='store_true');a=p.parse_args();main(a.prefix,a.publish)
