"""R070 staging: pinned R060 M15 seed + independently observed FINAM M15.

Pure offline/readonly input verification for EXT2, never an order or a LIVE hook.
Broker M15 GET currently has 30-day depth, too short to recreate R060's
historical Wilder daily ATR without a separately verified continuous seed.
Only matching OHLCV overlap permits joining old and recent candles; gaps,
non-final signal bars or incomplete prior sessions block new entries.
"""
from __future__ import annotations

from datetime import datetime, timedelta, date
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


def load_finam_terminal_csv(path: str | Path, *, expected_sha256: str) -> pd.DataFrame:
    """Read pinned FINAM terminal <DATE>/<TIME> M15 CSV as Moscow-local time.

    OFFLINE input only. The terminal's timestamps ALREADY match R060 MSK;
    do not localize/shift them. The caller must pin the exact source bytes,
    not just trust an arbitrary local file or a user-supplied 'complete' label.
    """
    import io
    if not isinstance(expected_sha256, str) or len(expected_sha256) != 64:
        raise EXT2HistoryBlocked("EXT2_FINAM_SOURCE_SHA_REQUIRED")
    source = Path(path)
    if not source.is_file() or source.is_symlink():
        raise EXT2HistoryBlocked("EXT2_FINAM_SOURCE_MISSING")
    raw = source.read_bytes()
    if sha256(raw).hexdigest() != expected_sha256.lower():
        raise EXT2HistoryBlocked("EXT2_FINAM_SOURCE_SHA_MISMATCH")
    try:
        frame = pd.read_csv(io.BytesIO(raw), sep=";", dtype=str,
                            encoding="utf-8-sig")
        columns = ["<DATE>", "<TIME>", "<OPEN>", "<HIGH>",
                   "<LOW>", "<CLOSE>", "<VOL>"]
        if list(frame.columns) != columns or frame.empty:
            raise ValueError("M15_EXPORT_SCHEMA")
        d = pd.DataFrame()
        d["Datetime"] = pd.to_datetime(
            frame["<DATE>"] + frame["<TIME>"].str.zfill(6),
            format="%Y%m%d%H%M%S", errors="raise")
        for col, raw_name in [
            ("Open", "<OPEN>"), ("High", "<HIGH>"), ("Low", "<LOW>"),
            ("Close", "<CLOSE>"), ("Volume", "<VOL>")
        ]:
            d[col] = pd.to_numeric(frame[raw_name], errors="raise")
        return _strict_m15(d)
    except (ValueError, TypeError, ArithmeticError, UnicodeError) as exc:
        raise EXT2HistoryBlocked("EXT2_FINAM_SOURCE_INVALID") from exc


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
                        signal_open_msk: datetime, observed_at_msk: datetime,
                        verified_open_days: tuple[date, ...] | None = None,
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
    _require_continuous_trading_sessions(
        stitched, from_msk=new.index[0].to_pydatetime(),
        signal_open_msk=signal_open_msk,
        verified_open_days=verified_open_days,
    )
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

