"""Final read-only main, frozen hashes, protected scope and deterministic artifact inventory."""
import json
from pathlib import Path
import common as C
PREFIX='IntradayLab/t3_m15_a6_s1_trail_plateau_v2/'

def run():
    actual=C.git('ls-remote','origin','refs/heads/main').decode().split()[0]
    assert actual==C.BASE,('MAIN_CHANGED_REVIEW_REQUIRED',actual)
    frozen=json.loads((C.HERE/'FREEZE.json').read_text())
    for path,sha in frozen['code_spec_sha256'].items():
        assert C.file_sha(C.HERE/path)==sha and C.sha(C.historical(PREFIX+path,frozen['commit']))==sha,('FROZEN_CHANGED',path)
    refs=json.loads((C.HERE/'PROTECTED_SHA256.json').read_text())
    for path,sha in refs.items():assert C.file_sha(C.REPO/path)==sha,('PROTECTED_CHANGED',path)
    paths=C.git('diff','--name-only',C.BASE).decode().splitlines()+C.git('ls-files','--others','--exclude-standard').decode().splitlines()
    assert all(p.startswith(PREFIX) for p in paths),('OUT_OF_SCOPE',paths)
    assert not C.git('ls-tree','-r','--name-only',C.BASE,'--',PREFIX).strip()
    data=Path('/workspace/market-pattern-data');original=Path('/workspace/market-pattern-discovery')
    assert C.git('rev-parse','HEAD',root=data).decode().strip()==C.DATA_SHA and not C.git('status','--porcelain',root=data).strip()
    assert C.git('rev-parse','HEAD',root=original).decode().strip()=='8c40950726446ebccb1ad80b8f129558470d9c11' and not C.git('status','--porcelain',root=original).strip()
    assert C.git('rev-parse',C.BASE+':TradingSystemLab').strip()==C.git('rev-parse','HEAD:TradingSystemLab').strip()
    for p in ('results/control/CONTROL_GATE.json','results/control_scalar/CONTROL_GATE.json','results/FEATURE_CONTROL.json','audit/AUDIT_RESULT.json','audit/PRESENTATION_AUDIT.json','REPEATABILITY.json'):
        assert json.loads((C.HERE/p).read_text())['status']=='PASS',p
    C.write_json(C.HERE/'FINAL_MAIN_CHECK.json',{'base_main':C.BASE,'observed_main':actual,'identical':True,'protected_files_verified':len(refs),'frozen_code_spec_verified':len(frozen['code_spec_sha256']),'data_pin_clean':True,'original_checkout_clean_untouched':True,'TradingSystemLab_git_tree_unchanged':True})
    C.write_json(C.HERE/'SCOPE_CHECK.json',{'status':'PASS','allowed_prefix':PREFIX,'all_changed_paths':sorted(set(paths)),'all_additions_in_new_directory':True,'protected_reference_sha256_unchanged':True,'NO_MERGE':True,'NO_AUTO_MERGE':True})
    C.write_json(C.HERE/'ARTIFACT_SHA256.json',{str(p.relative_to(C.HERE)):C.file_sha(p) for p in sorted(C.HERE.rglob('*')) if p.is_file() and '__pycache__' not in str(p) and p.name not in ('ARTIFACT_SHA256.json','FINAL_DIFF_CHECK.json')})
    print(json.dumps({'scope':'PASS','main':actual,'protected_files':len(refs),'frozen_code_spec':len(frozen['code_spec_sha256'])}))

if __name__=='__main__':run()
