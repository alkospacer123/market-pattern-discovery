"""T3 — Multi-Timeframe Trend H4 -> H1, frozen baseline v1.0."""
from __future__ import annotations

from dataclasses import dataclass
import pandas as pd

from ...core.indicators import adx, atr, ema, ema_slope
from ...core.strategy import Direction, Strategy


@dataclass(frozen=True)
class T3Parameters:
    ema_period: int = 100
    slope_lookback: int = 5
    adx_period: int = 14
    adx_threshold: float = 20.0
    atr_period: int = 14
    atr_average_period: int = 20
    breakout_period: int = 20
    stop_atr: float = 2.0
    trail_atr: float = 3.0


class T3MTFTrend(Strategy):
    name = "T3_MTF_Trend_v1.0"

    def __init__(self, parameters: T3Parameters | None = None) -> None:
        self.parameters = parameters or T3Parameters()

    def calculate_indicators(self, h1: pd.DataFrame, h4: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame]:
        p = self.parameters
        low, high = h1.copy(), h4.copy()
        low["ATR"] = atr(low, p.atr_period)
        # shift(1) is essential: today's close is compared only with highs/lows
        # which were already known before the signal candle began.
        low["PriorHigh"] = low["High"].rolling(p.breakout_period).max().shift(1)
        low["PriorLow"] = low["Low"].rolling(p.breakout_period).min().shift(1)
        high["EMA100"] = ema(high["Close"], p.ema_period)
        high["EMA50"] = ema(high["Close"], 50)
        high["EMA200"] = ema(high["Close"], 200)
        high["EMA100Slope"] = ema_slope(high["EMA100"], p.slope_lookback)
        high["ADX"] = adx(high, p.adx_period)
        high["ATR"] = atr(high, p.atr_period)
        high["ATRMean20"] = high["ATR"].rolling(p.atr_average_period).mean()
        return low, high

    def regime(self, bar: pd.Series) -> Direction | None:
        needed = ["Close", "EMA100", "EMA100Slope", "ADX", "ATR", "ATRMean20"]
        if bar[needed].isna().any() or bar["ADX"] <= self.parameters.adx_threshold or bar["ATR"] <= bar["ATRMean20"]:
            return None
        if bar["Close"] > bar["EMA100"] and bar["EMA100Slope"] > 0:
            return "LONG"
        if bar["Close"] < bar["EMA100"] and bar["EMA100Slope"] < 0:
            return "SHORT"
        return None

    def generate_signal(self, bar: pd.Series, regime: Direction | None) -> Direction | None:
        if regime == "LONG" and pd.notna(bar["PriorHigh"]) and bar["Close"] > bar["PriorHigh"]:
            return "LONG"
        if regime == "SHORT" and pd.notna(bar["PriorLow"]) and bar["Close"] < bar["PriorLow"]:
            return "SHORT"
        return None

    def calculate_stop_loss(self, direction: Direction, entry: float, atr_value: float) -> float:
        distance = self.parameters.stop_atr * atr_value
        return entry - distance if direction == "LONG" else entry + distance

    def calculate_take_profit(self, direction: Direction, entry: float, atr_value: float) -> None:
        return None

    def manage_position(self, direction: Direction, extreme: float, atr_value: float) -> float:
        distance = self.parameters.trail_atr * atr_value
        return extreme - distance if direction == "LONG" else extreme + distance

    def exit_signal(self, direction: Direction, bar: pd.Series, stop: float) -> bool:
        return bar["Low"] <= stop if direction == "LONG" else bar["High"] >= stop
