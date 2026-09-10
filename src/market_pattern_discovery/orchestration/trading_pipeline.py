"""Restart-safe orchestration of the existing post-research trading engines."""
from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Callable

from market_pattern_discovery.backtest import BacktestEngine
from market_pattern_discovery.ranking import StrategyRankingEngine
from market_pattern_discovery.research.hypotheses import Hypothesis
from market_pattern_discovery.research.intelligence import Evidence, Evaluation, PatternEffect
from market_pattern_discovery.research.strategy_candidates import StrategyBuilder
from market_pattern_discovery.research.trading_candidates import TradingCandidateGenerator
from market_pattern_discovery.validation import DataSplit, ValidationEngine


@dataclass(frozen=True, slots=True)
class PipelineRunReport:
    trading_candidates: int = 0
    strategy_candidates: int = 0
    backtests: int = 0
    validations: int = 0
    rankings: int = 0
    skipped: int = 0
    failures: int = 0


class AutonomousTradingPipeline:
    """Advance persisted scientific effects through fixed evaluation stages.

    The supplied market-data provider is the sole data boundary.  This class
    neither creates hypotheses nor changes/searches strategy definitions.
    """

    def __init__(self, memory: Any, data_provider: Callable[[Any], Any], *,
                 backtest_engine: BacktestEngine, validation_engine: ValidationEngine,
                 ranking_engine: StrategyRankingEngine | None = None,
                 split: DataSplit | None = None, data_version: str) -> None:
        if not data_version:
            raise ValueError("data_version is required")
        self.memory, self.data_provider = memory, data_provider
        self.backtest_engine, self.validation_engine = backtest_engine, validation_engine
        self.ranking_engine = ranking_engine or StrategyRankingEngine()
        self.split, self.data_version = split or DataSplit.calendar_v1(), data_version

    def _fail(self, stage: str, identifier: str, error: Exception) -> int:
        self.memory.record_pipeline_failure(stage, identifier, error)
        return 1

    @staticmethod
    def _complete_context(strategy: Any, data: Any) -> Any:
        """Represent absent declared context explicitly, never by silently dropping it."""
        if not isinstance(data, dict):
            return data
        missing = tuple(tf for tf in strategy.context_timeframes if tf not in data)
        return data if not missing else {**data, **{tf: [] for tf in missing}}

    def run(self) -> PipelineRunReport:
        counts = {name: 0 for name in PipelineRunReport.__dataclass_fields__}

        # New-format findings include the exact hypothesis needed by the
        # existing evidence gate. Older memories resume from any later object.
        known_effects = {candidate.source_pattern_effect_id
                         for candidate in self.memory.trading_candidates().values()}
        for finding in self.memory.scientific_findings():
            raw_effect, raw_hypothesis = finding.get("pattern_effect"), finding.get("hypothesis")
            if not raw_effect or not raw_hypothesis or raw_effect["effect_id"] in known_effects:
                counts["skipped"] += 1
                continue
            try:
                candidate = TradingCandidateGenerator().generate(
                    PatternEffect(**raw_effect), Evaluation(**finding["evaluation"]),
                    Evidence(**finding["evidence"]), Hypothesis(**raw_hypothesis))
                counts["trading_candidates"] += int(self.memory.add_trading_candidate(candidate))
                known_effects.add(raw_effect["effect_id"])
            except Exception as error:
                counts["failures"] += self._fail("TRADING_CANDIDATE", raw_effect["effect_id"], error)

        strategies = self.memory.strategy_candidates()
        for candidate in sorted(self.memory.trading_candidates().values(), key=lambda x: x.candidate_id):
            if any(row.source_trading_candidate_id == candidate.candidate_id for row in strategies.values()):
                counts["skipped"] += 1
                continue
            try:
                built = StrategyBuilder().build_and_persist(candidate, self.memory)
                counts["strategy_candidates"] += len(built)
                strategies.update({row.strategy_id: row for row in built})
            except Exception as error:
                counts["failures"] += self._fail("STRATEGY", candidate.candidate_id, error)

        backtests = self.memory.backtest_results()
        for strategy in sorted(strategies.values(), key=lambda x: x.strategy_id):
            if any(row.strategy_id == strategy.strategy_id for row in backtests.values()):
                counts["skipped"] += 1
                continue
            try:
                data = self._complete_context(strategy, self.data_provider(strategy))
                result = self.backtest_engine.run(strategy, data, data_version=self.data_version)
                counts["backtests"] += int(self.memory.add_backtest_result(result))
                backtests[result.backtest_id] = result
            except Exception as error:
                counts["failures"] += self._fail("BACKTEST", strategy.strategy_id, error)

        validations = self.memory.validation_reports()
        for backtest in sorted(backtests.values(), key=lambda x: x.backtest_id):
            if any(row.backtest_id == backtest.backtest_id for row in validations.values()):
                counts["skipped"] += 1
                continue
            strategy = strategies[backtest.strategy_id]
            try:
                data = self._complete_context(strategy, self.data_provider(strategy))
                report = self.validation_engine.validate(strategy, backtest, data,
                    split=self.split, data_version=self.data_version)
                counts["validations"] += int(self.memory.add_validation_report(report))
                validations[report.validation_id] = report
            except Exception as error:
                counts["failures"] += self._fail("VALIDATION", backtest.backtest_id, error)

        rankings = self.memory.strategy_rankings()
        trading = self.memory.trading_candidates()
        pending = []
        for report in sorted(validations.values(), key=lambda x: x.validation_id):
            if any(row.validation_id == report.validation_id for row in rankings.values()):
                counts["skipped"] += 1
                continue
            strategy = strategies[report.strategy_id]
            pending.append((report, strategy, trading[strategy.source_trading_candidate_id]))
        if pending:
            try:
                for ranking in self.ranking_engine.rank(pending):
                    counts["rankings"] += int(self.memory.add_strategy_ranking(ranking))
            except Exception as error:
                # Ranking is batch-atomic from the pipeline's perspective: if
                # scoring fails, no new ranking is appended by this block.
                counts["failures"] += self._fail("RANKING", pending[0][0].validation_id, error)
        return PipelineRunReport(**counts)
