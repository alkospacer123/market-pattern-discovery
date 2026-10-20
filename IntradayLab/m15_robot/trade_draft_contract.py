"""M15-only broker request DRAFT contract; no HTTP/order-capable transport.

Mirrors audited H1 market/100%-position-SLTP request *shapes*, not its live
permission. All drafts are offline-only. A future transport must obtain an
independent commit/account-bound M15 authorization, durable pre-POST intent,
real fill evidence and broker SLTP ACK before ANY actual submission.

Never import H1 modules, read tokens, call FINAM or touch active Windows Tasks.
"""
from __future__ import annotations

import hashlib
import re
from dataclasses import dataclass
from decimal import Decimal
from pathlib import Path
from typing import Any

from .account_boundary import validate_independent_binding
from .grid_risk import SizedOrder, require_on_grid
from .spec import EXECUTION_STATUS, INSTRUMENTS, ROBOT_ID


class M15DraftError(ValueError):
    pass


_KEY = re.compile(r"^m15:[A-Za-z0-9._:-]{1,123}$")
_KINDS = frozenset({"ENTRY", "PROTECTIVE_STOP_INSTALL", "PROTECTIVE_STOP_REPLACE", "EMERGENCY_EXIT"})


def _key(value: str) -> str:
    if not isinstance(value, str) or not _KEY.fullmatch(value):
        raise M15DraftError("M15_DRAFT_IDEMPOTENCY_KEY_INVALID")
    return value


def _client_id(key: str) -> str:
    return "m15" + hashlib.sha256(_key(key).encode("utf-8")).hexdigest()[:17]


def _symbol(instrument: str) -> str:
    if instrument not in INSTRUMENTS:
        raise M15DraftError("M15_DRAFT_INSTRUMENT_OUTSIDE_N4")
    return instrument + "@RTSX"


def _signed_position(direction: str, quantity: int, observed: int) -> None:
    if direction not in {"LONG", "SHORT"}:
        raise M15DraftError("M15_DRAFT_DIRECTION_INVALID")
    if type(quantity) is not int or quantity <= 0:
        raise M15DraftError("M15_DRAFT_QUANTITY_INVALID")
    expected = quantity if direction == "LONG" else -quantity
    if type(observed) is not int or observed != expected:
        raise M15DraftError("M15_DRAFT_BROKER_POSITION_NOT_EXACT")


def _price_on_grid(price: Decimal, price_step: Decimal) -> Decimal:
    try:
        return require_on_grid(price, price_step)
    except (ValueError, TypeError, ArithmeticError):
        raise M15DraftError("M15_DRAFT_PRICE_NOT_ON_GRID") from None


@dataclass(frozen=True)
class M15Draft:
    """Untrusted proposed payload, NOT proof of a submitted or accepted order."""
    kind: str
    account_fingerprint: str
    endpoint: str
    payload: dict[str, Any]
    live_authorized: bool = False
    submitted: bool = False


