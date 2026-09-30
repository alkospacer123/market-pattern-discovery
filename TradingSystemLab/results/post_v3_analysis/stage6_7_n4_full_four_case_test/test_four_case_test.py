from pathlib import Path
import ast, shutil, tempfile
import pandas as pd
import pytest
from audit_four_case_test import audit, clean_compare
from generate_four_case_test import CORE, generate, tolerance_compare

HERE=Path(__file__).parent

def test_exact_scientific_universe_and_diagnostic_2023():
    r=pd.read_csv(HERE/'four_case_registry.csv'); assert r.case_id.tolist()==['CANONICAL__N4_01__FULL__R15','TRAIL1__N4_01__FULL__R15','CANONICAL__N4_01__FULL__R20','TRAIL1__N4_01__FULL__R20']
    assert set(r.basket)=={'N4_01'} and set(r.load)=={'FULL'}
    assert not r.astype(str).apply(lambda c:c.str.contains('N2|N3|NORMALIZED|SESSION|LOCK1|STRUCTURAL_STACK').any()).any()
    y=pd.read_csv(HERE/'production_yearly_metrics.csv'); assert (y[y.year==2023].coverage_status=='PARTIAL_N4_DIAGNOSTIC_YEAR').all() and not y.hard_gate_used.any()

def test_clean_room_anti_coupling():
    tree=ast.parse((HERE/'audit_four_case_test.py').read_text())
    imported={a.name for n in ast.walk(tree) if isinstance(n,(ast.Import,ast.ImportFrom)) for a in n.names}
    assert 'generate_four_case_test' not in imported
    assert 'generate' not in {n.id for n in ast.walk(tree) if isinstance(n,ast.Name)}
    assert audit(HERE,False)['status']=='PASS'

def test_calendar_spines_and_partial_periods():
    m=pd.read_csv(HERE/'production_monthly_metrics.csv'); q=pd.read_csv(HERE/'production_quarterly_metrics.csv')
    assert (m.groupby('case_id').size()==33).all() and set(m[m.sign=='ZERO'].month)=={'2025-01'} and (m.groupby('case_id').sign.apply(lambda x:(x=='ZERO').sum())==1).all()
    assert (q.groupby('case_id').size()==11).all() and (q.groupby('case_id').completeness.apply(lambda x:(x=='COMPLETE').sum())==10).all()
    assert (q[(q.case_id.str.startswith('TRAIL1'))&(q.completeness=='COMPLETE')].sign=='POSITIVE').all()

def test_corrected_exposure_and_isolated_wf():
    p=pd.read_csv(HERE/'open_risk_summary.csv').set_index('case_id'); w=pd.read_csv(HERE/'wf24_open_risk_summary.csv')
    expected=[.7969437399,1.0240509307,1.0620576924,1.3641936395]
    assert all(abs(a-b)<.002 for a,b in zip(p.time_weighted_avg_open_risk_pct,expected))
    assert set(p.reporting_window)=={'2024-01-01_to_authenticated_endpoint'} and len(w)==4

def test_risk_trade_path_invariance_and_event_contract():
    h=pd.read_csv(HERE/'headline_comparison.csv'); t=pd.read_csv(HERE/'trade_metrics.csv')
    assert h.max_simultaneous_positions.eq(4).all() and set(h.max_nominal_open_risk_pct)=={6.,8.}
    assert t.set_index('variant').loc['CANONICAL','total_full_history_production_trades']==380
    assert t.set_index('variant').loc['TRAIL1','total_full_history_production_trades']==355
    assert 'EXIT before ENTRY' in (HERE/'audit_manifest.json').read_text()

def test_tolerance_comparisons():
    for fn in (tolerance_compare,clean_compare):
        assert fn(1,1+1e-12)==0 and fn(1,1+1e-10)==0 and fn(1,1+2e-9)==-1

def test_deterministic_isolated_generation_and_dual_audit():
    with tempfile.TemporaryDirectory(prefix='n4-run-a-') as a,tempfile.TemporaryDirectory(prefix='n4-run-b-') as b:
        pa,pb=Path(a),Path(b); assert generate(pa)==generate(pb)
        assert audit(pa,False)['status']==audit(pb,False)['status']=='PASS'

def test_report_has_no_hidden_winner_and_scope_protection_language():
    text=(HERE/'FINAL_N4_FULL_FOUR_CASE_REPORT.md').read_text()
    assert 'balanced production profile' not in text and 'recommended configuration' not in text and 'overall winner' in text
    assert 'Stage 6.8 was not started' in text and 'Stage 7 was not executed' in text

MUTATIONS=[
 ('annual_return','production_yearly_metrics.csv','return_pct','number'),('cagr','headline_comparison.csv','CAGR_2024_plus_pct','number'),('event_dd','headline_comparison.csv','max_realized_equity_DD_2024_plus_pct','number'),('monthly_return','production_monthly_metrics.csv','return_pct','number'),('missing_zero_month','production_monthly_metrics.csv',None,'dropzero'),('quarterly_return','production_quarterly_metrics.csv','return_pct','number'),('quarter_completeness','production_quarterly_metrics.csv','completeness','text'),('production_trade_count','trade_metrics.csv','trades_2024','number'),('instrument_contribution','instrument_summary.csv','contribution_share','number'),('direction_net_r','direction_summary.csv','net_R','number'),('production_exposure','open_risk_summary.csv','time_weighted_avg_open_risk_pct','number'),('wf_exposure','wf24_open_risk_summary.csv','time_weighted_avg_open_risk_pct','number'),('max_positions','open_risk_summary.csv','max_simultaneous_positions','number'),('pairwise_delta','pairwise_comparison.csv','delta','number'),('risk_efficiency','risk_efficiency_comparison.csv','CAGR_to_abs_MaxDD','number'),('case_membership','four_case_registry.csv','case_id','text'),('trade_path_mismatch','trade_metrics.csv','total_full_history_production_trades','number'),('endpoint','availability_registry.csv','end_timestamp','text'),('source_availability','availability_registry.csv','instrument','text'),('leader_tie','headline_comparison.csv','positive_quarter_share','number')]
@pytest.mark.parametrize('category,filename,column,kind',MUTATIONS,ids=[x[0] for x in MUTATIONS])
def test_semantic_mutations(category,filename,column,kind):
    with tempfile.TemporaryDirectory() as d:
        dst=Path(d); [shutil.copy(HERE/n,dst/n) for n in CORE]
        x=pd.read_csv(dst/filename)
        if kind=='dropzero': x=x.drop(x[x.sign=='ZERO'].index[0])
        elif kind=='number':
            x[column]=x[column].astype(float); x.loc[0,column]=float(x.loc[0,column])+0.01
        else: x.loc[0,column]='MUTATED'
        x.to_csv(dst/filename,index=False)
        result=audit(dst,False)
        assert result['status']=='FAIL' and any(filename in error for error in result['errors']),category
