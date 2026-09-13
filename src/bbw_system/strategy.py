from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum
import math
import pandas as pd

from .config import BBWConfig, InstrumentConfig
from .prices import align_price


class State(StrEnum):
    IDLE = "IDLE"
    COMPRESSION = "COMPRESSION"
    RANGE = "RANGE"
    BREAKOUT = "BREAKOUT"
    RETEST = "RETEST"
    CONFIRMATION = "CONFIRMATION"
    POSITION = "POSITION"
    CLOSED = "CLOSED"
    CANCELLED = "CANCELLED"


class Rejection(StrEnum):
    NO_VALID_RANGE = "NO_VALID_RANGE"
    RANGE_TOO_NARROW = "RANGE_TOO_NARROW"
    RANGE_TOO_WIDE = "RANGE_TOO_WIDE"
    RANGE_NOT_HORIZONTAL = "RANGE_NOT_HORIZONTAL"
    EMA_DIRECTION_FAIL = "EMA_DIRECTION_FAIL"
    BREAKOUT_FAILED = "BREAKOUT_FAILED"
    RETEST_TIMEOUT = "RETEST_TIMEOUT"
    RETEST_TOO_DEEP = "RETEST_TOO_DEEP"
    ENTRY_TOO_EXTENDED = "ENTRY_TOO_EXTENDED"
    CONFIRMATION_TOO_LARGE = "CONFIRMATION_TOO_LARGE"
    STOP_TOO_SMALL = "STOP_TOO_SMALL"
    STOP_TOO_LARGE = "STOP_TOO_LARGE"
    POSITION_SIZE_ZERO = "POSITION_SIZE_ZERO"
    POSITION_ALREADY_OPEN = "POSITION_ALREADY_OPEN"


@dataclass(frozen=True)
class Range:
    high: float
    low: float
    width: float
    bars: int


@dataclass(frozen=True)
class StopResult:
    stop: float
    distance: float
    stop_atr: float
    stop_range_ratio: float
    rejection: Rejection | None

    @property
    def distance_ticks(self) -> float:
        """Deprecated without tick metadata; callers log an exact normalized value."""
        return self.distance


def compression_threshold(bbw: pd.Series, dates: pd.Series, window_days: int = 10,
                          minima: int = 6, decimals: int = 3,
                          include_current_day_history: bool = False) -> pd.DataFrame:
    """Threshold at t uses only rows strictly before t and prior trading dates."""
    records = []
    for i, (timestamp, current) in enumerate(bbw.items()):
        current_date = dates.iloc[i]
        eligible = dates.iloc[:i]
        if not include_current_day_history:
            eligible = eligible[eligible != current_date]
        prior_dates = list(dict.fromkeys(eligible.tolist()))
        selected_dates = prior_dates[-window_days:]
        history = bbw.iloc[:i].iloc[dates.iloc[:i].isin(selected_dates).to_numpy()].dropna()
        lows = sorted(map(float, history), key=float)[:minima]
        threshold = math.ceil((sum(lows) / len(lows)) * 10**decimals) / 10**decimals if len(lows) == minima else math.nan
        records.append({"datetime": timestamp, "bbw_current": current, "threshold": threshold, "minima": tuple(lows), "trading_dates": tuple(selected_dates), "compression": bool(pd.notna(threshold) and current < threshold), "current_trading_date": current_date})
    return pd.DataFrame(records).set_index("datetime")


def construct_range(bars: pd.DataFrame) -> Range:
    return Range(float(bars.high.max()), float(bars.low.min()), float(bars.high.max() - bars.low.min()), len(bars))


def detect_range(bars: pd.DataFrame, compression_position: int, config: BBWConfig,
                 decision_position: int | None = None) -> Range:
    """Select a range deterministically using rows observable at the decision.

    The longest eligible window wins; ties are therefore independent of any
    later breakout. ``rolling_after_compression`` is called at each timestamp
    and can only use the prefix through that timestamp.
    """
    decision_position = len(bars) - 1 if decision_position is None else decision_position
    if not 0 <= compression_position <= decision_position < len(bars):
        raise ValueError("positions must identify an observable prefix")
    observable = bars.iloc[:decision_position + 1]
    if config.range_anchor_mode == "end_at_compression":
        available = bars.iloc[:compression_position + 1]
    elif config.range_anchor_mode == "start_at_compression":
        available = observable.iloc[compression_position:]
    elif config.range_anchor_mode == "rolling_after_compression":
        available = observable.iloc[max(compression_position, len(observable) - config.range_max_bars):]
    else:
        raise ValueError("unknown range_anchor_mode")
    available = available.iloc[:config.range_max_bars] if config.range_anchor_mode != "end_at_compression" else available.iloc[-config.range_max_bars:]
    if len(available) < config.range_min_bars:
        raise ValueError(Rejection.NO_VALID_RANGE.value)
    return construct_range(available)


def range_rejection(value: Range, atr_value: float, price: float, config: BBWConfig, instrument: InstrumentConfig) -> Rejection | None:
    if value.bars < config.range_min_bars:
        return Rejection.NO_VALID_RANGE
    if value.width < config.range_atr_min * atr_value:
        return Rejection.RANGE_TOO_NARROW
    if value.width > config.range_atr_max * atr_value or value.width / price > instrument.max_width_pct:
        return Rejection.RANGE_TOO_WIDE
    return None