class M15OfflineTradeDrafts:
    """Only pure request formatting and M15 boundary checks; NEVER sends orders."""

    def __init__(
        self, *, m15_account_id: str, h1_account_sha256: str,
        m15_runtime_root: Path, h1_runtime_root: Path, repository_root: Path,
    ):
        self._fingerprint = validate_independent_binding(
            m15_account_id=m15_account_id, h1_account_sha256=h1_account_sha256,
            m15_runtime_root=m15_runtime_root, h1_runtime_root=h1_runtime_root,
            repository_root=repository_root,
        )
        # Drafts are inert regardless of the independently authorized wire status.
        # The original NO-LIVE-only check would deadlock LIVE SLTP/ENTRY creation.
        if EXECUTION_STATUS not in {"NOT_LIVE_AUTHORIZED", "LIVE_AUTHORIZED"}:
            raise M15DraftError("M15_DRAFT_EXECUTION_STATUS_INVALID")
        self._identity = ROBOT_ID

    @property
    def execution_authorized(self) -> bool:
        return False

    @property
    def identity(self) -> str:
        return self._identity

    def _draft(self, kind: str, payload: dict[str, Any], endpoint: str) -> M15Draft:
        if kind not in _KINDS:
            raise M15DraftError("M15_DRAFT_KIND_INVALID")
        return M15Draft(kind, self._fingerprint, endpoint, payload)

    def entry(
        self, *, instrument: str, direction: str, idempotency_key: str,
        sized: SizedOrder, observed_occupied: bool,
    ) -> M15Draft:
        """ENTRY draft requires an earlier R15+GO sizing result; NOT a live gate."""
        symbol = _symbol(instrument)
        _key(idempotency_key)
        if direction not in {"LONG", "SHORT"}:
            raise M15DraftError("M15_DRAFT_DIRECTION_INVALID")
        if type(observed_occupied) is not bool or observed_occupied:
            raise M15DraftError("M15_DRAFT_INSTRUMENT_NOT_FLAT")
        if (not isinstance(sized, SizedOrder) or sized.reason != "OK"
                or type(sized.final_quantity) is not int or sized.final_quantity <= 0
                or sized.initial_nominal_risk <= 0 or sized.risk_budget <= 0
                or sized.initial_nominal_risk > sized.risk_budget):
            raise M15DraftError("M15_DRAFT_R15_GO_AUTHORITY_MISSING")
        payload = {
            "symbol": symbol,
            "quantity": {"value": str(sized.final_quantity)},
            "side": "SIDE_BUY" if direction == "LONG" else "SIDE_SELL",
            "type": "ORDER_TYPE_MARKET",
            "time_in_force": "TIME_IN_FORCE_DAY",
            "client_order_id": _client_id(idempotency_key),
        }
        return self._draft("ENTRY", payload, "REGULAR_ORDER_DRAFT")

    def protective_stop(
        self, *, instrument: str, direction: str, idempotency_key: str,
        observed_position_quantity: int, stop_price: Decimal, price_step: Decimal,
        kind: str = "PROTECTIVE_STOP_INSTALL",
        previous_active_stop: Decimal | None = None,
    ) -> M15Draft:
        """100% of broker-observed position, never a simulated fill count.

        An existing stop stays active until independent broker ACK; this draft
        has deliberately no cancel method or acknowledge/activation mechanism.
        """
        symbol = _symbol(instrument)
        _key(idempotency_key)
        if type(observed_position_quantity) is not int or observed_position_quantity == 0:
            raise M15DraftError("M15_DRAFT_BROKER_POSITION_REQUIRED")
        _signed_position(direction, abs(observed_position_quantity), observed_position_quantity)
        stop = _price_on_grid(stop_price, price_step)
        if kind not in {"PROTECTIVE_STOP_INSTALL", "PROTECTIVE_STOP_REPLACE"}:
            raise M15DraftError("M15_DRAFT_STOP_KIND_INVALID")
        if kind == "PROTECTIVE_STOP_REPLACE":
            if previous_active_stop is None:
                raise M15DraftError("M15_DRAFT_REPLACEMENT_REQUIRES_BACKSTOP")
            previous = _price_on_grid(previous_active_stop, price_step)
            if (direction == "LONG" and stop < previous
                    or direction == "SHORT" and stop > previous):
                raise M15DraftError("M15_DRAFT_STOP_WIDENING")
        elif previous_active_stop is not None:
            raise M15DraftError("M15_DRAFT_INITIAL_STOP_ALREADY_EXISTS")
        payload = {
            "symbol": symbol,
            "side": "SIDE_SELL" if direction == "LONG" else "SIDE_BUY",
            "quantity_sl": {"value": "100"},
            "sl_qty_measure": "SLTP_QTY_MEASURE_PERCENT",
            "sl_price": {"value": str(stop)},
            "valid_before": "VALID_BEFORE_GOOD_TILL_CANCEL",
            "client_order_id": _client_id(idempotency_key),
            "comment": idempotency_key,
        }
        return self._draft(kind, payload, "SLTP_ORDER_DRAFT")

    def emergency_exit(
        self, *, instrument: str, direction: str, idempotency_key: str,
        observed_position_quantity: int,
    ) -> M15Draft:
        symbol = _symbol(instrument)
        _key(idempotency_key)
        if type(observed_position_quantity) is not int or observed_position_quantity == 0:
            raise M15DraftError("M15_DRAFT_BROKER_POSITION_REQUIRED")
        _signed_position(direction, abs(observed_position_quantity), observed_position_quantity)
        return self._draft("EMERGENCY_EXIT", {
            "symbol": symbol, "quantity": {"value": str(abs(observed_position_quantity))},
            "side": "SIDE_SELL" if direction == "LONG" else "SIDE_BUY",
            "type": "ORDER_TYPE_MARKET", "time_in_force": "TIME_IN_FORCE_DAY",
            "client_order_id": _client_id(idempotency_key),
        }, "REGULAR_ORDER_DRAFT")

    def submit(self, *args: object, **kwargs: object) -> None:
        """Hard stage gate: there is no real order transport."""
        raise M15DraftError("M15_REAL_ORDER_SUBMISSION_NOT_AUTHORIZED")

    def cancel(self, *args: object, **kwargs: object) -> None:
        raise M15DraftError("M15_REAL_ORDER_CANCELLATION_NOT_AUTHORIZED")
