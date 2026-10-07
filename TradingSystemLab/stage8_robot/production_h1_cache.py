"""Persistent causal H1 authority for Stage 8.12.4 production.

The cache is external to Git. It is initialized once from the exact frozen N4
Stage 5 data files, then extended only by FINAM completed H1 bars after an exact
overlap comparison. Existing rows are never repaired or overwritten.
"""
from __future__ import annotations

import json
import os
import sqlite3
import tempfile
from pathlib import Path

import pandas as pd

from .production_history import (
    MOSCOW,
    OHLC,
    SEED_SHA256,
    STAGE5_DATA_COMMIT,
    ProductionHistoryError,
    load_stage5_seed_open_h1,
)
from .specification import INSTRUMENTS, PRODUCTION_SPECIFICATION_ID

CACHE_SCHEMA = "stage8_12_4_h1_cache.v1"
CACHE_FILENAME = "stage8-12-4-h1-cache.sqlite3"
REPOSITORY_ROOT = Path(__file__).resolve().parents[2]

_SCHEMA = """
CREATE TABLE metadata(
    key TEXT PRIMARY KEY,
    value TEXT NOT NULL
);
CREATE TABLE bars(
    instrument TEXT NOT NULL,
    open_utc TEXT NOT NULL,
    open TEXT NOT NULL,
    high TEXT NOT NULL,
    low TEXT NOT NULL,
    close TEXT NOT NULL,
    source TEXT NOT NULL,
    PRIMARY KEY(instrument, open_utc)
);
"""


class ProductionH1CacheError(RuntimeError):
    pass


def _outside_repository(path: Path) -> Path:
    resolved = path.resolve()
    if resolved == REPOSITORY_ROOT or REPOSITORY_ROOT in resolved.parents:
        raise ProductionH1CacheError("STAGE8_12_4_H1_CACHE_REPOSITORY_FORBIDDEN")
    return resolved


def cache_path(runtime_root: Path | str) -> Path:
    return _outside_repository(Path(runtime_root)) / "state" / CACHE_FILENAME


def _identity() -> dict:
    return {
        "schema_id": CACHE_SCHEMA,
        "production_specification_id": PRODUCTION_SPECIFICATION_ID,
        "stage5_data_commit": STAGE5_DATA_COMMIT,
        "seed_sha256": dict(SEED_SHA256),
        "instruments": list(INSTRUMENTS),
    }


def _validate_schema(connection: sqlite3.Connection) -> None:
    tables = {
        row[0]
        for row in connection.execute(
            "SELECT name FROM sqlite_master WHERE type='table'"
        )
    }
    if tables != {"metadata", "bars"}:
        raise ProductionH1CacheError("STAGE8_12_4_H1_CACHE_SCHEMA_INVALID")
    row = connection.execute(
        "SELECT value FROM metadata WHERE key='identity'"
    ).fetchone()
    if row is None:
        raise ProductionH1CacheError("STAGE8_12_4_H1_CACHE_IDENTITY_MISSING")
    try:
        identity = json.loads(row[0])
    except json.JSONDecodeError:
        raise ProductionH1CacheError("STAGE8_12_4_H1_CACHE_IDENTITY_INVALID") from None
    if identity != _identity():
        raise ProductionH1CacheError("STAGE8_12_4_H1_CACHE_IDENTITY_MISMATCH")
    if connection.execute("PRAGMA integrity_check").fetchone() != ("ok",):
        raise ProductionH1CacheError("STAGE8_12_4_H1_CACHE_INTEGRITY_INVALID")


def _insert_frame(
    connection: sqlite3.Connection,
    instrument: str,
    frame: pd.DataFrame,
    *,
    source: str,
) -> None:
    if instrument not in INSTRUMENTS or source not in {"SEED", "FINAM"}:
        raise ProductionH1CacheError("STAGE8_12_4_H1_CACHE_INSERT_AUTHORITY_INVALID")
    rows = []
    for stamp, row in frame.iterrows():
        opened = pd.Timestamp(stamp)
        if opened.tzinfo is None:
            raise ProductionH1CacheError("STAGE8_12_4_H1_CACHE_TIMESTAMP_INVALID")
        opened_utc = opened.tz_convert("UTC").isoformat()
        rows.append((
            instrument,
            opened_utc,
            str(row.Open),
            str(row.High),
            str(row.Low),
            str(row.Close),
            source,
        ))
    try:
        connection.executemany(
            "INSERT INTO bars(instrument,open_utc,open,high,low,close,source) "
            "VALUES(?,?,?,?,?,?,?)",
            rows,
        )
    except sqlite3.IntegrityError:
        raise ProductionH1CacheError("STAGE8_12_4_H1_CACHE_DUPLICATE_INSERT") from None


