"""Public contracts for the BBW CORE v1 research engine."""
from __future__ import annotations

from dataclasses import dataclass

import pandas as pd


@dataclass(frozen=True)
class CoreExecutionConfig:
    """Execution-only controls; these are not optimization parameters.

    Prices are in instrument price units.  Costs are charged per unit on each
    filled entry/exit and slippage is adverse on every fill.  The default
    maximum holding period is one M15 trading day, preventing residual trades
    from being marked at the end of a multi-year data set.
    """

    max_range_width_atr: float | None = None
    max_range_width_pct: float | None = None
    max_breakout_extension_atr: float = 1.0
    max_breakout_extension_range: float = 0.5
    max_confirmation_range_atr: float = 1.5
    stop_offset: float = 0.0
    target_levels: tuple[float, ...] = (1.0, 2.0, 3.0)
    partial_fractions: tuple[float, ...] = (0.5, 0.3, 0.2)
    breakeven_after_target: int = 1
    lock_r_after_target: int = 2
    lock_r: float = 1.0
    trailing_atr_multiple: float | None = None
    m15_atr_period: int = 14
    max_holding_bars: int = 96
    commission_per_unit: float = 0.0
    slippage: float = 0.0
    same_bar_policy: str = "STOP_FIRST"
    drop_incomplete_trades: bool = True

    def __post_init__(self) -> None:
        for name in ("max_range_width_atr", "max_range_width_pct"):
            if (value := getattr(self, name)) is not None and value <= 0:
                raise ValueError(f"{name} must be positive or None")
        positive = (self.max_breakout_extension_atr, self.max_breakout_extension_range,
                    self.max_confirmation_range_atr, self.m15_atr_period, self.max_holding_bars)
        if any(value <= 0 for value in positive):
            raise ValueError("extension, candle, ATR-period, and holding limits must be positive")
        if self.stop_offset < 0 or self.commission_per_unit < 0 or self.slippage < 0:
            raise ValueError("stop offset, commission, and slippage cannot be negative")
        if self.same_bar_policy != "STOP_FIRST":
            raise ValueError("CORE v1 permits only deterministic STOP_FIRST ties")
        if len(self.target_levels) != len(self.partial_fractions) or not self.target_levels:
            raise ValueError("each target must have one partial fraction")
        if any(level <= 0 for level in self.target_levels) or any(fraction <= 0 for fraction in self.partial_fractions):
            raise ValueError("targets and fractions must be positive")
        if tuple(sorted(self.target_levels)) != self.target_levels:
            raise ValueError("target levels must be increasing")
        if abs(sum(self.partial_fractions) - 1.0) > 1e-12:
            raise ValueError("partial fractions must sum to one")


@dataclass(frozen=True)
class CoreReplayResult:
    """Immutable container of newly-created diagnostics and trade ledgers."""

    ranges: pd.DataFrame
    setups: pd.DataFrame
    trades: pd.DataFrame
    fills: pd.DataFrame
    rejections: pd.DataFrame
