import ast
import json
import os
import sqlite3
import subprocess
import sys
from contextlib import closing
from datetime import datetime, timezone
from pathlib import Path

import pytest
import TradingSystemLab.stage8_robot.operations as operations_module
import TradingSystemLab.stage8_robot.restore_state as restore_module

from TradingSystemLab.stage8_robot.backup_state import (
    BACKUP_MANIFEST_SCHEMA,
    create_production_backup,
    sha256_file,
)
from TradingSystemLab.stage8_robot.operations import (
    InstanceLock,
    prune_backups,
    sqlite_backup,
    validate_operational_database,
)
from TradingSystemLab.stage8_robot.readonly_supervisor import (
    OperationalState,
    ReadonlySupervisor,
    _authenticated_registry,
)
from TradingSystemLab.stage8_robot.restore_state import (
    CLEANUP_PENDING_BASENAME,
    RECOVERY_CLEANUP_PENDING,
    RECOVERY_LOCKED,
    ROLLBACK_BASENAME,
    main as restore_main,
    restore_production_state,
    validate_recovery_point,
)
from TradingSystemLab.stage8_robot.specification import INSTRUMENTS, PRODUCTION_SPECIFICATION_ID


def populated_state(root: Path, *, cycle: str = "17") -> tuple[OperationalState, dict[str, str]]:
    state = OperationalState(root / "state" / "readonly-supervisor.sqlite3")
    values = {
        "cycle_count": cycle,
        "consecutive_failures": "2",
        "last_api_contact": "2026-01-05T11:30:00+00:00",
        "last_reconciliation": "FAULT",
    }
    for index, symbol in enumerate(INSTRUMENTS):
        value = f"2026-01-05T{8 + index:02d}:00:00+00:00"
        values[f"h1:{symbol}"] = value
        values[f"expected_h1:{symbol}"] = value
    state.put_many(values)
    return state, values


def recovery_point(root: Path):
    state, values = populated_state(root)
    backup, manifest = create_production_backup(
        root, created_at=datetime(2026, 1, 5, 12, tzinfo=timezone.utc)
    )
    return state, values, backup, manifest


def test_online_backup_captures_committed_wal_state_as_standalone_database(tmp_path):
    state, values = populated_state(tmp_path)
    source = tmp_path / "state/readonly-supervisor.sqlite3"
    assert Path(str(source) + "-wal").exists()
    destination = tmp_path / "manual.sqlite3"
    sqlite_backup(source, destination)
    state.put_many({"cycle_count": "18"})
    state.close()
    with sqlite3.connect(destination) as database:
        assert database.execute("PRAGMA integrity_check").fetchone() == ("ok",)
        restored = dict(database.execute("SELECT key,value FROM operational_state"))
    assert restored == values
    assert not Path(str(destination) + "-wal").exists()
    assert not Path(str(destination) + "-shm").exists()


def test_online_backup_closes_every_temporary_handle_before_publication(tmp_path, monkeypatch):
    source = tmp_path / "source.sqlite3"
    destination = tmp_path / "published.sqlite3"
    temporary = destination.with_name(destination.name + ".incomplete")
    with sqlite3.connect(source) as database:
        database.execute("CREATE TABLE sample(value TEXT)")
        database.execute("INSERT INTO sample VALUES ('committed')")

    connections = []
    real_connect = sqlite3.connect
    real_replace = operations_module.os.replace

    class TrackingConnection(sqlite3.Connection):
        closed = False

        def close(self):
            self.closed = True
            return super().close()

    def tracking_connect(*args, **kwargs):
        kwargs["factory"] = TrackingConnection
        connection = real_connect(*args, **kwargs)
        connection.opened_path = str(args[0])
        connections.append(connection)
        return connection

    def assert_unlocked_then_replace(old, new):
        if Path(old) == temporary and Path(new) == destination:
            temporary_handles = [
                connection for connection in connections
                if temporary.resolve().as_uri() in connection.opened_path
                or connection.opened_path == str(temporary)
            ]
            assert len(temporary_handles) == 3
            assert all(connection.closed for connection in temporary_handles)
            assert all(connection.closed for connection in connections)
        return real_replace(old, new)

    monkeypatch.setattr(operations_module.sqlite3, "connect", tracking_connect)
    monkeypatch.setattr(operations_module.os, "replace", assert_unlocked_then_replace)

    assert sqlite_backup(source, destination) == destination
    assert destination.is_file()


