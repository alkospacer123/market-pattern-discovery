"""Validated offline recovery for REAL_READONLY operational continuity state."""
from __future__ import annotations

import argparse
import json
import os
from datetime import datetime
from pathlib import Path

from .backup_state import (
    BACKUP_MANIFEST_SCHEMA,
    SUPERVISOR_DATABASE,
    sha256_file,
)
from .operations import InstanceLock, sqlite_backup, validate_operational_database
from .specification import PRODUCTION_SPECIFICATION_ID

MANIFEST_KEYS = frozenset({"schema", "production_specification_id", "backup_filename", "created_at_utc", "sha256"})
RECOVERY_LOCKED = "SQLITE_RECOVERY_SUPERVISOR_RUNNING"
ROLLBACK_BASENAME = ".readonly-supervisor.restore-rollback.sqlite3"


def validate_operational_schema(path: Path) -> None:
    """Require the exact OperationalState table contract, not merely valid SQLite."""
    validate_operational_database(path)


def validate_recovery_point(runtime_root: Path, backup_filename: str) -> tuple[Path, Path]:
    if not isinstance(backup_filename, str) or Path(backup_filename).name != backup_filename:
        raise RuntimeError("SQLITE_RECOVERY_INPUT_INVALID")
    if not backup_filename.startswith("readonly-supervisor-") or not backup_filename.endswith(".sqlite3"):
        raise RuntimeError("SQLITE_RECOVERY_INPUT_INVALID")
    directory = Path(runtime_root) / "backups"
    if directory.is_symlink():
        raise RuntimeError("SQLITE_RECOVERY_INPUT_INVALID")
    backup = directory / backup_filename
    manifest = backup.with_name(backup.name + ".manifest.json")
    if not backup.is_file() or backup.is_symlink() or not manifest.is_file() or manifest.is_symlink():
        raise RuntimeError("SQLITE_RECOVERY_POINT_MISSING")
    try:
        payload = json.loads(manifest.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError) as exc:
        raise RuntimeError("SQLITE_RECOVERY_MANIFEST_INVALID") from exc
    if not isinstance(payload, dict) or frozenset(payload) != MANIFEST_KEYS:
        raise RuntimeError("SQLITE_RECOVERY_MANIFEST_INVALID")
    try:
        timestamp = datetime.fromisoformat(payload["created_at_utc"].replace("Z", "+00:00"))
    except (AttributeError, TypeError, ValueError) as exc:
        raise RuntimeError("SQLITE_RECOVERY_MANIFEST_INVALID") from exc
    if (
        payload["schema"] != BACKUP_MANIFEST_SCHEMA
        or payload["production_specification_id"] != PRODUCTION_SPECIFICATION_ID
        or payload["backup_filename"] != backup.name
        or timestamp.tzinfo is None
        or not isinstance(payload["sha256"], str)
        or len(payload["sha256"]) != 64
    ):
        raise RuntimeError("SQLITE_RECOVERY_MANIFEST_INVALID")
    if sha256_file(backup) != payload["sha256"]:
        raise RuntimeError("SQLITE_RECOVERY_CHECKSUM_MISMATCH")
    validate_operational_schema(backup)
    return backup, manifest


def restore_production_state(runtime_root: Path, backup_filename: str) -> Path:
    """Install a validated recovery point with rollback under the lifetime lock."""
    root = Path(runtime_root)
    backup, _ = validate_recovery_point(root, backup_filename)
    lock = InstanceLock(root / "state" / "stage8-readonly.lock")
    try:
        lock.acquire()
    except RuntimeError as exc:
        if str(exc) == "SECOND_ROBOT_INSTANCE_BLOCKED":
            raise RuntimeError(RECOVERY_LOCKED) from None
        raise
    temporary = None
    try:
        state_directory = root / "state"
        if state_directory.is_symlink():
            raise RuntimeError("SQLITE_RECOVERY_STATE_PATH_INVALID")
        state_directory.mkdir(parents=True, exist_ok=True)
        target = state_directory / SUPERVISOR_DATABASE
        temporary = state_directory / ".readonly-supervisor.recovery.sqlite3"
        rollback = state_directory / ROLLBACK_BASENAME
        originals = [target, Path(f"{target}-wal"), Path(f"{target}-shm")]
        quarantines = [rollback, Path(f"{rollback}-wal"), Path(f"{rollback}-shm")]
        if any(path.exists() for path in quarantines):
            # These internal-only files are never recovery points.  Refuse to
            # guess whether leftovers from an interrupted invocation are old
            # canonical state; an operator can preserve and inspect them.
            raise RuntimeError("SQLITE_RECOVERY_ROLLBACK_MATERIAL_PRESENT")
        # Revalidate under exclusion to close the selection-to-commit race.
        backup, _ = validate_recovery_point(root, backup_filename)
        temporary.unlink(missing_ok=True)
        sqlite_backup(backup, temporary)
        validate_operational_schema(temporary)
        moved: list[tuple[Path, Path]] = []
        installed = False
        try:
            # Quarantine the complete SQLite file set before changing it.  In
            # particular, never unlink a WAL which may contain committed state.
            for original, quarantine in zip(originals, quarantines):
                if original.exists():
                    os.replace(original, quarantine)
                    moved.append((original, quarantine))
            os.replace(temporary, target)
            installed = True
            validate_operational_schema(target)
        except BaseException:
            # Validation may have created sidecars for the candidate.  Remove
            # only candidate files, then put every quarantined original back.
            if installed:
                for candidate in (Path(f"{target}-shm"), Path(f"{target}-wal"), target):
                    candidate.unlink(missing_ok=True)
            rollback_error = None
            for original, quarantine in reversed(moved):
                try:
                    os.replace(quarantine, original)
                except OSError as exc:
                    rollback_error = rollback_error or exc
            if rollback_error is not None:
                raise RuntimeError("SQLITE_RECOVERY_ROLLBACK_FAILED") from rollback_error
            raise
        # The candidate is accepted.  Old sidecars can now be discarded and
        # can never replay over the validated restored database.
        for quarantine in quarantines:
            quarantine.unlink(missing_ok=True)
    finally:
        if temporary is not None:
            temporary.unlink(missing_ok=True)
        lock.release()
    return target


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Restore canonical REAL_READONLY supervisor state")
    parser.add_argument("--runtime-root", type=Path, required=True)
    parser.add_argument("--backup-filename", required=True, help="Filename listed by the verified backup command")
    args = parser.parse_args(argv)
    try:
        restore_production_state(args.runtime_root, args.backup_filename)
    except RuntimeError as exc:
        print(RECOVERY_LOCKED if str(exc) == RECOVERY_LOCKED else "READONLY_STATE_RECOVERY_FAILED")
        return 1
    except (ValueError, OSError):
        print("READONLY_STATE_RECOVERY_FAILED")
        return 1
    print("READONLY_STATE_RECOVERY_COMMITTED_RECONCILIATION_REQUIRED")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
