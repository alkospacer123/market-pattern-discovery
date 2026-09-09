"""Bounded, causal scientific research for the production multi-horizon loop."""
from __future__ import annotations

import argparse
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any
import json

import pandas as pd

from market_pattern_discovery.contracts import deterministic_hash
from market_pattern_discovery.data import MarketDataLoader
from market_pattern_discovery.features.context import CausalContextEngine
from market_pattern_discovery.research import (
    Evidence, Evaluation, Hypothesis, HypothesisScheduler, KnowledgeRecord,
    MultiHorizonScheduler, ResearchCell,
    ResearchIntelligence, ResearchMemory, ScientificResult, UnifiedResearchExecutor,
    create_pattern_effect,
)

UNKNOWN_METHODS = ("univariate_screen", "interaction_search", "subgroup_discovery")


def _context_definition(cell: ResearchCell, context: pd.DataFrame) -> list[str]:
    columns = [f"context_{timeframe}_close" for timeframe in cell.context_timeframes]
    if any(column not in context for column in columns):
        raise ValueError("handler requires causally aligned context columns")
    return columns


def _scientific_result(cell: ResearchCell, hypothesis: Hypothesis,
                       mask: pd.Series, target: pd.Series) -> ScientificResult:
    """Compare a causal state with the unconditional same-day behavioural baseline."""
    valid = target.notna()
    selected = valid & mask.fillna(False)
    baseline = pd.to_numeric(target.loc[valid], errors="coerce")
    conditional = pd.to_numeric(target.loc[selected], errors="coerce")
    baseline_stat = float(baseline.mean()) if len(baseline) else None
    conditional_stat = float(conditional.mean()) if len(conditional) else None
    effect = (conditional_stat - baseline_stat
              if conditional_stat is not None and baseline_stat is not None else None)
    hypothesis_id = hypothesis.hypothesis_id
    evaluation_id = deterministic_hash({"hypothesis_id": hypothesis_id,
                                        "scientific_contract": "multi-horizon-v2"})
    metadata = {"cell_id": cell.identity, "track": hypothesis.track,
                "method": hypothesis.method, "state": hypothesis.state_definition,
                "target": hypothesis.target_definition,
                "baseline": hypothesis.baseline_definition,
                "hypothesis_id": hypothesis_id,
                "baseline_sample_size": int(valid.sum()),
                "baseline_statistic": baseline_stat,
                "conditional_statistic": conditional_stat,
                "context_consumed": True}
    evaluation = Evaluation(evaluation_id, effect, int(selected.sum()), metadata,
        hypothesis_id, baseline_stat, conditional_stat, hypothesis.target_definition,
        hypothesis.method, hypothesis.context_timeframes)
    qualifies = bool(len(baseline) >= 10 and len(conditional) >= 5 and effect is not None)
    evidence = Evidence(evaluation_id, qualifies,
        "minimum baseline=10 and condition=5 satisfied" if qualifies
        else "insufficient baseline or conditional observations")
    return ScientificResult(hypothesis.method, hypothesis_id, evaluation, evidence)


def _condition_mask(condition: dict[str, Any], market_data: pd.DataFrame,
                    features: pd.DataFrame) -> pd.Series:
    feature, operator = condition["feature"], condition["operator"]
    values = market_data["close"] if feature == "close" else features[feature]
    if operator.startswith("quantile_"):
        threshold = float(values.quantile(float(condition["quantile"])))
        return values >= threshold if operator == "quantile_ge" else values <= threshold
    if operator == "nonnegative": return values >= 0
    if operator == "negative": return values < 0
    if operator == "above_prior_high_20": return values > features["prior_high_20"]
    if operator == "not_above_prior_high_20": return values <= features["prior_high_20"]
    raise ValueError(f"unsupported causal state operator: {operator}")


def _known(*, cell: ResearchCell, market_data: pd.DataFrame,
           context: pd.DataFrame, features: pd.DataFrame,
           hypothesis: Hypothesis | None = None) -> ScientificResult:
    """Measure a deterministic pre-existing causal market-event hypothesis."""
    context_columns = _context_definition(cell, context)
    if hypothesis is None:
        from market_pattern_discovery.research import known_hypotheses
        hypothesis = next(known_hypotheses(cell))
    mask = pd.Series(True, index=features.index)
    for condition in hypothesis.state_definition["conditions"]:
        mask &= _condition_mask(condition, market_data, features)
    return _scientific_result(cell, hypothesis, mask, features["future_signed_return"])


