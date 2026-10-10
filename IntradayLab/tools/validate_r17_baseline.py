#!/usr/bin/env python3
"""All IntradayLab tests, two deterministic R17 repeats, frozen ORB regression."""
import argparse
import hashlib
import json
from pathlib import Path
import subprocess
import sys
import unittest

ROOT=Path(__file__).resolve().parents[2]
LAB=ROOT/'IntradayLab'
sys.path.insert(0,str(ROOT))
from IntradayLab.tools.run_r17_baseline import run, OUT, FREEZE
from IntradayLab.tools.audit_r17_baseline import audit
from IntradayLab.core.reports import dump


def hashes(folder,excluded=()):
    return {str(p.relative_to(folder)):hashlib.sha256(p.read_bytes()).hexdigest()
            for p in sorted(folder.rglob('*')) if p.is_file() and p.name not in excluded}


def protected_manifest(base):
    all_paths=subprocess.check_output(['git','-C',str(ROOT),'ls-tree','-r','--name-only',base],text=True).splitlines()
    changed=subprocess.check_output(['git','-C',str(ROOT),'diff','--name-only',base],text=True).splitlines()
    allowed={'IntradayLab/core/backtester.py','IntradayLab/core/metrics.py'}
    forbidden=[p for p in changed if p in all_paths and p not in allowed]
    if forbidden:
        raise AssertionError('FROZEN_FILE_CHANGED '+str(forbidden))
    if any(not p.startswith('IntradayLab/') for p in changed):
        raise AssertionError('OUTSIDE_INTRADAYLAB')
    checks={}
    for path in all_paths:
        if path.startswith('IntradayLab/') and path not in allowed:
            original=subprocess.check_output(['git','-C',str(ROOT),'show',base+':'+path])
            if not (ROOT/path).is_file() or (ROOT/path).read_bytes()!=original:
                raise AssertionError('PROTECTED_BYTES '+path)
            checks[path]=hashlib.sha256(original).hexdigest()
    require_no_other_changes=subprocess.check_output(['git','-C',str(ROOT),'diff',base,'--','.',':(exclude)IntradayLab'],text=True)
    if require_no_other_changes:
        raise AssertionError('PROTECTED_ROOT_DIFF')
    return dict(status='PASS',all_existing_IntradayLab_files_except_two_core_extensions_byte_unchanged=True,
                checked_existing_files=len(checks),canonical_artifact_sha256={p:d for p,d in checks.items() if p.startswith('IntradayLab/results/orb_a_base_2023_canonical_v1/')},
                TradingSystemLab_diff_empty=True,outside_IntradayLab_diff_empty=True)


def validate(root,output):
    if output.resolve()!=OUT.resolve():
        raise ValueError('VALIDATION_OUTPUT_MUST_BE_R17_RESULT_DIRECTORY')
    cfg=json.loads((LAB/'config/r17_orb_breakout_retest_2023_m5_v1.json').read_text())
    suite=unittest.defaultTestLoader.discover(str(LAB/'tests'))
    def flatten(items):
        result=[]
        for item in items:
            result.extend([item] if isinstance(item,unittest.TestCase) else flatten(item))
        return result
    names=sorted(t.id() for t in flatten(suite))
    with (output/'test_execution.log').open('w') as stream:
        result=unittest.TextTestRunner(stream=stream,verbosity=2).run(suite)
    if not result.wasSuccessful():
        raise AssertionError('TECHNICAL_TESTS_FAIL; see test_execution.log')
    expected=hashes(output,('validation.json','artifact_hashes.json','test_execution.log','changed_files.txt'))
    repeats=[]
    for suffix in ('r17_repeat_one','r17_repeat_two'):
        target=LAB/'work'/suffix
        run(root,target);audit(root,target)
        actual=hashes(target)
        if expected!=actual:
            raise AssertionError('R17_NONDETERMINISTIC '+suffix+' '+str(sorted(k for k in expected if expected.get(k)!=actual.get(k))))
        repeats.append(dict(run=suffix,files=len(actual),all_bytes_identical=True))
    from IntradayLab.tools.run_canonical_baseline import run as canonical_run, OUT as CANONICAL
    from IntradayLab.tools.audit_canonical_baseline import audit as canonical_audit
    replay=LAB/'work/r17_orb_regression'
    canonical_run(root,replay);canonical_audit(root,replay)
    excluded=('validation.json','artifact_hashes.json','changed_files.txt','provenance.json')
    expected_orb=hashes(CANONICAL,excluded);actual_orb=hashes(replay,excluded)
    if expected_orb!=actual_orb:
        raise AssertionError('ORB_RESULT_BYTES_CHANGED '+str(sorted(k for k in expected_orb if expected_orb.get(k)!=actual_orb.get(k))))
    original_provenance=json.loads((CANONICAL/'provenance.json').read_text())
    new_provenance=json.loads((replay/'provenance.json').read_text())
    # A replay must honestly identify changed code, while committed artifacts
    # remain entirely byte-identical. Every other provenance field is equal.
    original_provenance.pop('code_sha256');new_provenance.pop('code_sha256')
    if original_provenance!=new_provenance:
        raise AssertionError('ORB_NON_CODE_PROVENANCE_CHANGED')
    protected=protected_manifest(cfg['base_main'])
    if subprocess.check_output(['git','-C',str(root),'status','--porcelain=v1','--untracked-files=all'],text=True).strip():
        raise AssertionError('DATA_SOURCE_CHANGED')
    status=json.loads((output/'metrics.json').read_text())['baseline_status']
    validation=dict(status='PASS',tests_run=result.testsRun,failures=len(result.failures),errors=len(result.errors),
        skipped=len(result.skipped),test_ids=names,R17_tests=sum('test_r17_' in n for n in names),
        replay_repeats=repeats,deterministic_artifact_sha256=expected,
        canonical_ORB_regression=dict(status='PASS',byte_identical_result_files=len(expected_orb),result_sha256=expected_orb,
            stored_canonical_artifacts_all_byte_unchanged=True,
            rerun_provenance_difference='Only code_sha256 differs, necessarily recording two generic core extensions and the newly present strategy module; stored canonical provenance remains untouched.',
            non_code_provenance_identical=True,independent_canonical_audit='PASS'),
        protected_files=protected,market_pattern_data_clean=True,source_ref=cfg['source_ref'],
        config_freeze_commit=FREEZE,config_unchanged_since_before_PnL=True,
        baseline_status=status,optimization_allowed=False)
    dump(output/'validation.json',validation)
    dump(output/'artifact_hashes.json',hashes(output,('artifact_hashes.json','changed_files.txt')))
    return validation


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--data-root',type=Path,required=True)
    p.add_argument('--output',type=Path,default=OUT)
    a=p.parse_args();result=validate(a.data_root,a.output)
    print(json.dumps({'status':result['status'],'tests':result['tests_run'],'R17_tests':result['R17_tests'],
        'repeat_runs':len(result['replay_repeats']),'ORB_byte_identical_result_files':result['canonical_ORB_regression']['byte_identical_result_files']},sort_keys=True))
