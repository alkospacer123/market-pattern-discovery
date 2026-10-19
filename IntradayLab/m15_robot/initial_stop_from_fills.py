"""M15 initial SLTP DRAFT from independently cross-checked FINAM GET fills.

Pure data transform: broker snapshots are caller-supplied, no FINAM client,
no credential, no submit/cancel, no trading SQLite and no H1 state.

Preserves exact weighted-average fill Fraction (often OFF the price grid even
when every individual execution is ON grid). Calculate raw +/-2*ATR from that
exact average and project ONLY the resulting protective stop outwards onto
the executable N4 tick grid. An actual SLTP ACK remains a separate gate.
"""
from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal, InvalidOperation
from fractions import Fraction
import hashlib

from .broker_fill_readonly import ExpectedEntry, analyze_account_trades
from .broker_reconcile_gate import assess_entry_evidence
from .grid_risk import project_stop
from .offline_trade_handoff import PreparedOfflineEntry
from .spec import INITIAL_STOP_ATR
from .trade_draft_contract import M15Draft, M15OfflineTradeDrafts


class M15InitialStopDraftError(RuntimeError):
    pass


@dataclass(frozen=True)
class M15InitialStopProposal:
    draft: M15Draft
    matched_quantity: int
    weighted_entry_exact: Fraction
    stop_price: Decimal
    fill_set_sha256: str
    source: str = "BOUNDED_FINAM_GET_EVIDENCE_OFFLINE"
    broker_stop_acknowledged: bool = False
    broker_position_protected: bool = False
    order_submission_authorized: bool = False
    live_authorized: bool = False


def initial_stop_draft_from_broker_get(
    *, drafts: M15OfflineTradeDrafts, prepared: PreparedOfflineEntry,
    expected: ExpectedEntry, stop_idempotency_key: str,
    atr_at_entry_signal: Decimal,
    account: dict, orders_response: dict, trades_response: dict,
    stop_trade_tag: str, start: str, end: str, limit: int = 1000,
) -> M15InitialStopProposal:
    """Fail closed unless a real-order-shaped, bounded GET receipt matches N4.

    Never install SLTP here: an unprotected fill remains unprotected until
    separately authenticated FINAM actually acknowledges the stop.
    """
    if (not isinstance(drafts, M15OfflineTradeDrafts)
            or not isinstance(prepared, PreparedOfflineEntry)
            or not isinstance(expected, ExpectedEntry)
            or drafts.execution_authorized or prepared.live_authorized
            or prepared.post_authorized or prepared.draft.submitted
            or prepared.draft.live_authorized or prepared.draft.kind != "ENTRY"
            or stop_idempotency_key == prepared.key):
        raise M15InitialStopDraftError("M15_INITIAL_SLTP_OFFLINE_IDENTITY_INVALID")
    if (not isinstance(atr_at_entry_signal, Decimal)
            or not atr_at_entry_signal.is_finite()
            or atr_at_entry_signal <= 0):
        raise M15InitialStopDraftError("M15_INITIAL_SLTP_SIGNAL_ATR_INVALID")
    try:
        account_sha = hashlib.sha256(expected.account_id.encode("utf-8")).hexdigest()
    except (AttributeError, UnicodeError):
        raise M15InitialStopDraftError("M15_INITIAL_SLTP_ACCOUNT_INVALID") from None
    if (account_sha != prepared.draft.account_fingerprint
            or prepared.instrument + "@RTSX" != expected.symbol
            or prepared.draft.payload.get("symbol") != expected.symbol
            or expected.side != prepared.draft.payload.get("side")
            or prepared.quantity != expected.quantity
            or prepared.draft.payload.get("quantity") != {"value": str(expected.quantity)}):
        raise M15InitialStopDraftError("M15_INITIAL_SLTP_DRAFT_BROKER_IDENTITY_MISMATCH")
    client_id = prepared.draft.payload.get("client_order_id")
    if not isinstance(client_id, str) or not client_id:
        raise M15InitialStopDraftError("M15_INITIAL_SLTP_CLIENT_ID_REQUIRED")
    # Both calls are pure. The cross-source check proves matching order, position,
    # bounded trades, zero unknown competing orders and valid STOP objects.
    evidence = assess_entry_evidence(
        account=account, orders_response=orders_response,
        trades_response=trades_response, expected=expected,
        expected_client_order_id=client_id, stop_trade_tag=stop_trade_tag,
        start=start, end=end, limit=limit,
    )
    if (evidence.matched_fill_quantity <= 0
            or evidence.matched_fill_quantity != abs(evidence.broker_position_quantity)
            or evidence.protection_status != "UNPROTECTED_BROKER_FILL"
            or evidence.active_sltp_count != 0
            or evidence.live_authorized or evidence.sqlite_adoption_authorized):
        raise M15InitialStopDraftError("M15_INITIAL_SLTP_FILL_OR_STOP_UNPROVEN")
    fills = analyze_account_trades(
        trades_response, expected, start=start, end=end, limit=limit,
    )
    if (fills["matched_quantity"] != evidence.matched_fill_quantity
            or fills["fill_set_sha256"] != evidence.fill_set_sha256
            or not fills["verified_fill"] or fills["weighted_price_exact"] is None
            or fills["live_authorized"] or fills["sqlite_reconciled"]):
        raise M15InitialStopDraftError("M15_INITIAL_SLTP_HISTORY_CONFLICT")
    exact = fills["weighted_price_exact"]
    try:
        avg = Fraction(int(exact["numerator"]), int(exact["denominator"]))
    except (TypeError, ValueError, KeyError, ZeroDivisionError):
        raise M15InitialStopDraftError("M15_INITIAL_SLTP_AVERAGE_INVALID") from None
    if avg <= 0:
        raise M15InitialStopDraftError("M15_INITIAL_SLTP_AVERAGE_INVALID")
    direction = "LONG" if expected.side == "SIDE_BUY" else "SHORT"
    atr = Fraction(atr_at_entry_signal)
    raw = avg - Fraction(INITIAL_STOP_ATR) * atr if direction == "LONG" else avg + Fraction(INITIAL_STOP_ATR) * atr
    if raw <= 0 or (direction == "LONG" and raw >= avg) or (direction == "SHORT" and raw <= avg):
        raise M15InitialStopDraftError("M15_INITIAL_SLTP_WRONG_SIDE")
    try:
        stop = project_stop(direction, raw, expected.price_step)
    except (ValueError, TypeError, InvalidOperation, ZeroDivisionError):
        raise M15InitialStopDraftError("M15_INITIAL_SLTP_GRID_INVALID") from None
    # A broker-verified partial fill must be protected at its CURRENT
    # quantity, not at the original planned quantity or a simulated fill.
    signed = evidence.broker_position_quantity
    draft = drafts.protective_stop(
        instrument=prepared.instrument, direction=direction,
        idempotency_key=stop_idempotency_key,
        observed_position_quantity=signed,
        stop_price=stop, price_step=expected.price_step,
    )
    if draft.submitted or draft.live_authorized or draft.payload["quantity_sl"] != {"value": "100"}:
        raise M15InitialStopDraftError("M15_INITIAL_SLTP_UNEXPECTED_AUTHORITY")
    return M15InitialStopProposal(draft, evidence.matched_fill_quantity, avg,
                                  stop, evidence.fill_set_sha256)
