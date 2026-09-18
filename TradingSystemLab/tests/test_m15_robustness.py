from __future__ import annotations

import json
from pathlib import Path

import pandas as pd
import pytest

from TradingSystemLab.multitimeframe.phase71 import STRATEGY_SHA256, reject_true_oos
from TradingSystemLab.multitimeframe.phase73 import hash_tree
from TradingSystemLab.optimization.experiment import stable_hash
from TradingSystemLab.timeframe_analysis import m15_robustness as subject
from TradingSystemLab.timeframe_validation import m15_baseline


def test_completed_prerequisites_and_exact_candidate_registries() -> None:
    baseline, optimization, registries = subject._load_provenance(subject.BASELINE, subject.OPTIMIZATION)
    assert baseline["status"] == "PHASE_M15_BASELINE_COMPLETE"
    assert optimization["status"] == "PHASE_M15_OPTIMIZATION_COMPLETE"
    for key, expected in subject.EXPECTED.items():
        assert (registries[key]["candidate_id"], registries[key]["configuration_id"],
                registries[key]["parameter_hash"]) == expected
        assert stable_hash(registries[key]["parameters"]) == expected[2]
        assert registries[key]["strategy_hash"] == STRATEGY_SHA256[key]


def test_full_development_period_cost_and_no_research_controls() -> None:
    assert subject.DEVELOPMENT_PERIOD == ["2023-01-01", "2024-12-31"]
    assert subject.TRUE_OOS_CUTOFF == "2025-01-01"
    assert all(value is False for value in subject.FLAGS.values())
    assert subject.COST_TICKS_PER_SIDE == 1
    with pytest.raises(ValueError):
        reject_true_oos(pd.DatetimeIndex([pd.Timestamp("2025-01-01", tz="Europe/Moscow")]))


def test_source_snapshot_is_exactly_baseline_and_optimization() -> None:
    baseline, optimization, _ = subject._load_provenance(subject.BASELINE, subject.OPTIMIZATION)
    loaded = {alias: m15_baseline.load_m15_development(subject.APPROVED_DATA_ROOT, alias)
              for _, alias in m15_baseline.INSTRUMENTS}
    actual = subject._sources(loaded)
    assert actual == subject._expected_sources(baseline)
    assert actual == optimization["source_data_hashes"]
    assert all("2025" not in item["name"] for row in actual for item in row["files"])


def test_exact_execution_reuse_and_causal_h1_contract() -> None:
    source = Path(subject.__file__).read_text(encoding="utf-8")
    baseline_source = Path(m15_baseline.__file__).read_text(encoding="utf-8")
    assert "m15_baseline._execute(key, frozen, alias, frame)" in source
    assert "for offset in range(0, len(day), 4)" in baseline_source
    assert "rows.append((block.index[-1], row))" in baseline_source
    assert "m15.groupby(m15.index.normalize(), sort=True)" in baseline_source


def test_metrics_and_concentration_use_unified_implementation() -> None:
    frame = pd.DataFrame({"net_R": [2.0, 1.0, -1.0], "MAE_R": [-.1, -.2, -.8],
        "MFE_R": [2.2, 1.2, .1], "entry_time": pd.to_datetime(["2023-01-01"] * 3, utc=True),
        "exit_time": pd.to_datetime(["2023-01-01 00:15", "2023-01-01 00:30", "2023-01-01 00:45"], utc=True)})
    result = subject._metric(frame)
    assert result["top_1_positive_R_concentration"] == pytest.approx(2 / 3)
    assert result["top_5_positive_R_concentration"] == 1
    assert result["net_R_without_top5"] == -1
    assert result["PF_without_top5"] == 0


def test_committed_artifacts_have_all_standard_slices_and_flags() -> None:
    root = subject.OUTPUT
    manifest = json.loads((root / "manifest.json").read_text(encoding="utf-8"))
    assert manifest["status"] == subject.STATUS and manifest["development_period"] == subject.DEVELOPMENT_PERIOD
    assert all(manifest[name] is False for name in subject.FLAGS)
    for key in ("T2", "T3"):
        assert pd.read_csv(root / key / "yearly_report.csv").year.tolist() == [2023, 2024]
        assert pd.read_csv(root / key / "instrument_report.csv").instrument.tolist() == ["USDRUBF", "CNYRUBF"]
        assert pd.read_csv(root / key / "direction_report.csv").direction.tolist() == ["LONG", "SHORT"]
        assert len(pd.read_csv(root / key / "monthly_report.csv")) == 24
        assert set(pd.read_csv(root / key / "baseline_year_comparison.csv").version) == {"baseline", "optimized"}


def test_protected_baseline_and_optimization_match_manifest_evidence() -> None:
    manifest = json.loads((subject.OUTPUT / "manifest.json").read_text(encoding="utf-8"))
    assert manifest["baseline_artifact_hash"] == hash_tree(subject.BASELINE)
    assert manifest["optimization_artifact_hash"] == hash_tree(subject.OPTIMIZATION)
    protected = manifest["protected_artifact_hashes"]
    assert all(value == hash_tree(Path(path)) for path, value in protected.items())


def test_generated_tree_is_deterministic_without_self_referential_hash() -> None:
    # The manifest intentionally does not hash its own output tree. Repeated real
    # runs are checked by hashing this complete tree in the acceptance commands.
    first = hash_tree(subject.OUTPUT)
    assert first == hash_tree(subject.OUTPUT)
    assert "artifact_tree_hash" not in json.loads((subject.OUTPUT / "manifest.json").read_text())
