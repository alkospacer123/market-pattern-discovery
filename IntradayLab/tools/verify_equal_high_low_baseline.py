#!/usr/bin/env python3
"""Reporting-only correction of legacy oracle field selection after first P&L.

Frozen validator compared every internal oracle annotation, including window
metadata absent from rejected canonical CSV rows. Use the original published
signal_keys/trade_keys instead. All trading code/config/output bytes stay frozen.
"""
import argparse
import ast
import hashlib
import importlib
import json
from pathlib import Path
import sys

ROOT=Path(__file__).resolve().parents[2];sys.path.insert(0,str(ROOT));LAB=ROOT/'IntradayLab'
from IntradayLab.tools import validate_equal_high_low_baseline as validator
from IntradayLab.tools.audit_canonical_baseline import read_source,read_csv,check_rows,assert_value,metric
from IntradayLab.tools.equal_high_low_contract import OUT,hashes,verify_freeze
from IntradayLab.core.reports import dump


def published_fields(module,name):
    """Read the exact field contract of the unchanged archived audit function."""
    tree=ast.parse(Path(module.__file__).read_text())
    function=next(n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name=='audit')
    assignments=[n for n in ast.walk(function) if isinstance(n,ast.Assign) and
        any(isinstance(t,ast.Name) and t.id==name for t in n.targets)]
    if len(assignments)!=1:raise AssertionError('PUBLISHED_AUDIT_CONTRACT '+name)
    # The already-pinned auditor owns literal field lists and static expansions.
    result=eval(compile(ast.Expression(assignments[0].value),module.__file__,'eval'),module.__dict__)
    if not isinstance(result,tuple) or not all(isinstance(k,str) for k in result):
        raise AssertionError('AUDIT_FIELD_LIST_SCHEMA')
    return result


def legacy_published_oracle(name,root,folder,cfg):
    oracle=importlib.import_module('IntradayLab.tools.audit_'+name+'_baseline')
    raw,receipts=read_source(root,cfg);ss=read_csv(folder/'signals.csv');tt=read_csv(folder/'trades.csv');checked=0
    signal_keys=published_fields(oracle,'signal_keys');trade_keys=published_fields(oracle,'trade_keys')
    for symbol in cfg['instruments']:
        observations=oracle.parent_rows(symbol,raw[symbol]) if name=='trend_pullback' else raw[symbol]
        if name in ('swing_pullback','trend_pullback'):
            events,contexts=oracle.episodes(symbol,observations,True)
            actual_context=read_csv(folder/('h1_context.csv' if name=='trend_pullback' else 'mtf_context.csv'))
            checked+=check_rows([r for r in actual_context if r['instrument']==symbol],contexts,tuple(contexts[0]),name+'_CONTEXT')
        else:events=oracle.episodes(symbol,observations)
        es,et=oracle.replay(symbol,observations,events)
        checked+=check_rows([s for s in ss if s['instrument']==symbol],es,signal_keys,name+'_SIGNALS')
        checked+=check_rows([t for t in tt if t['instrument']==symbol],et,trade_keys,name+'_TRADES')
        metrics=json.loads((folder/'metrics.json').read_text())['instruments'][symbol]['conditional_closed_only_C1']
        for k,v in metric([t for t in tt if t['instrument']==symbol]).items():
            assert_value(metrics[k],v,name+'_METRIC '+k);checked+=1
    return dict(status='PASS',checked_fields=checked,source_receipts=receipts,
        published_signal_fields=signal_keys,published_trade_fields=trade_keys,
        archived_auditor_sha256=hashlib.sha256(Path(oracle.__file__).read_bytes()).hexdigest(),
        method='Unchanged independent archived signal/path/metric oracle, exact published CSV audit fields; byte equality also required')


def verify(root,output):
    verify_freeze()
    previous_legacy,previous_trend=validator.legacy_oracle,validator.trend_oracle
    validator.legacy_oracle=legacy_published_oracle
    validator.trend_oracle=lambda root,folder,cfg:legacy_published_oracle('trend_pullback',root,folder,cfg)
    try:
        result=validator.validate(root,output)
    finally:
        validator.legacy_oracle,validator.trend_oracle=previous_legacy,previous_trend
    result['reporting_correction']=dict(
        status='PASS',added_after_first_pnl=True,trading_code_or_parameters_changed=False,
        original_frozen_validator_standalone_status='FAIL: legacy internal oracle annotation not in serialized rejected-signal CSV contract',
        observed_example='canonical USDRUBF_2023-01-03_-1_1235: oracle window_end=2023-01-03 14:00 MSK; canonical rejected-row window_end blank',
        correction='Use unchanged original auditors exact signal_keys/trade_keys; verify all replay economic files byte-identical. No signal, execution, C1 or P&L arithmetic changed.',
        verifier_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest())
    dump(output/'validation.json',result)
    dump(output/'artifact_hashes.json',hashes(output,('artifact_hashes.json',)))
    return result


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--data-root',type=Path,required=True);p.add_argument('--output',type=Path,default=OUT)
    a=p.parse_args();r=verify(a.data_root,a.output);print(json.dumps(dict(status=r['status'],repeats=len(r['repeats']),regressions=len(r['regressions']),reporting_correction=r['reporting_correction']),sort_keys=True))
