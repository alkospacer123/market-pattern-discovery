"""Stage 8.12.4 FINAM production transmission adapter.

This module is intentionally inert without a durable, exact Stage 8.12.4
authorization record.  Entry transmission additionally requires the live
new-entry gate to be OPEN.  Risk-reducing protection/emergency-exit operations
remain available after authorization even if the kill switch later HALTs new
entries.
"""
from __future__ import annotations

import hashlib
from pathlib import Path
from typing import Any

from .broker import broker_side, compact_client_order_id
from .finam_api import MARKET_ORDER_TYPE, TIME_IN_FORCE_DAY
from .production_authorization import load_authorization
from .production_broker_state import ProductionBrokerStateError, position_quantities
from .production_runtime import RuntimeAction
from .protective_stop_contract import (
    ProtectiveStopContractError,
    percent_position_stop_payload,
)
from .production_safety_gate import evaluate_production_entry_gate


class LiveExecutionError(RuntimeError):
    pass


class AuthorizedFinamProductionTransport:
    """Narrow order-capable adapter gated by exact durable authorization."""

    def __init__(
        self,
        *,
        api: Any,
        account_id: str,
        runtime_root: Path | str,
        accepted_commit: str,
    ):
        if not account_id:
            raise LiveExecutionError("STAGE8_12_4_ACCOUNT_REQUIRED")
        self.api = api
        self.account_id = str(account_id)
        self.runtime_root = Path(runtime_root)
        self.accepted_commit = str(accepted_commit).strip().lower()
        self.account_hash = hashlib.sha256(self.account_id.encode("utf-8")).hexdigest()
        self.connected = False
        self._require_authorization()

    def _require_authorization(self) -> dict[str, Any]:
        return load_authorization(
            self.runtime_root,
            expected_commit=self.accepted_commit,
            expected_account_hash=self.account_hash,
        )

    def connect(self) -> None:
        self._require_authorization()
        self.api.create_session()
        details = self.api.session_details()
        ids = details.get("account_ids") if isinstance(details, dict) else None
        if (
            not isinstance(ids, list)
            or [str(value) for value in ids].count(self.account_id) != 1
        ):
            raise LiveExecutionError("STAGE8_12_4_ACCOUNT_NOT_EXACTLY_ENUMERATED")
        if details.get("readonly") is not False:
            raise LiveExecutionError("STAGE8_12_4_TRADING_TOKEN_NOT_WRITE_CAPABLE")
        self.api.account(self.account_id)
        self.connected = True

    def _require_connected(self) -> None:
        if self.connected is not True:
            raise LiveExecutionError("STAGE8_12_4_TRANSPORT_NOT_CONNECTED")
        self._require_authorization()

    def _require_entry_gate(self, now) -> None:
        self._require_connected()
        gate = evaluate_production_entry_gate(
            runtime_root=self.runtime_root,
            now=now,
            expected_commit=self.accepted_commit,
            expected_account_hash=self.account_hash,
            execution_authorized=True,
        )
        if gate.get("entry_gate_open") is not True:
            reasons = ",".join(gate.get("reason_codes") or [])
            raise LiveExecutionError(f"STAGE8_12_4_ENTRY_GATE_BLOCKED:{reasons}")

    def _fresh_symbol_quantity(self, symbol: str) -> int:
        self._require_connected()
        try:
            positions = position_quantities(self.api.account(self.account_id))
        except ProductionBrokerStateError as exc:
            raise LiveExecutionError(str(exc)) from None
        return positions.get(symbol, 0)

    @staticmethod
    def _validate_action(action: RuntimeAction, kind: str) -> None:
        if (
            action.kind != kind
            or not action.idempotency_key
            or not action.finam_symbol
            or action.direction not in {"LONG", "SHORT"}
            or type(action.quantity) is not int
            or action.quantity <= 0
        ):
            raise LiveExecutionError("STAGE8_12_4_RUNTIME_ACTION_INVALID")

    @staticmethod
    def _market_payload(action: RuntimeAction, *, exit_order: bool) -> dict[str, Any]:
        client_id = compact_client_order_id(action.idempotency_key)
        return {
            "symbol": action.finam_symbol,
            "quantity": {"value": str(action.quantity)},
            "side": broker_side(action.direction, exit_order=exit_order),
            "type": MARKET_ORDER_TYPE,
            "time_in_force": TIME_IN_FORCE_DAY,
            "client_order_id": client_id,
        }

    def submit_entry(self, action: RuntimeAction, *, now) -> dict[str, Any]:
        self._validate_action(action, "ENTRY")
        self._require_entry_gate(now)
        if self._fresh_symbol_quantity(action.finam_symbol) != 0:
            raise LiveExecutionError("STAGE8_12_4_ENTRY_TARGET_NOT_FLAT")
        return self.api.place_order(
            self.account_id, self._market_payload(action, exit_order=False)
        )

    def submit_protective_stop(
        self,
        action: RuntimeAction,
        *,
        observed_position_quantity: int,
    ) -> dict[str, Any]:
        self._require_connected()
        if action.kind not in {"PROTECTIVE_STOP_INSTALL", "PROTECTIVE_STOP_REPLACE"}:
            raise LiveExecutionError("STAGE8_12_4_PROTECTIVE_STOP_ACTION_REQUIRED")
        expected = action.quantity if action.direction == "LONG" else -action.quantity
        if type(observed_position_quantity) is not int or observed_position_quantity != expected:
            raise LiveExecutionError("STAGE8_12_4_PROTECTIVE_STOP_POSITION_NOT_EXACT")
        if self._fresh_symbol_quantity(action.finam_symbol) != expected:
            raise LiveExecutionError("STAGE8_12_4_PROTECTIVE_STOP_FRESH_POSITION_NOT_EXACT")
        try:
            payload = percent_position_stop_payload(action)
        except ProtectiveStopContractError as exc:
            raise LiveExecutionError(str(exc)) from None
        payload.pop("schema_id", None)
        payload["client_order_id"] = compact_client_order_id(action.idempotency_key)
        if len(action.idempotency_key) > 128:
            raise LiveExecutionError("STAGE8_12_4_PROTECTIVE_STOP_COMMENT_TOO_LONG")
        payload["comment"] = action.idempotency_key
        return self.api.place_sltp_order(self.account_id, payload)

    def submit_emergency_exit(
        self,
        action: RuntimeAction,
        *,
        observed_position_quantity: int,
    ) -> dict[str, Any]:
        self._validate_action(action, "EMERGENCY_EXIT_REQUIRED")
        self._require_connected()
        expected = action.quantity if action.direction == "LONG" else -action.quantity
        if type(observed_position_quantity) is not int or observed_position_quantity != expected:
            raise LiveExecutionError("STAGE8_12_4_EMERGENCY_EXIT_POSITION_NOT_EXACT")
        if self._fresh_symbol_quantity(action.finam_symbol) != expected:
            raise LiveExecutionError("STAGE8_12_4_EMERGENCY_EXIT_FRESH_POSITION_NOT_EXACT")
        return self.api.place_order(
            self.account_id, self._market_payload(action, exit_order=True)
        )

    def cancel_protective_stop_after_flat(
        self,
        broker_order_id: str,
        *,
        observed_position_quantity: int,
        finam_symbol: str | None = None,
    ) -> dict[str, Any]:
        self._require_connected()
        if type(observed_position_quantity) is not int or observed_position_quantity != 0:
            raise LiveExecutionError("STAGE8_12_4_PROTECTIVE_STOP_CANCEL_REQUIRES_FLAT")
        if not isinstance(broker_order_id, str) or not broker_order_id:
            raise LiveExecutionError("STAGE8_12_4_BROKER_ORDER_ID_REQUIRED")
        if finam_symbol is not None:
            if not isinstance(finam_symbol, str) or not finam_symbol:
                raise LiveExecutionError("STAGE8_12_4_FINAM_SYMBOL_REQUIRED")
            if self._fresh_symbol_quantity(finam_symbol) != 0:
                raise LiveExecutionError("STAGE8_12_4_PROTECTIVE_STOP_CANCEL_FRESH_POSITION_NOT_FLAT")
        return self.api.cancel_order(self.account_id, broker_order_id)
