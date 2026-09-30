import json, shutil
from pathlib import Path
import pandas as pd
import pytest
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
from TradingSystemLab.results.post_v3_analysis.stage6_7_full_vs_normalized.generate_compact_analysis import simulate_events, period_returns, exposure, dd, canonical_hash

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

def test_zero_month_spine_and_nonpositive_sequence():
    t=_trades([dict(source_trade_id='a',lifecycle='baseline',instrument='X',entry_time='2023-01-01T00:00Z',exit_time='2023-01-15T00:00Z',strategy_R=1.),dict(source_trade_id='b',lifecycle='baseline',instrument='X',entry_time='2023-03-01T00:00Z',exit_time='2023-03-15T00:00Z',strategy_R=-1.)])
    m=period_returns(simulate_events(t,1,.1,('baseline',)),start='2023-01',end='2023-03'); vals=m[m.freq=='M'].ret.tolist()
    assert vals[0]>0 and vals[1]==0 and vals[2]<0
    assert np.mean(np.array(vals)>0)==1/3

def test_exposure_exit_precedes_entry_and_wf_isolation():
    t=_trades([dict(source_trade_id='a',lifecycle='baseline',instrument='X',entry_time='2023-01-01T00:00Z',exit_time='2023-01-02T00:00Z',strategy_R=1.),dict(source_trade_id='b',lifecycle='historical_true_oos',instrument='X',entry_time='2023-01-02T00:00Z',exit_time='2023-01-03T00:00Z',strategy_R=1.),dict(source_trade_id='wf',lifecycle='walk_forward',instrument='X',entry_time='2023-01-01T00:00Z',exit_time='2023-01-03T00:00Z',strategy_R=100.)])
    a=exposure(t,1,.1); b=exposure(t[t.lifecycle!='walk_forward'],1,.1)
    assert a['max_simultaneous_positions']==1 and a==b

def test_zero_availability_and_authenticated_quarters():
    iy=pd.read_csv(HERE/'instrument_year_R_metrics.csv'); z=iy[(iy.configuration_id=='TRAIL1__N2_03')&(iy.instrument=='IMOEXF')&(iy.lifecycle=='baseline')&(iy.year==2023)]
    assert set(z.classification)=={'PARTIAL_YEAR_ZERO'} and set(z.availability_status)=={'AVAILABLE_ZERO_TRADES'}
    a=pd.read_csv(HERE/'instrument_availability_registry.csv').set_index(['instrument','lifecycle'])
    assert a.loc[('USDRUBF','historical_true_oos'),'first_complete_quarter']=='2025Q1'
    assert a.loc[('USDRUBF','historical_true_oos'),'final_complete_quarter']=='2026Q2'

@pytest.mark.parametrize('filename,column',[
    ('quarter_stability_summary.csv','complete_quarters'),
    ('master_220_equity_cases.csv','zero_months'),
    ('instrument_year_R_metrics.csv','classification'),
    ('open_risk_summary.csv','max_reserved_risk_pct_of_equity'),
    ('master_220_equity_cases.csv','target_classification'),
    ('master_220_equity_cases.csv','reference_rank'),
])
def test_auditor_rejects_mutated_producer_fields(tmp_path,filename,column):
    for p in HERE.iterdir():
        if p.suffix in ('.csv','.json','.md'): shutil.copy2(p,tmp_path/p.name)
    p=tmp_path/filename; f=pd.read_csv(p)
    if column in ('classification','target_classification'): f.loc[0,column]='MUTATED'
    else: f.loc[0,column]=999999
    f.to_csv(p,index=False)
    with pytest.raises(AssertionError): audit(tmp_path)
