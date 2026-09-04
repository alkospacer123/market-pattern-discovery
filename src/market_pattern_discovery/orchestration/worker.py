"""Phase 7 bounded autonomous research worker.

The worker coordinates existing planners and runners; it does not implement or
alter strategies.  One invocation executes at most one explicitly budgeted
cycle, making retries and operator scheduling predictable.
"""
from __future__ import annotations

import json
import os
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any

from market_pattern_discovery.orchestration.cycle import CycleRunner
from market_pattern_discovery.research.memory import ResearchMemory
from market_pattern_discovery.validation.phase6d import validate_research_loop


@dataclass(frozen=True, slots=True)
class WorkerResult:
    cycle_number: int
    status: str
    cycle_id: str | None
    failures: dict[str, str]
    validation: dict[str, Any]


class AutonomousResearchWorker:
    """Run one deterministic, resumable, budget-capped research cycle."""

    def __init__(self, scheduler, memory: ResearchMemory, state_directory: str | Path,
                 *, runner: CycleRunner | None = None, track: str = "known",
                 unknown_scheduler=None, unknown_runner=None) -> None:
        if track not in {"known", "unknown", "mixed"}:
            raise ValueError("track must be known, unknown, or mixed")
        self.scheduler = scheduler
        self.memory = memory
        self.state_directory = Path(state_directory)
        self.runner = runner or CycleRunner()
        self.track = track
        self.unknown_scheduler = unknown_scheduler
        self.unknown_runner = unknown_runner
        if track in {"unknown", "mixed"} and (unknown_scheduler is None or unknown_runner is None):
            raise ValueError("unknown and mixed tracks require an unknown scheduler and runner")

    def _completed_cycles(self) -> set[int]:
        if not self.state_directory.exists():
            return set()
        return {int(path.stem.split("-")[-1]) for path in self.state_directory.glob("cycle-*.json")}

    @staticmethod
    def _atomic_json(path: Path, value: dict[str, Any]) -> None:
        path.parent.mkdir(parents=True, exist_ok=True)
        temporary = path.with_suffix(".tmp")
        temporary.write_text(json.dumps(value, indent=2, sort_keys=True) + "\n", encoding="utf-8")
        os.replace(temporary, path)

    def _run_known(self, cycle_number: int, budget: int) -> tuple[str, str | None, dict[str, str]]:
        manifest = self.scheduler.plan(cycle_number, budget)
        if not manifest.experiments:
            return "SEARCH_SPACE_EXHAUSTED", None, {}
        report = self.runner.run(manifest)
        return ("COMPLETED" if report.succeeded else "COMPLETED_WITH_FAILURES",
                report.cycle_id, dict(report.failures))

    def _run_unknown(self, cycle_number: int, budget: int) -> tuple[str, str | None, dict[str, str]]:
        plan = self.unknown_scheduler.plan(cycle_number, budget)
        batch = plan.get("pattern_batch")
        if batch is None:
            return "SEARCH_SPACE_EXHAUSTED", None, {}
        self.unknown_runner.run(plan, infer=False)
        return "COMPLETED", batch.pattern_batch_id, {}

    def run_once(self, *, cycle_number: int, budget: int) -> WorkerResult:
        if cycle_number < 0 or budget <= 0:
            raise ValueError("cycle_number must be non-negative and budget must be positive")
        if cycle_number in self._completed_cycles():
            raise ValueError(f"cycle already finalized: {cycle_number}")

        if self.track == "known":
            status, cycle_id, failures = self._run_known(cycle_number, budget)
        elif self.track == "unknown":
            status, cycle_id, failures = self._run_unknown(cycle_number, budget)
        else:
            outcomes = []
            failures = {}
            cycle_ids = []
            # Track order is part of the reproducibility contract.  An error in
            # one track must not prevent the other track from receiving its turn.
            for name, execute in (("known", self._run_known), ("unknown", self._run_unknown)):
                try:
                    outcome, identifier, track_failures = execute(cycle_number, budget)
                    outcomes.append(outcome)
                    if identifier is not None:
                        cycle_ids.append(f"{name}:{identifier}")
                    failures.update({f"{name}:{key}": value
                                     for key, value in track_failures.items()})
                except Exception as error:  # execution failures are persisted per track
                    outcomes.append("COMPLETED_WITH_FAILURES")
                    failures[name] = f"{type(error).__name__}: {error}"
            status = ("SEARCH_SPACE_EXHAUSTED" if all(
                value == "SEARCH_SPACE_EXHAUSTED" for value in outcomes)
                else "COMPLETED_WITH_FAILURES" if failures else "COMPLETED")
            cycle_id = "|".join(cycle_ids) or None

        validation = validate_research_loop(self.memory).as_dict()
        if status == "COMPLETED" and not validation["valid"]:
            status = "COMPLETED_WITH_FAILURES"
        result = WorkerResult(cycle_number, status, cycle_id, failures, validation)
        self._atomic_json(self.state_directory / f"cycle-{cycle_number:06d}.json", asdict(result))
        return result
