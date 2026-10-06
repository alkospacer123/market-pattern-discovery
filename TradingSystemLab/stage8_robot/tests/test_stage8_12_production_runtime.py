from __future__ import annotations

import ast
from datetime import datetime
from decimal import Decimal
from pathlib import Path
from zoneinfo import ZoneInfo

import pandas as pd
import pytest

from TradingSystemLab.stage8_robot.n4_capacity import (
    N4CapacityInput, simultaneous_positive_capacity,
)
from TradingSystemLab.stage8_robot.production_runtime import (
    InstrumentAuthority, ProductionRuntime, ProductionRuntimeError,
)
from TradingSystemLab.stage8_robot.strategy_core import CompletedBar, SignalIntent

MSK = ZoneInfo("Europe/Moscow")


def authority(instrument="USDRUBF"):
    return InstrumentAuthority(
        instrument=instrument,
        finam_symbol=f"{instrument}@RTSX",
        price_step=Decimal("1"),
        tick_value=Decimal("10"),
        trade_lot_size=1,
        long_initial_margin=Decimal("100"),
        short_initial_margin=Decimal("120"),
    )


def signal(instrument="USDRUBF", direction="LONG"):
    entry = 100.0
    stop = 95.0 if direction == "LONG" else 105.0
    return SignalIntent(
        signal_id=f"signal-{instrument}-{direction}",
        trade_id=f"trade-{instrument}-{direction}",
        instrument=instrument,
        direction=direction,
        timestamp=datetime(2026, 1, 2, 10, tzinfo=MSK),
        entry=entry,
        initial_stop=stop,
        initial_r=5.0,
        canonical_stop=stop,
    )


def test_stage8_12_runtime_is_structurally_broker_neutral():
    source = Path("TradingSystemLab/stage8_robot/production_runtime.py").read_text()
    tree = ast.parse(source)
    imports = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            imports.extend(alias.name for alias in node.names)
        elif isinstance(node, ast.ImportFrom):
            imports.append(node.module or "")
    assert not any(name.endswith(".broker") or name.endswith(".finam_api") for name in imports)
    assert "place_order(" not in source
    assert "submit_order(" not in source


def test_runtime_rejects_execution_authorization_in_assembly_stage(tmp_path):
    with pytest.raises(ProductionRuntimeError, match="REAL_ORDER_TRANSMISSION_NOT_AUTHORIZED"):
        ProductionRuntime(tmp_path / "state.db", execution_authorized=True)


def test_latest_signal_wires_context_builder_and_decision_core(tmp_path):
    runtime = ProductionRuntime(tmp_path / "state.db")
    timestamp = pd.Timestamp("2026-01-02T10:00:00", tz="Europe/Moscow")
    execution = pd.DataFrame([{
        "Open":100.0,"High":106.0,"Low":99.0,"Close":105.0,"ATR":2.0,
        "PriorHigh":104.0,"PriorLow":96.0,
    }], index=pd.DatetimeIndex([timestamp]))
    context = pd.DataFrame([{
        "Open":99.0,"High":111.0,"Low":98.0,"Close":110.0,
        "EMA100":100.0,"EMA100Slope":1.0,"ADX":25.0,"ATR":3.0,
        "ATRMean20":2.0,"EMA50":105.0,"EMA200":95.0,
    }], index=pd.DatetimeIndex([timestamp]))

    class Builder:
        def build(self, h1, now):
            return execution, context

    runtime.context_builder = Builder()
    frame = pd.DataFrame(index=pd.DatetimeIndex([timestamp]))
    out = runtime.build_latest_signal(
        "USDRUBF", frame, timestamp.to_pydatetime())
    repeated = runtime.build_latest_signal(
        "USDRUBF", frame, timestamp.to_pydatetime())
    assert out is not None and out.direction == "LONG"
    assert out.entry == 105.0 and out.initial_stop == 100.0
    assert repeated.signal_id == out.signal_id and repeated.trade_id == out.trade_id
    assert runtime.store.get("signal_sequence:USDRUBF") == 1
    runtime.close()


