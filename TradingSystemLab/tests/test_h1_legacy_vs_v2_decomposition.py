import json
from dataclasses import asdict
from pathlib import Path
import pandas as pd
from TradingSystemLab.audit_h1_legacy_vs_v2_decomposition import ROOT, audit
from TradingSystemLab.h1_legacy_vs_v2_decomposition import CELLS, PARAMETERS, CUTOFF, START, STRATEGY_HASHES

def test_fixed_design_and_contract():
    assert len(CELLS)==6 and len(CELLS)*2==12
    assert sum(x[3]=="SICNY" for x in CELLS)*2==8 and sum(x[3]=="ALL6" for x in CELLS)*2==4
    assert {x[1] for x in CELLS}=={"LEGACY_CONTINUOUS","QUARTERLY_V2"}
    assert {x[2] for x in CELLS}=={"LEGACY_PARAMS","V2_H1_PARAMS"}
    assert START.isoformat()=="2025-01-01T00:00:00+03:00" and CUTOFF.isoformat()=="2026-08-30T19:00:00+03:00"
    assert PARAMETERS["T2","LEGACY_PARAMS"]["ema_fast"]==20 and PARAMETERS["T2","V2_H1_PARAMS"]["ema_fast"]==25
    assert PARAMETERS["T3","LEGACY_PARAMS"]["ema_period"]==75 and PARAMETERS["T3","V2_H1_PARAMS"]["atr_average_period"]==30

def test_outputs_and_independent_audit():
    assert audit()
    m=json.loads((ROOT/"summary/manifest.json").read_text())
    assert m["parameter_hashes"]=={"T2_V2":"a98459cab4f22e598fbfd705fb60cfb8a65f1771fa7d903bafa581544faa35ea","T3_V2":"aeeb96942cf33d9551b5635f33d2f2745aefad572f57f7ea92b9791c2d992a39"}
    assert m["strategy_hashes"]==STRATEGY_HASHES and m["classification"]=="NOT_APPLICABLE_RETROSPECTIVE_DIAGNOSTIC"
    assert "futures_quarterly" in m["source_paths"]["quarterly_Si"][0] and "/2026/Si/Si_H1_" in m["source_paths"]["legacy_Si"][0]
    assert m["T2_execution"]=="standalone" and "four completed" in m["T3_context"]
    assert not any(m[x] for x in ("optimization","ranking","candidate_selection","portfolio_selection"))

def test_month_grid_and_classification():
    rows=pd.read_csv(ROOT/"summary/monthly_results.csv")
    assert len(rows)==240 and set(rows.month)==set(str(x) for x in pd.period_range("2025-01","2026-08",freq="M"))
    assert set(pd.read_csv(ROOT/"summary/factorial_results.csv").classification)=={"NOT_APPLICABLE_RETROSPECTIVE_DIAGNOSTIC"}
