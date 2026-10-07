from __future__ import annotations

from datetime import datetime
from decimal import Decimal
from pathlib import Path
from zoneinfo import ZoneInfo

import pandas as pd
import pytest

import TradingSystemLab.stage8_robot.production_service as service_module
from TradingSystemLab.stage8_robot.broker import compact_client_order_id
from TradingSystemLab.stage8_robot.production_runtime import (
    InstrumentAuthority,
    RuntimeAction,
)
from TradingSystemLab.stage8_robot.production_service import (
    ProductionService,
    ProductionServiceFault,
)
from TradingSystemLab.stage8_robot.strategy_core import SignalIntent

UTC = ZoneInfo("UTC")
MSK = ZoneInfo("Europe/Moscow")
NOW = datetime(2026, 10, 7, 12, 0, tzinfo=UTC)
ACCOUNT = "REAL-PRODUCTION-ACCOUNT"


def authority(instrument: str) -> InstrumentAuthority:
    economics = {
        "USDRUBF": (Decimal("0.01"), Decimal("10")),
        "CNYRUBF": (Decimal("0.001"), Decimal("1")),
        "GLDRUBF": (Decimal("0.1"), Decimal("0.1")),
        "IMOEXF": (Decimal("0.5"), Decimal("5")),
    }
    step, tick = economics[instrument]
    return InstrumentAuthority(
        instrument,
        f"{instrument}@RTSX",
        step,
        tick,
        1,
        Decimal("1000"),
        Decimal("1100"),
    )


def signal() -> SignalIntent:
    return SignalIntent(
        signal_id="signal-USDRUBF-live",
        trade_id="trade-USDRUBF-live",
        instrument="USDRUBF",
        direction="LONG",
        timestamp=datetime(2026, 10, 7, 13, 0, tzinfo=MSK),
        entry=100.0,
        initial_stop=99.0,
        initial_r=1.0,
        canonical_stop=99.0,
    )


class FakeHistory:
    def __init__(self, root):
        stamp = pd.date_range(
            "2026-08-01T00:00:00+03:00",
            periods=900,
            freq="1h",
            tz="Europe/Moscow",
        )
        self._frame = pd.DataFrame(
            {
                "Open": [100.0] * len(stamp),
                "High": [101.0] * len(stamp),
                "Low": [99.0] * len(stamp),
                "Close": [100.0] * len(stamp),
            },
            index=stamp,
        )
        self._frame.index.name = "CloseTime"

    def merge_finam_tail(self, **kwargs):
        return NOW

    def frame(self, instrument):
        return self._frame.copy()

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
        self.order_rows = []
        self.calls = []

    def account(self, account_id):
        assert account_id == ACCOUNT
        self.calls.append(("account",))
        return self.account_data

    def orders(self, account_id):
        assert account_id == ACCOUNT
        self.calls.append(("orders",))
        return {"orders": list(self.order_rows)}

    def schedule(self, symbol):
        self.calls.append(("schedule", symbol))
        return {"sessions": []}

    def bars(self, symbol, start, end):
        self.calls.append(("bars", symbol))
        return {"bars": []}


