from __future__ import annotations

import hashlib
from datetime import datetime, timezone
from decimal import Decimal
from pathlib import Path
from types import MethodType

import pandas as pd
import pytest

import TradingSystemLab.stage8_robot.production_service as service_mod
from TradingSystemLab.stage8_robot.margin import MarginBatchBudget
from TradingSystemLab.stage8_robot.production_authorization import (
    OPERATOR_AUTHORIZATION_PHRASE,
    write_authorization,
)
from TradingSystemLab.stage8_robot.production_broker_state import (
    BrokerOrderView,
)
from TradingSystemLab.stage8_robot.production_runtime import (
    InstrumentAuthority,
    ProductionRuntime,
    RuntimeAction,
)
from TradingSystemLab.stage8_robot.production_service import (
    BrokerSnapshot,
    ProductionService,
    ProductionServiceFault,
    _entry_session_open,
)
from TradingSystemLab.stage8_robot.specification import (
    INSTRUMENTS,
    PRODUCTION_SPECIFICATION_ID,
)
from TradingSystemLab.stage8_robot.strategy_core import SignalIntent
from TradingSystemLab.stage8_robot.trading_safety_gate import write_kill_switch


COMMIT = "a" * 40
ACCOUNT = "PRODUCTION-ACCOUNT"
ACCOUNT_HASH = hashlib.sha256(ACCOUNT.encode()).hexdigest()
NOW = datetime(2026, 10, 7, 8, 30, tzinfo=timezone.utc)


def money(value: str):
    units, _, fraction = value.partition(".")
    nanos = int((fraction + "0" * 9)[:9]) if fraction else 0
    return {"currency_code": "RUB", "units": units, "nanos": nanos}


def account(*, quantity: int = 0, unrealized: str = "0"):
    positions = []
    if quantity:
        positions.append(
            {
                "symbol": "USDRUBF@RTSX",
                "quantity": {"value": str(quantity)},
            }
        )
    return {
        "status": "ACCOUNT_ACTIVE",
        "type": "FORTS",
        "equity": {"value": "100000"},
        "unrealized_profit": {"value": unrealized},
        "portfolio_forts": {
            "available_cash": {"value": "50000"},
            "money_reserved": {"value": "0"},
        },
        "positions": positions,
    }


class FakeAPI:
    def __init__(self):
        self.calls = []
        self.account_value = account()
        self.orders_value = {"orders": []}

    def create_session(self):
        self.calls.append(("create_session",))
        return {}

    def session_details(self):
        self.calls.append(("session_details",))
        return {"readonly": False, "account_ids": [ACCOUNT]}

    def account(self, account_id):
        self.calls.append(("account", account_id))
        return self.account_value

    def orders(self, account_id):
        self.calls.append(("orders", account_id))
        return self.orders_value


class FakeCache:
    def close(self):
        pass


def history(stamp="2026-10-07 10:00:00+03:00"):
    index = pd.DatetimeIndex([pd.Timestamp(stamp)], name="CloseTime")
    return pd.DataFrame(
        [[100.0, 101.0, 99.0, 100.0]],
        index=index,
        columns=("Open", "High", "Low", "Close"),
    )


def authority(instrument):
    step = {
        "USDRUBF": "0.01",
        "CNYRUBF": "0.001",
        "GLDRUBF": "0.1",
        "IMOEXF": "0.5",
    }[instrument]
    tick = {
        "USDRUBF": "10",
        "CNYRUBF": "1",
        "GLDRUBF": "0.1",
        "IMOEXF": "5",
    }[instrument]
    return InstrumentAuthority(
        instrument,
        f"{instrument}@RTSX",
        Decimal(step),
        Decimal(tick),
        1,
        Decimal("1000"),
        Decimal("1000"),
    )


def authorize(root):
    write_authorization(
        root,
        accepted_commit=COMMIT,
        account_hash=ACCOUNT_HASH,
        operator_authorization_phrase=OPERATOR_AUTHORIZATION_PHRASE,
        now=NOW,
    )


