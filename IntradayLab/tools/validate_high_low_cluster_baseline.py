#!/usr/bin/env python3
"""Two B repeats per duration and unchanged old-engine/A ledgers; no new model."""
import argparse
import importlib
import json
from pathlib import Path
import sys
ROOT=Path(__file__).resolve().parents[2];sys.path.insert(0,str(ROOT))
from IntradayLab.core.reports import dump
from IntradayLab.tools.high_low_cluster_contract import LAB,verify_freeze,output_path,bounded_reads,hashes,protected_check
from IntradayLab.tools.run_high_low_cluster_baseline import run
from IntradayLab.tools.audit_high_low_cluster_baseline import audit
from IntradayLab.tools.validate_equal_high_low_baseline import current_core_metadata
from IntradayLab.tools.verify_equal_high_low_baseline import legacy_published_oracle


def regressions(root):
    out={}
    for name in ('canonical','level_rejection','r16','r17','swing_pullback','trend_pullback','equal_high_low'):
        module=importlib.import_module('IntradayLab.tools.run_'+name+'_baseline')
        old_cfg=json.loads(module.CONFIG.read_text());folder=LAB/'work'/('cluster_'+name+'_regression')
        if folder.exists():raise ValueError('REGRESSION_OUTPUT_EXISTS '+str(folder))
        with bounded_reads(root,old_cfg) as reads:
            with current_core_metadata(module,old_cfg):module.run(root,folder)
        excluded=('validation.json','artifact_hashes.json','changed_files.txt','test_execution.log','provenance.json','audit.json','Independent_Audit.md')
        old=hashes(module.OUT,excluded);new=hashes(folder,excluded)
        if old!=new:raise AssertionError('LEGACY_RESULT_DIFFERENCE '+name+' '+str([p for p in set(old)|set(new) if old.get(p)!=new.get(p)]))
        if name=='equal_high_low':
            auditor=importlib.import_module('IntradayLab.tools.audit_equal_high_low_baseline');receipt=auditor.audit(root,folder)
        else:
            with bounded_reads(root,old_cfg) as oracle_reads:receipt=legacy_published_oracle(name,root,folder,old_cfg)
            before=json.loads((module.OUT/'provenance.json').read_text());after=json.loads((folder/'provenance.json').read_text())
            before.pop('code_sha256');after.pop('code_sha256')
            if before!=after:raise AssertionError('LEGACY_NON_CODE_PROVENANCE '+name)
        out[name]=dict(status='PASS',byte_identical_result_files=len(old),independent_audit_status=receipt['status'],
            actual_source_reads=reads,metadata_exception='Current common core SHA in replay provenance only; original config/clock/parameters unchanged',archived_files_untouched=True)
        print(name+' unchanged economic artifacts / independent audit PASS',flush=True)
    return out


def validate(root):
    repeats_by={}
    for n in (4,7,10):
        cfg,freeze,_=verify_freeze(n);output=output_path(n)
        expected=hashes(output,('validation.json','artifact_hashes.json'));repeats=[]
        for label in ('repeat_one','repeat_two'):
            folder=LAB/'work'/f'cluster_b{n}_{label}';run(root,folder,n);receipt=audit(root,folder,n)
            actual=hashes(folder)
            if actual!=expected:raise AssertionError('BYTE_DIFFERENCE B'+str(n)+' '+str([p for p in set(actual)|set(expected) if actual.get(p)!=expected.get(p)]))
            repeats.append(dict(run=label,all_bytes_identical=True,identical_artifact_files=len(actual),independent_audit_status=receipt['status'],actual_source_reads=receipt['actual_read_guard']))
            print(f'B{n} {label} byte-identical / audit PASS',flush=True)
        repeats_by[n]=dict(repeats=repeats,deterministic_artifact_sha256=expected)
    old=regressions(root)
    pre=json.loads((LAB/'config/high_low_cluster_b4_b7_b10_pre_pnl_validation.json').read_text())
    test_log=(LAB/'config/high_low_cluster_b4_b7_b10_pre_pnl_tests.log').read_text()
    for n in (4,7,10):
        cfg,freeze,_=verify_freeze(n);output=output_path(n)
        result=dict(status='PASS',pre_pnl_freeze_commit=freeze,pre_pnl_validation=pre,pre_pnl_test_summary=test_log.splitlines()[-4:],
            **repeats_by[n],regressions=old,protected_files=protected_check(root,cfg),parameters_changed_after_pnl=False,
            source_ref=cfg['source_ref'],bytes_2024_plus_read=0,bytes_2025_plus_read=0,optimization_allowed=False)
        dump(output/'validation.json',result);dump(output/'artifact_hashes.json',hashes(output,('artifact_hashes.json',)))
    return dict(status='PASS',models=3,repeats=6,regressions=len(old))


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--data-root',type=Path,required=True);print(json.dumps(validate(p.parse_args().data_root),sort_keys=True))
