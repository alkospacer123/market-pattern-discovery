"""Pinned historical bootstrap + rolling FINAM H1 production history.

The frozen T3/H1 context contains EMA200 on four-H1 context bars.  FINAM H1
history is documented at 30 days, which is insufficient for a cold exact
indicator reconstruction.  Production therefore bootstraps from the already
validated perpetual H1 files, proves an exact OHLC overlap against FINAM, and
then maintains a durable merged cache whose tail must overlap every later FINAM
window.  Missing overlap fails closed; indicators are never silently re-warmed.
"""
from __future__ import annotations

import csv
import hashlib
import json
import os
import subprocess
import tempfile
from datetime import datetime, timedelta, timezone
from decimal import Decimal, InvalidOperation
from pathlib import Path
from typing import Any, Callable

import pandas as pd

from .instrument_resolver import parse_rest_value_object
from .specification import INSTRUMENTS
from .readonly_supervisor import (
    SafetyFault,
    newest_expected_h1_close,
    trading_h1_windows,
)
from .finam_api import completed_h1_bars

BOOTSTRAP_DATA_COMMIT = "50f1fd2178c18b7ab3bd969be82ad01f47a34745"
BOOTSTRAP_FILES = {
    "USDRUBF": ("forever/USDRUBF/USDRUBF_H1.csv", "d2c5b6368a4f75b76bff89c1f709f24064349d62"),
    "CNYRUBF": ("forever/CNYRUBF/CNYRUBF_H1.csv", "0b4be508311b2cc545e00b724d8542f6b36bc914"),
    "GLDRUBF": ("forever/GLDRUBF/GLDRUBF_H1.csv", "29c444f54687db1b5ea682430d8640d53763726a"),
    "IMOEXF": ("forever/IMOEXF/IMOEXF_H1.csv", "36990f468df3fc212915f3d44f45afccbba4a1bf"),
}
CACHE_SCHEMA = "stage8_12_4_h1_history_cache.v1"
CACHE_DIRNAME = "production-h1"
MIN_OVERLAP_BARS = 32
EXPECTED_COLUMNS = ("Datetime", "Open", "High", "Low", "Close", "Volume")
OHLC_COLUMNS = ("Open", "High", "Low", "Close")


class ProductionHistoryError(RuntimeError):
    pass


def _run_git(root: Path, *args: str) -> str:
    try:
        completed = subprocess.run(
            ["git", "-C", str(root), *args],
            check=True,
            capture_output=True,
            text=True,
        )
    except (OSError, subprocess.CalledProcessError):
        raise ProductionHistoryError("BOOTSTRAP_GIT_AUTHORITY_INVALID") from None
    return completed.stdout.strip()


def verify_bootstrap_checkout(data_root: Path | str) -> None:
    root = Path(data_root).resolve()
    if not root.is_dir():
        raise ProductionHistoryError("BOOTSTRAP_DATA_ROOT_MISSING")
    if _run_git(root, "rev-parse", "HEAD") != BOOTSTRAP_DATA_COMMIT:
        raise ProductionHistoryError("BOOTSTRAP_DATA_COMMIT_MISMATCH")
    if _run_git(root, "status", "--porcelain", "--untracked-files=all"):
        raise ProductionHistoryError("BOOTSTRAP_DATA_CHECKOUT_NOT_CLEAN")
    for relative, expected_blob in BOOTSTRAP_FILES.values():
        row = _run_git(root, "ls-files", "-s", "--", relative)
        parts = row.split()
        if len(parts) < 4 or parts[1] != expected_blob or parts[2] != "0":
            raise ProductionHistoryError("BOOTSTRAP_DATA_BLOB_MISMATCH")


def _decimal(value: Any, code: str) -> Decimal:
    try:
        parsed = Decimal(str(value))
    except (InvalidOperation, ValueError):
        raise ProductionHistoryError(code) from None
    if not parsed.is_finite():
        raise ProductionHistoryError(code)
    return parsed


def _validate_ohlc(open_: Decimal, high: Decimal, low: Decimal, close: Decimal) -> None:
    if high < max(open_, close) or low > min(open_, close) or high < low:
        raise ProductionHistoryError("H1_OHLC_INVALID")


