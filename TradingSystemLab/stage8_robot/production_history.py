"""Durable H1 history authority for Stage 8.12.4 production.

The frozen T3/H1 engine needs materially more than FINAM's documented 30-day H1
depth because its four-H1 context carries EMA200.  Production therefore seeds a
repository-external SQLite cache from the already-audited perpetual-v3 H1
authority, verifies the frozen Phase-5 OOS prefix hash, then extends that cache
only with overlapping FINAM H1 data.

The cache stores open-labelled UTC bars.  Consumers receive close-labelled
Europe/Moscow bars, matching the research DataLoader/Stage-7 execution semantic.
"""
from __future__ import annotations

import csv
import hashlib
import json
import re
import sqlite3
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any

import pandas as pd

from .finam_api import completed_h1_bars
from .instrument_resolver import parse_rest_value_object
from .readonly_supervisor import newest_expected_h1_close, trading_h1_windows
from .specification import ACTIVE_IDENTITY, INSTRUMENTS, PRODUCTION_SPECIFICATION_ID

CACHE_SCHEMA = "stage8_12_4_production_h1_cache.v1"
CACHE_FILENAME = "stage8-12-4-production-h1.sqlite3"
TRUE_OOS_START = pd.Timestamp("2025-01-01", tz="Europe/Moscow")
PHASE5_AUTHORITY_END = pd.Timestamp("2026-09-16T00:00:00+03:00")
MIN_CONTEXT_BARS = 200
MIN_EXECUTION_BARS = MIN_CONTEXT_BARS * 4
PHASE5_H1_AUTHORITY = {
    "CNYRUBF": (7093, "880e66d2efdba953fdfe65eaa3ffe178b71adcf94dcce5f4254e2e384050e5ec"),
    "GLDRUBF": (7834, "08dcec75a0eb7501c8c7be229a4e020703b4b97e0daff69aeea78c8c51e9053c"),
    "IMOEXF": (7853, "e993fceb16314649617c895e756931f6062d127592338675dbafc6c986d6e6a1189c7733ca7e1ecc52445db5848ebe58c3e6") if False else (7853, "e993fceb16314649617c895e756931f6062d1275923386e2a9b0d4dd35ce6d2b"),
    "USDRUBF": (7058, "ed8af35852c01d170bf9fba54feee05f57fe26865a4f9bfbf5891f747df05934"),
}
REPOSITORY_ROOT = Path(__file__).resolve().parents[2]


class ProductionHistoryError(RuntimeError):
    pass


def _outside_repository(path: Path) -> Path:
    resolved = path.resolve()
    if resolved == REPOSITORY_ROOT or REPOSITORY_ROOT in resolved.parents:
        raise ProductionHistoryError("STAGE8_12_4_HISTORY_CACHE_IN_REPOSITORY_FORBIDDEN")
    return resolved


def cache_path(runtime_root: Path | str) -> Path:
    return _outside_repository(Path(runtime_root)) / "state" / CACHE_FILENAME


def _phase5_frame_sha(frame: pd.DataFrame) -> str:
    return hashlib.sha256(
        pd.util.hash_pandas_object(frame, index=True).values.tobytes()
    ).hexdigest()


