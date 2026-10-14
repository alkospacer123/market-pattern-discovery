"""PR #493 task 1.2: FINAM-backed port for the existing operator harness.

Candidate-only dependency-injected adapter. It has no CLI, credential loader,
authorization file writer, Task control, or production SQLite access.
Real trading methods are CLOSED unless a separately reviewed external
operator_write_gate is supplied. Constructing or reading it does not authorize
an order; it never retries an uncertain POST/DELETE.
"""
from __future__ import annotations

from datetime import datetime, timezone
from decimal import Decimal, InvalidOperation
import hashlib
from typing import Callable

from TradingSystemLab.stage8_robot.broker import compact_client_order_id
from TradingSystemLab.stage8_robot.finam_api import (
    MARKET_ORDER_TYPE, TIME_IN_FORCE_DAY,
)
from TradingSystemLab.stage8_robot.diagnostics.stage8_493_finam_readonly_observation import (
    account_orders_snapshot, linked_history_fills, _time,
)
from TradingSystemLab.stage8_robot.diagnostics.stage8_493_operator_harness import (
    Hold, Plan,
)

_STOP_MEASURE = "SLTP_QTY_MEASURE_PERCENT"
_STOP_VALIDITY = "VALID_BEFORE_GOOD_TILL_CANCEL"
_N4_STEP = {"USDRUBF": "0.01", "CNYRUBF": "0.001",
            "GLDRUBF": "0.1", "IMOEXF": "0.5"}


def _positive_price(price: str) -> Decimal:
    if type(price) is not str:
        raise Hold("OPERATOR_PRICE_INVALID")
    try:
        value = Decimal(price)
    except InvalidOperation:
        raise Hold("OPERATOR_PRICE_INVALID") from None
    if not value.is_finite() or value <= 0:
        raise Hold("OPERATOR_PRICE_INVALID")
    return value


def _ack(reply) -> str:
    oid = reply.get("order_id") if isinstance(reply, dict) else None
    if not isinstance(oid, str) or not oid:
        raise Hold("BROKER_ACK_ORDER_ID_UNPROVEN")
    return oid


