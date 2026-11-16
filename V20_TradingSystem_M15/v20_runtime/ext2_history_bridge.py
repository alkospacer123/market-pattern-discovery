"""R070 staging: pinned R060 M15 seed + independently observed FINAM M15.

Pure offline/readonly input verification for EXT2, never an order or a LIVE hook.
Broker M15 GET currently has 30-day depth, too short to recreate R060's
historical Wilder daily ATR without a separately verified continuous seed.
Only matching OHLCV overlap permits joining old and recent candles; gaps,
non-final signal bars or incomplete prior sessions block new entries.
"""
from __future__ import annotations

from datetime import datetime, timedelta
from decimal import Decimal
from hashlib import sha256
from pathlib import Path
from typing import Any
import pandas as pd

from .ext2_r060 import REQUIRED, r060_features, EXT2DataInvalid

R060_SEED_SHA256 = {
    "CNYRUBF": "259298733d1528c0d917b100118896009519a9f08bdad33d4b373d9ce86f99b4",
    "GLDRUBF": "7381d672485b5687ca2c4d92aa5960c24bb132f527589bae3c622b2dfa20a83d",
    "IMOEXF": "a1b9fa6102a955103d61b28e81533ed19de68117e30fd84ceb53e8e617559773",
    "USDRUBF": "fef80630080a4e2a5e968d620b663f51acd1b7ab9d5d326a42c68cf2b80c67b8",
}


class EXT2HistoryBlocked(RuntimeError):
    """Input must not authorize an EXT2 entry until cause is resolved."""


def load_r060_pinned_csv(path: str | Path, *, symbol: str) -> pd.DataFrame:
    """Pin original research bytes before reading; not a LIVE data source."""
    if symbol not in R060_SEED_SHA256:
        raise EXT2HistoryBlocked("EXT2_SEED_SYMBOL_UNAPPROVED")
    source = Path(path)
    if not source.is_file() or source.is_symlink():
        raise EXT2HistoryBlocked("EXT2_SEED_MISSING")
    data = source.read_bytes()
    if sha256(data).hexdigest() != R060_SEED_SHA256[symbol]:
        raise EXT2HistoryBlocked("EXT2_SEED_SHA_MISMATCH")
    import io
    frame = pd.read_csv(io.BytesIO(data), sep=";", parse_dates=["Datetime"])
    if "Ticker" not in frame or not frame.Ticker.eq(symbol).all():
        raise EXT2HistoryBlocked("EXT2_SEED_SYMBOL_MISMATCH")
    return _strict_m15(frame)


def _strict_m15(bars: pd.DataFrame) -> pd.DataFrame:
    if not isinstance(bars, pd.DataFrame) or bars.empty or any(
            col not in bars for col in REQUIRED):
        raise EXT2HistoryBlocked("EXT2_HISTORY_M15_SCHEMA")
    d = bars[list(REQUIRED)].copy().reset_index(drop=True)
    try:
        t = pd.to_datetime(d.Datetime, errors="raise")
        if (t.dt.tz is not None or t.isna().any()
                or not t.is_monotonic_increasing or t.duplicated().any()
                or (t.dt.minute % 15).any() or t.dt.second.any()
                or t.dt.microsecond.any() or t.dt.nanosecond.any()):
            raise EXT2HistoryBlocked("EXT2_HISTORY_M15_TIME")
        d["Datetime"] = t
        for col in REQUIRED[1:]:
            vals = pd.to_numeric(d[col], errors="raise")
            if vals.isna().any() or not vals.map(lambda x: Decimal(str(x)).is_finite()).all():
                raise EXT2HistoryBlocked("EXT2_HISTORY_M15_NONFINITE")
            d[col] = vals
        if ((d[["Open", "High", "Low", "Close"]] <= 0).any().any()
                or (d.Volume < 0).any()
                or (d.High < d[["Open", "Low", "Close"]].max(axis=1)).any()
                or (d.Low > d[["Open", "High", "Close"]].min(axis=1)).any()):
            raise EXT2HistoryBlocked("EXT2_HISTORY_M15_OHLCV")
    except (ValueError, TypeError, ArithmeticError, OverflowError) as exc:
        raise EXT2HistoryBlocked("EXT2_HISTORY_M15_INVALID") from exc
    return d


