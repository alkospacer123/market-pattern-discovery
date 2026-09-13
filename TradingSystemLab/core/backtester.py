"""Deterministic close-to-close multi-timeframe backtester."""
from __future__ import annotations
from dataclasses import dataclass
import pandas as pd

from .metrics import calculate_metrics
from .portfolio import FixedRiskPortfolio
from .strategy import Strategy
from .execution import tick_cost_r

TRADE_COLUMNS = ["trade_id", "strategy", "symbol", "direction", "entry_time", "entry_price",
                 "initial_stop", "initial_risk", "exit_time", "exit_price", "exit_reason",
                 "bars_held", "gross_profit", "gross_R", "MAE_points", "MFE_points",
                 "MAE_R", "MFE_R", "profit_points", "profit_R", "quantity", "costs", "net_profit",
                 "tick_size", "initial_risk_ticks", "cost_R"]


@dataclass(frozen=True)
class BacktestResult:
    trades: pd.DataFrame
    equity_curve: pd.DataFrame
    metrics: dict


class Backtester:
    def __init__(self, portfolio: FixedRiskPortfolio | None = None, *,
                 commission_per_unit: float = 0.0, slippage_points: float = 0.0,
                 cost_ticks_per_side: float = 0.0, tick_size: float = 1.0) -> None:
        if min(commission_per_unit, slippage_points, cost_ticks_per_side) < 0 or tick_size <= 0:
            raise ValueError("costs and slippage must be non-negative")
        self.portfolio = portfolio or FixedRiskPortfolio()
        self.commission_per_unit = commission_per_unit
        self.slippage_points = slippage_points
        self.cost_ticks_per_side = cost_ticks_per_side
        self.tick_size = tick_size

    def run(self, strategy: Strategy, symbol: str, h1: pd.DataFrame, h4: pd.DataFrame, *,
            entry_start: pd.Timestamp | None = None,
            entry_end: pd.Timestamp | None = None) -> BacktestResult:
        """Run a strategy, optionally admitting entries only in ``[start, end)``.

        Indicator calculation still receives the preceding history as causal
        warm-up.  Iteration starts at ``entry_start`` with a deliberately flat
        position, and a position admitted before ``entry_end`` may continue to
        its natural exit afterwards.  This makes independent forward folds
        possible without carrying train or previous-fold position state.
        """
        if h1.empty or h4.empty:
            raise ValueError("H1 and H4 closed-candle data are required")
        if h1.index.tz is None or h4.index.tz is None or not h1.index.is_monotonic_increasing or not h4.index.is_monotonic_increasing:
            raise ValueError("timestamps must be timezone-aware and sorted")
        if (h1.index.year >= 2025).any() or (h4.index.year >= 2025).any():
            raise ValueError("calendar year 2025+ TRUE OOS is locked")
        if entry_start is not None and entry_end is not None and entry_start >= entry_end:
            raise ValueError("entry_start must precede entry_end")
        low, high = strategy.calculate_indicators(h1, h4)
        if entry_start is not None:
            low = low.loc[low.index >= entry_start]
        high_cursor, position, records = -1, None, []
        equity = self.portfolio.initial_capital
        curve = []
        for timestamp, bar in low.iterrows():
            while high_cursor + 1 < len(high) and high.index[high_cursor + 1] <= timestamp:
                high_cursor += 1
            current_regime = strategy.regime(high.iloc[high_cursor]) if high_cursor >= 0 else None
            if position is not None:
                # The stop entering this bar is checked before incorporating this
                # bar's extreme; this deterministic rule avoids unknowable OHLC order.
                old_stop = position["active_stop"]
                hit = strategy.exit_signal(position["direction"], bar, old_stop)
                if hit:
                    direction = position["direction"]
                    gap_price = min(bar["Open"], old_stop) if direction == "LONG" else max(bar["Open"], old_stop)
                    exit_price = gap_price - self.slippage_points if direction == "LONG" else gap_price + self.slippage_points
                    sign = 1 if direction == "LONG" else -1
                    points = sign * (exit_price - position["entry_price"])
                    # A stop bar is deliberately excluded from path extrema: OHLC
                    # cannot establish whether its favourable move preceded the stop.
                    costs = 2 * (self.commission_per_unit + self.cost_ticks_per_side * self.tick_size *
                                 self.portfolio.point_value) * position["quantity"]
                    net = points * position["quantity"] * self.portfolio.point_value - costs
                    initial_risk = abs(position["entry_price"] - position["initial_stop"])
                    cost_r = tick_cost_r(position["entry_price"], position["initial_stop"],
                                         self.tick_size, self.cost_ticks_per_side)
                    gross = points * position["quantity"] * self.portfolio.point_value
                    mae = (position["entry_price"] - position["min_low"] if direction == "LONG" else
                           position["max_high"] - position["entry_price"])
                    # The execution price is observable on the exit candle; lows/highs
                    # beyond it are not. Include only adverse travel through execution.
                    mae = max(mae, position["entry_price"] - exit_price if direction == "LONG"
                              else exit_price - position["entry_price"])
                    mfe = (position["max_high"] - position["entry_price"] if direction == "LONG" else
                           position["entry_price"] - position["min_low"])
                    records.append({"trade_id": f"{symbol}-{position['sequence']:06d}",
                        "strategy": strategy.name, "symbol": symbol, "direction": direction,
                        "entry_time": position["entry_time"], "entry_price": position["entry_price"],
                        "initial_stop": position["initial_stop"], "initial_risk": initial_risk,
                        "exit_time": timestamp, "exit_price": exit_price, "exit_reason": "ATR_TRAILING_STOP",
                        "bars_held": position["bars_held"] + 1, "gross_profit": gross,
                        "gross_R": points / initial_risk, "MAE_points": max(0.0, mae),
                        "MFE_points": max(0.0, mfe), "MAE_R": max(0.0, mae) / initial_risk,
                        "MFE_R": max(0.0, mfe) / initial_risk, "profit_points": points,
                        "profit_R": points / initial_risk - cost_r - 2 * self.commission_per_unit /
                        (self.portfolio.point_value * initial_risk),
                        "quantity": position["quantity"], "costs": costs, "net_profit": net,
                        "tick_size": self.tick_size, "initial_risk_ticks": initial_risk / self.tick_size,
                        "cost_R": cost_r + 2 * self.commission_per_unit /
                        (self.portfolio.point_value * initial_risk)})
                    equity += net
                    position = None
                else:
                    position["bars_held"] += 1
                    position["min_low"] = min(position["min_low"], float(bar["Low"]))
                    position["max_high"] = max(position["max_high"], float(bar["High"]))
                    if position["direction"] == "LONG":
                        position["extreme"] = max(position["extreme"], bar["High"])
                        position["active_stop"] = max(old_stop, strategy.manage_position("LONG", position["extreme"], bar["ATR"]))
                    else:
                        position["extreme"] = min(position["extreme"], bar["Low"])
                        position["active_stop"] = min(old_stop, strategy.manage_position("SHORT", position["extreme"], bar["ATR"]))
            entries_open = entry_end is None or timestamp < entry_end
            if position is None and entries_open and pd.notna(bar["ATR"]):
                signal = strategy.generate_signal(bar, current_regime)
                if signal:
                    raw_entry = float(bar["Close"])
                    entry = raw_entry + self.slippage_points if signal == "LONG" else raw_entry - self.slippage_points
                    stop = strategy.calculate_stop_loss(signal, entry, float(bar["ATR"]))
                    position = {"direction": signal, "entry_time": timestamp, "entry_price": entry,
                                "initial_stop": stop, "active_stop": stop, "extreme": entry,
                                "quantity": self.portfolio.size(equity, entry, stop),
                                "sequence": len(records) + 1, "bars_held": 0,
                                "min_low": entry, "max_high": entry}
            curve.append({"time": timestamp, "equity": equity})
        trades = pd.DataFrame(records, columns=TRADE_COLUMNS)
        equity_curve = pd.DataFrame(curve).set_index("time")
        return BacktestResult(trades, equity_curve, calculate_metrics(trades, equity_curve))
