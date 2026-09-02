#!/usr/bin/env python3
"""Platform-neutral bounded Phase 4C synthesis entry point."""
from __future__ import annotations

import argparse
import json
from pathlib import Path

from market_pattern_discovery.backtest.phase6b import default_configs
from market_pattern_discovery.experiments.runner import ExperimentRunner, ExperimentSpec
from market_pattern_discovery.research.memory import ResearchMemory, PatternStatus
from market_pattern_discovery.strategy_synthesis import synthesize_pattern


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--data-root", type=Path, required=True)
    parser.add_argument("--memory-root", type=Path, required=True)
    parser.add_argument("--output-root", type=Path, required=True)
    parser.add_argument("--cycle", type=int, required=True)
    parser.add_argument("--budget", type=int, required=True)
    args = parser.parse_args()
    if args.budget <= 0: parser.error("--budget must be positive")
    memory = ResearchMemory(args.memory_root)
    completed = {c.parameters.get("pattern_strategy_id") for c in memory.candidates().values()}
    manifest = {"label":"PHASE4C_PRODUCTION_SYNTHESIS", "cycle":args.cycle,
                "processed":[], "non_actionable":[], "skipped_completed":[]}
    remaining = args.budget
    for record in sorted(memory.pattern_effects().values(), key=lambda x:x.pattern_cell_id):
        if record.screening_status is not PatternStatus.PATTERN_SURVIVOR: continue
        spec, decision = synthesize_pattern(record)
        if spec is None:
            manifest["non_actionable"].append({"source_pattern_cell_id":record.pattern_cell_id,
                                                "reason":decision.reason})
            continue
        if spec.pattern_strategy_id in completed:
            manifest["skipped_completed"].append(spec.pattern_strategy_id); continue
        if remaining == 0: break
        out = args.output_root / f"cycle-{args.cycle}" / spec.pattern_strategy_id[:16]
        metadata = {"research_track":"SYNTHESIZED_STRATEGY", "instrument":spec.instrument,
                    "timeframe":spec.timeframe, "pattern_strategy":spec.to_dict(),
                    "exit_configurations":[list(x) for x in default_configs()]}
        result = ExperimentRunner(memory).run(ExperimentSpec(
            f"pattern-{spec.pattern_strategy_id[:16]}", args.data_root, out, args.cycle, metadata))
        manifest["processed"].append({"pattern_strategy_id":spec.pattern_strategy_id,
            "source_pattern_cell_id":record.pattern_cell_id, "candidates":len(result.candidates),
            "output":str(out)})
        remaining -= 1
    args.output_root.mkdir(parents=True, exist_ok=True)
    path = args.output_root / f"synthesis_manifest_cycle_{args.cycle}.json"
    path.write_text(json.dumps(manifest, indent=2)+"\n", encoding="utf-8")
    print(path)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
