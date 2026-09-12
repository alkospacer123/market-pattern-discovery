"""T1 — BBW expansion plus Donchian breakout, frozen baseline v1.0."""
from __future__ import annotations

from dataclasses import dataclass
import pandas as pd

from ...core.indicators import atr, bollinger_bandwidth, ema, rolling_percentile_rank
from ...core.strategy import Direction, Strategy


@dataclass(frozen=True)
class T1Parameters:
    bb_period: int = 20
    bb_std: float = 2.0
    bbw_percentile_window: int = 100
    bbw_compression_percentile: float = 30.0
    atr_period: int = 14
    atr_expansion_window: int = 20
    donchian_period: int = 20
    ema_period: int = 50
    stop_atr: float = 2.0
    trail_atr: float = 3.0


class T1BBWDonchian(Strategy):
    """Single-timeframe, close-confirmed volatility expansion strategy."""

    name = "T1_BBW_Donchian_v1.0"

    def __init__(self, parameters: T1Parameters | None = None) -> None:
        self.parameters = parameters or T1Parameters()

    def calculate_indicators(self, h1: pd.DataFrame,
                             _h4: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame]:
        p = self.parameters
        bars = h1.copy()
        bars["BBW"] = bollinger_bandwidth(bars["Close"], p.bb_period, p.bb_std)
        bars["BBWPrevious"] = bars["BBW"].shift(1)
        bars["BBWPercentile"] = rolling_percentile_rank(bars["BBW"], p.bbw_percentile_window)
        bars["BBWMean20"] = bars["BBW"].rolling(p.atr_expansion_window).mean()
        bars["ATR"] = atr(bars, p.atr_period)
        bars["ATRMean20"] = bars["ATR"].rolling(p.atr_expansion_window).mean()
        bars["PriorHigh"] = bars["High"].rolling(p.donchian_period).max().shift(1)
        bars["PriorLow"] = bars["Low"].rolling(p.donchian_period).min().shift(1)
        bars["EMA50"] = ema(bars["Close"], p.ema_period)
        # Returning the same close-labelled frame lets the existing causal
        # alignment engine expose the signal candle only at its H1 close.
        return bars, bars

    def regime(self, bar: pd.Series) -> Direction | None:
        required = ["BBW", "BBWPercentile", "BBWMean20", "ATR", "ATRMean20"]
        if bar[required].isna().any():
            return None
        if (bar["BBWPercentile"] <= self.parameters.bbw_compression_percentile
                and bar["BBW"] > bar["BBWPrevious"]
                and bar["BBW"] > bar["BBWMean20"]
                and bar["ATR"] > bar["ATRMean20"]):
            return "LONG"  # expansion is direction-neutral; entry chooses direction
        return None

    def generate_signal(self, bar: pd.Series, regime: Direction | None) -> Direction | None:
        if regime is None:
            return None
        if bar["Close"] > bar["PriorHigh"] and bar["Close"] > bar["EMA50"]:
            return "LONG"
        if bar["Close"] < bar["PriorLow"] and bar["Close"] < bar["EMA50"]:
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
