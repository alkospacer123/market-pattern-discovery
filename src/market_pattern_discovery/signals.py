"""Deterministic scientific-hypothesis to executable-signal translation.

The translator is deliberately a compiler, not a search procedure.  Its fixed
v1 rules consume no prices, outcomes, rankings, or performance measurements.
"""
from __future__ import annotations

from dataclasses import asdict, dataclass
from enum import StrEnum
from typing import Any, Mapping

from market_pattern_discovery.contracts import deterministic_hash
from market_pattern_discovery.research.strategy_candidates import (
    EntryDefinition, ExitDefinition, RiskDefinition, StrategyCandidate,
)
from market_pattern_discovery.research.trading_candidates import TradingDirection


class SignalType(StrEnum):
    LEVEL_REJECTION = "LEVEL_REJECTION"
    BREAKOUT = "BREAKOUT"
    MEAN_REVERSION = "MEAN_REVERSION"
    TREND_CONTINUATION = "TREND_CONTINUATION"


@dataclass(frozen=True, slots=True)
class EntrySemantics:
    signal_candle: str
    confirmation_candle: str
    execution_candle: str

    def __post_init__(self) -> None:
        if not all((self.signal_candle, self.confirmation_candle, self.execution_candle)):
            raise ValueError("complete entry semantics are required")


@dataclass(frozen=True, slots=True)
class ExecutableSignalDefinition:
    """Immutable, fully lineage-bound input accepted by ``BacktestEngine``."""

    signal_id: str
    version: str
    source_strategy_candidate_id: str
    symbol: str
    execution_timeframe: str
    context_timeframes: tuple[str, ...]
    direction: TradingDirection
    signal_type: SignalType
    conditions: tuple[Mapping[str, Any], ...]
    entry_semantics: EntrySemantics
    risk: RiskDefinition
    exit: ExitDefinition

    def __post_init__(self) -> None:
        required = (self.signal_id, self.version, self.source_strategy_candidate_id,
                    self.symbol, self.execution_timeframe)
        if not all(required) or not self.context_timeframes or not self.conditions:
            raise ValueError("executable signal requires identity, lineage, scope, and conditions")
        object.__setattr__(self, "context_timeframes", tuple(self.context_timeframes))
        object.__setattr__(self, "direction", TradingDirection(self.direction))
        if self.direction not in {TradingDirection.LONG, TradingDirection.SHORT}:
            raise ValueError("executable signal direction must be LONG or SHORT")
        object.__setattr__(self, "signal_type", SignalType(self.signal_type))
        object.__setattr__(self, "conditions", tuple(dict(row) for row in self.conditions))
        if not isinstance(self.entry_semantics, EntrySemantics):
            object.__setattr__(self, "entry_semantics", EntrySemantics(**self.entry_semantics))
        if not isinstance(self.risk, RiskDefinition):
            object.__setattr__(self, "risk", RiskDefinition(**self.risk))
        if not isinstance(self.exit, ExitDefinition):
            object.__setattr__(self, "exit", ExitDefinition(**self.exit))

    def to_dict(self) -> dict[str, Any]:
        return {"signal_id": self.signal_id, "version": self.version,
                "source_strategy_candidate_id": self.source_strategy_candidate_id,
                "symbol": self.symbol, "execution_timeframe": self.execution_timeframe,
                "context_timeframes": list(self.context_timeframes),
                "direction": self.direction.value, "signal_type": self.signal_type.value,
                "conditions": [dict(row) for row in self.conditions],
                "entry_semantics": asdict(self.entry_semantics),
                "risk": {"risk_type": self.risk.risk_type.value,
                         "parameters": dict(self.risk.parameters)},
                "exit": {"exit_type": self.exit.exit_type.value,
                         "parameters": dict(self.exit.parameters)}}

    @classmethod
    def from_dict(cls, value: Mapping[str, Any]) -> "ExecutableSignalDefinition":
        return cls(**dict(value))

    @property
    def strategy_id(self) -> str:
        """Lineage alias used by result-producing engine integrations."""
        return self.source_strategy_candidate_id


class ScientificSignalTranslator:
    """Compile exactly four reviewed signal primitives with fixed v1 rules."""

    VERSION = "executable-signal-v1"

    def translate(self, strategy: StrategyCandidate) -> ExecutableSignalDefinition:
        if not isinstance(strategy, StrategyCandidate):
            raise TypeError("translation requires a lineage-complete StrategyCandidate")
        source = str(strategy.market_condition).lower()
        if "equal_high" in source or "equal high" in source:
            kind, primitive = SignalType.LEVEL_REJECTION, "EQUAL_HIGH"
        elif "equal_low" in source or "equal low" in source:
            kind, primitive = SignalType.LEVEL_REJECTION, "EQUAL_LOW"
        elif "breakout" in source or "break" in source:
            kind, primitive = SignalType.BREAKOUT, "CLOSE_BREAKS_PRIOR_EXTREME"
        elif "mean_reversion" in source or "mean reversion" in source or "deviation" in source:
            kind, primitive = SignalType.MEAN_REVERSION, "DEVIATION_FROM_ROLLING_MEAN"
        else:
            # Known causal states compile to the sole generic v1 primitive;
            # this is a fixed semantic mapping rather than a fitted choice.
            kind, primitive = SignalType.TREND_CONTINUATION, "DIRECTIONAL_CONTINUATION"
        conditions = self._conditions(kind, primitive, strategy.direction)
        if (kind is SignalType.TREND_CONTINUATION
                and all(isinstance(value, (str, int, float, bool, type(None)))
                        for value in strategy.market_condition.values())):
            conditions += ({"type": "OBSERVABLE_FIELDS", "condition": "ALL_EQUAL",
                            "values": dict(strategy.market_condition)},)
        semantics = EntrySemantics(
            "closed candle satisfies all potential conditions",
            "next closed candle satisfies the fixed directional confirmation",
            "open of the candle after confirmation, within the same trading day",
        )
        basis = {"version": self.VERSION,
                 "source_strategy_candidate_id": strategy.strategy_id,
                 "symbol": strategy.symbol,
                 "execution_timeframe": strategy.execution_timeframe,
                 "context_timeframes": strategy.context_timeframes,
                 "direction": strategy.direction.value, "signal_type": kind.value,
                 "conditions": conditions, "entry_semantics": asdict(semantics),
                 "risk": asdict(strategy.risk), "exit": asdict(strategy.exit)}
        return ExecutableSignalDefinition(
            deterministic_hash(basis), self.VERSION, strategy.strategy_id, strategy.symbol,
            strategy.execution_timeframe, strategy.context_timeframes, strategy.direction,
            kind, conditions, semantics, strategy.risk, strategy.exit)

    @staticmethod
    def _conditions(kind: SignalType, primitive: str, direction: TradingDirection
                    ) -> tuple[Mapping[str, Any], ...]:
        side = direction.value
        if kind is SignalType.LEVEL_REJECTION:
            return ({"type": "PRICE_LEVEL", "condition": primitive,
                     "lookback": 3, "relative_tolerance": 0.001},
                    {"type": "CANDLE", "condition": "REJECTION", "direction": side})
        if kind is SignalType.BREAKOUT:
            return ({"type": "BREAKOUT", "condition": primitive, "lookback": 3},)
        if kind is SignalType.MEAN_REVERSION:
            return ({"type": "MEAN_REVERSION", "condition": primitive,
                     "lookback": 3, "deviation_ranges": 2.0},)
        return ({"type": "TREND", "condition": primitive, "direction": side},)
