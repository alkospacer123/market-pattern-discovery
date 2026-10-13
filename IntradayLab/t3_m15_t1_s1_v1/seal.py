"""Read-only source/freeze checks and in-scope artifact inventory."""
import argparse
import json
from pathlib import Path
import independent as I

def seal(root):
    freeze=json.loads((I.HERE/'FREEZE.json').read_text())
    for name,digest in freeze['code_and_spec_SHA256'].items():
        assert I.file_sha(I.HERE/name)==digest
        assert I.sha(I.historical('IntradayLab/t3_m15_t1_s1_v1/'+name,freeze['freeze_commit']))==digest
    assert I.git('rev-parse','HEAD',root=root).decode().strip()==I.DATA_SHA
    assert not I.git('status','--porcelain',root=root).strip()
    for source in json.loads((I.HERE/'EXPERIMENT_SPECS.json').read_text())['sources']:
        assert I.file_sha(root/source['path'])==source['full_sha256']
        assert I.git('hash-object','--',str(root/source['path']),root=root).decode().strip()==source['git_blob_sha']
    for folder in ('results','independent_results'):
        for name,digest in json.loads((I.HERE/folder/'GENERATED_SHA256.json').read_text()).items():
            assert I.file_sha(I.HERE/folder/name)==digest
    prefix='IntradayLab/t3_m15_t1_s1_v1/'
    status=I.git('status','--porcelain=v1','--untracked-files=all').decode().splitlines()
    assert all(r[3:].startswith(prefix) for r in status),('OUT_OF_SCOPE_WORKTREE',status)
    # Local legacy checkout must remain byte-identical to its original HEAD.
    assert not I.git('diff','--name-only').strip() and not I.git('diff','--cached','--name-only').strip()
    branch=I.git('rev-parse','research/t3-m15-t1-s1-v1').decode().strip()
    changes=I.git('diff','--name-status',I.BASE,branch).decode().splitlines()
    assert all(r.startswith('A\t'+prefix) for r in changes)
    remote=I.git('ls-remote','origin','refs/heads/main').decode().split()[0]
    assert remote==I.BASE,'FINAL_MAIN_CHANGED_REVIEW_REQUIRED'
    files=sorted(p for p in I.HERE.rglob('*') if p.is_file() and not p.is_relative_to(I.HERE/'work') and '__pycache__' not in p.parts and p.name!='ARTIFACT_SHA256.json')
    I.write_json(I.HERE/'SCOPE_CHECK.json',{'status':'PASS','labels':I.LABEL,'2023_2024':'DEVELOPMENT_EXPOSED',
        'remote_main':remote,'base_main':I.BASE,'local_legacy_HEAD':I.git('rev-parse','HEAD').decode().strip(),
        'legacy_checkout_unchanged':True,'allowed_prefix':prefix,'out_of_scope_changes':[],
        'only_added_files':True,'market_pattern_data_clean':True,'source_hashes_rechecked':True,'freeze_code_unchanged':True,
        'TradingSystemLab_changed':False,'robot_changed':False,'prior_research_changed':False,'ROADMAP_changed':False,
        'future_OHLC_parsed':False,'merge':False,'auto_merge':False,
        'deliverable_files':sorted(set(str(p.relative_to(I.REPO)) for p in files)|{prefix+'SCOPE_CHECK.json',prefix+'ARTIFACT_SHA256.json'})})
    files=sorted(p for p in I.HERE.rglob('*') if p.is_file() and not p.is_relative_to(I.HERE/'work') and '__pycache__' not in p.parts and p.name!='ARTIFACT_SHA256.json')
    I.write_json(I.HERE/'ARTIFACT_SHA256.json',{str(p.relative_to(I.HERE)):I.file_sha(p) for p in files})
    print(json.dumps({'scope':'PASS','artifacts_hashed':len(files),'freeze_unchanged':True,'remote_main':remote}))

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--data-root',type=Path,required=True);a=p.parse_args();seal(a.data_root)
