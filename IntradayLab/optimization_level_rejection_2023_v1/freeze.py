"""Pre-P&L source metadata, immutable file inventory and dependency commitments."""
import hashlib
import json
from pathlib import Path
import subprocess

ROOT=Path(__file__).resolve().parents[2]
STUDY=Path(__file__).resolve().parent


def freeze():
    policy=json.loads((STUDY/'OPTIMIZATION_LEVEL_REJECTION_POLICY.json').read_text())
    def git(*args):return subprocess.check_output(['git','-C',str(ROOT),*args],text=True).strip()
    if git('rev-parse','HEAD')!=policy['base_main']:raise ValueError('FREEZE_MUST_START_AT_VERIFIED_MAIN')
    paths=git('ls-tree','-r','--name-only',policy['base_main']).splitlines()
    protected={p:hashlib.sha256((ROOT/p).read_bytes()).hexdigest() for p in paths}
    (STUDY/'protected_file_sha256.json').write_text(json.dumps(protected,indent=2,sort_keys=True)+'\n')
    dependencies=[*sorted((ROOT/'IntradayLab/core').glob('*.py')),
        ROOT/'IntradayLab/strategies/level_rejection_m5_optimization_v1.py',ROOT/'IntradayLab/strategies/__init__.py',
        *sorted(STUDY.glob('*.py')),STUDY/'OPTIMIZATION_LEVEL_REJECTION_POLICY.json',STUDY/'GRID.csv',STUDY/'EVALUATION_MATRIX.csv',
        STUDY/'audit_tests.log',STUDY/'pre_pnl_tests.log',STUDY/'protected_file_sha256.json',STUDY/'preflight.json',
        STUDY/'synthetic_pipeline_receipt.json',STUDY/'synthetic_pipeline.log',STUDY/'PREREGISTRATION.md',STUDY/'existing_tests_receipt.log',STUDY/'existing_stock_tests.log',STUDY/'previous_optimization_tests.log',STUDY/'existing_full_tests.log',STUDY/'github_preflight.json']
    dependencies.extend(ROOT/p for p in policy['baseline_dependencies'])
    sha={str(p.relative_to(ROOT)):hashlib.sha256(p.read_bytes()).hexdigest() for p in dependencies}
    obj=dict(schema='LR_OPT2023_FREEZE_V1',base_main=policy['base_main'],dependencies_sha256=sha,
        input_commitments=policy['inputs'],source_sha=policy['source_ref'],pre_PNL_optimization_candle_reads=0,pre_PNL_legacy_regression_candle_reads=json.loads((STUDY/'preflight.json').read_text())['pre_PNL_legacy_regression_source_reads'],
        policy_sha256=sha[str((STUDY/'OPTIMIZATION_LEVEL_REJECTION_POLICY.json').relative_to(ROOT))],
        configuration_count=72,evaluations_per_run=216,search_budget=policy['budget'],
        preexisting_repository_files=len(protected),protection_inventory_sha256=sha[str((STUDY/'protected_file_sha256.json').relative_to(ROOT))])
    (STUDY/'source_commitments.json').write_text(json.dumps(obj,indent=2,sort_keys=True)+'\n')
    print(json.dumps({k:v for k,v in obj.items() if k not in ('dependencies_sha256','input_commitments')},sort_keys=True))


if __name__=='__main__':freeze()
