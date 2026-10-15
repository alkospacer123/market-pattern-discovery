"""Read-only startup identity gate for the legacy and opt-in V2 launchers.

This module grants no trading authority and never touches FINAM or DPAPI.
It runs before the launcher obtains a credential or starts production_service.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path
import sqlite3

from .execution_grid import FINAM_FILL_AUTHORITY_VERIFIED, EXECUTION_REVISION
from .production_runtime import AMENDED_RUNTIME_SCHEMA, MODE, RUNTIME_SCHEMA
from .specification import ACTIVE_IDENTITY, PRODUCTION_SPECIFICATION_ID
from .state import _validate_acceptance_schema


class LauncherRevisionError(RuntimeError):
    pass


def validate_state(runtime_root: Path, *, mode: str) -> None:
    """Reject an unintended SQLite revision without opening a writable handle."""
    if mode not in {"legacy", "v2"}:
        raise LauncherRevisionError("STAGE8_493_LAUNCHER_MODE_INVALID")
    path = Path(runtime_root) / "state" / "stage8-12-production.sqlite3"
    if path.is_symlink():
        raise LauncherRevisionError("STAGE8_493_LAUNCHER_STATE_PATH_INVALID")
    if not path.exists():
        # Preserve initial legacy installation behavior. V2 must be migrated first.
        if mode == "legacy":
            return
        raise LauncherRevisionError("STAGE8_493_V2_DATABASE_REQUIRED")
    if not path.is_file():
        raise LauncherRevisionError("STAGE8_493_LAUNCHER_STATE_PATH_INVALID")
    expected = {
        "schema_id": AMENDED_RUNTIME_SCHEMA if mode == "v2" else RUNTIME_SCHEMA,
        "production_specification_id": PRODUCTION_SPECIFICATION_ID,
        "active_identity": ACTIVE_IDENTITY,
        "mode": MODE,
    }
    if mode == "v2":
        expected["execution_revision"] = EXECUTION_REVISION
    try:
        # Read-only open: no schema creation, no WAL checkpoint and no migration.
        db = sqlite3.connect(path.resolve().as_uri() + "?mode=ro", uri=True)
        try:
            db.execute("PRAGMA query_only=ON")
            _validate_acceptance_schema(db)
            if db.execute("PRAGMA integrity_check").fetchone() != ("ok",):
                raise LauncherRevisionError("STAGE8_493_LAUNCHER_STATE_INTEGRITY_INVALID")
            row = db.execute("SELECT value FROM state WHERE key='database_identity'").fetchone()
            if row is None or json.loads(row[0]) != expected:
                raise LauncherRevisionError("STAGE8_493_LAUNCHER_STATE_REVISION_MISMATCH")
        finally:
            db.close()
    except LauncherRevisionError:
        raise
    except (sqlite3.Error, ValueError, TypeError, OSError) as exc:
        raise LauncherRevisionError("STAGE8_493_LAUNCHER_STATE_UNREADABLE") from exc


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Read-only Stage8 launcher revision gate")
    parser.add_argument("--runtime-root", type=Path, required=True)
    parser.add_argument("--mode", choices=("legacy", "v2"), required=True)
    args = parser.parse_args(argv)
    try:
        validate_state(args.runtime_root, mode=args.mode)
        # No V2 launch while release/fill authority is unverified, even if
        # the migrated database and explicitly selected revision are correct.
        if args.mode == "v2" and FINAM_FILL_AUTHORITY_VERIFIED is not True:
            raise LauncherRevisionError("STAGE8_493_V2_RELEASE_AUTHORITY_NOT_VERIFIED")
    except LauncherRevisionError as exc:
        print(str(exc))
        return 1
    print("STAGE8_493_LAUNCHER_STATE_GATE_PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
