"""Immutable transport contracts; these adapt V3 facts without computing them."""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Mapping

from .hashing import deterministic_hash


def _required(**values: str) -> None:
    missing = [name for name, value in values.items() if not value]
    if missing:
        raise ValueError(f"required fields are empty: {', '.join(missing)}")


@dataclass(frozen=True, slots=True)
class CandleContract:
    instrument: str
    timeframe: str
    open_time: datetime
    close_time: datetime
    open: float
    high: float
    low: float
    close: float
    volume: float

    def __post_init__(self) -> None:
        _required(instrument=self.instrument, timeframe=self.timeframe)
        if self.open_time >= self.close_time:
            raise ValueError("a candle is observable only after a later close_time")
        if self.high < max(self.open, self.close) or self.low > min(self.open, self.close) or self.low > self.high:
            raise ValueError("invalid OHLC bounds")
        if self.volume < 0:
            raise ValueError("volume must be non-negative")


@dataclass(frozen=True, slots=True)
class SignalContract:
    strategy_id: str
    instrument: str
    timeframe: str
    signal_time: datetime
    side: str
    bar_index: int
    attributes: Mapping[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        _required(strategy_id=self.strategy_id, instrument=self.instrument, timeframe=self.timeframe)
        if self.side not in {"LONG", "SHORT"} or self.bar_index < 0:
            raise ValueError("side must be LONG/SHORT and bar_index non-negative")
        object.__setattr__(self, "attributes", dict(self.attributes))


@dataclass(frozen=True, slots=True)
class StrategyContract:
    strategy_id: str
    version: str
    parameters: Mapping[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        _required(strategy_id=self.strategy_id, version=self.version)
        object.__setattr__(self, "parameters", dict(self.parameters))


@dataclass(frozen=True, slots=True)
class MetricsContract:
    strategy_id: str
    instrument: str
    exit_configuration: str
    friction_scenario: str
    values: Mapping[str, Any]

    def __post_init__(self) -> None:
        _required(strategy_id=self.strategy_id, instrument=self.instrument,
                  exit_configuration=self.exit_configuration, friction_scenario=self.friction_scenario)
        object.__setattr__(self, "values", dict(self.values))


@dataclass(frozen=True, slots=True)
class ManifestContract:
    kind: str
    version: str
    payload: Mapping[str, Any]

    def __post_init__(self) -> None:
        _required(kind=self.kind, version=self.version)
        object.__setattr__(self, "payload", dict(self.payload))

    @property
    def manifest_id(self) -> str:
        return deterministic_hash(self)
