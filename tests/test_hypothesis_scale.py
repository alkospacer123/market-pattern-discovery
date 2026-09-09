from dataclasses import replace

import pandas as pd

from market_pattern_discovery.orchestration.multihorizon import _known, _unknown
from market_pattern_discovery.research import (
    HypothesisScheduler, ResearchTrack, create_pattern_effect, hypotheses_for,
    research_space,
)


def _frames(cell, n=80):
    market = pd.DataFrame({"close": [100 + i + (i % 3) for i in range(n)],
                           "high": [102 + i + (i % 3) for i in range(n)]})
    context = pd.DataFrame({f"context_{tf}_close": range(n)
                            for tf in cell.context_timeframes})
    features = pd.DataFrame({
        "return_1": [(i % 11 - 5) / 100 for i in range(n)],
        "range": [float(i % 7 + 1) for i in range(n)],
        "range_median_7": [4.] * n,
        "prior_high_20": [90 + i for i in range(n)],
        "context_direction": [1. if i % 3 else -1. for i in range(n)],
        "future_signed_return": [.01 if i % 4 else -.02 for i in range(n)],
    })
    return market, context, features


def test_one_cell_has_many_deterministic_distinct_hypotheses():
    cell = next(c for c in research_space() if c.research_track is ResearchTrack.UNKNOWN)
    first = tuple(h for _, h in zip(range(200), hypotheses_for(cell)))
    again = tuple(h for _, h in zip(range(200), hypotheses_for(cell)))
    assert len(first) == 200
    assert [h.hypothesis_id for h in first] == [h.hypothesis_id for h in again]
    assert len({h.hypothesis_id for h in first}) == len(first)


def test_scheduler_restart_continues_without_duplicates():
    cell = next(c for c in research_space() if c.research_track is ResearchTrack.UNKNOWN)
    scheduler = HypothesisScheduler((cell,), seed=7)
    process_a = scheduler.plan(set(), 10)
    process_b = scheduler.plan({h.hypothesis_id for h in process_a}, 10)
    assert process_b
    assert not ({h.hypothesis_id for h in process_a} &
                {h.hypothesis_id for h in process_b})


def test_known_registry_and_all_unknown_methods_execute_scientifically():
    known_cell = next(c for c in research_space() if c.research_track is ResearchTrack.KNOWN)
    known = tuple(hypotheses_for(known_cell))
    assert len(known) == 6
    market, context, features = _frames(known_cell)
    assert _known(cell=known_cell, market_data=market, context=context,
                  features=features, hypothesis=known[1]).evaluation.hypothesis_id

    unknown_cell = replace(known_cell, research_track=ResearchTrack.UNKNOWN)
    market, context, features = _frames(unknown_cell)
    universe = hypotheses_for(unknown_cell)
    selected = {}
    for hypothesis in universe:
        selected.setdefault(hypothesis.method, hypothesis)
        if len(selected) == 3:
            break
    assert set(selected) == {"univariate_screen", "interaction_search", "subgroup_discovery"}
    for method, hypothesis in selected.items():
        result = _unknown(cell=unknown_cell, market_data=market, context=context,
                          features=features, hypothesis=hypothesis)
        assert result.discovery_method == method
        assert result.evaluation.hypothesis_id == hypothesis.hypothesis_id
        assert result.evidence.evaluation_id == result.evaluation.evaluation_id
        effect = create_pattern_effect(result.evaluation, result.evidence)
        if effect:
            assert effect.evaluation_id == result.evaluation.evaluation_id


def test_hypothesis_definition_has_no_profitability_objective():
    text = str(tuple(h for _, h in zip(range(500), hypotheses_for(next(
        c for c in research_space() if c.research_track is ResearchTrack.UNKNOWN))))).lower()
    assert not any(term in text for term in
                   ("profit_factor", "win_rate", "expectancy", "stop_loss", "take_profit"))
