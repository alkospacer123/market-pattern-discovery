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
from .finam_api import (
    MARKET_ORDER_TYPE,
    TIME_IN_FORCE_DAY,
    FinamOrderRejected,
    FinamUncertainSubmission,
)
from .production_authorization import load_authorization
from .production_runtime import RuntimeAction
from .protective_stop_contract import (
    ProtectiveStopContractError,
    percent_position_stop_payload,
)
from .production_safety_gate import evaluate_production_entry_gate
from .state import StateStore


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
    def _require_persisted_action(
        action: RuntimeAction, state_store: StateStore
    ) -> dict[str, Any]:
        if not action.idempotency_key:
            raise LiveExecutionError("STAGE8_12_4_IDEMPOTENCY_KEY_REQUIRED")
        intent = state_store.intent(action.idempotency_key)
        if intent is None or intent.get("status") != "INTENT_PERSISTED":
            raise LiveExecutionError("STAGE8_12_4_PERSISTED_INTENT_REQUIRED")
        payload = intent.get("payload")
        if not isinstance(payload, dict):
            raise LiveExecutionError("STAGE8_12_4_PERSISTED_INTENT_INVALID")
        expected = action.payload()
        for key in (
            "kind", "idempotency_key", "instrument", "finam_symbol",
            "direction", "quantity", "trade_id", "signal_id",
            "reference_price", "stop_price", "expected_position_quantity",
        ):
            if payload.get(key) != expected.get(key):
                raise LiveExecutionError("STAGE8_12_4_PERSISTED_INTENT_MISMATCH")
        return intent

    @staticmethod
    def _ack_order_id(result: Any) -> str:
        if not isinstance(result, dict):
            raise LiveExecutionError("STAGE8_12_4_BROKER_ACK_INVALID")
        value = result.get("order_id") or result.get("orderId")
        if not isinstance(value, str) or not value:
            raise LiveExecutionError("STAGE8_12_4_BROKER_ACK_ORDER_ID_MISSING")
        return value

    def _submit_persisted(
        self,
        action: RuntimeAction,
        state_store: StateStore,
        submitter,
    ) -> dict[str, Any]:
        self._require_persisted_action(action, state_store)
        key = action.idempotency_key
        state_store.transition_intent(key, "SUBMITTED")
        try:
            result = submitter()
        except FinamUncertainSubmission:
            state_store.transition_intent(key, "UNCERTAIN")
            raise
        except FinamOrderRejected:
            state_store.transition_intent(key, "REJECTED")
            raise
        try:
            broker_id = self._ack_order_id(result)
        except LiveExecutionError:
            state_store.transition_intent(key, "UNCERTAIN")
            raise FinamUncertainSubmission(
                "RECONCILIATION_REQUIRED:BROKER_ACK_ORDER_ID_MISSING"
            ) from None
        state_store.transition_intent(key, "ACK", broker_id)
        return result

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

    def submit_entry(
        self, action: RuntimeAction, *, now, state_store: StateStore
    ) -> dict[str, Any]:
        self._validate_action(action, "ENTRY")
        self._require_entry_gate(now)
        return self._submit_persisted(
            action,
            state_store,
            lambda: self.api.place_order(
                self.account_id, self._market_payload(action, exit_order=False)
            ),
        )

    def submit_protective_stop(
        self,
        action: RuntimeAction,
        *,
        observed_position_quantity: int,
        state_store: StateStore,
    ) -> dict[str, Any]:
        self._require_connected()
        if action.kind not in {"PROTECTIVE_STOP_INSTALL", "PROTECTIVE_STOP_REPLACE"}:
            raise LiveExecutionError("STAGE8_12_4_PROTECTIVE_STOP_ACTION_REQUIRED")
        expected = action.quantity if action.direction == "LONG" else -action.quantity
        if type(observed_position_quantity) is not int or observed_position_quantity != expected:
            raise LiveExecutionError("STAGE8_12_4_PROTECTIVE_STOP_POSITION_NOT_EXACT")
        try:
            payload = percent_position_stop_payload(action)
        except ProtectiveStopContractError as exc:
            raise LiveExecutionError(str(exc)) from None
        payload.pop("schema_id", None)
        payload["client_order_id"] = compact_client_order_id(action.idempotency_key)
        if len(action.idempotency_key) > 128:
            raise LiveExecutionError("STAGE8_12_4_PROTECTIVE_STOP_COMMENT_TOO_LONG")
        payload["comment"] = action.idempotency_key
        return self._submit_persisted(
            action,
            state_store,
            lambda: self.api.place_sltp_order(self.account_id, payload),
        )

    def submit_emergency_exit(
        self,
        action: RuntimeAction,
        *,
        observed_position_quantity: int,
        state_store: StateStore,
    ) -> dict[str, Any]:
        self._validate_action(action, "EMERGENCY_EXIT_REQUIRED")
        self._require_connected()
        expected = action.quantity if action.direction == "LONG" else -action.quantity
        if type(observed_position_quantity) is not int or observed_position_quantity != expected:
            raise LiveExecutionError("STAGE8_12_4_EMERGENCY_EXIT_POSITION_NOT_EXACT")
        return self._submit_persisted(
            action,
            state_store,
            lambda: self.api.place_order(
                self.account_id, self._market_payload(action, exit_order=True)
            ),
        )

    def cancel_protective_stop_after_flat(
        self,
        broker_order_id: str,
        *,
        observed_position_quantity: int,
    ) -> dict[str, Any]:
        self._require_connected()
        if type(observed_position_quantity) is not int or observed_position_quantity != 0:
            raise LiveExecutionError("STAGE8_12_4_PROTECTIVE_STOP_CANCEL_REQUIRES_FLAT")
        if not isinstance(broker_order_id, str) or not broker_order_id:
            raise LiveExecutionError("STAGE8_12_4_BROKER_ORDER_ID_REQUIRED")
        return self.api.cancel_order(self.account_id, broker_order_id)
