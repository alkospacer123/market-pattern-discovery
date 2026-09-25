"""Regression contracts for frozen-candidate Phase 3 robustness v2."""
from __future__ import annotations

import inspect
import json
from pathlib import Path

import pandas as pd

from TradingSystemLab.baseline_v2 import FROZEN_TICK_SIZE, four_bar_context
from TradingSystemLab.robustness import phase3_v2 as phase

ROOT = Path("TradingSystemLab/results/robustness_v2")


def test_registry_is_the_only_frozen_candidate_source() -> None:
    candidates, _ = phase.load_frozen_registry()
    assert phase.REGISTRY_PATH.as_posix().endswith("phase3_candidate_freeze/candidate_registry.json")
    assert [(x["strategy"], x["timeframe"]) for x in candidates] == list(phase.STUDIES)
    assert [(x["candidate_id"], x["parameter_hash"]) for x in candidates] == [phase.EXPECTED_IDS[x] for x in phase.STUDIES]
    assert all(x["selection_locked_before_validation"] for x in candidates)


def test_no_selection_replacement_ranking_or_optimization_primitive() -> None:
    source = inspect.getsource(phase.run)
    assert "load_frozen_registry" in source
    for forbidden in ("select_candidate", "replace_candidate", "rank_candidates", "optimize"):
        assert forbidden not in source


def test_fixed_universe_period_cost_and_bootstrap() -> None:
    assert phase.STUDIES == (("T2", "M30"), ("T2", "H1"), ("T3", "M30"), ("T3", "H1"))
    assert phase.INSTRUMENTS == ("Si", "CNY", "GD", "BR", "MIX", "NG")
    assert phase.DEVELOPMENT_PERIOD == ("2020-01-01", "2024-12-31")
    assert str(phase.TRUE_OOS_START.date()) == "2025-01-01"
    assert FROZEN_TICK_SIZE == .001 and phase.COST_MODELS == ("C1",)
    assert phase.BOOTSTRAP_ITERATIONS == 10_000 and phase.BOOTSTRAP_SEED == 330_2025


def test_context_contracts_are_separate_and_causal() -> None:
    manifests = [json.loads((ROOT / s / t / "manifest.json").read_text()) for s, t in phase.STUDIES]
    assert [x["execution_context"] for x in manifests[:2]] == ["none", "none"]
    assert manifests[2]["execution_context"] == "four completed non-overlapping M30 bars; local-day reset"
    assert manifests[3]["execution_context"] == "four completed non-overlapping H1 bars; local-day reset"
    assert "DataLoader.h4_from_h1" in inspect.getsource(four_bar_context)


def test_exact_concentration_and_classification_rules() -> None:
    assert phase.severe_concentration({"top_3_positive_R_share": .50001, "expectancy_C1_without_top3": 1})
    assert phase.severe_concentration({"top_3_positive_R_share": .5, "expectancy_C1_without_top3": 0})
    assert not phase.severe_concentration({"top_3_positive_R_share": .5, "expectancy_C1_without_top3": .01})
    assert phase.classify(.1, True, True, False, .50001) == "ROBUST_READY"
    assert phase.classify(.1, False, True, False, .9) == "BORDERLINE"
    assert phase.classify(.1, True, False, False, .9) == "BORDERLINE"
    assert phase.classify(.1, True, True, False, .5) == "BORDERLINE"
    assert phase.classify(0, True, True, False, .9) == "REJECTED"


def test_artifacts_have_exact_c1_only_shape_and_no_future_stage() -> None:
    assert not any("walk_forward" in p.name.lower() or "true_oos" in p.name.lower()
                   for p in ROOT.rglob("*"))
    for strategy, timeframe in phase.STUDIES:
        target = ROOT / strategy / timeframe
        comparison = pd.read_csv(target / "baseline_vs_candidate.csv")
        cost = pd.read_csv(target / "cost_report.csv")
        assert comparison[["version", "scenario"]].values.tolist() == [["baseline", "C1"], ["candidate", "C1"]]
        assert cost[["version", "scenario"]].values.tolist() == [["candidate", "C1"]]
        assert pd.read_csv(target / "instrument_report.csv").symbol.tolist() == list(phase.INSTRUMENTS)


def test_completed_audit_and_reconciliation_evidence() -> None:
    root = json.loads((ROOT / "validation_manifest.json").read_text())
    assert root["status"] == "PHASE_3_ROBUSTNESS_COMPLETE"
    assert root["true_oos_blocked"] and not root["walk_forward_executed"] and not root["true_oos_executed"]
    assert root["candidate_count"] == 4 and len(root["classifications"]) == 4
