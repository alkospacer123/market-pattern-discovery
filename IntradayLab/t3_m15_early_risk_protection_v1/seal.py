"""Final add-only scope, protected reference/source integrity and artifact inventory."""
import json,subprocess
import common as C

def run():
    start=json.loads((C.HERE/'START_GATE.json').read_text());prefix='IntradayLab/t3_m15_early_risk_protection_v1/'
    changed=C.git('diff','--name-status',C.BASE).decode().splitlines();assert all(line.startswith('A\t'+prefix) for line in changed)
    unstaged=C.git('diff','--name-only').decode().splitlines();assert all(p.startswith(prefix) for p in unstaged)
    untracked=C.git('ls-files','--others','--exclude-standard').decode().splitlines();assert all(p.startswith(prefix) for p in untracked)
    read=json.loads((C.HERE/'READ_REFERENCES_SHA256.json').read_text());assert all(C.file_sha(C.REPO/p)==h for p,h in read.items())
    original='/workspace/market-pattern-discovery';data='/workspace/market-pattern-data'
    assert C.git('rev-parse','HEAD',root=original).decode().strip()==start['original_checkout_HEAD']
    assert C.git('status','--porcelain',root=original).decode()==start['original_checkout_status']
    assert C.git('rev-parse','HEAD',root=data).decode().strip()==C.DATA_SHA and not C.git('status','--porcelain',root=data).strip()
    spec=json.loads((C.HERE/'SPEC.json').read_text())
    from pathlib import Path
    assert all(C.file_sha(Path(data)/s['path'])==s['full_sha256'] for s in spec['sources'])
    finalmain=json.loads(subprocess.check_output(['gh','api','repos/alkospacer123/market-pattern-discovery/commits/main']))
    pr507=json.loads(subprocess.check_output(['gh','pr','view','507','--json','state,mergeCommit,mergedAt,url']))
    C.write_json(C.HERE/'FINAL_MAIN_CHECK.json',{'initial_main':C.BASE,'final_main':finalmain['sha'],'unchanged':finalmain['sha']==C.BASE,'PR507':pr507,'NO_MERGE':True,'NO_AUTO_MERGE':True})
    assert finalmain['sha']==C.BASE and pr507['state']=='MERGED'
    result={'status':'PASS','base_main':C.BASE,'changed_tracked_files':len(changed),'untracked_files':len(untracked),'diff_additions_only':True,'all_changes_under':prefix,'read_references_unchanged':True,'original_checkout_unchanged':True,'source_data_HEAD':C.DATA_SHA,'source_data_clean_unchanged':True,'source_hashes_unchanged':True,'TradingSystemLab_robot_ROADMAP_prior_research_unchanged':True}
    C.write_json(C.HERE/'SCOPE_CHECK.json',result)
    for folder,file in [('audit','AUDIT_RESULT.json'),('audit','PRESENTATION_AUDIT.json'),('','REPEATABILITY.json')]:assert json.loads((C.HERE/folder/file).read_text())['status']=='PASS'
    freeze=json.loads((C.HERE/'FREEZE.json').read_text());assert all(C.file_sha(C.HERE/n)==h for n,h in freeze['code_spec_sha256'].items())
    C.write_json(C.HERE/'ARTIFACT_SHA256.json',{str(p.relative_to(C.HERE)):C.file_sha(p) for p in sorted(C.HERE.rglob('*')) if p.is_file() and p.name!='ARTIFACT_SHA256.json'})
    print(json.dumps(result),flush=True)
if __name__=='__main__':run()
