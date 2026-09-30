from pathlib import Path
import shutil, tempfile
import pandas as pd
from audit_four_case_test import audit
from generate_four_case_test import CORE, generate

HERE=Path(__file__).parent
def test_registry_and_audit():
    r=pd.read_csv(HERE/'four_case_registry.csv'); assert len(r)==4 and set(r.basket)=={'N4_01'} and set(r.load)=={'FULL'}
    assert audit(HERE,False)['status']=='PASS'
def test_deterministic_isolated_generation():
    with tempfile.TemporaryDirectory() as a,tempfile.TemporaryDirectory() as b: assert generate(Path(a))==generate(Path(b))
def test_semantic_mutations_are_detected():
    mutations=[('production_yearly_metrics.csv','return_pct'),('headline_comparison.csv','CAGR_2024_plus_pct'),('headline_comparison.csv','max_realized_equity_DD_2024_plus_pct'),('production_monthly_metrics.csv','return_pct'),('production_quarterly_metrics.csv','return_pct'),('trade_metrics.csv','trades_2024'),('instrument_summary.csv','contribution_share'),('open_risk_summary.csv','time_weighted_avg_open_risk_pct'),('wf24_open_risk_summary.csv','time_weighted_avg_open_risk_pct'),('pairwise_comparison.csv','delta'),('risk_efficiency_comparison.csv','CAGR_to_abs_MaxDD')]
    for filename,column in mutations:
        with tempfile.TemporaryDirectory() as d:
            dst=Path(d); [shutil.copy(HERE/n,dst/n) for n in CORE]
            x=pd.read_csv(dst/filename); x[column]=x[column].astype(float); x.loc[0,column]=float(x.loc[0,column])+0.01; x.to_csv(dst/filename,index=False)
            r=audit(dst,False); assert r['status']=='FAIL' and any(filename in e for e in r['errors'])