def test_operational_validation_closes_readonly_connection(tmp_path, monkeypatch):
    state = OperationalState(tmp_path / "state.sqlite3")
    state.close()
    connections = []
    real_connect = sqlite3.connect

    class TrackingConnection(sqlite3.Connection):
        closed = False

        def close(self):
            self.closed = True
            return super().close()

    def tracking_connect(*args, **kwargs):
        kwargs["factory"] = TrackingConnection
        connection = real_connect(*args, **kwargs)
        connections.append(connection)
        return connection

    monkeypatch.setattr(operations_module.sqlite3, "connect", tracking_connect)
    validate_operational_database(tmp_path / "state.sqlite3")

    assert len(connections) == 1
    assert connections[0].closed


def test_backup_missing_nonfile_and_corrupt_sources_fail_without_creation(tmp_path):
    missing = tmp_path / "missing.sqlite3"
    with pytest.raises(RuntimeError, match="SOURCE_INVALID"):
        sqlite_backup(missing, tmp_path / "missing-backup.sqlite3")
    assert not missing.exists()
    with pytest.raises(RuntimeError, match="SOURCE_INVALID"):
        sqlite_backup(tmp_path, tmp_path / "directory-backup.sqlite3")
    corrupt = tmp_path / "corrupt.sqlite3"
    corrupt.write_bytes(b"not sqlite")
    with pytest.raises(RuntimeError, match="SQLITE_BACKUP_FAILED"):
        sqlite_backup(corrupt, tmp_path / "corrupt-backup.sqlite3")


def test_production_manifest_is_minimal_correct_and_bound_to_checksum(tmp_path):
    state, _, backup, manifest = recovery_point(tmp_path)
    state.close()
    payload = json.loads(manifest.read_text())
    assert payload == {
        "backup_filename": backup.name,
        "created_at_utc": "2026-01-05T12:00:00Z",
        "production_specification_id": PRODUCTION_SPECIFICATION_ID,
        "schema": BACKUP_MANIFEST_SCHEMA,
        "sha256": sha256_file(backup),
    }
    assert "account" not in manifest.read_text().lower()
    assert validate_recovery_point(tmp_path, backup.name) == (backup, manifest)


@pytest.mark.parametrize("mutation", ["missing", "malformed", "extra", "production", "filename"])
def test_missing_or_malformed_manifest_fails_closed(tmp_path, mutation):
    state, _, backup, manifest = recovery_point(tmp_path)
    state.close()
    if mutation == "missing":
        manifest.unlink()
    elif mutation == "malformed":
        manifest.write_text("{")
    else:
        payload = json.loads(manifest.read_text())
        if mutation == "extra": payload["unexpected"] = True
        if mutation == "production": payload["production_specification_id"] = "WRONG"
        if mutation == "filename": payload["backup_filename"] = "other.sqlite3"
        manifest.write_text(json.dumps(payload))
    with pytest.raises(RuntimeError, match="RECOVERY_(POINT_MISSING|MANIFEST_INVALID)"):
        validate_recovery_point(tmp_path, backup.name)


def test_tampered_backup_and_valid_unrelated_database_fail_closed(tmp_path):
    state, _, backup, manifest = recovery_point(tmp_path)
    state.close()
    backup.write_bytes(backup.read_bytes() + b"tamper")
    with pytest.raises(RuntimeError, match="CHECKSUM_MISMATCH"):
        validate_recovery_point(tmp_path, backup.name)
    backup.unlink(); manifest.unlink()
    unrelated = tmp_path / "backups/readonly-supervisor-unrelated.sqlite3"
    with sqlite3.connect(unrelated) as database:
        database.execute("CREATE TABLE unrelated(value TEXT)")
    payload = {
        "backup_filename": unrelated.name, "created_at_utc": "2026-01-05T12:00:00Z",
        "production_specification_id": PRODUCTION_SPECIFICATION_ID,
        "schema": BACKUP_MANIFEST_SCHEMA, "sha256": sha256_file(unrelated),
    }
    unrelated.with_name(unrelated.name + ".manifest.json").write_text(json.dumps(payload))
    with pytest.raises(RuntimeError, match="SCHEMA_INVALID"):
        validate_recovery_point(tmp_path, unrelated.name)


