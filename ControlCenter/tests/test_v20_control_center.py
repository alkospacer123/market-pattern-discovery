"""V20-CC00/01/02 tests: no runtime access, three independent accounts, minimal UI."""
from datetime import datetime, timedelta, timezone
from hashlib import sha256
import json
from pathlib import Path
import pytest
from streamlit.testing.v1 import AppTest
from cc.v20_contract import ROBOTS, LABELS, NAMES, MAX_BYTES, TTL, digest, parse, age, unconnected
from cc import v20_receiver as receiver

ROOT = Path(__file__).resolve().parents[1]


def example(robot="V20_SHALLOW", at=None):
    now = at or datetime.now(timezone.utc)
    return dict(
        schema_id="cc.v20.readonly.v1", robot_id=robot,
        account_alias="V20-" + robot.split("_")[1],
        observed_at=now.isoformat(), heartbeat_at=now.isoformat(),
        engine_state="HEALTHY", task_state="RUNNING", kill_switch="ARMED",
        cycle=42, positions_local=0, stops_local=0, unresolved_local=0,
        last_error_code="NONE",
        events=[dict(at=now.isoformat(), cycle=42, result="PASS", code="NONE")],
    )


def wire(value):
    return json.dumps({**value, "payload_sha256": digest(value)},
                      ensure_ascii=True, separators=(",", ":")).encode("utf-8")


def test_contract_three_robots_and_unique_fixed_filenames():
    assert ROBOTS == ("V20_SHALLOW", "V20_OBV", "V20_INSIDE")
    assert len(set(NAMES.values())) == len(ROBOTS)
    assert set(LABELS) == set(NAMES) == set(ROBOTS)
    assert all(name.startswith("v20-") and name.endswith(".json") for name in NAMES.values())


def test_protected_policy_unapproved_and_no_runtime_access(monkeypatch):
    def fail(*args, **kwargs):
        raise AssertionError("policy or source cannot be opened")
    monkeypatch.setattr(receiver, "read_windows", fail)
    now = datetime.now(timezone.utc)
    assert all(x["status"] == "NOT_CONNECTED" for x in receiver.acquire(now).values())
    assert all(x["reason"] == "SOURCE_NOT_APPROVED" for x in receiver.acquire(now).values())


@pytest.mark.parametrize("robot", ROBOTS)
def test_valid_own_snapshot_is_never_a_broker_authority(robot):
    now = datetime.now(timezone.utc)
    got = parse(wire(example(robot)), robot, now, "V20-" + robot.split("_")[1])
    assert got["robot_id"] == robot and got["status"] == "HEALTHY"
    assert got["cycle"] == 42 and got["positions_local"] == 0
    assert len(got["events"]) == 1
    assert "broker" not in got and "trading_allowed" not in got


@pytest.mark.parametrize("mutator", (
    lambda x: x.update(robot_id="V20_OBV"),
    lambda x: x.update(account_alias="V20-OTHER"),
    lambda x: x.update(engine_state="INCORRECT"),
    lambda x: x.update(cycle=True),
    lambda x: x.update(cycle=-1),
    lambda x: x.update(positions_local=False),
    lambda x: x.update(last_error_code="SECRET-RAW-ACCOUNT"),
    lambda x: x.update(events=[dict(at=x["observed_at"], cycle=1, result="PASS", code="NONE")]*11),
))
def test_contract_rejects_wrong_identity_types_and_unbounded_events(mutator):
    value = example()
    mutator(value)
    with pytest.raises((ValueError, TypeError)):
        parse(wire(value), "V20_SHALLOW", datetime.now(timezone.utc), "V20-SHALLOW")


def test_corrupt_digest_and_duplicate_keys_rejected():
    now = datetime.now(timezone.utc)
    raw = wire(example())
    with pytest.raises(ValueError, match="HASH_MISMATCH"):
        parse(raw.replace(b'"cycle":42', b'"cycle":43'),
              "V20_SHALLOW", now, "V20-SHALLOW")
    duplicate = raw.replace(b'"cycle":42', b'"cycle":42,"cycle":43')
    with pytest.raises(ValueError, match="DUPLICATE_KEY"):
        parse(duplicate, "V20_SHALLOW", now, "V20-SHALLOW")


def test_too_large_and_naive_time_rejected():
    now = datetime.now(timezone.utc)
    with pytest.raises(ValueError, match="INVALID_SIZE"):
        parse(b"x" * (MAX_BYTES + 1), "V20_SHALLOW", now, "V20-SHALLOW")
    value = example()
    value["observed_at"] = "2026-10-23T10:00:00"
    with pytest.raises(ValueError, match="NAIVE_TIME"):
        parse(wire(value), "V20_SHALLOW", now, "V20-SHALLOW")