def _unknown(*, cell: ResearchCell, market_data: pd.DataFrame,
             context: pd.DataFrame, features: pd.DataFrame,
             hypothesis: Hypothesis | None = None) -> ScientificResult:
    """Run one bounded autonomous state hypothesis, unrestricted by known families."""
    context_columns = _context_definition(cell, context)
    if hypothesis is None:
        from market_pattern_discovery.research import unknown_hypotheses
        # Preserve direct-call coverage of all methods deterministically.
        wanted = UNKNOWN_METHODS[int(cell.identity[-8:], 16) % len(UNKNOWN_METHODS)]
        hypothesis = next(h for h in unknown_hypotheses(cell) if h.method == wanted and
            (h.state_definition.get("subgroup", {}).get("feature") == "context_direction" or
             any(c["feature"] == "context_direction" for c in
                 h.state_definition["conditions"])))
    mask = pd.Series(True, index=features.index)
    definitions = list(hypothesis.state_definition["conditions"])
    subgroup = hypothesis.state_definition.get("subgroup")
    if subgroup: definitions.append(subgroup)
    for condition in definitions:
        mask &= _condition_mask(condition, market_data, features)
    return _scientific_result(cell, hypothesis, mask, features["future_signed_return"])


@dataclass(frozen=True, slots=True)
class CycleResult:
    cycle: int
    planned: int
    hypotheses_evaluated: int
    recorded: int


class MultiHorizonResearchRunner:
    def __init__(self, data_root: str | Path, memory_root: str | Path, *, seed: int = 35) -> None:
        self.loader = MarketDataLoader(data_root)
        self.memory = ResearchMemory(memory_root)
        self.cells = {cell.identity: cell for cell in MultiHorizonScheduler(seed=seed).cells}
        self.scheduler = HypothesisScheduler(tuple(self.cells.values()), seed=seed)
        self.context = CausalContextEngine()
        self.executor = UnifiedResearchExecutor(_known, _unknown)

    def _prepare(self, cell: ResearchCell) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
        market = self.loader.load(cell.symbol, cell.primary_timeframe)
        aligned = market
        context_returns = []
        for context_tf in cell.context_timeframes:
            aligned = aligned.drop(columns=["context_close_time"], errors="ignore")
            aligned = self.context.align(aligned, self.loader.load(cell.symbol, context_tf))
            context_returns.append(aligned[f"context_{context_tf}_close"].pct_change(fill_method=None))
        trading_day = market.timestamp.dt.tz_convert("Europe/Moscow").dt.date
        next_close = market.close.shift(-1)
        if cell.primary_timeframe != "D1":
            next_close = next_close.where(trading_day.eq(trading_day.shift(-1)))
        features = pd.DataFrame(index=market.index)
        features["return_1"] = market.close.pct_change(fill_method=None)
        features["range"] = market.high - market.low
        features["range_median_7"] = features["range"].shift(1).rolling(7).median()
        features["prior_high_20"] = market.high.shift(1).rolling(20).max()
        features["context_direction"] = pd.concat(context_returns, axis=1).mean(axis=1)
        features["future_signed_return"] = next_close.div(market.close).sub(1)
        return market, aligned, features

    def run(self, cycles: int, *, budget: int = 1) -> tuple[CycleResult, ...]:
        if cycles <= 0:
            raise ValueError("cycles must be positive; unlimited execution is forbidden")
        if budget <= 0:
            raise ValueError("budget must be positive")
        results = []
        for cycle in range(cycles):
            completed = self.memory.completed_hypothesis_ids()
            hypotheses = self.scheduler.plan(completed, budget)
            recorded = evaluated = 0
            for hypothesis in hypotheses:
                cell = self.cells[hypothesis.cell_id]
                market, context, features = self._prepare(cell)
                attempt, result = self.executor.execute(cell, market, context, features, hypothesis)
                if not self.memory.record_research_attempt(attempt):
                    continue
                evaluated += 1
                evaluation, evidence = result.evaluation, result.evidence
                effect = create_pattern_effect(evaluation, evidence)
                conclusion = ResearchIntelligence().conclude(evaluation, evidence, effect)
                self.memory.record_scientific_finding(evaluation, evidence, effect)
                record = KnowledgeRecord(
                    cell.symbol, cell.research_horizon.value, cell.primary_timeframe,
                    ",".join(cell.context_timeframes), cell.research_track.value,
                    evaluation.evaluation_id, conclusion.conclusion.value, "CURRENT",
                    {**dict(evaluation.metadata),
                     "effect_id": effect.effect_id if effect else None,
                     "evidence_qualifies": evidence.qualifies,
                     "evidence_rationale": evidence.rationale})
                recorded += int(self.memory.add_knowledge_record(record))
            results.append(CycleResult(cycle, len(hypotheses), evaluated, recorded))
        return tuple(results)


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description="Bounded multi-horizon research")
    parser.add_argument("--data-root", required=True, type=Path)
    parser.add_argument("--memory-root", required=True, type=Path)
    parser.add_argument("--cycles", required=True, type=int)
    parser.add_argument("--budget", type=int, default=1)
    args = parser.parse_args(argv)
    result = MultiHorizonResearchRunner(args.data_root, args.memory_root).run(args.cycles, budget=args.budget)
    print(json.dumps([asdict(row) for row in result], sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