def test_restore_is_lock_excluded_and_does_not_modify_state(tmp_path):
    state, _, backup, _ = recovery_point(tmp_path)
    state.close()
    target = tmp_path / "state/readonly-supervisor.sqlite3"
    before = target.read_bytes()
    lock = InstanceLock(tmp_path / "state/stage8-readonly.lock").acquire()
    try:
        with pytest.raises(RuntimeError, match=RECOVERY_LOCKED):
            restore_production_state(tmp_path, backup.name)
    finally:
        lock.release()
    assert target.read_bytes() == before


def test_atomic_restore_preserves_exact_continuity_and_removes_stale_sidecars(tmp_path):
    state, expected, backup, _ = recovery_point(tmp_path)
    state.close()
    replacement = OperationalState(tmp_path / "state/readonly-supervisor.sqlite3")
    replacement.put_many({"cycle_count": "999", "invented": "newer"})
    replacement.close()
    target = tmp_path / "state/readonly-supervisor.sqlite3"
    Path(str(target) + "-wal").write_bytes(b"stale-wal")
    Path(str(target) + "-shm").write_bytes(b"stale-shm")
    assert restore_production_state(tmp_path, backup.name).target == target
    assert not Path(str(target) + "-wal").exists()
    assert not Path(str(target) + "-shm").exists()
    with sqlite3.connect(target) as database:
        assert database.execute("PRAGMA integrity_check").fetchone() == ("ok",)
        assert dict(database.execute("SELECT key,value FROM operational_state")) == expected
    normal = OperationalState(target)
    try:
        assert normal.get("cycle_count") == "17"
        assert normal.get("last_reconciliation") == "FAULT"
        assert normal.get("invented") is None
        normal.put_many({"cycle_count": "18", "last_reconciliation": "PASS"})
        assert normal.get("cycle_count") == "18"
    finally:
        normal.close()


def wal_backed_canonical_and_backup(root: Path):
    """Leave newer committed canonical state in a real crash-left WAL."""
    state, expected, backup, _ = recovery_point(root)
    state.close()
    target = root / "state/readonly-supervisor.sqlite3"

    # A separate interpreter is essential here.  os._exit deliberately skips
    # sqlite3 connection teardown, leaving committed WAL state without leaving
    # a live file handle in the parent (which would make the fixture POSIX-only).
    crash_writer = """
import os
import sqlite3
import sys
from pathlib import Path

target = Path(sys.argv[1])
database = sqlite3.connect(target)
assert database.execute("PRAGMA journal_mode=WAL").fetchone()[0].lower() == "wal"
database.execute("PRAGMA wal_autocheckpoint=0")
database.executemany(
    "INSERT INTO operational_state VALUES(?,?) "
    "ON CONFLICT(key) DO UPDATE SET value=excluded.value",
    (("cycle_count", "999"), ("invented", "wal-committed")),
)
database.commit()
assert Path(f"{target}-wal").is_file()
values = dict(database.execute("SELECT key,value FROM operational_state"))
assert values["cycle_count"] == "999"
assert values["invented"] == "wal-committed"
os._exit(0)
"""
    child = subprocess.run(
        [sys.executable, "-c", crash_writer, str(target)],
        check=False,
        timeout=30,
    )
    assert child.returncode == 0
    wal = Path(f"{target}-wal")
    shm = Path(f"{target}-shm")
    assert target.is_file()
    assert wal.is_file() and wal.stat().st_size > 0
    paths = [target, wal] + ([shm] if shm.exists() else [])
    before = {path: path.read_bytes() for path in paths}
    return expected, backup, target, paths, before


def assert_original_wal_state(paths, before, target):
    assert {path: path.read_bytes() for path in paths} == before
    with closing(sqlite3.connect(target)) as database:
        values = dict(database.execute("SELECT key,value FROM operational_state"))
    assert values["cycle_count"] == "999"
    assert values["invented"] == "wal-committed"


def test_failed_target_install_restores_real_wal_canonical_state(tmp_path, monkeypatch):
    _, backup, target, paths, before = wal_backed_canonical_and_backup(tmp_path)
    real_replace = restore_module.os.replace

    def fail_candidate_install(source, destination):
        if Path(source).name == ".readonly-supervisor.recovery.sqlite3" and Path(destination) == target:
            raise OSError("forced target replacement failure")
        return real_replace(source, destination)

    monkeypatch.setattr(restore_module.os, "replace", fail_candidate_install)
    with pytest.raises(OSError, match="forced target replacement failure"):
        restore_production_state(tmp_path, backup.name)
    assert_original_wal_state(paths, before, target)


