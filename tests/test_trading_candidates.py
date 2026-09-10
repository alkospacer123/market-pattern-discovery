from dataclasses import fields

import pytest

from market_pattern_discovery.research import (
    CandidateFamily, Evidence, Evaluation, Hypothesis, PatternEffect,
    ResearchCell, ResearchHorizon, ResearchMemory, ResearchTrack,
    TradingCandidate, TradingCandidateGenerator, TradingDirection,
    create_pattern_effect,
)


def finding(method="known_event_evaluation", effect_value=0.02):
    track = "KNOWN" if method == "known_event_evaluation" else "UNKNOWN"
    hypothesis = Hypothesis("cell", "Si", "Scalping", "M1", ("M15",), track,
        method, {"conditions": [{"feature": "return_1", "operator": "quantile_ge"}]},
        "future_signed_return_same_trading_day", "causal baseline")
    evaluation = Evaluation("evaluation", effect_value, 42, {}, hypothesis.hypothesis_id,
        target=hypothesis.target_definition, method=method, context=("M15",),
        state_definition=hypothesis.state_definition,
        uncertainty={"lower": .01, "upper": .03}, stability={"same_sign_folds": 3},
        null_comparison={"raw_p": .01}, multiplicity={"adjusted_q": .02})
    evidence = Evidence("evaluation", True, "all scientific gates passed", True, True, True, True)
    effect = create_pattern_effect(evaluation, evidence)
    return hypothesis, evaluation, evidence, effect


def test_pattern_effect_is_the_only_candidate_source_and_lineage_is_required():
    hypothesis, evaluation, evidence, effect = finding()
    candidate = TradingCandidateGenerator().generate(effect, evaluation, evidence, hypothesis)
    assert candidate.source_pattern_effect_id == effect.effect_id
    cell = ResearchCell("Si", ResearchHorizon.SCALPING, "M1", ("M15",), ResearchTrack.KNOWN)
    with pytest.raises(TypeError, match="PatternEffect"):
        TradingCandidateGenerator().generate(cell, evaluation, evidence, hypothesis)
    with pytest.raises(ValueError, match="lineage"):
        TradingCandidateGenerator().generate(
            PatternEffect("effect", "other-evaluation", .02, 42), evaluation, evidence, hypothesis)


def test_deterministic_identity_direction_and_restart_deduplication(tmp_path):
    hypothesis, evaluation, evidence, effect = finding(effect_value=.02)
    generator = TradingCandidateGenerator()
    first = generator.generate(effect, evaluation, evidence, hypothesis)
    assert first == generator.generate(effect, evaluation, evidence, hypothesis)
    assert first.direction is TradingDirection.LONG
    assert ResearchMemory(tmp_path).add_trading_candidate(first)
    restarted = ResearchMemory(tmp_path)
    assert not restarted.add_trading_candidate(first)
    assert list(restarted.trading_candidates()) == [first.candidate_id]
    assert restarted.trading_candidates()[first.candidate_id] == first
    negative = finding(effect_value=-.02)
    assert generator.generate(negative[3], negative[1], negative[2], negative[0]).direction is TradingDirection.SHORT


@pytest.mark.parametrize(("method", "family"), [
    ("known_event_evaluation", CandidateFamily.KNOWN),
    ("univariate_screen", CandidateFamily.UNKNOWN_UNIVARIATE),
    ("interaction_search", CandidateFamily.UNKNOWN_INTERACTION),
    ("subgroup_discovery", CandidateFamily.UNKNOWN_SUBGROUP),
])
def test_candidate_family_classification(method, family):
    hypothesis, evaluation, evidence, effect = finding(method)
    assert TradingCandidateGenerator().generate(effect, evaluation, evidence, hypothesis).candidate_family is family


@pytest.mark.parametrize("mutation", ["unqualified", "insufficient", "target", "context"])
def test_quality_filter_rejects_incomplete_science(mutation):
    hypothesis, evaluation, evidence, effect = finding()
    if mutation == "unqualified":
        evidence = Evidence("evaluation", False, "failed", True)
    elif mutation == "insufficient":
        evidence = Evidence("evaluation", True, "failed sample", False)
    elif mutation == "target":
        evaluation = Evaluation("evaluation", .02, 42, {}, hypothesis.hypothesis_id,
            target="", context=("M15",), state_definition=hypothesis.state_definition)
    else:
        evaluation = Evaluation("evaluation", .02, 42, {}, hypothesis.hypothesis_id,
            target=hypothesis.target_definition, context=(), state_definition=hypothesis.state_definition)
    with pytest.raises(ValueError):
        TradingCandidateGenerator().generate(effect, evaluation, evidence, hypothesis)


def test_candidate_contract_contains_no_strategy_or_profitability_leakage():
    names = {field.name.lower() for field in fields(TradingCandidate)}
    forbidden = {"sl", "stop_loss", "tp", "take_profit", "entry", "entry_optimization",
                 "profit_factor", "expectancy", "position_size", "risk_reward"}
    assert names.isdisjoint(forbidden)

