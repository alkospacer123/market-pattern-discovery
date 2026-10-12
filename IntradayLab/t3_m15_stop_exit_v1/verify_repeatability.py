"""Two fresh-process repeats; scope and final artifact checksum inventory."""
import argparse
import hashlib
import json
from pathlib import Path
import subprocess
import sys

HERE = Path(__file__).resolve().parent
REPO = HERE.parent.parent
MAIN = 'bc4f95f48b332f43d79ed10f26fc03c5ad01cd97'


def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def js(p,v):p.write_text(json.dumps(v,sort_keys=True,indent=2,allow_nan=False)+'\n')


def main(data_root):
    primary = json.loads((HERE/'results/GENERATED_SHA256.json').read_text())
    repeats = []
    for n in (1,2):
        target = HERE/'work'/f'repeat{n}'
        assert not target.exists(), 'FRESH_REPEAT_DIRECTORY_REQUIRED'
        subprocess.run([sys.executable,str(HERE/'research.py'),'--data-root',str(data_root),'--output',str(target)],check=True)
        generated = json.loads((target/'GENERATED_SHA256.json').read_text())
        assert generated == primary, ('DETERMINISM_FAILED',n)
        assert sha(target/'GENERATED_SHA256.json') == sha(HERE/'results/GENERATED_SHA256.json')
        repeats.append({'repeat':n,'fresh_process':True,'files_compared':len(primary)+1,'byte_identical':True,
            'aggregate_sha256':sha(target/'GENERATED_SHA256.json')})
    js(HERE/'REPEATABILITY.json',{'status':'PASS','primary_plus_fresh_repeats':3,'repeats':repeats,
        'scope':'All deterministic replay outputs including source manifest, controls, trade journals, signal/exit decisions and reports'})
    changed = subprocess.check_output(['git','-C',str(REPO),'diff','--name-only',MAIN]).decode().splitlines()
    other = [p for p in changed if not p.startswith('IntradayLab/t3_m15_stop_exit_v1/')]
    assert not other, ('OUT_OF_SCOPE_CHANGE',other)
    forbidden = subprocess.check_output(['git','-C',str(REPO),'status','--porcelain=v1','--untracked-files=all']).decode().splitlines()
    assert all(line[3:].startswith('IntradayLab/t3_m15_stop_exit_v1/') for line in forbidden), ('OUT_OF_SCOPE_WORKTREE',forbidden)
    js(HERE/'SCOPE_CHECK.json',{'status':'PASS','base_main':MAIN,'allowed_prefix':'IntradayLab/t3_m15_stop_exit_v1/',
        'out_of_scope_changed_files':other,'immutable_source_sha256_checked_by':'audit.py SOURCE_MANIFEST.json',
        'raw_data_read_only':True,'broker_endpoints_used':False,'production_changed':False,'merge':False,'auto_merge':False})
    artifact_paths = sorted(p for p in HERE.rglob('*') if p.is_file() and not p.is_relative_to(HERE/'work') and p.name != 'ARTIFACT_SHA256.json')
    js(HERE/'ARTIFACT_SHA256.json',{str(p.relative_to(HERE)):sha(p) for p in artifact_paths})
    print(json.dumps({'repeatability':'PASS','repeats':2,'artifact_hashes':len(artifact_paths),'scope':'PASS'}))


if __name__ == '__main__':
    p = argparse.ArgumentParser();p.add_argument('--data-root',type=Path,required=True)
    main(p.parse_args().data_root)
