from __future__ import annotations

from pathlib import Path

import pandas as pd
import pytest

from TradingSystemLab.multitimeframe.phase73 import hash_tree
from TradingSystemLab.optimization.m5 import BASELINES, RANGES, _metrics, bounded_design, run


def test_design_is_only_baseline_plus_one_factor() -> None:
    for key, row in BASELINES.items():
        baseline = row["parameters"]
        design = bounded_design(key, baseline)
        expected = 1 + sum(len(values) - 1 for values in RANGES[key].values())
        assert len(design) == expected
        assert all(sum(config[name] != baseline[name] for name in baseline) <= 1
                   for config in design)


def test_unified_metrics_include_excursions_and_dependency() -> None:
    trades = pd.DataFrame({"net_R": [1.0, -0.5], "MAE_R": [-.2, -.7],
                           "MFE_R": [1.2, .1],
                           "entry_time": pd.to_datetime(["2024-01-01", "2024-01-02"], utc=True),
                           "exit_time": pd.to_datetime(["2024-01-01 00:05", "2024-01-02 00:10"], utc=True)})
    result = _metrics("test", trades)
    assert result["average_MAE_R"] == pytest.approx(-.45)
    assert result["average_MFE_R"] == pytest.approx(.65)
    assert "top_five_trade_dependency_net_R" in result


def test_empty_run_writes_deterministic_required_tree(tmp_path: Path, monkeypatch) -> None:
    import TradingSystemLab.optimization.m5 as module
    monkeypatch.setattr(module, "load_m5_development", lambda *_: (None, []))
    output = tmp_path / "M5"
    assert run(output=output)["status"] == "PHASE_M5_OPTIMIZATION_COMPLETE"
    first = hash_tree(output)
    run(output=output)
    assert first == hash_tree(output)
    assert {p.name for p in output.iterdir()} == {"T2", "T3", "comparison.csv",
        "manifest.json", "m5_optimization_report.md"}
    required = {"optimization_results.csv", "plateau_analysis.csv", "parameter_stability.csv",
        "baseline_vs_optimized.csv", "candidate_registry.json", "metrics.json", "final_report.md"}
    assert {p.name for p in (output / "T2").iterdir()} == required
    manifest = (output / "manifest.json").read_text()
    assert '"optimization": true' in manifest
    assert '"true_oos_blocked": true' in manifest
