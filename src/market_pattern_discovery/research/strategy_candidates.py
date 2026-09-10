"""Bounded, deterministic construction of strategies from trade hypotheses.

Strategy building is deliberately mechanical: it enumerates a small reviewed
set of definitions and does not inspect returns or performance metrics.
"""
from __future__ import annotations

from dataclasses import asdict, dataclass
from enum import StrEnum
from itertools import product
from typing import Any, Mapping

from market_pattern_discovery.contracts import deterministic_hash

from .trading_candidates import (
    CandidateFamily, TradingCandidate, TradingCandidateStatus, TradingDirection,
)


class EntryType(StrEnum):
    CLOSE_ENTRY = "CLOSE_ENTRY"
    BREAKOUT_ENTRY = "BREAKOUT_ENTRY"
    CONFIRMATION_ENTRY = "CONFIRMATION_ENTRY"


class RiskType(StrEnum):
    ATR_STOP = "ATR_STOP"
    STRUCTURE_STOP = "STRUCTURE_STOP"
    FIXED_DISTANCE_STOP = "FIXED_DISTANCE_STOP"


class ExitType(StrEnum):
    TIME_EXIT = "TIME_EXIT"
    STATE_INVALIDATION_EXIT = "STATE_INVALIDATION_EXIT"
    SIMPLE_TARGET_EXIT = "SIMPLE_TARGET_EXIT"


class StrategyCandidateStatus(StrEnum):
    CREATED = "CREATED"
    READY_FOR_BACKTEST = "READY_FOR_BACKTEST"
    REJECTED = "REJECTED"


@dataclass(frozen=True, slots=True)
class EntryDefinition:
    entry_type: EntryType
    parameters: Mapping[str, Any]

    def __post_init__(self) -> None:
        object.__setattr__(self, "entry_type", EntryType(self.entry_type))
        object.__setattr__(self, "parameters", dict(self.parameters))


@dataclass(frozen=True, slots=True)
class RiskDefinition:
    risk_type: RiskType
    parameters: Mapping[str, Any]

    def __post_init__(self) -> None:
        object.__setattr__(self, "risk_type", RiskType(self.risk_type))
        object.__setattr__(self, "parameters", dict(self.parameters))


@dataclass(frozen=True, slots=True)
class ExitDefinition:
    exit_type: ExitType
    parameters: Mapping[str, Any]

    def __post_init__(self) -> None:
        object.__setattr__(self, "exit_type", ExitType(self.exit_type))
        object.__setattr__(self, "parameters", dict(self.parameters))


@dataclass(frozen=True, slots=True)
class StrategyCandidate:
    """An unevaluated execution hypothesis sourced from one TradingCandidate."""

    strategy_id: str
    source_trading_candidate_id: str
    symbol: str
    horizon: str
    execution_timeframe: str
    context_timeframes: tuple[str, ...]
    direction: TradingDirection
    description: str
    market_condition: Mapping[str, Any]
    candidate_family: CandidateFamily
    entry: EntryDefinition
    risk: RiskDefinition
    exit: ExitDefinition
    status: StrategyCandidateStatus
    schema_version: str = "strategy-candidate-v1"

    def __post_init__(self) -> None:
        required = (self.strategy_id, self.source_trading_candidate_id, self.symbol,
                    self.horizon, self.execution_timeframe, self.description,
                    self.schema_version)
        if not all(required) or not self.context_timeframes or not self.market_condition:
            raise ValueError("strategy candidate requires complete source and market scope")
        object.__setattr__(self, "context_timeframes", tuple(self.context_timeframes))
        object.__setattr__(self, "market_condition", dict(self.market_condition))
        object.__setattr__(self, "direction", TradingDirection(self.direction))
        object.__setattr__(self, "candidate_family", CandidateFamily(self.candidate_family))
        object.__setattr__(self, "entry", _definition(EntryDefinition, self.entry))
        object.__setattr__(self, "risk", _definition(RiskDefinition, self.risk))
        object.__setattr__(self, "exit", _definition(ExitDefinition, self.exit))
        object.__setattr__(self, "status", StrategyCandidateStatus(self.status))


def _definition(definition_type, value):
    return value if isinstance(value, definition_type) else definition_type(**value)


# These are definitions, not tunable ranges. Changing one is a builder-version
# change and therefore produces a new deterministic identity namespace.
ENTRIES = (
    EntryDefinition(EntryType.CLOSE_ENTRY, {"timing": "after_signal_close"}),
    EntryDefinition(EntryType.BREAKOUT_ENTRY, {"level": "signal_extreme"}),
    EntryDefinition(EntryType.CONFIRMATION_ENTRY, {"confirmation_bars": 1}),
)
RISKS = (
    RiskDefinition(RiskType.ATR_STOP, {"atr_period": 14, "atr_multiple": 1.0}),
    RiskDefinition(RiskType.STRUCTURE_STOP, {"reference": "signal_structure"}),
    RiskDefinition(RiskType.FIXED_DISTANCE_STOP, {"distance_units": 1}),
)
EXITS = (
    ExitDefinition(ExitType.TIME_EXIT, {"bars": 10}),
    ExitDefinition(ExitType.STATE_INVALIDATION_EXIT, {"state": "market_condition"}),
    ExitDefinition(ExitType.SIMPLE_TARGET_EXIT, {"distance_units": 1}),
)


class StrategyBuilder:
    """Enumerate exactly the reviewed 3×3×3 strategy construction space."""

    def __init__(self, builder_version: str = "strategy-builder-v1") -> None:
        if not builder_version:
            raise ValueError("builder_version is required")
        self.builder_version = builder_version

    def build(self, source: TradingCandidate) -> tuple[StrategyCandidate, ...]:
        if not isinstance(source, TradingCandidate):
            raise TypeError("StrategyCandidate source must be a TradingCandidate")
        if (source.status is not TradingCandidateStatus.READY_FOR_STRATEGY_SEARCH or
                source.direction not in {TradingDirection.LONG, TradingDirection.SHORT}):
            raise ValueError("TradingCandidate is not valid for strategy construction")
        result = []
        for entry, risk, exit_definition in product(ENTRIES, RISKS, EXITS):
            identity = {
                "schema_version": "strategy-candidate-v1",
                "builder_version": self.builder_version,
                "source_trading_candidate_id": source.candidate_id,
                "entry": asdict(entry), "risk": asdict(risk),
                "exit": asdict(exit_definition),
            }
            result.append(StrategyCandidate(
                deterministic_hash(identity), source.candidate_id, source.symbol,
                source.horizon, source.execution_timeframe, source.context_timeframes,
                source.direction, source.hypothesis_description,
                source.market_state_definition, source.candidate_family, entry, risk,
                exit_definition, StrategyCandidateStatus.CREATED,
            ))
        return tuple(result)

    def build_and_persist(self, source: TradingCandidate, memory: Any
                          ) -> tuple[StrategyCandidate, ...]:
        strategies = self.build(source)
        for strategy in strategies:
            memory.add_strategy_candidate(strategy)
        return strategies


def strategy_candidate_dict(candidate: StrategyCandidate) -> dict[str, Any]:
    value = asdict(candidate)
    value["direction"] = candidate.direction.value
    value["candidate_family"] = candidate.candidate_family.value
    value["entry"]["entry_type"] = candidate.entry.entry_type.value
    value["risk"]["risk_type"] = candidate.risk.risk_type.value
    value["exit"]["exit_type"] = candidate.exit.exit_type.value
    value["status"] = candidate.status.value
    return value