class FakeTransport:
    def __init__(self, *, api, account_id, runtime_root, accepted_commit):
        self.api = api
        self.account_id = account_id
        self.accepted_commit = accepted_commit
        self.calls = []

    def connect(self):
        self.calls.append(("connect",))

    def submit_entry(self, action, *, now, state_store):
        assert state_store.intent(action.idempotency_key)["status"] == "INTENT_PERSISTED"
        state_store.transition_intent(action.idempotency_key, "SUBMITTED")
        broker_id = "ENTRY-1"
        state_store.transition_intent(action.idempotency_key, "ACK", broker_id)
        self.api.order_rows.append({
            "order_id": broker_id,
            "status": "ORDER_STATUS_FILLED",
            "order": {
                "client_order_id": compact_client_order_id(action.idempotency_key),
                "symbol": action.finam_symbol,
            },
        })
        signed = action.quantity if action.direction == "LONG" else -action.quantity
        self.api.account_data["positions"] = [{
            "symbol": action.finam_symbol,
            "quantity": {"value": str(signed)},
        }]
        self.calls.append(("entry", action.instrument, action.quantity))
        return {"order_id": broker_id}

    def submit_protective_stop(
        self, action, *, observed_position_quantity, state_store
    ):
        assert state_store.intent(action.idempotency_key)["status"] == "INTENT_PERSISTED"
        state_store.transition_intent(action.idempotency_key, "SUBMITTED")
        broker_id = "STOP-1"
        state_store.transition_intent(action.idempotency_key, "ACK", broker_id)
        self.api.order_rows.append({
            "order_id": broker_id,
            "status": "ORDER_STATUS_WATCHING",
            "sltp_order": {
                "client_order_id": compact_client_order_id(action.idempotency_key),
                "comment": action.idempotency_key,
                "symbol": action.finam_symbol,
                "side": "SIDE_SELL" if action.direction == "LONG" else "SIDE_BUY",
                "quantity_sl": {"value": "100.000"},
                "sl_qty_measure": "SLTP_QTY_MEASURE_PERCENT",
                "sl_price": {"value": f"{action.stop_price}0"},
            },
        })
        self.calls.append(("stop", action.instrument, observed_position_quantity))
        return {"order_id": broker_id}

    def submit_emergency_exit(
        self, action, *, observed_position_quantity, state_store
    ):
        state_store.transition_intent(action.idempotency_key, "SUBMITTED")
        broker_id = "EXIT-1"
        state_store.transition_intent(action.idempotency_key, "ACK", broker_id)
        self.api.order_rows.append({
            "order_id": broker_id,
            "status": "ORDER_STATUS_FILLED",
            "order": {
                "client_order_id": compact_client_order_id(action.idempotency_key),
                "symbol": action.finam_symbol,
            },
        })
        self.api.account_data["positions"] = []
        self.calls.append(("emergency", action.instrument, observed_position_quantity))
        return {"order_id": broker_id}

    def cancel_protective_stop_after_flat(
        self, broker_order_id, *, observed_position_quantity
    ):
        assert observed_position_quantity == 0
        for row in self.api.order_rows:
            if row["order_id"] == broker_order_id:
                row["status"] = "ORDER_STATUS_CANCELED"
        return {"order_id": broker_order_id}


def make_service(tmp_path, monkeypatch):
    api = FakeAPI()
    monkeypatch.setattr(service_module, "ProductionHistoryCache", FakeHistory)
    monkeypatch.setattr(
        service_module, "AuthorizedFinamProductionTransport", FakeTransport
    )
    svc = ProductionService(
        tmp_path,
        api,
        ACCOUNT,
        "a" * 40,
        clock=lambda: NOW,
        sleeper=lambda _: None,
    )
    svc.symbols = {
        instrument: f"{instrument}@RTSX"
        for instrument in ("USDRUBF", "CNYRUBF", "GLDRUBF", "IMOEXF")
    }
    svc.authorities = {
        instrument: authority(instrument)
        for instrument in svc.symbols
    }
    return svc, api


def test_clean_cycle_initializes_realized_equity_and_sends_zero_orders(
    tmp_path, monkeypatch
):
    svc, api = make_service(tmp_path, monkeypatch)
    svc.runtime.build_latest_signal = lambda instrument, frame, now: None
    try:
        svc.cycle()
        assert svc.runtime.current_realized_equity() == Decimal("100000")
        assert svc.runtime.open_positions() == {}
        assert not [call for call in svc.transport.calls if call[0] in {"entry", "stop", "emergency"}]
        assert svc.cycle_count == 1
    finally:
        svc.close()


def test_entry_is_filled_and_protected_before_cycle_completes(tmp_path, monkeypatch):
    svc, api = make_service(tmp_path, monkeypatch)
    emitted = {"done": False}

    def latest(instrument, frame, now):
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
        assert [call[0] for call in svc.transport.calls] == ["entry", "stop"]
        heartbeat = (
            tmp_path
            / "diagnostics"
            / "stage8-12-4-production-heartbeat.json"
        ).read_text(encoding="utf-8")
        assert '"health_status":"HEALTHY"' in heartbeat
        assert '"instrument":"USDRUBF"' in heartbeat
        assert '"active_stop_order_ids":["STOP-1"]' in heartbeat
    finally:
        svc.close()


