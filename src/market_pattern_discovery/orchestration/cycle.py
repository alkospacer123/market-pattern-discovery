"""Deterministic, failure-isolated orchestration of V3.5 experiments."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Mapping

from market_pattern_discovery.contracts import deterministic_hash
from market_pattern_discovery.experiments import ExperimentResult, ExperimentRunner, ExperimentSpec
from market_pattern_discovery.research.memory import CandidateRecord


@dataclass(frozen=True, slots=True)
class CycleManifest:
    cycle_number: int
    experiments: tuple[ExperimentSpec, ...]
    metadata: Mapping[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if self.cycle_number < 0:
            raise ValueError("cycle_number must be non-negative")
        ordered = tuple(sorted(self.experiments, key=lambda spec: (spec.name, spec.experiment_id)))
        if len({spec.experiment_id for spec in ordered}) != len(ordered):
            raise ValueError("duplicate experiment in cycle")
        cell_ids = [spec.search_cell_id for spec in ordered if spec.search_cell_id is not None]
        if len(cell_ids) != len(set(cell_ids)):
            raise ValueError("duplicate search_cell_id in cycle")
        if any(spec.cycle_number != self.cycle_number for spec in ordered):
            raise ValueError("experiment cycle_number must match its cycle manifest")
        object.__setattr__(self, "experiments", ordered)
        object.__setattr__(self, "metadata", dict(self.metadata))

    @property
    def cycle_id(self) -> str:
        return deterministic_hash({"cycle_number": self.cycle_number,
                                   "experiments": [spec.experiment_id for spec in self.experiments],
                                   "metadata": self.metadata})


@dataclass(frozen=True, slots=True)
class CycleReport:
    cycle_id: str
    results: tuple[ExperimentResult, ...]
    failures: Mapping[str, str]
    candidates: tuple[CandidateRecord, ...]

    @property
    def succeeded(self) -> bool:
        return not self.failures

    def audit(self, manifest: CycleManifest, memory) -> Mapping[str, Any]:
        """Return a JSON-serializable planning/execution and ranking snapshot."""
        from market_pattern_discovery.research.memory import RankingView
        rankings = {view.value: [row.candidate_id for row in memory.view(view)] for view in RankingView}
        return {"cycle_number": manifest.cycle_number, "cycle_id": self.cycle_id,
            "planned_experiments": [{"experiment_id": spec.experiment_id,
                "search_cell_id": spec.search_cell_id,
                "selection_mode": spec.metadata.get("selection_mode"),
                "parent_search_cell_id": spec.metadata.get("parent_search_cell_id"),
                "parameters": spec.metadata.get("parameters"),
                **dict(spec.metadata.get("search_spec") or {})} for spec in manifest.experiments],
            **dict(manifest.metadata), "failures": dict(self.failures),
            "candidate_count": len(self.candidates), "rankings": rankings}


class CycleRunner:
    def __init__(self, experiment_runner: ExperimentRunner | None = None) -> None:
        self.experiment_runner = experiment_runner or ExperimentRunner()

    def run(self, manifest: CycleManifest) -> CycleReport:
        results: list[ExperimentResult] = []
        failures: dict[str, str] = {}
        for spec in manifest.experiments:
            try:
                results.append(self.experiment_runner.run(spec))
            except Exception as error:  # isolation is intentionally at the experiment boundary
                failures[spec.experiment_id] = f"{type(error).__name__}: {error}"
        candidates = sorted((candidate for result in results for candidate in result.candidates),
                            key=lambda candidate: candidate.candidate_id)
        return CycleReport(manifest.cycle_id, tuple(results), failures, tuple(candidates))
