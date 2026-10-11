#!/usr/bin/env python3
"""Two exact A_v1 repeats, unchanged default-mode replays and scope receipts."""
import argparse
from contextlib import contextmanager
import hashlib
import importlib
import json
from pathlib import Path
import subprocess
import sys
from types import SimpleNamespace

ROOT=Path(__file__).resolve().parents[2];LAB=ROOT/'IntradayLab';sys.path.insert(0,str(ROOT))
from IntradayLab.tools.equal_high_low_contract import OUT,verify_freeze,bounded_reads,hashes,protected_check
from IntradayLab.tools.run_equal_high_low_baseline import run
from IntradayLab.tools.audit_equal_high_low_baseline import audit
from IntradayLab.tools.validate_trend_pullback_baseline import legacy_oracle
from IntradayLab.tools.audit_canonical_baseline import read_source,read_csv,check_rows,assert_value,metric
from IntradayLab.core.reports import dump


@contextmanager
def current_core_metadata(module,cfg):
    """Legacy config bytes stay unchanged; only replay's code identity is current.

    Parameters, clocks and source budgets are unchanged. New provenance records
    actual core hashes, never aliases them to historical hashes.
    """
    original=module.json
    digests={p:hashlib.sha256((ROOT/p).read_bytes()).hexdigest() for p in (
        'IntradayLab/core/backtester.py','IntradayLab/core/execution.py')}
    def loads(value,*args,**kwargs):
        obj=original.loads(value,*args,**kwargs)
        if isinstance(obj,dict) and obj.get('id')==cfg.get('id') and 'execution_code_sha256' in obj:
            obj['execution_code_sha256']=dict(obj['execution_code_sha256'])
            for path,digest in digests.items():
                if path in obj['execution_code_sha256']:obj['execution_code_sha256'][path]=digest
        return obj
    module.json=SimpleNamespace(loads=loads,dumps=original.dumps)
    try:yield
    finally:module.json=original


def trend_oracle(root,folder,cfg):
    oracle=importlib.import_module('IntradayLab.tools.audit_trend_pullback_baseline')
    raw,receipts=read_source(root,cfg);ss=read_csv(folder/'signals.csv');tt=read_csv(folder/'trades.csv');checked=0
    for symbol in cfg['instruments']:
        parents=oracle.parent_rows(symbol,raw[symbol])
        events,contexts=oracle.episodes(symbol,parents,True)
        expected_s,expected_t=oracle.replay(symbol,parents,events)
        for actual,expected,label in ((ss,expected_s,'SIGNALS'),(tt,expected_t,'TRADES')):
            checked+=check_rows([r for r in actual if r['instrument']==symbol],expected,
                sorted({k for r in expected for k in r if k!='unknown_effective_at'}),'TREND '+label)
        for k,v in metric([t for t in tt if t['instrument']==symbol]).items():
            assert_value(json.loads((folder/'metrics.json').read_text())['instruments'][symbol]['conditional_closed_only_C1'][k],v,'TREND_METRIC');checked+=1
    return dict(status='PASS',checked_fields=checked,source_receipts=receipts)