def test_entry_schedule_requires_current_valid_trading_window():
    schedule = {
        "sessions": [
            {
                "type": "CORE_TRADING",
                "interval": {
                    "start_time": "2026-10-07T06:00:00Z",
                    "end_time": "2026-10-07T10:00:00Z",
                },
            }
        ]
    }
    assert _entry_session_open(schedule, NOW) is True
    assert _entry_session_open(
        schedule, datetime(2026, 10, 7, 10, 1, tzinfo=timezone.utc)
    ) is False


def test_realized_basis_excludes_unrealized_profit(tmp_path):
    service = ProductionService.__new__(ProductionService)
    service.runtime = ProductionRuntime(tmp_path / "state.db")
    try:
        value = service._realized_basis(
            {
                "equity": {"value": "105000"},
                "unrealized_profit": {"value": "5000"},
            }
        )
        assert value == Decimal("100000")
        service.runtime.store.put("explained_external_cash_flows", "2500")
        assert service._realized_basis(
            {
                "equity": {"value": "107500"},
                "unrealized_profit": {"value": "5000"},
            }
        ) == Decimal("100000")
    finally:
        service.runtime.close()


def test_first_authorized_cycle_primes_watermarks_without_forced_order(
    tmp_path, monkeypatch
):
    authorize(tmp_path)
    write_kill_switch(tmp_path, "ARMED", allow_arm=True, now=NOW)
    api = FakeAPI()

    monkeypatch.setattr(service_mod, "initialize_cache", lambda *_: None)
    monkeypatch.setattr(service_mod, "ProductionH1Cache", lambda *_: FakeCache())

    service = ProductionService(
        runtime_root=tmp_path,
        data_root=tmp_path / "data",
        accepted_commit=COMMIT,
        api=api,
        account_id=ACCOUNT,
        clock=lambda: NOW,
        sleeper=lambda _: None,
    )
    histories = {instrument: history() for instrument in INSTRUMENTS}
    authorities = {instrument: authority(instrument) for instrument in INSTRUMENTS}
    schedules = {
        instrument: {
            "sessions": [
                {
                    "type": "CORE_TRADING",
                    "interval": {
                        "start_time": "2026-10-07T06:00:00Z",
                        "end_time": "2026-10-07T10:00:00Z",
                    },
                }
            ]
        }
        for instrument in INSTRUMENTS
    }
    service._instrument_data = MethodType(
        lambda self, now: (authorities, histories, schedules), service
    )
    service.runtime.build_latest_signal = lambda *args, **kwargs: None
    try:
        service.cycle()
        activation = service.runtime.store.get("production_activation_watermarks")
        assert activation["accepted_commit"] == COMMIT
        assert set(activation["watermarks"]) == set(INSTRUMENTS)
        assert service.runtime.current_realized_equity() == Decimal("100000")
        assert not [
            call for call in api.calls
            if call[0] in {"place_order", "place_sltp_order", "cancel_order"}
        ]
    finally:
        service.close()


def test_entry_intent_is_durable_before_transport_and_position_is_authority(
    tmp_path
):
    runtime = ProductionRuntime(tmp_path / "state.db")
    signal = SignalIntent(
        "signal-1",
        "trade-1",
        "USDRUBF",
        "LONG",
        pd.Timestamp("2026-10-07 10:00:00", tz="Europe/Moscow").to_pydatetime(),
        100.0,
        99.9,
        0.1,
        99.9,
    )
    runtime.store.put("pending_signal:USDRUBF", {
        "signal_id": signal.signal_id,
        "trade_id": signal.trade_id,
        "instrument": signal.instrument,
        "direction": signal.direction,
        "timestamp": signal.timestamp.isoformat(),
        "entry": signal.entry,
        "initial_stop": signal.initial_stop,
        "initial_r": signal.initial_r,
        "canonical_stop": signal.canonical_stop,
    })
    runtime.store.put(
        "last_evaluated_h1:USDRUBF",
        pd.Timestamp("2026-10-07 09:00:00", tz="Europe/Moscow").isoformat(),
    )
    action = runtime.plan_entry(
        signal,
        authority("USDRUBF"),
        realized_equity=Decimal("100000"),
        budget=MarginBatchBudget(Decimal("50000")),
    )

    class Transport:
        def __init__(self):
            self.runtime = runtime
            self.seen_status = None

        def submit_entry(self, submitted, *, now):
            self.seen_status = self.runtime.store.intent(
                submitted.idempotency_key
            )["status"]
            return {"order_id": "ENTRY-1"}

    service = ProductionService.__new__(ProductionService)
    service.runtime = runtime
    service.transport = Transport()
    service._snapshot = MethodType(
        lambda self: BrokerSnapshot(
            account(),
            {"USDRUBF@RTSX": action.expected_position_quantity},
            [],
            Decimal("100000"),
            Decimal("50000"),
        ),
        service,
    )
    service._wait_for_position = MethodType(lambda self, _: self._snapshot(), service)
    service._ensure_stop_or_exit = MethodType(
        lambda self, stop, snapshot: snapshot, service
    )
    try:
        service._submit_new_entry(action, NOW)
        assert service.transport.seen_status == "SUBMITTED"
        assert runtime.store.intent(action.idempotency_key)["status"] == "RECONCILED"
        assert runtime.open_positions()["USDRUBF"]["quantity"] == action.quantity
        assert runtime.store.get("last_managed_h1:USDRUBF") == signal.timestamp.isoformat()
    finally:
        runtime.close()


