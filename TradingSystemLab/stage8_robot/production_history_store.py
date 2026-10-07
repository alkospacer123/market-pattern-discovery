"""Repository-external persistent H1 continuity for Stage 8.12.4 production."""
from __future__ import annotations

import json
import os
import sqlite3
import tempfile
from decimal import Decimal
from pathlib import Path

import pandas as pd

from .production_history import (
    MOSCOW,
    OHLC,
    SEED_FILES,
    SEED_SHA256,
    STAGE5_DATA_COMMIT,
    ProductionHistoryError,
    close_index_for_frozen_t3,
    load_stage5_seed_open_h1,
)
from .specification import ACTIVE_IDENTITY, INSTRUMENTS, PRODUCTION_SPECIFICATION_ID

HISTORY_STORE_SCHEMA = "stage8_12_4_h1_history_store.v1"
HISTORY_STORE_FILENAME = "stage8-12-4-h1-history.sqlite3"
REPOSITORY_ROOT = Path(__file__).resolve().parents[2]


class ProductionHistoryStoreError(RuntimeError):
    pass


def history_store_path(runtime_root: Path | str) -> Path:
    root = Path(runtime_root).resolve()
    if root == REPOSITORY_ROOT or REPOSITORY_ROOT in root.parents:
        raise ProductionHistoryStoreError("STAGE8_12_4_HISTORY_STORE_IN_REPOSITORY_FORBIDDEN")
    return root / "state" / HISTORY_STORE_FILENAME


def _identity() -> dict:
    return {
        "schema_id": HISTORY_STORE_SCHEMA,
        "production_specification_id": PRODUCTION_SPECIFICATION_ID,
        "active_identity": ACTIVE_IDENTITY,
        "stage5_data_commit": STAGE5_DATA_COMMIT,
        "seed_files": dict(sorted(SEED_FILES.items())),
        "seed_sha256": dict(sorted(SEED_SHA256.items())),
    }


def _decimal_text(value) -> str:
    number = Decimal(str(value))
    if not number.is_finite() or number <= 0:
        raise ProductionHistoryStoreError("STAGE8_12_4_HISTORY_PRICE_INVALID")
    text = format(number.normalize(), "f")
    return text.rstrip("0").rstrip(".") if "." in text else text


def _rows(instrument: str, frame: pd.DataFrame, source: str):
    for stamp, row in frame.iterrows():
        opened = pd.Timestamp(stamp)
        if opened.tzinfo is None:
            raise ProductionHistoryStoreError("STAGE8_12_4_HISTORY_TIMESTAMP_INVALID")
        opened = opened.tz_convert(MOSCOW)
        yield (
            instrument,
            opened.isoformat(),
            *(_decimal_text(row[column]) for column in OHLC),
            source,
        )


def initialize_history_store(
    runtime_root: Path | str, market_data_root: Path | str
) -> Path:
    destination = history_store_path(runtime_root)
    destination.parent.mkdir(parents=True, exist_ok=True)
    if destination.exists():
        store = ProductionHistoryStore(runtime_root)
        store.close()
        return destination

    descriptor, name = tempfile.mkstemp(
        prefix=f".{HISTORY_STORE_FILENAME}.", suffix=".incomplete",
        dir=destination.parent,
    )
    os.close(descriptor)
    temporary = Path(name)
    try:
        db = sqlite3.connect(temporary)
        try:
            db.execute("PRAGMA journal_mode=DELETE")
            db.execute("CREATE TABLE metadata(key TEXT PRIMARY KEY,value TEXT NOT NULL)")
            db.execute(
                "CREATE TABLE bars("
                "instrument TEXT NOT NULL,"
                "open_time_moscow TEXT NOT NULL,"
                "open TEXT NOT NULL,high TEXT NOT NULL,low TEXT NOT NULL,close TEXT NOT NULL,"
                "source TEXT NOT NULL,"
                "PRIMARY KEY(instrument,open_time_moscow))"
            )
            db.execute(
                "INSERT INTO metadata(key,value) VALUES(?,?)",
                ("identity", json.dumps(_identity(), sort_keys=True)),
            )
            for instrument in INSTRUMENTS:
                seed = load_stage5_seed_open_h1(market_data_root, instrument)
                db.executemany(
                    "INSERT INTO bars VALUES(?,?,?,?,?,?,?)",
                    _rows(instrument, seed, "STAGE5_PINNED_SEED"),
                )
            db.commit()
            if db.execute("PRAGMA integrity_check").fetchone() != ("ok",):
                raise ProductionHistoryStoreError(
                    "STAGE8_12_4_HISTORY_STORE_INTEGRITY_INVALID"
                )
        finally:
            db.close()
        try:
            os.link(temporary, destination)
        except FileExistsError:
            store = ProductionHistoryStore(runtime_root)
            store.close()
        else:
            temporary.unlink()
    except (sqlite3.Error, OSError, ProductionHistoryError) as exc:
        if isinstance(exc, ProductionHistoryStoreError):
            raise
        raise ProductionHistoryStoreError(
            "STAGE8_12_4_HISTORY_STORE_INITIALIZATION_FAILED"
        ) from exc
    finally:
        temporary.unlink(missing_ok=True)
    return destination


