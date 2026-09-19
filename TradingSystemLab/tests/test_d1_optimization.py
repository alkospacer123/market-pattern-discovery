from __future__ import annotations

import inspect
import json
from pathlib import Path
import shutil

import pandas as pd
import pytest

import TradingSystemLab.optimization.d1 as d1
from TradingSystemLab.optimization.experiment import stable_hash
from TradingSystemLab.timeframe_validation import d1_baseline as baseline


def test_standalone_architecture_and_methodological_contract() -> None:
    source = inspect.getsource(d1)
    assert d1.PHASE == "D1_OPTIMIZATION"
    assert d1.METHODOLOGICAL_SOURCE == "H1_PHASE_3_2"
    assert d1.CANONICAL_BASELINE_MERGE == "132c64158a7a28dbe66a1e2bbd2629dc3144eb01"
    for forbidden in ("optimization.h4", "optimization.m30", "optimization.m15", "optimization.m5"):
        assert forbidden not in source
    assert "d1_baseline as baseline" in source
    assert d1.SPACES == {
        "T2": {"ema_fast": [15, 20, 25, 30], "ema_trend": [40, 50, 60],
               "ema_slow": [150, 200, 250], "adx_threshold": [15, 20, 25, 30],
               "impulse_distance_atr": [.3, .5, .7], "confirmation_window": [2, 3, 4],
               "max_initial_stop_atr": [2., 2.5, 3.], "trailing_atr": [2., 3., 4.]},
        "T3": {"ema_period": [50, 75, 100, 150, 200], "adx_threshold": [15, 20, 25, 30],
               "breakout_period": [10, 20, 30, 40, 55], "atr_average_period": [10, 20, 30, 50],
               "stop_atr": [1.5, 2., 2.5, 3.], "trail_atr": [2., 2.5, 3., 3.5, 4.]}}


@pytest.mark.parametrize(("key", "count"), [("T2", 19), ("T3", 22)])
def test_exact_centers_hashes_and_oat_design(key: str, count: int) -> None:
    configs = d1.bounded_design(key)
    center = baseline.EXPECTED[key]["parameters"]
    assert len(configs) == count and configs.count(center) == 1
    assert stable_hash(center) == baseline.EXPECTED[key]["parameter_hash"]
    assert all(sum(row[name] != center[name] for name in d1.SPACES[key]) <= 1 for row in configs)
    assert baseline.EXPECTED["T3"]["parameters"]["ema_period"] == 75
    baseline.verify_frozen_strategies()


def test_exact_immediate_neighbor_definition() -> None:
    configs = d1.bounded_design("T2")
    center = baseline.EXPECTED["T2"]["parameters"]
    index = configs.index(center)
    neighbors = [configs[item] for item in d1.immediate_neighbors(configs, index, "T2")]
    # Every center parameter has its adjacent lower and upper level.
    assert len(neighbors) == 16
    assert all(sum(row[name] != center[name] for name in d1.SPACES["T2"]) == 1 for row in neighbors)
    assert {row["ema_fast"] for row in neighbors if row["ema_fast"] != 20} == {15, 25}
    assert not any(row["ema_fast"] == 30 for row in neighbors)


def test_exact_plateau_rules() -> None:
    configs = [{"x": 0}, {"x": 1}, {"x": 2}]
    original = d1.SPACES
    d1.SPACES = {**original, "X": {"x": [0, 1, 2]}}
    try:
        def analyze(values: list[float | None]) -> list[str]:
            results = [{"configuration_id": str(i), "expectancy_C1": value, "PF_C1": 1}
                       for i, value in enumerate(values)]
            return [row["classification"] for row in d1.classify(configs, results, "X")[0]]
        assert analyze([.07, .08, .09]) == ["LOCAL_SPIKE", "ROBUST_PLATEAU", "LOCAL_SPIKE"]
        assert analyze([-.1, 0, None]) == ["NO_EDGE", "NO_EDGE", "NO_EDGE"]
        # 35% threshold, bounded below by 0.01.
        rows = [{"configuration_id": str(i), "expectancy_C1": value, "PF_C1": 1}
                for i, value in enumerate([.001, .009, .011])]
        report = d1.classify(configs, rows, "X")[0]
        assert report[0]["stability_threshold"] == .01
    finally:
        d1.SPACES = original


