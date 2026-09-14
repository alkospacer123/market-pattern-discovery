"""Deterministic, strategy-free market-data normalization and diagnostics."""
from __future__ import annotations

from dataclasses import dataclass, field
from hashlib import sha256
from pathlib import Path
from typing import Any, Iterable
import json
import re

import numpy as np
import pandas as pd

CANONICAL_COLUMNS = ("timestamp", "open", "high", "low", "close", "volume", "symbol", "timeframe")
OPTIONAL_COLUMNS = ("contract", "open_interest", "source", "trading_date", "roll_flag", "session_id")
REASON_CODES = ("WEEKEND", "OUTSIDE_SESSION", "DUPLICATE", "INVALID_OHLC", "HOLIDAY", "DATA_GAP", "ROLLOVER", "OTHER")
NORMALIZATION_VERSION = "1.0"
FREQUENCIES = {"M1": "1min", "M5": "5min", "M15": "15min", "M30": "30min", "H1": "1h", "D1": "1D"}


def file_sha256(path: str | Path) -> str:
    digest = sha256()
    with Path(path).open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def dataframe_sha256(frame: pd.DataFrame) -> str:
    """Stable hash of canonical CSV bytes (independent of output location)."""
    ordered = frame.sort_values(["timestamp", "symbol", "timeframe"], kind="stable")
    return sha256(ordered.to_csv(index=False, lineterminator="\n").encode("utf-8")).hexdigest()


def infer_identity(path: str | Path) -> tuple[str | None, str | None]:
    name = Path(path).stem.upper()
    symbol = next((s for s in ("CNYRUBF", "IMOEXF", "GLDRUBF", "GOLD", "BR") if re.search(rf"(^|[^A-Z]){s}([^A-Z]|$)", name)), None)
    tf = next((tf for tf in FREQUENCIES if re.search(rf"(^|[^A-Z0-9]){tf}([^A-Z0-9]|$)", name)), None)
    return symbol, tf


def _clock(value: str) -> int:
    h, m = map(int, value.split(":"))
    return h * 60 + m


@dataclass(frozen=True)
class CalendarConfig:
    holiday_dates: tuple[str, ...] = ()
    shortened_session_dates: dict[str, str] = field(default_factory=dict)
    special_session_dates: dict[str, tuple[str, str]] = field(default_factory=dict)


@dataclass(frozen=True)
class NormalizationConfig:
    symbol: str
    timeframe: str
    source_timezone: str | None
    exchange_timezone: str | None
    session_start: str | None
    session_end: str | None
    breaks: tuple[tuple[str, str], ...] = ()
    calendar: CalendarConfig = field(default_factory=CalendarConfig)


def read_source(path: str | Path) -> tuple[pd.DataFrame, dict[str, Any]]:
    """Read generic or Finam CSV without inferring timezone or futures type."""
    path = Path(path)
    sample = path.read_bytes()[:65536]
    encoding = "utf-8-sig"
    try:
        text = sample.decode(encoding)
    except UnicodeDecodeError:
        encoding, text = "cp1251", sample.decode("cp1251")
    delimiter = max((",", ";", "\t"), key=lambda item: text.splitlines()[0].count(item))
    raw = pd.read_csv(path, sep=delimiter, encoding=encoding)
    columns = {str(c).strip().lower().strip("<>"): c for c in raw.columns}
    finam = "date" in columns and "time" in columns
    if finam:
        timestamp = raw[columns["date"]].astype(str).str.strip() + " " + raw[columns["time"]].astype(str).str.zfill(6)
        raw["timestamp"] = pd.to_datetime(timestamp, format="%Y%m%d %H%M%S", errors="coerce")
    else:
        candidate = next((columns[k] for k in ("timestamp", "datetime", "date_time", "date") if k in columns), None)
        if candidate is None:
            raise ValueError("No timestamp column")
        raw["timestamp"] = pd.to_datetime(raw[candidate], errors="coerce")
    rename = {columns[k]: k for k in ("open", "high", "low", "close", "volume", "contract", "open_interest", "roll_flag") if k in columns}
    # Finam's canonical field is <VOL>; expose it as canonical ``volume``.
    if "volume" not in columns and "vol" in columns:
        rename[columns["vol"]] = "volume"
    raw = raw.rename(columns=rename)
    return raw, {"format": "finam_csv" if finam else "csv", "delimiter": delimiter, "encoding": encoding}


