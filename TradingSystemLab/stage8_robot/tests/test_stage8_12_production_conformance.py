from __future__ import annotations

import ast
from datetime import datetime, timedelta
from decimal import Decimal
from pathlib import Path
from zoneinfo import ZoneInfo

import pytest

from TradingSystemLab.stage8_robot.account_cleanliness import count_active_orders
from TradingSystemLab.stage8_robot.market_data import validate_stream
from TradingSystemLab.stage8_robot.production_runtime import (
    InstrumentAuthority,
    ProductionRuntime,
    ProductionRuntimeError,
)
from TradingSystemLab.stage8_robot.protective_stop_contract import (
    CONTRACT_SCHEMA,
    QTY_MEASURE,
    QTY_PERCENT,
    SyntheticPercentPositionStopAdapter,
    ProtectiveStopContractError,
)
from TradingSystemLab.stage8_robot.readonly_supervisor import SafetyFault, _session_is_safe
from TradingSystemLab.stage8_robot.strategy_core import CompletedBar, SignalIntent
from TradingSystemLab.stage8_robot.trading_safety_gate import (
    evaluate_new_entry_gate,
    write_kill_switch,
)

MSK = ZoneInfo("Europe/Moscow")
FROZEN_ECONOMICS = {
    "USDRUBF": (Decimal("0.01"), Decimal("10")),
    "CNYRUBF": (Decimal("0.001"), Decimal("1")),
    "GLDRUBF": (Decimal("0.1"), Decimal("0.1")),
    "IMOEXF": (Decimal("0.5"), Decimal("5")),
}


def authority(instrument: str) -> InstrumentAuthority:
    step, tick = FROZEN_ECONOMICS[instrument]
    return InstrumentAuthority(
        instrument=instrument,
        finam_symbol=f"{instrument}@RTSX",
        price_step=step,
        tick_value=tick,
        trade_lot_size=1,
        long_initial_margin=Decimal("100"),
        short_initial_margin=Decimal("120"),
    )


def signal(instrument: str, direction: str) -> SignalIntent:
    step, _ = FROZEN_ECONOMICS[instrument]
    entry = Decimal("100")
    distance = step * 5
    stop = entry - distance if direction == "LONG" else entry + distance
    stamp = datetime(2026, 1, 2, 10, tzinfo=MSK)
    return SignalIntent(
        signal_id=f"stage8.12.2-{instrument}-{direction}-signal",
        trade_id=f"stage8.12.2-{instrument}-{direction}-trade",
        instrument=instrument,
        direction=direction,
        timestamp=stamp,
        entry=float(entry),
        initial_stop=float(stop),
        initial_r=float(distance),
        canonical_stop=float(stop),
    )


def bars(direction: str) -> tuple[CompletedBar, CompletedBar]:
    if direction == "LONG":
        return (
            CompletedBar(datetime(2026,1,2,11,tzinfo=MSK),100,106,100,105,2,completed=True),
            CompletedBar(datetime(2026,1,2,12,tzinfo=MSK),105,107,101,106,2,completed=True),
        )
    return (
        CompletedBar(datetime(2026,1,2,11,tzinfo=MSK),100,100,94,95,2,completed=True),
        CompletedBar(datetime(2026,1,2,12,tzinfo=MSK),95,99,93,94,2,completed=True),
    )


