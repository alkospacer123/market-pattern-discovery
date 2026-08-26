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
    """Explicit price-grid configuration; it is never inferred from outcomes."""

    step: str
    touch_tolerance: str = "0"

    def __post_init__(self) -> None:
        from decimal import Decimal
        if Decimal(self.step) <= 0 or Decimal(self.touch_tolerance) < 0:
            raise ValueError("round-level step must be positive and tolerance non-negative")


@dataclass(frozen=True)
class CoreFeatureConfig:
    """The fixed, non-optimized Phase 2A research scales."""

    general_windows: tuple[int, ...] = GENERAL_WINDOWS
    rolling_windows: tuple[int, ...] = ROLLING_WINDOWS

    def __post_init__(self) -> None:
        if self.general_windows != GENERAL_WINDOWS or self.rolling_windows != ROLLING_WINDOWS:
            raise ValueError("Phase 2A window grids are fixed and may not be optimized")
