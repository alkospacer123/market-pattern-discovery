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
                 *, runner: CycleRunner | None = None) -> None:
        self.scheduler = scheduler
        self.memory = memory
        self.state_directory = Path(state_directory)
        self.runner = runner or CycleRunner()

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

    def run_once(self, *, cycle_number: int, budget: int) -> WorkerResult:
        if cycle_number < 0 or budget <= 0:
            raise ValueError("cycle_number must be non-negative and budget must be positive")
        if cycle_number in self._completed_cycles():
            raise ValueError(f"cycle already finalized: {cycle_number}")
        manifest = self.scheduler.plan(cycle_number, budget)
        if not manifest.experiments:
            result = WorkerResult(cycle_number, "SEARCH_SPACE_EXHAUSTED", None, {},
                                  validate_research_loop(self.memory).as_dict())
        else:
            report = self.runner.run(manifest)
            validation = validate_research_loop(self.memory).as_dict()
            status = "COMPLETED" if report.succeeded and validation["valid"] else "COMPLETED_WITH_FAILURES"
            result = WorkerResult(cycle_number, status, report.cycle_id,
                                  dict(report.failures), validation)
        self._atomic_json(self.state_directory / f"cycle-{cycle_number:06d}.json", asdict(result))
        return result
