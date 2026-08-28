from __future__ import annotations
import json
from pathlib import Path
import pandas as pd
import pytest
from jsonschema import Draft202012Validator

from market_pattern_discovery.strategy_discovery.causality import (
 assert_closed_m5, assert_deterministic_replay, assert_future_mutation_invariance,
 assert_prefix_invariance, assert_reference_known, CausalityViolation)
from market_pattern_discovery.strategy_discovery.governance import (
 authorize_dataset, canonical_sha256, deterministic_candidate_id, estimate_candidates, verify_frozen_strategy,
 CandidateLimitExceeded, DataAccessForbidden, DatasetRole, ExecutionMode,
 StrategyFreezeViolation, TrueOOSAccessForbidden)
from market_pattern_discovery.strategy_discovery.models import (
 MLHypothesisConfig, OracleTarget, FutureFieldLeakage, validate_causal_strategy,
 validate_predictors, plateau_summary)
from market_pattern_discovery.strategy_discovery.synthetic import known_events

ROOT=Path(__file__).parents[2]

def registry(): return json.loads((ROOT/'config/phase6a/strategy_candidate_registry_v1.json').read_text())

def test_registry_schema_ids_status_and_fingerprints():
    data=registry(); schema=json.loads((ROOT/'schemas/phase6a/strategy_candidate_registry_v1.schema.json').read_text())
    Draft202012Validator(schema).validate(data)
    ids=[x['strategy_family_id'] for x in data['families']]
    assert len(ids)==len(set(ids))==59
    assert not {'promoted','frozen'} & {x['scientific_status'] for x in data['families']}
    for family in data['families']:
        unsigned={k:v for k,v in family.items() if k!='fingerprint'}
        assert family['fingerprint']==canonical_sha256(unsigned)

def test_frozen_round_semantics_and_count_estimator():
    round_family=next(x for x in registry()['families'] if x['strategy_family_id']=='KRL-01')
    assert round_family['instrument_semantics']['CNYRUBF']=={'tick':.001,'round_level_step':.05}
    assert round_family['instrument_semantics']['USDRUBF']=={'tick':.01,'round_level_step':.1}
    estimates=estimate_candidates(registry()['families'])
    assert estimates[0].parameter_combinations==2
    with pytest.raises(CandidateLimitExceeded): estimate_candidates(registry()['families'],max_per_family=1)
    with pytest.raises(CandidateLimitExceeded): estimate_candidates(registry()['families'],max_total=1)
    args=('KRL-01',{'lookback':5})
    one=deterministic_candidate_id(*args,instrument='CNYRUBF',timeframe='M1',seed=617,code_version='abc')
    assert one==deterministic_candidate_id(*args,instrument='CNYRUBF',timeframe='M1',seed=617,code_version='abc')
    assert one!=deterministic_candidate_id(*args,instrument='CNYRUBF',timeframe='M1',seed=618,code_version='abc')

@pytest.mark.parametrize('mode,role,frozen,allowed',[
 (ExecutionMode.DISCOVERY,DatasetRole.DISCOVERY,False,True),
 (ExecutionMode.DISCOVERY,DatasetRole.INTERNAL_CONFIRMATION,False,False),
 (ExecutionMode.CONFIRMATION,DatasetRole.INTERNAL_CONFIRMATION,True,True),
 (ExecutionMode.CONFIRMATION,DatasetRole.INTERNAL_CONFIRMATION,False,False),
 (ExecutionMode.TRUE_OOS_FINAL,DatasetRole.TRUE_OOS,True,True)])
def test_access_matrix(mode,role,frozen,allowed):
    if allowed: authorize_dataset(mode,role,strategy_frozen=frozen)
    else:
        with pytest.raises(DataAccessForbidden): authorize_dataset(mode,role,strategy_frozen=frozen)

def test_architecture_synthetic_only_and_true_oos_hard_fail():
    authorize_dataset(ExecutionMode.ARCHITECTURE,DatasetRole.DISCOVERY,synthetic=True)
    with pytest.raises(DataAccessForbidden): authorize_dataset(ExecutionMode.ARCHITECTURE,DatasetRole.DISCOVERY)
    with pytest.raises(TrueOOSAccessForbidden): authorize_dataset(ExecutionMode.DISCOVERY,DatasetRole.TRUE_OOS)

