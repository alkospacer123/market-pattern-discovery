"""Stage 8 #493: candidate-only real runtime partial-growth safety checks.

All broker orders are synthetic BrokerOrderView fixtures. NO FINAM transport.
Never test against LIVE SQLite, production task, or real authorization.
"""
from dataclasses import replace
from decimal import Decimal as D
import pytest

from TradingSystemLab.stage8_robot.broker import compact_client_order_id
from TradingSystemLab.stage8_robot.production_broker_state import BrokerOrderView
from TradingSystemLab.stage8_robot.tests.test_stop_tick_grid_amendment import (
    runtime, signal, plan,
)


def two_contracts(tmp_path, direction="LONG"):
    rt = runtime(tmp_path / "offline-only.db")
    cash = D("250") if direction == "LONG" else D("300")
    budget = rt.begin_batch(realized_equity=D("100000"), available_cash=cash)
    entry = plan(rt, signal(side=direction), budget=budget)
    assert entry.quantity == 2
    observed = 1 if direction == "LONG" else -1
    stop = rt.confirm_entry_position(entry.idempotency_key, observed)
    assert stop is not None and stop.kind == "PROTECTIVE_STOP_INSTALL"
    rt.confirm_protective_stop(stop.idempotency_key, "synthetic-initial-stop")
    value = rt.open_positions()[entry.instrument]
    assert value["quantity"] == 1 and value["protective_covered_quantity"] == 1
    return rt, entry, stop


def order_for(stop, **updates):
    payload = {
        "symbol": stop.finam_symbol,
        "side": "SIDE_SELL" if stop.direction == "LONG" else "SIDE_BUY",
        "client_order_id": compact_client_order_id(stop.idempotency_key),
        "comment": stop.idempotency_key,
        "quantity_sl": {"value": "100"},
        "sl_qty_measure": "SLTP_QTY_MEASURE_PERCENT",
        "sl_price": {"value": str(stop.stop_price)},
        "valid_before": "VALID_BEFORE_GOOD_TILL_CANCEL",
    }
    modified = dict(updates)
    payload.update(modified.pop("request_changes", {}))
    return BrokerOrderView(
        order_id=modified.pop("order_id", "synthetic-initial-stop"),
        status=modified.pop("status", "NEW"),
        active=modified.pop("active", True),
        kind=modified.pop("kind", "SLTP"),
        symbol=modified.pop("symbol", stop.finam_symbol),
        client_order_id=modified.pop("client_order_id", compact_client_order_id(stop.idempotency_key)),
        comment=modified.pop("comment", stop.idempotency_key),
        side=modified.pop("side", payload["side"]),
        request=payload,
    )


@pytest.mark.parametrize("direction", ["LONG", "SHORT"])
def test_observed_one_to_two_same_100_percent_stop_only(direction, tmp_path):
    rt, entry, stop = two_contracts(tmp_path, direction)
    before = len(rt.store.all_intents())
    observed = 2 if direction == "LONG" else -2
    result = rt.confirm_entry_position(entry.idempotency_key, observed,
        observed_protective_stop=order_for(stop))
    assert result is None
    p = rt.open_positions()[entry.instrument]
    assert p["quantity"] == 2 and p["protective_covered_quantity"] == 2
    assert p["protective_stop_broker_order_id"] == "synthetic-initial-stop"
    assert p["verified_fill_entry"] is None and p["fill_authority"] == "MISSING"
    assert len(rt.store.all_intents()) == before
    assert rt.store.get("execution_halt") is None
    e = rt.store.get(f"entry_growth_stop_observed:{entry.idempotency_key}")
    assert e["from_quantity"] == 1 and e["to_quantity"] == 2
    assert e["quantity_percent"] == "100"
    assert e["real_finam_dynamic_coverage_proven"] is False
    rt.close()


