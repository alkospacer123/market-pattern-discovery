"""Offline protective-stop contract for Stage 8.12.2 conformance.

No FINAM client, broker, authentication, socket, or order endpoint is imported.
The contract models the documented FINAM SL/TP percentage-of-position semantics
so production behavior can be audited before any real-order authorization.

A tighter TRAIL1 stop is added before any older protection is retired. Older
stops remain backstops while the position is open. Synthetic broker state is
durable so replay after a process restart resolves the same client idempotency
key to the same broker stop instead of creating another stop.

When one 100%-of-current-position stop closes the position, other overlapping
stops are *not* assumed terminal. Local closeout remains blocked until every
related stop has separately observed terminal/inactive broker state. Real FINAM
acceptance remains a later operational boundary.
"""
from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal
from pathlib import Path

from .production_runtime import RuntimeAction
from .state import StateStore

CONTRACT_SCHEMA = "stage8_12_percent_position_protective_stop.v2"
QTY_MEASURE = "SLTP_QTY_MEASURE_PERCENT"
QTY_PERCENT = Decimal("100")
VALID_BEFORE = "VALID_BEFORE_GOOD_TILL_CANCEL"
_BROKER_STATE_KEY = "synthetic_percent_position_broker_state"


class ProtectiveStopContractError(RuntimeError):
    pass


@dataclass(frozen=True)
class SyntheticProtectiveStop:
    broker_order_id: str
    idempotency_key: str
    instrument: str
    finam_symbol: str
    direction: str
    quantity: int
    expected_position_quantity: int
    trade_id: str
    stop_price: Decimal
    revision: int
    status: str = "ACTIVE"


