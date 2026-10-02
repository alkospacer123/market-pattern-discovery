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
    newest_expected_h1_close,
    run_from_environment,
    trading_h1_windows,
)
from TradingSystemLab.stage8_robot.specification import INSTRUMENTS


ACCOUNT = "real-account-test-only"
SECRET = "unit-test-secret"
ENV = {"FINAM_MODE": "REAL_READONLY", "NEW_ENTRIES_DISABLED": "true",
       "FINAM_API_SECRET": SECRET, "FINAM_REAL_ACCOUNT_ID": ACCOUNT}
NOW = datetime(2026, 1, 5, 12, 30, tzinfo=timezone.utc)


class ReadonlyFake:
    order_call_count = 0

    def __init__(self, _secret=SECRET, *, positions=None, orders=None, failures=0,
                 bar_opens=None, schedules=None):
        self.positions = [] if positions is None else positions
        self.active_orders = [] if orders is None else orders
        self.failures = failures
        self.created = 0
        self.bar_opens = bar_opens or {}
        self.schedules = schedules or {}
        self.called = []

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
        self.called.append("bars")
        assert symbol.endswith("@RTSX") and start and end
        opens = self.bar_opens.get(symbol, ["2026-01-05T11:00:00Z"])
        if isinstance(opens, str):
            opens = [opens]
        return {"bars": [{"timestamp": value, "close": "1"} for value in opens]}

    def schedule(self, symbol):
        self.called.append("schedule")
        return self.schedules.get(symbol, {"sessions": [{"type": "CORE_TRADING", "interval": {
            "start_time": "2026-01-05T07:00:00Z", "end_time": "2026-01-05T20:50:00Z"}}]})

    def place_order(self, *_args, **_kwargs):
        type(self).order_call_count += 1
        pytest.fail("order transmission reached")

    submit_order = place_order
    cancel_order = place_order
    modify_order = place_order


def supervisor(tmp_path, api=None, **kwargs):
    return ReadonlySupervisor(tmp_path, api or ReadonlyFake(), ACCOUNT, _authenticated_registry(),
                              poll_seconds=30, clock=lambda: NOW, sleeper=lambda _seconds: None,
                              **kwargs)


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
                                api_factory=ReadonlyFake, environment=ENV, clock=lambda: NOW) == 0
    heartbeat_text = (tmp_path / "diagnostics/stage8-heartbeat.json").read_text()
    heartbeat = json.loads(heartbeat_text)
    assert heartbeat["entries_enabled"] is False
    assert heartbeat["reconciliation_status"] == "PASS"
    assert heartbeat.get("failure_code") is None
    assert heartbeat["last_completed_h1_timestamp"] == "2026-01-05T11:00:00+00:00"
    assert len(heartbeat["account_hash"]) == 64
    assert ACCOUNT not in heartbeat_text and SECRET not in heartbeat_text
    log_text = (tmp_path / "logs/stage8-readonly.log").read_text()
    assert ACCOUNT not in log_text and SECRET not in log_text
    assert ReadonlyFake.order_call_count == 0
    with sqlite3.connect(tmp_path / "state/readonly-supervisor.sqlite3") as db:
        values = dict(db.execute("SELECT key,value FROM operational_state"))
        assert sum(key.startswith("h1:") for key in values) == 4
        assert sum(key.startswith("expected_h1:") for key in values) == 4
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


def test_missing_expected_h1_on_active_schedule_fails_closed_without_increment(tmp_path):
    ReadonlyFake.order_call_count = 0
    api = ReadonlyFake(bar_opens={"GLDRUBF@RTSX": "2026-01-05T10:00:00Z"})
    service = supervisor(tmp_path, api)
    try:
        assert service.run(once=True) == 1
        heartbeat = json.loads((tmp_path / "diagnostics/stage8-heartbeat.json").read_text())
        assert heartbeat["health_status"] == "UNHEALTHY"
        assert heartbeat["reconciliation_status"] == "FAULT"
        assert heartbeat["entries_enabled"] is False
        assert heartbeat["failure_code"] == "STALE_COMPLETED_H1_DATA"
        assert heartbeat["cycle_count"] == 0
        assert service.cycle_count == 0
        assert service.state.get("cycle_count", "0") == "0"
        assert all(service.state.get(f"h1:{name}") is None for name in INSTRUMENTS)
        assert ReadonlyFake.order_call_count == 0
    finally:
        service.close()


