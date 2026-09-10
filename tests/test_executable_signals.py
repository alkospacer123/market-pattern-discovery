from dataclasses import replace
from datetime import datetime, timedelta, timezone

import pytest

from market_pattern_discovery.backtest import BacktestEngine, CostModel
from market_pattern_discovery.research import (
    CandidateFamily, EntryDefinition, EntryType, ExitDefinition, ExitType,
    ResearchMemory, RiskDefinition, RiskType, StrategyCandidate,
    StrategyCandidateStatus, TradingCandidate, TradingCandidateStatus,
    TradingDirection,
)
from market_pattern_discovery.research.intelligence import PatternEffect
from market_pattern_discovery.signals import ScientificSignalTranslator, SignalType


def strategy(strategy_id="strategy-1", state=None):
    return StrategyCandidate(strategy_id, "trade-1", "TEST", "SCALPING", "M5",
        ("M15",), TradingDirection.SHORT, "equal high rejection",
        state or {"feature": "equal_high_pattern"}, CandidateFamily.KNOWN,
        EntryDefinition(EntryType.CONFIRMATION_ENTRY, {"confirmation_bars": 1}),
        RiskDefinition(RiskType.FIXED_DISTANCE_STOP, {"distance_units": 2}),
        ExitDefinition(ExitType.TIME_EXIT, {"bars": 1}),
        StrategyCandidateStatus.READY_FOR_BACKTEST)


def source():
    return TradingCandidate("trade-1", "effect-1", "TEST", "SCALPING", "M5",
        ("M15",), TradingDirection.SHORT, "equal high rejection",
        {"feature": "equal_high_pattern"}, "behavior", "target", -.1, 20, {},
        CandidateFamily.KNOWN, TradingCandidateStatus.READY_FOR_STRATEGY_SEARCH)


def fixture():
    at = datetime(2024, 1, 2, 9, tzinfo=timezone.utc)
    values = [(10, 11, 9, 10.5), (10.5, 12, 10, 11), (11, 12.005, 10, 10.5),
              (10.5, 11, 9.5, 10), (10, 10.5, 9, 9.5), (9.5, 10, 9, 9.5)]
    rows = [{"time": at + timedelta(minutes=5*i), "open": o, "high": h,
             "low": low, "close": close} for i, (o, h, low, close) in enumerate(values)]
    context = [{"time": at - timedelta(minutes=15), "open": 1, "high": 2,
                "low": 1, "close": 1.5}]
    return {"M5": rows, "M15": context}


def test_translation_is_deterministic_distinct_and_rejects_direct_effect():
    translator = ScientificSignalTranslator()
    first = translator.translate(strategy())
    assert first == translator.translate(strategy())
    assert first.signal_type is SignalType.LEVEL_REJECTION
    assert first.signal_id != translator.translate(strategy("strategy-2")).signal_id
    with pytest.raises(TypeError, match="StrategyCandidate"):
        translator.translate(PatternEffect("effect", "evaluation", .1, 20))


def test_executable_signal_is_causal_and_produces_diagnostics_and_trade():
    signal = ScientificSignalTranslator().translate(strategy())
    result = BacktestEngine(CostModel(.1, .05)).run(signal, fixture(), data_version="fixture-v1")
    assert result.signal_id == signal.signal_id
    assert result.condition_evaluations > result.potential_signals >= 1
    assert result.potential_signals >= result.confirmed_signals >= result.executed_entries == 1
    assert result.total_trades == len(result.trades) == 1
    # Altering the candle after entry cannot create an earlier signal/entry.
    changed = fixture()
    changed["M5"][-1] = {**changed["M5"][-1], "close": 9.9}
    later = BacktestEngine(CostModel(.1, .05)).run(signal, changed, data_version="fixture-v2")
    assert later.trades[0].entry_time == result.trades[0].entry_time


def test_memory_registry_is_lineage_checked_and_restart_safe(tmp_path):
    memory = ResearchMemory(tmp_path)
    signal = ScientificSignalTranslator().translate(strategy())
    with pytest.raises(ValueError, match="not in memory"):
        memory.add_executable_signal_definition(signal)
    memory.add_trading_candidate(source())
    memory.add_strategy_candidate(strategy())
    assert memory.add_executable_signal_definition(signal)
    assert not ResearchMemory(tmp_path).add_executable_signal_definition(signal)
    assert list(ResearchMemory(tmp_path).executable_signal_definitions()) == [signal.signal_id]
    with pytest.raises(ValueError, match="identity or strategy lineage"):
        memory.add_executable_signal_definition(replace(signal, signal_id="invalid"))


def test_backtest_rejects_scientific_pattern_effect():
    with pytest.raises(TypeError, match="ExecutableSignalDefinition"):
        BacktestEngine(CostModel(0, 0)).run(
            PatternEffect("effect", "evaluation", .1, 20), fixture(), data_version="v1")
