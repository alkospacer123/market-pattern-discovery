import pytest
from market_pattern_discovery.research import *


def test_effect_exists_only_for_qualified_real_evidence():
    evaluation = Evaluation("e1", .2, 50, {})
    assert create_pattern_effect(evaluation, Evidence("e1", False, "insufficient")) is None
    effect = create_pattern_effect(evaluation, Evidence("e1", True, "protocol passed"))
    assert effect.effect == .2
    assert ResearchIntelligence().conclude(evaluation,
        Evidence("e1", True, "protocol passed"), effect).conclusion == Conclusion.POSITIVE


def test_negative_and_unresolved_are_research_not_trading_logic():
    evaluation = Evaluation("e2", -.1, 20, {})
    evidence = Evidence("e2", True, "qualified")
    conclusion = ResearchIntelligence().conclude(evaluation, evidence,
        create_pattern_effect(evaluation, evidence))
    assert conclusion.conclusion == Conclusion.NEGATIVE
    assert not hasattr(conclusion, "signal")
    assert ResearchIntelligence().conclude(evaluation,
        Evidence("e2", False, "weak"), None).conclusion == Conclusion.UNRESOLVED


def test_qualified_effect_cannot_be_fabricated_without_measurement():
    with pytest.raises(ValueError):
        create_pattern_effect(Evaluation("e", None, 0, {}), Evidence("e", True, "bad"))
