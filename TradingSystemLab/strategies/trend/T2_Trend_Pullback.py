"""Frozen, causal T2 trend-pullback-continuation implementation."""
from __future__ import annotations

from dataclasses import asdict, dataclass
from enum import Enum
import pandas as pd

from ...core.indicators import adx, atr, ema
from ...core.portfolio import FixedRiskPortfolio

STRATEGY_ID = "T2_Trend_Pullback_Continuation_v1.0"


class T2State(str, Enum):
    FLAT_NO_SETUP = "FLAT_NO_SETUP"
    LONG_PULLBACK_ARMED = "LONG_PULLBACK_ARMED"
    SHORT_PULLBACK_ARMED = "SHORT_PULLBACK_ARMED"
    POSITION_OPEN = "POSITION_OPEN"


@dataclass(frozen=True)
class T2Parameters:
    ema_fast: int = 20
    ema_trend: int = 50
    ema_slow: int = 200
    adx_period: int = 14
    adx_threshold: float = 20.0
    atr_period: int = 14
    atr_regime_window: int = 20
    impulse_lookback: int = 10
    impulse_distance_atr: float = 0.5
    confirmation_window: int = 3
    stop_buffer_atr: float = 0.10
    max_initial_stop_atr: float = 3.0
    trailing_atr: float = 3.0


@dataclass
class PullbackSetup:
    direction: str
    pullback_start_time: pd.Timestamp
    pullback_start_index: int
    expiry_index: int
    pullback_extreme: float
    impulse_reference_time: pd.Timestamp


