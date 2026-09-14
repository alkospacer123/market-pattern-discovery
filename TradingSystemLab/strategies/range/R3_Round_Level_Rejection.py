"""Frozen causal M15 round-level rejection strategy."""
from __future__ import annotations

from dataclasses import asdict, dataclass

import pandas as pd

from ...core.indicators import adx, atr, ema
from ...core.levels import level_offset, nearest_lower_level, nearest_upper_level
from ...core.mtf import align_closed_context
from ...core.portfolio import FixedRiskPortfolio

STRATEGY_ID = "R3_Round_Level_Rejection_v1.0"
TRADE_COLUMNS = [
    "trade_id", "strategy_id", "symbol", "direction", "signal_time", "round_level",
    "round_level_step", "penetration_points", "penetration_atr", "signal_open",
    "signal_high", "signal_low", "signal_close", "entry_time", "entry_price",
    "initial_stop", "initial_risk_points", "initial_risk_ticks", "target_price",
    "target_distance_points", "exit_time", "exit_price", "exit_reason", "bars_held",
    "gross_R", "cost_R_C1", "net_R_C1", "MAE_R", "MFE_R", "H1_context_time",
    "H1_ADX14", "H1_ATR14", "H1_EMA200_slope_ATR", "quantity",
]


@dataclass(frozen=True)
class R3Parameters:
    execution_timeframe: str = "M15"
    atr_period_m15: int = 14
    minimum_penetration_atr: float = .05
    maximum_penetration_atr: float = .75
    require_half_bar_rejection: bool = True
    minimum_close_distance_atr: float = .05
    stop_buffer_atr: float = .10
    max_initial_stop_atr: float = 1.25
    target_fraction_of_step: float = .50
    max_holding_bars_m15: int = 12
    h1_diagnostics_enabled: bool = True
    h1_ema_period: int = 200
    h1_ema_slope_lookback: int = 10


