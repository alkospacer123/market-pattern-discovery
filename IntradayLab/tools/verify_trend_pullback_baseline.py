#!/usr/bin/env python3
"""Final reporting verifier using each legacy auditor's canonical field contract.

The pre-PnL validator's broad union included oracle-only window metadata on
rejected ORB probes. Legacy ledgers deliberately leave those fields blank.
This reporting wrapper uses the unchanged auditors' declared signal/trade
field sets. Frozen config, adapters, strategy, engine, runner and audit code
remain byte unchanged. No signals, execution or economics are changed here.
"""
import argparse
import ast
import hashlib
import importlib
import inspect
import json
from pathlib import Path
import sys

ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT))
sys.path.insert(0,str(ROOT/'IntradayLab/tools'))
from IntradayLab.tools import validate_trend_pullback_baseline as original
from IntradayLab.tools.audit_canonical_baseline import read_source,read_csv,check_rows,metric,assert_value
from IntradayLab.core.reports import dump


def canonical_fields(oracle):
    tree=ast.parse(inspect.getsource(oracle.audit));fields={}
    for node in ast.walk(tree):
        if isinstance(node,ast.Assign) and len(node.targets)==1 and isinstance(node.targets[0],ast.Name) and node.targets[0].id in ('signal_keys','trade_keys'):
            # Only constants/tuples/comprehensions of literal field names; no calls.
            if any(isinstance(n,(ast.Call,ast.Attribute)) for n in ast.walk(node.value)):
                raise AssertionError('NON_LITERAL_AUDIT_FIELD_CONTRACT')
            values=eval(compile(ast.Expression(node.value),'canonical legacy field names','eval'),{'__builtins__':{}},{})
            if not values or not all(isinstance(k,str) for k in values):raise AssertionError('FIELD_CONTRACT_SCHEMA')
            fields[node.targets[0].id]=values
    if set(fields)!={'signal_keys','trade_keys'}:raise AssertionError('LEGACY_FIELD_CONTRACT_MISSING')
    return fields


def legacy_oracle(name,source_root,folder,cfg):
    oracle=importlib.import_module('IntradayLab.tools.audit_'+name+'_baseline')
    fields=canonical_fields(oracle);raw,receipts=read_source(source_root,cfg)
    ss=read_csv(folder/'signals.csv');tt=read_csv(folder/'trades.csv');checked=0
    metrics=json.loads((folder/'metrics.json').read_text())
    for symbol in cfg['instruments']:
        if name=='swing_pullback':
            events,contexts=oracle.episodes(symbol,raw[symbol],True)
            actual=read_csv(folder/'mtf_context.csv')
            checked+=check_rows([r for r in actual if r['instrument']==symbol],contexts,tuple(contexts[0]),name+'_CONTEXT')
        else:events=oracle.episodes(symbol,raw[symbol])
        expected_s,expected_t=oracle.replay(symbol,raw[symbol],events)
        for actual,expected,keys,label in ((ss,expected_s,fields['signal_keys'],'SIGNALS'),(tt,expected_t,fields['trade_keys'],'TRADES')):
            checked+=check_rows([r for r in actual if r['instrument']==symbol],expected,keys,name+'_'+label)
        for key,value in metric([r for r in tt if r['instrument']==symbol]).items():
            assert_value(metrics['instruments'][symbol]['conditional_closed_only_C1'][key],value,name+'_METRIC '+key);checked+=1
    return dict(status='PASS',checked_fields=checked,method='unchanged independent raw-source signal/path/CSV economy oracles with their unchanged canonical field sets',
        signal_fields=list(fields['signal_keys']),trade_fields=list(fields['trade_keys']),source_receipts=receipts)


def verify(root,output):
    previous=original.legacy_oracle
    original.legacy_oracle=legacy_oracle
    try:result=original.validate(root,output)
    finally:original.legacy_oracle=previous
    result['reporting_verifier']=dict(path=str(Path(__file__).relative_to(ROOT)),sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
        added_after_first_PnL=True,reason='Use unchanged legacy auditors canonical comparison fields instead of oracle-only metadata on rejected probes',
        frozen_code_and_parameters_unchanged=True)
    dump(output/'validation.json',result)
    dump(output/'artifact_hashes.json',original.hashes(output,('artifact_hashes.json',)))
    return result


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--data-root',type=Path,required=True);p.add_argument('--output',type=Path,default=original.OUT)
    a=p.parse_args();r=verify(a.data_root,a.output)
    print(json.dumps(dict(status=r['status'],regressions=len(r['regressions']),repeats=len(r['replay_repeats']))))