def test_persisted_entry_on_restart_never_retransmits_automatically(
    tmp_path, monkeypatch
):
    svc, api = make_service(tmp_path, monkeypatch)
    action = RuntimeAction(
        "ENTRY",
        "stage8.12:restart-entry",
        "USDRUBF",
        "USDRUBF@RTSX",
        "LONG",
        1,
        "restart-trade",
        "restart-signal",
        Decimal("100"),
        Decimal("99"),
        1,
    )
    assert svc.runtime.store.persist_intent(
        action.idempotency_key, action.payload()
    )
    try:
        with pytest.raises(
            ProductionServiceFault,
            match="STAGE8_12_4_PERSISTED_ENTRY_REQUIRES_OPERATOR_RECONCILIATION",
        ):
            svc._reconcile_unresolved({}, [])
        assert not svc.transport.calls
    finally:
        svc.close()


def test_active_order_is_known_by_client_id_before_broker_id_binding(
    tmp_path, monkeypatch
):
    svc, api = make_service(tmp_path, monkeypatch)
    action = RuntimeAction(
        "ENTRY",
        "stage8.12:uncertain-entry",
        "USDRUBF",
        "USDRUBF@RTSX",
        "LONG",
        1,
        "uncertain-trade",
        "uncertain-signal",
        Decimal("100"),
        Decimal("99"),
        1,
    )
    assert svc.runtime.store.persist_intent(
        action.idempotency_key, action.payload()
    )
    svc.runtime.store.transition_intent(action.idempotency_key, "SUBMITTED")
    svc.runtime.store.transition_intent(action.idempotency_key, "UNCERTAIN")
    row = {
        "order_id": "BROKER-RECOVERED",
        "status": "ORDER_STATUS_NEW",
        "order": {
            "client_order_id": compact_client_order_id(action.idempotency_key),
            "symbol": action.finam_symbol,
        },
    }
    try:
        svc._known_active_order_ids([row])
    finally:
        svc.close()


def test_stop_broker_decimal_representation_is_numeric_not_textual(
    tmp_path, monkeypatch
):
    svc, api = make_service(tmp_path, monkeypatch)
    action = RuntimeAction(
        "PROTECTIVE_STOP_INSTALL",
        "stage8.12:test:stop:0000",
        "USDRUBF",
        "USDRUBF@RTSX",
        "LONG",
        1,
        "trade",
        "signal",
        Decimal("100"),
        Decimal("99.95"),
        1,
    )
    intent = {
        "idempotency_key": action.idempotency_key,
        "payload": action.payload(),
        "status": "ACK",
        "broker_order_id": "STOP-X",
    }
    row = {
        "order_id": "STOP-X",
        "status": "ORDER_STATUS_WATCHING",
        "sltp_order": {
            "client_order_id": compact_client_order_id(action.idempotency_key),
            "comment": action.idempotency_key,
            "symbol": action.finam_symbol,
            "side": "SIDE_SELL",
            "quantity_sl": {"value": "100.000"},
            "sl_qty_measure": "SLTP_QTY_MEASURE_PERCENT",
            "sl_price": {"value": "99.9500"},
        },
    }
    try:
        svc._verify_stop_row(row, intent)
    finally:
        svc.close()


def test_unexplained_realized_basis_change_blocks_cycle(tmp_path, monkeypatch):
    svc, api = make_service(tmp_path, monkeypatch)
    svc.runtime.set_realized_equity(Decimal("100000"))
    api.account_data["equity"] = {"value": "100100"}
    svc.runtime.build_latest_signal = lambda instrument, frame, now: None
    try:
        with pytest.raises(
            ProductionServiceFault,
            match="STAGE8_12_4_UNEXPLAINED_REALIZED_EQUITY_DISCREPANCY",
        ):
            svc.cycle()
    finally:
        svc.close()