def load_bootstrap_h1(data_root: Path | str, instrument: str) -> pd.DataFrame:
    if instrument not in INSTRUMENTS:
        raise ProductionHistoryError("BOOTSTRAP_INSTRUMENT_NOT_N4")
    relative, _ = BOOTSTRAP_FILES[instrument]
    path = Path(data_root).resolve() / relative
    try:
        with path.open("r", encoding="utf-8-sig", newline="") as handle:
            rows = list(csv.DictReader(handle, delimiter=";"))
    except (OSError, csv.Error, UnicodeError):
        raise ProductionHistoryError("BOOTSTRAP_H1_UNREADABLE") from None
    if not rows or tuple(rows[0].keys()) != EXPECTED_COLUMNS:
        raise ProductionHistoryError("BOOTSTRAP_H1_SCHEMA_INVALID")

    timestamps: list[pd.Timestamp] = []
    values: list[list[float]] = []
    for row in rows:
        if set(row) != set(EXPECTED_COLUMNS):
            raise ProductionHistoryError("BOOTSTRAP_H1_SCHEMA_INVALID")
        try:
            stamp = pd.Timestamp(datetime.strptime(row["Datetime"], "%Y-%m-%d %H:%M:%S"))
            stamp = stamp.tz_localize("Europe/Moscow")
        except (TypeError, ValueError):
            raise ProductionHistoryError("BOOTSTRAP_H1_TIMESTAMP_INVALID") from None
        o, h, l, c = (_decimal(row[name], "BOOTSTRAP_H1_PRICE_INVALID")
                      for name in OHLC_COLUMNS)
        _validate_ohlc(o, h, l, c)
        timestamps.append(stamp)
        values.append([float(o), float(h), float(l), float(c)])

    index = pd.DatetimeIndex(timestamps, name="timestamp")
    if index.has_duplicates or not index.is_monotonic_increasing:
        raise ProductionHistoryError("BOOTSTRAP_H1_ORDER_INVALID")
    return pd.DataFrame(values, index=index, columns=OHLC_COLUMNS)


def _parse_finam_rows(response: Any) -> tuple[pd.DataFrame, dict[pd.Timestamp, tuple[Decimal, ...]]]:
    if not isinstance(response, dict) or not isinstance(response.get("bars"), list):
        raise ProductionHistoryError("FINAM_H1_SCHEMA_INVALID")
    timestamps: list[pd.Timestamp] = []
    values: list[list[float]] = []
    exact: dict[pd.Timestamp, tuple[Decimal, ...]] = {}
    for row in response["bars"]:
        if not isinstance(row, dict) or not isinstance(row.get("timestamp"), str):
            raise ProductionHistoryError("FINAM_H1_SCHEMA_INVALID")
        try:
            opened = datetime.fromisoformat(row["timestamp"].replace("Z", "+00:00"))
        except ValueError:
            raise ProductionHistoryError("FINAM_H1_TIMESTAMP_INVALID") from None
        if opened.tzinfo is None:
            raise ProductionHistoryError("FINAM_H1_TIMESTAMP_INVALID")
        opened = opened.astimezone(timezone.utc)
        if opened.minute or opened.second or opened.microsecond:
            raise ProductionHistoryError("FINAM_H1_OPEN_NOT_WHOLE_HOUR_UTC")
        stamp = pd.Timestamp(opened).tz_convert("Europe/Moscow")
        try:
            o, h, l, c = (parse_rest_value_object(row[name]) for name in ("open", "high", "low", "close"))
        except (KeyError, ValueError):
            raise ProductionHistoryError("FINAM_H1_PRICE_INVALID") from None
        _validate_ohlc(o, h, l, c)
        if stamp in exact:
            raise ProductionHistoryError("FINAM_H1_DUPLICATE_BAR")
        exact[stamp] = (o, h, l, c)
        timestamps.append(stamp)
        values.append([float(o), float(h), float(l), float(c)])
    index = pd.DatetimeIndex(timestamps, name="timestamp")
    if index.has_duplicates or not index.is_monotonic_increasing:
        raise ProductionHistoryError("FINAM_H1_ORDER_INVALID")
    return pd.DataFrame(values, index=index, columns=OHLC_COLUMNS), exact


