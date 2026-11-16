"""R070 OFFLINE candidate entry boundary: frozen M15 signal -> checked EXT2.

No FINAM commands, positions, risk or SQLite. The historical prefix must be
built by the separately tested SHA/calendar/overlap bridge. This gate also
compares its latest M15 bars against independently read live FINAM M15 to
prevent a stale or unrelated data source from authorizing an entry.
"""
from __future__ import annotations

from datetime import datetime, timedelta
from decimal import Decimal, InvalidOperation
import pandas as pd

from .ext2_r060 import (
    APPLIES_TO, SYMBOLS, FULL_N4, EXT2Decision, ext2_signal_gate,
)
from .frozen_adapter import validate_completed_history
from .offline_planner import FrozenSignal


def evaluate_r070_candidate_ext2(
    *, robot: str, symbol: str, frozen_signal: FrozenSignal,
    finam_completed: pd.DataFrame, verified_full_history: pd.DataFrame | None,
) -> EXT2Decision:
    """A failed proof blocks ONLY a new EXT2 entry, never an open position.

    finam_completed is the existing frozen-signal M15 observation.
    verified_full_history must be previously stitched and calendar-checked.
    The last 4 completed FINAM bars MUST match the long-run history exactly,
    including volume, even when historical source comes from terminal CSV.
    """
    if robot not in {"v20-shallow", "v20-obv", "v20-inside"} or symbol not in FULL_N4:
        return EXT2Decision(True, False, "EXT2_CANDIDATE_IDENTITY_INVALID")
    if (not isinstance(frozen_signal, FrozenSignal)
            or frozen_signal.symbol != symbol
            or frozen_signal.side not in (-1, 1)
            or not isinstance(frozen_signal.signal_bar_open, datetime)
            or frozen_signal.signal_bar_open.tzinfo is not None):
        return EXT2Decision(True, False, "EXT2_FROZEN_SIGNAL_INVALID")
    if robot not in APPLIES_TO or symbol not in SYMBOLS:
        return EXT2Decision(False, True, "EXT2_NOT_APPLICABLE")
    if verified_full_history is None:
        return EXT2Decision(True, False, "EXT2_CERTIFIED_HISTORY_MISSING")
    try:
        signal_open = frozen_signal.signal_bar_open
        observed = signal_open + timedelta(minutes=15)
        recent = validate_completed_history(symbol, finam_completed, observed_at=observed)
        full = validate_completed_history(symbol, verified_full_history, observed_at=observed)
        if (len(recent) < 4 or len(full) < 4
                or recent.Datetime.iloc[-1] != pd.Timestamp(signal_open)
                or full.Datetime.iloc[-1] != pd.Timestamp(signal_open)):
            return EXT2Decision(True, False, "EXT2_RECENT_COMPLETED_M15_MISSING")
        window = recent.tail(4).reset_index(drop=True)
        subset = full.loc[full.Datetime.isin(window.Datetime)].reset_index(drop=True)
        if (len(subset) != 4
                or not subset.Datetime.equals(window.Datetime)):
            return EXT2Decision(True, False, "EXT2_HISTORY_FINAM_TIMESTAMPS_MISMATCH")
        for col in ("Open", "High", "Low", "Close", "Volume"):
            if any(Decimal(str(a)) != Decimal(str(b))
                   for a, b in zip(subset[col], window[col])):
                return EXT2Decision(True, False, "EXT2_HISTORY_FINAM_OHLCV_MISMATCH")
        return ext2_signal_gate(
            robot=robot, symbol=symbol, side=frozen_signal.side,
            signal_open_msk=signal_open, completed_bars=full)
    except (ValueError, TypeError, ArithmeticError, InvalidOperation, KeyError):
        return EXT2Decision(True, False, "EXT2_CANDIDATE_INPUT_UNVERIFIED")
