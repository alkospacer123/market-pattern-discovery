"""Frozen causal H1/M15 liquidity-sweep false-breakout strategy."""
from __future__ import annotations

from dataclasses import asdict, dataclass
from enum import Enum

import pandas as pd

from ...core.indicators import adx, atr, ema
from ...core.mtf import align_closed_context
from ...core.portfolio import FixedRiskPortfolio

STRATEGY_ID = "R2_Liquidity_Sweep_False_Breakout_v1.0"
TRADE_COLUMNS = [
    "trade_id", "strategy_id", "symbol", "direction", "range_context_time",
    "range_high", "range_low", "range_midpoint", "sweep_time", "sweep_extreme",
    "sweep_depth_points", "sweep_depth_atr", "entry_time", "entry_price",
    "initial_stop", "initial_risk_points", "initial_risk_ticks", "target_price",
    "exit_time", "exit_price", "exit_reason", "bars_held", "gross_R",
    "cost_R_C1", "net_R_C1", "MAE_R", "MFE_R", "ADX_H1_entry",
    "EMA200_slope_ATR_H1_entry", "ATR_M15_entry", "quantity",
]


class R2State(str, Enum):
    FLAT = "FLAT"
    POSITION_OPEN = "POSITION_OPEN"


@dataclass(frozen=True)
class R2Parameters:
    context_timeframe: str = "H1"
    execution_timeframe: str = "M15"
    range_lookback_h1: int = 20
    adx_period: int = 14
    adx_range_max: float = 25.0
    ema_period: int = 200
    ema_slope_lookback: int = 10
    ema_slope_max_atr: float = 0.35
    atr_period_m15: int = 14
    minimum_sweep_atr: float = 0.05
    maximum_sweep_atr: float = 1.0
    require_half_bar_rejection: bool = True
    stop_buffer_atr: float = 0.10
    max_initial_stop_atr: float = 1.5
    target: str = "range_midpoint"
    max_holding_bars_m15: int = 16


