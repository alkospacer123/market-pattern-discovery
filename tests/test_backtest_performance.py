from dataclasses import replace
from datetime import datetime, timedelta, timezone
from time import perf_counter

import pytest

from market_pattern_discovery.backtest import (
    BacktestEngine, CostModel, PreparedMarketData, Trade, TradeDirection,
)
from market_pattern_discovery.contracts import deterministic_hash
from market_pattern_discovery.research import TradingDirection

from test_backtest_engine import data, strategy


class ReferenceBacktestEngine(BacktestEngine):
    """The v1 prefix-building implementation, retained only as a test oracle."""

    def _simulate(self, candidate, candles, contexts, context_positions=None):
        candles = list(candles)
        contexts = {key: list(rows) for key, rows in contexts.items()}
        trades, index = [], 0
        while index < len(candles) - 1:
            signal = candles[index]
            visible = {key: [row for row in rows if row.time <= signal.time]
                       for key, rows in contexts.items()}
            if not all(visible.values()) or not self._signal(
                    candidate.market_condition, signal.values, visible):
                index += 1
                continue
            entry = self._entry(candidate, candles, index)
            if entry is None:
                index += 1
                continue
            entry_i, raw_entry = entry
            stop = self._stop(candidate, candles, index, entry_i, raw_entry)
            exit_i, raw_exit = self._exit(
                candidate, candles, entry_i, raw_entry, stop, visible)
            direction = 1 if candidate.direction is TradingDirection.LONG else -1
            actual_entry = raw_entry + direction * self.costs.slippage
            actual_exit = raw_exit - direction * self.costs.slippage
            gross = direction * (raw_exit - raw_entry)
            net = direction * (actual_exit - actual_entry) - self.costs.transaction_cost
            trade_id = deterministic_hash({"strategy_id": candidate.strategy_id,
                "entry_time": candles[entry_i].time, "exit_time": candles[exit_i].time})
            trades.append(Trade(trade_id, candidate.strategy_id, candles[entry_i].time,
                actual_entry, candles[exit_i].time, actual_exit,
                TradeDirection(candidate.direction.value), gross, net, exit_i - entry_i))
            index = exit_i + 1
        return tuple(trades)


def _large_data(size=4000):
    base = datetime(2024, 1, 2, tzinfo=timezone.utc)
    execution = [{"time": base + timedelta(minutes=i), "open": 10, "high": 11,
                  "low": 9, "close": 10, "state": "off", "signal": False}
                 for i in range(size)]
    contexts = [{"time": base + timedelta(minutes=15 * i), "open": 10,
                 "high": 11, "low": 9, "close": 10, "state": "on"}
                for i in range(size // 15)]
    return {"M1": execution, "M15": contexts}


def test_optimized_and_reference_results_are_identical():
    candidate = strategy(direction=TradingDirection.LONG)
    raw = data()
    optimized = BacktestEngine(CostModel(.1, .05)).run(candidate, raw, data_version="equivalence")
    reference = ReferenceBacktestEngine(CostModel(.1, .05)).run(
        candidate, raw, data_version="equivalence")
    assert optimized == reference


@pytest.mark.parametrize("execution_tf,context_tf,minutes", [
    ("M1", "M5", 1), ("M5", "H1", 5), ("H1", "D1", 60), ("D1", "D1", 1440),
])
def test_prepared_multitimeframe_indexes_are_causal(execution_tf, context_tf, minutes):
    base = datetime(2024, 1, 2, tzinfo=timezone.utc)
    rows = [{"time": base + timedelta(minutes=minutes * i), "open": 1,
             "high": 2, "low": 1, "close": 2} for i in range(3)]
    context_key = context_tf if context_tf != execution_tf else "CONTEXT_D1"
    context = [{"time": base - timedelta(seconds=1), "open": 1, "high": 2,
                "low": 1, "close": 2},
               {"time": base + timedelta(minutes=minutes, seconds=1), "open": 1,
                "high": 2, "low": 1, "close": 2}]
    prepared = BacktestEngine.prepare({execution_tf: rows, context_key: context}, execution_tf)
    assert isinstance(prepared, PreparedMarketData)
    for observation, position in zip(rows, prepared.context_positions[context_key]):
        if position >= 0:
            assert context[position]["time"] <= observation["time"]
            if position + 1 < len(context):
                assert context[position + 1]["time"] > observation["time"]


def test_prepared_data_can_be_reused_without_changing_identity():
    candidate = strategy()
    engine = BacktestEngine(CostModel(0, 0))
    prepared = engine.prepare(data(), candidate.execution_timeframe)
    first = engine.run(candidate, prepared, data_version="reused")
    second = engine.run(candidate, prepared, data_version="reused")
    assert first == second
    assert first.backtest_id == second.backtest_id


def test_context_index_removes_quadratic_prefix_runtime():
    raw = _large_data()
    candidate = replace(strategy(), execution_timeframe="M1")
    optimized = BacktestEngine(CostModel(0, 0))
    reference = ReferenceBacktestEngine(CostModel(0, 0))
    start = perf_counter()
    reference.run(candidate, raw, data_version="benchmark")
    before = perf_counter() - start
    start = perf_counter()
    optimized.run(candidate, raw, data_version="benchmark")
    after = perf_counter() - start
    assert after < before
    assert before / after >= 2
