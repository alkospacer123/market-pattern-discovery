#!/usr/bin/env python3
"""All tests, two deterministic Level Rejection repeats, frozen ORB/R17/R16 regressions."""
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
from IntradayLab.tools.run_level_rejection_baseline import run, OUT, FREEZE
from IntradayLab.tools.audit_level_rejection_baseline import audit
from IntradayLab.core.reports import dump


def hashes(folder,excluded=()):
    return {str(p.relative_to(folder)):hashlib.sha256(p.read_bytes()).hexdigest()
            for p in sorted(folder.rglob('*')) if p.is_file() and p.name not in excluded}


def protected_manifest(base):
    all_paths=subprocess.check_output(['git','-C',str(ROOT),'ls-tree','-r','--name-only',base],text=True).splitlines()
    changed=subprocess.check_output(['git','-C',str(ROOT),'diff','--name-only',base],text=True).splitlines()
    allowed={'IntradayLab/core/backtester.py','IntradayLab/core/execution.py'}
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
    return dict(status='PASS',all_existing_IntradayLab_files_except_two_opt_in_core_extensions_byte_unchanged=True,
                allowed_existing_changes=sorted(allowed),
                checked_existing_files=len(checks),canonical_artifact_sha256={p:d for p,d in checks.items() if p.startswith('IntradayLab/results/orb_a_base_2023_canonical_v1/')},
                R17_artifact_sha256={p:d for p,d in checks.items() if p.startswith('IntradayLab/results/r17_orb_breakout_retest_2023_m5_v1/')},
                R16_artifact_sha256={p:d for p,d in checks.items() if p.startswith('IntradayLab/results/r16_compression_breakout_2023_m5_v1/')},
                common_core_default_behavior_byte_regressions='ORB/R17/R16 PASS',TradingSystemLab_diff_empty=True,outside_IntradayLab_diff_empty=True)


def validate(root,output):
    if output.resolve()!=OUT.resolve():
        raise ValueError('VALIDATION_OUTPUT_MUST_BE_LEVEL_REJECTION_RESULT_DIRECTORY')
    cfg=json.loads((LAB/'config/level_rejection_2023_m5_v1.json').read_text())
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
    for suffix in ('level_rejection_repeat_one','level_rejection_repeat_two'):
        target=LAB/'work'/suffix
        run(root,target);audit(root,target)
        actual=hashes(target)
        if expected!=actual:
            raise AssertionError('LEVEL_REJECTION_NONDETERMINISTIC '+suffix+' '+str(sorted(k for k in expected if expected.get(k)!=actual.get(k))))
        repeats.append(dict(run=suffix,files=len(actual),all_bytes_identical=True))
    regressions={}
    for name in ('canonical','r17','r16'):
        if name=='canonical':
            from IntradayLab.tools.run_canonical_baseline import run as old_run, OUT as old_out
            from IntradayLab.tools.audit_canonical_baseline import audit as old_audit
        elif name=='r17':
            from IntradayLab.tools.run_r17_baseline import run as old_run, OUT as old_out
            from IntradayLab.tools.audit_r17_baseline import audit as old_audit
        else:
            from IntradayLab.tools.run_r16_baseline import run as old_run, OUT as old_out
            from IntradayLab.tools.audit_r16_baseline import audit as old_audit
        replay=LAB/'work'/('level_rejection_'+name+'_regression')
        old_run(root,replay);old_audit(root,replay)
        excluded=('validation.json','artifact_hashes.json','changed_files.txt','test_execution.log','provenance.json')
        expected_old=hashes(old_out,excluded);actual_old=hashes(replay,excluded)
        if expected_old!=actual_old:
            raise AssertionError(name+'_RESULT_BYTES_CHANGED '+str(sorted(k for k in set(expected_old)|set(actual_old) if expected_old.get(k)!=actual_old.get(k))))
        original_provenance=json.loads((old_out/'provenance.json').read_text())
        new_provenance=json.loads((replay/'provenance.json').read_text())
        original_code=original_provenance.pop('code_sha256');new_code=new_provenance.pop('code_sha256')
        code_changes={path:dict(stored=original_code.get(path),replayed=new_code.get(path))
            for path in sorted(set(original_code)|set(new_code)) if original_code.get(path)!=new_code.get(path)}
        for path,change in code_changes.items():
            if path in cfg['execution_code_sha256']:
                if change['replayed'] != cfg['execution_code_sha256'][path]:
                    raise AssertionError(name+'_FROZEN_EXECUTION_HASH '+path)
                change['explanation']=('Current optional common execution extension' if '/core/' in path
                    else 'New frozen strategy included by legacy runner strategy-directory hash enumeration')
            else:
                # Earlier baselines predate already merged R17/R16 strategies and
                # shared metric helpers. Their legacy runners enumerate current
                # code files; require those bytes to match our untouched base main.
                original_base=subprocess.check_output(['git','-C',str(ROOT),'show',cfg['base_main']+':'+path])
                if change['replayed'] != hashlib.sha256(original_base).hexdigest():
                    raise AssertionError(name+'_BASE_MAIN_CODE_CHANGED '+path)
                change['explanation']='Already merged base-main code; unchanged by this PR'
        if original_provenance!=new_provenance:
            raise AssertionError(name+'_NON_CODE_PROVENANCE_CHANGED')
        regressions[name]=dict(status='PASS',byte_identical_result_files=len(expected_old),
            result_sha256=expected_old,stored_artifacts_all_byte_unchanged=True,
            non_code_provenance_identical=True,changed_code_hashes_in_separate_replay_provenance=code_changes,
            independent_audit='PASS')
    protected=protected_manifest(cfg['base_main'])
    if subprocess.check_output(['git','-C',str(root),'status','--porcelain=v1','--untracked-files=all'],text=True).strip():
        raise AssertionError('DATA_SOURCE_CHANGED')
    status=json.loads((output/'metrics.json').read_text())['baseline_status']
    validation=dict(status='PASS',tests_run=result.testsRun,failures=len(result.failures),errors=len(result.errors),
        skipped=len(result.skipped),test_ids=names,Level_Rejection_tests=sum('test_level_rejection' in n or 'test_net_c1_execution' in n for n in names),
        replay_repeats=repeats,deterministic_artifact_sha256=expected,
        canonical_ORB_regression=regressions['canonical'],R17_regression=regressions['r17'],R16_regression=regressions['r16'],
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
    print(json.dumps({'status':result['status'],'tests':result['tests_run'],'Level_Rejection_tests':result['Level_Rejection_tests'],
        'repeat_runs':len(result['replay_repeats']),'ORB_byte_identical_result_files':result['canonical_ORB_regression']['byte_identical_result_files'],
        'R17_byte_identical_result_files':result['R17_regression']['byte_identical_result_files'],
        'R16_byte_identical_result_files':result['R16_regression']['byte_identical_result_files']},sort_keys=True))
