"""Deterministic, evaluation-only ranking of validated strategies."""
from __future__ import annotations

from dataclasses import asdict, dataclass
from enum import StrEnum
from math import isfinite
from typing import Any, Iterable, Mapping

from market_pattern_discovery.contracts import deterministic_hash
from market_pattern_discovery.research.strategy_candidates import StrategyCandidate
from market_pattern_discovery.research.trading_candidates import TradingCandidate
from market_pattern_discovery.validation import ValidationReport, ValidationStatus


class RankingStatus(StrEnum):
    RANKED = "RANKED"
    REJECTED = "REJECTED"
    INSUFFICIENT_DATA = "INSUFFICIENT_DATA"


@dataclass(frozen=True, slots=True)
class StrategyRanking:
    ranking_id: str
    strategy_id: str
    validation_id: str
    trading_candidate_id: str
    pattern_effect_id: str
    symbol: str
    horizon: str
    timeframe: str
    scientific_score: float
    statistical_score: float
    backtest_score: float
    validation_score: float
    risk_score: float
    composite_score: float
    position: int | None
    status: RankingStatus
    ranking_version: str
    engine_version: str

    def __post_init__(self) -> None:
        object.__setattr__(self, "status", RankingStatus(self.status))

    def to_dict(self) -> dict[str, Any]:
        value = asdict(self)
        value["status"] = self.status.value
        return value

    @classmethod
    def from_dict(cls, value: Mapping[str, Any]) -> "StrategyRanking":
        return cls(**dict(value))


class StrategyRankingEngine:
    """Apply one public formula to immutable reports; never search or optimize."""

    def __init__(self, *, ranking_version: str = "strategy-ranking-formula-v1",
                 engine_version: str = "strategy-ranking-engine-v1") -> None:
        if not ranking_version or not engine_version:
            raise ValueError("ranking and engine versions are required")
        self.ranking_version, self.engine_version = ranking_version, engine_version

    @staticmethod
    def _cap(value: float, maximum: float) -> float:
        return max(0.0, min(maximum, value)) if isfinite(value) else 0.0

    def score(self, report: ValidationReport, strategy: StrategyCandidate,
              source: TradingCandidate) -> StrategyRanking:
        """Score one validated fact set; position is assigned only by ``rank``."""
        if report.strategy_id != strategy.strategy_id:
            raise ValueError("validation does not reference strategy")
        if strategy.source_trading_candidate_id != source.candidate_id:
            raise ValueError("strategy does not reference TradingCandidate")
        if (report.symbol, report.timeframe) != (strategy.symbol, strategy.execution_timeframe):
            raise ValueError("validation market scope conflicts with strategy")

        # Every component is bounded [0, 20]. No observed metric changes a weight.
        scientific = self._cap(report.sample_size / 50.0, 20.0)
        statistical = 10.0 * self._cap(report.stability_score, 1.0) + \
            10.0 * self._cap(report.parameter_sensitivity_score, 1.0)
        pf = 0.0 if report.profit_factor is None else self._cap(report.profit_factor, 2.0)
        backtest = 5.0 * pf + 5.0 * self._cap(report.expectancy, 1.0) + \
            5.0 * self._cap(report.trade_count / 20.0, 1.0)
        validation = 10.0 * self._cap(report.walk_forward_score, 1.0) + \
            10.0 * float(report.expectancy > 0.0)
        risk = 20.0 / (1.0 + max(0.0, report.max_drawdown))
        components = tuple(round(x, 8) for x in
                           (scientific, statistical, backtest, validation, risk))
        status = {ValidationStatus.ACCEPTED: RankingStatus.RANKED,
                  ValidationStatus.REJECTED: RankingStatus.REJECTED,
                  ValidationStatus.INSUFFICIENT_DATA: RankingStatus.INSUFFICIENT_DATA}[report.status]
        composite = round(sum(components), 8) if status is RankingStatus.RANKED else 0.0
        identity = deterministic_hash({"validation_id": report.validation_id,
                                       "ranking_version": self.ranking_version})
        return StrategyRanking(identity, strategy.strategy_id, report.validation_id,
            source.candidate_id, source.source_pattern_effect_id, strategy.symbol,
            strategy.horizon, strategy.execution_timeframe, *components, composite,
            None, status, self.ranking_version, self.engine_version)

    def rank(self, inputs: Iterable[tuple[ValidationReport, StrategyCandidate, TradingCandidate]]) \
            -> tuple[StrategyRanking, ...]:
        """Assign active positions by score, then stable strategy/validation tie-breaks."""
        records = [self.score(*item) for item in inputs]
        active = sorted((r for r in records if r.status is RankingStatus.RANKED),
                        key=lambda r: (-r.composite_score, r.strategy_id, r.validation_id))
        positions = {row.ranking_id: index for index, row in enumerate(active, 1)}
        ranked = [StrategyRanking(**{**row.to_dict(), "position": positions.get(row.ranking_id)})
                  for row in records]
        return tuple(sorted(ranked, key=lambda r: (r.position is None,
                    r.position or 0, r.strategy_id, r.validation_id)))