def test_c1_only_metrics_include_empty_slices_and_concentration() -> None:
    trades = pd.DataFrame([{"net_R": .8, "instrument": "USDRUBF", "direction": "LONG",
                            "exit_time": "2023-01-01T10:00:00Z"}])
    row = d1.metric_row("x", trades)
    assert row["net_R_C1"] == .8 and row["instrument_CNYRUBF_trades"] == 0
    assert row["year_2024_trades"] == 0 and row["direction_SHORT_trades"] == 0
    assert "top_1_positive_R_share" in row
    assert not any("C0" in name or "C05" in name or "C2" in name for name in row)


def test_source_provenance_changed_missing_unexpected_and_fail_before_execution(
        tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    manifest = json.loads((d1.BASELINE_ROOT / "manifest.json").read_text())
    monkeypatch.setattr(d1, "_git", lambda *args: "")
    monkeypatch.setattr(baseline, "verify_frozen_strategies", lambda *_: None)
    monkeypatch.setattr(baseline, "frozen_candidates", lambda *_: {
        key: {**baseline.EXPECTED[key]} for key in ("T2", "T3")})
    root = tmp_path / "data"
    files = {}
    for item in manifest["source_files"]:
        path = root / "2026" / item["alias"] / item["filename"]
        path.parent.mkdir(parents=True, exist_ok=True); path.write_text(item["sha256"])
        files[item["alias"], item["filename"]] = path
    frames = {alias: pd.DataFrame(index=pd.DatetimeIndex([], tz="UTC")) for alias in ("Si", "CNY")}
    def loader(_root: Path, alias: str):
        paths = sorted((root / "2026" / alias).glob("*.csv"), key=lambda path: path.name)
        return frames[alias], paths
    monkeypatch.setattr(baseline, "load_h1_development", loader)
    # Hashes necessarily differ from the audited inventory: hard fail before execution.
    called = False
    def forbidden(*_args):
        nonlocal called; called = True
    monkeypatch.setattr(d1, "_execute", forbidden)
    with pytest.raises(RuntimeError, match="SOURCE_HASH_MISMATCH"):
        d1.run(data_root=root, output=tmp_path / "out")
    assert not called
    # Missing and unexpected files fail through the same closed gate.
    next(iter(files.values())).unlink()
    with pytest.raises(RuntimeError, match="SOURCE_HASH_MISMATCH"):
        d1.verify_baseline_prerequisite(data_root=root)
    extra = root / "2026" / "Si" / "Si_H1_2024_Q4.csv"; extra.write_text("unexpected")
    with pytest.raises(RuntimeError, match="SOURCE_HASH_MISMATCH"):
        d1.verify_baseline_prerequisite(data_root=root)


def test_full_period_execution_semantics_and_true_oos_barrier() -> None:
    source = inspect.getsource(d1)
    assert '["2023-01-01", "2024-12-31"]' in source
    assert "baseline._execute" in source
    baseline.reject_true_oos(pd.DatetimeIndex(["2024-12-31T20:00:00Z"]))
    with pytest.raises(ValueError, match="TRUE_OOS"):
        baseline.reject_true_oos(pd.DatetimeIndex(["2025-01-01T00:00:00Z"]))
    baseline_source = inspect.getsource(baseline._execute)
    assert "causal_d1(h1)" in baseline_source and "causal_4d(execution)" in baseline_source


def test_committed_artifact_contract_and_determinism() -> None:
    root_manifest = json.loads((d1.OUTPUT / "manifest.json").read_text())
    assert root_manifest["status"] == d1.STATUS
    assert root_manifest["baseline_parity"] == {"T2": "EXACT", "T3": "EXACT"}
    assert root_manifest["tested_configurations"] == {"T2": 19, "T3": 22}
    assert root_manifest["source_files"] == json.loads((d1.BASELINE_ROOT / "manifest.json").read_text())["source_files"]
    for flag in ("cartesian_grid", "ranking", "selection", "winner_selection", "robustness",
                 "walk_forward", "parameter_space_expansion", "strategy_change"):
        assert root_manifest[flag] is False
    assert root_manifest["one_factor_at_a_time"] and root_manifest["true_oos_blocked"]
    assert not (d1.OUTPUT / "candidate_registry.json").exists()
    for key, count in (("T2", 19), ("T3", 22)):
        parameters = pd.read_csv(d1.OUTPUT / key / "parameters.csv")
        results = pd.read_csv(d1.OUTPUT / key / "results.csv")
        assert len(parameters) == len(results) == count
        assert parameters.baseline_configuration.sum() == 1
        center = results.loc[results.configuration_id == parameters.loc[
            parameters.baseline_configuration, "configuration_id"].iloc[0]].iloc[0]
        for name, expected in d1.EXPECTED_METRICS[key].items():
            assert center[name] == pytest.approx(expected)
