#!/usr/bin/env python3
"""Technical acceptance, two complete replays/audits and artifact byte checks."""
import hashlib
import json
from pathlib import Path
import subprocess
import sys
import unittest

ROOT=Path(__file__).resolve().parents[2]
LAB=ROOT/'IntradayLab'
sys.path.insert(0,str(ROOT))
from run_canonical_baseline import run, OUT
from audit_canonical_baseline import audit


def hashes(folder):
    return {p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in sorted(folder.iterdir())
            if p.is_file() and p.name not in ('validation.json','artifact_hashes.json','changed_files.txt')}


def main():
    suite=unittest.defaultTestLoader.discover(str(LAB/'tests'))
    def flatten(suite):
        out=[]
        for item in suite:
            out.extend([item] if isinstance(item,unittest.TestCase) else flatten(item))
        return out
    names=sorted(item.id() for item in flatten(suite))
    result=unittest.TextTestRunner(verbosity=1).run(suite)
    if not result.wasSuccessful():
        raise SystemExit('TECHNICAL_TESTS_FAIL')
    root=Path('/workspace/market-pattern-data')
    run(root,OUT);audit(root,OUT)
    expected=hashes(OUT)
    receipts=[]
    for suffix in ('replay_one','replay_two'):
        target=LAB/'work'/suffix
        run(root,target);audit(root,target)
        actual=hashes(target)
        if actual!=expected:
            raise AssertionError('NONDETERMINISTIC_ARTIFACTS '+suffix)
        receipts.append(dict(run=suffix,files=len(actual),all_bytes_identical=True))
    base=json.loads((OUT/'provenance.json').read_text())['base_main']
    protected=subprocess.check_output(['git','-C',str(ROOT),'diff',base,'--','.',':(exclude)IntradayLab'],text=True)
    if protected:
        raise AssertionError('PROTECTED_DIFF')
    status=subprocess.check_output(['git','-C',str(root),'status','--porcelain=v1','--untracked-files=all'],text=True)
    if status:
        raise AssertionError('SOURCE_CHANGED')
    validation=dict(status='PASS',tests_run=result.testsRun,failures=len(result.failures),
        errors=len(result.errors),skipped=len(result.skipped),test_ids=names,
        synthetic_tests=sum('universal_backtester' in n for n in names),
        audit_guard_tests=sum('canonical_audit' in n for n in names),
        replay_repeats=receipts,deterministic_artifact_sha256=expected,
        protected_diff_outside_IntradayLab_empty=True,market_pattern_data_clean=True,
        source_ref='f8486b446cf3d5f9f3cba6dfec32bdef8fd184c8',
        historical_reference='9c65d03aae117c6d88bbb4e6186f6a4fbb6b73ec',
        baseline_status='INCONCLUSIVE',optimization_allowed=False)
    (OUT/'validation.json').write_text(json.dumps(validation,indent=2,sort_keys=True)+'\n')
    final={p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in sorted(OUT.iterdir())
           if p.is_file() and p.name!='artifact_hashes.json'}
    (OUT/'artifact_hashes.json').write_text(json.dumps(final,indent=2,sort_keys=True)+'\n')
    print(json.dumps({'status':'PASS','tests':result.testsRun,'identical_artifacts':len(expected),
                      'repeat_runs':2},sort_keys=True))


if __name__=='__main__':
    main()
