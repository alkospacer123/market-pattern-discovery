"""Research-space cells and deterministic multi-horizon scheduling."""
from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum

from market_pattern_discovery.contracts import deterministic_hash
from market_pattern_discovery.data import TIMEFRAMES


class ResearchHorizon(StrEnum):
    SCALPING = "Scalping"
    INTRADAY = "Intraday"
    MEDIUM_TERM = "Medium-term"


class ResearchTrack(StrEnum):
    KNOWN = "KNOWN"
    UNKNOWN = "UNKNOWN"


PROFILES = {
    ResearchHorizon.SCALPING: (("M1", "M5"), ("M15",)),
    ResearchHorizon.INTRADAY: (("M5", "M15", "M30"), ("H1", "D1")),
    ResearchHorizon.MEDIUM_TERM: (("H1", "D1"), ("H1", "D1")),
}


@dataclass(frozen=True, slots=True)
class ResearchCell:
    symbol: str
    research_horizon: ResearchHorizon
    primary_timeframe: str
    context_timeframes: tuple[str, ...]
    research_track: ResearchTrack
    feature_version: str = "1"
    context_version: str = "1"

    def __post_init__(self) -> None:
        object.__setattr__(self, "research_horizon", ResearchHorizon(self.research_horizon))
        object.__setattr__(self, "research_track", ResearchTrack(self.research_track))
        executions, contexts = PROFILES[self.research_horizon]
        if self.symbol not in {"CNY", "Si"} or self.primary_timeframe not in executions:
            raise ValueError("cell is outside its canonical research profile")
        if tuple(self.context_timeframes) != contexts or any(tf not in TIMEFRAMES for tf in contexts):
            raise ValueError("invalid context timeframes")

    @property
    def identity(self) -> str:
        return deterministic_hash(self)


def research_space() -> tuple[ResearchCell, ...]:
    return tuple(
        ResearchCell(symbol, horizon, primary, contexts, track)
        for symbol in ("CNY", "Si")
        for horizon, (primaries, contexts) in PROFILES.items()
        for primary in primaries
        for track in ResearchTrack
    )


class MultiHorizonScheduler:
    def __init__(self, cells: tuple[ResearchCell, ...] | None = None, *, seed: int = 35) -> None:
        self.cells, self.seed = cells or research_space(), seed

    def plan(self, completed: set[str], limit: int) -> tuple[ResearchCell, ...]:
        if limit <= 0:
            raise ValueError("limit must be positive")
        unseen = (cell for cell in self.cells if cell.identity not in completed)
        return tuple(sorted(unseen, key=lambda cell: deterministic_hash(
            {"seed": self.seed, "cell": cell.identity}))[:limit])