def test_closed_schedule_preserves_persisted_expectation_across_restart(tmp_path):
    symbols = _authenticated_registry()
    api = ReadonlyFake()
    first = supervisor(tmp_path, api)
    first.cycle()
    first.close()
    closed = {"sessions": [{"type": "CLOSED", "interval": {
        "start_time": "2026-01-05T20:50:00Z", "end_time": "2026-01-06T04:00:00Z"}}]}
    api.schedules = {symbol: closed for symbol in symbols.values()}
    service = ReadonlySupervisor(tmp_path, api, ACCOUNT, symbols, poll_seconds=30,
                                 clock=lambda: NOW, sleeper=lambda _seconds: None)
    try:
        service.cycle()
        assert service.cycle_count == 2
        assert all(service.state.get(f"expected_h1:{name}") == "2026-01-05T11:00:00+00:00" for name in INSTRUMENTS)
    finally:
        service.close()


def test_cold_start_closed_fails_closed(tmp_path):
    closed = {"sessions": [{"type": "CLOSED", "interval": {
        "start_time": "2026-01-05T00:00:00Z", "end_time": "2026-01-06T00:00:00Z"}}]}
    symbols = _authenticated_registry()
    api = ReadonlyFake(schedules={symbol: closed for symbol in symbols.values()})
    service = supervisor(tmp_path, api)
    try:
        assert service.run(once=True) == 1
        heartbeat = json.loads((tmp_path / "diagnostics/stage8-heartbeat.json").read_text())
        assert heartbeat["failure_code"] == "H1_EXPECTED_COMPLETED_WATERMARK_UNAVAILABLE"
    finally:
        service.close()


def regular_schedule():
    return {"sessions": [
        {"type": "EARLY_TRADING", "interval": {"start_time": "2026-01-05T04:00:00Z", "end_time": "2026-01-05T06:00:00Z"}},
        {"type": "CORE_TRADING", "interval": {"start_time": "2026-01-05T06:00:00Z", "end_time": "2026-01-05T16:00:00Z"}},
        {"type": "LATE_TRADING", "interval": {"start_time": "2026-01-05T16:00:00Z", "end_time": "2026-01-05T20:50:00Z"}},
    ]}


def test_contiguous_grid_active_and_final_partial_bar():
    schedule = regular_schedule()
    assert trading_h1_windows(schedule) == [(datetime(2026, 1, 5, 4, tzinfo=timezone.utc), datetime(2026, 1, 5, 20, 50, tzinfo=timezone.utc))]
    assert newest_expected_h1_close(schedule, datetime(2026, 1, 5, 19, 30, tzinfo=timezone.utc)).hour == 18
    assert newest_expected_h1_close(schedule, datetime(2026, 1, 5, 20, 49, tzinfo=timezone.utc)).hour == 19
    assert newest_expected_h1_close(schedule, datetime(2026, 1, 5, 20, 50, tzinfo=timezone.utc)).hour == 20
    assert newest_expected_h1_close(schedule, datetime(2026, 1, 5, 23, tzinfo=timezone.utc)).hour == 20


def test_auction_and_clearing_never_generate_expectations():
    schedule = {"sessions": [
        {"type": "OPENING_AUCTION", "interval": {"start_time": "2026-01-05T03:30:00Z", "end_time": "2026-01-05T04:00:00Z"}},
        {"type": "CLEARING", "interval": {"start_time": "2026-01-05T14:00:00Z", "end_time": "2026-01-05T14:05:00Z"}},
    ]}
    assert newest_expected_h1_close(schedule, NOW) is None


def test_altered_weekend_schedule_uses_schedule_grid():
    schedule = {"sessions": [{"type": "CORE_TRADING", "interval": {
        "start_time": "2026-01-10T09:00:00Z", "end_time": "2026-01-10T12:20:00Z"}}]}
    assert newest_expected_h1_close(schedule, datetime(2026, 1, 10, 12, 20, tzinfo=timezone.utc)).isoformat() == "2026-01-10T12:00:00+00:00"


@pytest.mark.parametrize("schedule", [
    None,
    {"sessions": [{}]},
    {"sessions": [{"type": "UNKNOWN", "interval": {"start_time": "2026-01-05T04:00:00Z", "end_time": "2026-01-05T05:00:00Z"}}]},
    {"sessions": [{"type": "CORE_TRADING", "interval": {"start_time": "2026-01-05T05:00:00Z", "end_time": "2026-01-05T04:00:00Z"}}]},
    {"sessions": [{"type": "CORE_TRADING", "interval": {"start_time": "2026-01-05T04:30:00Z", "end_time": "2026-01-05T05:30:00Z"}}]},
    {"sessions": [{"type": "CORE_TRADING", "interval": {"start_time": "2026-01-05T04:00:00", "end_time": "2026-01-05T05:00:00"}}]},
])
def test_malformed_or_unsafe_schedule_fails_closed(schedule):
    with pytest.raises(SafetyFault, match="H1_FRESHNESS_SCHEDULE_INVALID"):
        trading_h1_windows(schedule)