class T2TrendPullback:
    """Explicit one-position state machine operating on closed H1 candles."""
    name = STRATEGY_ID

    def __init__(self, parameters: T2Parameters | None = None) -> None:
        self.parameters = parameters or T2Parameters()

    def calculate_indicators(self, h1: pd.DataFrame) -> pd.DataFrame:
        self._validate(h1)
        p, out = self.parameters, h1.copy()
        out["EMA20"] = ema(out.Close, p.ema_fast)
        out["EMA50"] = ema(out.Close, p.ema_trend)
        out["EMA200"] = ema(out.Close, p.ema_slow)
        out["ATR"] = atr(out, p.atr_period)
        out["ADX"] = adx(out, p.adx_period)
        out["ATRMean20"] = out.ATR.rolling(p.atr_regime_window, min_periods=p.atr_regime_window).mean()
        return out

    @staticmethod
    def _validate(frame: pd.DataFrame) -> None:
        if frame.empty or frame.index.tz is None or not frame.index.is_monotonic_increasing:
            raise ValueError("closed H1 timestamps must be timezone-aware, nonempty, and sorted")
        if (frame.index.year >= 2025).any():
            raise ValueError("calendar year 2025+ TRUE OOS is locked")
        if not {"Open", "High", "Low", "Close"}.issubset(frame.columns):
            raise ValueError("H1 OHLC columns are required")

    def regime(self, bar: pd.Series) -> str | None:
        needed = ["EMA50", "EMA200", "ADX", "ATR", "ATRMean20"]
        if bar[needed].isna().any() or bar.ADX <= self.parameters.adx_threshold or bar.ATR < bar.ATRMean20:
            return None
        if bar.EMA50 > bar.EMA200:
            return "LONG"
        if bar.EMA50 < bar.EMA200:
            return "SHORT"
        return None

    def impulse_reference(self, data: pd.DataFrame, index: int, direction: str) -> pd.Timestamp | None:
        """Return latest evidence strictly before ``index`` (never the pullback)."""
        p = self.parameters
        prior = data.iloc[max(0, index - p.impulse_lookback):index]
        if direction == "LONG":
            valid = (prior.Close > prior.EMA20) & ((prior.Close - prior.EMA20) >= p.impulse_distance_atr * prior.ATR)
        else:
            valid = (prior.Close < prior.EMA20) & ((prior.EMA20 - prior.Close) >= p.impulse_distance_atr * prior.ATR)
        matches = prior.index[valid.fillna(False)]
        return matches[-1] if len(matches) else None

    def is_pullback(self, bar: pd.Series, direction: str) -> bool:
        return bool(bar.Low <= bar.EMA20 and bar.Close >= bar.EMA50) if direction == "LONG" else bool(
            bar.High >= bar.EMA20 and bar.Close <= bar.EMA50)

    def is_confirmation(self, bar: pd.Series, previous: pd.Series, direction: str) -> bool:
        return bool(bar.Close > previous.High and bar.Close > bar.EMA20) if direction == "LONG" else bool(
            bar.Close < previous.Low and bar.Close < bar.EMA20)

    def run(self, h1: pd.DataFrame, symbol: str, *, tick_size: float = 0.001,
            portfolio: FixedRiskPortfolio | None = None) -> pd.DataFrame:
        data, p = self.calculate_indicators(h1), self.parameters
        portfolio = portfolio or FixedRiskPortfolio()
        state, setup, position, records, equity = T2State.FLAT_NO_SETUP, None, None, [], portfolio.initial_capital

        def close_trade(i: int, price: float, reason: str) -> None:
            nonlocal position, state, equity
            d, sign = position["direction"], 1 if position["direction"] == "LONG" else -1
            points = sign * (price - position["entry_price"])
            risk = position["initial_risk_points"]
            cost_r = 2.0 * tick_size / risk
            gross_r = points / risk
            records.append({**position["metadata"], "exit_time": data.index[i], "exit_price": price,
                "exit_reason": reason, "bars_held": position["bars_held"] + 1, "gross_R": gross_r,
                "cost_R_C1": cost_r, "net_R_C1": gross_r - cost_r,
                "MAE_R": max(0.0, position["entry_price"] - position["min_low"] if d == "LONG" else position["max_high"] - position["entry_price"]) / risk,
                "MFE_R": max(0.0, position["max_high"] - position["entry_price"] if d == "LONG" else position["entry_price"] - position["min_low"]) / risk,
                "quantity": position["quantity"]})
            equity += (gross_r - cost_r) * equity * portfolio.risk_fraction
            position, state = None, T2State.FLAT_NO_SETUP

        for i, (_, bar) in enumerate(data.iterrows()):
            regime = self.regime(bar)
            if position is not None:
                old_stop = position["active_stop"]
                hit = bar.Low <= old_stop if position["direction"] == "LONG" else bar.High >= old_stop
                if hit:  # intrabar stop has priority over a close-based strategy exit
                    gap = min(float(bar.Open), old_stop) if position["direction"] == "LONG" else max(float(bar.Open), old_stop)
                    close_trade(i, gap, "INITIAL_STOP" if old_stop == position["initial_stop"] else "ATR_TRAILING_STOP")
                    continue
                ema_loss = bar.Close < bar.EMA50 if position["direction"] == "LONG" else bar.Close > bar.EMA50
                if ema_loss:
                    close_trade(i, float(bar.Close), "EMA50_TREND_LOSS")
                    continue
                position["bars_held"] += 1
                position["min_low"] = min(position["min_low"], float(bar.Low))
                position["max_high"] = max(position["max_high"], float(bar.High))
                # This close-derived stop becomes executable only on the next bar.
                candidate = position["max_high"] - p.trailing_atr * bar.ATR if position["direction"] == "LONG" else position["min_low"] + p.trailing_atr * bar.ATR
                position["active_stop"] = max(old_stop, candidate) if position["direction"] == "LONG" else min(old_stop, candidate)
                continue

            if setup is not None:
                if i > setup.expiry_index or regime != setup.direction:
                    setup, state = None, T2State.FLAT_NO_SETUP
                elif i > setup.pullback_start_index:
                    setup.pullback_extreme = (min(setup.pullback_extreme, float(bar.Low)) if setup.direction == "LONG"
                                              else max(setup.pullback_extreme, float(bar.High)))
                    if self.is_confirmation(bar, data.iloc[i - 1], setup.direction):
                        entry = float(bar.Close)
                        stop = setup.pullback_extreme - p.stop_buffer_atr * bar.ATR if setup.direction == "LONG" else setup.pullback_extreme + p.stop_buffer_atr * bar.ATR
                        risk = entry - stop if setup.direction == "LONG" else stop - entry
                        if risk > 0 and risk <= p.max_initial_stop_atr * bar.ATR:
                            metadata = {"trade_id": f"{symbol}-{len(records)+1:06d}", "strategy_id": self.name,
                                "symbol": symbol, "direction": setup.direction, "pullback_time": setup.pullback_start_time,
                                "confirmation_time": data.index[i], "entry_time": data.index[i], "entry_price": entry,
                                "initial_stop": stop, "initial_risk_points": risk, "initial_risk_ticks": risk / tick_size,
                                "impulse_reference_time": setup.impulse_reference_time,
                                "setup_age_bars": i - setup.pullback_start_index}
                            position = {"direction": setup.direction, "entry_price": entry, "initial_stop": stop,
                                "initial_risk_points": risk, "active_stop": stop, "bars_held": 0,
                                "min_low": entry, "max_high": entry, "quantity": portfolio.size(equity, entry, stop),
                                "metadata": metadata}
                            state = T2State.POSITION_OPEN
                        else:
                            state = T2State.FLAT_NO_SETUP
                        setup = None
                continue

            if regime and i:
                reference = self.impulse_reference(data, i, regime)
                if reference is not None and self.is_pullback(bar, regime):
                    extreme = float(bar.Low if regime == "LONG" else bar.High)
                    setup = PullbackSetup(regime, data.index[i], i, i + p.confirmation_window, extreme, reference)
                    state = T2State.LONG_PULLBACK_ARMED if regime == "LONG" else T2State.SHORT_PULLBACK_ARMED
        return pd.DataFrame(records, columns=["trade_id", "strategy_id", "symbol", "direction", "pullback_time",
            "confirmation_time", "entry_time", "entry_price", "initial_stop", "initial_risk_points",
            "initial_risk_ticks", "exit_time", "exit_price", "exit_reason", "bars_held", "gross_R",
            "cost_R_C1", "net_R_C1", "MAE_R", "MFE_R", "impulse_reference_time", "setup_age_bars", "quantity"])

    def frozen_parameters(self) -> dict:
        return asdict(self.parameters)
