"""Build the C_v1 pre-P&L technical receipt and dependency hashes, never run P&L."""
import argparse
import hashlib
import json
from pathlib import Path
from IntradayLab.core.reports import dump
from IntradayLab.tools.return_retest_contract import ROOT,LAB,CONFIG,BASE
from IntradayLab.tools.preflight_return_retest import preflight
from IntradayLab.tools.validate_data_gap_v2 import tests


def freeze(data_root):
    import subprocess
    prior=subprocess.check_output(['git','-C',str(ROOT),'log','-1','--diff-filter=A','--format=%H','--',str(CONFIG.relative_to(ROOT))],text=True).strip()
    if prior:raise ValueError('C_CONFIG_ALREADY_FROZEN')
    if subprocess.check_output(['git','-C',str(ROOT),'rev-parse','HEAD'],text=True).strip()!=BASE:
        raise ValueError('PRE_PNL_BASE_MUST_BE_TASK_BASE')
    log=LAB/'config/return_retest_c_v1_pre_pnl_tests.log'
    receipt=tests(log)
    screen=preflight(data_root,LAB/'config/return_retest_c_v1_pre_pnl_validation.json')
    cfg=json.loads(CONFIG.read_text());cfg['pre_pnl_tests']=receipt
    names=[p for p in (LAB/'core').rglob('*') if p.is_file() and '__pycache__' not in str(p)]
    names += [LAB/p for p in ('strategies/return_retest_rejection_m5.py',
        'tools/return_retest_contract.py','tools/run_return_retest_baseline.py','tools/audit_return_retest_baseline.py',
        'tools/preflight_return_retest.py','tools/freeze_return_retest.py','tools/validate_return_retest_baseline.py',
        'tools/equal_high_low_contract.py','tests/test_return_retest_rejection_m5.py',
        'reports/RETURN_RETEST_C_V1_PREREGISTRATION.md','config/return_retest_c_v1_scope_manifest.json',
        'config/return_retest_c_v1_pre_pnl_validation.json','config/return_retest_c_v1_pre_pnl_tests.log')]
    cfg['execution_code_sha256']={str(p.relative_to(ROOT)):hashlib.sha256(p.read_bytes()).hexdigest() for p in sorted(names)}
    dump(CONFIG,cfg)
    digest=hashlib.sha256(CONFIG.read_bytes()).hexdigest()
    CONFIG.with_suffix('.sha256').write_text(digest+'  '+CONFIG.name+'\n')
    print(json.dumps(dict(status='READY_FOR_SEPARATE_PRE_PNL_COMMIT',tests=receipt['tests'],config_sha256=digest,
        historical_C_pnl_calculated=False,source_guard='2023 exact prefixes only'),sort_keys=True))


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--data-root',type=Path,required=True)
    freeze(p.parse_args().data_root)
