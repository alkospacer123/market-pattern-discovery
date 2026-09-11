"""Bounded, causal scientific research for the production multi-horizon loop."""
from __future__ import annotations

import argparse
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any
import json

import pandas as pd
import numpy as np

from market_pattern_discovery.contracts import deterministic_hash
from market_pattern_discovery.backtest import BacktestEngine, CostModel
from market_pattern_discovery.data import MarketDataLoader, timeframe
from market_pattern_discovery.features.context import CausalContextEngine
from market_pattern_discovery.discovery.protocol import benjamini_hochberg, day_block_bootstrap
from market_pattern_discovery.research import (
    Evidence, Evaluation, Hypothesis, HypothesisScheduler, KnowledgeRecord,
    MultiHorizonScheduler, ResearchCell,
    ResearchIntelligence, ResearchMemory, ScientificResult, UnifiedResearchExecutor,
    StrategyBuilder, TradingCandidateGenerator, create_pattern_effect,
)
from market_pattern_discovery.validation import ValidationEngine

from .trading_pipeline import AutonomousTradingPipeline
from .run_artifacts import AutonomousRunArtifacts

UNKNOWN_METHODS = ("univariate_screen", "interaction_search", "subgroup_discovery")
PRODUCTION_COSTS = CostModel(transaction_cost=.001, slippage=.0005)
PRODUCTION_DATA_VERSION = "finam-development-2026-v1"


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
    frame = pd.DataFrame({"target": target, "moscow_trading_date": target.index.map(
        lambda _: None)}, index=target.index)
    # The target carries the causal preparation frame's trading dates in attrs.
    frame["moscow_trading_date"] = target.attrs.get("trading_date", pd.Series(target.index, index=target.index))
    uncertainty = (day_block_bootstrap(frame, selected, "target", statistic="mean_difference",
        replications=5, seed=20260401) if len(baseline) and len(conditional) else
        {"method": "moscow_trading_date_resampling", "replications": 0,
         "seed": 20260401, "lower": None, "upper": None, "standard_error": None})
    fold_effects = []
    for positions in np.array_split(np.arange(len(target)), 3):
        fold_valid = valid.iloc[positions]
        fold_selected = selected.iloc[positions]
        b = pd.to_numeric(target.iloc[positions][fold_valid], errors="coerce")
        a = pd.to_numeric(target.iloc[positions][fold_selected], errors="coerce")
        fold_effects.append(float(a.mean() - b.mean()) if len(a) and len(b) else None)
    same_sign = int(sum(value is not None and effect is not None and
                        np.sign(value) == np.sign(effect) for value in fold_effects))
    lower, upper = uncertainty.get("lower"), uncertainty.get("upper")
    reliable = bool(lower is not None and upper is not None and (lower > 0 or upper < 0))
    raw_p = float(min(1.0, 2 * min(sum(value <= 0 for value in fold_effects if value is not None),
                                   sum(value >= 0 for value in fold_effects if value is not None)) /
                            max(1, sum(value is not None for value in fold_effects))))
    adjusted = float(benjamini_hochberg([raw_p])[0])
    metadata = {"cell_id": cell.identity, "track": hypothesis.track,
                "method": hypothesis.method, "state": hypothesis.state_definition,
                "target": hypothesis.target_definition,
                "baseline": hypothesis.baseline_definition,
                "hypothesis_id": hypothesis_id,
                "baseline_sample_size": int(valid.sum()),
                "baseline_statistic": baseline_stat,
                "conditional_statistic": conditional_stat,
                "context_consumed": True, "feature_version": "scientific-inventory-v1",
                "target_version": "behavioural-targets-v1"}
    evaluation = Evaluation(evaluation_id, effect, int(selected.sum()), metadata,
        hypothesis_id, baseline_stat, conditional_stat, hypothesis.target_definition,
        hypothesis.method, hypothesis.context_timeframes, uncertainty,
        hypothesis.state_definition, hypothesis.baseline_definition,
        {"method": "three_ordered_walk_forward_blocks", "fold_effects": fold_effects,
         "same_sign_folds": same_sign},
        {"method": "zero_effect_null", "raw_p": raw_p},
        {"method": "benjamini_hochberg", "family": f"{cell.symbol}|{cell.primary_timeframe}|{hypothesis.method}|{hypothesis.target_definition}",
         "family_size_observed": 1, "adjusted_q": adjusted})
    enough = bool(len(baseline) >= 10 and len(conditional) >= 5)
    practical = bool(effect is not None and abs(effect) > 1e-12)
    stable = same_sign >= 2
    qualifies = enough and practical and reliable and stable and adjusted <= .05
    evidence = Evidence(evaluation_id, qualifies,
        "sample, effect, bootstrap reliability, walk-forward stability and BH qualification satisfied"
        if qualifies else "one or more scientific qualification gates failed",
        enough, practical, reliable and adjusted <= .05, stable)
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
    key = hypothesis.target_definition.removesuffix("_same_trading_day").removesuffix("_cross_day_D1")
    return _scientific_result(cell, hypothesis, mask,
                              features[key] if key in features else features["future_signed_return"])


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
    key = hypothesis.target_definition.removesuffix("_same_trading_day").removesuffix("_cross_day_D1")
    return _scientific_result(cell, hypothesis, mask,
                              features[key] if key in features else features["future_signed_return"])


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
        self._prepared: dict[str, tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]] = {}
        self._trading_data: dict[tuple[str, tuple[str, ...]], dict[str, pd.DataFrame]] = {}
        self.trading_pipeline = AutonomousTradingPipeline(
            self.memory, self._strategy_market_data,
            backtest_engine=BacktestEngine(PRODUCTION_COSTS),
            validation_engine=ValidationEngine(PRODUCTION_COSTS),
            data_version=PRODUCTION_DATA_VERSION,
        )

    def _strategy_market_data(self, strategy: Any) -> dict[str, pd.DataFrame]:
        """Load the candidate's exact scope with timestamps at bar availability."""
        timeframes = (strategy.execution_timeframe, *strategy.context_timeframes)
        key = (strategy.symbol, timeframes)
        if key not in self._trading_data:
            frames = {}
            for timeframe_id in dict.fromkeys(timeframes):
                frame = self.loader.load(strategy.symbol, timeframe_id).copy()
                # MarketDataLoader timestamps are candle opens. Trading engines
                # consume observation times, so expose a bar only at its close.
                frame["timestamp"] = frame["timestamp"] + timeframe(timeframe_id).duration
                frames[timeframe_id] = frame
            self._trading_data[key] = frames
        return self._trading_data[key]

    def _prepare(self, cell: ResearchCell) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
        if cell.identity in self._prepared:
            return self._prepared[cell.identity]
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
        features["body_to_range"] = (market.close - market.open).abs().div(features["range"].replace(0, np.nan))
        features["close_position"] = market.close.sub(market.low).div(features["range"].replace(0, np.nan))
        grouped_return = features["return_1"].groupby(trading_day)
        grouped_range = features["range"].groupby(trading_day)
        features["volatility_5"] = grouped_return.transform(lambda x: x.shift(1).rolling(5).std())
        features["range_percentile_20"] = grouped_range.transform(
            lambda x: x.shift(1).rolling(20).rank(pct=True))
        features["momentum_5"] = market.close.groupby(trading_day).pct_change(5)
        prior_low = market.low.groupby(trading_day).transform(lambda x: x.shift(1).rolling(20).min())
        prior_high = market.high.groupby(trading_day).transform(lambda x: x.shift(1).rolling(20).max())
        features["position_in_range_20"] = market.close.sub(prior_low).div(prior_high.sub(prior_low))
        features["range_median_7"] = grouped_range.transform(
            lambda x: x.shift(1).rolling(7).median())
        features["prior_high_20"] = prior_high
        features["context_direction"] = pd.concat(context_returns, axis=1).mean(axis=1)
        features["future_signed_return"] = next_close.div(market.close).sub(1)
        features["future_volatility"] = features["future_signed_return"].abs()
        features["future_range_expansion"] = features["range"].shift(-1).div(features["range"].replace(0, np.nan)).sub(1)
        features["future_direction"] = np.sign(features["future_signed_return"])
        features["future_state_transition"] = np.sign(features["return_1"].shift(-1)).ne(
            np.sign(features["return_1"])).astype(float)
        for column in ("future_signed_return", "future_volatility", "future_range_expansion",
                       "future_direction", "future_state_transition"):
            if cell.primary_timeframe != "D1":
                features[column] = features[column].where(trading_day.eq(trading_day.shift(-1)))
            features[column].attrs["trading_date"] = pd.Series(trading_day, index=features.index)
        prepared = (market, aligned, features)
        self._prepared[cell.identity] = prepared
        return prepared

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
                self.memory.record_scientific_finding(evaluation, evidence, effect, hypothesis)
                if effect is not None:
                    candidate = TradingCandidateGenerator().generate(
                        effect, evaluation, evidence, hypothesis)
                    self.memory.add_trading_candidate(candidate)
                    StrategyBuilder().build_and_persist(candidate, self.memory)
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
        # This is the sole production hand-off into trading execution. The
        # restart-safe pipeline discovers all newly persisted strategies and
        # independently advances every stage that is still missing.
        self.trading_pipeline.run()
        return tuple(results)


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description="Bounded multi-horizon research")
    parser.add_argument("--data-root", required=True, type=Path)
    parser.add_argument("--memory-root", required=True, type=Path)
    parser.add_argument("--cycles", required=True, type=int)
    parser.add_argument("--budget", type=int, default=1)
    parser.add_argument("--artifacts-root", type=Path,
        default=Path("/workspace/market-pattern-artifacts"),
        help="persistent storage root (default: /workspace/market-pattern-artifacts)")
    parser.add_argument("--run-id", help="stable run directory name")
    parser.add_argument("--data-manifest", type=Path,
        help="manifest whose bytes bind the run to its external, read-only data")
    args = parser.parse_args(argv)
    if not args.data_manifest:
        parser.error("--data-manifest is required for the persistent artifact bundle")
    runner = MultiHorizonResearchRunner(args.data_root, args.memory_root)
    result = runner.run(args.cycles, budget=args.budget)
    AutonomousRunArtifacts(args.artifacts_root).export(
        runner.memory, data_manifest=args.data_manifest,
        repository=Path(__file__).resolve().parents[3], run_id=args.run_id, seed=35,
        launch_parameters={"cycles": args.cycles, "budget": args.budget, "seed": 35})
    print(json.dumps([asdict(row) for row in result], sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
