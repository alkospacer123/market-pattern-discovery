"""Deterministic close-to-close multi-timeframe backtester."""
from __future__ import annotations
from dataclasses import dataclass
import pandas as pd

from .metrics import calculate_metrics
from .portfolio import FixedRiskPortfolio
from .strategy import Strategy

TRADE_COLUMNS = ["strategy", "symbol", "direction", "entry_time", "entry_price",
                 "exit_time", "exit_price", "stop_loss", "exit_reason",
                 "profit_points", "profit_R", "quantity", "costs", "net_profit"]


@dataclass(frozen=True)
class BacktestResult:
    trades: pd.DataFrame
    equity_curve: pd.DataFrame
    metrics: dict


class Backtester:
    def __init__(self, portfolio: FixedRiskPortfolio | None = None, *,
                 commission_per_unit: float = 0.0, slippage_points: float = 0.0) -> None:
        if commission_per_unit < 0 or slippage_points < 0:
            raise ValueError("costs and slippage must be non-negative")
        self.portfolio = portfolio or FixedRiskPortfolio()
        self.commission_per_unit = commission_per_unit
        self.slippage_points = slippage_points

    def run(self, strategy: Strategy, symbol: str, h1: pd.DataFrame, h4: pd.DataFrame) -> BacktestResult:
        if h1.empty or h4.empty:
            raise ValueError("H1 and H4 closed-candle data are required")
        if h1.index.tz is None or h4.index.tz is None or not h1.index.is_monotonic_increasing or not h4.index.is_monotonic_increasing:
            raise ValueError("timestamps must be timezone-aware and sorted")
        if (h1.index.year == 2025).any() or (h4.index.year == 2025).any():
            raise ValueError("calendar year 2025 TRUE OOS is locked")
        low, high = strategy.calculate_indicators(h1, h4)
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
                    costs = 2 * self.commission_per_unit * position["quantity"]
                    net = points * position["quantity"] * self.portfolio.point_value - costs
                    initial_risk = abs(position["entry_price"] - position["initial_stop"])
                    records.append({"strategy": strategy.name, "symbol": symbol, "direction": direction,
                        "entry_time": position["entry_time"], "entry_price": position["entry_price"],
                        "exit_time": timestamp, "exit_price": exit_price, "stop_loss": position["initial_stop"],
                        "exit_reason": "ATR_TRAILING_STOP", "profit_points": points,
                        "profit_R": points / initial_risk - costs / (position["quantity"] * self.portfolio.point_value * initial_risk),
                        "quantity": position["quantity"], "costs": costs, "net_profit": net})
                    equity += net
                    position = None
                else:
                    if position["direction"] == "LONG":
                        position["extreme"] = max(position["extreme"], bar["High"])
                        position["active_stop"] = max(old_stop, strategy.manage_position("LONG", position["extreme"], bar["ATR"]))
                    else:
                        position["extreme"] = min(position["extreme"], bar["Low"])
                        position["active_stop"] = min(old_stop, strategy.manage_position("SHORT", position["extreme"], bar["ATR"]))
            if position is None and pd.notna(bar["ATR"]):
                signal = strategy.generate_signal(bar, current_regime)
                if signal:
                    raw_entry = float(bar["Close"])
                    entry = raw_entry + self.slippage_points if signal == "LONG" else raw_entry - self.slippage_points
                    stop = strategy.calculate_stop_loss(signal, entry, float(bar["ATR"]))
                    position = {"direction": signal, "entry_time": timestamp, "entry_price": entry,
                                "initial_stop": stop, "active_stop": stop, "extreme": entry,
                                "quantity": self.portfolio.size(equity, entry, stop)}
            curve.append({"time": timestamp, "equity": equity})
        trades = pd.DataFrame(records, columns=TRADE_COLUMNS)
        equity_curve = pd.DataFrame(curve).set_index("time")
        return BacktestResult(trades, equity_curve, calculate_metrics(trades, equity_curve))
