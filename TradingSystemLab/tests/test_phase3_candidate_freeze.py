"""Regression contract for the artifact-only Phase 3 candidate freeze."""
from __future__ import annotations

import json
from pathlib import Path

import pytest

from TradingSystemLab.audit_phase3_candidate_freeze import audit
from TradingSystemLab.phase3_candidate_freeze import (
    BASELINES, PREDECLARED_CANDIDATES, STRATEGY_FILES, STRATEGY_HASHES,
    build_registry, stable_hash,
)

ROOT = Path(__file__).resolve().parents[2]
FREEZE = ROOT / "TradingSystemLab/results/phase3_candidate_freeze"


def _registry() -> dict:
    return json.loads((FREEZE / "candidate_registry.json").read_text(encoding="utf-8"))


def _corrupted(tmp_path: Path, mutate) -> Path:
    value = _registry()
    mutate(value)
    target = tmp_path / "registry.json"
    target.write_text(json.dumps(value), encoding="utf-8")
    return target


def test_exact_declarations_order_membership_and_persisted_parameters() -> None:
    records = _registry()["candidates"]
    expected = [
        ("T2_M30_candidate_v2", "T2", "M30", "T2-M30-7c89b4a215cd"),
        ("T2_H1_candidate_v2", "T2", "H1", "T2-H1-a98459cab4f2"),
        ("T3_M30_candidate_v2", "T3", "M30", "T3-M30-0050d828c1a8"),
        ("T3_H1_candidate_v2", "T3", "H1", "T3-H1-aeeb96942cf3"),
    ]
    assert PREDECLARED_CANDIDATES == tuple(expected)
    assert [(r["candidate_id"], r["strategy"], r["timeframe"], r["phase2_configuration_id"])
            for r in records] == expected
    assert build_registry(ROOT) == _registry()
    assert audit(ROOT)["candidate_count"] == 4


def test_hashes_locks_and_strategy_sources_are_deterministic() -> None:
    import hashlib
    for record in _registry()["candidates"]:
        assert stable_hash(record["parameters"]) == record["parameter_hash"]
        assert stable_hash(record["parameters"]) == stable_hash(record["parameters"])
        assert record["canonical_baseline_parameters"] == BASELINES[record["strategy"]]
        assert stable_hash(BASELINES[record["strategy"]]) == record["canonical_baseline_parameter_hash"]
        assert record["selection_locked_before_validation"] is True
        assert record["robustness_executed"] is False
        assert record["walk_forward_executed"] is False
        assert record["true_oos_executed"] is False
        actual = hashlib.sha256((ROOT / STRATEGY_FILES[record["strategy"]]).read_bytes()).hexdigest()
        assert actual == STRATEGY_HASHES[record["strategy"]]


def test_freeze_is_artifact_only_and_contains_no_execution_or_selection_engine() -> None:
    source = (ROOT / "TradingSystemLab/phase3_candidate_freeze.py").read_text(encoding="utf-8")
    manifest = json.loads((FREEZE / "manifest.json").read_text(encoding="utf-8"))
    forbidden_imports = ("Backtester", "load_development", "T2TrendPullback", "T3MTFTrend")
    assert not any(token in source for token in forbidden_imports)
    assert "PREDECLARED_CANDIDATES = (" in source
    for flag in ("raw_market_data_read", "optimization_executed", "parameter_search_executed",
                 "ranking_executed", "robustness_executed", "walk_forward_executed",
                 "true_oos_executed", "phase7_mtf_research"):
        assert manifest[flag] is False
    assert manifest["true_oos_blocked"] is True
    assert manifest["selection_locked_before_validation"] is True


def test_phase1_and_phase2_trees_are_unchanged_from_reference() -> None:
    import subprocess
    protected = ["TradingSystemLab/results/baseline_v2", "TradingSystemLab/results/optimization_v2"]
    result = subprocess.run(["git", "diff", "--exit-code",
                             "9206e2f2ca9a6524ddf78ba473b9b882938aefc6", "--", *protected],
                            cwd=ROOT, capture_output=True, text=True, check=False)
    assert result.returncode == 0, result.stdout + result.stderr


@pytest.mark.parametrize("mutation", [
    lambda data: data["candidates"][0].__setitem__("phase2_configuration_id", "CORRUPTED"),
    lambda data: data["candidates"][0]["parameters"].__setitem__("adx_threshold", 999),
    lambda data: data["candidates"][0].__setitem__("phase2_classification", "LOCAL_SPIKE"),
])
def test_audit_fails_closed_on_registry_corruption(tmp_path: Path, mutation) -> None:
    with pytest.raises(AssertionError):
        audit(ROOT, _corrupted(tmp_path, mutation))
