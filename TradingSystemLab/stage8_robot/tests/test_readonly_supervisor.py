import json
import sqlite3
from datetime import datetime, timezone

import pytest

from TradingSystemLab.stage8_robot.operations import InstanceLock
from TradingSystemLab.stage8_robot.readonly_supervisor import (
    ReadonlySupervisor,
    SafetyFault,
    _authenticated_registry,
    _required_environment,
    run_from_environment,
)
from TradingSystemLab.stage8_robot.specification import INSTRUMENTS


ACCOUNT = "real-account-test-only"
SECRET = "unit-test-secret"
ENV = {"FINAM_MODE": "REAL_READONLY", "NEW_ENTRIES_DISABLED": "true",
       "FINAM_API_SECRET": SECRET, "FINAM_REAL_ACCOUNT_ID": ACCOUNT}
NOW = datetime(2026, 1, 5, 12, 30, tzinfo=timezone.utc)


class ReadonlyFake:
    order_call_count = 0

    def __init__(self, _secret=SECRET, *, positions=None, orders=None, failures=0):
        self.positions = [] if positions is None else positions
        self.active_orders = [] if orders is None else orders
        self.failures = failures
        self.created = 0

    def create_session(self):
        self.created += 1
        return {}

    def session_details(self):
        if self.failures:
            self.failures -= 1
            raise ConnectionError("sensitive transport body must not escape")
        return {"readonly": True, "account_ids": [ACCOUNT]}

    def account(self, account):
        assert account == ACCOUNT
        return {"status": "ACCOUNT_ACTIVE", "positions": self.positions}

    def orders(self, account):
        assert account == ACCOUNT
        return {"orders": self.active_orders}

    def bars(self, symbol, start, end):
        assert symbol.endswith("@RTSX") and start and end
        return {"bars": [
            {"timestamp": "2026-01-05T10:00:00Z", "close": "1"},
            {"timestamp": "2999-01-05T12:00:00Z", "close": "2"},
        ]}

    def place_order(self, *_args, **_kwargs):
        type(self).order_call_count += 1
        pytest.fail("order transmission reached")

    submit_order = place_order
    cancel_order = place_order


def supervisor(tmp_path, api=None, **kwargs):
    return ReadonlySupervisor(tmp_path, api or ReadonlyFake(), ACCOUNT, _authenticated_registry(),
                              poll_seconds=30, clock=lambda: NOW, sleeper=lambda _seconds: None, **kwargs)


def test_startup_environment_gates():
    assert _required_environment(ENV) == (SECRET, ACCOUNT)
    for key, value, code in (
        ("FINAM_MODE", "LIVE", "FINAM_REAL_READONLY_MODE_REQUIRED"),
        ("NEW_ENTRIES_DISABLED", "false", "NEW_ENTRIES_DISABLED_REQUIRED"),
        ("FINAM_API_SECRET", "", "FINAM_API_SECRET_MISSING"),
        ("FINAM_REAL_ACCOUNT_ID", "", "FINAM_REAL_ACCOUNT_ID_MISSING"),
    ):
        bad = {**ENV, key: value}
        with pytest.raises(SafetyFault, match=code):
            _required_environment(bad)


def test_once_clean_account_persists_only_completed_n4_and_sanitized_heartbeat(tmp_path):
    ReadonlyFake.order_call_count = 0
    assert run_from_environment(tmp_path, once=True, poll_seconds=30,
                                api_factory=ReadonlyFake, environment=ENV) == 0
    heartbeat_text = (tmp_path / "diagnostics/stage8-heartbeat.json").read_text()
    heartbeat = json.loads(heartbeat_text)
    assert heartbeat["entries_enabled"] is False
    assert heartbeat["reconciliation_status"] == "PASS"
    assert heartbeat["last_completed_h1_timestamp"] == "2026-01-05T11:00:00+00:00"
    assert len(heartbeat["account_hash"]) == 64
    assert ACCOUNT not in heartbeat_text and SECRET not in heartbeat_text
    log_text = (tmp_path / "logs/stage8-readonly.log").read_text()
    assert ACCOUNT not in log_text and SECRET not in log_text
    assert ReadonlyFake.order_call_count == 0
    with sqlite3.connect(tmp_path / "state/readonly-supervisor.sqlite3") as db:
        values = dict(db.execute("SELECT key,value FROM operational_state"))
        assert {key for key in values if key.startswith("h1:")} == {f"h1:{name}" for name in INSTRUMENTS}
        assert set(values[key] for key in values if key.startswith("h1:")) == {"2026-01-05T11:00:00+00:00"}
        assert db.execute("PRAGMA integrity_check").fetchone()[0] == "ok"


