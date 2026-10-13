"""Read-only base/main/data/protected-tree verification and final artifact inventory."""
import json
from pathlib import Path
import common as C

PREFIX='IntradayLab/t3_m15_a6_s1_entry_quality_v1/'


def run():
    actual=C.git('ls-remote','origin','refs/heads/main').decode().split()[0]
    assert actual==C.BASE,('ACTUAL_MAIN_CHANGED_REVIEW_REQUIRED',actual)
    freeze=json.loads((C.HERE/'FREEZE.json').read_text())
    for name,digest in freeze['code_spec_sha256'].items():
        assert C.file_sha(C.HERE/name)==digest and C.sha(C.historical(PREFIX+name,freeze['commit']))==digest,('FROZEN_CHANGED',name)
    protected=json.loads((C.HERE/'PROTECTED_SHA256.json').read_text())
    for name,digest in protected.items():assert C.file_sha(C.REPO/name)==digest,('PROTECTED_CHANGED',name)
    data=Path('/workspace/market-pattern-data');original=Path('/workspace/market-pattern-discovery')
    assert C.git('rev-parse','HEAD',root=data).decode().strip()==C.DATA_SHA and not C.git('status','--porcelain',root=data).strip()
    assert C.git('rev-parse','HEAD',root=original).decode().strip()=='0546e10d9977687a77638d76847b205c99223e16' and not C.git('status','--porcelain',root=original).strip()
    assert C.git('rev-parse',C.BASE+':TradingSystemLab').strip()==C.git('rev-parse','HEAD:TradingSystemLab').strip()
    assert not C.git('ls-tree','-r','--name-only',C.BASE,'--',PREFIX).strip(),'DIRECTORY_PREEXISTED'
    for p in ('results/control/CONTROL_GATE.json','results/control/PR506_GATE.json','results/control_scalar/CONTROL_GATE.json','results/control_scalar/PR506_GATE.json','results/FEATURE_CONTROL.json','audit/AUDIT_RESULT.json','audit/PRESENTATION_AUDIT.json','audit/CONCLUSION_REVIEW.json','REPEATABILITY.json'):
        assert json.loads((C.HERE/p).read_text())['status']=='PASS',p
    for folder,manifest in [('results','FIRST_COMPUTATION_SHA256.json'),('audit','FIRST_AUDIT_SHA256.json')]:
        for path,digest in json.loads((C.HERE/manifest).read_text()).items():assert C.file_sha(C.HERE/folder/path)==digest,('FIRST_OUTPUT_CHANGED',path)
    full=json.loads((C.HERE/'FIRST_FULL_PIPELINE_SHA256.json').read_text())
    for folder,files in full.items():
        actual_files={str(p.relative_to(C.HERE/folder)):C.file_sha(p) for p in sorted((C.HERE/folder).rglob('*')) if p.is_file()}
        assert actual_files==files,('POST_REPEAT_OUTPUT_CHANGED',folder)
    C.write_json(C.HERE/'FINAL_MAIN_CHECK.json',{'status':'PASS','base_main':C.BASE,'observed_main':actual,'PR505_merged':True,'PR506_merged':True,'PR506_merge_commit':C.BASE,'protected_file_sha256_verified':len(protected),'frozen_files_verified':len(freeze['code_spec_sha256']),'data_pin_clean_read_only':True,'original_checkout_clean_untouched':True,'TradingSystemLab_tree_unchanged':True})
    C.write_json(C.HERE/'SCOPE_CHECK.json',{})
    C.write_json(C.HERE/'ARTIFACT_SHA256.json',{})
    changed=C.git('diff','--name-status',C.BASE).decode().splitlines()
    assert all(line.startswith('A\t'+PREFIX) for line in changed),('NON_ADDITION_OR_OUT_OF_SCOPE',changed)
    untracked=C.git('ls-files','--others','--exclude-standard').decode().splitlines()
    assert all(p.startswith(PREFIX) for p in untracked),('OUT_OF_SCOPE_UNTRACKED',untracked)
    paths=sorted(set(line.split('\t')[1] for line in changed)|set(untracked))
    C.write_json(C.HERE/'SCOPE_CHECK.json',{'status':'PASS','allowed_prefix':PREFIX,'changed_paths':paths,'all_additions_in_previously_absent_directory':True,'protected_original_files_unchanged':True,'TradingSystemLab_robot_roadmap_data_previous_studies_unchanged':True,'new_strategies':0,'filter_replays':0,'NO_MERGE':True,'NO_AUTO_MERGE':True,'STOP_AFTER_DRAFT_PR':True})
    artifacts={str(p.relative_to(C.HERE)):C.file_sha(p) for p in sorted(C.HERE.rglob('*')) if p.is_file() and '__pycache__' not in str(p) and p.name!='ARTIFACT_SHA256.json'}
    C.write_json(C.HERE/'ARTIFACT_SHA256.json',artifacts)
    print(json.dumps({'status':'PASS','main':actual,'changed_paths':len(paths),'artifact_hashes':len(artifacts),'protected_files':len(protected),'frozen_files':len(freeze['code_spec_sha256'])}))

if __name__=='__main__':run()
