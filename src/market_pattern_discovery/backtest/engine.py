"""Causal, deterministic evaluation of an already-defined strategy candidate."""
from __future__ import annotations

from dataclasses import asdict, dataclass
from datetime import datetime, timedelta
from enum import StrEnum
from math import isfinite
from typing import Any, Iterable, Mapping

from market_pattern_discovery.contracts import deterministic_hash
from market_pattern_discovery.research.strategy_candidates import ExitType, RiskType
from market_pattern_discovery.research.strategy_candidates import StrategyCandidate
from market_pattern_discovery.research.trading_candidates import TradingDirection
from market_pattern_discovery.signals import ExecutableSignalDefinition, SignalType

from .costs import CostModel


class TradeDirection(StrEnum):
    LONG = "LONG"
    SHORT = "SHORT"


@dataclass(frozen=True, slots=True)
class Trade:
    trade_id: str
    strategy_id: str
    entry_time: datetime
    entry_price: float
    exit_time: datetime
    exit_price: float
    direction: TradeDirection
    gross_pnl: float
    net_pnl: float
    holding_bars: int

    def __post_init__(self) -> None:
        object.__setattr__(self, "entry_time", _time(self.entry_time))
        object.__setattr__(self, "exit_time", _time(self.exit_time))
        object.__setattr__(self, "direction", TradeDirection(self.direction))
        if self.exit_time < self.entry_time or self.holding_bars < 0:
            raise ValueError("trade exits must not precede entry")


@dataclass(frozen=True, slots=True)
class BacktestResult:
    backtest_id: str
    strategy_id: str
    symbol: str
    timeframe: str
    context_timeframes: tuple[str, ...]
    start_time: datetime
    end_time: datetime
    total_trades: int
    winning_trades: int
    losing_trades: int
    gross_profit: float
    gross_loss: float
    net_result: float
    profit_factor: float | None
    expectancy: float
    win_rate: float
    max_drawdown: float
    largest_win: float
    largest_loss: float
    average_holding_bars: float
    average_holding_time: timedelta
    commission_model: str
    slippage_model: str
    data_version: str
    engine_version: str
    trades: tuple[Trade, ...] = ()
    signal_id: str = ""
    condition_evaluations: int = 0
    potential_signals: int = 0
    confirmed_signals: int = 0
    executed_entries: int = 0

    def __post_init__(self) -> None:
        object.__setattr__(self, "context_timeframes", tuple(self.context_timeframes))
        object.__setattr__(self, "start_time", _time(self.start_time))
        object.__setattr__(self, "end_time", _time(self.end_time))
        object.__setattr__(self, "average_holding_time", _duration(self.average_holding_time))
        object.__setattr__(self, "trades", tuple(t if isinstance(t, Trade) else Trade(**t)
                                                 for t in self.trades))

    def to_dict(self) -> dict[str, Any]:
        value = asdict(self)
        value["start_time"] = self.start_time.isoformat()
        value["end_time"] = self.end_time.isoformat()
        value["average_holding_time"] = self.average_holding_time.total_seconds()
        for raw, trade in zip(value["trades"], self.trades):
            raw["entry_time"] = trade.entry_time.isoformat()
            raw["exit_time"] = trade.exit_time.isoformat()
            raw["direction"] = trade.direction.value
        return value

    @classmethod
    def from_dict(cls, value: Mapping[str, Any]) -> "BacktestResult":
        return cls(**dict(value))


def _time(value: Any) -> datetime:
    result = value if isinstance(value, datetime) else datetime.fromisoformat(str(value))
    if result.tzinfo is None:
        raise ValueError("candle and trade timestamps must be timezone-aware")
    return result


def _duration(value: Any) -> timedelta:
    return value if isinstance(value, timedelta) else timedelta(seconds=float(value))


@dataclass(frozen=True)
class _Candle:
    time: datetime
    open: float
    high: float
    low: float
    close: float
    values: Mapping[str, Any]


