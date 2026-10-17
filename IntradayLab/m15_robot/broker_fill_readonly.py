"""Read-only FINAM AccountTrade evidence: no SQLite writes, orders or live handoff.

Adapt only the bounded history-validation invariants from H1
finam_fill_price_readonly.analyze_history. No FINAM API, token, H1 import,
commission assumptions, synthetic fill adoption or mutable trading authority.
"""
from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from decimal import Decimal, InvalidOperation
from fractions import Fraction
import hashlib
import json
import re
from typing import Any

_TIMESTAMP = re.compile(
    r"^(?P<date>\d{4}-\d{2}-\d{2})T(?P<time>\d{2}:\d{2}:\d{2})"
    r"(?:\.(?P<fraction>\d{1,9}))?(?P<zone>Z|[+-]\d{2}:\d{2})$"
)
_EPOCH = datetime(1970, 1, 1, tzinfo=timezone.utc)


class M15FillEvidenceError(RuntimeError):
    pass


def _time(value: str) -> tuple[int, int]:
    match = _TIMESTAMP.fullmatch(value) if isinstance(value, str) else None
    if match is None:
        raise M15FillEvidenceError("M15_TRADE_TIMESTAMP_INVALID")
    zone = "+00:00" if match["zone"] == "Z" else match["zone"]
    try:
        dt = datetime.fromisoformat(match["date"] + "T" + match["time"] + zone).astimezone(timezone.utc)
    except ValueError:
        raise M15FillEvidenceError("M15_TRADE_TIMESTAMP_INVALID") from None
    delta = dt - _EPOCH
    return delta.days * 86400 + delta.seconds, int((match["fraction"] or "").ljust(9, "0") or "0")


def _decimal(value: Any, *, positive=True) -> Decimal:
    if not isinstance(value, dict) or set(value) != {"value"} or not isinstance(value["value"], str):
        raise M15FillEvidenceError("M15_TRADE_DECIMAL_SCHEMA_INVALID")
    try:
        d = Decimal(value["value"])
    except InvalidOperation:
        raise M15FillEvidenceError("M15_TRADE_DECIMAL_INVALID") from None
    if not d.is_finite() or (positive and d <= 0):
        raise M15FillEvidenceError("M15_TRADE_DECIMAL_INVALID")
    return d


def _sha(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


@dataclass(frozen=True)
class ExpectedEntry:
    account_id: str
    order_id: str
    symbol: str
    side: str
    quantity: int
    price_step: Decimal

    def __post_init__(self):
        if not all(isinstance(v, str) and v and len(v) <= 128 for v in
                   (self.account_id, self.order_id, self.symbol)):
            raise M15FillEvidenceError("M15_EXPECTED_IDENTITY_INVALID")
        if self.side not in {"SIDE_BUY", "SIDE_SELL"}:
            raise M15FillEvidenceError("M15_EXPECTED_SIDE_INVALID")
        if type(self.quantity) is not int or self.quantity <= 0:
            raise M15FillEvidenceError("M15_EXPECTED_QUANTITY_INVALID")
        if not isinstance(self.price_step, Decimal) or not self.price_step.is_finite() or self.price_step <= 0:
            raise M15FillEvidenceError("M15_EXPECTED_PRICE_STEP_INVALID")


def analyze_account_trades(
    response: dict, expected: ExpectedEntry, *, start: str, end: str, limit: int
) -> dict:
    """No live adoption. Empty/no-matching history is NOT a verified fill."""
    lower, upper = _time(start), _time(end)
    if lower >= upper or type(limit) is not int or not 0 < limit <= 1000:
        raise M15FillEvidenceError("M15_HISTORY_INTERVAL_OR_LIMIT_INVALID")
    if not isinstance(response, dict) or not isinstance(response.get("trades"), list):
        raise M15FillEvidenceError("M15_HISTORY_SCHEMA_INVALID")
    rows = response["trades"]
    if len(rows) >= limit or any(response.get(k) not in (None, "", 0) for k in
                                 ("next_cursor", "next_page_token")):
        raise M15FillEvidenceError("M15_HISTORY_COMPLETENESS_UNPROVEN")
    found = {}
    for row in rows:
        if not isinstance(row, dict):
            raise M15FillEvidenceError("M15_HISTORY_ROW_INVALID")
        if row.get("order_id") != expected.order_id:
            continue
        if (row.get("account_id") != expected.account_id or
                row.get("symbol") != expected.symbol or row.get("side") != expected.side):
            raise M15FillEvidenceError("M15_MATCHING_ORDER_IDENTITY_INVALID")
        if row.get("currency") not in {"RUB", "XXX"}:
            raise M15FillEvidenceError("M15_FILL_CURRENCY_UNPROVEN")
        trade_id = row.get("trade_id")
        if not isinstance(trade_id, str) or not trade_id:
            raise M15FillEvidenceError("M15_TRADE_ID_MISSING")
        timestamp = _time(row.get("timestamp"))
        if not lower <= timestamp < upper:
            raise M15FillEvidenceError("M15_FILL_OUTSIDE_HISTORY_INTERVAL")
        price = _decimal(row.get("price"))
        if (price / expected.price_step) != (price / expected.price_step).to_integral_value():
            raise M15FillEvidenceError("M15_FILL_PRICE_OFF_GRID")
        contracts = _decimal(row.get("size"))
        if contracts != contracts.to_integral_value():
            raise M15FillEvidenceError("M15_FILL_QUANTITY_NOT_INTEGER")
        q = int(contracts)
        fact = {"trade_id_sha256": _sha(trade_id), "quantity": q, "price": format(price, "f"),
                "timestamp_seconds": timestamp[0], "timestamp_nanoseconds": timestamp[1],
                "feed_currency": row["currency"]}
        if trade_id in found and found[trade_id] != fact:
            raise M15FillEvidenceError("M15_FILL_ID_CONFLICT")
        found[trade_id] = fact
    facts = sorted(found.values(), key=lambda v: v["trade_id_sha256"])
    qty = sum(f["quantity"] for f in facts)
    if qty > expected.quantity:
        raise M15FillEvidenceError("M15_FILLS_EXCEED_ORDER_QUANTITY")
    weighted = sum((Fraction(f["price"]) * f["quantity"] for f in facts), Fraction(0))
    avg = weighted / qty if qty else None
    return {
        "account_sha256": _sha(expected.account_id),
        "order_id_sha256": _sha(expected.order_id),
        "symbol": expected.symbol,
        "side": expected.side,
        "fill_count": len(facts),
        "matched_quantity": qty,
        "fill_set_sha256": _sha(json.dumps(facts, sort_keys=True, separators=(",", ":"))),
        "weighted_price_exact": (None if avg is None else {
            "numerator": str(avg.numerator), "denominator": str(avg.denominator)
        }),
        "quantity_status": ("FULL" if qty == expected.quantity else "PARTIAL" if qty else "NO_MATCH"),
        "verified_fill": qty > 0,
        "commission_authority": "NOT_VERIFIED",
        "sqlite_reconciled": False,
        "live_authorized": False,
        "scope": "READONLY_DIAGNOSTIC_ONLY",
    }
