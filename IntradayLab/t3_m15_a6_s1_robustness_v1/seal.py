"""Protected-tree, source, original-checkout and addition-only scope evidence."""
import json
from pathlib import Path
import common as C,integrity as F

def seal():
    frozen=F.freeze_guard();prefix=C.HERE.relative_to(C.REPO).as_posix()+'/'
    protected=json.loads((C.HERE/'PROTECTED_SHA256.json').read_text())
    for name,digest in protected.items():assert C.file_sha(C.REPO/name)==digest,('PROTECTED_FILE_CHANGED',name)
    names=C.git('diff','--name-status',C.BASE,'--').decode().splitlines()
    for line in names:
        status,name=line.split('\t');assert status=='A' and name.startswith(prefix),('SCOPE_VIOLATION',line)
    staged=C.git('diff','--cached','--name-status').decode().splitlines()
    for line in staged:
        status,name=line.split('\t');assert status=='A' and name.startswith(prefix),('STAGED_SCOPE_VIOLATION',line)
    original=Path('/workspace/market-pattern-discovery');data=Path('/workspace/market-pattern-data')
    start=json.loads((C.HERE/'START_GATE.json').read_text())
    assert C.git('rev-parse','HEAD',root=original).decode().strip()==start['original_checkout_head']
    assert C.git('status','--porcelain',root=original).decode()==start['original_checkout_status']
    assert C.git('rev-parse','HEAD',root=data).decode().strip()==C.DATA_SHA
    assert not C.git('status','--porcelain',root=data).strip()
    for source in json.loads((C.HERE/'SPEC.json').read_text())['sources']:assert C.file_sha(data/source['path'])==source['full_sha256']
    remote=C.git('ls-remote','origin','refs/heads/main').decode().split()[0]
    C.write_json(C.HERE/'FINAL_MAIN_CHECK.json',{'actual_main':remote,'analysis_base_main':C.BASE,'unchanged_since_start':remote==C.BASE,
        'PR508_confirmed_merged_before_start':True,'NO_MERGE':True,'NO_AUTO_MERGE':True})
    C.write_json(C.HERE/'SCOPE_CHECK.json',{'status':'PASS','protected_files':len(protected),'protected_sha256_unchanged':True,
        'TradingSystemLab_git_tree_unchanged':not C.git('diff',C.BASE,'--','TradingSystemLab').strip(),
        'ROADMAP_and_previous_IntradayLab_unchanged':True,'data_pin_and_bytes_unchanged':True,'original_checkout_unchanged':True,
        'changes_only_additions_in':prefix,'freeze_commit':frozen['commit'],'main_at_final_check':remote})
    files={p.relative_to(C.HERE).as_posix():C.file_sha(p) for p in sorted(C.HERE.rglob('*')) if p.is_file()
           and 'work' not in p.relative_to(C.HERE).parts and '__pycache__' not in p.relative_to(C.HERE).parts and p.name!='ARTIFACT_SHA256.json'}
    C.write_json(C.HERE/'ARTIFACT_SHA256.json',files)
    print(json.dumps({'scope':'PASS','protected_files':len(protected),'inventory_entries':len(files),'main':remote}))

if __name__=='__main__':seal()
