"""Final Git/source/scope checks and non-self-referential artifact inventory."""
import hashlib,json,subprocess
from pathlib import Path
HERE=Path(__file__).resolve().parent;REPO=HERE.parent.parent
BASE='8c40950726446ebccb1ad80b8f129558470d9c11';DATA='f8486b446cf3d5f9f3cba6dfec32bdef8fd184c8'
def command(*args):return subprocess.check_output(args,text=True).strip()
def git(*args):return command('git','-C',str(REPO),*args)
def digest(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def run():
    remote=command('gh','api','repos/alkospacer123/market-pattern-discovery/branches/main','--jq','.commit.sha');assert remote==BASE,('MAIN_CHANGED_REVIEW_REQUIRED',remote)
    assert git('rev-parse','HEAD')==BASE
    data_root=Path('/workspace/market-pattern-data')
    assert command('git','-C',str(data_root),'rev-parse','HEAD')==DATA
    assert not command('git','-C',str(data_root),'status','--porcelain')
    source=json.loads((HERE/'results/SOURCE_MANIFEST.json').read_text())
    for path,h in source['references_SHA256'].items():assert digest(REPO/path)==h,('REFERENCE_CHANGED',path)
    for src in source['sources']:
        assert digest(data_root/src['path'])==src['full_sha256']
        assert command('git','-C',str(data_root),'hash-object',str(data_root/src['path']))==src['git_blob_sha']
    for path,h in json.loads((HERE/'READ_REFERENCES_SHA256.json').read_text()).items():assert digest(REPO/path)==h
    for name,h in source['code_SHA256'].items():assert digest(HERE/name)==h,('CODE_CHANGED_AFTER_FINAL_RUN',name)
    assert json.loads((HERE/'REPEATABILITY.json').read_text())['status']=='PASS'
    assert json.loads((HERE/'audit/AUDIT_RESULT.json').read_text())['status']=='PASS'
    assert json.loads((HERE/'audit/PRESENTATION_AUDIT.json').read_text())['status']=='PASS'
    prefix=str(HERE.relative_to(REPO))+'/'
    files=lambda:sorted(p for p in HERE.rglob('*') if p.is_file() and 'work' not in p.relative_to(HERE).parts and '__pycache__' not in p.relative_to(HERE).parts)
    planned=set(str(p.relative_to(REPO)) for p in files())|{prefix+'SCOPE_CHECK.json',prefix+'ARTIFACT_SHA256.json'}
    scope={'status':'PASS','base_main':BASE,'actual_GitHub_main_before_commit':remote,'pinned_data_commit':DATA,'source_worktree_clean':True,
        'only_new_directory':prefix,'existing_files_changed':False,'TradingSystemLab_changed':False,'ROADMAP_changed':False,
        'old_local_checkout_HEAD':command('git','-C','/workspace/market-pattern-discovery','rev-parse','HEAD'),
        'old_local_checkout_status':command('git','-C','/workspace/market-pattern-discovery','status','--porcelain'),
        'prior_T1_S1_tree_sha':git('rev-parse',f'{BASE}:IntradayLab/t3_m15_t1_s1_v1'),
        'protected_TradingSystemLab_tree_sha':git('rev-parse',f'{BASE}:TradingSystemLab'),
        'full_diff_paths':sorted(planned),'file_count':len(planned),'labels':'GROSS_ONLY / COSTS_DEFERRED / NOT_LIVE_READY','2023_2024':'DEVELOPMENT_EXPOSED',
        'new_strategy_variants_run':0,'numeric_Optimization_run':False,'merge_authorized':False,'completion':'ONE_DRAFT_PR_AUTO_MERGE_OFF_STOP'}
    assert scope['old_local_checkout_HEAD']=='249a9f58a726416bee9d3efd259a9824d348e292' and not scope['old_local_checkout_status']
    (HERE/'SCOPE_CHECK.json').write_text(json.dumps(scope,indent=2,sort_keys=True)+'\n')
    manifest={str(p.relative_to(HERE)):digest(p) for p in files() if p.name!='ARTIFACT_SHA256.json'}
    (HERE/'ARTIFACT_SHA256.json').write_text(json.dumps(manifest,indent=2,sort_keys=True)+'\n')
    subprocess.run(['git','-C',str(REPO),'add','-f','--',*[str(p.relative_to(REPO)) for p in files()]],check=True)
    diff=git('diff','--cached','--name-status',BASE)
    rows=[line.split('\t') for line in diff.splitlines()]
    assert all(status=='A' and path.startswith(prefix) for status,path in rows),('OUTSIDE_SCOPE',diff)
    assert {p for status,p in rows}==planned
    check=subprocess.run(['git','-C',str(REPO),'diff','--cached','--check'],capture_output=True,text=True)
    assert check.returncode==0,check.stdout[:1000]
    print(json.dumps({'status':'PASS','main':remote,'data':DATA,'added_files':len(rows),'only_new_directory':prefix}))
if __name__=='__main__':run()
