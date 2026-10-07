from __future__ import annotations

import hashlib
from datetime import datetime, timezone
from decimal import Decimal

import pytest

from TradingSystemLab.stage8_robot.finam_api import FinamOrderRejected
from TradingSystemLab.stage8_robot.production_authorization import (
    OPERATOR_AUTHORIZATION_PHRASE,
    write_authorization,
)
from TradingSystemLab.stage8_robot.production_runtime import InstrumentAuthority
from TradingSystemLab.stage8_robot.production_safety_gate import (
    write_production_heartbeat,
)
from TradingSystemLab.stage8_robot.production_service import (
    ProductionService,
    ProductionServiceFault,
)
from TradingSystemLab.stage8_robot.specification import PRODUCTION_SPECIFICATION_ID
from TradingSystemLab.stage8_robot.strategy_core import SignalIntent
from TradingSystemLab.stage8_robot.trading_safety_gate import write_kill_switch


COMMIT = "b" * 40
ACCOUNT = "REAL-PRODUCTION"
ACCOUNT_HASH = hashlib.sha256(ACCOUNT.encode()).hexdigest()
NOW = datetime(2026, 10, 7, 12, tzinfo=timezone.utc)


class FakeAPI:
    def __init__(self):
        self.calls = []
        self.transaction_rows = []
        self.reject_sltp = False

    def create_session(self):
        self.calls.append(("create_session",))
        return {}

    def session_details(self):
        return {"readonly": False, "account_ids": [ACCOUNT]}

    def account(self, account_id):
        return {
            "account_id": account_id,
            "type": "UNION",
            "status": "ACCOUNT_ACTIVE",
            "equity": {"value": "100000"},
            "unrealized_profit": {"value": "0"},
            "positions": [],
            "portfolio_mc": {
                "available_cash": {"value": "1000000"},
                "initial_margin": {"value": "0"},
                "maintenance_margin": {"value": "0"},
            },
        }

    def transactions(self, account_id, start, end, limit=1000):
        self.calls.append(("transactions", start, end, limit))
        return {"transactions": list(self.transaction_rows)}

    def orders(self, account_id):
        return {"orders": []}

    def place_order(self, account_id, payload):
        self.calls.append(("place_order", payload))
        return {
            "order_id": f"O{len(self.calls)}",
            "status": "ORDER_STATUS_NEW",
            "order": dict(payload),
        }

    def place_sltp_order(self, account_id, payload):
        self.calls.append(("place_sltp_order", payload))
        if self.reject_sltp:
            raise FinamOrderRejected(400)
        return {
            "order_id": "SL1",
            "status": "ORDER_STATUS_WATCHING",
            "sltp_order": dict(payload),
        }


def authorize(root):
    return write_authorization(
        root,
        accepted_commit=COMMIT,
        account_hash=ACCOUNT_HASH,
        operator_authorization_phrase=OPERATOR_AUTHORIZATION_PHRASE,
        now=NOW,
    )


def service(tmp_path, api=None):
    authorize(tmp_path)
    api = api or FakeAPI()
    value = ProductionService(
        runtime_root=tmp_path,
        data_root=tmp_path / "data",
        api=api,
        account_id=ACCOUNT,
        accepted_commit=COMMIT,
        clock=lambda: NOW,
        sleeper=lambda _: None,
    )
    value.transport.connect()
    return value, api


def authority():
    return InstrumentAuthority(
        "USDRUBF",
        "USDRUBF@RTSX",
        Decimal("0.01"),
        Decimal("10"),
        1,
        Decimal("100"),
        Decimal("100"),
    )


def signal():
    return SignalIntent(
        signal_id="signal-1",
        trade_id="trade-1",
        instrument="USDRUBF",
        direction="LONG",
        timestamp=NOW,
        entry=100.0,
        initial_stop=99.95,
        initial_r=0.05,
        canonical_stop=99.95,
    )


def healthy_entry_gate(root):
    write_production_heartbeat(
        root,
        accepted_commit=COMMIT,
        account_hash=ACCOUNT_HASH,
        reconciliation_status="PASS",
        unresolved_intent_count=0,
        health_status="HEALTHY",
        cycle_count=1,
        last_api_contact=NOW,
        position_protection=[],
        broker_open_position_count=0,
        now=NOW,
    )
    write_kill_switch(root, "ARMED", allow_arm=True, now=NOW)


