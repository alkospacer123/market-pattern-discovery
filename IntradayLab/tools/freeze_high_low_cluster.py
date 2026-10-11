#!/usr/bin/env python3
"""Prepare all three fixed configs; finalize hashes only before their first commit."""
import argparse
import hashlib
import json
import re
from pathlib import Path
import subprocess
import sys
ROOT=Path(__file__).resolve().parents[2];sys.path.insert(0,str(ROOT))
from IntradayLab.strategies.high_low_cluster_m5 import parameters,ROUND_STEPS
from IntradayLab.tools.high_low_cluster_contract import LAB,BASE,config_path


def digest(path):return hashlib.sha256(path.read_bytes()).hexdigest()
def write(path,obj):path.write_text(json.dumps(obj,indent=2,sort_keys=True,ensure_ascii=False)+'\n')


def prepare(final=False):
    if any(subprocess.check_output(['git','-C',str(ROOT),'ls-files','--',str(config_path(n).relative_to(ROOT))],text=True).strip() for n in (4,7,10)):
        raise ValueError('ALREADY_TRACKED_FREEZE_CANNOT_BE_REGENERATED')
    old=json.loads((LAB/'config/equal_high_low_m5_2023_a_v1.json').read_text())
    manifest=LAB/'config/high_low_cluster_b4_b7_b10_scope_manifest.json'
    files=subprocess.check_output(['git','-C',str(ROOT),'ls-tree','-r',BASE],text=True).splitlines()
    inside={};outside={}
    for line in files:
        meta,path=line.split('\t');blob=meta.split()[2]
        if path.startswith('IntradayLab/'):inside[path]=digest(ROOT/path)
        else:outside[path]=blob
    write(manifest,dict(base_main=BASE,allowed_existing_changes=[],existing_intraday_sha256=inside,protected_git_blobs=outside))
    deps=[*sorted((LAB/'core').glob('*.py')),LAB/'core/README.md',
        LAB/'strategies/high_low_cluster_m5.py',*sorted((LAB/'tools').glob('*high_low_cluster*.py')),
        LAB/'tools/equal_high_low_contract.py',LAB/'tools/run_equal_high_low_baseline.py',
        LAB/'tools/audit_equal_high_low_baseline.py',LAB/'tools/audit_canonical_baseline.py',
        LAB/'tools/verify_equal_high_low_baseline.py',LAB/'tools/validate_equal_high_low_baseline.py',
        LAB/'tests/test_high_low_cluster_m5.py',LAB/'reports/HIGH_LOW_CLUSTER_B4_B7_B10_PREREGISTRATION.md',manifest]
    if final:
        deps += [LAB/'config/high_low_cluster_b4_b7_b10_pre_pnl_validation.json',LAB/'config/high_low_cluster_b4_b7_b10_pre_pnl_tests.log']
        receipt=json.loads(deps[-2].read_text())
        if receipt['status']!='PASS':raise ValueError('PRE_PNL_VALIDATION_REQUIRED')
        log=deps[-1].read_text();match=re.search(r'Ran (\d+) tests in ',log)
        if not match or not log.rstrip().endswith('OK'):raise ValueError('FULL_TEST_PASS_REQUIRED')
        receipt['unittest_count']=int(match.group(1));receipt['unittest_status']='PASS';write(deps[-2],receipt)
    for n in (4,7,10):
        cfg={k:old[k] for k in ('schema','bar_label','calendar','classification_policy','end_exclusive','execution','inputs','instruments','research_phase','source_ref','source_repository','start','tick_schedule','timeframe_minutes','timezone')}
        cfg.update(id=f'high_low_cluster_m5_2023_b{n}_v1',strategy='HIGH_LOW_CLUSTER_M5',base_main=BASE,
            parameters=parameters(n),scope_manifest=str(manifest.relative_to(ROOT)),
            preregistration='IntradayLab/reports/HIGH_LOW_CLUSTER_B4_B7_B10_PREREGISTRATION.md',
            round_steps=ROUND_STEPS,round_near_ticks=1,pre_pnl_unittest_count=receipt['unittest_count'] if final else None,
            contract='Greedy causal envelope <=3 ticks; first formed nonzero N-bar slice consumed even if Close/admission fails; both ambiguous signals rejected. Common episode ID across models; no independent-sample claim. NEXT_OPEN only. No tuning or next stage.',
            execution_code_sha256={str(p.relative_to(ROOT)):digest(p) for p in deps if p.exists()})
        write(config_path(n),cfg)
        config_path(n).with_suffix('.sha256').write_text(digest(config_path(n))+'  '+config_path(n).name+'\n')


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--finalize',action='store_true');prepare(p.parse_args().finalize)