def normalize(raw: pd.DataFrame, config: NormalizationConfig) -> tuple[pd.DataFrame, dict[str, Any]]:
    """Classify every input row; only explicitly configured timezone/session is used."""
    if not config.source_timezone or not config.exchange_timezone:
        raise ValueError("source_timezone and exchange_timezone must be explicit")
    missing = set(("timestamp", "open", "high", "low", "close", "volume")) - set(raw.columns)
    if missing:
        raise ValueError(f"Missing columns: {sorted(missing)}")
    out = raw.copy()
    out["source_timestamp"] = out["timestamp"].astype(str)
    ts = pd.to_datetime(out["timestamp"], errors="coerce")
    if ts.dt.tz is None:
        ts = ts.dt.tz_localize(config.source_timezone, ambiguous="NaT", nonexistent="NaT")
    out["timestamp"] = ts.dt.tz_convert(config.exchange_timezone)
    for col in ("open", "high", "low", "close", "volume"):
        out[col] = pd.to_numeric(out[col], errors="coerce")
    out["symbol"], out["timeframe"] = config.symbol, config.timeframe
    out["status"], out["reason_code"] = "VALID", pd.NA
    bad = out["timestamp"].isna() | out[["open", "high", "low", "close"]].isna().any(axis=1)
    bad |= (out.high < out[["open", "close", "low"]].max(axis=1)) | (out.low > out[["open", "close", "high"]].min(axis=1)) | (out.volume < 0)
    out.loc[bad, ["status", "reason_code"]] = ["ERROR", "INVALID_OHLC"]
    dup = out["timestamp"].duplicated(keep="first") & ~out.timestamp.isna()
    out.loc[dup & ~bad, ["status", "reason_code"]] = ["EXCLUDED", "DUPLICATE"]
    valid = out.status.eq("VALID")
    weekend = out.timestamp.dt.weekday.ge(5)
    out.loc[valid & weekend, ["status", "reason_code"]] = ["EXCLUDED", "WEEKEND"]
    dates = out.timestamp.dt.date.astype(str)
    holiday = dates.isin(config.calendar.holiday_dates)
    out.loc[out.status.eq("VALID") & holiday, ["status", "reason_code"]] = ["EXCLUDED", "HOLIDAY"]
    if config.session_start is None or config.session_end is None:
        raise ValueError("session_start and session_end must be explicit")
    minute = out.timestamp.dt.hour * 60 + out.timestamp.dt.minute
    starts, ends = pd.Series(_clock(config.session_start), index=out.index), pd.Series(_clock(config.session_end), index=out.index)
    for date, end in config.calendar.shortened_session_dates.items(): ends.loc[dates.eq(date)] = _clock(end)
    inside = (minute >= starts) & (minute <= ends)
    for date, bounds in config.calendar.special_session_dates.items():
        inside.loc[dates.eq(date)] = minute.loc[dates.eq(date)].between(_clock(bounds[0]), _clock(bounds[1]))
    for start, end in config.breaks: inside &= ~minute.between(_clock(start), _clock(end))
    out.loc[out.status.eq("VALID") & ~inside, ["status", "reason_code"]] = ["EXCLUDED", "OUTSIDE_SESSION"]
    out["trading_date"] = dates
    if "roll_flag" not in out: out["roll_flag"] = False
    out["roll_flag"] = out.roll_flag.fillna(False).astype(bool)
    out = out.sort_values("timestamp", kind="stable", na_position="last").reset_index(drop=True)
    report = quality_report(out, config.timeframe)
    return out, report


