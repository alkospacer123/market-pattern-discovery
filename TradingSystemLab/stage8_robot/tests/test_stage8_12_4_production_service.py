from __future__ import annotations

from datetime import datetime
from decimal import Decimal
from pathlib import Path
from zoneinfo import ZoneInfo

import pandas as pd
import pytest

import TradingSystemLab.stage8_robot.production_service as service_module
from TradingSystemLab.stage8_robot.broker import compact_client_order_id
from TradingSystemLab.stage8_robot.production_runtime import InstrumentAuthority
from TradingSystemLab.stage8_robot.production_service import (
    ProductionService,
    ProductionServiceFault,
)
from TradingSystemLab.stage8_robot.strategy_core import SignalIntent
from TradingSystemLab.stage8_robot.trading_safety_gate import write_kill_switch

UTC = ZoneInfo("UTC")
MSK = ZoneInfo("Europe/Moscow")
NOW = datetime(2026, 10, 7, 12, 0, tzinfo=UTC)
ACCOUNT = "REAL-PRODUCTION-ACCOUNT"
COMMIT = "a" * 40


class FakeHistoryStore:
    def __init__(self, root):
        pass
    def close(self):
        pass


class FakeAPI:
    def __init__(self):
        self.account_data = {
            "account_id": ACCOUNT,
            "type": "FORTS",
            "status": "ACCOUNT_ACTIVE",
            "equity": {"value": "100000"},
            "unrealized_profit": {"value": "0"},
            "positions": [],
            "portfolio_forts": {
                "available_cash": {"value": "1000000"},
                "money_reserved": {"value": "0"},
            },
        }
        self.orders_data = []

    def account(self, account_id):
        assert account_id == ACCOUNT
        return self.account_data

    def orders(self, account_id):
        assert account_id == ACCOUNT
        return {"orders": list(self.orders_data)}


class FakeTransport:
    def __init__(self, *, api, account_id, runtime_root, accepted_commit):
        self.api = api
        self.calls = []

    def connect(self):
        self.calls.append(("connect",))

    def submit_entry(self, action, *, now, state_store):
        assert state_store.intent(action.idempotency_key)["status"] == "INTENT_PERSISTED"
        state_store.transition_intent(action.idempotency_key, "SUBMITTED")
        state_store.transition_intent(action.idempotency_key, "ACK", "ENTRY-1")
        self.api.orders_data.append({
            "order_id": "ENTRY-1",
            "status": "ORDER_STATUS_FILLED",
            "order": {
                "symbol": action.finam_symbol,
                "quantity": {"value": str(action.quantity)},
                "side": "SIDE_BUY" if action.direction == "LONG" else "SIDE_SELL",
                "client_order_id": compact_client_order_id(action.idempotency_key),
            },
        })
        signed = action.quantity if action.direction == "LONG" else -action.quantity
        self.api.account_data["positions"] = [{
            "symbol": action.finam_symbol,
            "quantity": {"value": str(signed)},
        }]
        self.calls.append(("entry", action.instrument, action.quantity))
        return {"order_id": "ENTRY-1"}

    def submit_protective_stop(
        self, action, *, observed_position_quantity, state_store
    ):
        assert state_store.intent(action.idempotency_key)["status"] == "INTENT_PERSISTED"
        state_store.transition_intent(action.idempotency_key, "SUBMITTED")
        state_store.transition_intent(action.idempotency_key, "ACK", "STOP-1")
        self.api.orders_data.append({
            "order_id": "STOP-1",
            "status": "ORDER_STATUS_WATCHING",
            "sltp_order": {
                "symbol": action.finam_symbol,
                "side": "SIDE_SELL" if action.direction == "LONG" else "SIDE_BUY",
                "quantity_sl": {"value": "100.000"},
                "sl_qty_measure": "SLTP_QTY_MEASURE_PERCENT",
                "sl_price": {"value": f"{action.stop_price}0"},
                "valid_before": "VALID_BEFORE_GOOD_TILL_CANCEL",
                "client_order_id": compact_client_order_id(action.idempotency_key),
                "comment": action.idempotency_key,
            },
        })
        self.calls.append(("stop", action.instrument, observed_position_quantity))
        return {"order_id": "STOP-1"}

    def submit_emergency_exit(
        self, action, *, observed_position_quantity, state_store
    ):
        state_store.transition_intent(action.idempotency_key, "SUBMITTED")
        state_store.transition_intent(action.idempotency_key, "ACK", "EXIT-1")
        self.api.orders_data.append({
            "order_id": "EXIT-1",
            "status": "ORDER_STATUS_FILLED",
            "order": {
                "symbol": action.finam_symbol,
                "quantity": {"value": str(action.quantity)},
                "side": "SIDE_SELL" if action.direction == "LONG" else "SIDE_BUY",
                "client_order_id": compact_client_order_id(action.idempotency_key),
            },
        })
        self.api.account_data["positions"] = []
        self.calls.append(("emergency", action.instrument, observed_position_quantity))
        return {"order_id": "EXIT-1"}

    def cancel_protective_stop_after_flat(
        self, broker_order_id, *, observed_position_quantity
    ):
        assert observed_position_quantity == 0
        for row in self.api.orders_data:
            if row["order_id"] == broker_order_id:
                row["status"] = "ORDER_STATUS_CANCELED"
        self.calls.append(("cancel", broker_order_id))
        return {"order_id": broker_order_id}


