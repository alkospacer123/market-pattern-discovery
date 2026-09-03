from market_pattern_discovery.research.memory import CandidateRecord, ResearchMemory
from market_pattern_discovery.validation.phase6d import validate_research_loop


def test_phase6d_validates_complete_persisted_lineage(tmp_path):
    memory = ResearchMemory(tmp_path)
    memory.record_experiment("exp-1", {"search_cell_id": "cell-1", "data_period": "2020-2024"})
    memory.add_candidate(CandidateRecord("candidate-1", "strategy", "Si", "M5",
        {"originating_experiment_id": "exp-1"}, "evaluation-1", 1))
    memory.record_evaluation("evaluation-1", "candidate-1", {"profit_factor": 1.1})

    report = validate_research_loop(memory)

    assert report.valid
    assert report.counts == {"experiments": 1, "candidates": 1, "evaluations": 1}


def test_phase6d_rejects_true_oos_access(tmp_path):
    memory = ResearchMemory(tmp_path)
    memory.record_experiment("exp-1", {"true_oos_2025_accessed": True})

    report = validate_research_loop(memory)

    assert not report.valid
    assert not report.checks["true_oos_not_accessed"]
