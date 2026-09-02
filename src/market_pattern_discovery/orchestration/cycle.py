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
