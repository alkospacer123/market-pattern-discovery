"""V20-CC00/01/02 tests: no runtime access, three independent accounts, minimal UI."""
from datetime import datetime, timedelta, timezone
from hashlib import sha256
import json
from pathlib import Path
import pytest
from streamlit.testing.v1 import AppTest
from cc.v20_contract import ROBOTS, LABELS, NAMES, MAX_BYTES, TTL, digest, parse, age, unconnected, heartbeat_health
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
    assert [tab.label for tab in app.tabs] == ["Главная", "Журнал", "Управление"]
    assert not app.sidebar.button and not app.sidebar.radio
    assert len(app.button) == 13  # refresh + 12 CC-07 permanently disabled controls
    assert len(app.metric) == 0
    visible = "\\n".join(str(item.value) for kind in ("markdown", "caption", "info", "warning", "success", "error")
                         for item in getattr(app, kind))
    assert "Позиции · локально" not in visible
    assert "Стопы · локально" not in visible
    assert "Цикл" not in visible
    assert sum("Heartbeat:" in x.value and "НЕТ ДАННЫХ" in x.value for x in app.tabs[0].markdown) == 3
    assert all("UNHEALTHY" not in x.value for x in app.tabs[0].markdown)
    assert any("Последняя проверка: —" in x.value for x in app.caption)
    assert not app.get("plotly_chart")
    assert not app.dataframe
    assert sum("НЕ ПОДКЛЮЧЁН" in x.value for x in app.tabs[0].info) == 3
    assert any("Последние циклы" in x.value for x in app.tabs[1].subheader)
    assert any("Административный оператор пока не подтверждён." in x.value for x in app.tabs[2].info)
    app.run()  # rerun without explicit click must not access any V20 source
    assert not app.exception
    assert len(app.button) == 13  # refresh + 12 CC-07 permanently disabled controls


def test_manual_click_one_acquire_and_no_navigation_reread(monkeypatch):
    import cc.v20_receiver as source
    calls = []
    def fake(now):
        calls.append(True)
        return {r: unconnected(r) for r in ROBOTS}
    monkeypatch.setattr(source, "acquire", fake)
    app = AppTest.from_file(str(ROOT / "v20_app.py"), default_timeout=15).run()
    assert [tab.label for tab in app.tabs] == ["Главная", "Журнал", "Управление"]
    app.run()
    assert calls == []
    assert "v20-last-checked-at" not in app.session_state
    app.button(key="v20-manual-refresh").click().run()
    assert len(calls) == 1
    check_at = app.session_state["v20-last-checked-at"]
    assert check_at.tzinfo is not None
    assert any("Последняя проверка: " in x.value and "МСК" in x.value for x in app.caption)
    app.run()  # even a Streamlit rerun cannot trigger another V20 acquisition
    assert len(calls) == 1
    assert app.session_state["v20-last-checked-at"] == check_at



def test_main_shows_only_current_operational_health_without_trade_metrics():
    now = datetime.now(timezone.utc)
    states = {r: unconnected(r) for r in ROBOTS}
    states["V20_SHALLOW"] = parse(wire(example("V20_SHALLOW", now)),
                                  "V20_SHALLOW", now, "V20-SHALLOW")
    states["V20_OBV"] = parse(wire(example("V20_OBV", now - timedelta(seconds=TTL + 5))),
                             "V20_OBV", now, "V20-OBV")
    app = AppTest.from_file(str(ROOT / "v20_app.py"), default_timeout=15)
    app.session_state["v20-snapshots"] = states
    app.run()
    assert not app.exception
    assert len(app.metric) == 0
    visible = "\\n".join(str(item.value) for kind in ("markdown", "caption", "info", "warning", "success", "error")
                         for item in getattr(app, kind))
    assert "Windows Task" in visible and "RUNNING" in visible
    assert "Kill switch" in visible and "ARMED" in visible
    assert "Последняя ошибка: нет" not in visible  # no filler when no error
    assert "Heartbeat:" in visible
    heartbeat_lines = [x.value for x in app.tabs[0].markdown if "Heartbeat:" in x.value]
    assert len(heartbeat_lines) == 3
    assert any("🟢 HEALTHY" in x for x in heartbeat_lines)
    assert any("🔴 UNHEALTHY" in x for x in heartbeat_lines)
    assert any("⚪ НЕТ ДАННЫХ" in x for x in heartbeat_lines)
    assert all("STALE" not in x and "UNKNOWN" not in x for x in heartbeat_lines)
    assert "Текущее состояние Task/защиты и ошибок не подтверждено" in visible
    assert "Состояние Windows Task и ошибок не подтверждено" in visible
    assert "Позиции · локально" not in visible
    assert "Стопы · локально" not in visible
    assert "Цикл" not in visible
    assert len(app.button) == 13  # refresh + 12 CC-07 permanently disabled controls
    assert [tab.label for tab in app.tabs] == ["Главная", "Журнал", "Управление"]
    assert not app.sidebar.button and not app.sidebar.radio
    assert not app.exception


