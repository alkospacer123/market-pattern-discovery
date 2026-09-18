from __future__ import annotations

import json
from pathlib import Path

import pandas as pd
import pytest

from TradingSystemLab.multitimeframe.phase71 import STRATEGY_SHA256, reject_true_oos
from TradingSystemLab.multitimeframe.phase73 import hash_tree
from TradingSystemLab.optimization.experiment import stable_hash
from TradingSystemLab.optimization.m15 import (
    BASELINES, BASELINE_ROOT, EXPECTED_CONFIGURATIONS, OPTIMIZATION_END,
    OPTIMIZATION_START, PROTECTED, RANGES, _metrics, _neighbors, _plateau,
    baseline_candidates, bounded_design, run,
)
from TradingSystemLab.timeframe_validation import m15_baseline


def test_baseline_provenance_and_frozen_hashes() -> None:
    assert baseline_candidates() == BASELINES
    manifest = json.loads((BASELINE_ROOT / "manifest.json").read_text())
    assert manifest["development_period"] == ["2023-01-01", "2024-12-31"]
    assert manifest["frozen_strategy_hashes"] == STRATEGY_SHA256
    for key in BASELINES:
        assert manifest["parameter_hashes"][key] == stable_hash(BASELINES[key]["parameters"])


def test_baseline_provenance_fails_closed(tmp_path: Path) -> None:
    manifest = json.loads((BASELINE_ROOT / "manifest.json").read_text())
    manifest["optimization"] = True
    path = tmp_path / "manifest.json"
    path.write_text(json.dumps(manifest))
    with pytest.raises(RuntimeError, match="M15_BASELINE_PROVENANCE_INVALID"):
        baseline_candidates(path)


def test_full_period_and_true_oos_rejection() -> None:
    assert OPTIMIZATION_START == pd.Timestamp("2023-01-01", tz="Europe/Moscow")
    assert OPTIMIZATION_END == pd.Timestamp("2025-01-01", tz="Europe/Moscow")
    with pytest.raises(ValueError):
        reject_true_oos(pd.DatetimeIndex([pd.Timestamp("2025-01-01", tz="Europe/Moscow")]))


def test_approved_ranges_and_exact_one_factor_design() -> None:
    assert RANGES == {
        "T2": {"ema_fast": [15, 20, 25, 30], "ema_trend": [40, 50, 60],
            "ema_slow": [150, 200, 250], "adx_threshold": [15, 20, 25, 30],
            "impulse_distance_atr": [.3, .5, .7], "confirmation_window": [2, 3, 4],
            "max_initial_stop_atr": [2, 2.5, 3], "trailing_atr": [2, 3, 4]},
        "T3": {"ema_period": [50, 75, 100, 150, 200], "adx_threshold": [15, 20, 25, 30],
            "breakout_period": [10, 20, 30, 40, 55], "atr_average_period": [10, 20, 30, 50],
            "stop_atr": [1.5, 2, 2.5, 3], "trail_atr": [2, 2.5, 3, 3.5, 4]},
    }
    for key, baseline_row in BASELINES.items():
        baseline = baseline_row["parameters"]
        design = bounded_design(key, baseline)
        assert len(design) == EXPECTED_CONFIGURATIONS[key]
        assert len(design) == 1 + sum(len(values) - 1 for values in RANGES[key].values())
        assert all(sum(row[name] != baseline[name] for name in baseline) <= 1 for row in design)
        assert len(design) < 5000  # explicit bounded, never Cartesian
        assert len(design) < __import__("math").prod(map(len, RANGES[key].values()))


def test_neighbors_and_robust_plateau_methodology() -> None:
    configs = bounded_design("T2", BASELINES["T2"]["parameters"])
    results = [{"configuration_id": str(i), "expectancy_R": .1} for i in range(len(configs))]
    plateau, _ = _plateau("T2", configs, results)
    for i, row in enumerate(plateau):
        expected = "ROBUST_PLATEAU" if len(_neighbors(configs, i, "T2")) >= 2 else "LOCAL_PEAK"
        assert row["classification"] == expected


def test_optimization_reuses_exact_m15_execution_and_context() -> None:
    import TradingSystemLab.optimization.m15 as module
    assert module._execute is m15_baseline._execute
    source = Path(m15_baseline.__file__).read_text()
    assert "causal_h1_context(m15)" in source
    assert "for offset in range(0, len(day), 4)" in source


def test_unified_metrics_include_required_fields() -> None:
    trades = pd.DataFrame({"net_R": [1.0, -0.5], "MAE_R": [-.2, -.7], "MFE_R": [1.2, .1],
        "entry_time": pd.to_datetime(["2024-01-01", "2024-01-02"], utc=True),
        "exit_time": pd.to_datetime(["2024-01-01 00:15", "2024-01-02 00:30"], utc=True)})
    metric = _metrics("x", trades)
    required = {"trades", "PF", "expectancy_R", "net_R", "max_drawdown_R", "recovery_factor",
        "win_rate", "average_holding_minutes", "losing_streak", "average_MAE_R", "average_MFE_R",
        "concentration_top_1", "concentration_top_5", "top_five_trade_dependency_net_R",
        "top_five_trade_dependency_PF"}
    assert required <= metric.keys()


def test_empty_run_is_deterministic_and_preserves_research(tmp_path: Path, monkeypatch) -> None:
    import TradingSystemLab.optimization.m15 as module
    monkeypatch.setattr(module, "load_m15_development", lambda *_: (None, []))
    protected_before = {str(path): hash_tree(path) for path in PROTECTED}
    output = tmp_path / "M15"
    first_result = run(output=output)
    first_hash = hash_tree(output)
    second_result = run(output=output)
    assert first_result == second_result
    assert first_hash == hash_tree(output)
    assert protected_before == {str(path): hash_tree(path) for path in PROTECTED}
    assert first_result["status"] == "PHASE_M15_OPTIMIZATION_COMPLETE"
    assert [row["candidate_id"] for row in first_result["strategies"]] == [
        "T2_M15_candidate_v1", "T3_M15_candidate_v1"]
    assert all(row["selection_status"] == "BASELINE_FALLBACK_NO_QUALIFYING_PLATEAU"
               for row in first_result["strategies"])
    for key in ("T2", "T3"):
        registry = json.loads((output / key / "candidate_registry.json").read_text())
        assert registry["parameter_hash"] == stable_hash(registry["parameters"])