def run_end_to_end(root: Path, instrument: str, direction: str) -> dict:
    runtime = ProductionRuntime(root / "production.sqlite3")
    adapter = SyntheticPercentPositionStopAdapter()
    try:
        budget = runtime.begin_batch(
            realized_equity=Decimal("100000"),
            available_cash=Decimal("1000000"),
        )
        entry = runtime.plan_entry(
            signal(instrument, direction),
            authority(instrument),
            realized_equity=Decimal("100000"),
            budget=budget,
        )
        assert entry.kind == "ENTRY"
        assert entry.quantity > 0
        broker_position = entry.expected_position_quantity

        initial_stop = runtime.confirm_entry_position(
            entry.idempotency_key, broker_position)
        assert initial_stop.kind == "PROTECTIVE_STOP_INSTALL"

        # An accepted position is not considered safe before broker-confirmed
        # protection. No next-bar progression is allowed through this gap.
        first_bar, second_bar = bars(direction)
        with pytest.raises(
            ProductionRuntimeError,
            match="UNRESOLVED_INTENT_BLOCKS_BAR_PROCESSING",
        ):
            runtime.manage_completed_bar(
                instrument, first_bar,
                observed_position_quantity=broker_position,
            )

        first_stop_id = adapter.submit(
            initial_stop, observed_position_quantity=broker_position)
        runtime.confirm_protective_stop(
            initial_stop.idempotency_key, first_stop_id)

        assert runtime.manage_completed_bar(
            instrument, first_bar,
            observed_position_quantity=broker_position,
        ) is None

        tighten = runtime.manage_completed_bar(
            instrument, second_bar,
            observed_position_quantity=broker_position,
        )
        assert tighten.kind == "PROTECTIVE_STOP_REPLACE"
        old_effective = adapter.effective_stop(instrument, entry.trade_id)
        second_stop_id = adapter.submit(
            tighten, observed_position_quantity=broker_position)
        new_effective = adapter.effective_stop(instrument, entry.trade_id)

        # New tighter protection is active before any older backstop could be
        # retired; the conformance model intentionally keeps both.
        assert len(adapter.active_stops(instrument, entry.trade_id)) == 2
        if direction == "LONG":
            assert new_effective.stop_price > old_effective.stop_price
        else:
            assert new_effective.stop_price < old_effective.stop_price

        runtime.confirm_protective_stop(
            tighten.idempotency_key, second_stop_id)
        assert runtime.store.unresolved_intent_count() == 0

        # Trigger the effective stop. Percentage-of-current-position semantics
        # make the first triggered stop flatten the position; older backstops
        # then have zero current position to close.
        broker_position = adapter.trigger(
            instrument, entry.trade_id,
            observed_position_quantity=broker_position,
            price=new_effective.stop_price,
        )
        assert broker_position == 0
        assert adapter.terminal_proof(instrument, entry.trade_id)
        assert adapter.trigger(
            instrument, entry.trade_id,
            observed_position_quantity=0,
            price=new_effective.stop_price,
        ) == 0

        observed = runtime.manage_completed_bar(
            instrument,
            CompletedBar(
                datetime(2026,1,2,13,tzinfo=MSK),
                float(new_effective.stop_price),
                float(new_effective.stop_price),
                float(new_effective.stop_price),
                float(new_effective.stop_price),
                2,
                completed=True,
            ),
            observed_position_quantity=0,
        )
        assert observed.kind == "BROKER_EXIT_OBSERVED"

        closed = runtime.broker_exit_observed(
            instrument,
            realized_equity_after_exit=Decimal("100000"),
            protective_stop_terminal=adapter.terminal_proof(
                instrument, entry.trade_id),
        )
        assert closed.kind == "BROKER_EXIT_OBSERVED"
        assert runtime.open_positions() == {}
        assert runtime.store.unresolved_intent_count() == 0
        assert adapter.real_order_endpoint_call_count == 0

        return {
            "instrument": instrument,
            "direction": direction,
            "entry_quantity": entry.quantity,
            "entry_expected_position": entry.expected_position_quantity,
            "initial_stop": str(initial_stop.stop_price),
            "tightened_stop": str(tighten.stop_price),
            "active_stop_count_before_exit": 2,
            "final_position": broker_position,
            "terminal_proof": adapter.terminal_proof(
                instrument, entry.trade_id),
            "real_order_endpoint_call_count": adapter.real_order_endpoint_call_count,
        }
    finally:
        runtime.close()


def test_protective_stop_contract_is_structurally_offline():
    path = Path("TradingSystemLab/stage8_robot/protective_stop_contract.py")
    source = path.read_text(encoding="utf-8")
    tree = ast.parse(source)
    imports = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            imports.extend(alias.name for alias in node.names)
        elif isinstance(node, ast.ImportFrom):
            imports.append(node.module or "")
    forbidden = ("finam_api", "broker", "requests", "httpx", "socket", "urllib")
    assert not any(any(term in name for term in forbidden) for name in imports)
    assert "place_order(" not in source
    assert "submit_order(" not in source
    assert CONTRACT_SCHEMA.endswith(".v1")
    assert QTY_MEASURE == "SLTP_QTY_MEASURE_PERCENT"
    assert QTY_PERCENT == Decimal("100")