def test_second_instance_is_blocked(tmp_path):
    lock = InstanceLock(tmp_path / "state/stage8-readonly.lock").acquire()
    try:
        with pytest.raises(RuntimeError, match="SECOND_ROBOT_INSTANCE_BLOCKED"):
            run_from_environment(tmp_path, once=True, poll_seconds=30,
                                 api_factory=ReadonlyFake, environment=ENV)
    finally:
        lock.release()


@pytest.mark.parametrize(("api", "code"), [
    (ReadonlyFake(positions=[{"symbol": "unexpected"}]), "UNEXPECTED_BROKER_POSITION"),
    (ReadonlyFake(orders=[{"order_id": "unexpected"}]), "UNEXPECTED_ACTIVE_ORDER"),
])
def test_unexpected_broker_state_fails_closed(tmp_path, api, code):
    service = supervisor(tmp_path, api)
    try:
        assert service.run(once=True) == 1
        heartbeat = json.loads((tmp_path / "diagnostics/stage8-heartbeat.json").read_text())
        assert heartbeat["failure_code"] == code
        assert heartbeat["entries_enabled"] is False
        assert heartbeat["unresolved_order_count"] == (1 if code == "UNEXPECTED_ACTIVE_ORDER" else 0)
    finally:
        service.close()


def test_all_four_n4_are_required(tmp_path):
    symbols = _authenticated_registry()
    symbols.pop("IMOEXF")
    service = ReadonlySupervisor(tmp_path, ReadonlyFake(), ACCOUNT, symbols,
                                 poll_seconds=30, clock=lambda: NOW)
    try:
        with pytest.raises(SafetyFault, match="N4_MARKET_DATA_REQUIRED"):
            service.cycle()
    finally:
        service.close()


def test_transient_failure_recovers_and_success_resets_counter(tmp_path):
    api = ReadonlyFake(failures=1)
    service = supervisor(tmp_path, api, max_failures=3, backoff_seconds=0)
    calls = 0

    def stop_after_success(_seconds):
        nonlocal calls
        calls += 1
        if calls == 2:
            raise KeyboardInterrupt

    service.sleeper = stop_after_success
    try:
        with pytest.raises(KeyboardInterrupt):
            service.run()
        assert service.consecutive_failures == 0
        assert service.state.get("consecutive_failures") == "0"
        assert json.loads((tmp_path / "diagnostics/stage8-heartbeat.json").read_text())["health_status"] == "HEALTHY"
    finally:
        service.close()


def test_persistent_api_failure_is_bounded_and_nonzero(tmp_path):
    service = supervisor(tmp_path, ReadonlyFake(failures=99), max_failures=3, backoff_seconds=0)
    try:
        assert service.run() == 1
        heartbeat = json.loads((tmp_path / "diagnostics/stage8-heartbeat.json").read_text())
        assert heartbeat["consecutive_failures"] == 3
        assert heartbeat["failure_code"] == "FINAM_OPERATIONAL_CYCLE_FAILED"
    finally:
        service.close()


def test_restart_loads_prior_operational_state_and_database_remains_valid(tmp_path):
    first = supervisor(tmp_path)
    try:
        first.cycle()
        assert first.cycle_count == 1
    finally:
        first.close()
    second = supervisor(tmp_path)
    try:
        assert second.cycle_count == 1
        second.cycle()
        assert second.cycle_count == 2
    finally:
        second.close()
    with sqlite3.connect(tmp_path / "state/readonly-supervisor.sqlite3") as db:
        assert db.execute("PRAGMA integrity_check").fetchone()[0] == "ok"


@pytest.mark.parametrize("seconds", [29, 3601])
def test_poll_interval_bounds(tmp_path, seconds):
    with pytest.raises(ValueError, match="POLL_SECONDS_OUT_OF_RANGE"):
        ReadonlySupervisor(tmp_path, ReadonlyFake(), ACCOUNT, _authenticated_registry(), poll_seconds=seconds)