def _read_seed_source(source: Path) -> tuple[pd.DataFrame, pd.DataFrame]:
    rows: list[dict[str, str]] = []
    with source.open(encoding="utf-8-sig", newline="") as stream:
        sample = stream.read(4096)
        stream.seek(0)
        if not sample:
            raise ProductionHistoryError("STAGE8_12_4_H1_SEED_EMPTY")
        header = sample.splitlines()[0]
        delimiter = max((",", ";", "\t"), key=header.count)
        reader = csv.DictReader(stream, delimiter=delimiter)
        if not reader.fieldnames:
            raise ProductionHistoryError("STAGE8_12_4_H1_SEED_HEADER_MISSING")
        names = {
            re.sub(r"[<>]", "", field).strip().title(): field
            for field in reader.fieldnames
        }
        time_name = next(
            (names[name] for name in ("Datetime", "Timestamp", "Date") if name in names),
            None,
        )
        if not time_name:
            raise ProductionHistoryError("STAGE8_12_4_H1_SEED_TIMESTAMP_MISSING")
        for raw in reader:
            rows.append(raw)
    if not rows:
        raise ProductionHistoryError("STAGE8_12_4_H1_SEED_EMPTY")

    raw = pd.DataFrame(rows).rename(
        columns=lambda value: re.sub(r"[<>]", "", str(value)).strip().title()
    )
    time_column = next(
        (name for name in ("Datetime", "Timestamp", "Date") if name in raw), None
    )
    if time_column is None:
        raise ProductionHistoryError("STAGE8_12_4_H1_SEED_TIMESTAMP_MISSING")
    stamps = pd.DatetimeIndex(pd.to_datetime(raw[time_column], errors="raise"))
    stamps = (
        stamps.tz_localize("Europe/Moscow")
        if stamps.tz is None
        else stamps.tz_convert("Europe/Moscow")
    )
    columns = ["Open", "High", "Low", "Close"] + (["Volume"] if "Volume" in raw else [])
    frame = raw[columns].apply(pd.to_numeric, errors="raise")
    frame.index = stamps + pd.Timedelta("1h")
    frame.index.name = "CloseTime"
    if frame.index.has_duplicates or not frame.index.is_monotonic_increasing:
        raise ProductionHistoryError("STAGE8_12_4_H1_SEED_TIMESTAMP_ORDER_INVALID")
    if (
        (frame[["Open", "High", "Low", "Close"]] <= 0).any().any()
        or (frame.High < frame[["Open", "Close", "Low"]].max(axis=1)).any()
        or (frame.Low > frame[["Open", "Close", "High"]].min(axis=1)).any()
    ):
        raise ProductionHistoryError("STAGE8_12_4_H1_SEED_OHLC_INVALID")
    oos = frame.loc[
        (frame.index >= TRUE_OOS_START) & (frame.index <= PHASE5_AUTHORITY_END)
    ].copy()
    return frame, oos


def _seed_rows(frame: pd.DataFrame):
    for close_time, row in frame.iterrows():
        close_msk = pd.Timestamp(close_time).tz_convert("Europe/Moscow")
        open_msk = close_msk - pd.Timedelta("1h")
        open_utc = open_msk.tz_convert("UTC")
        yield (
            open_utc.isoformat(),
            close_msk.isoformat(),
            format(float(row.Open), ".15g"),
            format(float(row.High), ".15g"),
            format(float(row.Low), ".15g"),
            format(float(row.Close), ".15g"),
        )


