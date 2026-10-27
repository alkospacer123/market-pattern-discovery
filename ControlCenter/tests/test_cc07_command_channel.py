"""CC-07: GUI intent serialization, strict confirmation and no trade authority."""
import json
import os
from datetime import datetime, timedelta, timezone
from pathlib import Path
from types import SimpleNamespace

import pytest
from streamlit.testing.v1 import AppTest

from cc import v20_command_channel as channel

ROOT = Path(__file__).resolve().parents[1]


def healthy(now):
    return json.dumps({
        "schema": channel.GATEWAY_SCHEMA, "status": "ONLINE",
        "operator_blob": channel.OPERATOR_BLOB,
        "published_at": now.isoformat(),
        "expires_at": (now + timedelta(seconds=15)).isoformat(),
    }).encode("utf-8")


def test_gateway_requires_exact_acl_attested_live_status(monkeypatch):
    now = datetime.now(timezone.utc)
    calls = []
    monkeypatch.setattr(channel, "os", SimpleNamespace(name="nt"))
    monkeypatch.setattr(channel, "read_windows", lambda *a, **k:
                        (calls.append((a, k)) or healthy(now)))
    assert channel.gateway_ready(now) is True
    assert calls[0][0] == (channel.STATUS_ROOT, "gateway.json", 1024)
    assert calls[0][1] == {"admin_policy": True}
    assert channel.gateway_ready(now + timedelta(seconds=31)) is False
    monkeypatch.setattr(channel, "read_windows", lambda *a, **k: b'{"status":"ONLINE"}')
    assert channel.gateway_ready(now) is False
    monkeypatch.setattr(channel, "read_windows", lambda *a, **k: (_ for _ in ()).throw(OSError("denied")))
    assert channel.gateway_ready(now) is False


def test_confirmed_request_is_single_bounded_cc_only_file(tmp_path, monkeypatch):
    now = datetime.now(timezone.utc)
    real_os = os
    fake_os = SimpleNamespace(name="nt", open=real_os.open,
                               fdopen=real_os.fdopen, fsync=real_os.fsync,
                               O_WRONLY=real_os.O_WRONLY,
                               O_CREAT=real_os.O_CREAT, O_EXCL=real_os.O_EXCL)
    monkeypatch.setattr(channel, "os", fake_os)
    monkeypatch.setattr(channel, "REQUEST_ROOT", tmp_path)
    monkeypatch.setattr(channel, "read_windows", lambda *a, **k: healthy(now))
    request_id = "c" * 32
    result = channel.submit("v20-shallow", "pause", "cc07 pause v20-shallow",
                            now=now, id_factory=lambda: request_id)
    assert result == {"decision": "QUEUED_NOT_EXECUTED", "request_id": request_id}
    wire = (tmp_path / (request_id + ".json")).read_bytes()
    row = json.loads(wire)
    assert set(row) == {"schema", "request_id", "robot", "action", "confirmed", "created_at"}
    assert row["schema"] == channel.SCHEMA
    assert row["robot"] == "v20-shallow" and row["action"] == "pause"
    assert len(wire) <= 512
    replay = channel.submit("v20-shallow", "pause", "cc07 pause v20-shallow",
                            now=now, id_factory=lambda: request_id)
    assert replay["decision"] == "REFUSED_INBOX_UNAVAILABLE"
    assert len(list(tmp_path.iterdir())) == 1


@pytest.mark.parametrize("robot,action,phrase,expected", [
    ("wrong", "start", "cc07 start wrong", "REFUSED_INVALID_ROBOT"),
    ("v20-shallow", "unknown", "cc07 unknown v20-shallow", "REFUSED_INVALID_ACTION"),
    ("v20-shallow", "start", "cc07 stop v20-shallow", "REFUSED_CONFIRMATION"),
    ("v20-shallow", "start", "CC07 start v20-shallow", "REFUSED_CONFIRMATION"),
])
def test_invalid_intents_never_write(tmp_path, monkeypatch, robot, action, phrase, expected):
    monkeypatch.setattr(channel, "REQUEST_ROOT", tmp_path)
    assert channel.submit(robot, action, phrase)["decision"] == expected
    assert list(tmp_path.iterdir()) == []


def test_receipts_require_exact_readonly_source_and_schema(monkeypatch):
    now = datetime.now(timezone.utc)
    monkeypatch.setattr(channel, "os", SimpleNamespace(name="nt"))
    rid = "a" * 32
    value = {"schema": channel.RECEIPT_SCHEMA, "request_id": rid,
             "robot": "v20-obv", "action": "pause", "decision": "EXECUTED",
             "observed_at": now.isoformat()}
    seen = []
    def read(*args, **kwargs):
        seen.append((args, kwargs))
        return json.dumps(value).encode()
    monkeypatch.setattr(channel, "read_windows", read)
    assert channel.receipt(rid) == value
    assert seen == [((channel.STATUS_ROOT, "receipt-" + rid + ".json", 1024),
                     {"admin_policy": True})]
    assert channel.receipt("../bad")["decision"] == "RECEIPT_UNAVAILABLE"
    value["decision"] = "ARMED_FROM_UNTRUSTED_SOURCE"
    assert channel.receipt(rid)["decision"] == "RECEIPT_INVALID"


def test_ui_has_no_direct_executor_and_only_confirmed_button_queues(monkeypatch):
    import cc.v20_command_channel as commands
    seen = []
    monkeypatch.setattr(commands, "submit", lambda *args:
                        (seen.append(args) or {"decision": "QUEUED_NOT_EXECUTED",
                                                "request_id": "f" * 32}))
    app = AppTest.from_file(str(ROOT / "v20_app.py"), default_timeout=15)
    app.session_state["cc07-gateway-ready"] = True
    app.run()
    assert not app.exception
    assert len(app.button) == 13
    assert all(button.disabled for button in app.tabs[2].button)
    app.text_input(key="cc07-action-confirm").set_value("cc07 pause v20-obv").run()
    assert not app.exception
    assert app.button(key="cc07-v20_obv-pause").disabled is False
    assert app.button(key="cc07-v20_obv-start").disabled is True
    assert app.button(key="cc07-v20_shallow-pause").disabled is True
    app.button(key="cc07-v20_obv-pause").click().run()
    assert seen == [("v20-obv", "pause", "cc07 pause v20-obv")]
    assert app.session_state["cc07-last-request-id"] == "f" * 32
    assert "queued" not in str(app.session_state.get("cc07-last-receipt", "")).lower()
    source = (ROOT / "v20_app.py").read_text()
    for banned in ("subprocess", "os.system", "start-scheduledtask", "stop-scheduledtask",
                   "finam_live", "cc07-v20-operator.ps1"):
        assert banned not in source.lower()