def test_entry_r15_margin_position_authority_and_initial_stop(tmp_path):
    runtime = ProductionRuntime(tmp_path / "state.db")
    budget = runtime.begin_batch(
        realized_equity=Decimal("100000"), available_cash=Decimal("1000"))
    action = runtime.plan_entry(
        signal(), authority(), realized_equity=Decimal("100000"), budget=budget)

    assert action.kind == "ENTRY"
    assert action.quantity == 10
    assert action.expected_position_quantity == 10
    assert runtime.store.unresolved_intent_count() == 1

    assert runtime.confirm_entry_position(action.idempotency_key, 0) is None
    stop = runtime.confirm_entry_position(action.idempotency_key, 10)
    assert stop.kind == "PROTECTIVE_STOP_INSTALL"
    assert stop.stop_price == Decimal("95.0")
    assert runtime.store.unresolved_intent_count() == 1

    runtime.confirm_protective_stop(stop.idempotency_key, "synthetic-stop")
    position = runtime.open_positions()["USDRUBF"]
    assert position["quantity"] == 10
    assert position["protective_stop_state"] == "ACTIVE"
    assert runtime.store.unresolved_intent_count() == 0
    runtime.close()


def test_wrong_position_authority_fails_closed(tmp_path):
    runtime = ProductionRuntime(tmp_path / "state.db")
    budget = runtime.begin_batch(
        realized_equity=Decimal("100000"), available_cash=Decimal("1000"))
    action = runtime.plan_entry(
        signal(), authority(), realized_equity=Decimal("100000"), budget=budget)
    with pytest.raises(ProductionRuntimeError, match="UNEXPECTED_QUANTITY"):
        runtime.confirm_entry_position(action.idempotency_key, -action.quantity)
    runtime.close()


def test_zero_capacity_is_clean_skip_without_durable_intent(tmp_path):
    runtime = ProductionRuntime(tmp_path / "state.db")
    budget = runtime.begin_batch(
        realized_equity=Decimal("100000"), available_cash=Decimal("50"))
    action = runtime.plan_entry(
        signal(), authority(), realized_equity=Decimal("100000"), budget=budget)
    assert action.kind == "SKIP_ZERO_CAPACITY"
    assert action.quantity == 0
    assert runtime.store.unresolved_intent_count() == 0
    runtime.close()


def _open_and_protect(runtime):
    budget = runtime.begin_batch(
        realized_equity=Decimal("100000"), available_cash=Decimal("1000"))
    entry = runtime.plan_entry(
        signal(), authority(), realized_equity=Decimal("100000"), budget=budget)
    stop = runtime.confirm_entry_position(entry.idempotency_key, entry.quantity)
    runtime.confirm_protective_stop(stop.idempotency_key, "stop-0")
    return entry


def test_trail1_tightening_emits_stop_replace_not_market_exit(tmp_path):
    runtime = ProductionRuntime(tmp_path / "state.db")
    entry = _open_and_protect(runtime)

    first = CompletedBar(
        datetime(2026,1,2,11,tzinfo=MSK),100,106,99,105,2,completed=True)
    assert runtime.manage_completed_bar(
        "USDRUBF", first, observed_position_quantity=entry.quantity) is None

    second = CompletedBar(
        datetime(2026,1,2,12,tzinfo=MSK),105,107,101,106,2,completed=True)
    replace = runtime.manage_completed_bar(
        "USDRUBF", second, observed_position_quantity=entry.quantity)
    assert replace.kind == "PROTECTIVE_STOP_REPLACE"
    assert replace.stop_price == Decimal("101.0")
    assert replace.reason == "ATOMIC_REPLACEMENT_ADAPTER_REQUIRED"
    assert runtime.open_positions()["USDRUBF"]["protective_stop_state"] == "PENDING_REPLACE"
    runtime.close()


def test_unprotected_position_blocks_bar_progression(tmp_path):
    runtime = ProductionRuntime(tmp_path / "state.db")
    budget = runtime.begin_batch(
        realized_equity=Decimal("100000"), available_cash=Decimal("1000"))
    entry = runtime.plan_entry(
        signal(), authority(), realized_equity=Decimal("100000"), budget=budget)
    runtime.confirm_entry_position(entry.idempotency_key, entry.quantity)
    bar = CompletedBar(
        datetime(2026,1,2,11,tzinfo=MSK),100,106,99,105,2,completed=True)
    with pytest.raises(ProductionRuntimeError, match="PROTECTIVE_STOP_NOT_ACTIVE"):
        runtime.manage_completed_bar(
            "USDRUBF", bar, observed_position_quantity=entry.quantity)
    runtime.close()


