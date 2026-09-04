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
    patterns_created: int = 0
    inference_pending: int = 0
    inference_completed: int = 0
    survivors: int = 0
    screened_out: int = 0


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

    def _run_unknown(self, cycle_number: int, budget: int, inference_budget: int
                     ) -> tuple[str, str | None, dict[str, str], dict[str, int]]:
        plan = self.unknown_scheduler.plan(cycle_number, budget)
        batch = plan.get("pattern_batch")
        created = self.unknown_runner.run(plan, infer=False) if batch is not None else ()

        # Inference is deliberately selected from memory after discovery.  It
        # can therefore consume cells created by this cycle or resume cells
        # left pending by an earlier process invocation.
        pending = self.unknown_scheduler.pending_inference_cells(inference_budget)
        inferred = self.unknown_runner.add_inference(
            pending, self.unknown_scheduler.data_root)
        finalized = self.unknown_runner.finalize_ready_families(
            self.unknown_scheduler.search_space)
        effective = self.memory.pattern_effects()
        metrics = {
            "patterns_created": len(created),
            "inference_pending": len(self.unknown_scheduler.pending_inference_cells(
                len(self.unknown_scheduler.search_space))),
            "inference_completed": len(inferred),
            "survivors": sum(effective[cell_id].screening_status.value == "PATTERN_SURVIVOR"
                             for cell_id in finalized),
            "screened_out": sum(effective[cell_id].screening_status.value == "SCREENED_OUT"
                                for cell_id in finalized),
        }
        status = ("SEARCH_SPACE_EXHAUSTED"
                  if batch is None and metrics["inference_pending"] == 0
                  else "COMPLETED")
        return status, batch.pattern_batch_id if batch is not None else None, {}, metrics

    def run_once(self, *, cycle_number: int, budget: int,
                 inference_budget: int = 0) -> WorkerResult:
        if cycle_number < 0 or budget <= 0 or inference_budget < 0:
            raise ValueError("cycle_number and inference_budget must be non-negative; "
                             "budget must be positive")
        if cycle_number in self._completed_cycles():
            raise ValueError(f"cycle already finalized: {cycle_number}")

        if self.track == "known":
            status, cycle_id, failures = self._run_known(cycle_number, budget)
            metrics = {}
        elif self.track == "unknown":
            status, cycle_id, failures, metrics = self._run_unknown(
                cycle_number, budget, inference_budget)
        else:
            outcomes = []
            failures = {}
            cycle_ids = []
            # Track order is part of the reproducibility contract.  An error in
            # one track must not prevent the other track from receiving its turn.
            metrics = {}
            # The total discovery budget is split in stable track order.  For
            # odd budgets KNOWN receives the extra unit; zero-budget tracks are
            # skipped rather than violating planner preconditions.
            allocations = {"known": (budget + 1) // 2, "unknown": budget // 2}
            executions = (("known", self._run_known), ("unknown", self._run_unknown))
            for name, execute in executions:
                if allocations[name] == 0:
                    continue
                try:
                    if name == "unknown":
                        outcome, identifier, track_failures, metrics = execute(
                            cycle_number, allocations[name], inference_budget)
                    else:
                        outcome, identifier, track_failures = execute(
                            cycle_number, allocations[name])
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
        result = WorkerResult(cycle_number, status, cycle_id, failures, validation, **metrics)
        self._atomic_json(self.state_directory / f"cycle-{cycle_number:06d}.json", asdict(result))
        return result
