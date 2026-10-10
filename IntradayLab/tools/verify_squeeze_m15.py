#!/usr/bin/env python3
"""Scope, frozen files, protected-tree and bounded-prefix verification."""
import json,hashlib,subprocess
from pathlib import Path
from run_squeeze_m15 import read_inputs,CONFIG,encoded,sha
LAB=Path(__file__).resolve().parents[1];ROOT=LAB.parent;OUT=LAB/'results/stage2_squeeze_m15_v1'

def git(*args):return subprocess.check_output(['git','-C',str(ROOT),*args],text=True).strip()
def canonical_sha(obj):return sha(json.dumps(obj,sort_keys=True,separators=(',',':')).encode())

def verify():
    initial=json.loads((OUT/'initial_state.json').read_text());before=initial['tracked_file_sha256']
    permitted={'IntradayLab/ROADMAP.md','IntradayLab/PROJECT_CONTEXT.md'}
    after={p:sha((ROOT/p).read_bytes()) for p in before}
    changed=[p for p in before if before[p]!=after[p]]
    assert set(changed)<=permitted,changed
    protected={p:v for p,v in before.items() if not p.startswith('IntradayLab/')}
    protected_after={p:after[p] for p in protected}
    frozen={p:v for p,v in before.items() if p.startswith('IntradayLab/') and p not in permitted}
    assert protected==protected_after and all(after[p]==v for p,v in frozen.items())
    main=git('rev-parse','origin/main');assert main==initial['base_main']
    root_initial=[line for line in initial['protected_root_git_ids'] if not line.endswith('\tIntradayLab')]
    root_now=[line for line in git('ls-tree','HEAD').splitlines() if not line.endswith('\tIntradayLab')]
    assert root_initial==root_now
    freeze=json.loads((OUT/'pre_returns_freeze.json').read_text())
    assert all(sha((LAB/p).read_bytes())==v for p,v in freeze['files_sha256'].items())
    data,inputs=read_inputs(Path('/workspace/market-pattern-data'),json.loads(CONFIG.read_text()))
    first=json.loads((OUT/'input_provenance.json').read_text())['inputs'];assert first==json.loads(encoded(inputs))
    paths=git('diff','--name-only','origin/main').splitlines()+git('diff','--cached','--name-only').splitlines()
    assert all(p.startswith('IntradayLab/') for p in paths)
    audit=json.loads((OUT/'independent/independent_audit.json').read_text())
    assert audit['status']=='INDEPENDENT_TRADING_LOGIC_PASS' and not audit['discrepancies']
    repro=json.loads((OUT/'reproducibility.json').read_text());assert repro['status']=='PASS' and repro['reporting_replays_identical']
    r=dict(status='PASS',actual_github_main=main,base_main=initial['base_main'],merged_prs={'455':'7643513a7ce718b142454fe094186c3e6bbb4605','456':'23f25d6ea07e778fa4333fcab3564aeddb763a6a'},protected_tracked_files=len(protected),frozen_accepted_lab_files=len(frozen),protected_file_sha256_before=canonical_sha(protected),protected_file_sha256_after=canonical_sha(protected_after),frozen_lab_sha256_before=canonical_sha(frozen),frozen_lab_sha256_after=canonical_sha({p:after[p] for p in frozen}),protected_git_root_ids=root_now,existing_modified_files=changed,allowed_diff_only_intraday=True,source_ref=initial['source_head'],source_initial_final_prefix_sha256={s:dict(initial=first[s]['prefix_sha256'],final=inputs[s]['prefix_sha256'],bytes_2024_plus_read=0,bytes_2025_plus_read=0) for s in inputs},frozen_rule_files_sha256=freeze['files_sha256'],config_and_engine_after_returns='UNCHANGED',full_diff_paths=sorted(set(paths)),independent_checked_fields=audit['checked_fields'],replay_artifacts_identical=True,reporting_only_additions='Preserved first_returns_snapshot + reporting_correction_history',full_annual_metrics='NULL',conclusion='NO ECONOMIC BASELINE PASS: all four researched Squeeze architectures',stage_3_wf_oos_live_merge=False)
    (OUT/'pre_publication_verification.json').write_text(encoded(r))
    print('Protected source/files/trees, actual main, frozen rules and diff: PASS',len(protected),len(frozen))

if __name__=='__main__':verify()
