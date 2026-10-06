from __future__ import annotations

import ast
from datetime import datetime, timedelta
from decimal import Decimal
from pathlib import Path
from zoneinfo import ZoneInfo

import pandas as pd
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
ENTRY_OBSERVED_AT = datetime(2026, 1, 2, 10, 5, tzinfo=MSK)
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


def bars(
        direction: str, entry: float = 100.0,
        signal_time: datetime | None = None) -> tuple[CompletedBar, CompletedBar]:
    signal_time = signal_time or datetime(2026,1,2,10,tzinfo=MSK)
    first_time = signal_time + timedelta(hours=1)
    second_time = signal_time + timedelta(hours=2)
    if direction == "LONG":
        return (
            CompletedBar(
                first_time,
                entry, entry + 6, entry, entry + 5, 2, completed=True),
            CompletedBar(
                second_time,
                entry + 5, entry + 7, entry + 1, entry + 6, 2, completed=True),
        )
    return (
        CompletedBar(
            first_time,
            entry, entry, entry - 6, entry - 5, 2, completed=True),
        CompletedBar(
            second_time,
            entry - 5, entry - 1, entry - 7, entry - 6, 2, completed=True),
    )


def genuine_h1_frame(direction: str) -> pd.DataFrame:
    """Synthetic completed H1 bars consumed by the real causal T3ContextBuilder."""
    start = pd.Timestamp("2026-01-01T10:00:00", tz="Europe/Moscow")
    price = 200.0
    sign = 1.0 if direction == "LONG" else -1.0
    rows: list[tuple[float, float, float, float]] = []
    index: list[pd.Timestamp] = []
    for day in range(130):
        day_start = start + pd.Timedelta(days=day)
        deltas = (
            [sign * 0.25, 0.0, 0.0, 0.0]
            if day < 110
            else [sign * 0.75] * 4
        )
        for hour, delta in enumerate(deltas):
            open_price = price
            close_price = price + delta
            padding = (1.0 - abs(delta)) / 2.0
            high = max(open_price, close_price) + padding
            low = min(open_price, close_price) - padding
            index.append(day_start + pd.Timedelta(hours=hour))
            rows.append((open_price, high, low, close_price))
            price = close_price
    return pd.DataFrame(
        rows,
        index=pd.DatetimeIndex(index),
        columns=["Open", "High", "Low", "Close"],
    )


def genuine_t3_signal(runtime: ProductionRuntime, instrument: str, direction: str) -> SignalIntent:
    frame = genuine_h1_frame(direction)
    signal_intent = runtime.build_latest_signal(
        instrument, frame, frame.index[-1].to_pydatetime())
    assert signal_intent is not None
    assert signal_intent.instrument == instrument
    assert signal_intent.direction == direction
    assert signal_intent.entry == (287.5 if direction == "LONG" else 112.5)
    assert signal_intent.initial_r == 2.5
    expected_stop = Decimal("285.0") if direction == "LONG" else Decimal("115.0")
    assert Decimal(str(signal_intent.initial_stop)) == expected_stop
    step, _ = FROZEN_ECONOMICS[instrument]
    assert Decimal(str(signal_intent.initial_r)) / step == (
        Decimal(str(signal_intent.initial_r)) / step).to_integral_value()
    return signal_intent


