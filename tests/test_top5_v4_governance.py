import importlib.util,json,os,subprocess,sys
from pathlib import Path
import numpy as np
import pandas as pd
import pytest

from market_pattern_discovery.backtest.top5_v4 import *
from market_pattern_discovery.backtest.top5_v4.freeze import file_sha256

ROOT=Path(__file__).resolve().parents[1]

def load_runner():
    spec=importlib.util.spec_from_file_location('run_top5_v4',ROOT/'scripts/run_top5.py');m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m);return m

def test_machine_contract_is_runtime_source_for_period_ticks_friction():
    c=json.loads((ROOT/'config/top5_v4/strategy_contract.json').read_text())
    assert DEV_START==pd.Timestamp(c['periods']['DEV'][0]) and DEV_END==pd.Timestamp(c['periods']['DEV'][1])
    assert TICKS==c['ticks'] and ROUND_STEPS==c['round_steps']
    assert FRICTION_TICKS=={k:c['friction'][k] for k in ('GROSS','BASE','STRESS')}

def test_contract_freezes_same_timestamp_exit_entry_order():
    c=load_contract();assert 'exit timestamp is processed before' in c['execution']['same_timestamp_exit_entry_precedence']

def test_v4_contract_marks_v3_engine_historical_only():
    c=load_contract();s=c['freeze_policy']['legacy_v3_scope'];assert 'historical' in s and 'top5_v4' in s

def test_dev_and_validation_access_ledgers_are_separate():
    m=load_runner();assert m.DEV_ACCESS_FILE!=m.VALIDATION_ACCESS_FILE

def test_runtime_gate_is_read_from_contract_not_runner_constant():
    m=load_runner();assert not hasattr(m,'RUNTIME_GATE');assert load_contract()['testing_policy']['full_grid_runtime_gate_seconds']==600

def test_audit_succeeds_when_market_data_path_does_not_exist(tmp_path):
    env=os.environ.copy();env['PYTHONPATH']=str(ROOT/'src');env['MARKET_PATTERN_DATA']=str(tmp_path/'definitely_missing')
    p=subprocess.run([sys.executable,str(ROOT/'scripts/run_top5.py'),'--audit'],cwd=ROOT,env=env,capture_output=True,text=True)
    assert p.returncode==0,p.stderr;report=json.loads((ROOT/'results/top5_real_strategies_v4/audit_report.json').read_text());assert report['status']=='PASS' and report['market_data_accessed'] is False

def test_runner_without_explicit_mode_does_nothing():
    env=os.environ.copy();env['PYTHONPATH']=str(ROOT/'src')
    p=subprocess.run([sys.executable,str(ROOT/'scripts/run_top5.py')],cwd=ROOT,env=env,capture_output=True,text=True)
    assert p.returncode!=0 and 'required' in p.stderr.lower()

def test_candidate_registry_file_is_exact_descriptor():
    c=load_contract();rows=build_candidate_registry(c);d=json.loads(REGISTRY_PATH.read_text());assert d==registry_descriptor(rows)

def test_validation_workflow_classification_not_internal_confirmation():
    c=load_contract();x=c['validation_workflow']['classification'];assert 'nested inside repository 2026 DISCOVERY period' in x and 'not repository INTERNAL_CONFIRMATION' in x

def test_selected_semantic_hash_ignores_only_all_null_union_schema_columns():
    base=pd.DataFrame([{'candidate_id':'CAND-x','signal_id':'SIG-x','trade_id':'TRADE-x','friction':'BASE','pnl_bps':1.25}])
    union=base.assign(beta_at_entry=np.nan,entry_z=np.nan,w_cny=np.nan,w_si=np.nan)
    assert semantic_ledger_hash(base)==semantic_ledger_hash(union)
    populated=base.assign(beta_at_entry=0.5)
    assert semantic_ledger_hash(base)!=semantic_ledger_hash(populated)
