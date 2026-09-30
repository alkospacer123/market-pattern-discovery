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