class R2LiquiditySweep:
    """Deterministic one-position state machine over close-labelled bars."""
    name = STRATEGY_ID

    def __init__(self, parameters: R2Parameters | None = None):
        self.parameters = parameters or R2Parameters()

    @staticmethod
    def _validate(frame: pd.DataFrame, label: str) -> None:
        if frame.empty or frame.index.tz is None or not frame.index.is_monotonic_increasing:
            raise ValueError(f"closed {label} timestamps must be timezone-aware, nonempty, and sorted")
        if frame.index.has_duplicates:
            raise ValueError(f"closed {label} timestamps must be unique")
        if (frame.index >= pd.Timestamp("2025-01-01", tz=frame.index.tz)).any():
            raise ValueError("timestamp >= 2025-01-01 TRUE OOS is locked")
        if not {"Open", "High", "Low", "Close"}.issubset(frame.columns):
            raise ValueError(f"{label} OHLC columns are required")

    def calculate_h1_context(self, h1: pd.DataFrame) -> pd.DataFrame:
        self._validate(h1, "H1")
        p, out = self.parameters, h1.copy()
        # shift(1) excludes the context candle itself from its range.
        out["range_high"] = out.High.shift(1).rolling(p.range_lookback_h1, min_periods=p.range_lookback_h1).max()
        out["range_low"] = out.Low.shift(1).rolling(p.range_lookback_h1, min_periods=p.range_lookback_h1).min()
        out["range_midpoint"] = (out.range_high + out.range_low) / 2.0
        out["ATR_H1"] = atr(out, p.adx_period)
        out["ADX_H1"] = adx(out, p.adx_period)
        out["EMA200"] = ema(out.Close, p.ema_period)
        out["EMA200_slope_ATR_H1"] = (out.EMA200 - out.EMA200.shift(p.ema_slope_lookback)).abs() / out.ATR_H1
        out["range_regime"] = ((out.ADX_H1 <= p.adx_range_max) &
                               (out.EMA200_slope_ATR_H1 <= p.ema_slope_max_atr))
        return out

    def prepare(self, h1: pd.DataFrame, m15: pd.DataFrame) -> pd.DataFrame:
        self._validate(m15, "M15")
        context = self.calculate_h1_context(h1)[
            ["Close", "range_high", "range_low", "range_midpoint", "ADX_H1",
             "EMA200_slope_ATR_H1", "range_regime"]
        ].rename(columns={"Close": "H1_Close"})
        out = align_closed_context(m15, context, "15min")
        out["ATR_M15"] = atr(m15, self.parameters.atr_period_m15)
        # A completed H1 close can cause a close-based exit at the same M15 close.
        close_context = pd.merge_asof(
            pd.DataFrame({"execution_close": m15.index}),
            pd.DataFrame({"failure_context_time": h1.index, "H1_Close_at_execution": h1.Close.to_numpy()}),
            left_on="execution_close", right_on="failure_context_time", direction="backward",
        ).set_index(m15.index)
        out[["failure_context_time", "H1_Close_at_execution"]] = close_context[["failure_context_time", "H1_Close_at_execution"]]
        return out

    def frozen_parameters(self) -> dict:
        return asdict(self.parameters)

    def run(self, h1: pd.DataFrame, m15: pd.DataFrame, symbol: str, *, tick_size: float = .001,
            portfolio: FixedRiskPortfolio | None = None) -> pd.DataFrame:
        d, p = self.prepare(h1, m15), self.parameters
        portfolio = portfolio or FixedRiskPortfolio()
        state, pos, records, equity = R2State.FLAT, None, [], portfolio.initial_capital

        def close_position(i: int, price: float, reason: str, low: float, high: float) -> None:
            nonlocal state, pos, equity
            sign = 1 if pos["direction"] == "LONG" else -1
            risk = pos["initial_risk_points"]
            gross = sign * (price - pos["entry_price"]) / risk
            cost = 2 * tick_size / risk
            minimum = min(pos["min_low"], low)
            maximum = max(pos["max_high"], high)
            rec = {**pos["metadata"], "exit_time": d.index[i], "exit_price": price,
                   "exit_reason": reason, "bars_held": pos["bars_held"] + 1,
                   "gross_R": gross, "cost_R_C1": cost, "net_R_C1": gross - cost,
                   "MAE_R": max(0., pos["entry_price"] - minimum if sign == 1 else maximum - pos["entry_price"]) / risk,
                   "MFE_R": max(0., maximum - pos["entry_price"] if sign == 1 else pos["entry_price"] - minimum) / risk,
                   "quantity": pos["quantity"]}
            records.append(rec)
            equity += (gross - cost) * equity * portfolio.risk_fraction
            state, pos = R2State.FLAT, None

        for i, (_, bar) in enumerate(d.iterrows()):
            if state == R2State.POSITION_OPEN:
                long = pos["direction"] == "LONG"
                stop_hit = bar.Low <= pos["initial_stop"] if long else bar.High >= pos["initial_stop"]
                target_hit = bar.High >= pos["target_price"] if long else bar.Low <= pos["target_price"]
                if stop_hit:
                    fill = min(float(bar.Open), pos["initial_stop"]) if long else max(float(bar.Open), pos["initial_stop"])
                    close_position(i, fill, "STOP", fill if long else pos["min_low"], pos["max_high"] if long else fill)
                    continue
                if target_hit:
                    target = pos["target_price"]
                    close_position(i, target, "RANGE_MIDPOINT_TARGET", pos["min_low"] if long else target,
                                   target if long else pos["max_high"])
                    continue
                new_h1 = pd.notna(bar.failure_context_time) and bar.failure_context_time > pos["last_failure_context_time"]
                failure = new_h1 and ((bar.H1_Close_at_execution < pos["range_low"]) if long else
                                      (bar.H1_Close_at_execution > pos["range_high"]))
                if failure:
                    close_position(i, float(bar.Close), "RANGE_FAILURE", float(bar.Low), float(bar.High))
                    continue
                held = pos["bars_held"] + 1
                pos["min_low"], pos["max_high"] = min(pos["min_low"], float(bar.Low)), max(pos["max_high"], float(bar.High))
                if held >= p.max_holding_bars_m15:
                    close_position(i, float(bar.Close), "TIME_EXIT", float(bar.Low), float(bar.High))
                    continue
                pos["bars_held"] = held
                if new_h1:
                    pos["last_failure_context_time"] = bar.failure_context_time
                continue

            required = [bar.context_time, bar.range_high, bar.range_low, bar.range_midpoint,
                        bar.ATR_M15, bar.ADX_H1, bar.EMA200_slope_ATR_H1]
            if not all(pd.notna(value) for value in required) or not bool(bar.range_regime) or bar.ATR_M15 <= 0:
                continue
            midpoint = (bar.High + bar.Low) / 2.0
            long_depth, short_depth = bar.range_low - bar.Low, bar.High - bar.range_high
            direction = None
            if (bar.Low < bar.range_low and bar.Close > bar.range_low and
                    p.minimum_sweep_atr * bar.ATR_M15 <= long_depth <= p.maximum_sweep_atr * bar.ATR_M15 and
                    (not p.require_half_bar_rejection or bar.Close >= midpoint)):
                direction, depth, extreme = "LONG", float(long_depth), float(bar.Low)
            elif (bar.High > bar.range_high and bar.Close < bar.range_high and
                  p.minimum_sweep_atr * bar.ATR_M15 <= short_depth <= p.maximum_sweep_atr * bar.ATR_M15 and
                  (not p.require_half_bar_rejection or bar.Close <= midpoint)):
                direction, depth, extreme = "SHORT", float(short_depth), float(bar.High)
            if direction is None:
                continue
            entry, target, atr_entry = float(bar.Close), float(bar.range_midpoint), float(bar.ATR_M15)
            stop = extreme - p.stop_buffer_atr * atr_entry if direction == "LONG" else extreme + p.stop_buffer_atr * atr_entry
            risk = entry - stop if direction == "LONG" else stop - entry
            target_valid = target > entry if direction == "LONG" else target < entry
            if risk <= 0 or risk > p.max_initial_stop_atr * atr_entry or not target_valid:
                continue
            metadata = {"trade_id": f"{symbol}-{len(records)+1:06d}", "strategy_id": self.name,
                        "symbol": symbol, "direction": direction, "range_context_time": bar.context_time,
                        "range_high": float(bar.range_high), "range_low": float(bar.range_low),
                        "range_midpoint": target, "sweep_time": d.index[i], "sweep_extreme": extreme,
                        "sweep_depth_points": depth, "sweep_depth_atr": depth / atr_entry,
                        "entry_time": d.index[i], "entry_price": entry, "initial_stop": stop,
                        "initial_risk_points": risk, "initial_risk_ticks": risk / tick_size,
                        "target_price": target, "ADX_H1_entry": float(bar.ADX_H1),
                        "EMA200_slope_ATR_H1_entry": float(bar.EMA200_slope_ATR_H1), "ATR_M15_entry": atr_entry}
            last_failure = bar.failure_context_time if pd.notna(bar.failure_context_time) else pd.Timestamp.min.tz_localize(d.index.tz)
            pos = {"direction": direction, "entry_price": entry, "initial_stop": stop,
                   "initial_risk_points": risk, "target_price": target, "range_low": float(bar.range_low),
                   "range_high": float(bar.range_high), "bars_held": 0, "min_low": entry, "max_high": entry,
                   "last_failure_context_time": last_failure,
                   "quantity": portfolio.size(equity, entry, stop), "metadata": metadata}
            state = R2State.POSITION_OPEN
        return pd.DataFrame(records, columns=TRADE_COLUMNS)
