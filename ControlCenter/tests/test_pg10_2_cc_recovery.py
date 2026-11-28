"""PG10.2 M03: durable CC command recovery after disposable process crashes."""
import json
from types import SimpleNamespace
import subprocess

import pytest

import v20_admin_control as admin


ROBOT = "v20-shallow"
ACTION = "start"
ID = "d" * 32


def setup(tmp_path, monkeypatch):
    release = tmp_path / "private" / "cc07-v20-release.json"
    release.parent.mkdir()
    monkeypatch.setattr(admin, "RELEASE", release)
    monkeypatch.setattr(admin, "admin_ready", lambda: True)
    monkeypatch.setattr(admin, "_actor_sid", lambda: "S-1-5-21-1-2-3-4")
    monkeypatch.setattr(admin.secrets, "token_hex", lambda n: ID)
    return release


def confirmation(request_id=ID):
    return "cc07 resolve " + ROBOT + " " + ACTION + " " + request_id


def test_crash_after_dispatch_blocks_restart_until_explicit_reconcile(tmp_path, monkeypatch):
    release = setup(tmp_path, monkeypatch)
    calls = []
    original_event = admin._request_event

    def crash_on_finish(*args, **kwargs):
        if args[1] == "finished":
            raise KeyboardInterrupt("synthetic process termination")
        return original_event(*args, **kwargs)

    def child(*args, **kwargs):
        calls.append(1)
        return SimpleNamespace(returncode=0, stdout="cc07_result=verified_start\n")

    monkeypatch.setattr(admin, "_request_event", crash_on_finish)
    monkeypatch.setattr(admin.subprocess, "run", child)
    with pytest.raises(KeyboardInterrupt):
        admin.submit(ROBOT, ACTION, admin.confirmation(ROBOT, ACTION))
    monkeypatch.setattr(admin, "_request_event", original_event)
    release_bytes = release.read_bytes()
    assert release_bytes
    assert admin.recovery_status() == {
        "decision": "RECOVERY_REQUIRED", "request_id": ID, "phase": "INTERRUPTED"}

    # A new process/request cannot repeat the interrupted stock operation.
    monkeypatch.setattr(admin.secrets, "token_hex", lambda n: "e" * 32)
    blocked = admin.submit(ROBOT, ACTION, admin.confirmation(ROBOT, ACTION))
    assert blocked["decision"] == "RECOVERY_REQUIRED"
    assert len(calls) == 1
    assert admin.resolve_recovery(ID, "wrong")["decision"] == "REFUSED_CONFIRMATION"
    assert release.read_bytes() == release_bytes

    resolved = admin.resolve_recovery(ID, confirmation())
    assert resolved == {"decision": "RECONCILED_NO_RETRY", "request_id": ID}
    assert len(calls) == 1
    assert not release.exists()
    archived = release.parent / "cc07-release-history" / (ID + ".json")
    assert archived.read_bytes() == release_bytes
    assert admin.recovery_status() == {"decision": "RECOVERY_CLEAR"}


def test_crash_before_dispatch_never_calls_child_and_preserves_release(tmp_path, monkeypatch):
    release = setup(tmp_path, monkeypatch)
    original_event = admin._request_event

    def crash_on_dispatch(*args, **kwargs):
        if args[1] == "dispatched":
            raise KeyboardInterrupt("synthetic power loss")
        return original_event(*args, **kwargs)

    def forbidden(*args, **kwargs):
        raise AssertionError("child must not run")

    monkeypatch.setattr(admin, "_request_event", crash_on_dispatch)
    monkeypatch.setattr(admin.subprocess, "run", forbidden)
    with pytest.raises(KeyboardInterrupt):
        admin.submit(ROBOT, ACTION, admin.confirmation(ROBOT, ACTION))
    monkeypatch.setattr(admin, "_request_event", original_event)
    assert release.exists()
    events = admin._request_events(ID)
    assert [row["phase"] for row in events] == ["prepared", "release_created"]
    assert admin.recovery_status()["request_id"] == ID
    assert admin.resolve_recovery(ID, confirmation())["decision"] == "RECONCILED_NO_RETRY"
    assert not release.exists()


def test_pause_crash_has_no_release_but_durable_intent_survives(tmp_path, monkeypatch):
    release = setup(tmp_path, monkeypatch)
    action = "pause"
    original_event = admin._request_event

    def crash_on_finish(*args, **kwargs):
        if args[1] == "finished":
            raise KeyboardInterrupt("synthetic reboot")
        return original_event(*args, **kwargs)

    monkeypatch.setattr(admin, "_request_event", crash_on_finish)
    monkeypatch.setattr(admin.subprocess, "run", lambda *a, **k:
                        SimpleNamespace(returncode=0,
                                        stdout="cc07_result=already_halted_no_change\n"))
    with pytest.raises(KeyboardInterrupt):
        admin.submit(ROBOT, action, admin.confirmation(ROBOT, action))
    monkeypatch.setattr(admin, "_request_event", original_event)
    assert not release.exists()
    assert admin.recovery_status()["request_id"] == ID
    phrase = "cc07 resolve " + ROBOT + " " + action + " " + ID
    assert admin.resolve_recovery(ID, phrase)["decision"] == "RECONCILED_NO_RETRY"
    assert not release.exists()
    assert admin.recovery_status()["decision"] == "RECOVERY_CLEAR"


def test_connection_timeout_unknown_is_not_retried_or_deleted(tmp_path, monkeypatch):
    release = setup(tmp_path, monkeypatch)
    calls = []

    def timeout(*args, **kwargs):
        calls.append(1)
        raise subprocess.TimeoutExpired(cmd="synthetic", timeout=180)

    monkeypatch.setattr(admin.subprocess, "run", timeout)
    first = admin.submit(ROBOT, ACTION, admin.confirmation(ROBOT, ACTION))
    assert first["decision"] == "FAILED_UNKNOWN"
    release_bytes = release.read_bytes()
    assert release_bytes
    second = admin.submit(ROBOT, ACTION, admin.confirmation(ROBOT, ACTION))
    assert second["decision"] == "RECOVERY_REQUIRED"
    assert len(calls) == 1
    assert release.read_bytes() == release_bytes
    events = admin._request_events(ID)
    assert events[-1]["decision"] == "FAILED_UNKNOWN"
    assert admin.resolve_recovery(ID, confirmation())["decision"] == "RECONCILED_NO_RETRY"
    assert (release.parent / "cc07-release-history" / (ID + ".json")).read_bytes() == release_bytes
    assert len(calls) == 1


def test_legacy_unknown_release_is_archived_not_unlinked(tmp_path, monkeypatch):
    release = setup(tmp_path, monkeypatch)
    row = {
        "schema": "cc.v20.release.v1", "approved": True, "robot": ROBOT,
        "action": ACTION, "request_id": ID, "actor_sid": "S-1-5-21-1-2-3-4",
        "issued_utc": "2026-11-28T00:00:00+00:00",
        "expires_utc": "2026-11-28T00:01:30+00:00",
    }
    release.write_text(json.dumps(row), encoding="ascii")
    assert admin.recovery_status()["request_id"] == ID
    assert admin.resolve_recovery(ID, confirmation())["decision"] == "RECONCILED_NO_RETRY"
    assert not release.exists()
    assert json.loads((release.parent / "cc07-release-history" / (ID + ".json")).read_text()) == row
