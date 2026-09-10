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


UTC = timezone.utc


def strategy(direction=TradingDirection.LONG, entry=EntryType.CLOSE_ENTRY,
             risk=RiskType.FIXED_DISTANCE_STOP, exit_type=ExitType.TIME_EXIT):
    return StrategyCandidate(
        f"strategy-{direction}-{entry}-{risk}-{exit_type}", "source-1", "TEST",
        "SCALPING", "M5", ("M15",), direction, "causal signal", {"state": "on"},
        CandidateFamily.KNOWN, EntryDefinition(entry, {"confirmation_bars": 1}),
        RiskDefinition(risk, {"distance_units": 2, "atr_period": 2, "atr_multiple": 1}),
        ExitDefinition(exit_type, {"bars": 2, "distance_units": 1}),
        StrategyCandidateStatus.READY_FOR_BACKTEST,
    )


def data(direction=TradingDirection.LONG):
    base = datetime(2024, 1, 2, 9, tzinfo=UTC)
    values = [(10, 11, 9, 10), (10, 11.5, 9.5, 11), (11, 13, 10.5, 12),
              (12, 12.5, 10.5, 11), (11, 11.5, 10, 10.5)]
    execution = []
    for i, (o, h, low, close) in enumerate(values):
        execution.append({"time": base + timedelta(minutes=5 * i), "open": o,
            "high": h, "low": low, "close": close, "state": "on",
            "signal": i == 0})
    if direction is TradingDirection.SHORT:
        execution = [{**row, "open": 20-row["open"], "high": 20-row["low"],
                      "low": 20-row["high"], "close": 20-row["close"]}
                     for row in execution]
    context = [{"time": base - timedelta(minutes=15), "open": 1, "high": 2,
                "low": 1, "close": 2, "trend": "known"}]
    return {"M5": execution, "M15": context}


@pytest.mark.parametrize("direction", [TradingDirection.LONG, TradingDirection.SHORT])
def test_long_and_short_lineage_metrics_and_determinism(direction):
    candidate = strategy(direction)
    engine = BacktestEngine(CostModel(.1, .05))
    first = engine.run(candidate, data(direction), data_version="fixture-v1")
    second = engine.run(candidate, data(direction), data_version="fixture-v1")
    assert first == second
    assert first.backtest_id == second.backtest_id
    assert first.strategy_id == candidate.strategy_id
    assert first.total_trades == len(first.trades) == 1
    assert first.trades[0].direction.value == direction.value


@pytest.mark.parametrize("entry", list(EntryType))
@pytest.mark.parametrize("risk", list(RiskType))
@pytest.mark.parametrize("exit_type", list(ExitType))
def test_all_reviewed_execution_definitions(entry, risk, exit_type):
    result = BacktestEngine(CostModel(0, 0)).run(
        strategy(entry=entry, risk=risk, exit_type=exit_type), data(), data_version="v1")
    assert result.total_trades == 1
    assert result.start_time <= result.trades[0].entry_time <= result.end_time


def test_costs_reduce_after_cost_result_without_changing_gross():
    candidate = strategy(exit_type=ExitType.SIMPLE_TARGET_EXIT)
    free = BacktestEngine(CostModel(0, 0)).run(candidate, data(), data_version="v1")
    costly = BacktestEngine(CostModel(.2, .1)).run(candidate, data(), data_version="v1")
    assert costly.gross_profit == free.gross_profit
    assert costly.net_result == pytest.approx(free.net_result - .4)
    assert costly.commission_model == "fixed:0.2"
    assert costly.slippage_model == "fixed_per_fill:0.1"


def test_causality_validation_and_candidate_immutability():
    candidate = strategy()
    original = repr(candidate)
    bad = data()
    bad["M5"] = list(reversed(bad["M5"]))
    with pytest.raises(ValueError, match="strictly ordered"):
        BacktestEngine(CostModel(0, 0)).run(candidate, bad, data_version="v1")
    future = data()
    future["M15"] = [{**future["M15"][0], "time": datetime(2024, 2, 1, tzinfo=UTC)}]
    result = BacktestEngine(CostModel(0, 0)).run(candidate, future, data_version="v1")
    assert result.total_trades == 0  # future context was not made visible
    assert repr(candidate) == original


def test_backtest_memory_is_append_only_restart_safe(tmp_path):
    candidate = strategy()
    source = TradingCandidate("source-1", "effect", "TEST", "SCALPING", "M5", ("M15",),
        TradingDirection.LONG, "causal signal", {"state": "on"}, "behavior", "target",
        .1, 20, {"confidence": "reviewed"}, CandidateFamily.KNOWN,
        TradingCandidateStatus.READY_FOR_STRATEGY_SEARCH)
    memory_a = ResearchMemory(tmp_path)
    memory_a.add_trading_candidate(source)
    memory_a.add_strategy_candidate(candidate)
    result = BacktestEngine(CostModel(0, 0)).run(candidate, data(), data_version="v1")
    assert memory_a.add_backtest_result(result)
    memory_b = ResearchMemory(tmp_path)
    assert not memory_b.add_backtest_result(result)
    assert memory_b.backtest_results()[result.backtest_id] == result
    assert len(memory_b.backtest_results()) == 1


def test_true_oos_is_locked_by_default():
    locked = data()
    locked["M5"] = [{**row, "time": row["time"].replace(year=2025)} for row in locked["M5"]]
    with pytest.raises(ValueError, match="TRUE OOS"):
        BacktestEngine(CostModel(0, 0)).run(strategy(), locked, data_version="locked")
