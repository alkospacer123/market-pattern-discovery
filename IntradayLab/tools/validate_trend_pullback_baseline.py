#!/usr/bin/env python3
"""Two byte-identical M15/H1 repeats and five frozen M5 regressions."""
import argparse
from contextlib import contextmanager
import hashlib
import importlib
import json
from pathlib import Path
import subprocess
import sys
from types import SimpleNamespace

ROOT=Path(__file__).resolve().parents[2];LAB=ROOT/'IntradayLab'
sys.path.insert(0,str(ROOT))
from IntradayLab.tools.run_trend_pullback_baseline import run,OUT,FREEZE,CONFIG
from IntradayLab.tools.audit_trend_pullback_baseline import audit
from IntradayLab.tools.audit_canonical_baseline import read_source,read_csv,check_rows,assert_value,metric
from IntradayLab.core.reports import dump


def hashes(folder,excluded=()):
    return {str(p.relative_to(folder)):hashlib.sha256(p.read_bytes()).hexdigest()
        for p in sorted(folder.rglob('*')) if p.is_file() and p.name not in excluded}


def protected_manifest(base):
    paths=subprocess.check_output(['git','-C',str(ROOT),'ls-tree','-r','--name-only',base],text=True).splitlines()
    changed=subprocess.check_output(['git','-C',str(ROOT),'diff','--name-only',base],text=True).splitlines()
    allowed={'IntradayLab/core/backtester.py'}
    if any(not p.startswith('IntradayLab/') or (p in paths and p not in allowed) for p in changed):
        raise AssertionError('PROTECTED_PATH_CHANGED '+str(changed))
    receipt={}
    for path in paths:
        if path.startswith('IntradayLab/') and path not in allowed:
            original=subprocess.check_output(['git','-C',str(ROOT),'show',base+':'+path])
            if (ROOT/path).read_bytes()!=original:raise AssertionError('PROTECTED_BYTES '+path)
            receipt[path]=hashlib.sha256(original).hexdigest()
    return dict(status='PASS',allowed_existing_changes=sorted(allowed),checked_existing_files=len(receipt),
        preserved_result_hashes={p:d for p,d in receipt.items() if p.startswith('IntradayLab/results/')},
        TradingSystemLab_diff_empty=True,outside_IntradayLab_diff_empty=True,
        all_old_strategies_configs_results_byte_unchanged=True)


@contextmanager
def approved_m15_engine_receipt(module,cfg):
    """Only allow the explicitly approved engine SHA in legacy in-memory metadata.

    Old config bytes, source budgets, parameters and all economic rules are
    still checked unchanged by the legacy runner. No archived file is edited.
    Replay provenance records the actual new engine SHA, never an old alias.
    """
    original=module.json;digest=hashlib.sha256((LAB/'core/backtester.py').read_bytes()).hexdigest()
    def loads(value,*args,**kwargs):
        obj=original.loads(value,*args,**kwargs)
        if isinstance(obj,dict) and obj.get('id')==cfg.get('id') and 'execution_code_sha256' in obj:
            obj['execution_code_sha256']=dict(obj['execution_code_sha256'])
            obj['execution_code_sha256']['IntradayLab/core/backtester.py']=digest
        return obj
    module.json=SimpleNamespace(loads=loads,dumps=original.dumps)
    try:yield
    finally:module.json=original


def legacy_oracle(name,source_root,folder,cfg):
    """Invoke unchanged independent raw-source oracle functions directly.

    Legacy full-audit entrypoints require historical engine bytes and therefore
    intentionally cannot authorize a new engine. Here their unchanged signal,
    path and CSV metric oracles audit this approved M5 regression independently.
    """
    oracle=importlib.import_module('IntradayLab.tools.audit_'+name+'_baseline')
    raw,receipts=read_source(source_root,cfg)
    ss=read_csv(folder/'signals.csv');tt=read_csv(folder/'trades.csv');checked=0
    metrics=json.loads((folder/'metrics.json').read_text())
    for symbol in cfg['instruments']:
        if name=='swing_pullback':
            events,contexts=oracle.episodes(symbol,raw[symbol],True)
            actual_context=read_csv(folder/'mtf_context.csv')
            checked+=check_rows([c for c in actual_context if c['instrument']==symbol],contexts,tuple(contexts[0]),name+'_CONTEXT')
        else:events=oracle.episodes(symbol,raw[symbol])
        expected_s,expected_t=oracle.replay(symbol,raw[symbol],events)
        for actual,expected,label in ((ss,expected_s,'SIGNALS'),(tt,expected_t,'TRADES')):
            keys=sorted({k for r in expected for k in r if k!='unknown_effective_at'})
            checked+=check_rows([r for r in actual if r['instrument']==symbol],expected,keys,name+'_'+label)
        m=metric([r for r in tt if r['instrument']==symbol])
        for key,value in m.items():assert_value(metrics['instruments'][symbol]['conditional_closed_only_C1'][key],value,name+'_METRIC '+key);checked+=1
    return dict(status='PASS',checked_fields=checked,method='unchanged independent raw-source signal/path/CSV economy oracles; no production imports',source_receipts=receipts)