def validated_finam_tail(
    response: Any,
    *,
    schedule: Any,
    now: datetime,
    prior_expected: datetime | None,
) -> tuple[pd.DataFrame, datetime]:
    """Validate the broad FINAM tail plus exact current-schedule freshness."""
    observed = now.astimezone(timezone.utc)
    frame, _ = _parse_finam_rows(response)
    windows = trading_h1_windows(schedule)
    derived = newest_expected_h1_close(schedule, observed)
    scope_start_utc = (
        windows[0][0].replace(hour=0, minute=0, second=0, microsecond=0)
        if windows
        else observed.replace(hour=0, minute=0, second=0, microsecond=0)
    )
    schedule_day_start = pd.Timestamp(scope_start_utc).tz_convert("Europe/Moscow")

    try:
        completed_current = completed_h1_bars(response, observed, windows)
    except (SafetyFault, TypeError, ValueError):
        raise ProductionHistoryError("FINAM_H1_CURRENT_SCHEDULE_INVALID") from None

    raw_current_scope = {stamp for stamp in frame.index if stamp >= schedule_day_start}
    completed_current_scope = {
        pd.Timestamp(datetime.fromisoformat(row["timestamp"]).astimezone(timezone.utc)).tz_convert("Europe/Moscow")
        for row in completed_current
    }
    if raw_current_scope != completed_current_scope:
        raise ProductionHistoryError("FINAM_H1_CURRENT_SCHEDULE_MISMATCH")

    historical = frame.loc[frame.index < schedule_day_start]
    historical_candidate = (
        historical.index[-1].tz_convert("UTC").to_pydatetime()
        if not historical.empty else None
    )
    candidates = [
        candidate.astimezone(timezone.utc)
        for candidate in (derived, prior_expected, historical_candidate)
        if candidate is not None
    ]
    if not candidates:
        raise ProductionHistoryError("H1_EXPECTED_WATERMARK_UNAVAILABLE")
    expected = max(candidates)
    expected_msk = pd.Timestamp(expected).tz_convert("Europe/Moscow")
    if expected_msk not in frame.index:
        raise ProductionHistoryError("STALE_COMPLETED_H1_DATA")

    frame = frame.loc[frame.index <= expected_msk]
    if frame.empty or frame.index[-1] != expected_msk:
        raise ProductionHistoryError("STALE_COMPLETED_H1_DATA")
    return frame, expected


def _frame_exact(frame: pd.DataFrame) -> dict[pd.Timestamp, tuple[Decimal, ...]]:
    result: dict[pd.Timestamp, tuple[Decimal, ...]] = {}
    for stamp, row in frame.iterrows():
        result[stamp] = tuple(Decimal(str(row[name])) for name in OHLC_COLUMNS)
    return result


def merge_h1_history(base: pd.DataFrame, tail: pd.DataFrame) -> pd.DataFrame:
    if base.empty or tail.empty:
        raise ProductionHistoryError("H1_HISTORY_EMPTY")
    overlap = base.index.intersection(tail.index)
    if len(overlap) < MIN_OVERLAP_BARS:
        raise ProductionHistoryError("H1_HISTORY_OVERLAP_INSUFFICIENT")
    # The old cache end must still be inside the FINAM window.  Losing that
    # bridge means the server was offline longer than FINAM's H1 depth.
    if base.index[-1] not in tail.index:
        raise ProductionHistoryError("H1_HISTORY_CONTINUITY_LOST")
    left = _frame_exact(base.loc[overlap])
    right = _frame_exact(tail.loc[overlap])
    if left != right:
        raise ProductionHistoryError("H1_HISTORY_OVERLAP_MISMATCH")
    extension = tail.loc[tail.index > base.index[-1]]
    merged = pd.concat([base, extension])
    if merged.index.has_duplicates or not merged.index.is_monotonic_increasing:
        raise ProductionHistoryError("H1_HISTORY_MERGE_INVALID")
    return merged


def _cache_paths(runtime_root: Path | str, instrument: str) -> tuple[Path, Path]:
    root = Path(runtime_root).resolve() / "state" / CACHE_DIRNAME
    return root / f"{instrument}.csv", root / f"{instrument}.json"


