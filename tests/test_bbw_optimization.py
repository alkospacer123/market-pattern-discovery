from __future__ import annotations

import hashlib
import json
from pathlib import Path

import pandas as pd
import pytest

from bbw_system.bbw_engine import OUTPUT_NAME
from bbw_system.optimization.bbw_parameter_search import (
    OptimizationParameters, calculate_candidate_features, calculate_metrics,
    generate_parameter_grid, run_optimization,
)
from bbw_system.optimization.bbw_optimization_r2 import (
    R2_BASELINE, R2_SPACE, generate_r2_parameter_grid, run_r2_optimization,
)


BASELINE = {
    "range_min_bars": 6, "range_max_bars": 30, "range_atr_min": 1.0,
    "range_atr_max": 2.0, "retest_min_bars": 5, "retest_max_bars": 30,
    "penetration_range_pct": .2, "stop_offset": 4.0,
    "tp_levels": [1, 2, 3], "tp_fractions": [.5, .3, .2],
}


def parameters() -> OptimizationParameters:
    return OptimizationParameters(10, 2, 10, 6, 30, 1, 2, 50, .001, 5, 30, .2)


def frames(year: int = 2024) -> tuple[pd.DataFrame, pd.DataFrame]:
    h1_time = pd.date_range(f"{year}-01-03", periods=80, freq="h")
    close = [100 + (index % 7) * .1 for index in range(80)]
    h1 = pd.DataFrame({"timestamp": h1_time, "open": close, "high": [x + 1 for x in close],
        "low": [x - 1 for x in close], "close": close, "volume": 1, "atr14": 2.0})
    m15_time = pd.date_range(f"{year}-01-03", periods=320, freq="15min")
    m15 = pd.DataFrame({"timestamp": m15_time, "open": 100, "high": 101,
                        "low": 99, "close": 100, "volume": 1})
    return h1, m15


def bundle(root: Path) -> tuple[Path, Path, Path]:
    feature, normalized, baseline = root / "features", root / "normalized", root / "baseline"
    feature.mkdir(); (normalized / "CNYRUBF").mkdir(parents=True); baseline.mkdir()
    h1, m15 = frames()
    h1.to_csv(feature / OUTPUT_NAME, index=False)
    m15.to_csv(normalized / "CNYRUBF" / "M15.csv", index=False)
    (baseline / "bbw_baseline.json").write_text(json.dumps(BASELINE))
    return feature, normalized, baseline


def test_grid_is_valid_bounded_and_deterministic() -> None:
    first = generate_parameter_grid(31)
    assert first == generate_parameter_grid(31)
    assert len(first) == 31 and parameters() in first
    assert all(item.range_min_bars <= item.range_max_bars and item.atr_min <= item.atr_max for item in first)
    assert len(generate_parameter_grid(None)) == 419_904


def test_metrics_are_correct_and_cost_aware() -> None:
    trades = pd.DataFrame({"result_R": [2.0, -1.0, 1.0],
        "entry_time": pd.to_datetime(["2024-01-03 01:00"] * 3),
        "exit_time": pd.to_datetime(["2024-01-03 02:00", "2024-01-03 03:00", "2024-01-03 04:00"])})
    result = calculate_metrics(trades)
    assert result["trades"] == 3
    assert result["profit_factor"] == 3
    assert result["total_R"] == 2
    assert result["max_drawdown"] == 1
    assert result["avg_duration"] == 120
    assert calculate_metrics(trades, .1)["total_R"] == pytest.approx(1.7)


def test_candidate_features_are_prefix_causal_and_true_oos_is_blocked() -> None:
    h1, _ = frames()
    expected = calculate_candidate_features(h1.iloc[:60], parameters())
    changed = h1.copy(); changed.loc[60:, "close"] = 999
    actual = calculate_candidate_features(changed, parameters()).iloc[:60]
    pd.testing.assert_series_equal(expected.bbw, actual.bbw)
    future, _ = frames(2025)
    with pytest.raises(ValueError, match="TRUE OOS"):
        calculate_candidate_features(future, parameters())


