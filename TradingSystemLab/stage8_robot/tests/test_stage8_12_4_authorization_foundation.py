from __future__ import annotations

import hashlib
from datetime import datetime, timezone
from decimal import Decimal
from pathlib import Path

import pytest

from TradingSystemLab.stage8_robot.live_execution import (
    AuthorizedFinamProductionTransport,
    LiveExecutionError,
)
from TradingSystemLab.stage8_robot.operations import write_heartbeat
from TradingSystemLab.stage8_robot.production_authorization import (
    OPERATOR_AUTHORIZATION_PHRASE,
    ProductionAuthorizationError,
    STAGE8_12_2_EVIDENCE_SHA256,
    STAGE8_12_3_EVIDENCE_SHA256,
    load_authorization,
    write_authorization,
)
from TradingSystemLab.stage8_robot.production_runtime import RuntimeAction
from TradingSystemLab.stage8_robot.specification import (
    ACTIVE_IDENTITY,
    PRODUCTION_SPECIFICATION_ID,
)
from TradingSystemLab.stage8_robot.trading_safety_gate import write_kill_switch


COMMIT = "a" * 40
ACCOUNT = "PRODUCTION-ACCOUNT"
ACCOUNT_HASH = hashlib.sha256(ACCOUNT.encode("utf-8")).hexdigest()
NOW = datetime(2026, 10, 7, 12, 0, tzinfo=timezone.utc)


def authorize(root: Path):
    return write_authorization(
        root,
        accepted_commit=COMMIT,
        account_hash=ACCOUNT_HASH,
        operator_authorization_phrase=OPERATOR_AUTHORIZATION_PHRASE,
        now=NOW,
    )


def healthy_heartbeat(root: Path):
    write_heartbeat(
        root / "diagnostics" / "stage8-heartbeat.json",
        mode="REAL_READONLY",
        production_id=PRODUCTION_SPECIFICATION_ID,
        account_hash=ACCOUNT_HASH,
        last_completed_h1="2026-10-07T10:00:00+00:00",
        last_api_contact=NOW.isoformat(),
        reconciliation_status="PASS",
        entries_enabled=False,
        unresolved_order_count=0,
        health_status="HEALTHY",
        failure_code=None,
        consecutive_failures=0,
        cycle_count=1,
    )


class FakeAPI:
    def __init__(self):
        self.calls = []

    def create_session(self):
        self.calls.append(("create_session",))
        return {}

    def session_details(self):
        self.calls.append(("session_details",))
        return {"readonly": False, "account_ids": [ACCOUNT]}

    def account(self, account_id):
        self.calls.append(("account", account_id))
        return {"status": "ACCOUNT_ACTIVE", "positions": []}

    def place_order(self, account_id, payload):
        self.calls.append(("place_order", account_id, payload))
        return {"order_id": "ENTRY-1"}

    def place_sltp_order(self, account_id, payload):
        self.calls.append(("place_sltp_order", account_id, payload))
        return {"order_id": "STOP-1"}

    def cancel_order(self, account_id, order_id):
        self.calls.append(("cancel_order", account_id, order_id))
        return {"order_id": order_id, "status": "ORDER_STATUS_CANCELLED"}


def entry_action(direction="LONG"):
    return RuntimeAction(
        "ENTRY",
        "stage8.12:test-trade:entry",
        "USDRUBF",
        "USDRUBF@RTSX",
        direction,
        2,
        "test-trade",
        "test-signal",
        Decimal("100"),
        Decimal("99.95") if direction == "LONG" else Decimal("100.05"),
        2 if direction == "LONG" else -2,
    )


def stop_action(direction="LONG"):
    return RuntimeAction(
        "PROTECTIVE_STOP_INSTALL",
        "stage8.12:test-trade:stop:0000",
        "USDRUBF",
        "USDRUBF@RTSX",
        direction,
        2,
        "test-trade",
        "test-signal",
        Decimal("100"),
        Decimal("99.95") if direction == "LONG" else Decimal("100.05"),
        2 if direction == "LONG" else -2,
    )


def emergency_action(direction="LONG"):
    return RuntimeAction(
        "EMERGENCY_EXIT_REQUIRED",
        "stage8.12:test-trade:emergency-exit",
        "USDRUBF",
        "USDRUBF@RTSX",
        direction,
        2,
        "test-trade",
        "test-signal",
        Decimal("99.95"),
        Decimal("99.95"),
        0,
        "PROTECTIVE_STOP_DIVERGENCE_POSITION_STILL_OPEN",
    )


def test_authorization_requires_exact_operator_phrase_and_external_path(tmp_path):
    with pytest.raises(
        ProductionAuthorizationError,
        match="STAGE8_12_4_EXPLICIT_OPERATOR_AUTHORIZATION_REQUIRED",
    ):
        write_authorization(
            tmp_path,
            accepted_commit=COMMIT,
            account_hash=ACCOUNT_HASH,
            operator_authorization_phrase="yes",
            now=NOW,
        )

    with pytest.raises(
        ProductionAuthorizationError,
        match="STAGE8_12_4_REPOSITORY_AUTHORIZATION_FORBIDDEN",
    ):
        write_authorization(
            Path("TradingSystemLab"),
            accepted_commit=COMMIT,
            account_hash=ACCOUNT_HASH,
            operator_authorization_phrase=OPERATOR_AUTHORIZATION_PHRASE,
            now=NOW,
        )