class ProductionHistoryCache:
    def __init__(self, runtime_root: Path | str):
        self.path = cache_path(runtime_root)
        if not self.path.is_file() or self.path.is_symlink():
            raise ProductionHistoryError("STAGE8_12_4_HISTORY_CACHE_MISSING")
        self.db = sqlite3.connect(self.path)
        if self.db.execute("PRAGMA integrity_check").fetchone() != ("ok",):
            raise ProductionHistoryError("STAGE8_12_4_HISTORY_CACHE_INTEGRITY_INVALID")
        identity = self.db.execute(
            "SELECT value FROM metadata WHERE key='identity'"
        ).fetchone()
        expected = {
            "schema_id": CACHE_SCHEMA,
            "production_specification_id": PRODUCTION_SPECIFICATION_ID,
            "active_identity": ACTIVE_IDENTITY,
        }
        if identity is None or json.loads(identity[0]) != expected:
            raise ProductionHistoryError("STAGE8_12_4_HISTORY_CACHE_IDENTITY_INVALID")

    def close(self) -> None:
        self.db.close()

    def latest_open(self, instrument: str) -> datetime | None:
        row = self.db.execute(
            "SELECT open_time_utc FROM bars WHERE instrument=? "
            "ORDER BY open_time_utc DESC LIMIT 1",
            (instrument,),
        ).fetchone()
        return None if row is None else datetime.fromisoformat(row[0])

    def _bar(self, instrument: str, open_time_utc: str):
        return self.db.execute(
            "SELECT open,high,low,close FROM bars WHERE instrument=? AND open_time_utc=?",
            (instrument, open_time_utc),
        ).fetchone()

    def merge_finam_tail(
        self,
        *,
        instrument: str,
        response: dict[str, Any],
        schedule: Any,
        now: datetime,
    ) -> datetime:
        if instrument not in INSTRUMENTS:
            raise ProductionHistoryError("STAGE8_12_4_HISTORY_INSTRUMENT_INVALID")
        if not isinstance(response, dict) or not isinstance(response.get("bars"), list):
            raise ProductionHistoryError("STAGE8_12_4_H1_BARS_SCHEMA_INVALID")
        now_utc = now.astimezone(timezone.utc)
        try:
            windows = trading_h1_windows(schedule)
            completed_today = completed_h1_bars(response, now_utc, windows)
        except (RuntimeError, TypeError, ValueError) as exc:
            raise ProductionHistoryError("STAGE8_12_4_H1_BARS_SCHEMA_INVALID") from exc

        derived = newest_expected_h1_close(schedule, now_utc)
        latest_before = self.latest_open(instrument)
        expected = (
            max(derived, latest_before)
            if derived is not None and latest_before is not None
            else derived or latest_before
        )
        if expected is None:
            raise ProductionHistoryError("STAGE8_12_4_H1_EXPECTED_WATERMARK_UNAVAILABLE")

        current_day = (
            windows[0][0].replace(hour=0, minute=0, second=0, microsecond=0)
            if windows
            else now_utc.replace(hour=0, minute=0, second=0, microsecond=0)
        )
        completed_today_by_open = {
            datetime.fromisoformat(str(row["timestamp"]).replace("Z", "+00:00")).astimezone(timezone.utc): row
            for row in completed_today
        }

        parsed: list[tuple[datetime, tuple[str, str, str, str]]] = []
        seen: set[datetime] = set()
        for row in response["bars"]:
            if not isinstance(row, dict):
                raise ProductionHistoryError("STAGE8_12_4_H1_BARS_SCHEMA_INVALID")
            try:
                opened = datetime.fromisoformat(
                    str(row.get("timestamp")).replace("Z", "+00:00")
                ).astimezone(timezone.utc)
            except (TypeError, ValueError):
                raise ProductionHistoryError("STAGE8_12_4_H1_BARS_SCHEMA_INVALID") from None
            if opened.minute or opened.second or opened.microsecond:
                raise ProductionHistoryError("STAGE8_12_4_H1_OPEN_NOT_WHOLE_HOUR")
            if opened in seen:
                raise ProductionHistoryError("STAGE8_12_4_H1_DUPLICATE_BAR")
            seen.add(opened)
            if opened > expected:
                continue
            if opened >= current_day and opened not in completed_today_by_open:
                raise ProductionHistoryError("STAGE8_12_4_H1_CURRENT_SCHEDULE_MISMATCH")
            try:
                values = tuple(
                    str(parse_rest_value_object(row.get(name), positive=True))
                    for name in ("open", "high", "low", "close")
                )
            except ValueError:
                raise ProductionHistoryError("STAGE8_12_4_H1_BARS_SCHEMA_INVALID") from None
            o, h, l, cl = map(float, values)
            if h < max(o, cl, l) or l > min(o, cl, h):
                raise ProductionHistoryError("STAGE8_12_4_H1_OHLC_INVALID")
            parsed.append((opened, values))

        if not any(opened == expected for opened, _ in parsed):
            raise ProductionHistoryError("STAGE8_12_4_H1_DATA_STALE")

        overlap = 0
        new_rows = []
        for opened, values in sorted(parsed):
            key = opened.isoformat()
            existing = self._bar(instrument, key)
            if existing is not None:
                overlap += 1
                if tuple(existing) != values:
                    raise ProductionHistoryError("STAGE8_12_4_H1_OVERLAP_MISMATCH")
            else:
                close_msk = (opened + timedelta(hours=1)).astimezone(
                    timezone(timedelta(hours=3))
                )
                new_rows.append(
                    (instrument, key, close_msk.isoformat(), *values, "FINAM")
                )
        if latest_before is not None and overlap == 0:
            raise ProductionHistoryError("STAGE8_12_4_H1_CACHE_OVERLAP_REQUIRED")
        with self.db:
            self.db.executemany(
                "INSERT INTO bars(instrument,open_time_utc,close_time_moscow,"
                "open,high,low,close,source) VALUES(?,?,?,?,?,?,?,?)",
                new_rows,
            )
        return expected

    def frame(self, instrument: str) -> pd.DataFrame:
        rows = self.db.execute(
            "SELECT close_time_moscow,open,high,low,close FROM bars "
            "WHERE instrument=? ORDER BY open_time_utc",
            (instrument,),
        ).fetchall()
        if len(rows) < MIN_EXECUTION_BARS:
            raise ProductionHistoryError("STAGE8_12_4_H1_WARMUP_INSUFFICIENT")
        index = pd.DatetimeIndex(
            [pd.Timestamp(row[0]).tz_convert("Europe/Moscow") for row in rows],
            name="CloseTime",
        )
        frame = pd.DataFrame(
            [[float(value) for value in row[1:]] for row in rows],
            columns=["Open", "High", "Low", "Close"],
            index=index,
        )
        if frame.index.has_duplicates or not frame.index.is_monotonic_increasing:
            raise ProductionHistoryError("STAGE8_12_4_H1_CACHE_ORDER_INVALID")
        return frame