def test_stop_divergence_requires_emergency_exit_action(tmp_path):
    runtime = ProductionRuntime(tmp_path / "state.db")
    entry = _open_and_protect(runtime)
    hit = CompletedBar(
        datetime(2026,1,2,11,tzinfo=MSK),94,100,90,95,2,completed=True)
    action = runtime.manage_completed_bar(
        "USDRUBF", hit, observed_position_quantity=entry.quantity)
    assert action.kind == "EMERGENCY_EXIT_REQUIRED"
    assert action.expected_position_quantity == 0
    assert action.reason == "PROTECTIVE_STOP_DIVERGENCE_POSITION_STILL_OPEN"
    runtime.close()


def test_broker_flat_is_position_authority_for_exit_and_equity_sync(tmp_path):
    runtime = ProductionRuntime(tmp_path / "state.db")
    entry = _open_and_protect(runtime)
    bar = CompletedBar(
        datetime(2026,1,2,11,tzinfo=MSK),100,106,99,105,2,completed=True)
    observed = runtime.manage_completed_bar(
        "USDRUBF", bar, observed_position_quantity=0)
    assert observed.kind == "BROKER_EXIT_OBSERVED"
    closed = runtime.broker_exit_observed(
        "USDRUBF", realized_equity_after_exit=Decimal("100500"))
    assert closed.kind == "BROKER_EXIT_OBSERVED"
    assert runtime.open_positions() == {}
    assert runtime.current_realized_equity() == Decimal("100500")
    runtime.close()


def test_maximum_nominal_initial_risk_is_enforced(tmp_path):
    runtime = ProductionRuntime(tmp_path / "state.db")
    runtime.store.put("production_positions", {
        "CNYRUBF":{"risk_cash":"6000"}
    })
    budget = runtime.begin_batch(
        realized_equity=Decimal("100000"), available_cash=Decimal("1000"))
    before = budget.remaining
    skipped = runtime.plan_entry(
        signal(), authority(), realized_equity=Decimal("100000"), budget=budget)
    assert skipped.kind == "SKIP_RISK_LIMIT"
    assert skipped.reason == "MAXIMUM_NOMINAL_INITIAL_RISK_EXCEEDED"
    assert budget.remaining == before
    runtime.close()


def capacity_inputs(loss="100"):
    return {
        "USDRUBF":N4CapacityInput(Decimal(loss),1,Decimal("1000"),Decimal("1500")),
        "CNYRUBF":N4CapacityInput(Decimal("200") if loss=="100" else Decimal(loss),1,Decimal("2000"),Decimal("1800")),
        "GLDRUBF":N4CapacityInput(Decimal("300") if loss=="100" else Decimal(loss),1,Decimal("3000"),Decimal("3500")),
        "IMOEXF":N4CapacityInput(Decimal("400") if loss=="100" else Decimal(loss),1,Decimal("4000"),Decimal("4500")),
    }


def test_n4_capacity_reports_r15_margin_and_explicit_reserve():
    plan = simultaneous_positive_capacity(
        capacity_inputs(), reserve_fraction=Decimal("0.20"))
    assert plan.r15_equity_floor == Decimal("400") / Decimal("0.015")
    assert plan.long_margin_floor == Decimal("10000")
    assert plan.short_margin_floor == Decimal("11300")
    assert plan.worst_direction_margin_floor == Decimal("11500")
    assert plan.base_required_capital == plan.r15_equity_floor
    assert plan.required_capital_with_reserve == Decimal("32000.00000000000000000000000")


def test_n4_capacity_can_be_margin_dominated_and_requires_exact_n4():
    plan = simultaneous_positive_capacity(
        capacity_inputs("10"), reserve_fraction=Decimal("0"))
    assert plan.base_required_capital == Decimal("11500")
    bad = capacity_inputs("10")
    bad.pop("IMOEXF")
    with pytest.raises(ValueError, match="FROZEN_BASKET"):
        simultaneous_positive_capacity(bad, reserve_fraction=Decimal("0"))