@pytest.mark.parametrize("mutation", [
    {"order_id": "other-stop"},
    {"active": False},
    {"status": "FILLED"},
    {"kind": "REGULAR"},
    {"symbol": "GLDRUBF@RTSX"},
    {"side": "SIDE_BUY"},
    {"comment": "other-comment"},
    {"client_order_id": "other-client-id"},
    {"request_changes": {"quantity_sl": {"value":"50"}}},
    {"request_changes": {"sl_qty_measure": "SLTP_QTY_MEASURE_UNITS"}},
    {"request_changes": {"sl_price": {"value":"0"}}},
    {"request_changes": {"valid_before": "VALID_BEFORE_DAY"}},
    {"request_changes": {"symbol":"GLDRUBF@RTSX"}},
    {"request_changes": {"side":"SIDE_BUY"}},
    {"request_changes": {"comment":"foreign"}},
    {"request_changes": {"client_order_id":"foreign"}},
])
def test_growth_wrong_broker_stop_sticky_halt(tmp_path, mutation):
    rt, entry, stop = two_contracts(tmp_path)
    before = len(rt.store.all_intents())
    rt.confirm_entry_position(entry.idempotency_key, 2,
        observed_protective_stop=order_for(stop, **mutation))
    p = rt.open_positions()[entry.instrument]
    assert p["quantity"] == 1 and p["protective_covered_quantity"] == 1
    assert rt.store.get("execution_halt")["status"] == "HALTED"
    assert rt.store.get(f"entry_growth_hold:{entry.idempotency_key}")["observed_quantity"] == 2
    assert len(rt.store.all_intents()) == before
    # A later valid-looking observation NEVER auto-clears an operator hold.
    rt.confirm_entry_position(entry.idempotency_key, 2,
        observed_protective_stop=order_for(stop))
    assert rt.open_positions()[entry.instrument]["quantity"] == 1
    rt.close()


def test_growth_missing_stop_requires_operator_hold(tmp_path):
    rt, entry, stop = two_contracts(tmp_path)
    assert rt.confirm_entry_position(entry.idempotency_key,2) is None
    assert rt.store.get("execution_halt")["operator_intervention_required"] is True
    assert rt.open_positions()[entry.instrument]["quantity"] == 1
    rt.close()


def test_growth_success_survives_restart_with_same_stop_id(tmp_path):
    rt, entry, stop = two_contracts(tmp_path)
    rt.confirm_entry_position(entry.idempotency_key, 2, observed_protective_stop=order_for(stop))
    rt.close()
    rt = runtime(tmp_path / "offline-only.db")
    assert rt.open_positions()[entry.instrument]["quantity"] == 2
    assert rt.open_positions()[entry.instrument]["protective_covered_quantity"] == 2
    assert rt.store.get(f"entry_growth_stop_observed:{entry.idempotency_key}")["broker_stop_id"] == "synthetic-initial-stop"
    assert len(rt.store.all_intents()) == 2
    rt.close()


def test_growth_hold_survives_restart_no_unhalt(tmp_path):
    rt, entry, stop = two_contracts(tmp_path)
    rt.confirm_entry_position(entry.idempotency_key, 2)
    rt.close()
    rt = runtime(tmp_path / "offline-only.db")
    assert rt.store.get("execution_halt") is not None
    assert rt.store.get(f"entry_growth_hold:{entry.idempotency_key}")["observed_quantity"] == 2
    rt.confirm_entry_position(entry.idempotency_key, 2, observed_protective_stop=order_for(stop))
    assert rt.open_positions()[entry.instrument]["quantity"] == 1
    rt.close()


def test_pending_first_stop_can_wait_for_remeasured_quantity(tmp_path):
    rt = runtime(tmp_path / "offline-only.db")
    budget = rt.begin_batch(realized_equity=D("100000"), available_cash=D("250"))
    entry = plan(rt, signal(), budget=budget)
    assert entry.quantity == 2
    stop = rt.confirm_entry_position(entry.idempotency_key, 1)
    again = rt.confirm_entry_position(entry.idempotency_key, 2)
    assert again.idempotency_key == stop.idempotency_key
    assert rt.open_positions()[entry.instrument]["quantity"] == 2
    assert rt.open_positions()[entry.instrument]["protective_covered_quantity"] == 0
    # No premature 100%-coverage claim until a protective submission/ACK and broker proof.
    rt.close()


def test_growth_does_not_unlock_v2_real_order_transport(tmp_path):
    from TradingSystemLab.stage8_robot.execution_grid import FINAM_FILL_AUTHORITY_VERIFIED
    assert FINAM_FILL_AUTHORITY_VERIFIED is False
    rt, entry, stop = two_contracts(tmp_path)
    rt.confirm_entry_position(entry.idempotency_key,2,observed_protective_stop=order_for(stop))
    assert rt.store.get("execution_halt") is None
    assert rt.store.get(f"entry_growth_stop_observed:{entry.idempotency_key}")["real_finam_dynamic_coverage_proven"] is False
    rt.close()


def test_candidate_service_receives_broker_orders_not_flag():
    from TradingSystemLab.stage8_robot import production_service
    import inspect
    src = inspect.getsource(production_service.ProductionService._reconcile_candidate_entry)
    assert "active_sltp_for_trade" in src
    assert "observed_protective_stop=stop_observation" in src
    assert "entry_growth_hold" in src
    assert "place_order" not in src and "place_sltp_order" not in src