def _require_continuous_trading_sessions(
    bars: pd.DataFrame, *, from_msk: datetime, signal_open_msk: datetime,
    verified_open_days: tuple[date, ...] | None,
) -> None:
    """Validate ALL recent normal-session M15 against an independently proved calendar.

    R060 daily calculation is unchanged, but a short/incomplete LIVE history
    must fail closed. No inferred weekdays: exchange holidays and special
    sessions require broker/MOEX calendar authority supplied by the caller.
    A nonstandard shortened session remains blocked until separately proved.
    This function never retrieves or trusts a calendar by itself.
    """
    if (not isinstance(verified_open_days, tuple)
            or not verified_open_days
            or any(type(day) is not date for day in verified_open_days)
            or tuple(sorted(set(verified_open_days))) != verified_open_days):
        raise EXT2HistoryBlocked("EXT2_VERIFIED_SESSION_CALENDAR_REQUIRED")
    begin = from_msk.date()
    final = signal_open_msk.date()
    relevant = tuple(day for day in verified_open_days if begin <= day <= final)
    if not relevant or relevant[-1] != final:
        raise EXT2HistoryBlocked("EXT2_SIGNAL_SESSION_NOT_PROVEN")
    minutes = bars.Datetime.dt.hour * 60 + bars.Datetime.dt.minute
    regular = bars.loc[minutes.between(600, 1065), "Datetime"]
    day_to_bars = {d: pd.DatetimeIndex(x) for d, x in
                   regular.groupby(regular.dt.date, sort=True)}
    unexpected = set(day_to_bars).intersection(
        {begin + timedelta(days=i) for i in range((final - begin).days + 1)}
    ) - set(relevant)
    if unexpected:
        raise EXT2HistoryBlocked("EXT2_M15_ON_UNPROVEN_SESSION")
    for day in relevant:
        end = (pd.Timestamp(signal_open_msk) if day == final else
               pd.Timestamp(datetime.combine(day, datetime.min.time())) +
               timedelta(hours=17, minutes=45))
        start = pd.Timestamp(datetime.combine(day, datetime.min.time())) + timedelta(hours=10)
        if end < start or end > start + timedelta(hours=7, minutes=45):
            raise EXT2HistoryBlocked("EXT2_SIGNAL_OUTSIDE_SESSION")
        expected = pd.date_range(start, end, freq="15min")
        present = day_to_bars.get(day, pd.DatetimeIndex([]))
        if not present.equals(expected):
            raise EXT2HistoryBlocked("EXT2_RECENT_SESSION_M15_MISSING")


def canonical_m15_csv_bytes(bars: pd.DataFrame) -> bytes:
    """Stable, lossless numeric CSV for candidate history checkpoints."""
    normalized = _strict_m15(bars)
    return normalized.to_csv(
        index=False, date_format="%Y-%m-%dT%H:%M:%S",
        float_format="%.17g", lineterminator="\n",
    ).encode("utf-8")


def m15_history_sha256(bars: pd.DataFrame) -> str:
    """Detect altered M15 OHLCV; source authenticity is proved separately."""
    return sha256(canonical_m15_csv_bytes(bars)).hexdigest()


def advance_verified_m15(
    *, verified_prefix: pd.DataFrame, prefix_sha256: str,
    finam_recent: pd.DataFrame, signal_open_msk: datetime,
    observed_at_msk: datetime, verified_open_days: tuple[date, ...],
) -> tuple[pd.DataFrame, str]:
    """Advance a previously checked source using ONLY overlapping FINAM GET M15.

    Keep the entire historical DATR warmup; request only a short recent M15
    window from FINAM on updates. Missing overlap, changed history, missing
    calendar, unclosed candles or a repeated/out-of-order signal all block.
    No writes or API calls. The caller persists the returned *new* digest
    together with the new frame only after the pair is independently checked.
    """
    if (not isinstance(prefix_sha256, str)
            or len(prefix_sha256) != 64
            or m15_history_sha256(verified_prefix) != prefix_sha256.lower()):
        raise EXT2HistoryBlocked("EXT2_VERIFIED_PREFIX_SHA_MISMATCH")
    before = _strict_m15(verified_prefix)
    if (not isinstance(signal_open_msk, datetime)
            or signal_open_msk.tzinfo is not None
            or signal_open_msk <= before.Datetime.iloc[-1].to_pydatetime()):
        raise EXT2HistoryBlocked("EXT2_PREFIX_NOT_ADVANCING")
    stitched = stitch_verified_m15(
        seed=before, finam_recent=finam_recent,
        signal_open_msk=signal_open_msk,
        observed_at_msk=observed_at_msk,
        verified_open_days=verified_open_days,
    )
    if (len(stitched) <= len(before)
            or not stitched.iloc[:len(before)][list(REQUIRED)].reset_index(drop=True).equals(
                before[list(REQUIRED)].reset_index(drop=True))):
        raise EXT2HistoryBlocked("EXT2_VERIFIED_PREFIX_CHANGED")
    return stitched, m15_history_sha256(stitched)