@pytest.mark.parametrize("case,expected", (
    ("absent", "UNKNOWN"), ("fresh", "HEALTHY"), ("old_heartbeat", "STALE"),
    ("old_source", "STALE"), ("missing_heartbeat", "UNKNOWN"),
    ("failed_task", "HEALTHY"), ("future", "UNKNOWN"),
))
def test_heartbeat_independent_freshness(case, expected):
    now = datetime.now(timezone.utc)
    if case == "absent":
        report = unconnected("V20_SHALLOW")
    else:
        value = example(at=now)
        if case == "old_heartbeat":
            value["heartbeat_at"] = (now - timedelta(seconds=TTL+5)).isoformat()
        elif case == "old_source":
            value["observed_at"] = (now - timedelta(seconds=TTL+5)).isoformat()
            value["heartbeat_at"] = value["observed_at"]
            value["events"][0]["at"] = value["observed_at"]
        elif case == "missing_heartbeat":
            value["heartbeat_at"] = None
        elif case == "failed_task":
            value["task_state"] = "DISABLED"
        report = parse(wire(value), "V20_SHALLOW", now, "V20-SHALLOW")
        if case == "future":
            report["heartbeat_at"] = now + timedelta(seconds=1)
    assert heartbeat_health(report, now) == expected


def test_no_false_top_update_from_opening_tabs_or_rerun():
    app = AppTest.from_file(str(ROOT / "v20_app.py"), default_timeout=15).run()
    assert not app.exception
    assert "v20-last-checked-at" not in app.session_state
    assert any("Последняя проверка: —" in x.value for x in app.caption)
    app.run()
    assert not app.exception
    assert "v20-last-checked-at" not in app.session_state


def test_staging_overview_compact_and_robot_only_journal():
    now = datetime.now(timezone.utc)
    states = {robot: dict(unconnected(robot), status="STAGING",
                          reason="VERIFIED_OPERATOR_STAGING", observed_at=now,
                          task_state="DISABLED", workers_observed=0,
                          last_error_code="UNKNOWN") for robot in ROBOTS}
    app = AppTest.from_file(str(ROOT / "v20_app.py"), default_timeout=15)
    app.session_state["v20-snapshots"] = states
    app.run()
    assert not app.exception
    overview = app.tabs[0]
    journal = app.tabs[1]
    assert len(overview.info) == 3
    assert all("STAGING · LIVE OFF" in item.value for item in overview.info)
    assert sum("**Windows Task:** DISABLED" in item.value for item in overview.markdown) == 3
    assert sum("Heartbeat:" in item.value for item in overview.markdown) == 3
    assert not any("Worker:" in item.value or "Reconciliation:" in item.value
                   for item in overview.caption)
    assert sum("Worker: 0" in item.value for item in journal.caption) == 3
    assert not any("FINAM READONLY" in item.value or "Деньги PASS" in item.value
                   for item in app.caption)
    assert "v20-finam" not in app.session_state
    assert len(app.button) == 13  # refresh + 12 CC-07 permanently disabled controls


def test_ten_latest_completed_cycles_newest_first():
    now = datetime.now(timezone.utc)
    payload = example(at=now)
    payload["cycle"] = 110
    payload["events"] = [
        dict(at=(now - timedelta(minutes=10 - i)).isoformat(),
             cycle=101 + i, result="PASS" if i < 9 else "FAULT",
             code="NO_SIGNAL" if i < 9 else "SOURCE_UNAVAILABLE")
        for i in range(10)
    ]
    snapshot = parse(wire(payload), "V20_SHALLOW", now, "V20-SHALLOW")
    app = AppTest.from_file(str(ROOT / "v20_app.py"), default_timeout=15)
    app.session_state["v20-snapshots"] = {
        **{robot: unconnected(robot) for robot in ROBOTS},
        "V20_SHALLOW": snapshot,
    }
    app.run()
    assert not app.exception
    assert len(app.tabs[1].dataframe) == 1
    data = app.tabs[1].dataframe[0].value
    assert list(data.columns) == ["Время", "Цикл", "Результат", "Причина"]
    assert data["Цикл"].tolist() == list(range(110, 100, -1))
    assert data["Результат"].tolist()[0] == "FAULT"
    assert data["Причина"].tolist()[0] == "SOURCE_UNAVAILABLE"
    assert "FINAM READONLY" not in str(data)


