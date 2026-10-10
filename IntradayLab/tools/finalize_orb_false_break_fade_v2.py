#!/usr/bin/env python3
"""Record exact repeats, protected blobs and code/data provenance; no replay."""
import argparse
import hashlib
import json
from pathlib import Path
import subprocess

LAB=Path(__file__).resolve().parents[1]
ROOT=LAB.parent
OUT=LAB/'results/stage2_orb_false_break_fade_m5_v2_research'
RECEIVED='b3b5069025e9a13814ac8cc7905aa706683b06a6'
MAIN='9914ebbc97e3ba1fded1b6f06fb4bd66a82c2811'
FREEZE='6843dbf8037a9df6eae6f88e8d1301c9f60e24bd'


def git(*args,cwd=ROOT):
    return subprocess.check_output(['git','-C',str(cwd),*args])


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def dump(path,value):
    path.write_text(json.dumps(value,indent=2,ensure_ascii=False,sort_keys=True)+'\n')


def core_hashes():
    names=list(json.loads((OUT/'sha256.json').read_text()))+['sha256.json']
    names+=['v1_daywise/'+n for n in json.loads((OUT/'v1_daywise/file_hashes.json').read_text())]+['v1_daywise/file_hashes.json']
    return {n:sha(OUT/n) for n in sorted(names)}


def finish(args):
    first=json.loads(args.repeat_reference.read_text());second=core_hashes()
    assert first==second,'NONDETERMINISTIC_RESEARCH_ARTIFACTS'
    text=args.tests_log.read_text()
    assert '\nOK\n' in text and 'Ran 269 tests' in text,'TEST_RECEIPT_NOT_PASS'
    (OUT/'tests.log').write_text(text)
    allowed={'IntradayLab/tools/run_orb_false_break_fade_daywise.py','IntradayLab/tools/run_orb_false_break_fade_v2.py'}
    old=git('ls-tree','-r','--name-only',RECEIVED).decode().splitlines()
    protected={};discrepancies=[]
    for name in old:
        if name in allowed:continue
        current=(ROOT/name).read_bytes();expected=git('show',RECEIVED+':'+name)
        if current!=expected:discrepancies.append(name)
        protected[name]=hashlib.sha256(current).hexdigest()
    assert not discrepancies,discrepancies
    assert git('rev-parse','HEAD',cwd=args.data_root).decode().strip()=='f8486b446cf3d5f9f3cba6dfec32bdef8fd184c8'
    assert not git('status','--porcelain=v1','--untracked-files=all',cwd=args.data_root).strip()
    conf=LAB/'config/stage2_orb_false_break_fade_m5_v2_research.json'
    assert conf.read_bytes()==git('show',FREEZE+':IntradayLab/config/'+conf.name)
    trees={}
    for root in git('ls-tree','-d','--name-only',RECEIVED).decode().splitlines():
        if root=='IntradayLab':continue
        tree=git('rev-parse',RECEIVED+':'+root).decode().strip()
        assert tree==git('rev-parse','HEAD:'+root).decode().strip()
        assert tree==git('rev-parse',MAIN+':'+root).decode().strip()
        trees[root]=tree
    audit=json.loads((OUT/'independent_audit.json').read_text());assert audit['status']=='PASS'
    dump(OUT/'protected_file_hashes.json',protected)
    dump(OUT/'validation.json',dict(status='PASS',tests=269,independent_audit='PASS',
         deterministic_repeats=dict(status='PASS',compared_artifacts=len(first),first=first,second=second),
         received_HEAD=RECEIVED,protected_original_files=len(protected),protected_discrepancies=[],
         protected_root_trees=trees,data_ref_verified=True,data_worktree_clean=True,
         frozen_config_byte_identical=True,technical_parameters_changed=False,
         source_2024_plus_bytes_read=0,real_account_flat_reconciliation=False))
    code=git('rev-parse','HEAD').decode().strip()
    files=[p for p in (LAB/'tools').glob('*orb_false_break_fade*.py')]+[conf]
    changed=set(git('diff','--name-only',MAIN,'HEAD').decode().splitlines())
    changed.update(str(p.relative_to(ROOT)) for p in OUT.rglob('*') if p.is_file())
    changed.update(str((OUT/n).relative_to(ROOT)) for n in ['manifest.json','changed_files.txt'])
    (OUT/'changed_files.txt').write_text('\n'.join(sorted(changed))+'\n')
    artifacts={str(p.relative_to(OUT)):sha(p) for p in OUT.rglob('*') if p.is_file() and p.name!='manifest.json'}
    dump(OUT/'manifest.json',dict(schema=2,classification='INCONCLUSIVE_UNRESOLVED',
         continuous_annual_net_pf_dd=None,research='CONDITIONAL_INDEPENDENT_DAYS_CLOSED_ONLY',
         v2_post_2023_v1_outcomes_not_OOS=True,main=MAIN,received_HEAD=RECEIVED,implementation_SHA=code,
         freeze_v2=FREEZE,config_sha256=sha(conf),source_repository='alkospacer123/market-pattern-data',
         source_ref='f8486b446cf3d5f9f3cba6dfec32bdef8fd184c8',
         implementation_sha256={str(p.relative_to(ROOT)):sha(p) for p in files},
         artifact_sha256=artifacts,protected_root_trees=trees,tests=269,
         final_artifact_commit='Commit containing this manifest; excluded from its own fingerprint',
         technical_errors_corrected=['daywise output outside v2 root','self-recursive repeated hash manifests',
             'absent full days lost from daywise signal/day tables',
             'future UNKNOWN incorrectly labelled before missing slot; fixed diagnostic reason only'],
         audit='PASS',stage3=False,walk_forward=False,true_oos=False,live=False,merge=False))
    print(json.dumps({'status':'PASS','implementation_SHA':code,'deterministic_artifacts':len(first),'protected_files':len(protected),'output':str(OUT)}))


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--data-root',type=Path,required=True)
    p.add_argument('--repeat-reference',type=Path,required=True)
    p.add_argument('--tests-log',type=Path,required=True)
    p.add_argument('--snapshot',action='store_true')
    a=p.parse_args()
    if a.snapshot:dump(a.repeat_reference,core_hashes())
    else:finish(a)
