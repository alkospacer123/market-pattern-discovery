"""Three fresh complete runs after code freeze; exact output verification."""
import json,shutil,subprocess,sys
from pathlib import Path
from support import *

def run():
    freeze=json.loads((HERE/'CODE_FREEZE.json').read_text())
    for rel,d in freeze['files'].items():assert sha(HERE/rel)==d,('CODE_FREEZE_CHANGED',rel)
    base=HERE/'work/repeat'
    base.mkdir(parents=True,exist_ok=True)
    counter=1
    while any((base/f'v1_{counter}_{i}').exists() for i in range(3)):counter+=1
    runs=[]
    for i in range(3):
        dest=base/f'v1_{counter}_{i}'
        with (base/f'v1_{counter}_{i}.log').open('w') as log:
            subprocess.run([sys.executable,str(HERE/'run.py'),'--output',str(dest)],stdout=log,stderr=subprocess.STDOUT,check=True)
        files={p.name:sha(p) for p in sorted(dest.iterdir()) if p.is_file()}
        assert files,'NO_ARTIFACTS'
        if runs:
            assert files==runs[0]['files'],('SHA256_MISMATCH',i)
            for name in files:assert (dest/name).read_bytes()==(Path(runs[0]['path'])/name).read_bytes(),('BYTE_MISMATCH',i,name)
        runs.append(dict(path=str(dest),files=files))
        print(f'Fresh full run {i+1}/3 PASS; {len(files)} direct-byte/SHA256 artifacts',flush=True)
    for name in runs[0]['files']:shutil.copyfile(Path(runs[0]['path'])/name,HERE/name)
    receipt=dict(status='PASS',code_freeze_sha256=sha(HERE/'CODE_FREEZE.json'),
      fresh_processes=3,artifacts_per_run=len(runs[0]['files']),comparison='Every generated file: direct bytes AND SHA256, all three runs',
      full_control_replayed_each_process=True,development_recomputed_each_process=True,independent_checks_each_process=True,
      runs=[dict(path=str(Path(r['path']).relative_to(HERE)),files=r['files']) for r in runs],
      excludes='REPEATABILITY and SHA256SUMS are final receipts; static source/protocol/docs authenticated by CODE_FREEZE and SHA256SUMS')
    js(HERE/'REPEATABILITY.json',receipt)
    delivered=[p for p in sorted(HERE.iterdir()) if p.is_file() and p.name!='SHA256SUMS']
    (HERE/'SHA256SUMS').write_text(''.join(f'{sha(p)}  {p.name}\n' for p in delivered))
    print('PUBLISHED_ONLY_AFTER_ALL_THREE_MATCH',flush=True)

if __name__=='__main__':run()
