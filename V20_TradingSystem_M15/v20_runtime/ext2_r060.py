"""Pure, broker-free TRL-R060 EXT2 feature and eligibility calculation.

Staging only. Not wired into LIVE. All inputs are completed Moscow-time
M15 bars; original V20 signal functions, trading/risk/FINAM code untouched.

Reference: R060 ZIP SHA256 80291246ba4692485545f58fd28c7563199bf7be28033fc16eb296efee377e31
           input/run_r059.py and input/input/frozen/sources/research_extended.py
"""
from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
import math

import numpy as np
import pandas as pd

APPLIES_TO = frozenset({"v20-shallow", "v20-obv"})
SYMBOLS = frozenset({"USDRUBF", "CNYRUBF", "GLDRUBF"})
FULL_N4 = frozenset({*SYMBOLS, "IMOEXF"})
REQUIRED = ("Datetime", "Open", "High", "Low", "Close", "Volume")


class EXT2DataInvalid(ValueError):
    """No authorization to enter on unverifiable historical data."""


@dataclass(frozen=True)
class EXT2Decision:
    applicable: bool
    permit: bool
    reason: str
    extension_datr: float | None = None
    opposing_m15: int | None = None


def r060_features(bars: pd.DataFrame) -> pd.DataFrame:
    """Exact R059/R060 previous-session high/low and Wilder DATR14.

    Uses 10:00..17:45 MSK M15 candles to aggregate a D session, with a
    09:00 MSK session-date shift. Daily EWM uses full prior history, not a
    14-day truncation. Three opposing bodies precede the signal M15 bar.
    Output is indexed identically to the input, never changes it.
    """
    if not isinstance(bars, pd.DataFrame) or bars.empty or any(
        x not in bars for x in REQUIRED
    ):
        raise EXT2DataInvalid("EXT2_M15_INPUT_INVALID")
    d = bars.copy()
    stamps = pd.to_datetime(d["Datetime"], errors="raise")
    if (stamps.dt.tz is not None or stamps.isna().any()
            or not stamps.is_monotonic_increasing or stamps.duplicated().any()
            or (stamps.dt.minute % 15).any() or stamps.dt.second.any()
            or stamps.dt.microsecond.any()):
        raise EXT2DataInvalid("EXT2_M15_TIME_INVALID")
    for col in REQUIRED[1:]:
        v = pd.to_numeric(d[col], errors="coerce")
        if (not np.isfinite(v.to_numpy(dtype=float)).all()
                or ((v <= 0).any() if col != "Volume" else (v < 0).any())):
            raise EXT2DataInvalid("EXT2_M15_OHLCV_INVALID")
    if ((d.High < d[["Open", "Close", "Low"]].max(axis=1)).any()
            or (d.Low > d[["Open", "Close", "High"]].min(axis=1)).any()):
        raise EXT2DataInvalid("EXT2_M15_PRICE_INVALID")
    day = (stamps - pd.Timedelta(hours=9)).dt.normalize()
    minute = stamps.dt.hour * 60 + stamps.dt.minute
    session = d.loc[minute.between(600, 1065)]
    ss = session.assign(day=day.loc[session.index]).groupby("day", sort=True).agg(
        hi=("High", "max"), lo=("Low", "min"), sclose=("Close", "last")
    )
    previous_close = ss.sclose.shift(1)
    tr = pd.concat([
        ss.hi - ss.lo,
        (ss.hi - previous_close).abs(),
        (ss.lo - previous_close).abs(),
    ], axis=1).max(axis=1)
    atr = tr.ewm(alpha=1/14, adjust=False, min_periods=14).mean().shift(1)
    body = d.Close - d.Open
    three_rising = sum((body.shift(j) > 0).astype(int) for j in range(1, 4))
    three_falling = sum((body.shift(j) < 0).astype(int) for j in range(1, 4))
    return pd.DataFrame({
        "signal_open": stamps,
        "prior_low": day.map(ss.lo.shift(1)).to_numpy(),
        "prior_high": day.map(ss.hi.shift(1)).to_numpy(),
        "prior_datr14": day.map(atr).to_numpy(),
        "extension_long": (d.Close - day.map(ss.lo.shift(1))).to_numpy() / day.map(atr).to_numpy(),
        "extension_short": (day.map(ss.hi.shift(1)) - d.Close).to_numpy() / day.map(atr).to_numpy(),
        "three_falling": three_falling.to_numpy(),
        "three_rising": three_rising.to_numpy(),
    }, index=d.index)


def ext2_signal_gate(*, robot: str, symbol: str, side: int,
                     signal_open_msk: datetime, completed_bars: pd.DataFrame) -> EXT2Decision:
    """Return a fail-closed entry permission; never sends or creates orders.

    Caller supplies the COMPLETE historical M15 prefix including the signal
    bar and no uncompleted bars. An incomplete DATR warm-up blocks entry.
    """
    if robot not in {"v20-shallow", "v20-obv", "v20-inside"} or symbol not in FULL_N4:
        raise EXT2DataInvalid("EXT2_SCOPE_INVALID")
    if side not in (-1, 1) or not isinstance(signal_open_msk, datetime) or signal_open_msk.tzinfo is not None:
        raise EXT2DataInvalid("EXT2_SIGNAL_INVALID")
    if robot not in APPLIES_TO or symbol not in SYMBOLS:
        return EXT2Decision(False, True, "EXT2_NOT_APPLICABLE")
    if completed_bars is None or "Datetime" not in completed_bars:
        return EXT2Decision(True, False, "EXT2_HISTORY_UNAVAILABLE")
    # Defensive: an as-yet-unclosed candle cannot become an input, even if
    # the caller passed a larger frame. Do not silently accept future data.
    timestamps = pd.to_datetime(completed_bars.Datetime, errors="coerce")
    if timestamps.isna().any() or (timestamps > pd.Timestamp(signal_open_msk)).any():
        return EXT2Decision(True, False, "EXT2_FUTURE_OR_INCOMPLETE_M15")
    try:
        feats = r060_features(completed_bars)
    except (EXT2DataInvalid, ValueError, TypeError, ArithmeticError):
        return EXT2Decision(True, False, "EXT2_HISTORY_INVALID")
    row = feats.iloc[-1]
    if row.signal_open != pd.Timestamp(signal_open_msk):
        return EXT2Decision(True, False, "EXT2_SIGNAL_BAR_MISSING")
    ext = float(row.extension_long if side == 1 else row.extension_short)
    opp = int(row.three_falling if side == 1 else row.three_rising)
    if not (math.isfinite(float(row.prior_datr14)) and float(row.prior_datr14) > 0
            and math.isfinite(ext) and len(completed_bars) >= 4):
        return EXT2Decision(True, False, "EXT2_PRIOR_DAY_ATR_UNVERIFIED")
    if ext >= 2.0 and opp == 0:
        return EXT2Decision(True, False, "EXT2_LATE_NO_OPPOSING_M15", ext, opp)
    return EXT2Decision(True, True, "EXT2_PASS", ext, opp)
