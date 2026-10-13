"""Read-only protected code/tree/main checks. Does not open raw market data."""
import hashlib,json,subprocess
from pathlib import Path
HERE=Path(__file__).resolve().parent;ROOT=HERE.parent.parent
BASE='fa188b51fbd27df5a51a43a9742bc772a1c17abd';PREFIX=HERE.relative_to(ROOT).as_posix()+'/'
def git(*args,root=ROOT):return subprocess.check_output(['git','-C',str(root),*args]).decode()
def digest(p):
    h=hashlib.sha256()
    with p.open('rb') as f:
        for chunk in iter(lambda:f.read(1048576),b''):h.update(chunk)
    return h.hexdigest()
def save(n,x):(HERE/n).write_text(json.dumps(x,indent=2,sort_keys=True)+'\n')
def main():
    protected=json.loads((HERE/'PROTECTED_SHA256.json').read_text());diff=[]
    for path,expected in protected.items():
        observed=digest(ROOT/path)
        if observed!=expected:diff.append({'path':path,'expected':expected,'observed':observed})
    names=git('diff','--name-only',BASE).splitlines();outside=[p for p in names if not p.startswith(PREFIX)]
    tree_before={line.split('\t',1)[1]:line.split('\t',1)[0] for line in (HERE/'BASE_TREE_INVENTORY.txt').read_text().splitlines()}
    tree_after={line.split('\t',1)[1]:line.split('\t',1)[0] for line in git('ls-tree','-r','--full-tree','HEAD').splitlines()}
    tree_diff=[p for p,v in tree_before.items() if tree_after.get(p)!=v]
    code=json.loads((HERE/'FREEZE.json').read_text());code_diff=[p for p,v in code['code_spec_sha256'].items() if digest(HERE/p)!=v]
    main_sha=git('ls-remote','origin','refs/heads/main').split()[0]
    branch_sha=git('rev-parse','HEAD').strip()
    original=Path('/workspace/market-pattern-discovery');original_head=git('rev-parse','HEAD',root=original).strip();original_dirty=git('status','--porcelain',root=original).strip()
    data_sha=git('rev-parse','HEAD',root=Path('/workspace/market-pattern-data')).strip()
    seals={}
    for label in ('CONTROL','W1','W2','W3','W4'):
        folder=HERE/'results'/label;seal=json.loads((folder/'SEAL.json').read_text());mismatches=[p for p,v in seal['files_SHA256'].items() if digest(folder/p)!=v]
        assert not mismatches,('SEALED_RESULT_CHANGED',label,mismatches)
        seals[label]={'status':'PASS','files':len(seal['files_SHA256'])}
    report={'status':'PASS' if not (diff or outside or tree_diff or code_diff or original_dirty) and main_sha==BASE and data_sha=='f8486b446cf3d5f9f3cba6dfec32bdef8fd184c8' and original_head=='fbfb0650ac2af6c6b374d10b67dd62801cd0fcc4' else 'FAIL',
      'base_main':BASE,'actual_GitHub_main':main_sha,'research_branch_head_at_check':branch_sha,
      'protected_SHA256_files':len(protected),'protected_SHA256_differences':diff,'entire_preexisting_git_tree_differences':tree_diff,
      'changed_tracked_files':len(names),'outside_allowed_scope':outside,'frozen_code_spec_differences':code_diff,
      'canonical_engine_scalar_metrics_byte_identical_to_PR510':all(digest(HERE/n)==x['sha256'] for n,x in json.loads((HERE/'SOURCE_ORIGIN.json').read_text()).items()),
      'original_checkout_HEAD':original_head,'original_checkout_dirty':original_dirty,'data_HEAD_metadata_only':data_sha,
      'sealed_files_checks':seals,'ROADMAP_TradingSystemLab_robot_previous_studies_unchanged':not diff and not tree_diff,
      'raw_data_full_hash_performed':False,'TRUE_OOS_executed':False,'LIVE_broker_operations':False,
      'merge':False,'auto_merge':False,'external_human_review':'PENDING'}
    save('FINAL_MAIN_CHECK.json',report);assert report['status']=='PASS',report
    proc=subprocess.run(['git','-C',str(ROOT),'diff','--check',BASE],capture_output=True,text=True);assert proc.returncode==0,proc.stdout+proc.stderr
    save('SCOPE_CHECK.json',{'status':'PASS','changed_files':names,'all_new_files_under':PREFIX,'protected_tree_unchanged':True,'git_diff_check':'PASS'})
    print(json.dumps({'status':report['status'],'main':main_sha,'protected_files':len(protected),'scope_files':len(names),'seals':seals}))
if __name__=='__main__':main()