def authority(instrument):
    values = {
        "USDRUBF": (Decimal("0.01"), Decimal("10")),
        "CNYRUBF": (Decimal("0.001"), Decimal("1")),
        "GLDRUBF": (Decimal("0.1"), Decimal("0.1")),
        "IMOEXF": (Decimal("0.5"), Decimal("5")),
    }
    step, tick = values[instrument]
    return InstrumentAuthority(
        instrument, f"{instrument}@RTSX", step, tick, 1,
        Decimal("1000"), Decimal("1100"),
    )


def frame():
    index = pd.date_range(
        "2026-08-01T00:00:00+03:00",
        periods=900,
        freq="1h",
        tz="Europe/Moscow",
    )
    return pd.DataFrame(
        {"Open": 100.0, "High": 101.0, "Low": 99.0, "Close": 100.0},
        index=index,
    )


def signal():
    return SignalIntent(
        "signal-live", "trade-live", "USDRUBF", "LONG",
        datetime(2026, 10, 7, 13, 0, tzinfo=MSK),
        100.0, 99.0, 1.0, 99.0,
    )


def make_service(tmp_path, monkeypatch):
    api = FakeAPI()
    monkeypatch.setattr(service_module, "ProductionHistoryStore", FakeHistoryStore)
    svc = ProductionService(
        tmp_path, api, ACCOUNT, COMMIT,
        clock=lambda: NOW, sleeper=lambda _: None,
        transport_factory=FakeTransport,
    )
    svc.symbols = {x: f"{x}@RTSX" for x in ("USDRUBF","CNYRUBF","GLDRUBF","IMOEXF")}
    svc.authorities = {x: authority(x) for x in svc.symbols}
    svc._refresh_history = lambda now: {x: frame() for x in svc.symbols}
    write_kill_switch(tmp_path, "HALTED", now=NOW)
    return svc, api


def test_halted_clean_cycle_is_healthy_and_zero_order(tmp_path, monkeypatch):
    svc, _ = make_service(tmp_path, monkeypatch)
    svc.runtime.build_latest_signal = lambda instrument, bars, now: None
    try:
        svc.cycle()
        assert svc.runtime.current_realized_equity() == Decimal("100000")
        assert svc.runtime.open_positions() == {}
        assert not [x for x in svc.transport.calls if x[0] in {"entry","stop","emergency"}]
        assert svc.cycle_count == 1
    finally:
        svc.close()


def test_armed_entry_requires_fill_then_active_initial_stop(tmp_path, monkeypatch):
    svc, _ = make_service(tmp_path, monkeypatch)
    write_kill_switch(tmp_path, "ARMED", allow_arm=True, now=NOW)
    emitted = {"done": False}
    def latest(instrument, bars, now):
        if instrument == "USDRUBF" and not emitted["done"]:
            emitted["done"] = True
            return signal()
        return None
    svc.runtime.build_latest_signal = latest
    try:
        svc.cycle()
        position = svc.runtime.open_positions()["USDRUBF"]
        assert position["quantity"] == 1
        assert position["protective_stop_state"] == "ACTIVE"
        assert position["protective_stop_broker_order_id"] == "STOP-1"
        assert svc.runtime.store.unresolved_intent_count() == 0
        assert [x[0] for x in svc.transport.calls] == ["entry", "stop"]
        heartbeat = (
            tmp_path / "diagnostics" / "stage8-12-4-production-heartbeat.json"
        ).read_text(encoding="utf-8")
        assert '"health_status":"HEALTHY"' in heartbeat
        assert '"instrument":"USDRUBF"' in heartbeat
        assert '"active_stop_order_ids":["STOP-1"]' in heartbeat
    finally:
        svc.close()


def test_persisted_entry_restart_never_auto_retransmits(tmp_path, monkeypatch):
    svc, _ = make_service(tmp_path, monkeypatch)
    action = service_module.RuntimeAction(
        "ENTRY", "stage8.12:restart:entry", "USDRUBF", "USDRUBF@RTSX",
        "LONG", 1, "trade-restart", "signal-restart",
        Decimal("100"), Decimal("99"), 1,
    )
    assert svc.runtime.store.persist_intent(action.idempotency_key, action.payload())
    try:
        with pytest.raises(
            ProductionServiceFault,
            match="PERSISTED_ENTRY_REQUIRES_OPERATOR_RECONCILIATION",
        ):
            svc._reconcile_unresolved({}, [], allow_missing=False)
        assert not [x for x in svc.transport.calls if x[0] == "entry"]
    finally:
        svc.close()


def test_extra_n4_broker_position_fails_closed(tmp_path, monkeypatch):
    svc, _ = make_service(tmp_path, monkeypatch)
    try:
        with pytest.raises(
            ProductionServiceFault,
            match="UNEXPECTED_N4_BROKER_POSITION",
        ):
            svc._position_protection({"USDRUBF@RTSX": 1}, [])
    finally:
        svc.close()


def test_unexplained_realized_basis_change_blocks_cycle(tmp_path, monkeypatch):
    svc, api = make_service(tmp_path, monkeypatch)
    svc.runtime.set_realized_equity(Decimal("100000"))
    api.account_data["equity"] = {"value": "100100"}
    try:
        with pytest.raises(
            ProductionServiceFault,
            match="UNEXPLAINED_REALIZED_EQUITY_DISCREPANCY",
        ):
            svc.cycle()
    finally:
        svc.close()
