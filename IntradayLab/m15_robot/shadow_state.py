"""H1-style durable but order-incapable M15 SQLite shadow authority.

An entirely separate runtime root and account hash are mandatory. This store
records only bounded diagnostic receipts; no order/position mutations, no
trading credential, and no ability to arm a robot. SQLite schema never opens
the running H1 database.
"""
from __future__ import annotations

import hashlib
import json
import os
import sqlite3
import tempfile
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path

from .account_boundary import validate_independent_binding
from .spec import EXECUTION_STATUS, ROBOT_ID

DATABASE_FILENAME = "m15-shadow-readonly.sqlite3"
SCHEMA = (
    "CREATE TABLE authority(key TEXT PRIMARY KEY, value TEXT NOT NULL);"
    "CREATE TABLE observations("
    "cycle INTEGER PRIMARY KEY, observed_at TEXT NOT NULL UNIQUE,"
    "receipt_sha256 TEXT NOT NULL, status TEXT NOT NULL, reason TEXT NOT NULL);"
)


class ShadowStateError(RuntimeError):
    pass


def _check_db(path: Path, identity: dict) -> None:
    uri = path.resolve().as_uri() + "?mode=ro"
    con = sqlite3.connect(uri, uri=True)
    try:
        tables = {row[0] for row in con.execute(
            "SELECT name FROM sqlite_master WHERE type='table'"
        )}
        if tables != {"authority", "observations"}:
            raise ShadowStateError("M15_SHADOW_SCHEMA_MISMATCH")
        row = con.execute("SELECT value FROM authority WHERE key='identity'").fetchone()
        if row is None or json.loads(row[0]) != identity:
            raise ShadowStateError("M15_SHADOW_ACCOUNT_OR_IDENTITY_MISMATCH")
        if con.execute("PRAGMA integrity_check").fetchone() != ("ok",):
            raise ShadowStateError("M15_SHADOW_SQLITE_INTEGRITY_FAIL")
    finally:
        con.close()


class ShadowLedger:
    """Fail-closed account-bound receipts, no orders, permanently HALTED."""

    def __init__(
        self, *, runtime_root: Path, h1_runtime_root: Path, repository_root: Path,
        m15_account_id: str, h1_account_sha256: str,
    ):
        account_hash = validate_independent_binding(
            m15_account_id=m15_account_id,
            h1_account_sha256=h1_account_sha256,
            m15_runtime_root=runtime_root, h1_runtime_root=h1_runtime_root,
            repository_root=repository_root,
        )
        self.identity = {
            "robot": ROBOT_ID, "account_hash": account_hash,
            "broker": "FINAM", "environment": "M15_READONLY_SHADOW",
            "order_authorization": EXECUTION_STATUS,
        }
        self.path = runtime_root.resolve() / "state" / DATABASE_FILENAME
        self.path.parent.mkdir(parents=True, exist_ok=True)
        if not self.path.exists():
            fd, name = tempfile.mkstemp(
                prefix="." + DATABASE_FILENAME, suffix=".pending",
                dir=self.path.parent,
            )
            os.close(fd)
            tmp = Path(name)
            try:
                # 'with sqlite3.connect(...)' only commits/rolls back;
                # it does NOT close the connection. Windows forbids unlinking
                # a still-open .pending SQLite file (WinError 32).
                con = sqlite3.connect(tmp)
                try:
                    con.executescript(SCHEMA)
                    con.execute(
                        "INSERT INTO authority(key,value) VALUES (?,?)",
                        ("identity", json.dumps(self.identity, sort_keys=True)),
                    )
                    con.commit()
                finally:
                    con.close()
                _check_db(tmp, self.identity)
                try:
                    os.link(tmp, self.path)
                except FileExistsError:
                    pass  # Recheck the winner; never overwrite or reset it.
            finally:
                tmp.unlink(missing_ok=True)
        _check_db(self.path, self.identity)
        self._con = sqlite3.connect(self.path)
        self._con.execute("PRAGMA busy_timeout=3000")

    @property
    def halted(self) -> bool:
        return True  # No arming API or persisted re-arm transition exists.

    def latest(self) -> dict | None:
        row = self._con.execute(
            "SELECT cycle,observed_at,receipt_sha256,status,reason"
            " FROM observations ORDER BY cycle DESC LIMIT 1"
        ).fetchone()
        return None if row is None else dict(
            zip(("cycle", "observed_at", "receipt_sha256", "status", "reason"), row)
        )

    def append(self, *, observed_at: datetime, status: str, reason: str, facts: dict) -> dict:
        if observed_at.tzinfo is None or observed_at.utcoffset() is None:
            raise ShadowStateError("M15_SHADOW_TIMEZONE_REQUIRED")
        if status not in ("HEALTHY_READONLY", "FAULT_HALTED"):
            raise ShadowStateError("M15_SHADOW_STATUS_INVALID")
        if not isinstance(reason, str) or not reason or len(reason) > 128:
            raise ShadowStateError("M15_SHADOW_REASON_INVALID")
        if not isinstance(facts, dict):
            raise ShadowStateError("M15_SHADOW_FACTS_INVALID")
        # The bounded facts never include raw account IDs, symbols or credentials.
        if set(facts) != {"position_count", "active_order_count"}:
            raise ShadowStateError("M15_SHADOW_FACTS_SCHEMA_INVALID")
        if any(type(v) is not int or v < 0 for v in facts.values()):
            raise ShadowStateError("M15_SHADOW_FACTS_INVALID")
        stamp = observed_at.astimezone(timezone.utc).isoformat()
        payload = {"at": stamp, "status": status, "reason": reason, **facts}
        digest = hashlib.sha256(json.dumps(payload, sort_keys=True).encode()).hexdigest()
        with self._con:
            last = self.latest()
            if last is not None and stamp <= last["observed_at"]:
                raise ShadowStateError("M15_SHADOW_STALE_OR_REPEATED_CYCLE")
            cycle = (last["cycle"] + 1) if last is not None else 1
            self._con.execute(
                "INSERT INTO observations(cycle,observed_at,receipt_sha256,status,reason)"
                " VALUES (?,?,?,?,?)",
                (cycle, stamp, digest, status, reason),
            )
        return {"cycle": cycle, "status": status, "reason": reason,
                "observed_at": stamp, "receipt_sha256": digest, "halted": True}

    def close(self) -> None:
        self._con.close()