def test_manual_refresh_does_not_read_broker_history(monkeypatch):
    import cc.v20_receiver as source
    import cc.v20_staging as staging
    import cc.v20_finam as broker_history
    def forbidden(*args, **kwargs):
        raise AssertionError("broker history must not be read by V20 dashboard")
    monkeypatch.setattr(broker_history, "acquire", forbidden)
    monkeypatch.setattr(source, "acquire",
                        lambda now: {robot: unconnected(robot) for robot in ROBOTS})
    monkeypatch.setattr(staging, "acquire_staging",
                        lambda now: {robot: unconnected(robot) for robot in ROBOTS})
    app = AppTest.from_file(str(ROOT / "v20_app.py"), default_timeout=15).run()
    app.button(key="v20-manual-refresh").click().run()
    assert not app.exception
    assert "v20-finam" not in app.session_state


def test_cc07_buttons_visible_but_all_twelve_inert_and_disabled(monkeypatch):
    """The UI never dispatches, even when an operator visits controls."""
    import cc.v20_receiver as source
    import cc.v20_staging as stage
    import cc.v20_finam as finam
    def forbidden(*args, **kwargs):
        raise AssertionError("disabled operator controls must not touch sources")
    monkeypatch.setattr(source, "acquire", forbidden)
    monkeypatch.setattr(stage, "acquire_staging", forbidden)
    monkeypatch.setattr(finam, "acquire", forbidden)
    app = AppTest.from_file(str(ROOT / "v20_app.py"), default_timeout=15).run()
    assert not app.exception
    assert len(app.button) == 13
    assert app.button(key="v20-manual-refresh").disabled is False
    controls = app.tabs[2].button
    assert len(controls) == 12
    for robot in ROBOTS:
        for action in ("start", "pause", "stop", "restart"):
            key = "cc07-" + robot.lower() + "-" + action
            item = app.button(key=key)
            assert item.disabled is True
            assert item.label == action.upper()
    assert [item.disabled for item in controls] == [True] * 12
    assert "v20-last-checked-at" not in app.session_state
    app.run()
    assert not app.exception
    assert "v20-last-checked-at" not in app.session_state


def test_cc02_armed_unknown_shows_verified_local_cycle_not_broker_health():
    """Real CC-02 ARMED has engine UNKNOWN because FINAM reconciliation is unavailable."""
    now = datetime.now(timezone.utc)
    value = example(at=now - timedelta(seconds=2))
    value.update(engine_state="UNKNOWN", positions_local=None, stops_local=None,
                 unresolved_local=None)
    report = parse(wire(value), "V20_SHALLOW", now, "V20-SHALLOW")
    assert report["status"] == "UNKNOWN"
    app = AppTest.from_file(str(ROOT / "v20_app.py"), default_timeout=15)
    app.session_state["v20-snapshots"] = {
        **{r: unconnected(r) for r in ROBOTS}, "V20_SHALLOW": report
    }
    app.run()
    assert not app.exception
    main = app.tabs[0]
    assert any("ARMED · ЦИКЛ PASS" in x.value for x in main.info)
    assert any("**Windows Task:** RUNNING" in x.value and
               "**Kill switch:** ARMED" in x.value for x in main.markdown)
    assert any("SL/TP FINAM этим снимком не проверены" in x.value
               for x in main.caption)
    assert not any("ARMED · ЦИКЛ PASS" in x.value for x in main.success)


@pytest.mark.parametrize("variant", ("stale", "task_not_running", "cycle_not_verified"))
def test_cc02_armed_never_claims_cycle_without_fresh_trustworthy_local_proof(variant):
    now = datetime.now(timezone.utc)
    value = example(at=now - timedelta(seconds=2))
    value.update(engine_state="UNKNOWN", unresolved_local=None)
    report = parse(wire(value), "V20_SHALLOW", now, "V20-SHALLOW")
    if variant == "stale":
        report["observed_at"] = now - timedelta(seconds=TTL + 5)
        report["heartbeat_at"] = report["observed_at"]
    elif variant == "task_not_running":
        report["task_state"] = "DISABLED"
    else:
        report["events"] = ()
    app = AppTest.from_file(str(ROOT / "v20_app.py"), default_timeout=15)
    app.session_state["v20-snapshots"] = {
        **{r: unconnected(r) for r in ROBOTS}, "V20_SHALLOW": report
    }
    app.run()
    assert not app.exception
    main = app.tabs[0]
    assert not any("ARMED · ЦИКЛ" in x.value for x in main.info)
    assert any("Состояние Windows Task и ошибок не подтверждено" in x.value
               for x in main.caption)