def test_unconfirmed_healthy_gates_do_not_go_green():
    now = datetime.now(timezone.utc)
    for name, changed in (("heartbeat_at", None), ("task_state", "DISABLED"),
                          ("kill_switch", "HALTED"), ("unresolved_local", 1)):
        value = example()
        value[name] = changed
        assert parse(wire(value), "V20_SHALLOW", now, "V20-SHALLOW")["status"] == "UNKNOWN"


def test_stale_and_rollback_latched():
    now = datetime.now(timezone.utc)
    old = now - timedelta(seconds=TTL+2)
    report = parse(wire(example(at=old)), "V20_SHALLOW", now, "V20-SHALLOW")
    assert report["status"] == "STALE"
    fresh = parse(wire(example()), "V20_SHALLOW", now, "V20-SHALLOW")
    stale = age(fresh, now + timedelta(seconds=TTL+1))
    assert stale["status"] == "STALE" and stale["cycle"] is None
    assert age(stale, now)["status"] == "STALE"


def test_per_robot_failure_does_not_affect_others(monkeypatch):
    now = datetime.now(timezone.utc)
    policy = dict(schema_id="cc.v20.source-policy.v1", approved=True, root_id=[1,2,3],
                  account_aliases={r: "V20-" + r.split("_")[1] for r in ROBOTS})
    seen = []
    def read(root, filename, maximum, expected_root=None, admin_policy=False):
        seen.append((filename, expected_root, admin_policy))
        if filename == receiver.POLICY_NAME:
            return json.dumps(policy).encode()
        if filename == NAMES["V20_OBV"]:
            raise ValueError("SIMULATED_BAD_SOURCE")
        robot = next(r for r in ROBOTS if NAMES[r] == filename)
        return wire(example(robot))
    monkeypatch.setattr(receiver, "read_windows", read)
    states = receiver.acquire(now)
    assert states["V20_SHALLOW"]["status"] == "HEALTHY"
    assert states["V20_OBV"]["status"] == "NOT_CONNECTED"
    assert states["V20_INSIDE"]["status"] == "HEALTHY"
    assert seen[0][0] == receiver.POLICY_NAME and seen[0][-1] is True
    assert all(x[1:] == ([1,2,3], True) for x in seen[1:])


def test_policy_blocks_cross_robot_alias_and_extra_permissions():
    correct = dict(schema_id="cc.v20.source-policy.v1", approved=True,
                   root_id=[1,2,3],
                   account_aliases={r: "V20-" + r.split("_")[1] for r in ROBOTS})
    receiver.policy_check(correct)
    for wrong in ({**correct, "approved": False},
                  {**correct, "root_id": None},
                  {**correct, "account_aliases": {r:"V20-SHARED" for r in ROBOTS}},
                  {**correct, "credentials": "SECRET"}):
        with pytest.raises(ValueError):
            receiver.policy_check(wrong)


def test_minimal_streamlit_starts_without_read_or_trading_controls(monkeypatch):
    def fail(*args, **kwargs):
        raise AssertionError("startup must not read sources")
    monkeypatch.setattr(receiver, "read_windows", fail)
    app = AppTest.from_file(str(ROOT / "v20_app.py"), default_timeout=15).run()
    assert not app.exception
    assert list(app.radio[0].options) == ["Главная", "Журнал", "Управление"]
    assert len(app.button) == 1
    assert len(app.metric) == 9
    assert not app.get("plotly_chart")
    assert not app.dataframe
    assert sum("НЕ ПОДКЛЮЧЁН" in x.value for x in app.info) == 3
    for tab in ("Журнал", "Управление", "Главная"):
        app.radio[0].set_value(tab).run()
        assert not app.exception
        assert len(app.button) == 1


def test_manual_click_one_acquire_and_no_navigation_reread(monkeypatch):
    import cc.v20_receiver as source
    calls = []
    def fake(now):
        calls.append(True)
        return {r: unconnected(r) for r in ROBOTS}
    monkeypatch.setattr(source, "acquire", fake)
    app = AppTest.from_file(str(ROOT / "v20_app.py"), default_timeout=15).run()
    app.radio[0].set_value("Журнал").run()
    app.radio[0].set_value("Главная").run()
    assert calls == []
    app.button(key="v20-manual-refresh").click().run()
    assert len(calls) == 1
    app.radio[0].set_value("Управление").run()
    app.radio[0].set_value("Главная").run()
    assert len(calls) == 1