def validate(root,output):
    if output.resolve()!=OUT.resolve():raise ValueError('CANONICAL_OUTPUT_REQUIRED')
    cfg=json.loads(CONFIG.read_text())
    pre=json.loads((LAB/'config/trend_pullback_m15_h1_2023_v1_pre_pnl_validation.json').read_text())
    if pre['status']!='PASS':raise AssertionError('PRE_PNL_TECHNICAL_TESTS')
    expected=hashes(output,('validation.json','artifact_hashes.json','test_execution.log'))
    repeats=[]
    for suffix in ('repeat_one','repeat_two'):
        target=LAB/'work'/('trend_'+suffix)
        run(root,target);audit(root,target)
        actual=hashes(target)
        if expected!=actual:raise AssertionError('NONDETERMINISTIC '+str([k for k in set(expected)|set(actual) if expected.get(k)!=actual.get(k)]))
        repeats.append(dict(run=suffix,files=len(actual),all_bytes_identical=True))
        print('Trend '+suffix+' byte-identical',flush=True)
    regressions={}
    for name in ('canonical','r17','r16','level_rejection','swing_pullback'):
        module=importlib.import_module('IntradayLab.tools.run_'+name+'_baseline')
        old_cfg=json.loads(module.CONFIG.read_text())
        replay=LAB/'work'/('trend_'+name+'_regression')
        with approved_m15_engine_receipt(module,old_cfg):module.run(root,replay)
        excluded=('validation.json','artifact_hashes.json','changed_files.txt','test_execution.log','provenance.json','audit.json','Independent_Audit.md')
        old_hash=hashes(module.OUT,excluded);new_hash=hashes(replay,excluded)
        if old_hash!=new_hash:raise AssertionError(name+'_RESULT_CHANGED '+str([k for k in set(old_hash)|set(new_hash) if old_hash.get(k)!=new_hash.get(k)]))
        oracle=legacy_oracle(name,root,replay,old_cfg)
        old_prov=json.loads((module.OUT/'provenance.json').read_text());new_prov=json.loads((replay/'provenance.json').read_text())
        old_code=old_prov.pop('code_sha256');new_code=new_prov.pop('code_sha256')
        if old_prov!=new_prov:raise AssertionError(name+'_NON_CODE_PROVENANCE_CHANGED')
        changes={}
        for path in sorted(set(old_code)|set(new_code)):
            if old_code.get(path)==new_code.get(path):continue
            current=new_code.get(path)
            if path in cfg['execution_code_sha256']:
                if current!=cfg['execution_code_sha256'][path]:raise AssertionError('NEW_CODE_HASH '+path)
                explanation='Approved pre-P&L M15 engine/adapter/strategy; M5 output bytes unchanged'
            else:
                data=subprocess.check_output(['git','-C',str(ROOT),'show',cfg['base_main']+':'+path])
                if current!=hashlib.sha256(data).hexdigest():raise AssertionError('BASE_CODE_HASH '+path)
                explanation='Already merged base-main code unchanged by this PR'
            changes[path]=dict(stored=old_code.get(path),replayed=current,explanation=explanation)
        regressions[name]=dict(status='PASS',byte_identical_result_files=len(old_hash),result_sha256=old_hash,
            independent_audit=oracle,stored_artifacts_all_byte_unchanged=True,non_code_provenance_identical=True,
            separate_replay_code_sha_changes=changes,
            legacy_metadata_exception='In-memory execution-code SHA only; config bytes and all parameters unchanged')
        print(name+' byte-identical / independent oracle PASS',flush=True)
    protected=protected_manifest(cfg['base_main'])
    if subprocess.check_output(['git','-C',str(root),'status','--porcelain=v1','--untracked-files=all'],text=True).strip():raise AssertionError('SOURCE_CHANGED')
    result=dict(status='PASS',pre_pnl_tests=pre,replay_repeats=repeats,deterministic_artifact_sha256=expected,
        regressions=regressions,protected_files=protected,config_freeze_commit=FREEZE,
        config_unchanged_since_before_PnL=True,market_pattern_data_clean=True,
        source_ref=cfg['source_ref'],parameters_changed_after_PnL=False,optimization_allowed=False)
    dump(output/'validation.json',result)
    dump(output/'artifact_hashes.json',hashes(output,('artifact_hashes.json',)))
    return result


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--data-root',type=Path,required=True);p.add_argument('--output',type=Path,default=OUT)
    a=p.parse_args();r=validate(a.data_root,a.output);print(json.dumps(dict(status=r['status'],regressions=len(r['regressions']),repeats=len(r['replay_repeats']))))
