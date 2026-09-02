"""Single-call experiment adapter around the verified V3 Phase 6B pipeline."""
from __future__ import annotations

import csv
import json
import math
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Callable, Mapping

from market_pattern_discovery.backtest.phase6b import run as run_v3
from market_pattern_discovery.contracts import deterministic_hash
from market_pattern_discovery.research.memory import CandidateRecord, ResearchMemory


@dataclass(frozen=True, slots=True)
class ExperimentSpec:
    name: str
    data_root: str | Path
    output_directory: str | Path
    cycle_number: int = 0
    metadata: Mapping[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if not self.name or self.cycle_number < 0:
            raise ValueError("name is required and cycle_number must be non-negative")
        object.__setattr__(self, "data_root", Path(self.data_root))
        object.__setattr__(self, "output_directory", Path(self.output_directory))
        object.__setattr__(self, "metadata", dict(self.metadata))

    @property
    def experiment_id(self) -> str:
        # Output location is deliberately excluded: moving a run cannot change its identity.
        return deterministic_hash({"name": self.name, "data_root": self.data_root,
                                   "cycle_number": self.cycle_number, "metadata": self.metadata})


@dataclass(frozen=True, slots=True)
class ExperimentResult:
    experiment_id: str
    manifest: Mapping[str, Any]
    candidates: tuple[CandidateRecord, ...]
    output_directory: Path


def _finite_metrics(row: Mapping[str, str]) -> dict[str, float]:
    aliases = {"profit_factor_ATR": "profit_factor", "expectancy_ATR": "expectancy",
               "recovery_factor_ATR": "robustness"}
    result: dict[str, float] = {}
    for source, target in aliases.items():
        try:
            value = float(row[source])
        except (KeyError, TypeError, ValueError):
            continue
        if math.isfinite(value):
            result[target] = value
    return result


def adapt_v3_results(spec: ExperimentSpec, manifest: Mapping[str, Any]) -> list[tuple[CandidateRecord, dict[str, float]]]:
    """Project V3's persisted summary into candidates without recalculating metrics."""
    summary = spec.output_directory / "strategy_summary.csv"
    if not summary.is_file():
        return []
    adapted = []
    with summary.open(newline="", encoding="utf-8") as stream:
        for row in csv.DictReader(stream):
            identity = {key: row[key] for key in ("strategy_id", "instrument", "exit_configuration",
                                                   "friction_scenario")}
            candidate_id = deterministic_hash({"experiment_id": spec.experiment_id, **identity})
            evaluation_id = deterministic_hash({"candidate_id": candidate_id, "kind": "v3_metrics"})
            candidate = CandidateRecord(candidate_id, row["strategy_id"], row["instrument"], "M1",
                {"exit_configuration": row["exit_configuration"], "friction_scenario": row["friction_scenario"]},
                evaluation_id, spec.cycle_number)
            adapted.append((candidate, _finite_metrics(row)))
    return adapted


class ExperimentRunner:
    """Invoke V3 exactly once, then persist only an adapter view of its artifacts."""

    def __init__(self, memory: ResearchMemory | None = None,
                 pipeline: Callable[[str | Path, str | Path], Mapping[str, Any]] = run_v3) -> None:
        self.memory = memory
        self.pipeline = pipeline

    def run(self, spec: ExperimentSpec) -> ExperimentResult:
        spec.output_directory.mkdir(parents=True, exist_ok=True)
        manifest = self.pipeline(spec.data_root, spec.output_directory)  # the one and only V3 call
        if manifest is None:
            manifest = json.loads((spec.output_directory / "run_manifest.json").read_text())
        adapted = adapt_v3_results(spec, manifest)
        if self.memory is not None:
            self.memory.record_experiment(spec.experiment_id,
                {"name": spec.name, "cycle_number": spec.cycle_number,
                 "output_directory": spec.output_directory.as_posix(), "v3_manifest": dict(manifest)})
            for candidate, metric_values in adapted:
                self.memory.add_candidate(candidate)
                self.memory.record_evaluation(candidate.metrics_reference, candidate.candidate_id, metric_values,
                                              {"source": "V3 strategy_summary.csv"})
        return ExperimentResult(spec.experiment_id, dict(manifest),
                                tuple(candidate for candidate, _ in adapted), spec.output_directory)
