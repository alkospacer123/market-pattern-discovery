#!/usr/bin/env python3
"""Crash-safe, platform-neutral Phase 4C synthesis entry point."""
from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

from market_pattern_discovery.backtest.phase6b import default_configs
from market_pattern_discovery.experiments.runner import ExperimentRunner, ExperimentSpec
from market_pattern_discovery.research.memory import RankingView, ResearchMemory, PatternStatus
from market_pattern_discovery.strategy_synthesis import (
    assess_exit_surface, execution_cell_id, persisted_exit_evidence, synthesize_pattern,
)

FRICTION_SIBLINGS = frozenset({"GROSS", "BASE", "STRESS"})


def execution_cell_states(memory: ResearchMemory, pattern_strategy_id: str,
                          configs: list[tuple[Any, ...]]) -> dict[str, dict[str, Any]]:
    """Reconstruct completion from semantic cells, never from strategy presence."""
    candidates = list(memory.candidates().values())
    experiments = memory.experiments()
    states = {}
    for config in configs:
        name = str(config[0]); cell = execution_cell_id(pattern_strategy_id, config)
        siblings = {str(c.parameters.get("friction_scenario")) for c in candidates
                    if c.parameters.get("execution_search_cell_id") == cell}
        zero_signal = any((row["metadata"].get("search_cell_id") == cell
                           or cell in (row["metadata"].get("execution_search_cell_ids") or []))
                          and row["metadata"].get("v3_manifest", {}).get("raw_signals") == 0
                          for row in experiments)
        states[name] = {"execution_search_cell_id": cell, "siblings": sorted(siblings),
                        "zero_signal": zero_signal,
                        "complete": siblings == FRICTION_SIBLINGS or zero_signal,
                        "partial": bool(siblings) and siblings != FRICTION_SIBLINGS}
    return states


def _artifact_experiments(memory: ResearchMemory, pattern_strategy_id: str) -> dict[str, dict[str, Any]]:
    found = {}
    for row in memory.experiments():
        metadata = row["metadata"]
        pattern = metadata.get("pattern_strategy") or {}
        configs = metadata.get("exit_configurations") or []
        if pattern.get("pattern_strategy_id") == pattern_strategy_id:
            for config in configs:
                found[str(config[0])] = dict(metadata) | {"_experiment_id": row["experiment_id"]}
    return found


def completed_surface_assessment(memory: ResearchMemory, pattern_strategy_id: str,
                                 configs: list[tuple[Any, ...]]) -> bool:
    """Return whether every semantic cell has a completed assessment fact."""
    latest = memory.latest_synthesis_assessments()
    return all((row := latest.get(execution_cell_id(pattern_strategy_id, config))) is not None
               and row.get("pattern_strategy_id") == pattern_strategy_id
               and row.get("assessment_complete") is True
               for config in configs)


def _assessment_changed(previous: dict[str, Any] | None, current: dict[str, Any]) -> bool:
    """Compare scientific evidence while ignoring invocation-only provenance."""
    if previous is None:
        return True
    ignored = {"cycle"}
    return ({key: value for key, value in previous.items() if key not in ignored}
            != {key: value for key, value in current.items() if key not in ignored})


def persist_surface_assessment(memory: ResearchMemory, spec: Any, configs: list[tuple[Any, ...]],
                               cycle: int) -> tuple[bool, list[str]]:
    """Rebuild V3 evidence after restart, assess once complete, and append facts."""
    states = execution_cell_states(memory, spec.pattern_strategy_id, configs)
    complete = all(row["complete"] for row in states.values())
    artifacts = _artifact_experiments(memory, spec.pattern_strategy_id)
    evidence = {}
    if complete and not any(row["zero_signal"] for row in states.values()):
        for config in configs:
            name = str(config[0]); metadata = artifacts.get(name)
            if metadata is None:
                complete = False
                break
            evidence[name] = persisted_exit_evidence(metadata["output_directory"], name)
    assessed = assess_exit_surface(evidence) if complete and len(evidence) == len(configs) else {}
    survivors = []
    latest = memory.latest_synthesis_assessments()
    for config in configs:
        name = str(config[0]); cell = states[name]["execution_search_cell_id"]
        row = assessed.get(name)
        payload = {
            "pattern_strategy_id": spec.pattern_strategy_id,
            "source_pattern_cell_id": spec.source_pattern_cell_id,
            "execution_search_cell_id": cell, "exit_configuration": name,
            "BASE": (row or {}).get("BASE", {}), "STRESS": (row or {}).get("STRESS", {}),
            "unique_trading_days": evidence.get(name, {}).get("unique_trading_days", 0),
            "positive_calendar_blocks": evidence.get(name, {}).get("positive_calendar_blocks", 0),
            "largest_winner_share": evidence.get(name, {}).get("largest_winner_share"),
            "neighbours": (row or {}).get("neighbours", []), "checks": (row or {}).get("checks", {}),
            "assessment_complete": bool(complete),
            "trading_survivor": bool(row and row["trading_survivor"]),
            "reason": None if complete else "INCOMPLETE_EXECUTION_SURFACE",
            "source_v3_artifacts": {"paths": evidence.get(name, {}).get("artifact_paths", {}),
                "hashes": artifacts.get(name, {}).get("v3_manifest", {}).get("outputs", {})},
            "cycle": cycle,
            "experiment_id": artifacts.get(name, {}).get("_experiment_id"),
        }
        if _assessment_changed(latest.get(cell), payload):
            memory.record_synthesis_assessment(payload)
        if payload["trading_survivor"]:
            survivors.append(name)
    return complete, survivors