class ProductionHistoryStore:
    def __init__(self, runtime_root: Path | str):
        self.path = history_store_path(runtime_root)
        if not self.path.is_file() or self.path.is_symlink():
            raise ProductionHistoryStoreError("STAGE8_12_4_HISTORY_STORE_MISSING")
        self.db = sqlite3.connect(self.path)
        if self.db.execute("PRAGMA integrity_check").fetchone() != ("ok",):
            raise ProductionHistoryStoreError("STAGE8_12_4_HISTORY_STORE_INTEGRITY_INVALID")
        row = self.db.execute(
            "SELECT value FROM metadata WHERE key='identity'"
        ).fetchone()
        if row is None or json.loads(row[0]) != _identity():
            raise ProductionHistoryStoreError("STAGE8_12_4_HISTORY_STORE_IDENTITY_INVALID")

    def close(self) -> None:
        self.db.close()

    def _open_frame(self, instrument: str) -> pd.DataFrame:
        if instrument not in INSTRUMENTS:
            raise ProductionHistoryStoreError("STAGE8_12_4_HISTORY_INSTRUMENT_INVALID")
        rows = self.db.execute(
            "SELECT open_time_moscow,open,high,low,close FROM bars "
            "WHERE instrument=? ORDER BY open_time_moscow",
            (instrument,),
        ).fetchall()
        if not rows:
            raise ProductionHistoryStoreError("STAGE8_12_4_HISTORY_EMPTY")
        index = pd.DatetimeIndex(
            [pd.Timestamp(row[0]).tz_convert(MOSCOW) for row in rows],
            name="OpenTime",
        )
        frame = pd.DataFrame(
            [[Decimal(value) for value in row[1:]] for row in rows],
            index=index,
            columns=OHLC,
            dtype=object,
        )
        if frame.index.has_duplicates or not frame.index.is_monotonic_increasing:
            raise ProductionHistoryStoreError("STAGE8_12_4_HISTORY_ORDER_INVALID")
        return frame

    def merge_live(self, instrument: str, live: pd.DataFrame) -> None:
        if live.empty or live.index.tz is None:
            raise ProductionHistoryStoreError("STAGE8_12_4_HISTORY_LIVE_INVALID")
        live = live.tz_convert(MOSCOW).sort_index(kind="mergesort")
        if live.index.has_duplicates:
            raise ProductionHistoryStoreError("STAGE8_12_4_HISTORY_LIVE_INVALID")
        existing = self._open_frame(instrument)
        overlap = existing.loc[
            (existing.index >= live.index.min()) & (existing.index <= live.index.max())
        ]
        live_overlap = live.loc[
            (live.index >= existing.index.min()) & (live.index <= existing.index.max())
        ]
        if overlap.empty or live_overlap.empty:
            raise ProductionHistoryStoreError("STAGE8_12_4_HISTORY_OVERLAP_REQUIRED")
        if not overlap.index.equals(live_overlap.index):
            raise ProductionHistoryStoreError("STAGE8_12_4_HISTORY_OVERLAP_TIMESTAMP_MISMATCH")
        for column in OHLC:
            if any(
                Decimal(str(a)) != Decimal(str(b))
                for a, b in zip(overlap[column], live_overlap[column])
            ):
                raise ProductionHistoryStoreError("STAGE8_12_4_HISTORY_OVERLAP_OHLC_MISMATCH")
        appended = live.loc[live.index > existing.index.max()]
        if appended.empty:
            return
        with self.db:
            self.db.executemany(
                "INSERT INTO bars VALUES(?,?,?,?,?,?,?)",
                _rows(instrument, appended, "FINAM_COMPLETED_H1"),
            )

    def close_frame(self, instrument: str) -> pd.DataFrame:
        return close_index_for_frozen_t3(self._open_frame(instrument))
