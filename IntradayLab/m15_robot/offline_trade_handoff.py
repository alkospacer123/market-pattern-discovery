"""Offline-only M15 draft -> durable rehearsal intent -> FINAM GET evidence bridge.

The two existing SQLite stores are deliberately different:
  * OfflineIntentLedger is SYNTHETIC_ONLY and never adopts an actual fill.
  * M15ReadOnlyBrokerReceiptStore records sanitized GET evidence fingerprints.
This module proves matching draft/intent/broker identities before observing.
It has no broker API or trading endpoint and NEVER promotes evidence to LIVE.
"""
from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal
import hashlib

from .broker_fill_readonly import ExpectedEntry
from .broker_receipt_store import M15ReadOnlyBrokerReceiptStore
from .grid_risk import SizedOrder
from .offline_intents import OfflineIntentLedger
from .trade_draft_contract import M15Draft, M15OfflineTradeDrafts


class M15OfflineHandoffError(RuntimeError):
    pass


@dataclass(frozen=True)
class PreparedOfflineEntry:
    key: str
    instrument: str
    direction: str
    quantity: int
    draft: M15Draft
    new_intent: bool
    live_authorized: bool = False
    post_authorized: bool = False


def _fingerprint(account: str) -> str:
    return hashlib.sha256(account.encode("utf-8")).hexdigest()


def prepare_offline_entry(
    *, drafts: M15OfflineTradeDrafts, ledger: OfflineIntentLedger,
    instrument: str, direction: str, idempotency_key: str,
    sized: SizedOrder, observed_occupied: bool,
) -> PreparedOfflineEntry:
    """Prepare a nontransmitting request, then persist SYNTHETIC intent.

    Repeating the same key is non-submitting, even after an UNCERTAIN state.
    The caller MUST NOT use this synthetic ledger for a real order POST.
    """
    if (not isinstance(drafts, M15OfflineTradeDrafts)
            or not isinstance(ledger, OfflineIntentLedger)
            or drafts.execution_authorized is not False
            or ledger.execution_authorized is not False):
        raise M15OfflineHandoffError("M15_HANDOFF_OFFLINE_ONLY")
    draft = drafts.entry(
        instrument=instrument, direction=direction,
        idempotency_key=idempotency_key, sized=sized,
        observed_occupied=observed_occupied,
    )
    if (draft.kind != "ENTRY" or draft.submitted or draft.live_authorized
            or draft.account_fingerprint != ledger.identity.get("account_sha256")
            or ledger.identity.get("broker") != "SYNTHETIC_ONLY"):
        raise M15OfflineHandoffError("M15_HANDOFF_ACCOUNT_OR_AUTHORITY_MISMATCH")
    created = ledger.prepare(
        key=idempotency_key, instrument=instrument, direction=direction,
        quantity=sized.final_quantity,
    )
    return PreparedOfflineEntry(
        key=idempotency_key, instrument=instrument, direction=direction,
        quantity=sized.final_quantity, draft=draft, new_intent=created,
    )


def inspect_broker_evidence_offline(
    *, prepared: PreparedOfflineEntry, ledger: OfflineIntentLedger,
    receipts: M15ReadOnlyBrokerReceiptStore, expected: ExpectedEntry,
    account: dict, orders_response: dict, trades_response: dict,
    observed_at: datetime, stop_trade_tag: str, start: str, end: str,
    limit: int = 1000,
) -> dict:
    """Append sanitized READONLY broker proof; NEVER acknowledge synthetic intent.

    All inputs are externally supplied snapshots. Caller must independently
    authenticate the M15 FINAM READONLY session; this module has no network.
    Actual broker fills are never entered into the SYNTHETIC ledger.
    """
    if (not isinstance(prepared, PreparedOfflineEntry)
            or not isinstance(ledger, OfflineIntentLedger)
            or not isinstance(receipts, M15ReadOnlyBrokerReceiptStore)
            or not isinstance(expected, ExpectedEntry)
            or prepared.live_authorized or prepared.post_authorized
            or prepared.draft.submitted or prepared.draft.live_authorized
            or ledger.execution_authorized or receipts.execution_authorized):
        raise M15OfflineHandoffError("M15_HANDOFF_BROKER_PROOF_OFFLINE_ONLY")
    intent = ledger.intent(prepared.key)
    if (intent is None or intent["status"] not in {"PREPARED", "UNCERTAIN"}
            or intent["instrument"] != prepared.instrument
            or intent["direction"] != prepared.direction
            or intent["planned_quantity"] != prepared.quantity):
        raise M15OfflineHandoffError("M15_HANDOFF_DURABLE_INTENT_MISMATCH")
    fingerprint = prepared.draft.account_fingerprint
    if (not isinstance(expected.account_id, str)
            or _fingerprint(expected.account_id) != fingerprint
            or ledger.identity.get("account_sha256") != fingerprint
            or receipts.identity.get("account_sha256") != fingerprint
            or expected.symbol != prepared.draft.payload.get("symbol")
            or expected.side != prepared.draft.payload.get("side")
            or expected.quantity != prepared.quantity
            or prepared.draft.payload.get("quantity") != {"value": str(prepared.quantity)}
            or prepared.draft.payload.get("client_order_id") is None):
        raise M15OfflineHandoffError("M15_HANDOFF_BROKER_DRAFT_IDENTITY_MISMATCH")
    return {
        **receipts.observe(
            observed_at=observed_at, expected=expected,
            expected_client_order_id=prepared.draft.payload["client_order_id"],
            stop_trade_tag=stop_trade_tag,
            account=account, orders_response=orders_response,
            trades_response=trades_response, start=start, end=end, limit=limit,
        ),
        "synthetic_intent_unchanged": ledger.intent(prepared.key) == intent,
        "live_authorized": False,
        "sqlite_fill_adoption_authorized": False,
        "order_submission_authorized": False,
    }