def quality_report(frame: pd.DataFrame, timeframe: str) -> dict[str, Any]:
    valid = frame[frame.status.eq("VALID")].copy()
    gaps = 0
    if len(valid) > 1 and timeframe in FREQUENCIES:
        gaps = int((valid.timestamp.diff() > pd.Timedelta(FREQUENCIES[timeframe]) * 1.5).sum())
    previous = valid.close.shift()
    gap_abs = (valid.open - previous).abs()
    ranges = valid.high - valid.low
    median = ranges.shift().rolling(20, min_periods=5).median()
    suspicious = (gap_abs > 5 * median) & median.gt(0)
    true_ranges = pd.concat([ranges, (valid.high-previous).abs(), (valid.low-previous).abs()], axis=1).max(axis=1)
    recent_atr = true_ranges.shift().rolling(14, min_periods=5).mean()
    jump_rows = []
    for index in valid.index[suspicious]:
        price, jump = abs(float(previous.loc[index])), float(gap_abs.loc[index])
        atr_value = float(recent_atr.loc[index])
        jump_rows.append({"timestamp": _iso(valid.timestamp.loc[index]), "absolute_gap": jump,
            "gap_to_price": jump / price if price else None,
            "gap_to_atr": jump / atr_value if atr_value else None,
            "gap_to_recent_median_range": jump / float(median.loc[index])})
    return {
        "row_count": len(frame), "first_timestamp": _iso(valid.timestamp.min()), "last_timestamp": _iso(valid.timestamp.max()),
        "duplicates": int(frame.reason_code.eq("DUPLICATE").sum()), "reversed_timestamps": int(pd.to_datetime(frame.source_timestamp, errors="coerce").diff().dt.total_seconds().lt(0).sum()),
        "missing_ohlc": int(frame[["open", "high", "low", "close"]].isna().any(axis=1).sum()), "invalid_ohlc": int(frame.reason_code.eq("INVALID_OHLC").sum()),
        "negative_volumes": int(frame.volume.lt(0).sum()), "zero_volume_bars": int(valid.volume.eq(0).sum()), "zero_range_bars": int(valid.high.eq(valid.low).sum()),
        "large_gaps": gaps, "duplicate_trading_timestamps": int(frame.timestamp.duplicated(keep=False).sum()), "weekend_bars": int(frame.reason_code.eq("WEEKEND").sum()),
        "excluded_holiday_bars": int(frame.reason_code.eq("HOLIDAY").sum()), "outside_session_bars": int(frame.reason_code.eq("OUTSIDE_SESSION").sum()),
        "suspicious_price_jumps": int(suspicious.sum()), "suspicious_jump_details": jump_rows,
    }


def _iso(value: Any) -> str | None:
    return None if pd.isna(value) else pd.Timestamp(value).isoformat()


def coverage_report(frame: pd.DataFrame, timeframe: str) -> pd.DataFrame:
    valid = frame[frame.status.eq("VALID")].copy()
    rows = []
    interval = pd.Timedelta(FREQUENCIES[timeframe]) if timeframe in FREQUENCIES else None
    for date, group in valid.groupby("trading_date", sort=True):
        missing = int(((group.timestamp.diff() / interval) - 1).clip(lower=0).fillna(0).sum()) if interval else 0
        rows.append({"trading_date": date, "bars": len(group), "first_bar": _iso(group.timestamp.min()), "last_bar": _iso(group.timestamp.max()), "total_volume": float(group.volume.sum()), "zero_volume_count": int(group.volume.eq(0).sum()), "missing_expected_intervals": missing})
    return pd.DataFrame(rows)


def liquidity_profile(frame: pd.DataFrame) -> pd.DataFrame:
    valid = frame[frame.status.eq("VALID")].copy()
    valid["hour"] = valid.timestamp.dt.hour
    valid["candle_range"] = valid.high - valid.low
    valid["true_range"] = pd.concat([valid.candle_range, (valid.high-valid.close.shift()).abs(), (valid.low-valid.close.shift()).abs()], axis=1).max(axis=1)
    return valid.groupby(["symbol", "timeframe", "hour"], sort=True).agg(median_volume=("volume", "median"), mean_volume=("volume", "mean"), zero_volume_pct=("volume", lambda x: 100*x.eq(0).mean()), median_true_range=("true_range", "median"), median_candle_range=("candle_range", "median"), observations=("volume", "size")).reset_index()


def setup_crosses_rollover(frame: pd.DataFrame, start: Any, end: Any, series_type: str, rollover_policy: str) -> bool:
    if rollover_policy == "allow_adjusted_series" and series_type == "continuous_adjusted": return False
    if rollover_policy == "individual_contract_only" and series_type != "individual_contract": return True
    window = frame.loc[(frame.timestamp >= pd.Timestamp(start)) & (frame.timestamp <= pd.Timestamp(end))]
    return bool(window.get("roll_flag", pd.Series(False, index=window.index)).fillna(False).any())


def build_manifest(source: str | Path, normalized: pd.DataFrame, config: NormalizationConfig) -> dict[str, Any]:
    valid = normalized[normalized.status.eq("VALID")]
    return {"source_sha256": file_sha256(source), "normalized_sha256": dataframe_sha256(normalized), "source_path": str(Path(source).resolve()), "instrument": config.symbol, "timeframe": config.timeframe, "first_timestamp": _iso(valid.timestamp.min()), "last_timestamp": _iso(valid.timestamp.max()), "rows_raw": len(normalized), "rows_valid": len(valid), "excluded_rows": int(normalized.status.eq("EXCLUDED").sum()), "errors": int(normalized.status.eq("ERROR").sum()), "normalization_version": NORMALIZATION_VERSION}
