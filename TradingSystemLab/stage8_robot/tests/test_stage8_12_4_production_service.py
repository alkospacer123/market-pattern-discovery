from __future__ import annotations

import ast
from datetime import datetime, timezone
from decimal import Decimal
from pathlib import Path

import pytest

from TradingSystemLab.stage8_robot.live_execution import LiveExecutionError
from TradingSystemLab.stage8_robot.production_runtime import RuntimeAction
from TradingSystemLab.stage8_robot.production_service import (
    MODE,
    STATE_DATABASE,
    ProductionService,
    Snapshot,
)


COMMIT = "a" * 40
ACCOUNT = "synthetic-production-account"


class ReadOnlyGetFakeAPI:
    def __init__(self):
        self.calls = []

    def create_session(self):
        self.calls.append("create_session")
        return {}

    def session_details(self):
        self.calls.append("session_details")
        return {"readonly": False, "account_ids": [ACCOUNT]}

    def account(self, account_id):
        self.calls.append(("account", account_id))
        return {"status": "ACCOUNT_ACTIVE"}


def service(tmp_path, api=None):
    return ProductionService(
        tmp_path,
        tmp_path / "stage5",
        api or ReadOnlyGetFakeAPI(),
        ACCOUNT,
        COMMIT,
    )


def test_package2_service_has_no_direct_finam_order_endpoint_calls():
    source = Path("TradingSystemLab/stage8_robot/production_service.py").read_text()
    tree = ast.parse(source)
    assert "place_order(" not in source
    assert "place_sltp_order(" not in source
    assert "write_authorization" not in source
    assert "write_kill_switch" not in source
    imports = [
        node.module or ""
        for node in ast.walk(tree)
        if isinstance(node, ast.ImportFrom)
    ]
    assert "TradingSystemLab.stage8_robot.strategy_core" not in imports


def test_package2_uses_exact_production_state_and_30_day_h1_authority():
    source = Path("TradingSystemLab/stage8_robot/production_service.py").read_text()
    assert STATE_DATABASE == "stage8-12-production.sqlite3"
    assert 'H1_LOOKBACK_DAYS = 30' in source
    assert "load_stage5_seed_open_h1" in source
    assert "splice_seed_and_finam_open_h1" in source
    assert "newest_expected_h1_close" in source
    assert "T3ContextBuilder" not in source  # ProductionRuntime owns the frozen builder.
    assert "self.runtime.context_builder.build" in source


def test_absent_authorization_never_constructs_order_transport(tmp_path, monkeypatch):
    import TradingSystemLab.stage8_robot.production_service as module

    class BombTransport:
        def __init__(self, **kwargs):
            raise AssertionError("order transport constructed while unauthorized")

    monkeypatch.setattr(module, "AuthorizedFinamProductionTransport", BombTransport)
    api = ReadOnlyGetFakeAPI()
    svc = service(tmp_path, api)
    try:
        svc.authenticate()
        assert svc.transport is None
        assert api.calls == [
            "create_session",
            "session_details",
            ("account", ACCOUNT),
        ]
    finally:
        svc.close()


def test_unauthorized_or_halted_path_cannot_consume_entry_signal(tmp_path, monkeypatch):
    svc = service(tmp_path)
    try:
        svc.transport = None
        monkeypatch.setattr(
            svc.runtime,
            "build_latest_signal",
            lambda *args, **kwargs: (_ for _ in ()).throw(
                AssertionError("signal consumed before authorization/ARM")
            ),
        )
        snap = Snapshot(
            account={},
            positions={},
            orders=[],
            realized_equity=Decimal("100000"),
            available_cash=Decimal("100000"),
            observed_at=datetime(2026, 10, 7, 12, tzinfo=timezone.utc),
        )
        svc._plan_entry({}, snap)
        assert svc.runtime.store.unresolved_intent_count() == 0
    finally:
        svc.close()


def test_realized_equity_authority_excludes_unrealized_and_explained_cash(tmp_path):
    svc = service(tmp_path)
    try:
        svc.runtime.store.put("explained_external_cash_flows", "1000")
        realized = svc._realized_basis({
            "equity": {"value": "11000"},
            "unrealized_profit": {"value": "500"},
        }, {}, [])
        assert realized == Decimal("9500")
        assert svc.runtime.current_realized_equity() == Decimal("9500")
    finally:
        svc.close()


def test_realized_equity_bootstrap_requires_clean_broker_account(tmp_path):
    svc = service(tmp_path)
    try:
        with pytest.raises(
            RuntimeError,
            match="STAGE8_12_4_REALIZED_EQUITY_BOOTSTRAP_REQUIRES_CLEAN_ACCOUNT",
        ):
            svc._realized_basis({
                "equity": {"value": "10000"},
                "unrealized_profit": {"value": "500"},
            }, {"USDRUBF@RTSX": 1}, [])
        assert svc.runtime.current_realized_equity() is None
        assert svc.runtime.store.get("starting_realized_equity") is None
    finally:
        svc.close()


def _entry_action():
    return RuntimeAction(
        "ENTRY",
        "stage8.12:service-test:entry",
        "USDRUBF",
        "USDRUBF@RTSX",
        "LONG",
        1,
        "service-test",
        "service-signal",
        Decimal("100"),
        Decimal("99.95"),
        1,
    )


