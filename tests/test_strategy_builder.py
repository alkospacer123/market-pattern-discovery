from dataclasses import fields

import pytest

from market_pattern_discovery.research import (
    CandidateFamily, EntryType, ExitType, PatternEffect, ResearchMemory,
    RiskType, StrategyBuilder, StrategyCandidate, TradingCandidate,
    TradingCandidateStatus, TradingDirection,
)


def trading_candidate(candidate_id="trade-1"):
    return TradingCandidate(
        candidate_id, "effect-1", "Si", "Scalping", "M1", ("M15",),
        TradingDirection.SHORT, "negative conditional future return",
        {"condition": "causally_observed_state"}, "qualified negative behavior",
        "future_signed_return_same_trading_day", -.01, 100,
        {"evidence": "qualified"}, CandidateFamily.KNOWN,
        TradingCandidateStatus.READY_FOR_STRATEGY_SEARCH,
    )


def test_only_valid_trading_candidate_can_be_built():
    source = trading_candidate()
    strategies = StrategyBuilder().build(source)
    assert all(row.source_trading_candidate_id == source.candidate_id for row in strategies)
    with pytest.raises(TypeError, match="TradingCandidate"):
        StrategyBuilder().build(PatternEffect("effect", "evaluation", -.1, 100))
    rejected = TradingCandidate(
        source.candidate_id, source.source_pattern_effect_id, source.symbol,
        source.horizon, source.execution_timeframe, source.context_timeframes,
        source.direction, source.hypothesis_description,
        source.market_state_definition, source.observed_behavior,
        source.target_definition, source.effect, source.sample_size,
        source.confidence_metadata, source.candidate_family,
        TradingCandidateStatus.REJECTED,
    )
    with pytest.raises(ValueError, match="not valid"):
        StrategyBuilder().build(rejected)


def test_generation_is_deterministic_bounded_and_complete():
    first = StrategyBuilder().build(trading_candidate())
    second = StrategyBuilder().build(trading_candidate())
    assert len(first) == 27
    assert len({row.strategy_id for row in first}) == 27
    assert [row.strategy_id for row in first] == [row.strategy_id for row in second]
    assert {row.entry.entry_type for row in first} == set(EntryType)
    assert {row.risk.risk_type for row in first} == set(RiskType)
    assert {row.exit.exit_type for row in first} == set(ExitType)
    assert len(StrategyBuilder("strategy-builder-v2").build(trading_candidate())) == 27
    assert first[0].strategy_id != StrategyBuilder("strategy-builder-v2").build(
        trading_candidate())[0].strategy_id


def test_memory_is_restart_safe_and_requires_persisted_lineage(tmp_path):
    source = trading_candidate()
    memory_a = ResearchMemory(tmp_path)
    with pytest.raises(ValueError, match="not in memory"):
        memory_a.add_strategy_candidate(StrategyBuilder().build(source)[0])
    assert memory_a.add_trading_candidate(source)
    built = StrategyBuilder().build_and_persist(source, memory_a)
    assert len(memory_a.strategy_candidates()) == 27

    memory_b = ResearchMemory(tmp_path)
    rebuilt = StrategyBuilder().build_and_persist(source, memory_b)
    assert [row.strategy_id for row in rebuilt] == [row.strategy_id for row in built]
    assert len(memory_b.strategy_candidates()) == 27

    source_2 = trading_candidate("trade-2")
    assert memory_b.add_trading_candidate(source_2)
    StrategyBuilder().build_and_persist(source_2, memory_b)
    assert len(ResearchMemory(tmp_path).strategy_candidates()) == 54


def test_contract_has_no_profitability_creation_fields():
    names = {field.name.lower() for field in fields(StrategyCandidate)}
    forbidden = {"profit_factor", "pf", "expectancy", "win_rate", "sharpe",
                 "maximum_profit", "fitness", "profitability"}
    assert names.isdisjoint(forbidden)
    for strategy in StrategyBuilder().build(trading_candidate()):
        assert forbidden.isdisjoint(str(strategy).lower().replace(" ", "_").split("="))
