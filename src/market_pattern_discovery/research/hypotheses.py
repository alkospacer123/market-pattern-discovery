"""Deterministic, lazy hypothesis spaces for multi-horizon research."""
from __future__ import annotations

from dataclasses import asdict, dataclass
from itertools import chain, combinations
from typing import Iterator, Mapping, Any

from market_pattern_discovery.contracts import deterministic_hash
from .cells import ResearchCell, ResearchTrack


@dataclass(frozen=True, slots=True)
class Hypothesis:
    """A versioned scientific question, independent of its eventual observations."""
    cell_id: str
    symbol: str
    horizon: str
    primary_timeframe: str
    context_timeframes: tuple[str, ...]
    track: str
    method: str
    state_definition: Mapping[str, Any]
    target_definition: str
    baseline_definition: str
    version: str = "1"

    def __post_init__(self) -> None:
        object.__setattr__(self, "state_definition", dict(self.state_definition))

    @property
    def hypothesis_id(self) -> str:
        return deterministic_hash(asdict(self))


TARGETS = (
    "future_signed_return", "future_volatility", "future_range_expansion",
    "future_direction", "future_state_transition",
)
BASELINE = "all rows with an observable same-day next native bar"


def _make(cell: ResearchCell, method: str, state: Mapping[str, Any], target: str = TARGETS[0]) -> Hypothesis:
    target = f"{target}_cross_day_D1" if cell.primary_timeframe == "D1" else f"{target}_same_trading_day"
    baseline = ("all rows with an observable next native D1 bar" if
                cell.primary_timeframe == "D1" else BASELINE)
    return Hypothesis(cell.identity, cell.symbol, cell.research_horizon.value,
        cell.primary_timeframe, cell.context_timeframes, cell.research_track.value,
        method, state, target, baseline)


def known_hypotheses(cell: ResearchCell) -> Iterator[Hypothesis]:
    """Registry of existing causal event families; it contains no trading rules."""
    families = (
        ("momentum", {"feature": "return_1", "operator": "quantile_ge", "quantile": .5}),
        ("narrow_range", {"feature": "range", "operator": "quantile_le", "quantile": .25}),
        ("recent_high", {"feature": "close", "operator": "above_prior_high_20"}),
    )
    for ordinal, (family, condition) in enumerate(families):
        for context_state in ("nonnegative", "negative"):
            yield _make(cell, "known_event_evaluation", {
                "family": family, "conditions": [condition,
                    {"feature": "context_direction", "operator": context_state}]},
                TARGETS[ordinal % len(TARGETS)])


def unknown_hypotheses(cell: ResearchCell) -> Iterator[Hypothesis]:
    """Lazily enumerate a bounded data-independent feature/state universe."""
    states = tuple(
        {"feature": feature, "operator": operator, "quantile": quantile}
        for quantile in tuple(i / 20 for i in range(1, 20))
        for operator in ("quantile_ge", "quantile_le")
        for feature in ("return_1", "range", "body_to_range", "close_position",
                        "volatility_5", "range_percentile_20", "momentum_5",
                        "position_in_range_20")
    ) + (
        {"feature": "context_direction", "operator": "nonnegative"},
        {"feature": "context_direction", "operator": "negative"},
        {"feature": "close", "operator": "above_prior_high_20"},
        {"feature": "close", "operator": "not_above_prior_high_20"},
    )
    for ordinal, state in enumerate(states):
        yield _make(cell, "univariate_screen", {"conditions": [state]}, TARGETS[ordinal % len(TARGETS)])
    # Pair order is canonical, making the interaction universe duplicate-free.
    for ordinal, (left, right) in enumerate(combinations(states, 2)):
        if left["feature"] != right["feature"]:
            yield _make(cell, "interaction_search", {"conditions": [left, right]}, TARGETS[ordinal % len(TARGETS)])
    for ordinal, state in enumerate(states):
        for context_state in ("nonnegative", "negative"):
            if state["feature"] != "context_direction":
                yield _make(cell, "subgroup_discovery", {"conditions": [state],
                    "subgroup": {"feature": "context_direction", "operator": context_state}},
                    TARGETS[ordinal % len(TARGETS)])


def hypotheses_for(cell: ResearchCell) -> Iterator[Hypothesis]:
    return (known_hypotheses(cell) if cell.research_track is ResearchTrack.KNOWN
            else unknown_hypotheses(cell))


class HypothesisScheduler:
    """Restart-safe bounded scheduler that never materializes the universe."""
    def __init__(self, cells: tuple[ResearchCell, ...], *, seed: int = 35) -> None:
        self.cells = tuple(sorted(cells, key=lambda c: deterministic_hash(
            {"seed": seed, "cell": c.identity})))

    def plan(self, completed: set[str], limit: int) -> tuple[Hypothesis, ...]:
        if limit <= 0:
            raise ValueError("limit must be positive")
        selected: list[Hypothesis] = []
        # Four explicit lanes prevent the large univariate universe starving
        # interactions and subgroups. Reconstructing lanes makes restart exact.
        lanes = ("known_event_evaluation", "univariate_screen",
                 "interaction_search", "subgroup_discovery")
        def lane_iterator(lane: str) -> Iterator[Hypothesis]:
            eligible = (cell for cell in self.cells if
                (lane == "known_event_evaluation") == (cell.research_track is ResearchTrack.KNOWN))
            return chain.from_iterable(
                (h for h in hypotheses_for(cell) if h.method == lane) for cell in eligible)
        iterators = [lane_iterator(lane) for lane in lanes]
        while iterators and len(selected) < limit:
            remaining = []
            for iterator in iterators:
                try:
                    hypothesis = next(iterator)
                except StopIteration:
                    continue
                remaining.append(iterator)
                if hypothesis.hypothesis_id not in completed:
                    selected.append(hypothesis)
                    if len(selected) == limit:
                        break
            iterators = remaining
        return tuple(selected)