@dataclass(frozen=True, slots=True)
class PreparedMarketData:
    """Validated, immutable indexes used by repeated backtest evaluations.

    ``context_positions[timeframe][i]`` is the last context candle whose close
    is observable at execution candle ``i``.  A value of ``-1`` means that no
    candle is available yet.  The indexes are built with a monotonic cursor,
    so preparation is linear rather than a historical scan per observation.
    """

    execution_timeframe: str
    timeframe_index: Mapping[str, tuple[_Candle, ...]]
    candle_close_timestamps: Mapping[str, tuple[datetime, ...]]
    context_positions: Mapping[str, tuple[int, ...]]
    symbol_index: Mapping[str, tuple[int, ...]]


class BacktestEngine:
    """Single-pass simulator; it evaluates and never mutates or searches strategies."""

    def __init__(self, costs: CostModel, *, engine_version: str = "backtest-engine-v1",
                 forbid_true_oos: bool = True) -> None:
        if not engine_version:
            raise ValueError("engine_version is required")
        self.costs, self.engine_version, self.forbid_true_oos = costs, engine_version, forbid_true_oos

    def run(self, signal: ExecutableSignalDefinition, market_data: Any, *, data_version: str) -> BacktestResult:
        # Compatibility is kept at this public boundary for existing callers;
        # simulation itself can only consume compiler output.
        if isinstance(signal, StrategyCandidate):
            from market_pattern_discovery.signals import ScientificSignalTranslator
            signal = ScientificSignalTranslator().translate(signal)
        if not isinstance(signal, ExecutableSignalDefinition):
            raise TypeError("BacktestEngine requires an ExecutableSignalDefinition")
        if signal.direction not in {TradingDirection.LONG, TradingDirection.SHORT}:
            raise ValueError("backtests require a LONG or SHORT direction")
        if not data_version:
            raise ValueError("data_version is required")
        before = deterministic_hash(signal.to_dict())
        prepared = (market_data if isinstance(market_data, PreparedMarketData)
                    else self.prepare(market_data, signal.execution_timeframe))
        if prepared.execution_timeframe != signal.execution_timeframe:
            raise ValueError("prepared data execution timeframe does not match signal")
        execution = prepared.timeframe_index[signal.execution_timeframe]
        contexts = {tf: rows for tf, rows in prepared.timeframe_index.items()
                    if tf != signal.execution_timeframe}
        if len(execution) < 2:
            raise ValueError("at least two execution candles are required")
        if self.forbid_true_oos and any(c.time.year == 2025 for c in execution):
            raise ValueError("calendar year 2025 TRUE OOS is locked")
        missing = set(signal.context_timeframes) - contexts.keys()
        if missing:
            raise ValueError(f"missing context timeframes: {sorted(missing)}")
        trades, diagnostics = self._simulate(signal, execution, contexts, prepared.context_positions)
        if deterministic_hash(signal.to_dict()) != before:
            raise RuntimeError("ExecutableSignalDefinition was modified during evaluation")
        identity = deterministic_hash({"signal_id": signal.signal_id,
            "data_version": data_version, "engine_version": self.engine_version})
        return self._result(identity, signal, execution, trades, data_version, diagnostics)

    @classmethod
    def prepare(cls, data: Any, timeframe: str) -> PreparedMarketData:
        """Validate market data once and precompute strictly causal lookups."""
        if isinstance(data, Mapping):
            if timeframe not in data:
                raise ValueError(f"execution timeframe {timeframe} is unavailable")
            raw_execution = data[timeframe]
            raw_contexts = {str(k): v for k, v in data.items() if str(k) != timeframe}
        else:
            raw_execution, raw_contexts = data, {}
        execution = tuple(cls._candles(raw_execution))
        contexts = {key: tuple(cls._candles(value)) for key, value in raw_contexts.items()}
        timeframe_index = {timeframe: execution, **contexts}
        close_times = {key: tuple(c.time for c in rows)
                       for key, rows in timeframe_index.items()}
        positions: dict[str, tuple[int, ...]] = {}
        for key, rows in contexts.items():
            cursor = -1
            aligned = []
            for observation in execution:
                while cursor + 1 < len(rows) and rows[cursor + 1].time <= observation.time:
                    cursor += 1
                aligned.append(cursor)
            positions[key] = tuple(aligned)
        symbols: dict[str, list[int]] = {}
        for index, candle in enumerate(execution):
            symbol = str(candle.values.get("symbol", "*"))
            symbols.setdefault(symbol, []).append(index)
        return PreparedMarketData(timeframe, timeframe_index, close_times, positions,
                                  {key: tuple(value) for key, value in symbols.items()})

    @classmethod
    def _load(cls, data: Any, timeframe: str) -> tuple[list[_Candle], dict[str, list[_Candle]]]:
        """Compatibility loader retained for callers that inspect validated rows."""
        prepared = cls.prepare(data, timeframe)
        return (list(prepared.timeframe_index[timeframe]),
                {key: list(rows) for key, rows in prepared.timeframe_index.items()
                 if key != timeframe})

    @staticmethod
    def _candles(rows: Iterable[Any]) -> list[_Candle]:
        if hasattr(rows, "to_dict"):
            rows = rows.to_dict("records")
        result = []
        for row in rows:
            raw = dict(row) if isinstance(row, Mapping) else asdict(row)
            stamp = raw.get("close_time", raw.get("time", raw.get("timestamp")))
            candle = _Candle(_time(stamp), *(float(raw[k]) for k in ("open", "high", "low", "close")), raw)
            if not all(isfinite(v) for v in (candle.open, candle.high, candle.low, candle.close)):
                raise ValueError("OHLC values must be finite")
            if candle.low > min(candle.open, candle.close) or candle.high < max(candle.open, candle.close):
                raise ValueError("invalid OHLC candle")
            result.append(candle)
        if any(a.time >= b.time for a, b in zip(result, result[1:])):
            raise ValueError("candles must be strictly ordered without duplicates")
        return result

    def _simulate(self, s: ExecutableSignalDefinition, candles: Iterable[_Candle],
                  contexts: Mapping[str, Iterable[_Candle]],
                  context_positions: Mapping[str, tuple[int, ...]] | None = None
                  ) -> tuple[tuple[Trade, ...], tuple[int, int, int, int]]:
        candles = list(candles)
        contexts = {tf: list(rows) for tf, rows in contexts.items()}
        if context_positions is None:
            # Private-method compatibility; production runs always pass prepared indexes.
            context_positions = self.prepare(
                {s.execution_timeframe: candles, **contexts},
                s.execution_timeframe).context_positions
        trades, i = [], 0
        evaluated = potential = confirmed = entries = 0
        while i < len(candles) - 2:
            signal = candles[i]
            # Existing signal/exit semantics inspect only the most recent visible
            # context candle.  A one-element prefix therefore has identical
            # behaviour without allocating and rescanning the full history.
            visible = {tf: ([] if context_positions[tf][i] < 0
                            else [rows[context_positions[tf][i]]])
                       for tf, rows in contexts.items()}
            evaluated += 1
            if not all(visible.values()) or not self._potential(s, candles, i, visible):
                i += 1; continue
            potential += 1
            if not self._confirmed(s, candles, i):
                i += 1; continue
            confirmed += 1
            entry_i = i + 2
            if candles[entry_i].time.date() != candles[i].time.date():
                i += 1; continue
            raw_entry = candles[entry_i].open
            entries += 1
            stop = self._stop(s, candles, i, entry_i, raw_entry)
            exit_i, raw_exit = self._exit(s, candles, entry_i, raw_entry, stop, visible)
            direction = 1 if s.direction is TradingDirection.LONG else -1
            actual_entry = raw_entry + direction * self.costs.slippage
            actual_exit = raw_exit - direction * self.costs.slippage
            gross = direction * (raw_exit - raw_entry)
            net = direction * (actual_exit - actual_entry) - self.costs.transaction_cost
            trade_id = deterministic_hash({"strategy_id": s.source_strategy_candidate_id,
                "entry_time": candles[entry_i].time, "exit_time": candles[exit_i].time})
            trades.append(Trade(trade_id, s.source_strategy_candidate_id, candles[entry_i].time, actual_entry,
                candles[exit_i].time, actual_exit, TradeDirection(s.direction.value), gross, net,
                exit_i - entry_i))
            i = exit_i + 1
        return tuple(trades), (evaluated, potential, confirmed, entries)

    @staticmethod
    def _potential(s: ExecutableSignalDefinition, candles: list[_Candle], index: int,
                   contexts: Mapping[str, list[_Candle]]) -> bool:
        """Evaluate only the current close and the already-closed prefix."""
        candle, prior = candles[index], candles[:index]
        direction = 1 if s.direction is TradingDirection.LONG else -1
        if s.signal_type is SignalType.TREND_CONTINUATION:
            field_conditions = [row for row in s.conditions
                                if row["type"] == "OBSERVABLE_FIELDS"]
            if field_conditions:
                return all(candle.values.get(key) == value for key, value in
                           field_conditions[0]["values"].items())
            return direction * (candle.close - candle.open) > 0
        if index < 1:
            return False
        condition = s.conditions[0]
        lookback = int(condition.get("lookback", 3))
        known = prior[-lookback:]
        if len(known) < lookback:
            return False
        if s.signal_type is SignalType.LEVEL_REJECTION:
            use_high = condition["condition"] == "EQUAL_HIGH"
            value = candle.high if use_high else candle.low
            values = [row.high if use_high else row.low for row in known]
            tolerance = max(abs(value), 1.0) * float(condition["relative_tolerance"])
            equal = any(abs(value - other) <= tolerance for other in values)
            rejection = candle.close < candle.open if use_high else candle.close > candle.open
            return equal and rejection
        if s.signal_type is SignalType.BREAKOUT:
            level = max(row.high for row in known) if direction == 1 else min(row.low for row in known)
            return candle.close > level if direction == 1 else candle.close < level
        closes = [row.close for row in known]
        reference = sum(closes) / len(closes)
        ranges = sum(row.high - row.low for row in known) / len(known)
        threshold = ranges * float(condition["deviation_ranges"])
        return candle.close < reference - threshold if direction == 1 else candle.close > reference + threshold

    @staticmethod
    def _confirmed(s: ExecutableSignalDefinition, candles: list[_Candle], index: int) -> bool:
        confirmation = candles[index + 1]
        if confirmation.time.date() != candles[index].time.date():
            return False
        if s.signal_type is SignalType.MEAN_REVERSION:
            known = candles[max(0, index - 2):index + 1]
            reference = sum(row.close for row in known) / len(known)
            return confirmation.close > candles[index].close if s.direction is TradingDirection.LONG else confirmation.close < candles[index].close
        if s.signal_type is SignalType.BREAKOUT:
            level = candles[index].close
            return confirmation.close >= level if s.direction is TradingDirection.LONG else confirmation.close <= level
        return (confirmation.close > candles[index].close
                if s.direction is TradingDirection.LONG
                else confirmation.close < candles[index].close)

    @staticmethod
    def _signal(condition: Mapping[str, Any], candle: Mapping[str, Any],
                contexts: Mapping[str, list[_Candle]]) -> bool:
        if "signal" in candle:
            return bool(candle["signal"])
        return BacktestEngine._condition(condition, candle, contexts)

    @staticmethod
    def _condition(condition: Mapping[str, Any], candle: Mapping[str, Any],
                   contexts: Mapping[str, list[_Candle]]) -> bool:
        for key, expected in condition.items():
            if key.startswith("context."):
                _, timeframe, field = key.split(".", 2)
                if timeframe not in contexts or contexts[timeframe][-1].values.get(field) != expected:
                    return False
            elif key not in candle or candle[key] != expected:
                return False
        return True

    @staticmethod
    def _entry(s: ExecutableSignalDefinition, candles: list[_Candle], signal_i: int) -> tuple[int, float] | None:
        if candles[signal_i + 1].time.date() != candles[signal_i].time.date():
            return None
        return signal_i + 1, candles[signal_i + 1].open

    @staticmethod
    def _stop(s: ExecutableSignalDefinition, candles: list[_Candle], signal_i: int,
              entry_i: int, entry: float) -> float:
        direction = 1 if s.direction is TradingDirection.LONG else -1
        if s.risk.risk_type is RiskType.FIXED_DISTANCE_STOP:
            distance = float(s.risk.parameters.get("distance_units", 1))
        elif s.risk.risk_type is RiskType.STRUCTURE_STOP:
            return candles[signal_i].low if direction == 1 else candles[signal_i].high
        else:
            period = int(s.risk.parameters.get("atr_period", 14))
            known = candles[max(0, entry_i - period):entry_i]
            previous = candles[max(0, entry_i - period - 1):entry_i - 1]
            tr = [max(c.high - c.low, abs(c.high - p.close), abs(c.low - p.close))
                  for c, p in zip(known, previous)]
            distance = (sum(tr) / len(tr) if tr else candles[signal_i].high - candles[signal_i].low)
            distance *= float(s.risk.parameters.get("atr_multiple", 1))
        if distance <= 0:
            raise ValueError("stop distance must be positive")
        return entry - direction * distance

    @staticmethod
    def _exit(s: ExecutableSignalDefinition, candles: list[_Candle], entry_i: int,
              entry: float, stop: float, context: Mapping[str, list[_Candle]]) -> tuple[int, float]:
        direction = 1 if s.direction is TradingDirection.LONG else -1
        bars = int(s.exit.parameters.get("bars", 10))
        target = entry + direction * float(s.exit.parameters.get("distance_units", 1))
        for index in range(entry_i, len(candles)):
            candle = candles[index]
            if candle.time.date() != candles[entry_i].time.date():
                return index - 1, candles[index - 1].close
            stopped = candle.low <= stop if direction == 1 else candle.high >= stop
            if stopped:
                return index, stop
            if s.exit.exit_type is ExitType.SIMPLE_TARGET_EXIT:
                hit = candle.high >= target if direction == 1 else candle.low <= target
                if hit: return index, target
            elif s.exit.exit_type is ExitType.TIME_EXIT and index - entry_i >= bars:
                return index, candle.close
            elif (s.exit.exit_type is ExitType.STATE_INVALIDATION_EXIT
                  and not BacktestEngine._confirmed(s, candles, max(0, index - 1))):
                return index, candle.close
        return len(candles) - 1, candles[-1].close

    def _result(self, identity: str, s: ExecutableSignalDefinition, candles: list[_Candle],
                trades: tuple[Trade, ...], version: str,
                diagnostics: tuple[int, int, int, int]) -> BacktestResult:
        wins, losses = [t.net_pnl for t in trades if t.net_pnl > 0], [t.net_pnl for t in trades if t.net_pnl < 0]
        gross_profit, gross_loss = sum(max(t.gross_pnl, 0) for t in trades), sum(min(t.gross_pnl, 0) for t in trades)
        equity = peak = drawdown = 0.0
        for trade in trades:
            equity += trade.net_pnl; peak = max(peak, equity); drawdown = max(drawdown, peak - equity)
        n = len(trades); span = sum((t.exit_time - t.entry_time for t in trades), timedelta())
        return BacktestResult(identity, s.source_strategy_candidate_id, s.symbol, s.execution_timeframe,
            s.context_timeframes, candles[0].time, candles[-1].time, n, len(wins), len(losses),
            gross_profit, gross_loss, sum(t.net_pnl for t in trades),
            (sum(wins) / abs(sum(losses)) if losses else None),
            sum(t.net_pnl for t in trades) / n if n else 0.0, len(wins) / n if n else 0.0,
            drawdown, max((t.net_pnl for t in trades), default=0.0),
            min((t.net_pnl for t in trades), default=0.0),
            sum(t.holding_bars for t in trades) / n if n else 0.0, span / n if n else timedelta(),
            f"fixed:{self.costs.transaction_cost}", f"fixed_per_fill:{self.costs.slippage}",
            version, self.engine_version, trades, s.signal_id, *diagnostics)