class SyntheticPercentPositionStopAdapter:
    """Durable, order-incapable proof model for the protective-stop contract."""

    def __init__(self, state_path: Path):
        state_path = Path(state_path)
        state_path.parent.mkdir(parents=True, exist_ok=True)
        self._store = StateStore(
            state_path,
            {
                "schema_id": CONTRACT_SCHEMA,
                "authority": "SYNTHETIC_OFFLINE_PROTECTIVE_STOP_BROKER",
            },
        )
        raw = self._store.get(_BROKER_STATE_KEY, {"sequence": 0, "stops": {}})
        if (
            not isinstance(raw, dict)
            or type(raw.get("sequence")) is not int
            or raw["sequence"] < 0
            or not isinstance(raw.get("stops"), dict)
        ):
            raise ProtectiveStopContractError("SYNTHETIC_BROKER_STATE_INVALID")
        self._sequence = raw["sequence"]
        self._stops: dict[str, SyntheticProtectiveStop] = {}
        try:
            for broker_id, value in raw["stops"].items():
                if not isinstance(value, dict) or value.get("broker_order_id") != broker_id:
                    raise ValueError
                self._stops[broker_id] = SyntheticProtectiveStop(
                    broker_order_id=broker_id,
                    idempotency_key=str(value["idempotency_key"]),
                    instrument=str(value["instrument"]),
                    finam_symbol=str(value["finam_symbol"]),
                    direction=str(value["direction"]),
                    quantity=int(value["quantity"]),
                    expected_position_quantity=int(value["expected_position_quantity"]),
                    trade_id=str(value["trade_id"]),
                    stop_price=Decimal(str(value["stop_price"])),
                    revision=int(value["revision"]),
                    status=str(value["status"]),
                )
        except Exception as exc:
            raise ProtectiveStopContractError("SYNTHETIC_BROKER_STATE_INVALID") from exc
        if any(stop.status not in {"ACTIVE", "TERMINAL", "INACTIVE"}
               for stop in self._stops.values()):
            raise ProtectiveStopContractError("SYNTHETIC_BROKER_STATE_INVALID")
        if len({stop.idempotency_key for stop in self._stops.values()}) != len(self._stops):
            raise ProtectiveStopContractError("SYNTHETIC_BROKER_IDEMPOTENCY_INVALID")
        self.real_order_endpoint_call_count = 0

    def close(self) -> None:
        self._store.close()

    def _persist(self) -> None:
        self._store.put(_BROKER_STATE_KEY, {
            "sequence": self._sequence,
            "stops": {
                broker_id: {
                    "broker_order_id": stop.broker_order_id,
                    "idempotency_key": stop.idempotency_key,
                    "instrument": stop.instrument,
                    "finam_symbol": stop.finam_symbol,
                    "direction": stop.direction,
                    "quantity": stop.quantity,
                    "expected_position_quantity": stop.expected_position_quantity,
                    "trade_id": stop.trade_id,
                    "stop_price": str(stop.stop_price),
                    "revision": stop.revision,
                    "status": stop.status,
                }
                for broker_id, stop in self._stops.items()
            },
        })

    @staticmethod
    def payload(action: RuntimeAction) -> dict:
        if action.kind not in {"PROTECTIVE_STOP_INSTALL", "PROTECTIVE_STOP_REPLACE"}:
            raise ProtectiveStopContractError("PROTECTIVE_STOP_ACTION_REQUIRED")
        if (
            not action.idempotency_key
            or not action.instrument
            or action.direction not in {"LONG", "SHORT"}
            or action.quantity <= 0
            or not action.trade_id
            or action.stop_price is None
            or type(action.expected_position_quantity) is not int
        ):
            raise ProtectiveStopContractError("PROTECTIVE_STOP_ACTION_INVALID")
        expected = action.quantity if action.direction == "LONG" else -action.quantity
        if action.expected_position_quantity != expected:
            raise ProtectiveStopContractError("PROTECTIVE_STOP_POSITION_AUTHORITY_INVALID")
        return {
            "schema_id": CONTRACT_SCHEMA,
            "symbol": action.finam_symbol,
            "side": "SIDE_SELL" if action.direction == "LONG" else "SIDE_BUY",
            "quantity_sl": {"value": str(QTY_PERCENT)},
            "sl_qty_measure": QTY_MEASURE,
            "sl_price": {"value": str(action.stop_price)},
            "valid_before": VALID_BEFORE,
            "client_order_id": action.idempotency_key[-20:],
            "comment": action.idempotency_key,
        }

    @staticmethod
    def _matches_action(stop: SyntheticProtectiveStop, action: RuntimeAction) -> bool:
        return (
            stop.idempotency_key == action.idempotency_key
            and stop.instrument == action.instrument
            and stop.finam_symbol == action.finam_symbol
            and stop.direction == action.direction
            and stop.quantity == action.quantity
            and stop.expected_position_quantity == action.expected_position_quantity
            and stop.trade_id == action.trade_id
            and stop.stop_price == action.stop_price
        )

    def _existing_for_key(self, key: str) -> SyntheticProtectiveStop | None:
        matches = [stop for stop in self._stops.values() if stop.idempotency_key == key]
        if len(matches) > 1:
            raise ProtectiveStopContractError("SYNTHETIC_BROKER_IDEMPOTENCY_INVALID")
        return matches[0] if matches else None

    def _trade_stops(self, action: RuntimeAction) -> list[SyntheticProtectiveStop]:
        return [
            stop for stop in self._stops.values()
            if stop.instrument == action.instrument
            and stop.trade_id == action.trade_id
            and stop.status == "ACTIVE"
        ]

    def submit(self, action: RuntimeAction, *, observed_position_quantity: int) -> str:
        """Synthetic ACK only. Never contacts FINAM or any order endpoint."""
        self.payload(action)
        existing = self._existing_for_key(action.idempotency_key)
        if existing is not None:
            if not self._matches_action(existing, action):
                raise ProtectiveStopContractError("IDEMPOTENCY_PAYLOAD_MISMATCH")
            if observed_position_quantity != action.expected_position_quantity:
                raise ProtectiveStopContractError("PROTECTIVE_STOP_POSITION_NOT_EXACT")
            return existing.broker_order_id

        if observed_position_quantity != action.expected_position_quantity:
            raise ProtectiveStopContractError("PROTECTIVE_STOP_POSITION_NOT_EXACT")

        active = self._trade_stops(action)
        if action.kind == "PROTECTIVE_STOP_INSTALL" and active:
            raise ProtectiveStopContractError("INITIAL_STOP_ALREADY_ACTIVE")
        if action.kind == "PROTECTIVE_STOP_REPLACE":
            if not active:
                raise ProtectiveStopContractError("REPLACEMENT_REQUIRES_ACTIVE_BACKSTOP")
            effective = max(active, key=lambda stop: stop.revision)
            if action.direction == "LONG" and action.stop_price <= effective.stop_price:
                raise ProtectiveStopContractError("PROTECTIVE_STOP_NOT_TIGHTER")
            if action.direction == "SHORT" and action.stop_price >= effective.stop_price:
                raise ProtectiveStopContractError("PROTECTIVE_STOP_NOT_TIGHTER")

        self._sequence += 1
        revision = 0 if action.kind == "PROTECTIVE_STOP_INSTALL" else max(
            stop.revision for stop in active) + 1
        broker_id = f"synthetic-percent-stop-{self._sequence}"
        self._stops[broker_id] = SyntheticProtectiveStop(
            broker_order_id=broker_id,
            idempotency_key=action.idempotency_key,
            instrument=action.instrument,
            finam_symbol=action.finam_symbol,
            direction=action.direction,
            quantity=action.quantity,
            expected_position_quantity=action.expected_position_quantity,
            trade_id=action.trade_id,
            stop_price=action.stop_price,
            revision=revision,
        )
        self._persist()
        return broker_id

    def active_stops(self, instrument: str, trade_id: str) -> tuple[SyntheticProtectiveStop, ...]:
        return tuple(sorted(
            (
                stop for stop in self._stops.values()
                if stop.instrument == instrument
                and stop.trade_id == trade_id
                and stop.status == "ACTIVE"
            ),
            key=lambda stop: stop.revision,
        ))

    def effective_stop(self, instrument: str, trade_id: str) -> SyntheticProtectiveStop:
        active = self.active_stops(instrument, trade_id)
        if not active:
            raise ProtectiveStopContractError("NO_ACTIVE_PROTECTIVE_STOP")
        return active[-1]

    def trigger(self, instrument: str, trade_id: str, *,
                observed_position_quantity: int, price: Decimal) -> int:
        """Model one percentage-of-current-position stop flattening the position."""
        if observed_position_quantity == 0:
            return 0
        active = self.active_stops(instrument, trade_id)
        if not active:
            raise ProtectiveStopContractError("NO_ACTIVE_PROTECTIVE_STOP")
        directions = {stop.direction for stop in active}
        if len(directions) != 1:
            raise ProtectiveStopContractError("PROTECTIVE_STOP_DIRECTION_MISMATCH")
        direction = active[-1].direction
        triggered = [
            stop for stop in active
            if (direction == "LONG" and price <= stop.stop_price)
            or (direction == "SHORT" and price >= stop.stop_price)
        ]
        if not triggered:
            return observed_position_quantity

        # The tightest triggered 100%-of-current-position stop is sufficient to
        # flatten the current position. Other stops remain ACTIVE until an
        # independent broker observation proves them terminal/inactive.
        executed = (
            max(triggered, key=lambda stop: stop.stop_price)
            if direction == "LONG"
            else min(triggered, key=lambda stop: stop.stop_price)
        )
        self._stops[executed.broker_order_id] = SyntheticProtectiveStop(
            **{**executed.__dict__, "status": "TERMINAL"}
        )
        self._persist()
        return 0

    def observe_inactive(self, broker_order_id: str, *,
                         observed_position_quantity: int) -> None:
        """Record GET/reconciliation proof that a remaining stop is inactive."""
        if observed_position_quantity != 0:
            raise ProtectiveStopContractError("INACTIVE_PROOF_REQUIRES_FLAT_POSITION")
        stop = self._stops.get(broker_order_id)
        if stop is None:
            raise ProtectiveStopContractError("PROTECTIVE_STOP_NOT_FOUND")
        if stop.status in {"TERMINAL", "INACTIVE"}:
            return
        if stop.status != "ACTIVE":
            raise ProtectiveStopContractError("PROTECTIVE_STOP_STATUS_INVALID")
        self._stops[broker_order_id] = SyntheticProtectiveStop(
            **{**stop.__dict__, "status": "INACTIVE"}
        )
        self._persist()

    def terminal_proof(self, instrument: str, trade_id: str) -> bool:
        related = [
            stop for stop in self._stops.values()
            if stop.instrument == instrument and stop.trade_id == trade_id
        ]
        return bool(related) and all(
            stop.status in {"TERMINAL", "INACTIVE"} for stop in related)