def test_partial_quarantine_failure_rolls_back_real_wal_state(tmp_path, monkeypatch):
    _, backup, target, paths, before = wal_backed_canonical_and_backup(tmp_path)
    real_replace = restore_module.os.replace

    def fail_while_staging_wal(source, destination):
        if Path(source) == Path(f"{target}-wal"):
            raise OSError("forced partial quarantine failure")
        return real_replace(source, destination)

    monkeypatch.setattr(restore_module.os, "replace", fail_while_staging_wal)
    with pytest.raises(OSError, match="forced partial quarantine failure"):
        restore_production_state(tmp_path, backup.name)
    assert_original_wal_state(paths, before, target)


def test_final_validation_failure_rolls_back_real_wal_state(tmp_path, monkeypatch):
    _, backup, target, paths, before = wal_backed_canonical_and_backup(tmp_path)
    real_validate = restore_module.validate_operational_schema

    def fail_installed_candidate(path):
        real_validate(path)
        if Path(path) == target:
            raise RuntimeError("forced final validation failure")

    monkeypatch.setattr(restore_module, "validate_operational_schema", fail_installed_candidate)
    with pytest.raises(RuntimeError, match="forced final validation failure"):
        restore_production_state(tmp_path, backup.name)
    assert_original_wal_state(paths, before, target)


def test_successful_restore_discards_real_old_wal_and_selects_backup(tmp_path):
    expected, backup, target, _, _ = wal_backed_canonical_and_backup(tmp_path)
    assert restore_production_state(tmp_path, backup.name).target == target
    assert not Path(f"{target}-wal").exists()
    assert not Path(f"{target}-shm").exists()
    with closing(sqlite3.connect(target)) as database:
        assert dict(database.execute("SELECT key,value FROM operational_state")) == expected
    assert not list((tmp_path / "state").glob(".readonly-supervisor.restore-rollback.sqlite3*"))


@pytest.mark.parametrize("suffix", ["", "-wal", "-shm"])
def test_post_commit_cleanup_failure_has_distinct_committed_outcome(tmp_path, monkeypatch, suffix):
    expected, backup, target, _, _ = wal_backed_canonical_and_backup(tmp_path)
    real_unlink = Path.unlink
    failed_path = tmp_path / "state" / f"{CLEANUP_PENDING_BASENAME}{suffix}"

    def fail_selected_committed_cleanup(path, *args, **kwargs):
        if path == failed_path:
            raise OSError("forced post-commit cleanup failure")
        return real_unlink(path, *args, **kwargs)

    monkeypatch.setattr(Path, "unlink", fail_selected_committed_cleanup)
    result = restore_production_state(tmp_path, backup.name)
    assert result.target == target
    assert result.cleanup_pending is True

    with closing(sqlite3.connect(target)) as database:
        assert dict(database.execute("SELECT key,value FROM operational_state")) == expected
    assert not Path(f"{target}-wal").exists()
    assert not Path(f"{target}-shm").exists()
    assert failed_path.exists()
    assert not list((tmp_path / "state").glob(f"{ROLLBACK_BASENAME}*"))

    with pytest.raises(RuntimeError, match=RECOVERY_CLEANUP_PENDING):
        restore_production_state(tmp_path, backup.name)
    monkeypatch.setattr(Path, "unlink", real_unlink)
    repeated = restore_production_state(tmp_path, backup.name)
    assert repeated.target == target
    assert repeated.cleanup_pending is False


def test_cli_reports_committed_cleanup_pending_without_generic_failure(tmp_path, monkeypatch, capsys):
    _, backup, _, _, _ = wal_backed_canonical_and_backup(tmp_path)
    real_unlink = Path.unlink
    failed_path = tmp_path / "state" / CLEANUP_PENDING_BASENAME

    def fail_committed_database_cleanup(path, *args, **kwargs):
        if path == failed_path:
            raise OSError("forced committed cleanup failure")
        return real_unlink(path, *args, **kwargs)

    monkeypatch.setattr(Path, "unlink", fail_committed_database_cleanup)
    assert restore_main([
        "--runtime-root", str(tmp_path), "--backup-filename", backup.name,
    ]) == 0
    assert capsys.readouterr().out.strip() == (
        "READONLY_STATE_RECOVERY_COMMITTED_CLEANUP_PENDING_RECONCILIATION_REQUIRED"
    )