def run_synthesis(data_root: Path, memory_root: Path, output_root: Path, cycle: int,
                  budget: int, *, runner_factory=ExperimentRunner,
                  exit_cell_budget: int | None = None) -> dict[str, Any]:
    memory = ResearchMemory(memory_root); configs = list(default_configs())
    manifest: dict[str, Any] = {"label": "PHASE4C_PRODUCTION_SYNTHESIS", "cycle": cycle,
        "processed": [], "non_actionable": [], "skipped_completed": []}
    remaining = budget
    for record in sorted(memory.pattern_effects().values(), key=lambda x: x.pattern_cell_id):
        if record.screening_status is not PatternStatus.PATTERN_SURVIVOR:
            continue
        spec, decision = synthesize_pattern(record)
        if spec is None:
            item = {"source_pattern_cell_id": record.pattern_cell_id, "reason": decision.reason}
            manifest["non_actionable"].append(item); continue
        before = execution_cell_states(memory, spec.pattern_strategy_id, configs)
        missing = [config for config in configs if not before[str(config[0])]["complete"]]
        if not missing and completed_surface_assessment(memory, spec.pattern_strategy_id, configs):
            manifest["skipped_completed"].append(spec.pattern_strategy_id)
            continue
        if remaining == 0:
            break
        executed = []
        scheduled = missing if exit_cell_budget is None else missing[:exit_cell_budget]
        if scheduled:
            names = [str(config[0]) for config in scheduled]
            cells = [before[name]["execution_search_cell_id"] for name in names]
            attempts = 1 + sum(any(cell in (row["metadata"].get("execution_search_cell_ids") or [])
                                   for cell in cells) for row in memory.experiments())
            batch_name = names[0] if len(names) == 1 else f"batch-{names[0]}-to-{names[-1]}"
            out = output_root / f"cycle-{cycle}" / spec.pattern_strategy_id[:16] / batch_name / f"attempt-{attempts}"
            metadata = {"research_track": "SYNTHESIZED_STRATEGY", "instrument": spec.instrument,
                "timeframe": spec.timeframe, "pattern_strategy": spec.to_dict(),
                "exit_configurations": [list(config) for config in scheduled],
                "execution_search_cell_ids": cells}
            runner_factory(memory).run(ExperimentSpec(
                f"pattern-{spec.pattern_strategy_id[:16]}-{batch_name}-attempt-{attempts}",
                data_root, out, cycle, metadata))
            executed.extend(names)
        after = execution_cell_states(memory, spec.pattern_strategy_id, configs)
        assessment_complete, survivors = persist_surface_assessment(memory, spec, configs, cycle)
        zero = [name for name, state in after.items() if state["zero_signal"]]
        rankings = {view.value: [c.candidate_id for c in memory.view(view)] for view in
            (RankingView.TOP_BASE_PF, RankingView.TOP_BASE_EXPECTANCY,
             RankingView.TOP_STRESS_PF, RankingView.TOP_RECOVERY)}
        manifest["processed"].append({"pattern_strategy_id": spec.pattern_strategy_id,
            "source_pattern_cell_id": record.pattern_cell_id, "exit_cells_expected": len(configs),
            "exit_cells_already_complete": sum(x["complete"] for x in before.values()),
            "exit_cells_executed_this_run": executed,
            "exit_cells_remaining": sum(not x["complete"] for x in after.values()),
            "candidate_count": sum(c.parameters.get("pattern_strategy_id") == spec.pattern_strategy_id
                                   for c in memory.candidates().values()),
            "assessment_complete": assessment_complete, "trading_survivor_exit_cells": survivors,
            "zero_signal_status": "ZERO_EXECUTABLE_SIGNALS" if zero else None,
            "zero_signal_exit_cells": zero, **rankings})
        remaining -= 1
    output_root.mkdir(parents=True, exist_ok=True)
    path = output_root / f"synthesis_manifest_cycle_{cycle}.json"
    path.write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
    manifest["manifest_path"] = str(path)
    return manifest


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--data-root", type=Path, required=True)
    parser.add_argument("--memory-root", type=Path, required=True)
    parser.add_argument("--output-root", type=Path, required=True)
    parser.add_argument("--cycle", type=int, required=True)
    parser.add_argument("--budget", type=int, required=True)
    parser.add_argument("--exit-cell-budget", type=int,
                        help="integration/resume bound; omit for the full exit surface")
    args = parser.parse_args()
    if args.budget <= 0:
        parser.error("--budget must be positive")
    if args.exit_cell_budget is not None and args.exit_cell_budget <= 0:
        parser.error("--exit-cell-budget must be positive")
    manifest = run_synthesis(args.data_root, args.memory_root, args.output_root, args.cycle,
                             args.budget, exit_cell_budget=args.exit_cell_budget)
    print(manifest["manifest_path"])
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
