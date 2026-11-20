"""CC-06/07 durable offline control journal. No execution adapters or LIVE switch.

All authorization/state inputs are simulated. The offline receipt never permits a
real Windows Task or FINAM operation, even when all hypothetical gates pass.
"""
from __future__ import annotations

from dataclasses import replace
from datetime import datetime, timezone
import json
from pathlib import Path
import sqlite3

from .v20_control import REQUEST_ID
from .v20_rehearsal import RehearsalFacts, rehearse

SCHEMA = "cc.v20.offline-intake.v1"
DB_NAME = "v20-control-offline.sqlite3"


class OfflineJournal:
    """Persist denied commands with atomic replay detection in CC-owned storage."""

    def __init__(self, directory: Path, operator_aliases: frozenset[str] = frozenset()):
        if type(operator_aliases) is not frozenset or any(
            type(x) is not str or not REQUEST_ID.fullmatch(x)
            for x in operator_aliases
        ):
            raise ValueError("CC07_OPERATOR_REGISTRY_INVALID")
        root = Path(directory)
        if not root.is_dir() or root.is_symlink():
            raise ValueError("CC07_AUDIT_DIRECTORY_INVALID")
        self.path = root / DB_NAME
        self.operators = operator_aliases
        connection = self._connect()
        try:
            connection.execute(
                "CREATE TABLE IF NOT EXISTS requests("
                "request_id TEXT PRIMARY KEY,robot TEXT NOT NULL,action TEXT NOT NULL)"
            )
            connection.execute(
                "CREATE TABLE IF NOT EXISTS events("
                "event_id INTEGER PRIMARY KEY AUTOINCREMENT,"
                "received_at TEXT NOT NULL,request_id TEXT NOT NULL,"
                "robot TEXT NOT NULL,action TEXT NOT NULL,actor TEXT NOT NULL,"
                "decision TEXT NOT NULL,blockers_json TEXT NOT NULL,"
                "pre_state TEXT NOT NULL,post_check TEXT NOT NULL)"
            )
            connection.commit()
        finally:
            connection.close()

    def _connect(self) -> sqlite3.Connection:
        if self.path.is_symlink():
            raise ValueError("CC07_AUDIT_SYMLINK_FORBIDDEN")
        return sqlite3.connect(str(self.path), timeout=0.0, isolation_level=None)

    def submit(
        self, robot: str, action: str, request_id: str, operator_alias: str,
        before: RehearsalFacts, after: RehearsalFacts | None = None
    ) -> dict:
        """Refuse and audit. All facts, including identity, are OFFLINE fixtures."""
        if type(operator_alias) is not str or not REQUEST_ID.fullmatch(operator_alias):
            raise ValueError("CC07_OPERATOR_ALIAS_INVALID")
        rehearse(robot, action, request_id, before)
        if after is not None:
            rehearse(robot, action, request_id, after)
        permitted = operator_alias in self.operators and before.identity_verified
        facts = replace(
            before, role="OPERATOR" if permitted else "VIEWER",
            identity_verified=bool(permitted), live_release_approved=False
        )
        blockers = list(rehearse(robot, action, request_id, facts)["blockers"])
        if after is None:
            post_check = "NOT_OBSERVED_NO_EXECUTION"
        elif (after.task_state, after.open_positions, after.reconciliation_pass) == (
            before.task_state, before.open_positions, before.reconciliation_pass
        ):
            post_check = "SIMULATED_UNCHANGED"
        else:
            post_check = "SIMULATED_UNEXPECTED_CHANGE"
            blockers.append("POST_STATE_MISMATCH")
        receipt = {
            "schema": SCHEMA, "robot": robot, "action": action,
            "request_id": request_id, "operator_alias": operator_alias,
            "decision": "REFUSED_OFFLINE", "blockers": blockers,
            "pre_state": before.task_state, "post_check": post_check,
            "executed": False, "task_mutated": False,
            "finam_contacted": False, "live_authorized": False,
            "audit_persisted": False, "event_id": None,
        }
        connection = None
        try:
            connection = self._connect()
            connection.execute("BEGIN IMMEDIATE")
            exists = connection.execute(
                "SELECT 1 FROM requests WHERE request_id=?", (request_id,)
            ).fetchone()
            if exists:
                receipt["decision"] = "REFUSED_DUPLICATE"
                receipt["blockers"].insert(0, "DUPLICATE_REQUEST")
            else:
                connection.execute(
                    "INSERT INTO requests(request_id,robot,action) VALUES(?,?,?)",
                    (request_id, robot, action)
                )
            cursor = connection.execute(
                "INSERT INTO events(received_at,request_id,robot,action,actor,"
                "decision,blockers_json,pre_state,post_check) VALUES(?,?,?,?,?,?,?,?,?)",
                (datetime.now(timezone.utc).isoformat(), request_id, robot,
                 action, operator_alias, receipt["decision"],
                 json.dumps(receipt["blockers"], separators=(",", ":")),
                 before.task_state, post_check)
            )
            event_id = cursor.lastrowid
            connection.commit()
            receipt["event_id"] = event_id
            receipt["audit_persisted"] = True
        except (sqlite3.Error, OSError, ValueError):
            if connection is not None:
                connection.rollback()
            receipt["decision"] = "REFUSED_AUDIT_UNAVAILABLE"
            receipt["blockers"].append("AUDIT_NOT_PERSISTED")
        finally:
            if connection is not None:
                connection.close()
        return receipt

    def recent(self, limit: int = 20) -> list[dict]:
        """Read bounded recorded denials, newest first."""
        if type(limit) is not int or not 1 <= limit <= 100:
            raise ValueError("CC07_AUDIT_LIMIT_INVALID")
        connection = self._connect()
        try:
            rows = connection.execute(
                "SELECT event_id,received_at,request_id,robot,action,actor,"
                "decision,blockers_json,pre_state,post_check "
                "FROM events ORDER BY event_id DESC LIMIT ?", (limit,)
            ).fetchall()
        finally:
            connection.close()
        return [
            dict(event_id=row[0], received_at=row[1], request_id=row[2],
                 robot=row[3], action=row[4], operator_alias=row[5],
                 decision=row[6], blockers=json.loads(row[7]),
                 pre_state=row[8], post_check=row[9])
            for row in rows
        ]