class FinamOperatorPort:
    """Concrete FINAM read/write interface for the *existing* OperatorHarness.

    The separate write_gate must verify current operator authorization, cash
    budget, Task isolation, broker identity, active session and plan outside
    this candidate module. No gate => zero order/cancel endpoints. The harness
    persists intents before invoking any write; uncertain responses are NOT
    retried here, including across process restarts.
    """

    def __init__(self, *, api, account_id: str, plan: Plan,
                 history_start: str, history_limit: int = 1000,
                 operator_write_gate: Callable[[str, Plan], None] | None = None):
        plan.check()
        if (type(account_id) is not str or not account_id
                or hashlib.sha256(account_id.encode()).hexdigest() != plan.account_hash
                or type(history_limit) is not int or not 0 < history_limit <= 1000
                or _time(history_start) >= datetime.now(timezone.utc)):
            raise Hold("OPERATOR_PORT_BINDING_INVALID")
        self.api, self.account_id, self.plan = api, account_id, plan
        self.history_start, self.history_limit = history_start, history_limit
        self.operator_write_gate = operator_write_gate
        self.connected = False
        self.write_capable = False
        self._sent = set()

    def connect(self) -> None:
        """Session authentication only; this is not an order endpoint."""
        if self.connected:
            raise Hold("OPERATOR_PORT_ALREADY_CONNECTED")
        self.api.create_session()
        details = self.api.session_details()
        if (not isinstance(details, dict)
                or not isinstance(details.get("account_ids"), list)
                or details["account_ids"].count(self.account_id) != 1
                or type(details.get("readonly")) is not bool):
            raise Hold("FINAM_OPERATOR_SESSION_NOT_ACCOUNT_BOUND")
        self.write_capable = details["readonly"] is False
        account = self.api.account(self.account_id)
        if (not isinstance(account, dict)
                or account.get("account_id") != self.account_id
                or account.get("status") not in {"ACCOUNT_ACTIVE", "ACCOUNT_STATUS_ACTIVE"}):
            raise Hold("FINAM_OPERATOR_ACCOUNT_INVALID")
        self.connected = True

    def _connected(self) -> None:
        if not self.connected:
            raise Hold("FINAM_OPERATOR_PORT_NOT_CONNECTED")

    def observe(self) -> dict:
        self._connected()
        account = self.api.account(self.account_id)
        if (not isinstance(account, dict) or account.get("account_id") != self.account_id
                or account.get("status") not in {"ACCOUNT_ACTIVE", "ACCOUNT_STATUS_ACTIVE"}):
            raise Hold("FINAM_OPERATOR_ACCOUNT_CHANGED")
        orders = self.api.orders(self.account_id)
        # This existing parser checks exact position/order schema and broker ID.
        return account_orders_snapshot(account, orders,
                                       account_id=self.account_id, symbol=self.plan.symbol)

    def fills(self, order_id: str) -> list[dict]:
        self._connected()
        if type(order_id) is not str or not order_id:
            raise Hold("ENTRY_FILL_ORDER_ID_INVALID")
        end = datetime.now(timezone.utc).isoformat()
        if _time(self.history_start) >= _time(end):
            raise Hold("FILL_HISTORY_WINDOW_INVALID")
        response = self.api.trades(self.account_id, start=self.history_start,
                                   end=end, limit=self.history_limit)
        # A complete bounded response is mandatory; no fallback to position
        # quantity, order ACK or synthetic average execution price.
        return linked_history_fills(response, account_id=self.account_id,
                                    order_id=order_id, symbol=self.plan.symbol,
                                    side="SIDE_BUY" if self.plan.direction == "LONG" else "SIDE_SELL",
                                    price_step=_N4_STEP[self.plan.instrument],
                                    start=self.history_start, end=end, limit=self.history_limit)

    def _permit(self, action: str, key: str, *, expected_key: str | None = None) -> None:
        self._connected()
        if (not self.write_capable or self.operator_write_gate is None
                or not callable(self.operator_write_gate)):
            raise Hold("REAL_ORDER_GATE_NOT_AUTHORIZED")
        if (type(key) is not str or not key or len(key) > 128
                or (expected_key is not None and key != expected_key)
                or (action, key) in self._sent):
            raise Hold("REAL_ORDER_OPERATION_OR_KEY_INVALID")
        # This hook must be provided by the subsequently independently
        # approved operator-only execution runner, NOT by this PR.
        self.operator_write_gate(action, self.plan)
        self._sent.add((action, key))  # sticky BEFORE endpoint: no same-process retry.

    @staticmethod
    def _side(side: str) -> None:
        if side not in {"SIDE_BUY", "SIDE_SELL"}:
            raise Hold("FINAM_SIDE_INVALID")

    def entry(self, *, key: str, symbol: str, side: str, quantity: int) -> str:
        expected_side = "SIDE_BUY" if self.plan.direction == "LONG" else "SIDE_SELL"
        if (symbol != self.plan.symbol or side != expected_side
                or type(quantity) is not int or quantity != 2):
            raise Hold("OPERATOR_ENTRY_PLAN_MISMATCH")
        snap = self.observe()
        if snap["position"] != 0 or snap["other_positions"] != 0 or any(
                row["active"] for row in snap["orders"]):
            raise Hold("OPERATOR_ENTRY_BROKER_NOT_FLAT")
        self._permit("ENTRY", key, expected_key=self.plan.entry_key)
        payload = {"symbol": symbol, "side": side, "quantity": {"value": "2"},
                   "type": MARKET_ORDER_TYPE, "time_in_force": TIME_IN_FORCE_DAY,
                   "client_order_id": compact_client_order_id(key)}
        return _ack(self.api.place_order(self.account_id, payload))

    def install_stop(self, *, key: str, symbol: str, side: str,
                     price: str, percent: int) -> str:
        expected = "SIDE_SELL" if self.plan.direction == "LONG" else "SIDE_BUY"
        requested_price = _positive_price(price)
        tick = Decimal(_N4_STEP[self.plan.instrument])
        snap = self.observe()
        signed = snap["position"] * (1 if self.plan.direction == "LONG" else -1)
        if (symbol != self.plan.symbol or side != expected
                or type(percent) is not int or percent != 100
                or requested_price != _positive_price(self.plan.stop_price)
                or requested_price % tick != 0 or signed not in (1, 2)
                or any(o["active"] and o["kind"] == "sltp" for o in snap["orders"])):
            raise Hold("OPERATOR_SLTP_PLAN_OR_POSITION_INVALID")
        self._permit("SLTP", key, expected_key=self.plan.stop_key)
        payload = {"symbol": symbol, "side": side,
                   "quantity_sl": {"value": "100"}, "sl_qty_measure": _STOP_MEASURE,
                   "sl_price": {"value": str(requested_price)},
                   "valid_before": _STOP_VALIDITY,
                   "client_order_id": compact_client_order_id(key), "comment": key}
        return _ack(self.api.place_sltp_order(self.account_id, payload))

    def cancel(self, order_id: str) -> str:
        """Only cancel a verified active acceptance order; never blind cancel."""
        snap = self.observe()
        matches = [o for o in snap["orders"] if o["id"] == order_id]
        if len(matches) != 1 or not matches[0]["active"]:
            raise Hold("OPERATOR_CANCEL_ORDER_NOT_ACTIVE")
        row = matches[0]
        if (row["symbol"] != self.plan.symbol or row["kind"] not in {"regular", "sltp"}
                or (row["kind"] == "sltp" and snap["position"] != 0)
                or (row["kind"] == "regular" and row["client_order_id"] !=
                    compact_client_order_id(self.plan.entry_key))):
            raise Hold("OPERATOR_CANCEL_NOT_SAFE")
        self._permit("CANCEL", order_id)
        reply = self.api.cancel_order(self.account_id, order_id)
        # Cancellation ACK alone is not a terminal-state reconciliation.
        if not isinstance(reply, dict):
            raise Hold("CANCEL_ACK_SCHEMA_INVALID")
        return "CANCEL_ACK_NOT_TERMINAL_PROOF"

    def exit(self, *, key: str, symbol: str, side: str, quantity: int) -> str:
        """Manual authorized exit only when order inventory proves no active
        entry or stop. An active SLTP is NOT automatically cancelled or raced
        against an opposing MARKET order: terminal intervention is required.
        """
        expected = "SIDE_SELL" if self.plan.direction == "LONG" else "SIDE_BUY"
        snap = self.observe()
        expected_position = quantity * (1 if self.plan.direction == "LONG" else -1)
        if (symbol != self.plan.symbol or side != expected
                or type(quantity) is not int or quantity not in (1, 2)
                or snap["position"] != expected_position
                or snap["other_positions"] != 0
                or any(o["active"] for o in snap["orders"])):
            raise Hold("OPERATOR_EXIT_REQUIRES_TERMINAL_ORDER_PROOF")
        self._permit("EXIT", key)
        payload = {"symbol": symbol, "side": side,
                   "quantity": {"value": str(quantity)},
                   "type": MARKET_ORDER_TYPE, "time_in_force": TIME_IN_FORCE_DAY,
                   "client_order_id": compact_client_order_id(key)}
        return _ack(self.api.place_order(self.account_id, payload))
