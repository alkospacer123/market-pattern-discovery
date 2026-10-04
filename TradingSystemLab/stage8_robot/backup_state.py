"""Fail-closed backup command for the REAL_READONLY supervisor database."""
from __future__ import annotations

import argparse
import hashlib
import json
import os
from datetime import datetime, timezone
from pathlib import Path

try:
    from .operations import prune_backups, sqlite_backup, validate_operational_database
    from .specification import PRODUCTION_SPECIFICATION_ID
    from .state import initialize_stage8_11_acceptance_ledger
except ImportError:  # pragma: no cover - permits direct operator invocation
    from operations import prune_backups, sqlite_backup, validate_operational_database
    from specification import PRODUCTION_SPECIFICATION_ID
    from state import initialize_stage8_11_acceptance_ledger

BACKUP_MANIFEST_SCHEMA = "stage8-readonly-sqlite-backup/v1"
SUPERVISOR_DATABASE = "readonly-supervisor.sqlite3"
ACCEPTANCE_BACKUP_MANIFEST_SCHEMA = "stage8-11-acceptance-sqlite-backup/v1"


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def create_production_backup(
    runtime_root: Path, *, keep: int = 14, created_at: datetime | None = None
) -> tuple[Path, Path]:
    """Back up only the canonical supervisor state into its runtime backup dir."""
    root = Path(runtime_root)
    state_directory = root / "state"
    backup_directory = root / "backups"
    if state_directory.is_symlink() or backup_directory.is_symlink():
        raise RuntimeError("SQLITE_BACKUP_RUNTIME_PATH_INVALID")
    source = state_directory / SUPERVISOR_DATABASE
    backup_directory.mkdir(parents=True, exist_ok=True)
    now = (created_at or datetime.now(timezone.utc)).astimezone(timezone.utc)
    stamp = now.strftime("%Y%m%dT%H%M%S.%fZ")
    backup = backup_directory / f"readonly-supervisor-{stamp}.sqlite3"
    manifest = backup.with_name(backup.name + ".manifest.json")
    manifest_temp = manifest.with_name(manifest.name + ".incomplete")
    if backup.exists() or manifest.exists():
        raise RuntimeError("SQLITE_BACKUP_DESTINATION_INVALID")
    try:
        sqlite_backup(source, backup)
        validate_operational_database(backup)
        payload = {
            "backup_filename": backup.name,
            "created_at_utc": now.isoformat().replace("+00:00", "Z"),
            "production_specification_id": PRODUCTION_SPECIFICATION_ID,
            "schema": BACKUP_MANIFEST_SCHEMA,
            "sha256": sha256_file(backup),
        }
        manifest_temp.write_text(json.dumps(payload, sort_keys=True, separators=(",", ":")) + "\n", encoding="utf-8")
        os.replace(manifest_temp, manifest)
        prune_backups(backup_directory, keep)
    except Exception:
        manifest_temp.unlink(missing_ok=True)
        manifest.unlink(missing_ok=True)
        backup.unlink(missing_ok=True)
        raise
    return backup, manifest


def create_stage8_11_acceptance_backup(runtime_root:Path,account_id:str,*,
                                       created_at:datetime|None=None)->tuple[Path,Path]:
    """Independently back up the validated ledger before a later physical run."""
    root=Path(runtime_root); source=initialize_stage8_11_acceptance_ledger(root,account_id)
    directory=root/"backups"/"stage8-11-acceptance"
    if directory.is_symlink(): raise RuntimeError("ACCEPTANCE_BACKUP_PATH_INVALID")
    directory.mkdir(parents=True,exist_ok=True)
    now=(created_at or datetime.now(timezone.utc)).astimezone(timezone.utc)
    backup=directory/f"stage8-11-acceptance-{now.strftime('%Y%m%dT%H%M%S.%fZ')}.sqlite3"
    manifest=backup.with_name(backup.name+".manifest.json")
    if backup.exists() or manifest.exists(): raise RuntimeError("ACCEPTANCE_BACKUP_DESTINATION_INVALID")
    sqlite_backup(source,backup)
    payload={"backup_filename":backup.name,"created_at_utc":now.isoformat().replace("+00:00","Z"),
             "production_specification_id":PRODUCTION_SPECIFICATION_ID,
             "schema":ACCEPTANCE_BACKUP_MANIFEST_SCHEMA,"sha256":sha256_file(backup)}
    temporary=manifest.with_suffix(manifest.suffix+".incomplete")
    try:
        temporary.write_text(json.dumps(payload,sort_keys=True,separators=(",",":"))+"\n",encoding="utf-8")
        os.replace(temporary,manifest)
    except Exception:
        temporary.unlink(missing_ok=True); manifest.unlink(missing_ok=True); backup.unlink(missing_ok=True); raise
    return backup,manifest


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Back up canonical REAL_READONLY supervisor state")
    parser.add_argument("--runtime-root", type=Path, required=True)
    parser.add_argument("--keep", type=int, default=14)
    args = parser.parse_args(argv)
    try:
        backup, _ = create_production_backup(args.runtime_root, keep=args.keep)
    except (RuntimeError, ValueError, OSError):
        print("READONLY_STATE_BACKUP_FAILED")
        return 1
    print(f"READONLY_STATE_BACKUP_CREATED filename={backup.name}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
