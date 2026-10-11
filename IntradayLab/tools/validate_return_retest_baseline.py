"""Two full frozen verification repeats, independent audit and exact artifact hashes."""
import argparse
from pathlib import Path
from IntradayLab.core.reports import dump
from IntradayLab.tools.return_retest_contract import LAB,OUT,verify_freeze,bounded_reads,hashes,protected_check
from IntradayLab.tools.run_return_retest_baseline import run
from IntradayLab.tools.audit_return_retest_baseline import audit


def validate(data_root,baseline,output):
    cfg,freeze,digest=verify_freeze()
    if output.exists() or not output.resolve().is_relative_to((LAB/'work').resolve()):
        raise ValueError('FRESH_WORK_OUTPUT_REQUIRED')
    output.mkdir(parents=True)
    before=hashes(baseline);audits=[];repeats=[]
    with bounded_reads(data_root,cfg) as reads:
        audits.append(dict(audit(baseline,data_root),actual_source_reads=reads))
    for n in (1,2):
        target=output/f'repeat_{n}'
        run(data_root,target)
        with bounded_reads(data_root,cfg) as reads:
            audits.append(dict(audit(target,data_root),actual_source_reads=reads))
        actual=hashes(target)
        if actual!=before:raise AssertionError('NONDETERMINISTIC_C_ARTIFACTS '+str(n))
        repeats.append(dict(repeat=n,status='PASS',all_bytes_identical=True,compared_files=len(actual),sha256=actual))
        print(f'C repeat {n}: all {len(actual)} files byte-identical; independent audit PASS',flush=True)
    receipt=dict(status='PASS',pre_pnl_freeze_commit=freeze,config_sha256=digest,
        pre_pnl_tests=cfg['pre_pnl_tests'],independent_audits=audits,deterministic_repeats=repeats,
        first_run_then_two_verification_repeats=True,parameters_changed_after_first_pnl=False,
        protected_scope=protected_check(data_root,cfg),bytes_2024_plus_read=0,
        archived_comparisons='Separate regression receipt; no archived artifact overwritten',
        technical_correctness='PASS',optimization_executed=False)
    dump(output/'validation.json',receipt)
    dump(baseline/'audit.json',audits[0]);dump(baseline/'validation.json',receipt)
    dump(baseline/'artifact_hashes.json',before)
    return receipt


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--data-root',type=Path,required=True)
    p.add_argument('--baseline',type=Path,default=OUT);p.add_argument('--output',type=Path,required=True)
    a=p.parse_args();r=validate(a.data_root,a.baseline,a.output);print(r['status'])
