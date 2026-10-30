"""CC-07 privilege boundary: simulate requests, no real V20/FINAM or Task I/O."""
import json
from datetime import datetime, timezone
from pathlib import Path
import subprocess
import sys

import pytest

from controller import cc07_command_worker as worker

ROOT = Path(__file__).resolve().parents[1]


def test_worker_cli_check_does_not_touch_intel(tmp_path):
    r = subprocess.run(
        [sys.executable, "-I", "-B",
         str(ROOT / "controller" / "cc07_command_worker.py"),
         "--mode", "check"],
        cwd=tmp_path, capture_output=True, text=True, timeout=8, check=False)
    assert r.returncode == 0
    assert "cc07_worker=source_only_no_execution" in r.stdout
    assert "cc07_worker_release=not_active" in r.stdout
    assert not list(tmp_path.iterdir())


def test_bounded_wire_and_strict_identity():
    data = json.dumps({"a": 1, "b": 2}).encode()
    assert worker.parse_strict(data, {"a", "b"}, 512) == {"a": 1, "b": 2}
    for raw in (b'{"a":1,"a":2,"b":2}', b'{"a":1}', b'{',
                b'{"a":NaN,"b":2}', b'x' * 513):
        with pytest.raises((ValueError, json.JSONDecodeError)):
            worker.parse_strict(raw, {"a", "b"}, 512)


def test_request_scope_rejects_wrong_robot_expired_and_sid(tmp_path, monkeypatch):
    now = datetime.now(timezone.utc)
    monkeypatch.setattr(worker, "sid_for_file", lambda p: "S-1-5-21-999")
    name = "f" * 32
    path = tmp_path / (name + ".json")
    document = {"schema": "cc.v20.control-intent.v1", "request_id": name,
                "robot": "v20-obv", "action": "pause", "confirmed": True,
                "created_at": now.isoformat()}
    path.write_text(json.dumps(document))
    assert worker.validate_request(path, "S-1-5-21-999") == document
    with pytest.raises(ValueError, match="CC07_REQUEST_SID_INVALID"):
        worker.validate_request(path, "S-1-5-21-998")
    document["robot"] = "h1"
    path.write_text(json.dumps(document))
    with pytest.raises(ValueError, match="CC07_REQUEST_SCOPE"):
        worker.validate_request(path, "S-1-5-21-999")


def test_process_one_latches_audit_before_execution_and_blocks_replay(tmp_path, monkeypatch):
    (tmp_path / "processed").mkdir()
    monkeypatch.setattr(worker, "INBOX", tmp_path)
    monkeypatch.setattr(worker, "sid_for_file", lambda p: "S-1-5-21-999")
    name = "e" * 32
    document = {"schema": "cc.v20.control-intent.v1", "request_id": name,
                "robot": "v20-inside", "action": "start", "confirmed": True,
                "created_at": datetime.now(timezone.utc).isoformat()}
    path = tmp_path / (name + ".json")
    path.write_text(json.dumps(document))
    record = []
    monkeypatch.setattr(worker, "log_event", lambda *args: record.append(args))
    replies = []
    monkeypatch.setattr(worker, "publish", lambda *args: replies.append(args))
    executions = []
    monkeypatch.setattr(worker, "invoke_installed", lambda *args:
                        (executions.append(args) or "EXECUTED"))
    cfg = {"panel_sid": "S-1-5-21-999", "operator_sid": "S-1-5-21-777"}
    seen = set()
    worker.process_one(path, cfg, seen)
    assert executions == [(document, "S-1-5-21-777")]
    assert name in seen
    assert record[0] == (name, "v20-inside", "start", "DISPATCH_BEGIN")
    assert replies[0][1]["decision"] == "EXECUTED"
    assert (tmp_path / "processed" / path.name).exists()

    # A crash after durable dispatch-BEGIN but before actual reply must
    # never cause repeated START on restored request file.
    path.write_text(json.dumps(document))
    worker.process_one(path, cfg, seen)
    assert len(executions) == 1
    assert replies[1][1]["decision"] == "FAILED_UNKNOWN"


def test_worker_requires_private_policy_and_no_implicit_release(monkeypatch):
    monkeypatch.setattr(worker, "os", type("FakeOS", (), {"name": "posix", "environ": {}}))
    with pytest.raises(ValueError, match="CC07_WRONG_HOST"):
        worker.policy()
    script=(ROOT / "controller" / "cc07_command_worker.py").read_text()
    assert 'if args.mode == "check":' in script
    assert "cc07_worker_release=not_active" in script
    assert "verify_acl(INBOX, {row[\"panel_sid\"]})" in script
    assert "already_dispatched()" in script
    assert "log_event(rid, robot, action, \"DISPATCH_BEGIN\")" in script
    assert "seen.add(rid)" in script
    assert "if action != \"pause\":" in script
