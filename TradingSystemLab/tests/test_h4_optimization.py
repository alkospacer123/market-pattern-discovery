"""Contract tests for the strict H4 bounded-OAT phase."""
from __future__ import annotations

import json

import pandas as pd

from TradingSystemLab.optimization.experiment import stable_hash
from TradingSystemLab.timeframe_optimization import h4
from TradingSystemLab.timeframe_validation import h4_baseline as baseline


def test_baseline_prerequisite_and_locked_period():
    manifest = json.loads(h4.BASELINE_MANIFEST.read_text())
    assert manifest["status"] == "PHASE_H4_BASELINE_COMPLETE"
    assert manifest["timeframe"] == "H4"
    assert manifest["development_period"] == ["2023-01-01", "2024-12-31"]
    assert manifest["true_oos_cutoff"] == "2025-01-01"
    assert manifest["true_oos_blocked"] is True


def test_frozen_identities_are_exact():
    expected = {
        "T2": ("T2_candidate_v1", "T2-0007-608dc87d09f1", "2b0494cdd24bfbfa8ce7d657d6f83d1408f07b9f565d38d093dec5b4856e3c00",
               "376df085cfda85eefccb31343aad40ed4fbb1078f1314496472a3a4ac9507774"),
        "T3": ("T3_candidate_v1", "T3-0014-0050d828c1a8", "938b6b3b78f680010115a204b9a49e7eef962db119f4ea121e388c00741920ba",
               "840dd3b2cda43fa00259445cd0a22ace6d82e677f4c793028ccc8126f9ad9a8c"),
    }
    manifest = json.loads(h4.BASELINE_MANIFEST.read_text())
    for key, values in expected.items():
        item = baseline.EXPECTED[key]
        assert (item["candidate_id"], item["phase32_configuration_id"], item["parameter_hash"],
                manifest["candidates"][key]["strategy_hash"]) == values
        assert stable_hash(item["parameters"]) == item["parameter_hash"]


def test_exact_h1_phase32_spaces():
    assert h4.SPACES["T2"] == {"ema_fast": [15, 20, 25, 30], "ema_trend": [40, 50, 60],
        "ema_slow": [150, 200, 250], "adx_threshold": [15, 20, 25, 30],
        "impulse_distance_atr": [.3, .5, .7], "confirmation_window": [2, 3, 4],
        "max_initial_stop_atr": [2., 2.5, 3.], "trailing_atr": [2., 3., 4.]}
    assert h4.SPACES["T3"] == {"ema_period": [50, 75, 100, 150, 200],
        "adx_threshold": [15, 20, 25, 30], "breakout_period": [10, 20, 30, 40, 55],
        "atr_average_period": [10, 20, 30, 50], "stop_atr": [1.5, 2., 2.5, 3.],
        "trail_atr": [2., 2.5, 3., 3.5, 4.]}


def test_oat_design_counts_identity_and_determinism():
    for key, count in (("T2", 19), ("T3", 22)):
        first, second = h4.configuration_rows(key), h4.configuration_rows(key)
        assert first == second and len(first) == count
        assert sum(row["baseline_configuration"] for row in first) == 1
        assert len({row["parameter_hash"] for row in first}) == count
        center = baseline.EXPECTED[key]["parameters"]
        assert next({name: row[name] for name in h4.SPACES[key]} for row in first
                    if row["baseline_configuration"]) == center
        for row in first:
            differences = sum(row[name] != center[name] for name in h4.SPACES[key])
            assert differences == (0 if row["baseline_configuration"] else 1)
            assert row["configuration_id"].startswith(f"{key}-H4-")


def test_immediate_neighbor_is_one_adjacent_factor_only():
    configs = h4.bounded_design("T2")
    center = configs.index(baseline.EXPECTED["T2"]["parameters"])
    neighbors = h4.immediate_neighbors(configs, center, "T2")
    assert neighbors
    for index in neighbors:
        differing = [name for name in h4.SPACES["T2"] if configs[index][name] != configs[center][name]]
        assert len(differing) == 1
        name = differing[0]
        values = h4.SPACES["T2"][name]
        assert abs(values.index(configs[index][name]) - values.index(configs[center][name])) == 1


def test_exact_plateau_classification_threshold():
    # threshold is max(.01, abs(.10)*.35) == .035
    assert h4.classify(.10, [.07, .13, -.1]) == (2, 2, "ROBUST_PLATEAU")
    assert h4.classify(.10, [.07, .20]) == (2, 1, "LOCAL_SPIKE")
    assert h4.classify(0.0, [.001, .002]) == (2, 0, "NO_EDGE")
    # absolute floor controls near zero.
    assert h4.classify(.001, [.009, .010]) == (2, 2, "ROBUST_PLATEAU")


def test_c1_only_metrics_and_concentration_columns():
    trades = pd.DataFrame({"net_R": [1., -.5], "symbol": ["Si", "CNY"],
                           "exit_time": ["2023-01-01T00:00:00Z", "2024-01-01T00:00:00Z"],
                           "direction": ["LONG", "SHORT"]})
    row = h4._metrics("x", trades)
    assert row["PF_C1"] == 2.0
    assert "PF_C0" not in row and "PF_C2" not in row
    assert "PF_C1_without_top5" in row


def test_execution_contract_and_no_later_phase_flags():
    source = baseline._execute.__code__.co_names
    assert "T2TrendPullback" in source and "causal_h4" in source and "causal_d1" in source
    assert "Completed Moscow-day candles" in baseline.causal_d1.__doc__
    module_source = h4.Path(h4.__file__).read_text()
    assert '"winner_selection": False' in module_source
    assert '"robustness": False' in module_source
    assert '"walk_forward": False' in module_source
    assert '"true_oos_blocked": True' in module_source


def test_c1_formula_and_direct_frozen_source_protection():
    gross = pd.DataFrame({"net_R": [1 - 2 / 100], "symbol": ["Si"],
                          "exit_time": ["2023-01-01T00:00:00Z"], "direction": ["LONG"]})
    assert h4._metrics("x", gross)["net_R_C1"] == .98
    snapshot = h4.protected_snapshot()
    for path in h4.FROZEN_STRATEGY_FILES:
        assert snapshot[str(path)] == h4._sha(path)
        assert snapshot[str(path)] in baseline.STRATEGY_SHA256.values()


def test_committed_outputs_have_required_deterministic_tree():
    if not h4.OUTPUT.exists():
        return
    required = {"manifest.json", "experiment.json", "parameters.csv", "results.csv",
                "metrics_summary.csv", "plateau_report.csv", "sensitivity_report.csv",
                "best_regions.md", "final_report.md"}
    for key in ("T2", "T3"):
        assert {p.name for p in (h4.OUTPUT / key).iterdir()} == required
    manifest = json.loads((h4.OUTPUT / "manifest.json").read_text())
    assert manifest["cartesian_grid"] is False
    assert manifest["one_factor_at_a_time"] is True
    assert manifest["robustness"] is False
    assert manifest["walk_forward"] is False