@pytest.mark.parametrize("instrument", tuple(FROZEN_ECONOMICS))
@pytest.mark.parametrize("direction", ("LONG", "SHORT"))
def test_full_production_path_is_deterministic_all_n4_long_short(
        tmp_path, instrument, direction):
    first = run_end_to_end(
        tmp_path / "first", instrument, direction)
    second = run_end_to_end(
        tmp_path / "second", instrument, direction)
    assert first == second
    assert first["final_position"] == 0
    assert first["terminal_proof"] is True
    assert first["real_order_endpoint_call_count"] == 0


@pytest.mark.parametrize(
    "direction,expected_side",
    (("LONG", "SIDE_SELL"), ("SHORT", "SIDE_BUY")),
)
def test_percent_stop_payload_is_close_only_shape(
        tmp_path, direction, expected_side):
    runtime = ProductionRuntime(tmp_path / f"{direction}.db")
    adapter = SyntheticPercentPositionStopAdapter()
    try:
        budget = runtime.begin_batch(
            realized_equity=Decimal("100000"),
            available_cash=Decimal("1000000"))
        entry = runtime.plan_entry(
            signal("USDRUBF", direction), authority("USDRUBF"),
            realized_equity=Decimal("100000"), budget=budget)
        stop = runtime.confirm_entry_position(
            entry.idempotency_key, entry.expected_position_quantity)
        payload = adapter.payload(stop)
        assert payload["side"] == expected_side
        assert payload["quantity_sl"] == {"value": "100"}
        assert payload["sl_qty_measure"] == "SLTP_QTY_MEASURE_PERCENT"
        assert payload["valid_before"] == "VALID_BEFORE_GOOD_TILL_CANCEL"
        assert "quantity_tp" not in payload
        assert "tp_price" not in payload
    finally:
        runtime.close()


def test_looser_or_duplicate_trailing_stop_is_rejected(tmp_path):
    runtime = ProductionRuntime(tmp_path / "state.db")
    adapter = SyntheticPercentPositionStopAdapter()
    try:
        budget = runtime.begin_batch(
            realized_equity=Decimal("100000"),
            available_cash=Decimal("1000000"))
        entry = runtime.plan_entry(
            signal("USDRUBF", "LONG"), authority("USDRUBF"),
            realized_equity=Decimal("100000"), budget=budget)
        initial = runtime.confirm_entry_position(
            entry.idempotency_key, entry.expected_position_quantity)
        adapter.submit(initial, observed_position_quantity=entry.expected_position_quantity)

        from dataclasses import replace
        looser = replace(
            initial,
            kind="PROTECTIVE_STOP_REPLACE",
            idempotency_key=initial.idempotency_key + ":looser",
            stop_price=initial.stop_price - Decimal("0.01"),
        )
        with pytest.raises(
            ProtectiveStopContractError,
            match="PROTECTIVE_STOP_NOT_TIGHTER",
        ):
            adapter.submit(
                looser, observed_position_quantity=entry.expected_position_quantity)

        with pytest.raises(
            ProtectiveStopContractError,
            match="DUPLICATE_PROTECTIVE_STOP_SUBMISSION",
        ):
            adapter.submit(
                initial, observed_position_quantity=entry.expected_position_quantity)
    finally:
        runtime.close()


def test_wrong_position_blocks_protective_stop(tmp_path):
    runtime = ProductionRuntime(tmp_path / "state.db")
    adapter = SyntheticPercentPositionStopAdapter()
    try:
        budget = runtime.begin_batch(
            realized_equity=Decimal("100000"),
            available_cash=Decimal("1000000"))
        entry = runtime.plan_entry(
            signal("USDRUBF", "SHORT"), authority("USDRUBF"),
            realized_equity=Decimal("100000"), budget=budget)
        stop = runtime.confirm_entry_position(
            entry.idempotency_key, entry.expected_position_quantity)
        with pytest.raises(
            ProtectiveStopContractError,
            match="PROTECTIVE_STOP_POSITION_NOT_EXACT",
        ):
            adapter.submit(stop, observed_position_quantity=0)
    finally:
        runtime.close()