def test_authorization_is_exact_create_only_and_bound_to_evidence(tmp_path):
    record = authorize(tmp_path)
    assert record["production_specification_id"] == PRODUCTION_SPECIFICATION_ID
    assert record["active_identity"] == ACTIVE_IDENTITY
    assert record["accepted_code_commit"] == COMMIT
    assert record["sanitized_account_hash"] == ACCOUNT_HASH
    assert record["stage8_12_2_external_evidence_sha256"] == STAGE8_12_2_EVIDENCE_SHA256
    assert record["stage8_12_3_external_evidence_sha256"] == STAGE8_12_3_EVIDENCE_SHA256
    assert record["execution_authorized"] is True

    loaded = load_authorization(
        tmp_path,
        expected_commit=COMMIT,
        expected_account_hash=ACCOUNT_HASH,
    )
    assert loaded == record
    with pytest.raises(
        ProductionAuthorizationError,
        match="STAGE8_12_4_AUTHORIZATION_BINDING_MISMATCH",
    ):
        load_authorization(
            tmp_path,
            expected_commit="c" * 40,
            expected_account_hash=ACCOUNT_HASH,
        )
    with pytest.raises(
        ProductionAuthorizationError,
        match="STAGE8_12_4_AUTHORIZATION_ALREADY_EXISTS",
    ):
        write_authorization(
            tmp_path,
            accepted_commit=COMMIT,
            account_hash=ACCOUNT_HASH,
            operator_authorization_phrase=OPERATOR_AUTHORIZATION_PHRASE,
            now=datetime(2026, 10, 7, 12, 1, tzinfo=timezone.utc),
        )


def test_live_transport_is_inert_without_durable_authorization(tmp_path):
    api = FakeAPI()
    with pytest.raises(
        ProductionAuthorizationError,
        match="STAGE8_12_4_AUTHORIZATION_MISSING",
    ):
        AuthorizedFinamProductionTransport(
            api=api,
            account_id=ACCOUNT,
            runtime_root=tmp_path,
            accepted_commit=COMMIT,
        )
    assert api.calls == []


def test_entry_requires_armed_fresh_exact_gate_and_uses_day_market_payload(tmp_path):
    authorize(tmp_path)
    healthy_heartbeat(tmp_path)
    write_kill_switch(tmp_path, "ARMED", allow_arm=True, now=NOW)
    api = FakeAPI()
    transport = AuthorizedFinamProductionTransport(
        api=api,
        account_id=ACCOUNT,
        runtime_root=tmp_path,
        accepted_commit=COMMIT,
    )
    transport.connect()
    response = transport.submit_entry(entry_action(), now=NOW)
    assert response["order_id"] == "ENTRY-1"
    payload = [call[2] for call in api.calls if call[0] == "place_order"][-1]
    assert payload["symbol"] == "USDRUBF@RTSX"
    assert payload["quantity"] == {"value": "2"}
    assert payload["side"] == "SIDE_BUY"
    assert payload["type"] == "ORDER_TYPE_MARKET"
    assert payload["time_in_force"] == "TIME_IN_FORCE_DAY"
    assert len(payload["client_order_id"]) <= 20
    assert payload["client_order_id"].isalnum()


def test_halted_blocks_entry_but_not_protection_or_emergency_exit(tmp_path):
    authorize(tmp_path)
    healthy_heartbeat(tmp_path)
    write_kill_switch(tmp_path, "HALTED", now=NOW)
    api = FakeAPI()
    transport = AuthorizedFinamProductionTransport(
        api=api,
        account_id=ACCOUNT,
        runtime_root=tmp_path,
        accepted_commit=COMMIT,
    )
    transport.connect()

    with pytest.raises(
        LiveExecutionError,
        match="STAGE8_12_4_ENTRY_GATE_BLOCKED",
    ):
        transport.submit_entry(entry_action(), now=NOW)
    assert not [call for call in api.calls if call[0] == "place_order"]

    stop = transport.submit_protective_stop(
        stop_action(), observed_position_quantity=2
    )
    assert stop["order_id"] == "STOP-1"
    payload = [call[2] for call in api.calls if call[0] == "place_sltp_order"][-1]
    assert payload["side"] == "SIDE_SELL"
    assert payload["quantity_sl"] == {"value": "100"}
    assert payload["sl_qty_measure"] == "SLTP_QTY_MEASURE_PERCENT"
    assert payload["valid_before"] == "VALID_BEFORE_GOOD_TILL_CANCEL"
    assert payload["sl_price"] == {"value": "99.95"}
    assert "quantity_tp" not in payload
    assert "tp_price" not in payload
    assert "schema_id" not in payload
    assert payload["client_order_id"].isalnum()

    result = transport.submit_emergency_exit(
        emergency_action(), observed_position_quantity=2
    )
    assert result["order_id"] == "ENTRY-1"
    exit_payload = [call[2] for call in api.calls if call[0] == "place_order"][-1]
    assert exit_payload["side"] == "SIDE_SELL"
    assert exit_payload["time_in_force"] == "TIME_IN_FORCE_DAY"


def test_protective_stop_requires_exact_position_and_cancel_requires_flat(tmp_path):
    authorize(tmp_path)
    api = FakeAPI()
    transport = AuthorizedFinamProductionTransport(
        api=api,
        account_id=ACCOUNT,
        runtime_root=tmp_path,
        accepted_commit=COMMIT,
    )
    transport.connect()
    with pytest.raises(
        LiveExecutionError,
        match="STAGE8_12_4_PROTECTIVE_STOP_POSITION_NOT_EXACT",
    ):
        transport.submit_protective_stop(
            stop_action(), observed_position_quantity=0
        )
    with pytest.raises(
        LiveExecutionError,
        match="STAGE8_12_4_PROTECTIVE_STOP_CANCEL_REQUIRES_FLAT",
    ):
        transport.cancel_protective_stop_after_flat(
            "STOP-1", observed_position_quantity=2
        )
    cancelled = transport.cancel_protective_stop_after_flat(
        "STOP-1", observed_position_quantity=0
    )
    assert cancelled["order_id"] == "STOP-1"