class R3RoundLevelRejection:
    """One-position engine; signal OHLC is never used for exit execution."""
    name = STRATEGY_ID

    def __init__(self, parameters: R3Parameters | None = None):
        self.parameters = parameters or R3Parameters()

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

    def prepare(self, m15: pd.DataFrame, h1: pd.DataFrame | None = None) -> pd.DataFrame:
        self._validate(m15, "M15")
        out = m15.copy()
        out["ATR_M15"] = atr(m15, self.parameters.atr_period_m15)
        for column in ("H1_context_time", "H1_ADX14", "H1_ATR14", "H1_EMA200_slope_ATR"):
            out[column] = pd.NaT if column.endswith("time") else float("nan")
        if h1 is not None:
            self._validate(h1, "H1")
        if h1 is not None and self.parameters.h1_diagnostics_enabled:
            context = h1.copy()
            context["H1_ATR14"] = atr(context, 14)
            context["H1_ADX14"] = adx(context, 14)
            e = ema(context.Close, self.parameters.h1_ema_period)
            context["H1_EMA200_slope_ATR"] = ((e - e.shift(self.parameters.h1_ema_slope_lookback)) /
                                               context.H1_ATR14)
            aligned = align_closed_context(m15, context[["H1_ADX14", "H1_ATR14", "H1_EMA200_slope_ATR"]], "15min")
            out[["H1_ADX14", "H1_ATR14", "H1_EMA200_slope_ATR"]] = aligned[["H1_ADX14", "H1_ATR14", "H1_EMA200_slope_ATR"]]
            out["H1_context_time"] = aligned.context_time
        return out

    def frozen_parameters(self) -> dict:
        return asdict(self.parameters)

    def run(self, m15: pd.DataFrame, symbol: str, *, round_level_step: float,
            tick_size: float = .001, h1: pd.DataFrame | None = None,
            portfolio: FixedRiskPortfolio | None = None) -> pd.DataFrame:
        if round_level_step <= 0 or tick_size <= 0:
            raise ValueError("round_level_step and tick_size must be positive")
        d, p = self.prepare(m15, h1), self.parameters
        portfolio = portfolio or FixedRiskPortfolio()
        pos, records, equity = None, [], portfolio.initial_capital

        def close(i: int, price: float, reason: str, low: float, high: float) -> None:
            nonlocal pos, equity
            sign, risk = (1 if pos["direction"] == "LONG" else -1), pos["risk"]
            gross = sign * (price - pos["entry"]) / risk
            lo, hi = min(pos["lo"], low), max(pos["hi"], high)
            mae = max(0., pos["entry"] - lo if sign == 1 else hi - pos["entry"]) / risk
            mfe = max(0., hi - pos["entry"] if sign == 1 else pos["entry"] - lo) / risk
            cost = 2 * tick_size / risk
            records.append({**pos["metadata"], "exit_time": d.index[i], "exit_price": price,
                            "exit_reason": reason, "bars_held": pos["held"] + 1, "gross_R": gross,
                            "cost_R_C1": cost, "net_R_C1": gross - cost, "MAE_R": mae,
                            "MFE_R": mfe, "quantity": pos["quantity"]})
            equity += (gross - cost) * equity * portfolio.risk_fraction
            pos = None

        for i, (timestamp, bar) in enumerate(d.iterrows()):
            if pos is not None:
                long = pos["direction"] == "LONG"
                stop_hit = bar.Low <= pos["stop"] if long else bar.High >= pos["stop"]
                target_hit = bar.High >= pos["target"] if long else bar.Low <= pos["target"]
                if stop_hit:
                    fill = min(float(bar.Open), pos["stop"]) if long else max(float(bar.Open), pos["stop"])
                    close(i, fill, "STOP", fill if long else float(bar.Low),
                          float(bar.High) if long else fill); continue
                if target_hit:
                    close(i, pos["target"], "ROUND_LEVEL_MIDPOINT_TARGET",
                          float(bar.Low) if long else pos["target"],
                          pos["target"] if long else float(bar.High)); continue
                failure = bar.Close < pos["level"] if long else bar.Close > pos["level"]
                if failure:
                    close(i, float(bar.Close), "LEVEL_FAILURE", float(bar.Low), float(bar.High)); continue
                pos["held"] += 1
                pos["lo"], pos["hi"] = min(pos["lo"], float(bar.Low)), max(pos["hi"], float(bar.High))
                if pos["held"] >= p.max_holding_bars_m15:
                    # close() adds the current executable bar; compensate its convention.
                    pos["held"] -= 1
                    close(i, float(bar.Close), "TIME_EXIT", float(bar.Low), float(bar.High))
                continue

            if pd.isna(bar.ATR_M15) or bar.ATR_M15 <= 0:
                continue
            atr_value, midpoint = float(bar.ATR_M15), (float(bar.High) + float(bar.Low)) / 2
            lower, upper = float(nearest_lower_level(bar.Open, round_level_step)), float(nearest_upper_level(bar.Open, round_level_step))
            long_depth, short_depth = lower - float(bar.Low), float(bar.High) - upper
            direction = None
            if (bar.Open >= lower and bar.Low < lower and bar.Close > lower and
                    bar.Low > lower - round_level_step and
                    p.minimum_penetration_atr * atr_value <= long_depth <= p.maximum_penetration_atr * atr_value and
                    (not p.require_half_bar_rejection or bar.Close >= midpoint) and
                    bar.Close - lower >= p.minimum_close_distance_atr * atr_value):
                direction, level, depth, extreme = "LONG", lower, long_depth, float(bar.Low)
            elif (bar.Open <= upper and bar.High > upper and bar.Close < upper and
                  bar.High < upper + round_level_step and
                  p.minimum_penetration_atr * atr_value <= short_depth <= p.maximum_penetration_atr * atr_value and
                  (not p.require_half_bar_rejection or bar.Close <= midpoint) and
                  upper - bar.Close >= p.minimum_close_distance_atr * atr_value):
                direction, level, depth, extreme = "SHORT", upper, short_depth, float(bar.High)
            if direction is None:
                continue
            entry = float(bar.Close)
            stop = extreme - p.stop_buffer_atr * atr_value if direction == "LONG" else extreme + p.stop_buffer_atr * atr_value
            risk = entry - stop if direction == "LONG" else stop - entry
            signed_fraction = p.target_fraction_of_step if direction == "LONG" else -p.target_fraction_of_step
            target = float(level_offset(level, round_level_step, signed_fraction))
            if risk <= 0 or risk > p.max_initial_stop_atr * atr_value or not (target > entry if direction == "LONG" else target < entry):
                continue
            metadata = {"trade_id": f"{symbol}-{len(records)+1:06d}", "strategy_id": self.name,
                        "symbol": symbol, "direction": direction, "signal_time": timestamp,
                        "round_level": level, "round_level_step": round_level_step,
                        "penetration_points": depth, "penetration_atr": depth / atr_value,
                        "signal_open": float(bar.Open), "signal_high": float(bar.High),
                        "signal_low": float(bar.Low), "signal_close": entry, "entry_time": timestamp,
                        "entry_price": entry, "initial_stop": stop, "initial_risk_points": risk,
                        "initial_risk_ticks": risk / tick_size, "target_price": target,
                        "target_distance_points": abs(target-entry), "H1_context_time": bar.H1_context_time,
                        "H1_ADX14": bar.H1_ADX14, "H1_ATR14": bar.H1_ATR14,
                        "H1_EMA200_slope_ATR": bar.H1_EMA200_slope_ATR}
            pos = {"direction": direction, "entry": entry, "stop": stop, "risk": risk,
                   "target": target, "level": level, "held": 0, "lo": entry, "hi": entry,
                   "quantity": portfolio.size(equity, entry, stop), "metadata": metadata}
        return pd.DataFrame(records, columns=TRADE_COLUMNS)
