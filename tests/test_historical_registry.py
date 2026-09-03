from market_pattern_discovery.research.historical_registry import build_historical_registry
from market_pattern_discovery.research.memory import CandidateRecord, CandidateStatus, ResearchMemory


def test_historical_registry_enriches_lineage_metrics_and_lifecycle(tmp_path):
    memory = ResearchMemory(tmp_path)
    candidate = CandidateRecord("candidate-1", "strategy-1", "CNY", "M5",
        {"originating_experiment_id": "experiment-1", "search_cell_id": "cell-1"},
        "evaluation-1", 4)
    memory.add_candidate(candidate)
    memory.record_evaluation("evaluation-1", "candidate-1", {"profit_factor": 1.2}, {"source": "test"})
    memory.transition("candidate-1", CandidateStatus.VALIDATED)

    first = build_historical_registry(memory)
    second = build_historical_registry(memory)
    record = first["records"][0]

    assert first == second
    assert record["lineage"]["originating_experiment_id"] == "experiment-1"
    assert record["metrics"] == {"profit_factor": 1.2}
    assert [event["event"] for event in record["lifecycle"]] == ["CREATED", "STATUS_CHANGED"]
    assert record["current_status"] == "VALIDATED"
