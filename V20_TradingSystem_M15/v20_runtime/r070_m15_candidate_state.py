"""R070 OFFLINE candidate checkpoint pointer using EXISTING H1 SQLite and lock.

Runs only when explicitly instantiated. Paths are separate from deployed
C:/V20Lab/robots/*, FINAM credentials, tasks, and V20 real SQLite.
Store checkpoint ZIP first, then its externally verifiable SHA and cursor
in a single H1 StateStore transaction. A crash before commit leaves the old
checkpoint pointer valid and new ZIP unreferenced (fail closed, no replay).
"""
from __future__ import annotations

from datetime import date, datetime
import hashlib
import json
import sqlite3
from contextlib import closing
from pathlib import Path
import uuid

import pandas as pd

from TradingSystemLab.stage8_robot.operations import InstanceLock
from TradingSystemLab.stage8_robot.state import StateStore

from .ext2_history_bridge import EXT2HistoryBlocked, _strict_m15, m15_history_sha256
from .h1_state_journal import ROBOT_STRATEGIES, _require_v20_root
from .r070_m15_checkpoint import (
    load_r070_m15_checkpoint, resume_r070_m15_checkpoint,
    save_r070_m15_checkpoint,
)

_ID = "v20.r070.m15.checkpoint_pointer.offline.v1"
_PREFIX = "r070_m15_checkpoint:"


