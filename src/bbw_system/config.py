from __future__ import annotations

from dataclasses import dataclass, field
import json
from pathlib import Path
from typing import Any


@dataclass(frozen=True)
class SessionConfig:
    timezone: str = "UTC"
    session_start: str = "00:00"
    session_end: str = "23:59"
    session_anchor: str = "00:00"
    excluded_weekdays: tuple[int, ...] = (5, 6)
    excluded_intervals: tuple[tuple[str, str], ...] = ()
    excluded_dates: tuple[str, ...] = ()
    session_end_overrides: tuple[tuple[str, str], ...] = ()


@dataclass(frozen=True)
class InstrumentConfig:
    symbol: str
    tick_size: float
    tick_value: float
    lot: float
    go: float
    point_value: float
    max_width_pct: float
    session: SessionConfig = field(default_factory=SessionConfig)

    @property
    def tick_value_per_contract(self) -> float:
        """Cash value of one tick for one contract (``lot`` is legacy metadata)."""
        return self.tick_value

    @property
    def go_per_contract(self) -> float:
        """Initial margin required for one contract."""
        return self.go


@dataclass(frozen=True)
class BBWConfig:
    setup_hours: int = 4
    bbw_period: int = 10
    bbw_deviation: float = 2.0
    threshold_days: int = 10
    threshold_minima: int = 6
    threshold_decimals: int = 3
    threshold_include_current_trading_day_history: bool = False
    setup_bar_completion_policy: str = "strict_source_count"
    range_anchor_mode: str = "end_at_compression"
    ema_period: int = 50
    ema_slope_lag: int = 10
    ema_min_slope_pct: float = 0.001
    atr_period: int = 14
    range_min_bars: int = 6
    range_max_bars: int = 30
    range_atr_min: float = 1.0
    range_atr_max: float = 2.0
    horizontal_max_atr: float = 0.5
    retest_min_bars: int = 5
    retest_max_bars: int = 30
    penetration_ticks: float = 0.0
    penetration_range_pct: float = 0.20
    max_entry_extension_atr: float = 1.0
    max_entry_extension_range_pct: float = 0.5
    max_confirmation_candle_atr: float = 1.5
    max_confirmation_body_atr: float | None = None
    stop_offset_ticks: float = 0.0
    stop_offset_price: float = 0.0
    min_stop_atr: float = 0.0
    max_stop_atr: float = 3.0
    min_stop_range_ratio: float = 0.0
    max_stop_range_ratio: float = 3.0
    risk_pct: float = 0.015
    max_margin_pct: float = 0.75
    commission_per_contract: float = 0.0
    slippage_ticks: float = 0.0
    conservative_policy: str = "STOP_FIRST"
    intrabar_policy: str = "stop_first"
    allow_lower_tf_fallback: bool = False
    partial_levels: tuple[float, ...] = (1.0, 2.0, 3.0)
    partial_fractions: tuple[float, ...] = (0.5, 0.3, 0.2)


def load_config(path: str | Path) -> tuple[BBWConfig, InstrumentConfig]:
    """Load JSON-compatible YAML without adding an opaque parser dependency."""
    raw: dict[str, Any] = json.loads(Path(path).read_text(encoding="utf-8"))
    instrument_raw = dict(raw["instrument"])
    session_raw = dict(instrument_raw.pop("session"))
    for key in ("excluded_weekdays", "excluded_intervals", "excluded_dates", "session_end_overrides"):
        if key in session_raw:
            session_raw[key] = tuple(tuple(v) if isinstance(v, list) else v for v in session_raw[key])
    session = SessionConfig(**session_raw)
    instrument = InstrumentConfig(session=session, **instrument_raw)
    strategy = dict(raw["strategy"])
    for key in ("partial_levels", "partial_fractions"):
        if key in strategy:
            strategy[key] = tuple(strategy[key])
    return BBWConfig(**strategy), instrument