def stitch_verified_m15(*, seed: pd.DataFrame, finam_recent: pd.DataFrame,
                        signal_open_msk: datetime, observed_at_msk: datetime
                        ) -> pd.DataFrame:
    """Join only exact overlapping completed M15, no gaps between sources.

    UTC/market completion must be attested by the caller; this function also
    checks observed time. Never infer missing bars, pull future bars from
    today's unfinished session or silently accept unrelated data histories.
    """
    if (not isinstance(signal_open_msk, datetime)
            or not isinstance(observed_at_msk, datetime)
            or signal_open_msk.tzinfo is not None
            or observed_at_msk.tzinfo is not None
            or observed_at_msk < signal_open_msk + timedelta(minutes=15)):
        raise EXT2HistoryBlocked("EXT2_SIGNAL_NOT_COMPLETED")
    old, new = _strict_m15(seed), _strict_m15(finam_recent)
    if (old.Datetime.iloc[-1] > signal_open_msk
            or new.Datetime.iloc[-1] != signal_open_msk):
        raise EXT2HistoryBlocked("EXT2_HISTORY_FUTURE_OR_SIGNAL_MISSING")
    old = old.set_index("Datetime")
    new = new.set_index("Datetime")
    overlap = old.index.intersection(new.index)
    if len(overlap) < 1:
        raise EXT2HistoryBlocked("EXT2_SEED_FINAM_OVERLAP_MISSING")
    for ts in overlap:
        for col in REQUIRED[1:]:
            if Decimal(str(old.loc[ts, col])) != Decimal(str(new.loc[ts, col])):
                raise EXT2HistoryBlocked("EXT2_SEED_FINAM_OHLCV_DISAGREEMENT")
    # Old prefix up to first recent candle, then exact recent FINAM facts.
    stitched = pd.concat([old.loc[old.index < new.index[0]], new]).reset_index()
    if stitched.Datetime.iloc[-1] != pd.Timestamp(signal_open_msk):
        raise EXT2HistoryBlocked("EXT2_SIGNAL_BAR_MISSING")
    _require_complete_previous_day(stitched, signal_open_msk)
    try:
        feats = r060_features(stitched)
    except (EXT2DataInvalid, ValueError, TypeError, ArithmeticError) as exc:
        raise EXT2HistoryBlocked("EXT2_RECONSTRUCTED_DATR_INVALID") from exc
    if pd.isna(feats.prior_datr14.iloc[-1]) or feats.prior_datr14.iloc[-1] <= 0:
        raise EXT2HistoryBlocked("EXT2_RECONSTRUCTED_DATR_UNAVAILABLE")
    return stitched


def _require_complete_previous_day(bars: pd.DataFrame, signal_open: datetime) -> None:
    """Use R060's session validity; reject deficient recent-session evidence.

    Historical R060 can contain incomplete sessions in ATR; no historical
    bars are altered. For LIVE admission, the latest previous session must
    be proven complete to R060's eligible_daily definition.
    """
    d = bars
    ts = d.Datetime
    day = (ts - pd.Timedelta(hours=9)).dt.normalize()
    minute = ts.dt.hour * 60 + ts.dt.minute
    main = d.loc[minute.between(600, 1065)].copy()
    main["session_day"] = day.loc[main.index]
    by_day = main.groupby("session_day", sort=True).agg(
        n=("Close", "size"),
        first=("Datetime", "min"),
        last=("Datetime", "max"),
    )
    signal_day = pd.Timestamp(signal_open - timedelta(hours=9)).normalize()
    previous = by_day[by_day.index < signal_day].tail(1)
    if previous.empty:
        raise EXT2HistoryBlocked("EXT2_PREVIOUS_D_SESSION_MISSING")
    record = previous.iloc[0]
    first = pd.Timestamp(record["first"])
    last = pd.Timestamp(record["last"])
    if not (record["n"] >= 12
            and first.hour == 10 and first.minute == 0
            and (last.hour * 60 + last.minute) >= 1035):
        raise EXT2HistoryBlocked("EXT2_PREVIOUS_D_SESSION_INCOMPLETE")