def run_end_to_end(root: Path, instrument: str, direction: str) -> dict:
    runtime = ProductionRuntime(root / "production.sqlite3")
    adapter = SyntheticPercentPositionStopAdapter(root / "synthetic-broker.sqlite3")
    try:
        budget = runtime.begin_batch(
            realized_equity=Decimal("1000000"),
            available_cash=Decimal("1000000"),
        )
        genuine_signal = genuine_t3_signal(runtime, instrument, direction)
        entry = runtime.plan_entry(
            genuine_signal,
            authority(instrument),
            realized_equity=Decimal("1000000"),
            budget=budget,
        )
        assert entry.kind == "ENTRY"
        assert entry.quantity > 0
        broker_position = entry.expected_position_quantity

        entry_observed_at = genuine_signal.timestamp + timedelta(minutes=5)
        initial_stop = runtime.confirm_entry_position(
            entry.idempotency_key, broker_position,
            observed_at=entry_observed_at)
        assert initial_stop.kind == "PROTECTIVE_STOP_INSTALL"

        # An accepted position is not considered safe before broker-confirmed
        # protection. No next-bar progression is allowed through this gap.
        first_bar, second_bar = bars(
            direction,
            entry=float(genuine_signal.entry),
            signal_time=genuine_signal.timestamp,
        )
        assert first_bar.timestamp > genuine_signal.timestamp
        assert second_bar.timestamp > first_bar.timestamp
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
        # Only the actually executed stop is terminal. The older backstop must
        # remain unproven until a separate broker observation says inactive.
        assert adapter.terminal_proof(instrument, entry.trade_id) is False
        remaining = adapter.active_stops(instrument, entry.trade_id)
        assert len(remaining) == 1
        with pytest.raises(
            ProductionRuntimeError,
            match="PROTECTIVE_STOP_TERMINAL_PROOF_REQUIRED",
        ):
            runtime.broker_exit_observed(
                instrument,
                realized_equity_after_exit=Decimal("1000000"),
                protective_stop_terminal=False,
            )
        assert adapter.trigger(
            instrument, entry.trade_id,
            observed_position_quantity=0,
            price=new_effective.stop_price,
        ) == 0
        for stop in remaining:
            with pytest.raises(
                ProtectiveStopContractError,
                match="PROTECTIVE_STOP_NOT_TERMINAL_OR_INACTIVE",
            ):
                adapter.observe_terminal_or_inactive(
                    stop.broker_order_id,
                    observed_status="ACTIVE",
                    observed_position_quantity=0,
                )
            adapter.observe_terminal_or_inactive(
                stop.broker_order_id,
                observed_status="INACTIVE",
                observed_position_quantity=0,
            )
        assert adapter.terminal_proof(instrument, entry.trade_id) is True

        observed = runtime.manage_completed_bar(
            instrument,
            CompletedBar(
                genuine_signal.timestamp + timedelta(hours=3),
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
            realized_equity_after_exit=Decimal("1000000"),
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
        adapter.close()
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
    assert CONTRACT_SCHEMA.endswith(".v2")
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
    adapter = SyntheticPercentPositionStopAdapter(tmp_path / f"{direction}-broker.db")
    try:
        budget = runtime.begin_batch(
            realized_equity=Decimal("100000"),
            available_cash=Decimal("1000000"))
        entry = runtime.plan_entry(
            signal("USDRUBF", direction), authority("USDRUBF"),
            realized_equity=Decimal("100000"), budget=budget)
        stop = runtime.confirm_entry_position(
            entry.idempotency_key, entry.expected_position_quantity,
            observed_at=ENTRY_OBSERVED_AT)
        payload = adapter.payload(stop)
        assert payload["side"] == expected_side
        assert payload["quantity_sl"] == {"value": "100"}
        assert payload["sl_qty_measure"] == "SLTP_QTY_MEASURE_PERCENT"
        assert payload["valid_before"] == "VALID_BEFORE_GOOD_TILL_CANCEL"
        assert "quantity_tp" not in payload
        assert "tp_price" not in payload
    finally:
        adapter.close()
        runtime.close()


def test_looser_trailing_stop_rejected_and_duplicate_is_idempotent(tmp_path):
    runtime = ProductionRuntime(tmp_path / "state.db")
    adapter = SyntheticPercentPositionStopAdapter(tmp_path / "looser-broker.db")
    try:
        budget = runtime.begin_batch(
            realized_equity=Decimal("100000"),
            available_cash=Decimal("1000000"))
        entry = runtime.plan_entry(
            signal("USDRUBF", "LONG"), authority("USDRUBF"),
            realized_equity=Decimal("100000"), budget=budget)
        initial = runtime.confirm_entry_position(
            entry.idempotency_key, entry.expected_position_quantity,
            observed_at=ENTRY_OBSERVED_AT)
        first_id = adapter.submit(
            initial, observed_position_quantity=entry.expected_position_quantity)

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

        replay_id = adapter.submit(
            initial, observed_position_quantity=entry.expected_position_quantity)
        assert replay_id == first_id
        assert len(adapter.active_stops("USDRUBF", entry.trade_id)) == 1
    finally:
        adapter.close()
        runtime.close()


def test_protective_stop_restart_reuses_same_broker_stop(tmp_path):
    runtime_path = tmp_path / "runtime.db"
    broker_path = tmp_path / "synthetic-broker.db"
    runtime = ProductionRuntime(runtime_path)
    adapter = SyntheticPercentPositionStopAdapter(broker_path)
    budget = runtime.begin_batch(
        realized_equity=Decimal("100000"),
        available_cash=Decimal("1000000"))
    entry = runtime.plan_entry(
        signal("USDRUBF", "LONG"), authority("USDRUBF"),
        realized_equity=Decimal("100000"), budget=budget)
    stop = runtime.confirm_entry_position(
        entry.idempotency_key, entry.expected_position_quantity,
        observed_at=ENTRY_OBSERVED_AT)
    broker_id = adapter.submit(
        stop, observed_position_quantity=entry.expected_position_quantity)

    # Crash boundary: broker accepted the stop, but local confirmation did not
    # happen yet. Both sides are reopened from durable state.
    adapter.close()
    runtime.close()
    runtime = ProductionRuntime(runtime_path)
    adapter = SyntheticPercentPositionStopAdapter(broker_path)
    try:
        recovered = runtime.recover_pending_protective_stop("USDRUBF")
        assert recovered == stop
        replay_id = adapter.submit(
            recovered, observed_position_quantity=entry.expected_position_quantity)
        assert replay_id == broker_id
        assert len(adapter.active_stops("USDRUBF", entry.trade_id)) == 1
        runtime.confirm_protective_stop(recovered.idempotency_key, replay_id)
        assert runtime.store.unresolved_intent_count() == 0
    finally:
        adapter.close()
        runtime.close()


def test_trailing_stop_restart_reuses_same_broker_stop(tmp_path):
    runtime_path = tmp_path / "runtime.db"
    broker_path = tmp_path / "synthetic-broker.db"
    runtime = ProductionRuntime(runtime_path)
    adapter = SyntheticPercentPositionStopAdapter(broker_path)
    budget = runtime.begin_batch(
        realized_equity=Decimal("100000"),
        available_cash=Decimal("1000000"))
    entry = runtime.plan_entry(
        signal("USDRUBF", "LONG"), authority("USDRUBF"),
        realized_equity=Decimal("100000"), budget=budget)
    initial = runtime.confirm_entry_position(
        entry.idempotency_key, entry.expected_position_quantity,
        observed_at=ENTRY_OBSERVED_AT)
    initial_id = adapter.submit(
        initial, observed_position_quantity=entry.expected_position_quantity)
    runtime.confirm_protective_stop(initial.idempotency_key, initial_id)
    first_bar, second_bar = bars("LONG")
    assert runtime.manage_completed_bar(
        "USDRUBF", first_bar,
        observed_position_quantity=entry.expected_position_quantity) is None
    tighten = runtime.manage_completed_bar(
        "USDRUBF", second_bar,
        observed_position_quantity=entry.expected_position_quantity)
    replacement_id = adapter.submit(
        tighten, observed_position_quantity=entry.expected_position_quantity)

    adapter.close()
    runtime.close()
    runtime = ProductionRuntime(runtime_path)
    adapter = SyntheticPercentPositionStopAdapter(broker_path)
    try:
        recovered = runtime.recover_pending_protective_stop("USDRUBF")
        assert recovered == tighten
        replay_id = adapter.submit(
            recovered, observed_position_quantity=entry.expected_position_quantity)
        assert replay_id == replacement_id
        assert len(adapter.active_stops("USDRUBF", entry.trade_id)) == 2
        runtime.confirm_protective_stop(recovered.idempotency_key, replay_id)
        assert runtime.store.unresolved_intent_count() == 0
    finally:
        adapter.close()
        runtime.close()


@pytest.mark.parametrize("persisted_status", ("ACK", "RECONCILED"))
def test_stop_confirmation_crash_window_recovers_without_resubmission(
        tmp_path, persisted_status):
    runtime_path = tmp_path / f"runtime-{persisted_status}.db"
    broker_path = tmp_path / f"broker-{persisted_status}.db"
    runtime = ProductionRuntime(runtime_path)
    adapter = SyntheticPercentPositionStopAdapter(broker_path)
    budget = runtime.begin_batch(
        realized_equity=Decimal("100000"),
        available_cash=Decimal("1000000"))
    entry = runtime.plan_entry(
        signal("USDRUBF", "LONG"), authority("USDRUBF"),
        realized_equity=Decimal("100000"), budget=budget)
    stop = runtime.confirm_entry_position(
        entry.idempotency_key, entry.expected_position_quantity,
        observed_at=ENTRY_OBSERVED_AT)
    broker_id = adapter.submit(
        stop, observed_position_quantity=entry.expected_position_quantity)

    # Simulate a crash after broker identity became durable but before the
    # protected-position state was saved.
    runtime.store.transition_intent(stop.idempotency_key, "ACK", broker_id)
    if persisted_status == "RECONCILED":
        runtime.store.transition_intent(
            stop.idempotency_key, "RECONCILED", broker_id)
    adapter.close()
    runtime.close()

    runtime = ProductionRuntime(runtime_path)
    adapter = SyntheticPercentPositionStopAdapter(broker_path)
    try:
        assert runtime.open_positions()["USDRUBF"]["protective_stop_state"] == "PENDING"
        assert runtime.recover_pending_protective_stop("USDRUBF") is None
        position = runtime.open_positions()["USDRUBF"]
        assert position["protective_stop_state"] == "ACTIVE"
        assert position["protective_stop_broker_order_id"] == broker_id
        assert runtime.store.intent(stop.idempotency_key)["status"] == "RECONCILED"
        assert runtime.store.unresolved_intent_count() == 0
        assert len(adapter.active_stops("USDRUBF", entry.trade_id)) == 1
    finally:
        adapter.close()
        runtime.close()


def test_replacement_intent_crash_before_pending_state_is_recovered(tmp_path):
    runtime_path = tmp_path / "runtime.db"
    broker_path = tmp_path / "broker.db"
    runtime = ProductionRuntime(runtime_path)
    adapter = SyntheticPercentPositionStopAdapter(broker_path)
    budget = runtime.begin_batch(
        realized_equity=Decimal("100000"),
        available_cash=Decimal("1000000"))
    entry_signal = signal("USDRUBF", "LONG")
    entry = runtime.plan_entry(
        entry_signal, authority("USDRUBF"),
        realized_equity=Decimal("100000"), budget=budget)
    initial = runtime.confirm_entry_position(
        entry.idempotency_key, entry.expected_position_quantity,
        observed_at=ENTRY_OBSERVED_AT)
    initial_id = adapter.submit(
        initial, observed_position_quantity=entry.expected_position_quantity)
    runtime.confirm_protective_stop(initial.idempotency_key, initial_id)

    first_bar, second_bar = bars(
        "LONG", signal_time=entry_signal.timestamp)
    assert runtime.manage_completed_bar(
        "USDRUBF", first_bar,
        observed_position_quantity=entry.expected_position_quantity) is None
    replacement = runtime.manage_completed_bar(
        "USDRUBF", second_bar,
        observed_position_quantity=entry.expected_position_quantity)
    assert replacement.kind == "PROTECTIVE_STOP_REPLACE"

    # Recreate the exact crash boundary after durable replacement intent
    # persistence but before PENDING_REPLACE/revision were durably saved.
    positions = runtime.open_positions()
    positions["USDRUBF"]["protective_stop_state"] = "ACTIVE"
    positions["USDRUBF"]["protective_stop_revision"] = 0
    runtime._save_positions(positions)
    assert runtime.store.unresolved_intent_count() == 1
    adapter.close()
    runtime.close()

    runtime = ProductionRuntime(runtime_path)
    adapter = SyntheticPercentPositionStopAdapter(broker_path)
    try:
        recovered = runtime.recover_pending_protective_stop("USDRUBF")
        assert recovered == replacement
        state = runtime.open_positions()["USDRUBF"]
        assert state["protective_stop_state"] == "PENDING_REPLACE"
        assert state["protective_stop_revision"] == 1
        replacement_id = adapter.submit(
            recovered, observed_position_quantity=entry.expected_position_quantity)
        runtime.confirm_protective_stop(
            recovered.idempotency_key, replacement_id)
        state = runtime.open_positions()["USDRUBF"]
        assert state["protective_stop_state"] == "ACTIVE"
        assert state["protective_stop_revision"] == 1
        assert state["protective_stop_broker_order_id"] == replacement_id
        assert runtime.store.unresolved_intent_count() == 0
        assert len(adapter.active_stops("USDRUBF", entry.trade_id)) == 2
    finally:
        adapter.close()
        runtime.close()


def test_management_bar_at_or_before_signal_fails_closed(tmp_path):
    runtime = ProductionRuntime(tmp_path / "runtime.db")
    adapter = SyntheticPercentPositionStopAdapter(tmp_path / "broker.db")
    try:
        budget = runtime.begin_batch(
            realized_equity=Decimal("100000"),
            available_cash=Decimal("1000000"))
        entry_signal = signal("USDRUBF", "LONG")
        entry = runtime.plan_entry(
            entry_signal, authority("USDRUBF"),
            realized_equity=Decimal("100000"), budget=budget)
        stop = runtime.confirm_entry_position(
            entry.idempotency_key, entry.expected_position_quantity,
            observed_at=ENTRY_OBSERVED_AT)
        stop_id = adapter.submit(
            stop, observed_position_quantity=entry.expected_position_quantity)
        runtime.confirm_protective_stop(stop.idempotency_key, stop_id)

        same_time = CompletedBar(
            entry_signal.timestamp, 100, 101, 99, 100, 1, completed=True)
        with pytest.raises(
            ProductionRuntimeError,
            match="BAR_NOT_AFTER_ENTRY_SIGNAL",
        ):
            runtime.manage_completed_bar(
                "USDRUBF", same_time,
                observed_position_quantity=entry.expected_position_quantity)

        earlier = CompletedBar(
            entry_signal.timestamp - timedelta(hours=1),
            100, 101, 99, 100, 1, completed=True)
        with pytest.raises(
            ProductionRuntimeError,
            match="BAR_NOT_AFTER_ENTRY_SIGNAL",
        ):
            runtime.manage_completed_bar(
                "USDRUBF", earlier,
                observed_position_quantity=entry.expected_position_quantity)
    finally:
        adapter.close()
        runtime.close()


def test_delayed_entry_observation_blocks_pre_fill_management_bars(tmp_path):
    runtime = ProductionRuntime(tmp_path / "runtime.db")
    adapter = SyntheticPercentPositionStopAdapter(tmp_path / "broker.db")
    try:
        entry_signal = signal("USDRUBF", "LONG")
        budget = runtime.begin_batch(
            realized_equity=Decimal("100000"),
            available_cash=Decimal("1000000"))
        entry = runtime.plan_entry(
            entry_signal, authority("USDRUBF"),
            realized_equity=Decimal("100000"), budget=budget)

        assert runtime.confirm_entry_position(
            entry.idempotency_key, 0,
            observed_at=entry_signal.timestamp + timedelta(minutes=5),
        ) is None

        delayed_observation = entry_signal.timestamp + timedelta(
            hours=2, minutes=5)
        stop = runtime.confirm_entry_position(
            entry.idempotency_key, entry.expected_position_quantity,
            observed_at=delayed_observation,
        )
        stop_id = adapter.submit(
            stop, observed_position_quantity=entry.expected_position_quantity)
        runtime.confirm_protective_stop(stop.idempotency_key, stop_id)
        assert runtime.open_positions()["USDRUBF"]["entry_observed_at"] == (
            delayed_observation.isoformat())

        for timestamp in (
            entry_signal.timestamp + timedelta(hours=1),
            entry_signal.timestamp + timedelta(hours=2),
        ):
            with pytest.raises(
                ProductionRuntimeError,
                match="BAR_NOT_AFTER_ENTRY_OBSERVATION",
            ):
                runtime.manage_completed_bar(
                    "USDRUBF",
                    CompletedBar(
                        timestamp, 100, 100.01, 99.99, 100, 1,
                        completed=True),
                    observed_position_quantity=entry.expected_position_quantity,
                )

        assert runtime.manage_completed_bar(
            "USDRUBF",
            CompletedBar(
                entry_signal.timestamp + timedelta(hours=3),
                100, 100.01, 99.99, 100, 1, completed=True),
            observed_position_quantity=entry.expected_position_quantity,
        ) is None
    finally:
        adapter.close()
        runtime.close()


def test_pending_signal_and_entry_restart_cannot_duplicate(tmp_path):
    runtime_path = tmp_path / "runtime.db"
    runtime = ProductionRuntime(runtime_path)
    first = genuine_t3_signal(runtime, "USDRUBF", "LONG")
    runtime.close()

    runtime = ProductionRuntime(runtime_path)
    try:
        repeated = runtime.build_latest_signal(
            "USDRUBF", None, first.timestamp)
        assert repeated == first
        budget = runtime.begin_batch(
            realized_equity=Decimal("1000000"),
            available_cash=Decimal("1000000"))
        entry = runtime.plan_entry(
            repeated, authority("USDRUBF"),
            realized_equity=Decimal("1000000"), budget=budget)
        assert runtime.store.unresolved_intent_count() == 1
    finally:
        runtime.close()

    runtime = ProductionRuntime(runtime_path)
    try:
        assert runtime.store.unresolved_intent_count() == 1
        budget = runtime.begin_batch(
            realized_equity=Decimal("1000000"),
            available_cash=Decimal("1000000"))
        with pytest.raises(
            ProductionRuntimeError,
            match="UNRESOLVED_INTENT_BLOCKS_NEW_ENTRY",
        ):
            runtime.plan_entry(
                repeated, authority("USDRUBF"),
                realized_equity=Decimal("1000000"), budget=budget)
        assert runtime.store.unresolved_intent_count() == 1
        assert runtime.store.intent(entry.idempotency_key) is not None
    finally:
        runtime.close()


def test_same_batch_margin_reservation_blocks_overallocation(tmp_path):
    runtime = ProductionRuntime(tmp_path / "runtime.db")
    try:
        budget = runtime.begin_batch(
            realized_equity=Decimal("100000"),
            available_cash=Decimal("150"))
        first = runtime.plan_entry(
            signal("USDRUBF", "LONG"), authority("USDRUBF"),
            realized_equity=Decimal("100000"), budget=budget)
        assert first.kind == "ENTRY"
        assert first.quantity == 1
        assert budget.remaining == Decimal("50")

        stop = runtime.confirm_entry_position(
            first.idempotency_key, first.expected_position_quantity,
            observed_at=ENTRY_OBSERVED_AT)
        runtime.confirm_protective_stop(stop.idempotency_key, "synthetic-stop")

        second = runtime.plan_entry(
            signal("CNYRUBF", "LONG"), authority("CNYRUBF"),
            realized_equity=Decimal("100000"), budget=budget)
        assert second.kind == "SKIP_ZERO_CAPACITY"
        assert second.quantity == 0
        assert budget.remaining == Decimal("50")
    finally:
        runtime.close()


def test_wrong_position_blocks_protective_stop(tmp_path):
    runtime = ProductionRuntime(tmp_path / "state.db")
    adapter = SyntheticPercentPositionStopAdapter(tmp_path / "wrong-position-broker.db")
    try:
        budget = runtime.begin_batch(
            realized_equity=Decimal("100000"),
            available_cash=Decimal("1000000"))
        entry = runtime.plan_entry(
            signal("USDRUBF", "SHORT"), authority("USDRUBF"),
            realized_equity=Decimal("100000"), budget=budget)
        stop = runtime.confirm_entry_position(
            entry.idempotency_key, entry.expected_position_quantity,
            observed_at=ENTRY_OBSERVED_AT)
        with pytest.raises(
            ProtectiveStopContractError,
            match="PROTECTIVE_STOP_POSITION_NOT_EXACT",
        ):
            adapter.submit(stop, observed_position_quantity=0)
    finally:
        adapter.close()
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