@pytest.mark.skipif(os.name != "nt", reason="Windows enforces active SQLite file handles")
def test_windows_external_open_database_fails_restore_closed(tmp_path):
    state, _, backup, _ = recovery_point(tmp_path)
    target = tmp_path / "state/readonly-supervisor.sqlite3"
    state.put_many({"cycle_count": "999", "invented": "actively-open"})
    try:
        with pytest.raises(PermissionError):
            restore_production_state(tmp_path, backup.name)
        assert state.get("cycle_count") == "999"
        assert state.get("invented") == "actively-open"
        assert target.is_file()
        assert not list((tmp_path / "state").glob(f"{ROLLBACK_BASENAME}*"))
        assert not list((tmp_path / "state").glob(f"{CLEANUP_PENDING_BASENAME}*"))
    finally:
        state.close()


class ReconciliationAPI:
    def __init__(self, stale_symbol=None): self.stale_symbol = stale_symbol
    def session_details(self): return {"readonly": True, "account_ids": ["synthetic"]}
    def account(self, _account): return {"status": "ACCOUNT_ACTIVE", "positions": []}
    def orders(self, _account): return {"orders": []}
    def schedule(self, _symbol):
        return {"sessions": [{"type": "CORE_TRADING", "interval": {
            "start_time": "2026-01-05T07:00:00Z", "end_time": "2026-01-05T20:50:00Z"
        }}]}
    def bars(self, symbol, _start, _end):
        opened = "2026-01-05T10:00:00Z" if symbol == self.stale_symbol else "2026-01-05T11:00:00Z"
        return {"bars": [{"timestamp": opened, "close": "1"}]}


def restored_supervisor(root, api):
    return ReadonlySupervisor(
        root, api, "synthetic", _authenticated_registry(), poll_seconds=30,
        clock=lambda: datetime(2026, 1, 5, 12, 30, tzinfo=timezone.utc),
        sleeper=lambda _seconds: None,
    )


def test_normal_reconciliation_advances_from_restored_state(tmp_path):
    state, _, backup, _ = recovery_point(tmp_path); state.close()
    restore_production_state(tmp_path, backup.name)
    service = restored_supervisor(tmp_path, ReconciliationAPI())
    try:
        assert service.run(once=True) == 0
        assert service.cycle_count == 18
        assert service.state.get("last_reconciliation") == "PASS"
        assert service.state.get("consecutive_failures") == "0"
    finally:
        service.close()


def test_post_restore_stale_mismatch_remains_fail_closed(tmp_path):
    state, expected, backup, _ = recovery_point(tmp_path); state.close()
    restore_production_state(tmp_path, backup.name)
    service = restored_supervisor(tmp_path, ReconciliationAPI("GLDRUBF@RTSX"))
    try:
        assert service.run(once=True) == 1
        assert service.cycle_count == 17
        assert service.state.get("h1:GLDRUBF") == expected["h1:GLDRUBF"]
        assert service.state.get("last_reconciliation") == "FAULT"
        assert service.state.get("consecutive_failures") == "3"
    finally:
        service.close()


def test_retention_prunes_database_manifest_units_and_incomplete_orphans(tmp_path):
    directory = tmp_path / "backups"; directory.mkdir()
    for name in ("a.sqlite3", "b.sqlite3", "c.sqlite3"):
        (directory / name).write_bytes(b"x")
        (directory / f"{name}.manifest.json").write_text("{}")
    (directory / "orphan.sqlite3").write_bytes(b"x")
    (directory / "lost.sqlite3.manifest.json").write_text("{}")
    kept = prune_backups(directory, 2)
    assert [path.name for path in kept] == ["c.sqlite3", "b.sqlite3"]
    assert sorted(path.name for path in directory.iterdir()) == [
        "b.sqlite3", "b.sqlite3.manifest.json", "c.sqlite3", "c.sqlite3.manifest.json"
    ]


def test_backup_and_recovery_modules_have_no_order_capable_calls():
    prohibited = {"place_order", "submit_order", "cancel_order", "modify_order"}
    for name in ("backup_state.py", "restore_state.py", "operations.py"):
        tree = ast.parse((Path(__file__).parents[1] / name).read_text())
        calls = {node.func.attr for node in ast.walk(tree)
                 if isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute)}
        assert not calls & prohibited


def test_windows_launcher_has_no_obsolete_state_authority():
    launcher = (Path(__file__).parents[1] / "deploy/windows/run-readonly.ps1").read_text()
    assert "ROBOT_STATE_PATH" not in launcher
    assert "stage8.sqlite3" not in launcher