class R070CandidateCheckpointState:
    """Isolated OFFLINE SQLite pointer; no LIVE worker or broker API methods."""

    def __init__(self, *, v20_root: Path, robot_id: str, account_id: str):
        if robot_id not in ROBOT_STRATEGIES:
            raise EXT2HistoryBlocked("R070_CANDIDATE_ROBOT_INVALID")
        if not isinstance(account_id, str) or not account_id.strip():
            raise EXT2HistoryBlocked("R070_CANDIDATE_ACCOUNT_REQUIRED")
        root = _require_v20_root(v20_root)
        # Strictly isolated; NEVER reuse the deployed /robots/<slug>/state.
        self.directory = root / "r070-candidate" / robot_id.removeprefix("v20-")
        state_dir = self.directory / "state"
        archive_dir = self.directory / "m15"
        for p in (root / "r070-candidate", self.directory, state_dir, archive_dir):
            if p.is_symlink():
                raise EXT2HistoryBlocked("R070_CANDIDATE_SYMLINK_FORBIDDEN")
            p.mkdir(parents=True, exist_ok=True)
        self.archive_dir = archive_dir
        self.identity = {
            "schema_id": _ID, "mode": "OFFLINE_ONLY",
            "robot_id": robot_id,
            "account_sha256": hashlib.sha256(account_id.encode("utf-8")).hexdigest(),
        }
        self.lock = InstanceLock(self.directory / "r070-candidate-instance.lock")
        self.lock.acquire()
        try:
            state_path = state_dir / "r070-m15-candidate.sqlite3"
            if state_path.is_symlink():
                raise EXT2HistoryBlocked("R070_CANDIDATE_STATE_SYMLINK")
            # H1 StateStore.__init__ may raise on identity mismatch *after*
            # opening SQLite. Probe readonly first and CLOSE the handle on
            # Windows before rejecting a different account/robot.
            if state_path.exists():
                if not state_path.is_file():
                    raise EXT2HistoryBlocked("R070_CANDIDATE_DB_INVALID")
                try:
                    with closing(sqlite3.connect(
                            state_path.as_uri() + "?mode=ro", uri=True)) as db:
                        if db.execute("PRAGMA integrity_check").fetchone() != ("ok",):
                            raise EXT2HistoryBlocked("R070_CANDIDATE_DB_INTEGRITY_INVALID")
                        stored = db.execute(
                            "SELECT value FROM state WHERE key='database_identity'"
                        ).fetchone()
                        if stored is None or json.loads(stored[0]) != self.identity:
                            raise EXT2HistoryBlocked(
                                "R070_CANDIDATE_ACCOUNT_OR_ROBOT_MISMATCH")
                except (sqlite3.DatabaseError, ValueError, TypeError) as exc:
                    raise EXT2HistoryBlocked("R070_CANDIDATE_DB_SCHEMA_INVALID") from exc
            self.store = StateStore(state_path, self.identity)
        except BaseException:
            self.lock.release()
            raise

    def __enter__(self):
        return self

    def __exit__(self, *_):
        self.close()

    def close(self):
        if getattr(self, "store", None) is not None:
            try:
                self.store.close()
            finally:
                self.store = None
                self.lock.release()

    def _get(self, symbol: str) -> dict | None:
        if symbol not in ("USDRUBF", "CNYRUBF", "GLDRUBF", "IMOEXF"):
            raise EXT2HistoryBlocked("R070_CANDIDATE_SYMBOL_INVALID")
        result = self.store.get(_PREFIX + symbol)
        if result is None:
            return None
        keys = {"symbol", "filename", "checkpoint_sha256",
                "history_sha256", "last_open_msk", "generation"}
        if (not isinstance(result, dict) or set(result) != keys
                or result["symbol"] != symbol
                or type(result["generation"]) is not int
                or result["generation"] < 1
                or not isinstance(result["filename"], str)
                or not result["filename"].startswith("r070-" + symbol.lower() + "-")
                or not result["filename"].endswith(".zip")
                or Path(result["filename"]).name != result["filename"]):
            raise EXT2HistoryBlocked("R070_CANDIDATE_POINTER_INVALID")
        return result

    def _save_new(self, *, symbol: str, verified_history: pd.DataFrame,
                  expected_history_sha256: str, previous: dict | None) -> dict:
        history = _strict_m15(verified_history)
        if m15_history_sha256(history) != expected_history_sha256:
            raise EXT2HistoryBlocked("R070_CANDIDATE_HISTORY_SHA_MISMATCH")
        current = history.Datetime.iloc[-1].to_pydatetime()
        if previous is not None:
            try:
                previous_last = datetime.fromisoformat(previous["last_open_msk"])
            except (TypeError, ValueError) as exc:
                raise EXT2HistoryBlocked("R070_CANDIDATE_CURSOR_INVALID") from exc
            if (previous_last.tzinfo is not None or current <= previous_last):
                raise EXT2HistoryBlocked("R070_CANDIDATE_CURSOR_NOT_ADVANCED")
        filename = "r070-" + symbol.lower() + "-" + uuid.uuid4().hex + ".zip"
        path = self.archive_dir / filename
        if path.exists():
            raise EXT2HistoryBlocked("R070_CANDIDATE_CHECKPOINT_ALREADY_EXISTS")
        digest = save_r070_m15_checkpoint(
            path=path, symbol=symbol,
            verified_history=history, expected_history_sha256=expected_history_sha256,
        )
        row = {
            "symbol": symbol, "filename": filename,
            "checkpoint_sha256": digest,
            "history_sha256": expected_history_sha256,
            "last_open_msk": current.isoformat(),
            "generation": 1 if previous is None else previous["generation"] + 1,
        }
        # This is the commit point. Failure leaves the prior pointer in SQLite
        # and the orphan ZIP is never considered authoritative after restart.
        with self.store.transaction():
            if self.store.get(_PREFIX + symbol) != previous:
                raise EXT2HistoryBlocked("R070_CANDIDATE_POINTER_CONCURRENT_CHANGE")
            self.store.put(_PREFIX + symbol, row)
        return row

    def bootstrap(self, *, symbol: str, verified_history: pd.DataFrame,
                  expected_history_sha256: str) -> dict:
        """Only for a caller-proven original R060/terminal/calendar history."""
        if self._get(symbol) is not None:
            raise EXT2HistoryBlocked("R070_CANDIDATE_BOOTSTRAP_EXISTS")
        return self._save_new(
            symbol=symbol, verified_history=verified_history,
            expected_history_sha256=expected_history_sha256, previous=None,
        )

    def restore_and_advance(
        self, *, symbol: str, finam_recent: pd.DataFrame,
        signal_open_msk: datetime, observed_at_msk: datetime,
        independently_verified_open_days: tuple[date, ...],
    ) -> tuple[pd.DataFrame, dict]:
        """Re-verify old SHA + fresh FINAM overlap, then advance once."""
        previous = self._get(symbol)
        if previous is None:
            raise EXT2HistoryBlocked("R070_CANDIDATE_BOOTSTRAP_REQUIRED")
        try:
            previous_cursor = datetime.fromisoformat(previous["last_open_msk"])
        except (ValueError, TypeError) as exc:
            raise EXT2HistoryBlocked("R070_CANDIDATE_CURSOR_INVALID") from exc
        if previous_cursor.tzinfo is not None:
            raise EXT2HistoryBlocked("R070_CANDIDATE_CURSOR_INVALID")
        history, next_sha = resume_r070_m15_checkpoint(
            path=self.archive_dir / previous["filename"], symbol=symbol,
            expected_checkpoint_sha256=previous["checkpoint_sha256"],
            minimum_last_m15_open_msk=previous_cursor,
            finam_recent=finam_recent, signal_open_msk=signal_open_msk,
            observed_at_msk=observed_at_msk,
            independently_verified_open_days=independently_verified_open_days,
        )
        new_row = self._save_new(
            symbol=symbol, verified_history=history,
            expected_history_sha256=next_sha, previous=previous,
        )
        return history, new_row

    def verified_cursor(self, symbol: str) -> dict | None:
        """Non-trading operator status from the candidate-only H1 SQLite."""
        row = self._get(symbol)
        return None if row is None else dict(row)
