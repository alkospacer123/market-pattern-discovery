"""Pre-variant gate, two full byte repeats, pinned source/freeze/scope verification."""
import argparse
import json
from pathlib import Path
import subprocess
import sys
from engine import E,HERE,MAIN
from research import js


def command(*args):return subprocess.run([sys.executable,*map(str,args)],check=True,capture_output=True,text=True)


def preflight(data_root):
    (HERE/'work').mkdir(exist_ok=True)
    tests=command(HERE/'test_research.py')
    (HERE/'TEST_RESULTS.txt').write_text(tests.stdout+tests.stderr)
    result=command(HERE/'research.py','--data-root',data_root,'--output',HERE/'work/preflight_control','--controls-only')
    (HERE/'CONTROL_LOG.txt').write_text(result.stdout+result.stderr)
    control=json.loads((HERE/'work/preflight_control/CONTROL_REPRODUCTION.json').read_text())
    assert control['status']=='PASS' and control['closed_total']==1442 and control['terminal_open']==2
    freeze=E.git(HERE,'log','-1','--format=%H','--','EXPERIMENT_SPECS.json')
    assert freeze!=MAIN
    for p in [*HERE.glob('*.py'),HERE/'EXPERIMENT_SPECS.json']:
        expected=subprocess.check_output(['git','-C',str(HERE),'show',f'{freeze}:{p.relative_to(HERE.parent.parent)}'])
        assert expected==p.read_bytes(),('UNCOMMITTED_IMPLEMENTATION',p)
    js(HERE/'PRE_VARIANT_GATE.json',{'control':'PASS','tests':'PASS','closed':1442,'terminal_open':2,'freeze_commit':freeze,
        'control_reproduction_sha256':E.sha_file(HERE/'work/preflight_control/CONTROL_REPRODUCTION.json'),
        'test_log_sha256':E.sha_file(HERE/'TEST_RESULTS.txt'),'before_variant_results':True})
    print(json.dumps({'pre_variant_gate':'PASS','freeze_commit':freeze}))


def finish(data_root):
    primary=json.loads((HERE/'results/GENERATED_SHA256.json').read_text())
    repeats=[]
    for n in (1,2):
        target=HERE/'work'/f'repeat{n}'
        assert not target.exists(),'FRESH_REPEAT_REQUIRED'
        r=command(HERE/'research.py','--data-root',data_root,'--output',target)
        (HERE/f'REPEAT_{n}_LOG.txt').write_text(r.stdout+r.stderr)
        other=json.loads((target/'GENERATED_SHA256.json').read_text())
        assert other==primary,('REPEAT_FAILED',n,[k for k in primary if primary[k]!=other.get(k)])
        for name in primary:assert (target/name).read_bytes()==(HERE/'results'/name).read_bytes(),('BYTE_MISMATCH',n,name)
        assert (target/'GENERATED_SHA256.json').read_bytes()==(HERE/'results/GENERATED_SHA256.json').read_bytes()
        repeats.append({'repeat':n,'files':len(primary)+1,'byte_identical':True,'aggregate_sha256':E.sha_file(target/'GENERATED_SHA256.json')})
    js(HERE/'REPEATABILITY.json',{'status':'PASS','full_fresh_process_repeats':2,'repeats':repeats,'scope':'all six replays, journals, reports, diagnostics, manifest, readable report'})
    seal(data_root)
    print(json.dumps({'repeatability':'PASS','scope':'PASS'}))


def seal(data_root):
    repo=HERE.parent.parent;prefix=str(HERE.relative_to(repo))+'/'
    changed=E.git(repo,'diff','--name-only',MAIN).splitlines()
    status=subprocess.check_output(['git','-C',str(repo),'status','--porcelain=v1','--untracked-files=all']).decode().splitlines()
    assert all(p.startswith(prefix) for p in changed)
    assert all(p[3:].startswith(prefix) for p in status)
    assert not E.git(data_root,'status','--porcelain=v1'),'DATA_WORKTREE_CHANGED'
    manifest=json.loads((HERE/'results/SOURCE_MANIFEST.json').read_text())
    for src in manifest['sources']:
        current=E.verify_source(data_root,src['path'])
        assert current['full_sha256']==src['full_sha256'] and current['git_blob_sha']==src['git_blob_sha']
    for name,sha in manifest['reference_sha256'].items():assert E.sha_file(HERE.parent/name)==sha
    for name,sha in manifest['implementation_sha256'].items():assert E.sha_file(HERE/name)==sha
    for name,sha in json.loads((HERE/'results/GENERATED_SHA256.json').read_text()).items():assert E.sha_file(HERE/'results'/name)==sha
    js(HERE/'SCOPE_CHECK.json',{'status':'PASS','base_main':MAIN,'allowed_prefix':prefix,'out_of_scope_changes':[],
        'changed_files':sorted(set(changed+[p[3:] for p in status]+[prefix+'SCOPE_CHECK.json',prefix+'ARTIFACT_SHA256.json'])),'raw_data_worktree_clean':True,'raw_source_hashes_rechecked':True,
        'frozen_references_unchanged':True,'TradingSystemLab_changed':False,'roadmap_changed':False,
        'future_OHLC_parsed':False,'merge':False,'auto_merge':False,'external_audit':'PENDING'})
    files=sorted(p for p in HERE.rglob('*') if p.is_file() and not p.is_relative_to(HERE/'work') and '__pycache__' not in p.parts and p.name!='ARTIFACT_SHA256.json')
    js(HERE/'ARTIFACT_SHA256.json',{str(p.relative_to(HERE)):E.sha_file(p) for p in files})

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--data-root',type=Path,required=True);p.add_argument('--preflight',action='store_true');p.add_argument('--seal-only',action='store_true')
    a=p.parse_args()
    if a.preflight:preflight(a.data_root)
    elif a.seal_only:seal(a.data_root)
    else:finish(a.data_root)