def horizontality(boundary: pd.Series, atr_value: float, max_atr: float) -> tuple[bool, dict[str, float]]:
    change = float(boundary.max() - boundary.min())
    limit = float(max_atr * atr_value)
    return change <= limit, {"boundary_change": change, "limit": limit, "atr": float(atr_value)}


def breakout(bar: pd.Series, value: Range) -> str | None:
    return "LONG" if bar.close > value.high else "SHORT" if bar.close < value.low else None


def trend_ok(direction: str, close: float, ema_now: float, ema_back: float, minimum: float) -> bool:
    slope = ema_now / ema_back - 1
    return (direction == "LONG" and slope > minimum and close > ema_now) or (direction == "SHORT" and slope < -minimum and close < ema_now)


def evaluate_retest(bar: pd.Series, direction: str, level: float, range_width: float, tick_size: float, config: BBWConfig) -> tuple[bool, Rejection | None, float]:
    penetration = max(0.0, level - float(bar.low)) if direction == "LONG" else max(0.0, float(bar.high) - level)
    # Both independent limits must pass. A zero tick allowance means no
    # penetration; it does not disable the tick constraint.
    maximum = min(config.penetration_ticks * tick_size, config.penetration_range_pct * range_width)
    touched = bool(bar.low <= level) if direction == "LONG" else bool(bar.high >= level)
    if penetration - maximum > max(1e-12, tick_size * 1e-9):
        return False, Rejection.RETEST_TOO_DEEP, penetration
    return touched, None, penetration


def confirmation(bar: pd.Series, direction: str, level: float) -> bool:
    return bool(bar.close > level) if direction == "LONG" else bool(bar.close < level)


def entry_rejection(entry: float, level: float, atr_value: float, range_width: float, confirmation_bar: pd.Series, config: BBWConfig) -> Rejection | None:
    extension = abs(entry - level)
    if extension > config.max_entry_extension_atr * atr_value or extension > config.max_entry_extension_range_pct * range_width:
        return Rejection.ENTRY_TOO_EXTENDED
    candle_range, body = confirmation_bar.high - confirmation_bar.low, abs(confirmation_bar.close - confirmation_bar.open)
    if candle_range > config.max_confirmation_candle_atr * atr_value or (config.max_confirmation_body_atr is not None and body > config.max_confirmation_body_atr * atr_value):
        return Rejection.CONFIRMATION_TOO_LARGE
    return None


def structural_stop(direction: str, entry: float, value: Range, atr_value: float, config: BBWConfig, instrument: InstrumentConfig) -> StopResult:
    offset = config.stop_offset_price + config.stop_offset_ticks * instrument.tick_size
    raw_stop = value.low - offset if direction == "LONG" else value.high + offset
    stop = align_price(raw_stop, instrument.tick_size, "down" if direction == "LONG" else "up")
    distance = abs(entry - stop)
    stop_atr, ratio = distance / atr_value, distance / value.width
    rejection = Rejection.STOP_TOO_SMALL if stop_atr < config.min_stop_atr or ratio < config.min_stop_range_ratio else Rejection.STOP_TOO_LARGE if stop_atr > config.max_stop_atr or ratio > config.max_stop_range_ratio else None
    return StopResult(stop, distance, stop_atr, ratio, rejection)


def position_size(equity: float, stop_distance: float, instrument: InstrumentConfig, config: BBWConfig) -> int:
    # tick_value is explicitly per contract. ``lot``/``point_value`` survive
    # only as input compatibility metadata and are never multiplied here.
    stop_money = stop_distance / instrument.tick_size * instrument.tick_value_per_contract
    by_risk = math.floor(equity * config.risk_pct / stop_money) if stop_money > 0 else 0
    by_margin = math.floor(equity * config.max_margin_pct / instrument.go_per_contract) if instrument.go_per_contract > 0 else 0
    return min(by_risk, by_margin)


def retest_bar_allowed(bars_after_breakout: int, config: BBWConfig) -> bool:
    """A touch is eligible on ordinal ``retest_min_bars`` after breakout.

    Thus baseline value 5 means bars 1--4 cannot retest and bar 5 can. It does
    not mean setup age or touch duration. The maximum is inclusive too.
    """
    return config.retest_min_bars <= bars_after_breakout <= config.retest_max_bars


ALLOWED_TRANSITIONS = {
    State.IDLE: {State.COMPRESSION}, State.COMPRESSION: {State.RANGE, State.CANCELLED},
    State.RANGE: {State.BREAKOUT, State.CANCELLED}, State.BREAKOUT: {State.RETEST, State.CANCELLED},
    State.RETEST: {State.CONFIRMATION, State.CANCELLED}, State.CONFIRMATION: {State.POSITION, State.CANCELLED},
    State.POSITION: {State.CLOSED}, State.CLOSED: {State.IDLE}, State.CANCELLED: {State.IDLE},
}


@dataclass
class StateMachine:
    setup_id: str
    state: State = State.IDLE

    def transition(self, new: State) -> None:
        if new not in ALLOWED_TRANSITIONS[self.state]:
            raise ValueError(f"Invalid transition {self.state}->{new}")
        self.state = new