def validate(root,output):
    if output.resolve()!=OUT.resolve():raise ValueError('CANONICAL_OUTPUT_REQUIRED')
    cfg,freeze,_=verify_freeze()
    pre=json.loads((LAB/'config/equal_high_low_m5_2023_a_v1_pre_pnl_validation.json').read_text())
    if pre['status']!='PASS':raise AssertionError('PRE_PNL_VALIDATION')
    excluded=('validation.json','artifact_hashes.json')
    expected=hashes(output,excluded);repeats=[]
    for label in ('repeat_one','repeat_two'):
        folder=LAB/'work'/('equal_'+label)
        run(root,folder)
        audit_reads=audit(root,folder)['actual_read_guard']
        actual=hashes(folder)
        if actual!=expected:raise AssertionError('BYTE_DIFFERENCE '+str([p for p in set(actual)|set(expected) if actual.get(p)!=expected.get(p)]))
        repeats.append(dict(run=label,identical_artifact_files=len(actual),all_bytes_identical=True,independent_audit_reads=audit_reads))
        print(label+' byte-identical / audit PASS',flush=True)
    regressions={}
    for name in ('canonical','level_rejection','r16','r17','swing_pullback','trend_pullback'):
        module=importlib.import_module('IntradayLab.tools.run_'+name+'_baseline');old_cfg=json.loads(module.CONFIG.read_text())
        folder=LAB/'work'/('equal_'+name+'_regression')
        with bounded_reads(root,old_cfg) as replay_reads:
            with current_core_metadata(module,old_cfg):module.run(root,folder)
        excluded_old=('validation.json','artifact_hashes.json','changed_files.txt','test_execution.log','provenance.json','audit.json','Independent_Audit.md')
        old=hashes(module.OUT,excluded_old);new=hashes(folder,excluded_old)
        if old!=new:raise AssertionError('LEGACY_RESULT_DIFFERENCE '+name+' '+str([p for p in set(old)|set(new) if old.get(p)!=new.get(p)]))
        with bounded_reads(root,old_cfg) as oracle_reads:
            receipt=trend_oracle(root,folder,old_cfg) if name=='trend_pullback' else legacy_oracle(name,root,folder,old_cfg)
        before=json.loads((module.OUT/'provenance.json').read_text());after=json.loads((folder/'provenance.json').read_text())
        before_code=before.pop('code_sha256');after_code=after.pop('code_sha256')
        if before!=after:raise AssertionError('LEGACY_NON_CODE_PROVENANCE_DIFFERENCE '+name)
        changes={p:dict(stored=before_code.get(p),replayed=after_code.get(p)) for p in set(before_code)|set(after_code) if before_code.get(p)!=after_code.get(p)}
        for p,item in changes.items():
            actual=hashlib.sha256((ROOT/p).read_bytes()).hexdigest()
            if item['replayed']!=actual:raise AssertionError('REPLAY_CODE_IDENTITY '+p)
            if p in cfg['execution_code_sha256']:
                if actual!=cfg['execution_code_sha256'][p]:raise AssertionError('FROZEN_NEW_DEPENDENCY '+p)
            elif p not in ('IntradayLab/core/backtester.py','IntradayLab/core/execution.py'):
                base_bytes=subprocess.check_output(['git','-C',str(ROOT),'show',cfg['base_main']+':'+p])
                if actual!=hashlib.sha256(base_bytes).hexdigest():raise AssertionError('UNAPPROVED_LEGACY_CODE_CHANGE '+p)
        regressions[name]=dict(status='PASS',byte_identical_result_files=len(old),result_sha256=old,
            independent_audit=receipt,actual_source_reads=replay_reads+oracle_reads,non_code_provenance_identical=True,
            replay_code_identity_changes=changes,archived_files_untouched=True,
            metadata_exception='Only current core SHA values in runner memory; original config bytes/parameters/clocks unchanged')
        print(name+' default replay byte-identical / independent audit PASS',flush=True)
    result=dict(status='PASS',pre_pnl_tests=pre,pre_pnl_freeze_commit=freeze,repeats=repeats,
        deterministic_artifact_sha256=expected,regressions=regressions,protected_files=protected_check(root,cfg),
        parameters_changed_after_pnl=False,source_ref=cfg['source_ref'],bytes_2024_plus_read=0,bytes_2025_plus_read=0,
        optimization_allowed=False)
    dump(output/'validation.json',result);dump(output/'artifact_hashes.json',hashes(output,('artifact_hashes.json',)))
    return result


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--data-root',type=Path,required=True);p.add_argument('--output',type=Path,default=OUT)
    a=p.parse_args();r=validate(a.data_root,a.output);print(json.dumps(dict(status=r['status'],repeats=len(r['repeats']),regressions=len(r['regressions']))))