def test_stop_confirmation_requires_full_production_identity(tmp_path):
    service = ProductionService.__new__(ProductionService)
    action = RuntimeAction(
        "PROTECTIVE_STOP_INSTALL",
        "stage8.12:trade-1:stop:0000",
        "USDRUBF",
        "USDRUBF@RTSX",
        "LONG",
        2,
        "trade-1",
        "signal-1",
        Decimal("100"),
        Decimal("99.5"),
        2,
    )
    good = BrokerOrderView(
        "STOP-1",
        "NEW",
        True,
        "SLTP",
        "USDRUBF@RTSX",
        "s8" + hashlib.sha256(action.idempotency_key.encode()).hexdigest()[:18],
        action.idempotency_key,
        "SIDE_SELL",
        {
            "symbol": "USDRUBF@RTSX",
            "side": "SIDE_SELL",
            "quantity_sl": {"value": "100"},
            "sl_qty_measure": "SLTP_QTY_MEASURE_PERCENT",
            "sl_price": {"value": "99.5"},
            "valid_before": "VALID_BEFORE_GOOD_TILL_CANCEL",
            "client_order_id": "s8" + hashlib.sha256(action.idempotency_key.encode()).hexdigest()[:18],
            "comment": action.idempotency_key,
        },
    )
    snapshot = BrokerSnapshot(account(), {}, [good], Decimal("100000"), Decimal("50000"))
    assert service._proven_active_stop(snapshot, action).order_id == "STOP-1"

    wrong_comment = BrokerOrderView(
        **{**good.__dict__, "comment": "manual-stop"}
    )
    snapshot = BrokerSnapshot(
        account(), {}, [wrong_comment], Decimal("100000"), Decimal("50000")
    )
    assert service._proven_active_stop(snapshot, action) is None


def test_runtime_discards_pre_intent_orphan_signal_on_restart(tmp_path):
    runtime = ProductionRuntime(tmp_path / "state.db")
    try:
        runtime.store.put(
            "pending_signal:USDRUBF",
            {
                "signal_id": "signal-1",
                "timestamp": "2026-10-07T10:00:00+03:00",
            },
        )
        assert runtime.discard_orphan_pending_signal("USDRUBF") is True
        assert runtime.store.get("pending_signal:USDRUBF") is None
        assert runtime.store.get("last_evaluated_h1:USDRUBF") == (
            "2026-10-07T10:00:00+03:00"
        )
    finally:
        runtime.close()


def test_production_service_does_not_reintroduce_trade_or_exact_order_fill_authority():
    source = Path(
        "TradingSystemLab/stage8_robot/production_service.py"
    ).read_text(encoding="utf-8")
    assert ".trades(" not in source
    assert ".order(" not in source
    assert "executed_quantity" not in source
    assert "remaining_quantity" not in source
    assert "position_quantities(" in source
    assert "emergency_halt(" in source
    assert "write_production_heartbeat(" in source
    assert "initialize_activation_watermarks(" in source
