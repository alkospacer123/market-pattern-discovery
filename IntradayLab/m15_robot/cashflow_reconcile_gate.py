"""Step15 M15 cashflow-to-realized-equity lifetime gate (GET evidence only).

Rebuild a proposed R15 capital basis from complete, bounded FINAM RUB
transaction windows. All windows must be contiguous, unsaturated and
reconciled exactly to separately verified FINAM equity minus unrealized P/L.
No trading, token access, order transport, SQLite adoption or live authority.
"""
from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from decimal import Decimal

from .broker_risk_readonly import check_account, M15RiskAuthorityError
from .initial_capital import _money, _timestamp

# Official FINAM accounts_service.proto TransactionCategory values.
_DOCUMENTED = {
    0: "OTHERS", 1: "DEPOSIT", 2: "WITHDRAW", 5: "INCOME",
    7: "COMMISSION", 8: "TAX", 9: "INHERITANCE", 11: "TRANSFER",
    12: "CONTRACT_TERMINATION", 13: "OUTCOMES", 15: "FINE", 19: "LOAN",
}
_CATEGORIES = frozenset(_DOCUMENTED.values())


class M15CashflowGateError(RuntimeError):
    pass


@dataclass(frozen=True)
class CashflowWindow:
    start: datetime
    end: datetime
    response: dict
    limit: int = 1000


@dataclass(frozen=True)
class CashflowReconciliation:
    proposed_realized_equity: Decimal
    transaction_count: int
    transaction_fingerprint_sha256: str
    source: str = "BOUNDED_FINAM_GET_OFFLINE_VERIFICATION"
    runtime_r15_authorized: bool = False
    live_authorized: bool = False


def _utc(value: datetime) -> datetime:
    if not isinstance(value, datetime) or value.tzinfo is None or value.utcoffset() is None:
        raise M15CashflowGateError("M15_CASHFLOW_WINDOW_TIMEZONE_INVALID")
    return value.astimezone(timezone.utc)


def _category(value) -> str:
    if type(value) is int and value in _DOCUMENTED:
        return _DOCUMENTED[value]
    if isinstance(value, str) and value in _CATEGORIES:
        return value
    raise M15CashflowGateError("M15_CASHFLOW_CATEGORY_NOT_DOCUMENTED")


def propose_realized_capital(
    *, account: dict, expected_account_id: str, windows: list[CashflowWindow],
    now: datetime,
) -> CashflowReconciliation:
    """No input window may be assumed complete without bounded FINAM evidence.

    A sum that agrees with broker equity is a consistency check, not proof of
    brokerage commission classification, authenticated timing, or safe LIVE
    resumption. Production adoption remains separately prohibited.
    """
    if not isinstance(expected_account_id, str) or not expected_account_id:
        raise M15CashflowGateError("M15_CASHFLOW_ACCOUNT_IDENTITY_REQUIRED")
    broker = check_account(account, expected_account_id)
    current = _utc(now)
    birth = _timestamp(account.get("open_account_date"))
    if birth > current or not isinstance(windows, list) or not windows:
        raise M15CashflowGateError("M15_CASHFLOW_LIFETIME_INCOMPLETE")
    expected_start = birth - timedelta(seconds=1)
    expected_end = current + timedelta(minutes=1)
    observed_ids: set[str] = set()
    facts: list[tuple[str, str, str, str]] = []
    total = Decimal("0")
    for item in windows:
        if not isinstance(item, CashflowWindow):
            raise M15CashflowGateError("M15_CASHFLOW_WINDOW_SCHEMA_INVALID")
        start, end = _utc(item.start), _utc(item.end)
        if (start != expected_start or start >= end or end > expected_end
                or type(item.limit) is not int or not 0 < item.limit <= 1000):
            raise M15CashflowGateError("M15_CASHFLOW_GAP_OVERLAP_OR_LIMIT")
        response = item.response
        if not isinstance(response, dict) or not isinstance(response.get("transactions"), list):
            raise M15CashflowGateError("M15_CASHFLOW_TRANSACTIONS_SCHEMA_INVALID")
        rows = response["transactions"]
        if len(rows) >= item.limit or any(
            response.get(key) not in (None, "", 0)
            for key in ("next_cursor", "next_page_token")
        ):
            raise M15CashflowGateError("M15_CASHFLOW_HISTORY_NOT_COMPLETE")
        for row in rows:
            if not isinstance(row, dict):
                raise M15CashflowGateError("M15_CASHFLOW_TRANSACTION_SCHEMA_INVALID")
            identity = row.get("id")
            if (not isinstance(identity, str) or not identity
                    or len(identity) > 256 or identity in observed_ids):
                raise M15CashflowGateError("M15_CASHFLOW_TRANSACTION_ID_INVALID")
            timestamp = _timestamp(row.get("timestamp"))
            if not start <= timestamp < end:
                raise M15CashflowGateError("M15_CASHFLOW_TRANSACTION_OUTSIDE_WINDOW")
            category = _category(row.get("transaction_category"))
            delta = _money(row.get("change"))
            observed_ids.add(identity)
            total += delta
            facts.append((
                hashlib.sha256(identity.encode()).hexdigest(),
                timestamp.isoformat(), category, format(delta, "f"),
            ))
        expected_start = end
    if expected_start != expected_end:
        raise M15CashflowGateError("M15_CASHFLOW_FINAL_WINDOW_MISSING")
    if total <= 0 or total != broker.broker_equity_minus_unrealized:
        raise M15CashflowGateError("M15_CASHFLOW_REALIZED_EQUITY_MISMATCH")
    fingerprint = hashlib.sha256(
        json.dumps(sorted(facts), separators=(",", ":")).encode()
    ).hexdigest()
    return CashflowReconciliation(total, len(observed_ids), fingerprint)
