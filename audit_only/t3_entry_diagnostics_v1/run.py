"""Fresh frozen-source CONTROL + development diagnostics + separate verification."""
import argparse,importlib.util,io,json,shutil,subprocess,sys,unittest
from pathlib import Path
from support import *

def run(out):
    assert not out.exists() or not any(out.iterdir()),'OUTPUT_MUST_BE_FRESH'
    if (HERE/'CODE_FREEZE.json').exists():
        freeze=json.loads((HERE/'CODE_FREEZE.json').read_text())
        for name,d in freeze['files'].items():assert sha(HERE/name)==d,('CODE_FREEZE_CHANGED',name)
    scratch=HERE/'work/runs'/out.name
    assert not scratch.exists(),'SCRATCH_MUST_BE_FRESH'
    scratch.mkdir(parents=True)
    control=scratch/'control'
    subprocess.run([sys.executable,str(HERE/'control.py'),'--output',str(control)],check=True)
    print('Isolated full CONTROL PASS',flush=True)
    from development import run as develop
    streams,results,entries,outcomes=develop(out,control/'CONTROL_RECONCILIATION.json')
    for name in ('SOURCE_MANIFEST.json','CONTROL_RECONCILIATION.json','CONTROL_RECONCILIATION.csv'):
        shutil.copyfile(control/name,out/name)
    from causality import audit
    from features import features_for_frame
    causal=audit(streams,entries,frozen());js(out/'CAUSALITY.json',causal)
    print('Prefix/future perturbation PASS',flush=True)
    # Explicit local module path: archived research also has a verify module.
    spec=importlib.util.spec_from_file_location('entry_independent_verification',HERE/'verify.py')
    verifier=importlib.util.module_from_spec(spec);spec.loader.exec_module(verifier)
    independent=verifier.verify(out)
    from verify_tables import check_tables
    table_audit=check_tables(out)
    print('Independent algorithm feature/path/calendar audit PASS',flush=True)
    spec=importlib.util.spec_from_file_location('entry_contract_tests',HERE/'test_contract.py')
    test=importlib.util.module_from_spec(spec);spec.loader.exec_module(test)
    buffer=io.StringIO();tests=unittest.TextTestRunner(stream=buffer).run(unittest.defaultTestLoader.loadTestsFromTestCase(test.Contract))
    assert tests.wasSuccessful(),buffer.getvalue()
    js(out/'SYNTHETIC_TESTS.json',dict(status='PASS',tests=tests.testsRun,cases=sorted(x for x in dir(test.Contract) if x.startswith('test_'))))
    from report import render
    render(out)
    audit_receipt=dict(status='PASS_DIAGNOSTICS_ONLY',CONTROL=json.loads((out/'CONTROL_RECONCILIATION.json').read_text()),
      independent_algorithm=independent,independent_table_arithmetic=table_audit,causality=dict(status=causal['status'],cases=len(causal['checks']),fields=causal['fields_compared']),
      synthetic_tests=tests.testsRun,protocol_commit=PROTOCOL,protocol_sha256=sha(HERE/'PROTOCOL_RU.md'),
      hypothesis_sha256=sha(HERE/'HYPOTHESES.md') if (HERE/'HYPOTHESES.md').exists() else None,
      code_sha256={p.name:sha(p) for p in sorted(HERE.glob('*.py'))},
      discovery_years=[2023,2024],locked_period_use='Isolated mandatory CONTROL only; no OOS feature analysis',
      parameter_search=False,new_filter_backtest=False,live_or_production_executed=False,source_OHLC_copied=False,
      costs='Gross R diagnostics; frozen normalized H1 C1 untouched; no executable net or cash improvement claim',
      independent_human_review='PENDING; verifier is a separate implementation by same author',
      deployment='DRAFT_ONLY_NO_MERGE_NO_AUTO_MERGE')
    js(out/'AUDIT.json',audit_receipt)
    print('FINISHED',out,flush=True)

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--output',type=Path,required=True);a=p.parse_args();run(a.output.resolve())
