import json
from pathlib import Path
import shutil

import pandas as pd
import pytest

from TradingSystemLab.audit_phase2_v2 import (
    BASELINES, EXPECTED_COUNTS, INSTRUMENTS, SPACES, STUDIES, T2_SPACE, T3_SPACE,
    audit, build_manifest, classify, expected_design, immediate_neighbors,
)


ROOT = Path("TradingSystemLab/results/optimization_v2")


def test_exact_four_study_scope_counts_and_spaces():
    assert STUDIES == (("T2", "M30"), ("T2", "H1"),
                       ("T3", "M30"), ("T3", "H1"))
    assert EXPECTED_COUNTS == {"T2": 19, "T3": 22}
    assert sum(EXPECTED_COUNTS[strategy] for strategy, _ in STUDIES) == 82
    assert T2_SPACE == {
        "ema_fast": [15, 20, 25, 30], "ema_trend": [40, 50, 60],
        "ema_slow": [150, 200, 250], "adx_threshold": [15, 20, 25, 30],
        "impulse_distance_atr": [0.3, 0.5, 0.7], "confirmation_window": [2, 3, 4],
        "max_initial_stop_atr": [2.0, 2.5, 3.0], "trailing_atr": [2.0, 3.0, 4.0]}
    assert T3_SPACE == {
        "ema_period": [50, 75, 100, 150, 200], "adx_threshold": [15, 20, 25, 30],
        "breakout_period": [10, 20, 30, 40, 55],
        "atr_average_period": [10, 20, 30, 50], "stop_atr": [1.5, 2.0, 2.5, 3.0],
        "trail_atr": [2.0, 2.5, 3.0, 3.5, 4.0]}


def test_oat_design_has_one_baseline_and_one_factor_deviations():
    for strategy in ("T2", "T3"):
        design, baseline = expected_design(strategy), BASELINES[strategy]
        assert len(design) == EXPECTED_COUNTS[strategy]
        assert design.count(baseline) == 1
        assert all(sum(row[name] != baseline[name] for name in SPACES[strategy]) == 1
                   for row in design if row != baseline)


def test_independent_immediate_neighbors_and_plateau_rule():
    space, configs = {"x": [1, 2, 3]}, [{"x": 1}, {"x": 2}, {"x": 3}]
    assert immediate_neighbors(configs, 1, space) == [0, 2]
    results = [{"configuration_id": str(i), "expectancy_C1": value}
               for i, value in enumerate((0.066, 0.1, 0.134))]
    rows, overall = classify(configs, results, space)
    assert rows[1]["stability_tolerance"] == pytest.approx(0.035)
    assert rows[1]["stable_positive_neighbors"] == 2
    assert rows[1]["classification"] == overall == "ROBUST_PLATEAU"
    results[0]["expectancy_C1"] = 0.064
    assert classify(configs, results, space)[0][1]["classification"] == "LOCAL_SPIKE"
    results[1]["expectancy_C1"] = 0.02
    assert classify(configs, results, space)[0][1]["stability_tolerance"] == 0.01


def test_inventory_is_canonical_not_performance_sorted_and_selects_no_candidate():
    result = audit(write_outputs=False)
    assert result == {"status": "PHASE_2_OPTIMIZATION_COMPLETE", "studies": 4,
                      "configurations": 82, "failures": []}
    manifest = json.loads((ROOT / "manifest.json").read_text()) if (ROOT / "manifest.json").exists() else build_manifest(True, [])
    assert manifest["candidate_selection"] is False
    assert "candidate_id" not in manifest and "winner" not in manifest and "ranking_score" not in manifest
    if (ROOT / "robust_plateau_inventory.csv").exists():
        inventory = pd.read_csv(ROOT / "robust_plateau_inventory.csv")
        observed = list(zip(inventory.strategy, inventory.timeframe))
        assert observed == sorted(observed, key=lambda item: (("T2", "T3").index(item[0]),
                                                              ("M30", "H1").index(item[1])))
        assert not inventory["PF_C1"].is_monotonic_decreasing


def test_complete_manifest_is_fail_closed():
    manifest = build_manifest(False, ["deliberate test failure"])
    assert manifest["status"] == "PHASE_2_OPTIMIZATION_AUDIT_FAILED"
    assert manifest["failed_checks"] == ["deliberate test failure"]


def test_corrupt_artifact_cannot_generate_complete_root_manifest(tmp_path):
    copied = tmp_path / "optimization_v2"
    copied.mkdir()
    shutil.copytree(ROOT / "T2", copied / "T2")
    shutil.copytree(ROOT / "T3", copied / "T3")
    parameters = copied / "T2" / "M30" / "parameters.csv"
    frame = pd.read_csv(parameters)
    frame.loc[0, "ema_fast"] = 999
    frame.to_csv(parameters, index=False)
    result = audit(output_root=copied, write_outputs=True)
    manifest = json.loads((copied / "manifest.json").read_text())
    assert result["status"] == manifest["status"] == "PHASE_2_OPTIMIZATION_AUDIT_FAILED"
    assert manifest["failed_checks"]
    assert tuple(manifest["instruments"]) == INSTRUMENTS