def _entry_payload(action):
    payload = action.payload()
    payload.update({
        "risk_cash": "1500",
        "actual_initial_loss_cash": "50",
        "loss_per_contract": "50",
        "initial_margin": "100",
        "r15_quantity": 1,
        "margin_quantity": 1,
        "signal_timestamp": "2026-10-07T12:00:00+03:00",
    })
    return payload


def test_position_authority_reconciles_entry_before_orders_converge(tmp_path):
    svc = service(tmp_path)
    action = _entry_action()
    try:
        assert svc.runtime.store.persist_intent(
            action.idempotency_key, _entry_payload(action)
        )
        svc.runtime.store.transition_intent(action.idempotency_key, "SUBMITTED")
        snap = Snapshot(
            account={},
            positions={"USDRUBF@RTSX": 1},
            orders=[],
            realized_equity=Decimal("100000"),
            available_cash=Decimal("100000"),
            observed_at=datetime(2026, 10, 7, 12, tzinfo=timezone.utc),
        )
        svc._reconcile_intents(snap)
        assert svc.runtime.store.intent(action.idempotency_key)["status"] == "RECONCILED"
        assert svc.runtime.open_positions()["USDRUBF"]["quantity"] == 1
        assert svc.runtime.store.unresolved_intent_count() == 1
    finally:
        svc.close()


def test_pre_submit_gate_failure_does_not_create_uncertain_order_state(tmp_path):
    class BlockedTransport:
        def submit_entry(self, action, *, now):
            raise LiveExecutionError("STAGE8_12_4_ENTRY_GATE_BLOCKED:KILL_SWITCH_NOT_ARMED")

    svc = service(tmp_path)
    action = _entry_action()
    try:
        assert svc.runtime.store.persist_intent(
            action.idempotency_key, _entry_payload(action)
        )
        svc.transport = BlockedTransport()
        snap = Snapshot(
            account={},
            positions={},
            orders=[],
            realized_equity=Decimal("100000"),
            available_cash=Decimal("100000"),
            observed_at=datetime(2026, 10, 7, 12, tzinfo=timezone.utc),
        )
        with pytest.raises(LiveExecutionError):
            svc._submit(action, snap)
        assert svc.runtime.store.intent(action.idempotency_key)["status"] == "INTENT_PERSISTED"
    finally:
        svc.close()


def test_service_requires_current_active_session_before_consuming_entry_signal():
    source = Path("TradingSystemLab/stage8_robot/production_service.py").read_text()
    assert "ENTRY_MINIMUM_REMAINING_SESSION = timedelta(minutes=5)" in source
    assert "def _entry_session_ready" in source
    assert "newest_expected_h1_close(schedule, now)" in source
    assert "STAGE8_12_4_ENTRY_H1_NOT_LATEST_CURRENT_SESSION_BAR" in source
    assert "if not self._entry_session_ready(" in source


def test_pending_order_reconciliation_overwrites_healthy_heartbeat():
    source = Path("TradingSystemLab/stage8_robot/production_service.py").read_text()
    assert "def _fault_heartbeat" in source
    assert 'reconciliation_status="FAULT"' in source
    assert 'health_status="UNHEALTHY"' in source
    assert "if action_started or self.runtime.store.unresolved_intent_count():" in source
    assert "if entry_started or self.runtime.store.unresolved_intent_count():" in source


def test_production_runtime_persists_entry_signal_watermark_contract():
    source = Path("TradingSystemLab/stage8_robot/production_runtime.py").read_text()
    assert '"signal_timestamp": signal.timestamp.isoformat()' in source
    assert 'watermark_key = f"last_managed_h1:{payload[\'instrument\']}"' in source
    assert "ENTRY_SIGNAL_WATERMARK_MISMATCH" in source


def test_windows_production_task_is_separate_and_installed_disabled():
    root = Path("TradingSystemLab/stage8_robot/deploy/windows")
    installer = (root / "install-production-task.ps1").read_text()
    launcher = (root / "run-production.ps1").read_text()
    assert 'TradingSystemLab-Stage8-Production' in installer
    assert 'TradingSystemLab-Stage8-Readonly' in installer
    assert "READONLY_TASK_MUST_REMAIN_DISABLED" in installer
    assert "Disable-ScheduledTask" in installer
    assert "Start-ScheduledTask" not in installer
    assert "Enable-ScheduledTask" not in installer
    assert "write_authorization" not in installer
    assert "write_kill_switch" not in installer
    assert "run-readonly.ps1" not in launcher
    assert "trading-credential-store.ps1" in launcher
    assert '$env:FINAM_MODE = "STAGE8_12_PRODUCTION"' in launcher
    assert "--accepted-commit" in launcher
    assert "--stage5-data-root" in launcher
    assert "ExpectedCommit" in launcher
    assert "STAGE8_12_4_PRODUCTION_COMMIT_MISMATCH" in launcher
    assert "-ExpectedCommit $commit" in installer
    assert "STAGE8_12_4_PRODUCTION_TASK_PRINCIPAL_MISMATCH" in installer
    assert "--once" in launcher
    assert "50f1fd2178c18b7ab3bd969be82ad01f47a34745" in launcher


def test_package2_mode_is_not_legacy_readonly():
    assert MODE == "STAGE8_12_PRODUCTION"
