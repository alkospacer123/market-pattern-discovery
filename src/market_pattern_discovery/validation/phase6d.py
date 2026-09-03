"""Phase 6D validation of the complete research loop.

The validator reads research metadata only.  It deliberately never opens market
data and rejects any manifest that indicates TRUE OOS access.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Mapping

from market_pattern_discovery.research.memory import ResearchMemory


@dataclass(frozen=True, slots=True)
class ResearchLoopValidation:
    valid: bool
    checks: Mapping[str, bool]
    counts: Mapping[str, int]

    def as_dict(self) -> dict[str, Any]:
        return {"phase": "6D", "valid": self.valid,
                "checks": dict(self.checks), "counts": dict(self.counts)}


def validate_research_loop(memory: ResearchMemory) -> ResearchLoopValidation:
    """Validate persisted experiment-to-evaluation lineage deterministically."""
    experiments = memory.experiments()
    candidates = memory.candidates()
    evaluations = memory.evaluation_history()
    experiment_ids = {row["experiment_id"] for row in experiments}
    evaluation_ids = {row["evaluation_id"] for row in evaluations}
    candidate_ids = set(candidates)

    no_oos_access = all(
        not row["metadata"].get("true_oos_2025_accessed", False)
        and str(row["metadata"].get("data_period", "")) != "2025"
        for row in experiments
    )
    unique_experiments = len(experiment_ids) == len(experiments)
    unique_evaluations = len(evaluation_ids) == len(evaluations)
    evaluation_lineage = all(row["candidate_id"] in candidate_ids for row in evaluations)
    metric_lineage = all(row.metrics_reference in evaluation_ids for row in candidates.values())
    experiment_lineage = all(
        not row.parameters.get("originating_experiment_id")
        or row.parameters["originating_experiment_id"] in experiment_ids
        for row in candidates.values()
    )
    completed_cells = [row["metadata"].get("search_cell_id") for row in experiments
                       if row["metadata"].get("search_cell_id")]
    deterministic_cells = len(completed_cells) == len(set(completed_cells))
    checks = {
        "true_oos_not_accessed": no_oos_access,
        "experiment_ids_unique": unique_experiments,
        "evaluation_ids_unique": unique_evaluations,
        "evaluation_candidate_lineage": evaluation_lineage,
        "candidate_metric_lineage": metric_lineage,
        "candidate_experiment_lineage": experiment_lineage,
        "search_cells_unique": deterministic_cells,
    }
    counts = {"experiments": len(experiments), "candidates": len(candidates),
              "evaluations": len(evaluations)}
    return ResearchLoopValidation(all(checks.values()), checks, counts)
