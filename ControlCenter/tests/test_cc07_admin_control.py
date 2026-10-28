"""CC-07 admin-only GUI controls: no bypass of stock proof/release/audit."""
from pathlib import Path
from types import SimpleNamespace
import json
import os
import pytest
import v20_admin_control as admin


def test_intel_only_and_stock_operator_pin():
    source = Path(__file__).resolve().parents[1] / "v20_admin_control.py"
    text = source.read_text(encoding="utf-8")
    for marker in ("URIU-PC", "IsUserAnAdmin", "cc07-v20-operator.ps1",
                   "7d3bf94ba2fff2d17072eb05f78b745f2a11c9e4",
                   "cc07-gateway-policy.json", "powershell.exe",
                   "cc.v20.release.v1", "O_EXCL", "CC07_RELEASE_SIZE",
                   "FAILED_UNKNOWN", "cc07_result=verified_"):
        assert marker in text
    assert "-noninteractive" not in text.lower().split("args = [", 1)[-1]
    for prohibited in ("start-scheduledtask", "stop-scheduledtask",
                       "finam_token", "open_order", "c:\\v20lab"):
        assert prohibited not in text.lower()


@pytest.mark.parametrize("robot,action,typed,decision", [
    ("unknown", "pause", "cc07 pause unknown", "REFUSED_INVALID_ROBOT"),
    ("v20-shallow", "arm", "cc07 arm v20-shallow", "REFUSED_INVALID_ACTION"),
    ("v20-shallow", "start", "cc07 stop v20-shallow", "REFUSED_CONFIRMATION"),
    ("v20-shallow", "start", "CC07 start v20-shallow", "REFUSED_CONFIRMATION"),
])
def test_invalid_inputs_never_dispatched(monkeypatch, robot, action, typed, decision):
    monkeypatch.setattr(admin, "admin_ready", lambda: True)
    def refuse(*args, **kw):
        raise AssertionError("UNAUTHORIZED_EXECUTION")
    monkeypatch.setattr(admin.subprocess, "run", refuse)
    assert admin.submit(robot, action, typed)["decision"] == decision


def test_offline_environment_fails_closed(monkeypatch):
    monkeypatch.setattr(admin, "admin_ready", lambda: False)
    assert admin.submit("v20-shallow", "pause", "cc07 pause v20-shallow") == {
        "decision": "REFUSED_ADMIN_OPERATOR_NOT_READY"
    }


def test_pause_calls_pinned_operator_without_release(tmp_path, monkeypatch):
    release = tmp_path / "private" / "cc07-v20-release.json"
    release.parent.mkdir()
    monkeypatch.setattr(admin, "RELEASE", release)
    monkeypatch.setattr(admin, "admin_ready", lambda: True)
    monkeypatch.setattr(admin.secrets, "token_hex", lambda n: "a" * 32)
    calls = []
    def fake_run(args, **kw):
        calls.append((args, kw))
        assert not release.exists()
        return SimpleNamespace(returncode=0, stdout="cc07_result=already_halted_no_change\n")
    monkeypatch.setattr(admin.subprocess, "run", fake_run)
    result = admin.submit("v20-obv", "pause", "cc07 pause v20-obv")
    assert result["decision"] == "ALREADY_HALTED"
    assert len(calls) == 1
    assert calls[0][1]["input"] == "cc07 pause v20-obv " + "a" * 32 + "\n"
    assert calls[0][0][-6:] == ["-robot", "v20-obv", "-action", "pause",
                                "-requestid", "a" * 32]


def test_start_release_matches_exact_action_and_is_removed(tmp_path, monkeypatch):
    release = tmp_path / "private" / "cc07-v20-release.json"
    release.parent.mkdir()
    monkeypatch.setattr(admin, "RELEASE", release)
    monkeypatch.setattr(admin, "admin_ready", lambda: True)
    monkeypatch.setattr(admin, "_actor_sid", lambda: "S-1-5-21-1-2-3-4")
    monkeypatch.setattr(admin.secrets, "token_hex", lambda n: "b" * 32)
    saved = []
    def fake_run(args, **kwargs):
        saved.append(json.loads(release.read_text(encoding="utf-8")))
        return SimpleNamespace(returncode=0, stdout="cc07_result=verified_start\n")
    monkeypatch.setattr(admin.subprocess, "run", fake_run)
    result = admin.submit("v20-shallow", "start", "cc07 start v20-shallow")
    assert result["decision"] == "EXECUTED"
    assert not release.exists()
    assert saved[0]["actor_sid"] == "S-1-5-21-1-2-3-4"
    assert saved[0]["approved"] is True
    assert saved[0]["request_id"] == "b" * 32
    assert saved[0]["robot"] == "v20-shallow"
    assert saved[0]["action"] == "start"


def test_existing_release_cannot_be_overwritten(tmp_path, monkeypatch):
    release = tmp_path / "private" / "cc07-v20-release.json"
    release.parent.mkdir()
    release.write_text('{"request_id":"old"}', encoding="utf-8")
    monkeypatch.setattr(admin, "RELEASE", release)
    monkeypatch.setattr(admin, "admin_ready", lambda: True)
    monkeypatch.setattr(admin, "_actor_sid", lambda: "S-1-5-21-1-2-3-4")
    result = admin.submit("v20-inside", "restart", "cc07 restart v20-inside")
    assert result["decision"] == "REFUSED_PREFLIGHT"
    assert release.read_text(encoding="utf-8") == '{"request_id":"old"}'


def test_no_success_on_ambiguous_exit(tmp_path, monkeypatch):
    release = tmp_path / "private" / "cc07-v20-release.json"
    release.parent.mkdir()
    monkeypatch.setattr(admin, "RELEASE", release)
    monkeypatch.setattr(admin, "admin_ready", lambda: True)
    monkeypatch.setattr(admin, "_actor_sid", lambda: "S-1-5-21-1-2-3-4")
    monkeypatch.setattr(admin.subprocess, "run", lambda *a, **k:
                        SimpleNamespace(returncode=1, stdout="cc07_result=verified_stop\n"))
    result = admin.submit("v20-shallow", "stop", "cc07 stop v20-shallow")
    assert result["decision"] == "FAILED_UNKNOWN"
    assert not release.exists()