def test_oracle_and_ml_predictor_separation_and_fingerprints():
    target=OracleTarget('O1','15m',('mfe','mae'),('atr_20','close'))
    assert target.horizon=='15m'
    with pytest.raises(FutureFieldLeakage): OracleTarget('bad','5m',('mfe',),('mfe',))
    with pytest.raises(FutureFieldLeakage): validate_predictors(['future_close'])
    a=MLHypothesisConfig('LOGISTIC_REGRESSION',('atr_20',),'mfe',provenance={'code':'abc'})
    b=MLHypothesisConfig('LOGISTIC_REGRESSION',('atr_20',),'mfe',provenance={'code':'abc'})
    assert a.config_sha256==b.config_sha256

def signal(frame): return frame.close.gt(frame.close.shift(1)).fillna(False)

def test_causality_prefix_mutation_replay_and_closed_m5():
    frame=pd.DataFrame({'open':[1,2,1,4], 'high':[2,3,2,5], 'low':[0,1,0,3], 'close':[1,2,1,4], 'volume':[1]*4})
    assert_prefix_invariance(signal,frame,2); assert_future_mutation_invariance(signal,frame,2); assert_deterministic_replay(signal,frame)
    t=pd.Timestamp('2026-01-05 10:15',tz='Europe/Moscow'); assert_closed_m5(t,t)
    with pytest.raises(CausalityViolation): assert_closed_m5(t,t+pd.Timedelta(minutes=5))
    with pytest.raises(CausalityViolation): assert_reference_known(t+pd.Timedelta(minutes=1),t)

def strategy():
    base={'strategy_id':'S-a','parent_family_id':'KRL-01','origin_track':'KNOWN','version':'1.0','instrument':'CNYRUBF','timeframe':'M1','decision_clock':'close_time','causal_predicates':[{'field':'close','op':'gt','value':1}], 'entry_side':'LONG','entry_timing':'next_open','reference_level_definition':{},'context_filters':[],'position_constraints':{},'exit_definition':{},'stop_definition':{},'target_definition':{},'time_exit':5,'transaction_cost_model_ref':'cost-v1','slippage_model_ref':'slip-v1','parameters':{},'lineage':[{'stage':'family','id':'KRL-01'},{'stage':'causal_strategy','id':'S-a'}],'parent_candidate_ids':['C-a'],'creation_stage':'architecture','status':'frozen','causal_validation_passed':True}
    base['strategy_sha256']=canonical_sha256(base); return base

def test_strategy_schema_lineage_freeze_and_hash_immutability():
    spec=strategy(); validate_causal_strategy(spec)
    schema=json.loads((ROOT/'schemas/phase6a/causal_strategy_v1.schema.json').read_text()); Draft202012Validator(schema).validate(spec)
    assert [x['stage'] for x in spec['lineage']]==['family','causal_strategy']
    verify_frozen_strategy(spec,spec['strategy_sha256'],discovery_frozen=True,confirmation_frozen=True,causal_validation_passed=True)
    changed={**spec,'time_exit':6}
    with pytest.raises(StrategyFreezeViolation): verify_frozen_strategy(changed,spec['strategy_sha256'],discovery_frozen=True,confirmation_frozen=True,causal_validation_passed=True)
    with pytest.raises(StrategyFreezeViolation): verify_frozen_strategy(spec,spec['strategy_sha256'],discovery_frozen=True,confirmation_frozen=False,causal_validation_passed=True)

def test_backtest_and_robustness_schemas_and_plateau():
    for name in ('backtest_result_v1.schema.json','robustness_result_v1.schema.json'):
        Draft202012Validator.check_schema(json.loads((ROOT/'schemas/phase6a'/name).read_text()))
    broad=plateau_summary([9.5,10,9.6]); sharp=plateau_summary([1,10,1])
    assert broad['near_peak_fraction']>sharp['near_peak_fraction']

def test_synthetic_known_event_semantics_are_close_only():
    # One deterministic fixture exercises every semantic output; dedicated
    # predicate assertions ensure no event is reported before sufficient prefix.
    close=[99.9,100.0,100.0,100.0,100.7,99.8,100.0,100.0,100.0,101.0]
    high =[100.0,100.05,100.04,100.03,100.8,100.6,100.05,100.05,100.05,101.1]
    low  =[99.8,99.95,99.96,99.97,99.9,99.7,99.95,99.95,99.95,99.9]
    df=pd.DataFrame({'open':close,'high':high,'low':low,'close':close,'volume':[1]*10})
    out=known_events(df,session_open_bars=3)
    required={'round_rejection','round_breakout','false_breakout','breakout_retest','repeated_tests','equal_high','equal_low','sweep','compression_expansion','momentum','mean_reversion','previous_high_low','opening_range'}
    assert required <= set(out)
    assert not out.loc[:2,['repeated_tests','compression_expansion','momentum','mean_reversion','opening_range']].any().any()
    assert out['round_breakout'].any() and out['false_breakout'].any() and out['repeated_tests'].any()
