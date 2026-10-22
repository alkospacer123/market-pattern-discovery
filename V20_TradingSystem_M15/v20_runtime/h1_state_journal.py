"""V20 isolated OFFLINE journal on audited H1 StateStore + InstanceLock.

No FINAM, no order intent, no SLTP, no activation. This journal stores ONLY
reference plans in H1's generic state key-value table. Real order intents,
fills and broker reconciliation are a later V20-04.3 integration, and must
not be inferred from these observations.
"""
from __future__ import annotations

import hashlib
import json
import sqlite3
from contextlib import closing
from datetime import timedelta
from pathlib import Path

from TradingSystemLab.stage8_robot.operations import InstanceLock
from TradingSystemLab.stage8_robot.state import StateStore

from .offline_planner import FrozenSignal, ProposedEntry

ROBOT_STRATEGIES = {
    "v20-shallow": "SHALLOW_PULLBACK",
    "v20-obv": "OBV_PRESSURE",
    "v20-inside": "INSIDE_DAY_RELEASE",
}
LIVE_ENABLED = False
STATE_FILE = "v20-offline-reference.sqlite3"
SCHEMA = "v20.h1_state_store.reference_only.v1"


class V20StateBoundaryError(RuntimeError):
    pass


def _require_v20_root(root: Path) -> Path:
    path = Path(root)
    if not path.is_absolute() or path.name.casefold() != "v20lab":
        raise V20StateBoundaryError("EXACT_ISOLATED_V20LAB_ROOT_REQUIRED")
    parents = (path, *path.parents)
    if any(p.is_symlink() for p in parents):
        raise V20StateBoundaryError("V20_PATH_SYMLINK_FORBIDDEN")
    protected = {"tradingsystemlab", "intradaylab", "controlcenter", ".git"}
    if any(p.name.casefold() in protected for p in path.parents):
        raise V20StateBoundaryError("V20_ROOT_INSIDE_PROTECTED_PROJECT")
    return path.resolve(strict=False)


