from dataclasses import replace

import pandas as pd

from market_pattern_discovery.orchestration.multihorizon import _scientific_result
from market_pattern_discovery.research import (
    HypothesisScheduler, ResearchTrack, hypotheses_for, research_space,
)


def test_balanced_scheduler_reaches_every_lane_and_restarts_without_duplicates():
    scheduler = HypothesisScheduler(research_space(), seed=35)
    first = scheduler.plan(set(), 8)
    assert [item.method for item in first[:4]] == [
        "known_event_evaluation", "univariate_screen", "interaction_search",
        "subgroup_discovery",
    ]
    second = scheduler.plan({item.hypothesis_id for item in first}, 8)
    assert not ({item.hypothesis_id for item in first} &
                {item.hypothesis_id for item in second})
    assert {item.method for item in second} == {item.method for item in first}


def test_inventory_and_behavioural_target_families_are_deep_and_versioned():
    cell = next(item for item in research_space()
                if item.research_track is ResearchTrack.UNKNOWN)
    hypotheses = tuple(item for _, item in zip(range(400), hypotheses_for(cell)))
    features = {condition["feature"] for item in hypotheses
                for condition in item.state_definition["conditions"]}
    assert {"return_1", "range", "body_to_range", "volatility_5",
            "momentum_5", "position_in_range_20"} <= features
    targets = {item.target_definition for item in hypotheses}
    assert len(targets) == 5
    assert all(item.version == "1" for item in hypotheses)
    forbidden = ("profit_factor", "win_rate", "expectancy", "stop_loss", "take_profit")
    assert not any(word in str(hypotheses).lower() for word in forbidden)


def test_evaluation_contains_bootstrap_walk_forward_and_multiplicity():
    cell = next(item for item in research_space()
                if item.research_track is ResearchTrack.UNKNOWN)
    hypothesis = next(hypotheses_for(cell))
    target = pd.Series(([.01] * 20) + ([-.01] * 20))
    target.attrs["trading_date"] = pd.Series([f"d{i // 4}" for i in range(40)])
    result = _scientific_result(cell, hypothesis,
                                pd.Series([i % 2 == 0 for i in range(40)]), target)
    evaluation = result.evaluation
    assert evaluation.uncertainty["method"] == "moscow_trading_date_resampling"
    assert evaluation.stability["method"] == "three_ordered_walk_forward_blocks"
    assert evaluation.multiplicity["method"] == "benjamini_hochberg"
    assert evaluation.state_definition == hypothesis.state_definition
    assert result.evidence.evaluation_id == evaluation.evaluation_id
