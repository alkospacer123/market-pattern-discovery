"""Stable configuration and schema constants for Feature Builder Core."""
from __future__ import annotations

from dataclasses import dataclass

FEATURE_BUILDER_VERSION = "1.1"
CORE_FEATURE_BUILDER_VERSION = "1.0"
GENERAL_WINDOWS = (1, 3, 5, 10, 20, 30, 60)
ROLLING_WINDOWS = (5, 10, 20, 60)
STRUCTURE_WINDOWS = (5, 10, 20, 60)


@dataclass(frozen=True)
class RoundLevelConfig:
    """Canonical exchange tick and independent research round-level grid."""

    tick_size: str | float
    round_level_step: str | float
    touch_tolerance: str | float = "0"

    def __post_init__(self) -> None:
        from decimal import Decimal
        tick = Decimal(str(self.tick_size))
        step = Decimal(str(self.round_level_step))
        tolerance = Decimal(str(self.touch_tolerance))
        if not all(value.is_finite() for value in (tick, step, tolerance)):
            raise ValueError("round-level configuration values must be finite")
        if tick <= 0 or step <= 0:
            raise ValueError("tick_size and round_level_step must be positive")
        if tolerance < 0:
            raise ValueError("touch_tolerance must be non-negative")
        ticks = step / tick
        if abs(ticks - ticks.to_integral_value()) > Decimal("1e-9"):
            raise ValueError("round_level_step / tick_size must be an integer")

    @property
    def round_level_step_ticks(self) -> int:
        from decimal import Decimal
        return int((Decimal(str(self.round_level_step)) / Decimal(str(self.tick_size))).to_integral_value())


@dataclass(frozen=True)
class CoreFeatureConfig:
    """The fixed, non-optimized Phase 2A research scales."""

    general_windows: tuple[int, ...] = GENERAL_WINDOWS
    rolling_windows: tuple[int, ...] = ROLLING_WINDOWS

    def __post_init__(self) -> None:
        if self.general_windows != GENERAL_WINDOWS or self.rolling_windows != ROLLING_WINDOWS:
            raise ValueError("Phase 2A window grids are fixed and may not be optimized")