def _frame_digest(frame: pd.DataFrame) -> str:
    payload = frame.to_csv(index=True, date_format="%Y-%m-%dT%H:%M:%S%z", lineterminator="\n")
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


def _write_cache(runtime_root: Path | str, instrument: str, frame: pd.DataFrame) -> None:
    data_path, meta_path = _cache_paths(runtime_root, instrument)
    data_path.parent.mkdir(parents=True, exist_ok=True)
    csv_payload = frame.to_csv(
        index=True, date_format="%Y-%m-%dT%H:%M:%S%z", lineterminator="\n"
    )
    metadata = {
        "schema_id": CACHE_SCHEMA,
        "instrument": instrument,
        "bootstrap_data_commit": BOOTSTRAP_DATA_COMMIT,
        "rows": len(frame),
        "first_timestamp": frame.index[0].isoformat(),
        "last_timestamp": frame.index[-1].isoformat(),
        "sha256": hashlib.sha256(csv_payload.encode("utf-8")).hexdigest(),
    }
    for destination, payload in (
        (data_path, csv_payload),
        (meta_path, json.dumps(metadata, sort_keys=True, separators=(",", ":")) + "\n"),
    ):
        fd, name = tempfile.mkstemp(prefix=f".{destination.name}.", suffix=".tmp", dir=destination.parent)
        temporary = Path(name)
        try:
            with os.fdopen(fd, "w", encoding="utf-8", newline="\n") as stream:
                stream.write(payload)
                stream.flush()
                os.fsync(stream.fileno())
            os.replace(temporary, destination)
        finally:
            temporary.unlink(missing_ok=True)


def _load_cache(runtime_root: Path | str, instrument: str) -> pd.DataFrame | None:
    data_path, meta_path = _cache_paths(runtime_root, instrument)
    if not data_path.exists() and not meta_path.exists():
        return None
    if not data_path.is_file() or not meta_path.is_file():
        raise ProductionHistoryError("H1_CACHE_INCOMPLETE")
    try:
        meta = json.loads(meta_path.read_text(encoding="utf-8"))
        payload = data_path.read_text(encoding="utf-8")
    except (OSError, UnicodeError, json.JSONDecodeError):
        raise ProductionHistoryError("H1_CACHE_INVALID") from None
    if (
        not isinstance(meta, dict)
        or meta.get("schema_id") != CACHE_SCHEMA
        or meta.get("instrument") != instrument
        or meta.get("bootstrap_data_commit") != BOOTSTRAP_DATA_COMMIT
        or meta.get("sha256") != hashlib.sha256(payload.encode("utf-8")).hexdigest()
    ):
        raise ProductionHistoryError("H1_CACHE_AUTHORITY_MISMATCH")
    try:
        frame = pd.read_csv(data_path, index_col="timestamp")
        index = pd.to_datetime(frame.index, utc=True).tz_convert("Europe/Moscow")
        frame.index = pd.DatetimeIndex(index, name="timestamp")
        frame = frame.loc[:, list(OHLC_COLUMNS)].astype(float)
    except Exception:
        raise ProductionHistoryError("H1_CACHE_INVALID") from None
    if (
        frame.empty
        or frame.index.has_duplicates
        or not frame.index.is_monotonic_increasing
        or meta.get("rows") != len(frame)
        or meta.get("first_timestamp") != frame.index[0].isoformat()
        or meta.get("last_timestamp") != frame.index[-1].isoformat()
    ):
        raise ProductionHistoryError("H1_CACHE_AUTHORITY_MISMATCH")
    return frame


def update_h1_history(
    *,
    runtime_root: Path | str,
    data_root: Path | str,
    instrument: str,
    finam_response: Any,
    schedule: Any,
    now: datetime,
    prior_expected: datetime | None,
) -> tuple[pd.DataFrame, datetime]:
    tail, expected = validated_finam_tail(
        finam_response, schedule=schedule, now=now, prior_expected=prior_expected
    )
    cached = _load_cache(runtime_root, instrument)
    if cached is None:
        verify_bootstrap_checkout(data_root)
        base = load_bootstrap_h1(data_root, instrument)
    else:
        base = cached
    merged = merge_h1_history(base, tail)
    _write_cache(runtime_root, instrument, merged)
    return merged, expected
