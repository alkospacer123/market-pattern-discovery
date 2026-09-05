#!/usr/bin/env python3
"""Production entry point for the Phase 7 autonomous research worker."""
from __future__ import annotations

import argparse
import json
import time
from dataclasses import asdict
from pathlib import Path
from typing import Sequence

from market_pattern_discovery.orchestration import (
    AutonomousResearchWorker,
    AutonomousSearchScheduler,
    PatternExperimentRunner,
    PatternSearchSpace,
    UnknownPatternScheduler,
    cells_for_matrix,
)
from market_pattern_discovery.discovery.unknown import load_discovery_matrix
from market_pattern_discovery.research import ResearchMemory


def _next_cycle_number(state_directory: Path) -> int:
    """Return the first cycle number after all persisted worker results."""
    completed = (
        int(path.stem.removeprefix("cycle-"))
        for path in state_directory.glob("cycle-*.json")
        if path.stem.removeprefix("cycle-").isdigit()
    )
    return max(completed, default=-1) + 1


def run(data_root: Path, memory_root: Path, output_root: Path, *, budget: int,
        mode: str, sleep_seconds: float, track: str = "known",
        inference_budget: int = 0) -> None:
    """Run one cycle, or cycles until the finite search space is exhausted."""
    memory = ResearchMemory(memory_root)
    scheduler = AutonomousSearchScheduler(memory, data_root, output_root)
    state_directory = output_root / "autonomous-state"
    worker_options = {"track": track}
    if track in {"unknown", "mixed"}:
        def build_unknown_components():
            # Loading matrices and enumerating the frozen search space can be
            # expensive.  Defer both until the worker actually gives UNKNOWN
            # its turn (after KNOWN in MIXED mode).
            search_space = PatternSearchSpace(
                load_discovery_matrix(data_root, instrument, timeframe)
                for instrument in ("CNYRUBF", "USDRUBF")
                for timeframe in ("M1", "M5")
            )
            return (
                UnknownPatternScheduler(
                    memory, data_root, output_root, search_space=search_space),
                PatternExperimentRunner(memory),
            )

        worker_options["unknown_components_factory"] = build_unknown_components
    worker = AutonomousResearchWorker(
        scheduler, memory, state_directory, **worker_options)
    cycle_number = _next_cycle_number(state_directory)

    while True:
        result = worker.run_once(cycle_number=cycle_number, budget=budget,
                                 inference_budget=inference_budget)
        print(json.dumps(asdict(result), sort_keys=True), flush=True)
        if mode == "once" or result.status in {"SEARCH_SPACE_EXHAUSTED", "INFERENCE_PENDING"}:
            return
        cycle_number += 1
        time.sleep(sleep_seconds)


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Run the bounded Phase 7 autonomous research worker.")
    parser.add_argument("--data-root", type=Path, required=True)
    parser.add_argument("--memory-root", type=Path, required=True)
    parser.add_argument("--output-root", type=Path, required=True)
    parser.add_argument("--budget", type=int, required=True)
    parser.add_argument(
        "--inference-budget", type=int, default=0,
        help="maximum pending UNKNOWN_PATTERN cells to enrich per cycle")
    parser.add_argument("--mode", choices=("once", "continuous"), default="once")
    parser.add_argument(
        "--track", choices=("known", "unknown", "mixed"), default="known")
    parser.add_argument("--sleep-seconds", type=float, default=0.0)
    args = parser.parse_args(argv)
    if args.budget <= 0:
        parser.error("--budget must be positive")
    if args.sleep_seconds < 0:
        parser.error("--sleep-seconds must be non-negative")
    if args.inference_budget < 0:
        parser.error("--inference-budget must be non-negative")

    run(args.data_root, args.memory_root, args.output_root, budget=args.budget,
        mode=args.mode, sleep_seconds=args.sleep_seconds, track=args.track,
        inference_budget=args.inference_budget)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
