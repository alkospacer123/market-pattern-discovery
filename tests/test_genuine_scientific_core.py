import pandas as pd
import pytest

from market_pattern_discovery.orchestration.multihorizon import (
    UNKNOWN_METHODS, _known, _unknown,
)
from market_pattern_discovery.research import ResearchTrack, research_space


def prepared(n=40, scale=1.0):
    market = pd.DataFrame({"close": range(1, n + 1), "high": range(2, n + 2)})
    features = pd.DataFrame({
        "return_1": [scale * (i % 7 - 3) for i in range(n)],
        "range": [float(i % 5 + 1) for i in range(n)],
        "range_median_7": [3.] * n, "prior_high_20": [0.] * n,
        "context_direction": [(-1.) ** i for i in range(n)],
        "future_signed_return": [0.01 if i % 3 else -0.02 for i in range(n)],
    })
    return market, market.copy(), features


def context_for(cell, n=40):
    return pd.DataFrame({f"context_{tf}_close": range(n)
                         for tf in cell.context_timeframes})


def test_known_and_unknown_are_data_dependent_and_lineaged():
    market, context, features = prepared()
    known_cell = next(c for c in research_space() if c.research_track is ResearchTrack.KNOWN)
    unknown_cell = next(c for c in research_space() if c.research_track is ResearchTrack.UNKNOWN)
    known = _known(cell=known_cell, market_data=market, context=context_for(known_cell), features=features)
    unknown = _unknown(cell=unknown_cell, market_data=market, context=context_for(unknown_cell), features=features)
    assert known.evaluation.sample_size > 0
    assert unknown.evaluation.sample_size > 0
    assert known.evidence.evaluation_id == known.evaluation.evaluation_id
    changed = _unknown(cell=unknown_cell, market_data=market, context=context_for(unknown_cell),
                       features=prepared(scale=10)[2])
    assert changed.hypothesis_id != unknown.hypothesis_id


def test_unknown_schedule_contains_all_genuine_methods_and_all_timeframes():
    unknown_cells = [c for c in research_space() if c.research_track is ResearchTrack.UNKNOWN]
    methods = {UNKNOWN_METHODS[int(c.identity[-8:], 16) % 3] for c in unknown_cells}
    assert methods == set(UNKNOWN_METHODS)
    assert {c.primary_timeframe for c in unknown_cells} == {"M1", "M5", "M15", "M30", "H1", "D1"}
    assert {c.symbol for c in unknown_cells} == {"CNY", "Si"}


def test_context_changes_tested_condition():
    market, context, features = prepared()
    cell = next(c for c in research_space() if c.research_track is ResearchTrack.UNKNOWN)
    first = _unknown(cell=cell, market_data=market, context=context_for(cell), features=features)
    altered = features.copy()
    altered["context_direction"] = -1
    second = _unknown(cell=cell, market_data=market, context=context_for(cell), features=altered)
    assert second.evaluation.sample_size != first.evaluation.sample_size


def test_no_profitability_objective_in_unknown_definition():
    _, _, features = prepared()
    cell = next(c for c in research_space() if c.research_track is ResearchTrack.UNKNOWN)
    result = _unknown(cell=cell, market_data=object(), context=context_for(cell), features=features)
    text = str(result.evaluation.metadata).lower()
    assert not any(word in text for word in ("profit_factor", "win_rate", "expectancy", "pnl"))
