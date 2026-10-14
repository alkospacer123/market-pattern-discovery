"""Final read-only main/source/scope checks and artifact inventory."""
import json,subprocess
from pathlib import Path
import common as C
PREFIX='IntradayLab/t3_m15_a6_s1_trail_optimization_v1/'

def run():
    actual=C.git('ls-remote','origin','refs/heads/main').decode().split()[0]
    if actual!=C.BASE:raise AssertionError(('MAIN_CHANGED_REVIEW_FULL_DIFF',actual))
    refs=json.loads((C.HERE/'READ_REFERENCES_SHA256.json').read_text())
    for path,sha in refs.items():assert C.file_sha(C.REPO/path)==sha,('PROTECTED_REFERENCE_CHANGED',path)
    paths=C.git('diff','--name-only',C.BASE).decode().splitlines()+C.git('ls-files','--others','--exclude-standard').decode().splitlines()
    assert all(p.startswith(PREFIX) for p in paths),('OUT_OF_SCOPE',paths)
    assert C.git('rev-parse','HEAD',root=Path('/workspace/market-pattern-data')).decode().strip()==C.DATA_SHA
    assert not C.git('status','--porcelain',root=Path('/workspace/market-pattern-data')).strip()
    assert C.git('rev-parse','HEAD',root=Path('/workspace/market-pattern-discovery')).decode().strip()=='8c40950726446ebccb1ad80b8f129558470d9c11'
    assert not C.git('status','--porcelain',root=Path('/workspace/market-pattern-discovery')).strip(),'ORIGINAL_CHECKOUT_CHANGED'
    C.write_json(C.HERE/'FINAL_MAIN_CHECK.json',{'base_main':C.BASE,'observed_main':actual,'identical':True,'protected_reference_files_verified':len(refs),'data_pin_clean':True,'original_checkout_untouched':True,'TradingSystemLab_git_tree_unchanged':C.git('rev-parse',C.BASE+':TradingSystemLab').decode().strip()==C.git('rev-parse','HEAD:TradingSystemLab').decode().strip(),'reviewed_local_to_main_diff_sha256':json.loads((C.HERE/'START_GATE.json').read_text())['local_to_main_diff_sha256']})
    C.write_json(C.HERE/'SCOPE_CHECK.json',{'status':'PASS','allowed_prefix':PREFIX,'all_changed_paths':sorted(set(paths)),'all_changes_are_additions_to_new_directory':not C.git('ls-tree','-r','--name-only',C.BASE,'--',PREFIX).strip(),'protected_reference_sha256_unchanged':True,'original_checkout_untouched':True,'data_pin_read_only_clean':True,'NO_MERGE':True,'NO_AUTO_MERGE':True})
    C.write_json(C.HERE/'ARTIFACT_SHA256.json',{str(p.relative_to(C.HERE)):C.file_sha(p) for p in sorted(C.HERE.rglob('*')) if p.is_file() and '__pycache__' not in str(p) and p.name!='ARTIFACT_SHA256.json'})
    print(json.dumps({'scope':'PASS','main':actual,'protected_files':len(refs)}))

if __name__=='__main__':run()
