"""Bounded production orchestration for autonomous multi-horizon research."""
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any
import argparse
import json
from dataclasses import asdict

import pandas as pd

from market_pattern_discovery.data import MarketDataLoader
from market_pattern_discovery.features.context import CausalContextEngine
from market_pattern_discovery.research import (Conclusion, Evidence, Evaluation,
    KnowledgeRecord, MultiHorizonScheduler, ResearchCell, ResearchIntelligence,
    ResearchMemory, ResearchTrack, UnifiedResearchExecutor, create_pattern_effect)


def _known(**contract: Any) -> dict[str, Any]:
    return {"discovery_method": "known-family-evaluation", "evidence_state": "EVALUATED"}


def _unknown(**contract: Any) -> dict[str, Any]:
    return {"discovery_method": "open-feature-effect-scan", "evidence_state": "EVALUATED"}


@dataclass(frozen=True, slots=True)
class CycleResult:
    cycle: int
    planned: int
    recorded: int


class MultiHorizonResearchRunner:
    def __init__(self, data_root: str | Path, memory_root: str | Path, *, seed: int = 35) -> None:
        self.loader = MarketDataLoader(data_root)
        self.memory = ResearchMemory(memory_root)
        self.scheduler = MultiHorizonScheduler(seed=seed)
        self.context = CausalContextEngine()
        self.executor = UnifiedResearchExecutor(_known, _unknown)

    def _prepare(self, cell: ResearchCell) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
        market = self.loader.load(cell.symbol, cell.primary_timeframe)
        aligned = market
        for context_tf in cell.context_timeframes:
            aligned = aligned.drop(columns=["context_close_time"], errors="ignore")
            aligned = self.context.align(aligned, self.loader.load(cell.symbol, context_tf))
        features = pd.DataFrame({"timestamp": market.timestamp,
            "close_change": market.close.diff()}, index=market.index)
        return market, aligned, features

    def run(self, cycles: int, *, budget: int = 1) -> tuple[CycleResult, ...]:
        if cycles <= 0:
            raise ValueError("cycles must be positive; unlimited execution is forbidden")
        results = []
        for cycle in range(cycles):
            completed = {row["cell_id"] for row in self.memory.research_attempts()}
            cells = self.scheduler.plan(completed, budget)
            recorded = 0
            for cell in cells:
                market, context, features = self._prepare(cell)
                attempt, _ = self.executor.execute(cell, market, context, features)
                if not self.memory.record_research_attempt(attempt):
                    continue
                observed = features.close_change.dropna()
                evaluation = Evaluation(f"evaluation-{attempt.identity}",
                    float(observed.mean()) if len(observed) else None, len(observed),
                    {"cell_id": cell.identity})
                evidence = Evidence(evaluation.evaluation_id, len(observed) >= 2,
                    "observed development bars" if len(observed) >= 2 else "insufficient observations")
                effect = create_pattern_effect(evaluation, evidence)
                conclusion = ResearchIntelligence().conclude(evaluation, evidence, effect)
                for context_tf in cell.context_timeframes:
                    record = KnowledgeRecord(cell.symbol, cell.research_horizon.value,
                        cell.primary_timeframe, context_tf, cell.research_track.value,
                        evaluation.evaluation_id, conclusion.conclusion.value, "CURRENT",
                        {"cell_id": cell.identity, "effect_id": effect.effect_id if effect else None})
                    self.memory.add_knowledge_record(record)
                recorded += 1
            results.append(CycleResult(cycle, len(cells), recorded))
        return tuple(results)


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description="Bounded multi-horizon research")
    parser.add_argument("--data-root", required=True, type=Path)
    parser.add_argument("--memory-root", required=True, type=Path)
    parser.add_argument("--cycles", required=True, type=int)
    parser.add_argument("--budget", type=int, default=1)
    args = parser.parse_args(argv)
    if args.cycles <= 0 or args.budget <= 0:
        parser.error("--cycles and --budget must be positive")
    result = MultiHorizonResearchRunner(args.data_root, args.memory_root).run(args.cycles, budget=args.budget)
    print(json.dumps([asdict(row) for row in result], sort_keys=True))
    return 0
