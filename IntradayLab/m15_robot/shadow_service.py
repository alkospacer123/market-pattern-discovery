"""FINAM GET-only shadow cycle using ported H1 parsing and isolated SQLite.

No token loading, POST/DELETE, runtime order intent, Windows Task or re-arm.
The service only consumes a caller-provided API with account() and orders().
The account MUST be separate from H1. Any foreign exposure or order fails
closed. A healthy shadow snapshot never authorizes an entry.
"""
from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from .broker_snapshot import (
    ProductionBrokerStateError, order_views, position_quantities,
)
from .shadow_state import ShadowLedger

ACCOUNT_ACTIVE = frozenset({"ACCOUNT_ACTIVE", "ACCOUNT_STATUS_ACTIVE"})


class ShadowObservationError(RuntimeError):
    pass


def observe_broker_once(
    *, ledger: ShadowLedger, read_api: Any, m15_account_id: str,
    observed_at: datetime,
) -> dict:
    """H1-style snapshot and strict reconciliation, but permanently HALTED.

    Input adapter never accepts or exposes an execution transport. No positions
    or orders may be adopted into a newly initialized M15 shadow ledger.
    """
    if observed_at.tzinfo is None or observed_at.utcoffset() is None:
        raise ShadowObservationError("M15_OBSERVATION_TIME_INVALID")
    import hashlib
    if hashlib.sha256(m15_account_id.encode("utf-8")).hexdigest() != ledger.identity["account_hash"]:
        raise ShadowObservationError("M15_OBSERVATION_ACCOUNT_MISMATCH")
    if not callable(getattr(read_api, "account", None)) or not callable(getattr(read_api, "orders", None)):
        raise ShadowObservationError("M15_READONLY_API_REQUIRED")

    position_count = 0
    active_order_count = 0
    reason = "BROKER_FLAT_AND_CLEAN"
    try:
        # Call ONLY GET-side methods; no order/withdrawal APIs exist here.
        account = read_api.account(m15_account_id)
        if (
            not isinstance(account, dict)
            or account.get("account_id") != m15_account_id
            or account.get("status") not in ACCOUNT_ACTIVE
        ):
            raise ShadowObservationError("M15_ACCOUNT_OR_STATUS_INVALID")
        positions = position_quantities(account)
        orders = order_views(read_api.orders(m15_account_id))
        position_count = len(positions)
        active_order_count = sum(order.active for order in orders)
        if positions or active_order_count:
            raise ShadowObservationError("M15_FOREIGN_EXPOSURE_OR_ACTIVE_ORDER")
    except Exception as exc:
        # Never serialize raw broker exception bodies, account IDs or secrets.
        reason = (
            str(exc) if isinstance(exc, (ShadowObservationError, ProductionBrokerStateError))
            else "BROKER_READ_OR_SCHEMA_FAULT"
        )
        ledger.append(
            observed_at=observed_at, status="FAULT_HALTED",
            reason=reason[:128],
            facts={"position_count": position_count, "active_order_count": active_order_count},
        )
        raise ShadowObservationError(reason) from None

    receipt = ledger.append(
        observed_at=observed_at, status="HEALTHY_READONLY", reason=reason,
        facts={"position_count": position_count, "active_order_count": active_order_count},
    )
    return receipt | {"execution_authorized": False, "entries_enabled": False}