def initialize_history_cache(
    runtime_root: Path | str, market_data_root: Path | str
) -> Path:
    destination = cache_path(runtime_root)
    if destination.exists():
        cache = ProductionHistoryCache(runtime_root)
        cache.close()
        return destination
    root = Path(market_data_root).resolve()
    forever = root / "forever"
    if not forever.is_dir():
        raise ProductionHistoryError("STAGE8_12_4_MARKET_DATA_FOREVER_ROOT_MISSING")
    destination.parent.mkdir(parents=True, exist_ok=True)
    temporary = destination.with_name(destination.name + ".incomplete")
    temporary.unlink(missing_ok=True)
    db = sqlite3.connect(temporary)
    try:
        db.execute("PRAGMA journal_mode=DELETE")
        db.execute("CREATE TABLE metadata(key TEXT PRIMARY KEY,value TEXT NOT NULL)")
        db.execute(
            "CREATE TABLE bars("
            "instrument TEXT NOT NULL,"
            "open_time_utc TEXT NOT NULL,"
            "close_time_moscow TEXT NOT NULL,"
            "open TEXT NOT NULL,high TEXT NOT NULL,low TEXT NOT NULL,close TEXT NOT NULL,"
            "source TEXT NOT NULL,"
            "PRIMARY KEY(instrument,open_time_utc))"
        )
        identity = {
            "schema_id": CACHE_SCHEMA,
            "production_specification_id": PRODUCTION_SPECIFICATION_ID,
            "active_identity": ACTIVE_IDENTITY,
        }
        db.execute(
            "INSERT INTO metadata(key,value) VALUES(?,?)",
            ("identity", json.dumps(identity, sort_keys=True)),
        )
        for instrument in INSTRUMENTS:
            source = forever / instrument / f"{instrument}_H1.csv"
            if not source.is_file():
                raise ProductionHistoryError("STAGE8_12_4_H1_SEED_FILE_MISSING")
            frame, oos = _read_seed_source(source)
            expected_rows, expected_hash = PHASE5_H1_AUTHORITY[instrument]
            if len(oos) != expected_rows or _phase5_frame_sha(oos) != expected_hash:
                raise ProductionHistoryError("STAGE8_12_4_PHASE5_H1_AUTHORITY_MISMATCH")
            if len(frame) < MIN_EXECUTION_BARS:
                raise ProductionHistoryError("STAGE8_12_4_H1_WARMUP_INSUFFICIENT")
            db.executemany(
                "INSERT INTO bars(instrument,open_time_utc,close_time_moscow,"
                "open,high,low,close,source) VALUES(?,?,?,?,?,?,?,?)",
                (
                    (instrument, *row, "PHASE5_AUDITED_SEED")
                    for row in _seed_rows(frame)
                ),
            )
        db.commit()
        if db.execute("PRAGMA integrity_check").fetchone() != ("ok",):
            raise ProductionHistoryError("STAGE8_12_4_HISTORY_CACHE_INTEGRITY_INVALID")
    finally:
        db.close()
    try:
        temporary.replace(destination)
    except OSError as exc:
        temporary.unlink(missing_ok=True)
        raise ProductionHistoryError("STAGE8_12_4_HISTORY_CACHE_PUBLISH_FAILED") from exc
    return destination