def test_authorized_entry_submission_requires_preexisting_healthy_gate(tmp_path):
    svc, api = service(tmp_path)
    try:
        budget = svc.runtime.begin_batch(
            realized_equity=Decimal("100000"),
            available_cash=Decimal("1000000"),
        )
        action = svc.runtime.plan_entry(
            signal(), authority(),
            realized_equity=Decimal("100000"),
            budget=budget,
        )
        intent = svc.runtime.store.intent(action.idempotency_key)
        with pytest.raises(
            ProductionServiceFault,
            match="STAGE8_12_4_ENTRY_GATE_BLOCKED",
        ):
            svc._submit_intent(
                {"idempotency_key": action.idempotency_key, **intent},
                now=NOW,
                broker_positions_map={name: 0 for name in svc.runtime.spec.instruments},
                allow_entry=True,
            )
        assert not [call for call in api.calls if call[0] == "place_order"]
    finally:
        svc.close()


def test_healthy_armed_entry_persists_before_single_post(tmp_path):
    svc, api = service(tmp_path)
    try:
        healthy_entry_gate(tmp_path)
        budget = svc.runtime.begin_batch(
            realized_equity=Decimal("100000"),
            available_cash=Decimal("1000000"),
        )
        action = svc.runtime.plan_entry(
            signal(), authority(),
            realized_equity=Decimal("100000"),
            budget=budget,
        )
        intent = svc.runtime.store.intent(action.idempotency_key)
        svc._submit_intent(
            {"idempotency_key": action.idempotency_key, **intent},
            now=NOW,
            broker_positions_map={name: 0 for name in svc.runtime.spec.instruments},
            allow_entry=True,
        )
        stored = svc.runtime.store.intent(action.idempotency_key)
        assert stored["status"] == "ACK"
        assert stored["broker_order_id"]
        posts = [call for call in api.calls if call[0] == "place_order"]
        assert len(posts) == 1
        assert posts[0][1]["client_order_id"]
    finally:
        svc.close()


def test_external_deposit_blocks_realized_equity_update(tmp_path):
    api = FakeAPI()
    api.transaction_rows = [{"transaction_category": "DEPOSIT"}]
    svc, _ = service(tmp_path, api)
    try:
        with pytest.raises(
            ProductionServiceFault,
            match="UNEXPLAINED_EXTERNAL_CASH_FLOW",
        ):
            svc._financial_authority(api.account(ACCOUNT), NOW)
        assert svc.runtime.current_realized_equity() is None
    finally:
        svc.close()


def test_terminal_initial_stop_rejection_submits_emergency_exit_immediately(tmp_path):
    api = FakeAPI()
    api.reject_sltp = True
    svc, _ = service(tmp_path, api)
    try:
        budget = svc.runtime.begin_batch(
            realized_equity=Decimal("100000"),
            available_cash=Decimal("1000000"),
        )
        entry = svc.runtime.plan_entry(
            signal(), authority(),
            realized_equity=Decimal("100000"),
            budget=budget,
        )
        svc.runtime.store.transition_intent(entry.idempotency_key, "ACK", "ENTRY1")
        stop = svc.runtime.confirm_entry_position(
            entry.idempotency_key, entry.expected_position_quantity
        )
        stop_intent = svc.runtime.store.intent(stop.idempotency_key)
        broker_positions_map = {
            name: (entry.expected_position_quantity if name == "USDRUBF" else 0)
            for name in svc.runtime.spec.instruments
        }
        with pytest.raises(
            ProductionServiceFault,
            match="PROTECTIVE_STOP_INSTALL_REJECTED_EMERGENCY_EXIT_SUBMITTED",
        ):
            svc._submit_intent(
                {"idempotency_key": stop.idempotency_key, **stop_intent},
                now=NOW,
                broker_positions_map=broker_positions_map,
                allow_entry=False,
            )
        sl_posts = [call for call in api.calls if call[0] == "place_sltp_order"]
        emergency_posts = [call for call in api.calls if call[0] == "place_order"]
        assert len(sl_posts) == 1
        assert len(emergency_posts) == 1
        unresolved = svc.runtime.store.unresolved_intents()
        assert len(unresolved) == 1
        assert unresolved[0]["payload"]["kind"] == "EMERGENCY_EXIT_REQUIRED"
        assert unresolved[0]["status"] == "ACK"
    finally:
        svc.close()


def test_orphaned_persisted_entry_is_never_auto_submitted_after_restart(tmp_path):
    svc, api = service(tmp_path)
    try:
        budget = svc.runtime.begin_batch(
            realized_equity=Decimal("100000"),
            available_cash=Decimal("1000000"),
        )
        svc.runtime.plan_entry(
            signal(), authority(),
            realized_equity=Decimal("100000"),
            budget=budget,
        )
        with pytest.raises(
            ProductionServiceFault,
            match="ORPHANED_ENTRY_INTENT_REQUIRES_OPERATOR",
        ):
            svc._settle_unresolved(NOW)
        assert not [call for call in api.calls if call[0] == "place_order"]
    finally:
        svc.close()
