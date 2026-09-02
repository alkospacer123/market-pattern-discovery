from __future__ import annotations

from dataclasses import replace

import pytest

from market_pattern_discovery.research.memory import (
    CandidateRecord,
    CandidateStatus,
    RankingView,
    ResearchMemory,
    rank_candidates,
)


def candidate(identifier: str, reference: str = "eval-1") -> CandidateRecord:
    return CandidateRecord(
        candidate_id=identifier,
        strategy_id="strategy-a",
        instrument="TEST",
        timeframe="M5",
        parameters={"window": 12},
        metrics_reference=reference,
        creation_cycle=3,
    )


def test_candidate_is_immutable_and_owns_parameters() -> None:
    parameters = {"window": 12}
    record = replace(candidate("C-1"), parameters=parameters)
    parameters["window"] = 99

    assert record.parameters == {"window": 12}
    with pytest.raises(AttributeError):
        record.status = CandidateStatus.REJECTED  # type: ignore[misc]


def test_append_only_history_survives_registry_restart(tmp_path) -> None:
    memory = ResearchMemory(tmp_path)
    memory.record_experiment("EXP-1", {"cycle": 3, "development_period": "2020-2024"})
    memory.add_candidate(candidate("C-1"))
    memory.record_evaluation("eval-1", "C-1", {"profit_factor": 1.4, "expectancy": 2.0})
    memory.transition("C-1", CandidateStatus.VALIDATED)
    memory.transition("C-1", CandidateStatus.PROMOTED)

    reopened = ResearchMemory(tmp_path)
    assert reopened.candidates()["C-1"].status is CandidateStatus.PROMOTED
    assert [event["event"] for event in reopened.candidate_history()] == ["CREATED", "STATUS_CHANGED", "STATUS_CHANGED"]
    assert reopened.experiments()[0]["metadata"]["cycle"] == 3
    assert reopened.evaluation_history()[0]["metrics"]["profit_factor"] == 1.4


def test_lifecycle_rejects_skips_and_terminal_transitions(tmp_path) -> None:
    memory = ResearchMemory(tmp_path)
    memory.add_candidate(candidate("C-1"))
    with pytest.raises(ValueError, match="invalid candidate transition"):
        memory.transition("C-1", CandidateStatus.PROMOTED)
    memory.transition("C-1", CandidateStatus.REJECTED)
    memory.transition("C-1", CandidateStatus.RETIRED)
    with pytest.raises(ValueError, match="invalid candidate transition"):
        memory.transition("C-1", CandidateStatus.VALIDATED)


def test_rankings_are_views_and_have_deterministic_ties(tmp_path) -> None:
    memory = ResearchMemory(tmp_path)
    for identifier in ("C-2", "C-1", "C-3"):
        memory.add_candidate(candidate(identifier, f"E-{identifier[-1]}"))
    memory.record_evaluation("E-2", "C-2", {"profit_factor": 1.5, "expectancy": 1.0, "robustness": 0.7})
    memory.record_evaluation("E-1", "C-1", {"profit_factor": 1.5, "expectancy": 3.0, "robustness": 0.5})
    memory.record_evaluation("E-3", "C-3", {"profit_factor": 1.1, "expectancy": 2.0, "robustness": 0.9})
    memory.transition("C-2", CandidateStatus.VALIDATED)
    memory.transition("C-2", CandidateStatus.PROMOTED)
    history_before = (memory.candidate_history(), memory.evaluation_history())

    assert [row.candidate_id for row in memory.view(RankingView.TOP_PF)] == ["C-1", "C-2", "C-3"]
    assert [row.candidate_id for row in memory.view(RankingView.TOP_EXPECTANCY, limit=2)] == ["C-1", "C-3"]
    assert [row.candidate_id for row in memory.view(RankingView.TOP_ROBUST)] == ["C-3", "C-2", "C-1"]
    assert [row.candidate_id for row in memory.view(RankingView.CHAMPIONS)] == ["C-2"]
    assert (memory.candidate_history(), memory.evaluation_history()) == history_before


def test_pure_ranking_uses_metrics_reference_without_evaluating() -> None:
    records = [candidate("C-2", "M-2"), candidate("C-1", "M-1")]
    metrics = {"M-1": {"profit_factor": 1.2}, "M-2": {"profit_factor": 1.1}}

    assert [row.candidate_id for row in rank_candidates(records, metrics, RankingView.TOP_PF)] == ["C-1", "C-2"]
    assert records[0].status is CandidateStatus.GENERATED


def test_duplicate_identifiers_are_rejected(tmp_path) -> None:
    memory = ResearchMemory(tmp_path)
    memory.record_experiment("EXP-1", {})
    memory.add_candidate(candidate("C-1"))
    memory.record_evaluation("E-1", "C-1", {})
    with pytest.raises(ValueError, match="experiment already exists"):
        memory.record_experiment("EXP-1", {})
    with pytest.raises(ValueError, match="candidate already exists"):
        memory.add_candidate(candidate("C-1"))
    with pytest.raises(ValueError, match="evaluation already exists"):
        memory.record_evaluation("E-1", "C-1", {})