def test_newer_pending_bar_cannot_hide_exact_missing_expected(tmp_path):
    observed = datetime(2026, 1, 5, 19, 30, tzinfo=timezone.utc)
    symbols = _authenticated_registry()
    opens = ["2026-01-05T17:00:00Z", "2026-01-05T19:00:00Z"]
    api = ReadonlyFake(bar_opens={symbol: opens for symbol in symbols.values()},
                       schedules={symbol: regular_schedule() for symbol in symbols.values()})
    service = ReadonlySupervisor(tmp_path, api, ACCOUNT, symbols, poll_seconds=30, clock=lambda: observed)
    try:
        assert service.run(once=True) == 1
        assert json.loads((tmp_path / "diagnostics/stage8-heartbeat.json").read_text())["failure_code"] == "STALE_COMPLETED_H1_DATA"
        assert all(service.state.get(f"expected_h1:{name}") is None for name in INSTRUMENTS)
    finally:
        service.close()


def test_off_grid_h1_open_surfaces_distinct_sanitized_safety_fault(tmp_path):
    symbols = _authenticated_registry()
    opens = ["2026-01-05T11:00:00Z", "2026-01-05T11:30:00Z"]
    api = ReadonlyFake(bar_opens={symbol: opens for symbol in symbols.values()})
    service = supervisor(tmp_path, api)
    try:
        assert service.run(once=True) == 1
        heartbeat = json.loads((tmp_path / "diagnostics/stage8-heartbeat.json").read_text())
        assert heartbeat["health_status"] == "UNHEALTHY"
        assert heartbeat["entries_enabled"] is False
        assert heartbeat["failure_code"] == "H1_BAR_OPEN_NOT_WHOLE_HOUR_UTC"
        assert heartbeat["cycle_count"] == 0
        assert all(service.state.get(f"h1:{name}") is None for name in INSTRUMENTS)
    finally:
        service.close()


def test_each_n4_instrument_uses_its_own_schedule(tmp_path):
    symbols = _authenticated_registry()
    schedules = {symbol: regular_schedule() for symbol in symbols.values()}
    special = symbols["IMOEXF"]
    schedules[special] = {"sessions": [{"type": "CORE_TRADING", "interval": {
        "start_time": "2026-01-05T09:00:00Z", "end_time": "2026-01-05T12:20:00Z"}}]}
    bars = {symbol: ["2026-01-05T11:00:00Z"] for symbol in symbols.values()}
    # Only IMOEXF's altered schedule requires the completed partial 12:00 bar.
    api = ReadonlyFake(bar_opens=bars, schedules=schedules)
    service = supervisor(tmp_path, api)
    try:
        assert service.run(once=True) == 1
        assert json.loads((tmp_path / "diagnostics/stage8-heartbeat.json").read_text())["failure_code"] == "STALE_COMPLETED_H1_DATA"
    finally:
        service.close()


def test_fresh_cycle_after_stale_fault_clears_failure(tmp_path):
    api = ReadonlyFake(bar_opens={"USDRUBF@RTSX": "2026-01-05T10:00:00Z"})
    first = supervisor(tmp_path, api)
    try:
        assert first.run(once=True) == 1
    finally:
        first.close()
    api.bar_opens["USDRUBF@RTSX"] = "2026-01-05T11:00:00Z"
    second = supervisor(tmp_path, api)
    try:
        second.cycle()
        heartbeat = json.loads((tmp_path / "diagnostics/stage8-heartbeat.json").read_text())
        assert heartbeat["health_status"] == "HEALTHY"
        assert heartbeat["reconciliation_status"] == "PASS"
        assert heartbeat["consecutive_failures"] == 0
        assert heartbeat.get("failure_code") is None
        assert second.cycle_count == 1
    finally:
        second.close()


@pytest.mark.parametrize("seconds", [29, 3601])
def test_poll_interval_bounds(tmp_path, seconds):
    with pytest.raises(ValueError, match="POLL_SECONDS_OUT_OF_RANGE"):
        ReadonlySupervisor(tmp_path, ReadonlyFake(), ACCOUNT, _authenticated_registry(), poll_seconds=seconds)