def test_run_is_deterministic_and_does_not_modify_inputs_or_baseline(tmp_path: Path) -> None:
    feature, normalized, baseline = bundle(tmp_path)
    sources = [feature / OUTPUT_NAME, normalized / "CNYRUBF" / "M15.csv", baseline / "bbw_baseline.json"]
    before = {path: (path.read_bytes(), hashlib.sha256(path.read_bytes()).hexdigest()) for path in sources}
    first = run_optimization(feature, normalized, baseline, tmp_path / "out1", "CNYRUBF", grid=[parameters()])
    second = run_optimization(feature, normalized, baseline, tmp_path / "out2", "CNYRUBF", grid=[parameters()])
    assert first["sha256"] == second["sha256"]
    assert (tmp_path / "out1" / "BBW_OPTIMIZATION_RESULTS.csv").read_bytes() == (tmp_path / "out2" / "BBW_OPTIMIZATION_RESULTS.csv").read_bytes()
    assert (tmp_path / "out1" / "BBW_OPTIMIZATION_REPORT.md").is_file()
    assert all(before[path][0] == path.read_bytes() for path in sources)


def test_run_loads_baseline_config_artifact_with_priority(tmp_path: Path) -> None:
    feature, normalized, baseline = bundle(tmp_path)
    legacy = baseline / "bbw_baseline.json"
    artifact = baseline / "BASELINE_CONFIG.json"
    artifact.write_bytes(legacy.read_bytes())
    legacy.write_text("not valid JSON")

    result = run_optimization(
        feature,
        normalized,
        baseline,
        tmp_path / "out",
        "CNYRUBF",
        grid=[parameters()],
    )

    assert result["combinations"] == 1


def test_r2_grid_is_bounded_deterministic_in_allowed_space_and_includes_baseline() -> None:
    first = generate_r2_parameter_grid()
    assert first == generate_r2_parameter_grid()
    assert len(first) == 1024
    assert R2_BASELINE in first
    for candidate in first:
        for name, allowed in R2_SPACE.items():
            assert getattr(candidate, name) in allowed
    with pytest.raises(ValueError, match="between 500 and 2000"):
        generate_r2_parameter_grid(499)


def test_r2_run_is_separate_deterministic_train_only_and_preserves_baseline(tmp_path: Path) -> None:
    feature, normalized, baseline = bundle(tmp_path)
    baseline_path = baseline / "bbw_baseline.json"
    before = baseline_path.read_bytes()
    # A 500-point real evaluation is unnecessary for this integration check;
    # identical constant-price outcomes still exercise deterministic R2 output.
    first = run_r2_optimization(feature, normalized, baseline, tmp_path / "R2-a", "CNYRUBF",
                                grid_limit=500)
    second = run_r2_optimization(feature, normalized, baseline, tmp_path / "R2-b", "CNYRUBF",
                                 grid_limit=500)
    assert first["combinations"] == 500
    assert first["sha256"] == second["sha256"]
    assert baseline_path.read_bytes() == before
    report = (tmp_path / "R2-a" / "BBW_OPTIMIZATION_REPORT.md").read_text()
    assert "R1 vs R2" in report and "Robustness and Walk Forward were not performed" in report


def test_r2_rejects_true_oos_before_search(tmp_path: Path) -> None:
    feature, normalized, baseline = bundle(tmp_path)
    h1, m15 = frames(2025)
    h1.to_csv(feature / OUTPUT_NAME, index=False)
    m15.to_csv(normalized / "CNYRUBF" / "M15.csv", index=False)
    with pytest.raises(ValueError, match="TRUE OOS"):
        run_r2_optimization(feature, normalized, baseline, tmp_path / "R2", "CNYRUBF",
                            grid_limit=500)