def test_unexpected_broker_position_fails_closed(tmp_path):
    runtime = ProductionRuntime(tmp_path / "state.db")
    try:
        bar = CompletedBar(
            datetime(2026,1,2,11,tzinfo=MSK),
            100,101,99,100,1,completed=True)
        with pytest.raises(
            ProductionRuntimeError,
            match="UNEXPECTED_BROKER_POSITION",
        ):
            runtime.manage_completed_bar(
                "USDRUBF", bar, observed_position_quantity=1)
    finally:
        runtime.close()


def test_unresolved_intent_blocks_new_signal_and_entry(tmp_path):
    runtime = ProductionRuntime(tmp_path / "state.db")
    try:
        budget = runtime.begin_batch(
            realized_equity=Decimal("100000"),
            available_cash=Decimal("1000000"))
        runtime.plan_entry(
            signal("USDRUBF", "LONG"), authority("USDRUBF"),
            realized_equity=Decimal("100000"), budget=budget)
        assert runtime.store.unresolved_intent_count() == 1
        with pytest.raises(
            ProductionRuntimeError,
            match="UNRESOLVED_INTENT_BLOCKS_SIGNAL_EVALUATION",
        ):
            runtime.build_latest_signal("CNYRUBF", None, datetime.now(MSK))
    finally:
        runtime.close()


def test_stale_and_malformed_h1_fail_closed():
    now = datetime(2026,1,2,15,tzinfo=MSK)
    with pytest.raises(ValueError, match="MARKET_DATA_STALE"):
        validate_stream([], now)

    malformed = CompletedBar(
        now - timedelta(hours=1),
        100, 90, 110, 100, 1, completed=True)
    with pytest.raises(ValueError):
        validate_stream([malformed], now)


def test_account_mismatch_and_active_order_fail_closed():
    with pytest.raises(SafetyFault, match="CONFIGURED_REAL_ACCOUNT_NOT_ENUMERATED"):
        _session_is_safe(
            {"readonly": True, "account_ids": ["OTHER"]},
            "EXPECTED",
        )
    assert count_active_orders(
        [{"status": "ORDER_STATUS_NEW"}]) == 1
    with pytest.raises(ValueError):
        count_active_orders([{"status": "ORDER_STATUS_UNSPECIFIED"}])


def test_invalid_or_halted_kill_switch_never_opens_entry_gate(tmp_path):
    now = datetime(2026,1,2,12,tzinfo=MSK)
    missing = evaluate_new_entry_gate(
        runtime_root=tmp_path, now=now, execution_authorized=False)
    assert missing["entry_gate_open"] is False
    assert "KILL_SWITCH_MISSING" in missing["reason_codes"]
    assert "EXECUTION_NOT_AUTHORIZED" in missing["reason_codes"]

    write_kill_switch(tmp_path, "HALTED", now=now)
    halted = evaluate_new_entry_gate(
        runtime_root=tmp_path, now=now, execution_authorized=True)
    assert halted["entry_gate_open"] is False
    assert "KILL_SWITCH_HALTED" in halted["reason_codes"]


def test_zero_capacity_r15_margin_and_six_percent_guards_remain_in_force(tmp_path):
    runtime = ProductionRuntime(tmp_path / "state.db")
    try:
        zero_budget = runtime.begin_batch(
            realized_equity=Decimal("100000"),
            available_cash=Decimal("0"))
        zero = runtime.plan_entry(
            signal("USDRUBF", "LONG"), authority("USDRUBF"),
            realized_equity=Decimal("100000"), budget=zero_budget)
        assert zero.kind == "SKIP_ZERO_CAPACITY"
        assert zero.quantity == 0

        # Re-open a clean runtime because the zero-capacity signal is consumed.
        runtime.close()
        runtime = ProductionRuntime(tmp_path / "risk.db")
        runtime.store.put("production_positions", {
            "CNYRUBF": {"risk_cash": "6000"}
        })
        budget = runtime.begin_batch(
            realized_equity=Decimal("100000"),
            available_cash=Decimal("1000000"))
        before = budget.remaining
        capped = runtime.plan_entry(
            signal("USDRUBF", "LONG"), authority("USDRUBF"),
            realized_equity=Decimal("100000"), budget=budget)
        assert capped.kind == "SKIP_RISK_LIMIT"
        assert budget.remaining == before
    finally:
        runtime.close()
