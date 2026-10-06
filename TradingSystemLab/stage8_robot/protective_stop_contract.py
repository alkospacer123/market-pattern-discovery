"""Offline protective-stop contract for Stage 8.12.2 conformance.

No FINAM client, broker, authentication, socket, or order endpoint is imported.
The contract models the documented FINAM SL/TP percentage-of-position semantics
so production behavior can be audited before any real-order authorization.

A tighter TRAIL1 stop is added before any older protection is retired. Older
stops remain backstops during the open position. Synthetic execution uses 100%
of the position at execution time, so once one protective stop closes the
position, remaining protective stops have zero position quantity to close.
Real FINAM acceptance remains a later operational boundary.
"""
from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal

from .production_runtime import RuntimeAction

CONTRACT_SCHEMA = "stage8_12_percent_position_protective_stop.v1"
QTY_MEASURE = "SLTP_QTY_MEASURE_PERCENT"
QTY_PERCENT = Decimal("100")
VALID_BEFORE = "VALID_BEFORE_GOOD_TILL_CANCEL"


class ProtectiveStopContractError(RuntimeError):
    pass


@dataclass(frozen=True)
class SyntheticProtectiveStop:
    broker_order_id: str
    idempotency_key: str
    instrument: str
    direction: str
    trade_id: str
    stop_price: Decimal
    revision: int
    status: str = "ACTIVE"


class SyntheticPercentPositionStopAdapter:
    """Order-incapable proof model for the protective-stop adapter contract."""

    def __init__(self):
        self._sequence = 0
        self._stops: dict[str, SyntheticProtectiveStop] = {}
        self._keys: set[str] = set()
        self.real_order_endpoint_call_count = 0

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
        if action.idempotency_key in self._keys:
            raise ProtectiveStopContractError("DUPLICATE_PROTECTIVE_STOP_SUBMISSION")
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
            direction=action.direction,
            trade_id=action.trade_id,
            stop_price=action.stop_price,
            revision=revision,
        )
        self._keys.add(action.idempotency_key)
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
        """Model documented percentage-of-current-position execution semantics."""
        active = self.active_stops(instrument, trade_id)
        if not active:
            raise ProtectiveStopContractError("NO_ACTIVE_PROTECTIVE_STOP")
        if observed_position_quantity == 0:
            return 0

        direction = active[-1].direction
        triggered = [
            stop for stop in active
            if (direction == "LONG" and price <= stop.stop_price)
            or (direction == "SHORT" and price >= stop.stop_price)
        ]
        if not triggered:
            return observed_position_quantity

        # First triggered 100%-of-current-position stop closes the position.
        # All remaining percentage stops then have zero current position to close.
        for broker_id, stop in tuple(self._stops.items()):
            if stop.instrument == instrument and stop.trade_id == trade_id:
                self._stops[broker_id] = SyntheticProtectiveStop(
                    **{**stop.__dict__, "status": "TERMINAL"}
                )
        return 0

    def terminal_proof(self, instrument: str, trade_id: str) -> bool:
        related = [
            stop for stop in self._stops.values()
            if stop.instrument == instrument and stop.trade_id == trade_id
        ]
        return bool(related) and all(stop.status == "TERMINAL" for stop in related)