class IsolatedReferenceJournal:
    def __init__(self, v20_root: Path, robot_id: str, account_id: str):
        if robot_id not in ROBOT_STRATEGIES:
            raise V20StateBoundaryError("UNKNOWN_V20_ROBOT")
        if not isinstance(account_id, str) or not account_id.strip():
            raise V20StateBoundaryError("ACCOUNT_ID_REQUIRED")
        self.robot_id = robot_id
        self.strategy = ROBOT_STRATEGIES[robot_id]
        self.account_hash = hashlib.sha256(account_id.encode("utf-8")).hexdigest()
        root = _require_v20_root(v20_root)
        slug = robot_id.removeprefix("v20-")
        self.instance_root = root / slug
        state_dir = self.instance_root / "state"
        for path in (self.instance_root, state_dir):
            if path.is_symlink():
                raise V20StateBoundaryError("V20_STATE_SYMLINK_FORBIDDEN")
        state_dir.mkdir(parents=True, exist_ok=True)
        self.state_path = state_dir / STATE_FILE
        if self.state_path.is_symlink():
            raise V20StateBoundaryError("V20_STATE_SYMLINK_FORBIDDEN")
        self.identity = {
            "schema_id": SCHEMA,
            "robot_id": robot_id,
            "strategy": self.strategy,
            "account_sha256": self.account_hash,
            "mode": "OFFLINE_ONLY",
        }
        self.lock = InstanceLock(self.instance_root / "v20-instance.lock")
        self.lock.acquire()
        self.store: StateStore | None = None
        try:
            self._preflight_existing_database()
            self.store = StateStore(self.state_path, self.identity)
        except BaseException:
            self.lock.release()
            raise

    def _preflight_existing_database(self) -> None:
        path = self.state_path
        if not path.exists():
            return
        if not path.is_file() or path.is_symlink():
            raise V20StateBoundaryError("V20_DATABASE_INVALID")
        try:
            with closing(sqlite3.connect(path.as_uri() + "?mode=ro", uri=True)) as db:
                if db.execute("PRAGMA integrity_check").fetchone() != ("ok",):
                    raise V20StateBoundaryError("V20_DATABASE_INTEGRITY_INVALID")
                row = db.execute(
                    "SELECT value FROM state WHERE key='database_identity'"
                ).fetchone()
                if row is None or json.loads(row[0]) != self.identity:
                    raise V20StateBoundaryError("V20_DATABASE_ACCOUNT_OR_STRATEGY_MISMATCH")
        except sqlite3.DatabaseError as exc:
            raise V20StateBoundaryError("V20_DATABASE_SCHEMA_INVALID") from exc

    def __enter__(self) -> "IsolatedReferenceJournal":
        return self

    def __exit__(self, *_):
        self.close()

    def close(self) -> None:
        try:
            if self.store is not None:
                self.store.close()
                self.store = None
        finally:
            self.lock.release()

    def _require_open(self) -> StateStore:
        if self.store is None:
            raise V20StateBoundaryError("V20_JOURNAL_CLOSED")
        return self.store

    def record_reference(self, signal: FrozenSignal, entry: ProposedEntry) -> str:
        """Idempotent OFFLINE reference only. This is NOT a broker order intent."""
        if (signal.strategy != self.strategy or entry.strategy != self.strategy
                or signal.symbol != entry.symbol
                or entry.mode != "OFFLINE_REFERENCE_NOT_ORDER"
                or signal.side not in (-1, 1)
                or entry.direction != ("LONG" if signal.side == 1 else "SHORT")
                or entry.entry_bar_open != signal.signal_bar_open + timedelta(minutes=15)
                or type(entry.quantity) is not int or entry.quantity <= 0):
            raise V20StateBoundaryError("REFERENCE_STRATEGY_OR_ENTRY_MISMATCH")
        day = (entry.entry_bar_open - timedelta(hours=9)).date().isoformat()
        material = "|".join((self.robot_id, self.account_hash, entry.symbol,
                             entry.entry_bar_open.isoformat(), entry.direction))
        ref_id = hashlib.sha256(material.encode("utf-8")).hexdigest()
        record = {
            "reference_id": ref_id, "mode": "OFFLINE_REFERENCE_NOT_ORDER",
            "robot_id": self.robot_id, "strategy": self.strategy,
            "symbol": entry.symbol, "session": day,
            "signal_bar_open": signal.signal_bar_open.isoformat(),
            "entry_bar_open": entry.entry_bar_open.isoformat(),
            "direction": entry.direction, "quantity": entry.quantity,
            "reference_entry": str(entry.reference_entry),
            "initial_stop": str(entry.initial_stop),
        }
        state = self._require_open()
        with state.transaction():
            index = state.get("v20_reference_index", {})
            entries = list(index.get(day, []))
            key = f"v20_reference:{ref_id}"
            old = state.get(key)
            if old is not None:
                if old != record:
                    raise V20StateBoundaryError("CONFLICTING_REFERENCE_REPLAY")
                return ref_id
            if len(entries) >= 2:
                raise V20StateBoundaryError("TWO_NEW_ENTRIES_PER_SESSION")
            for previous_key in entries:
                previous = state.get(f"v20_reference:{previous_key}")
                if previous is None:
                    raise V20StateBoundaryError("REFERENCE_INDEX_CORRUPTED")
                if previous["symbol"] == entry.symbol:
                    raise V20StateBoundaryError("ONE_ENTRY_PER_SYMBOL_PER_SESSION")
            state.put(key, record)
            index[day] = entries + [ref_id]
            state.put("v20_reference_index", index)
        return ref_id

    def offline_snapshot(self) -> list[dict]:
        state = self._require_open()
        index = state.get("v20_reference_index", {})
        output = []
        for day, ids in sorted(index.items()):
            for ref_id in ids:
                row = state.get(f"v20_reference:{ref_id}")
                if not isinstance(row, dict) or row.get("session") != day:
                    raise V20StateBoundaryError("REFERENCE_INDEX_CORRUPTED")
                output.append(row)
        return output
