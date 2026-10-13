"""Stage 8 #493 pre-isolation SQLite gate. Strictly read-only; never arms/stops production."""
from __future__ import annotations

import argparse
import json
import os
import sqlite3
from pathlib import Path

SPEC = "PROD_STAGE7_46DB784378797C7FB04636892350AFF21006D71A31F2CED9D4B974EDA2DC36B8"
IDENTITY = "TRAIL1__N4_01__FULL__R15"
DB_NAME = "stage8-12-production.sqlite3"
TERMINAL = frozenset({"CANCELLED", "REJECTED", "CLOSED", "RECONCILED"})


class Blocked(RuntimeError):
    pass


def require(value: bool, code: str) -> None:
    if not value:
        raise Blocked(code)


def no_reparse(path: Path) -> None:
    """Reject Windows junctions/reparse points and symlinks, including parents."""
    for candidate in (path, *path.parents):
        try:
            metadata = candidate.lstat()
        except OSError as exc:
            raise Blocked("SQLITE_PATH_METADATA_INVALID") from exc
        require(not candidate.is_symlink(), "SQLITE_SYMLINK_FORBIDDEN")
        attributes = getattr(metadata, "st_file_attributes", None)
        require(os.name != "nt" or attributes is not None,
                "SQLITE_WINDOWS_REPARSE_METADATA_MISSING")
        require(attributes is None or not (attributes & 0x400),
                "SQLITE_WINDOWS_REPARSE_FORBIDDEN")


def strict_root(path: Path) -> Path:
    require(path.is_absolute(), "RUNTIME_ROOT_NOT_ABSOLUTE")
    require(path.is_dir(), "RUNTIME_ROOT_INVALID")
    no_reparse(path)
    root = path.resolve(strict=True)
    require(root == path, "RUNTIME_ROOT_ALIAS_FORBIDDEN")
    for component in (root / "state", root / "state" / DB_NAME):
        require(component.exists(), "SQLITE_PATH_INVALID")
        no_reparse(component)
        require(component.resolve(strict=True) == component, "SQLITE_PATH_ALIAS_FORBIDDEN")
    return root


def inspect(root: Path) -> dict[str, int]:
    root = strict_root(root)
    database = root / "state" / DB_NAME
    # Read-only SQLite may need the pre-existing -wal and -shm files. Never create them.
    wal = database.with_name(database.name + "-wal")
    shm = database.with_name(database.name + "-shm")
    require(not wal.exists() or shm.is_file(), "SQLITE_WAL_REQUIRES_PREEXISTING_SHM")
    for item in (wal, shm):
        if item.exists():
            require(item.is_file(), "SQLITE_SIDEFILE_INVALID")
            no_reparse(item)
    uri = database.as_uri() + "?mode=ro"
    try:
        connection = sqlite3.connect(uri, uri=True, timeout=1)
        try:
            connection.execute("pragma query_only=on")
            connection.execute("begin")
            require(connection.execute("pragma integrity_check").fetchone() == ("ok",), "SQLITE_INTEGRITY_INVALID")
            tables = {r[0] for r in connection.execute("select name from sqlite_master where type='table'")}
            require({"state", "intents", "fills"}.issubset(tables), "SQLITE_SCHEMA_INVALID")
            states = connection.execute("select key, value from state").fetchall()
            require(all(isinstance(k, str) and isinstance(v, str) for k, v in states), "SQLITE_STATE_INVALID")
            require(len(states) == len({k for k, _ in states}), "SQLITE_DUPLICATE_STATE_KEYS")
            state = dict(states)
            require("database_identity" in state, "SQLITE_IDENTITY_MISSING")
            identity = json.loads(state["database_identity"])
            require(isinstance(identity, dict)
                    and identity.get("production_specification_id") == SPEC
                    and identity.get("active_identity") == IDENTITY,
                    "SQLITE_FROZEN_IDENTITY_MISMATCH")
            positions = json.loads(state.get("production_positions", "{}"))
            require(isinstance(positions, dict) and not positions, "SQLITE_POSITIONS_NOT_EMPTY")
            pending = [json.loads(v) for k, v in states if k.startswith("pending_signal:")]
            require(all(v is None for v in pending), "SQLITE_PENDING_SIGNALS_PRESENT")
            rows = connection.execute("select status from intents").fetchall()
            require(all(type(x[0]) is str for x in rows), "SQLITE_INTENT_STATUS_INVALID")
            unresolved = sum(x[0] not in TERMINAL for x in rows)
            require(unresolved == 0, "SQLITE_UNRESOLVED_INTENTS_PRESENT")
            # Stage8.11 is a different ledger and cannot stand in for the production SQLite.
            result = {"positions": len(positions), "unresolved_intents": unresolved,
                      "pending_signals": len([v for v in pending if v is not None])}
            connection.rollback()
            return result
        finally:
            connection.close()
    except (sqlite3.Error, OSError, ValueError, TypeError, KeyError) as exc:
        raise Blocked("SQLITE_READONLY_AUDIT_FAILED") from exc


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--runtime-root", required=True, type=Path)
    args = parser.parse_args()
    print("stage8_493_pre_isolation_sqlite_readonly_no_task_no_trade_no_writes")
    try:
        result = inspect(args.runtime_root)
    except Blocked as exc:
        print("SQLITE_ISOLATION_GATE=BLOCKED:" + str(exc))
        return 1
    for name, value in result.items():
        print(name.upper() + "=" + str(value))
    print("SQLITE_ISOLATION_GATE=PASS_READONLY_NOT_STOP_AUTHORITY")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