def initialize_cache(
    runtime_root: Path | str,
    data_root: Path | str,
) -> Path:
    """Create the cache exactly once from the pinned N4 seed bytes."""
    destination = cache_path(runtime_root)
    destination.parent.mkdir(parents=True, exist_ok=True)
    if destination.exists():
        connection = sqlite3.connect(destination)
        try:
            _validate_schema(connection)
        finally:
            connection.close()
        return destination

    descriptor, name = tempfile.mkstemp(
        prefix=f".{CACHE_FILENAME}.", suffix=".incomplete", dir=destination.parent
    )
    os.close(descriptor)
    temporary = Path(name)
    try:
        connection = sqlite3.connect(temporary)
        try:
            connection.executescript(_SCHEMA)
            connection.execute(
                "INSERT INTO metadata(key,value) VALUES('identity',?)",
                (json.dumps(_identity(), sort_keys=True, separators=(",", ":")),),
            )
            for instrument in INSTRUMENTS:
                seed = load_stage5_seed_open_h1(data_root, instrument)
                _insert_frame(connection, instrument, seed, source="SEED")
            connection.commit()
            connection.execute("PRAGMA wal_checkpoint(FULL)")
            _validate_schema(connection)
        finally:
            connection.close()

        try:
            os.link(temporary, destination)
        except FileExistsError:
            existing = sqlite3.connect(destination)
            try:
                _validate_schema(existing)
            finally:
                existing.close()
        else:
            temporary.unlink()
        return destination
    finally:
        temporary.unlink(missing_ok=True)


class ProductionH1Cache:
    def __init__(self, runtime_root: Path | str):
        self.path = cache_path(runtime_root)
        if not self.path.is_file() or self.path.is_symlink():
            raise ProductionH1CacheError("STAGE8_12_4_H1_CACHE_NOT_INITIALIZED")
        self.db = sqlite3.connect(self.path)
        _validate_schema(self.db)

    def close(self) -> None:
        self.db.close()

    def frame(self, instrument: str) -> pd.DataFrame:
        if instrument not in INSTRUMENTS:
            raise ProductionH1CacheError("STAGE8_12_4_H1_CACHE_INSTRUMENT_INVALID")
        rows = self.db.execute(
            "SELECT open_utc,open,high,low,close FROM bars "
            "WHERE instrument=? ORDER BY open_utc",
            (instrument,),
        ).fetchall()
        if not rows:
            raise ProductionH1CacheError("STAGE8_12_4_H1_CACHE_EMPTY")
        index = pd.DatetimeIndex(
            [pd.Timestamp(row[0]).tz_convert(MOSCOW) for row in rows],
            name="OpenTime",
        )
        frame = pd.DataFrame(
            [[row[1], row[2], row[3], row[4]] for row in rows],
            index=index,
            columns=OHLC,
        )
        for column in OHLC:
            frame[column] = frame[column].map(lambda value: __import__("decimal").Decimal(value))
        if index.has_duplicates or not index.is_monotonic_increasing:
            raise ProductionH1CacheError("STAGE8_12_4_H1_CACHE_ORDER_INVALID")
        return frame

    def merge_finam(self, instrument: str, live: pd.DataFrame) -> int:
        """Verify the overlapping tail exactly, then append strictly newer bars."""
        if instrument not in INSTRUMENTS:
            raise ProductionH1CacheError("STAGE8_12_4_H1_CACHE_INSTRUMENT_INVALID")
        if live.empty or live.index.tz is None:
            raise ProductionH1CacheError("STAGE8_12_4_H1_CACHE_LIVE_INVALID")
        if live.index.has_duplicates or not live.index.is_monotonic_increasing:
            raise ProductionH1CacheError("STAGE8_12_4_H1_CACHE_LIVE_INVALID")
        cached = self.frame(instrument)
        overlap_end = min(cached.index.max(), live.index.max())
        cached_overlap = cached.loc[
            (cached.index >= live.index.min()) & (cached.index <= overlap_end)
        ]
        live_overlap = live.loc[
            (live.index >= live.index.min()) & (live.index <= overlap_end)
        ]
        if cached_overlap.empty or live_overlap.empty:
            raise ProductionH1CacheError("STAGE8_12_4_H1_CACHE_NO_OVERLAP")
        if not cached_overlap.index.equals(live_overlap.index):
            raise ProductionH1CacheError("STAGE8_12_4_H1_CACHE_TIMESTAMP_MISMATCH")
        for column in OHLC:
            if any(
                left != right
                for left, right in zip(cached_overlap[column], live_overlap[column])
            ):
                raise ProductionH1CacheError("STAGE8_12_4_H1_CACHE_OHLC_MISMATCH")

        appended = live.loc[live.index > cached.index.max()]
        if appended.empty:
            return 0
        with self.db:
            _insert_frame(self.db, instrument, appended, source="FINAM")
        return len(appended)

    def latest_open(self, instrument: str) -> pd.Timestamp:
        row = self.db.execute(
            "SELECT open_utc FROM bars WHERE instrument=? "
            "ORDER BY open_utc DESC LIMIT 1",
            (instrument,),
        ).fetchone()
        if row is None:
            raise ProductionH1CacheError("STAGE8_12_4_H1_CACHE_EMPTY")
        return pd.Timestamp(row[0]).tz_convert(MOSCOW)
