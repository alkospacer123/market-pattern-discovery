from __future__ import annotations

import hashlib
from pathlib import Path

import pandas as pd
import pytest

from TradingSystemLab.core.unified_metrics import (break_even_round_trip_ticks,
    concentration, max_drawdown, profit_factor, stats, streaks)
from TradingSystemLab.run_unified_baseline_audit import (OUT, SPECS, apply_cost,
    parameter_hash, registry, reject_true_oos)


def test_registry_is_exactly_the_six_frozen_strategies():
    assert [row["strategy_key"] for row in registry()] == ["T1", "T2", "T3", "R1", "R2", "R3"]
    assert len(SPECS) == 6
    assert all(Path(row["config_path"]).is_file() for row in registry())


def test_parameter_hash_is_content_deterministic():
    for row in registry():
        path = Path(row["config_path"])
        assert parameter_hash(path) == hashlib.sha256(path.read_bytes()).hexdigest()


def test_corrected_cost_units_and_scenario_identity():
    source = pd.DataFrame({"trade_id":["x"],"initial_risk_ticks":[20.],"gross_R":[1.]})
    identities=[]
    for ticks in (0,.5,1,2):
        result=apply_cost(source,ticks); identities.append(result.trade_id.tolist())
    assert identities == [["x"]]*4
    assert apply_cost(source,1).iloc[0].cost_R == .1
    assert {row["strategy_key"] for row in registry()} == set(SPECS)


def test_r_metrics_formulas():
    values=pd.Series([2.,-1.,-1.,3.,-1.])
    assert profit_factor(values) == pytest.approx(5/3)
    assert stats(values)["expectancy"] == .4
    assert max_drawdown(values) == -2
    assert stats(values)["recovery_factor"] == 1
    assert streaks(values) == (1,2)


def test_profit_concentration_and_leave_top():
    result=concentration(pd.Series([4.,2.,-3.,-1.]))
    assert result["top_1_positive_R_share"] == pytest.approx(2/3)
    assert result["net_R_without_best_trade"] == -2
    assert result["expectancy_C1_without_top3"] == -2


def test_break_even_uses_individual_risk_ticks():
    assert break_even_round_trip_ticks(pd.Series([1.,1.]),pd.Series([10.,20.])) == pytest.approx(2/.15)
    assert break_even_round_trip_ticks(pd.Series([-1.]),pd.Series([10.])) is None


def test_true_oos_is_rejected():
    bad=pd.DataFrame({"entry_time":["2024-12-31T23:00:00Z"],"exit_time":["2025-01-01T00:00:00Z"]})
    with pytest.raises(ValueError,match="TRUE OOS"): reject_true_oos(bad)


@pytest.mark.parametrize("key", SPECS)
def test_frozen_parity_artifact_passes(key):
    parity=pd.read_csv(OUT/"parity_report.csv").set_index("strategy")
    assert parity.loc[key,"status"] == "PASS"
    assert bool(parity.loc[key,"trade_identity_match"])


def test_outputs_are_text_only_and_have_no_ranking_or_optimization():
    allowed={".py",".csv",".json",".md",".svg",".yaml"}
    assert all(path.suffix.lower() in allowed for path in OUT.rglob("*") if path.is_file())
    text="\n".join(path.read_text(encoding="utf-8") for path in OUT.rglob("*") if path.is_file())
    for forbidden in ("strategy_score","ranking_score","weighted_score","best_strategy"):
        assert forbidden not in text
    manifest=(OUT/"manifest.json").read_text()
    assert '"optimization_performed": false' in manifest
    assert '"true_oos_blocked": true' in manifest


def test_breakdowns_and_causal_diagnostics_are_complete():
    assert len(pd.read_csv(OUT/"instrument_report.csv")) == 12
    assert len(pd.read_csv(OUT/"direction_report.csv")) == 12
    assert len(pd.read_csv(OUT/"year_report.csv")) == 12
    mae=pd.read_csv(OUT/"mae_mfe_report.csv")
    assert set(mae.group)=={"ALL","WINNERS","LOSERS"}
    assert len(mae)==18
