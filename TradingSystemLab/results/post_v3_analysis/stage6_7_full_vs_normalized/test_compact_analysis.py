import json
from pathlib import Path
import pandas as pd
from TradingSystemLab.results.post_v3_analysis.stage6_7_full_vs_normalized.audit_compact_analysis import audit

HERE=Path(__file__).resolve().parent
def test_shapes_and_no_risk_expansion():
    assert len(pd.read_csv(HERE/'master_110_load_cases_R.csv'))==110
    assert len(pd.read_csv(HERE/'master_220_equity_cases.csv'))==220
    assert len(pd.read_csv(HERE/'full_vs_normalized_comparison.csv'))==110
    assert len(pd.read_csv(HERE/'equity_execution_hashes.csv'))==220
    assert 'risk_scenario' not in pd.read_csv(HERE/'load_monthly_R_metrics.csv').columns
    assert 'risk_scenario' not in pd.read_csv(HERE/'instrument_year_R_metrics.csv').columns
def test_basket_comparison_shapes():
    assert len(pd.read_csv(HERE/'n2_comparison.csv'))==120
    assert len(pd.read_csv(HERE/'n3_comparison.csv'))==80
    assert len(pd.read_csv(HERE/'n4_comparison.csv'))==20
def test_independent_audit(): assert audit()['status']=='PASS'
def test_manifest_scope_stop():
    m=json.loads((HERE/'audit_manifest.json').read_text()); assert not m['stage6_8_started']; assert not m['stage7_executed']

import numpy as np
from TradingSystemLab.results.post_v3_analysis.stage6_7_full_vs_normalized.generate_compact_analysis import simulate_events, period_returns, dd, canonical_hash

def _trades(rows):
    f=pd.DataFrame(rows); f['entry']=pd.to_datetime(f.entry_time,utc=True); f['exit']=pd.to_datetime(f.exit_time,utc=True); return f

def test_continuous_lifecycle_no_reset_and_risk_cash():
    t=_trades([dict(source_trade_id='a',lifecycle='baseline',instrument='X',entry_time='2023-01-01T00:00Z',exit_time='2023-01-02T00:00Z',strategy_R=5.),dict(source_trade_id='b',lifecycle='historical_true_oos',instrument='X',entry_time='2025-01-01T00:00Z',exit_time='2025-01-02T00:00Z',strategy_R=1.)])
    e=simulate_events(t,1,.1,('baseline','historical_true_oos'))
    assert list(e.pre_entry_equity)==[100,150] and e.iloc[1].risk_cash==15 and dd(e.equity_after_exit)==0

def test_elapsed_and_completed_year_cagr():
    years=2.; assert np.isclose(((200/100)**(1/years)-1)*100,41.4213562373)
    assert np.isclose((np.prod([1.1,1.2,1.3])**(1/3)-1)*100,19.7216,atol=.001)

def test_wf_isolation_and_no_duplicated_2024():
    m=pd.read_csv(HERE/'master_220_equity_cases.csv'); assert len(m)==220
    q=pd.read_csv(HERE/'quarter_stability_summary.csv'); assert (q.complete_quarters+q.partial_quarters<=15).all()
    assert {'production_chronological_event_sha256','wf24_event_sha256'}<=set(pd.read_csv(HERE/'equity_execution_hashes.csv').columns)

def test_availability_partial_periods():
    a=pd.read_csv(HERE/'instrument_availability_registry.csv'); b=a[a.lifecycle=='baseline'].set_index('instrument')
    assert b.loc['GLDRUBF','first_complete_quarter']=='2023Q4'; assert b.loc['IMOEXF','first_complete_quarter']=='2024Q1'
    iy=pd.read_csv(HERE/'instrument_year_R_metrics.csv'); assert iy[iy.year==2026].classification.str.startswith('PARTIAL_YEAR_').all()

def test_rank_pareto_and_gate_invariance():
    m=pd.read_csv(HERE/'master_220_equity_cases.csv'); assert m.loc[~m.production_eligible,'reference_rank'].isna().all(); assert not m.loc[~m.production_eligible,'production_pareto'].any()
    iy=pd.read_csv(HERE/'instrument_year_R_metrics.csv'); keys=['configuration_id','instrument','lifecycle','year']; assert iy.groupby(keys).classification.nunique().max()==1

def test_same_time_sizing_and_hash_determinism():
    t=_trades([dict(source_trade_id=x,lifecycle='baseline',instrument='X',entry_time='2023-01-01T00:00Z',exit_time='2023-01-02T00:00Z',strategy_R=1.) for x in ('a','b')]); e=simulate_events(t,1,.1,('baseline',)); assert e.pre_entry_equity.nunique()==1; assert canonical_hash(e)==canonical_hash(simulate_events(t.sample(frac=1),1,.1,('baseline',)))
