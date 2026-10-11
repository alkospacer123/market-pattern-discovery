"""Pre-P&L source metadata, immutable file inventory and dependency commitments."""
import hashlib
import json
from pathlib import Path
import subprocess

ROOT=Path(__file__).resolve().parents[2]
STUDY=Path(__file__).resolve().parent


def freeze():
    policy=json.loads((STUDY/'OPTIMIZATION_A_POLICY.json').read_text())
    def git(*args):return subprocess.check_output(['git','-C',str(ROOT),*args],text=True).strip()
    if git('rev-parse','HEAD')!=policy['base_main']:raise ValueError('FREEZE_MUST_START_AT_VERIFIED_MAIN')
    paths=git('ls-tree','-r','--name-only',policy['base_main']).splitlines()
    protected={p:hashlib.sha256((ROOT/p).read_bytes()).hexdigest() for p in paths}
    (STUDY/'protected_file_sha256.json').write_text(json.dumps(protected,indent=2,sort_keys=True)+'\n')
    dependencies=[*sorted((ROOT/'IntradayLab/core').glob('*.py')),
        ROOT/'IntradayLab/strategies/equal_high_low_m5_optimization_a_v1.py',
        *sorted(STUDY.glob('*.py')),STUDY/'OPTIMIZATION_A_POLICY.json',STUDY/'GRID.csv',
        STUDY/'pre_pnl_tests.log',STUDY/'protected_file_sha256.json',STUDY/'preflight.json',
        STUDY/'PREREGISTRATION.md',STUDY/'existing_tests_receipt.log',STUDY/'existing_full_tests.log',STUDY/'github_preflight.json']
    sha={str(p.relative_to(ROOT)):hashlib.sha256(p.read_bytes()).hexdigest() for p in dependencies}
    obj=dict(schema='A_OPT2023_FREEZE_V1',base_main=policy['base_main'],dependencies_sha256=sha,
        input_commitments=policy['inputs'],source_sha=policy['source_ref'],pre_PNL_candle_reads=0,
        policy_sha256=sha[str((STUDY/'OPTIMIZATION_A_POLICY.json').relative_to(ROOT))],
        configuration_count=72,evaluations_per_run=144,search_budget=policy['budget'],
        preexisting_repository_files=len(protected),protection_inventory_sha256=sha[str((STUDY/'protected_file_sha256.json').relative_to(ROOT))])
    (STUDY/'source_commitments.json').write_text(json.dumps(obj,indent=2,sort_keys=True)+'\n')
    print(json.dumps({k:v for k,v in obj.items() if k not in ('dependencies_sha256','input_commitments')},sort_keys=True))


if __name__=='__main__':freeze()
