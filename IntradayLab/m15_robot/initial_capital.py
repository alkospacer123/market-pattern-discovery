"""Initial M15 realized-equity proof from own FINAM cash transactions.

Pure checks on already retrieved exact-account READONLY responses.
This proves an INITIAL deposit-only basis, not future ledger reconciliation.
No secrets, balances or raw FINAM responses are logged.
"""
from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from decimal import Decimal, InvalidOperation
from typing import Any

from .broker_risk_readonly import M15AccountSnapshot, M15RiskAuthorityError


def _timestamp(value: Any) -> datetime:
    if not isinstance(value, str):
        raise M15RiskAuthorityError("M15_CAPITAL_TIMESTAMP_MISSING")
    try:
        dt = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError:
        raise M15RiskAuthorityError("M15_CAPITAL_TIMESTAMP_INVALID") from None
    if dt.tzinfo is None or dt.utcoffset() is None:
        raise M15RiskAuthorityError("M15_CAPITAL_TIMESTAMP_INVALID")
    return dt.astimezone(timezone.utc)


def lifetime_interval(account: dict, now: datetime) -> tuple[str, str, datetime, datetime]:
    """Account creation to fresh UTC, inclusive birth/exclusive end."""
    if not isinstance(account, dict) or not isinstance(now, datetime):
        raise M15RiskAuthorityError("M15_CAPITAL_ACCOUNT_SCHEMA_INVALID")
    if now.tzinfo is None or now.utcoffset() is None:
        raise M15RiskAuthorityError("M15_CAPITAL_CLOCK_INVALID")
    birth = _timestamp(account.get("open_account_date"))
    current = now.astimezone(timezone.utc)
    if birth > current or (current - birth) > timedelta(days=31):
        raise M15RiskAuthorityError("M15_CAPITAL_ACCOUNT_LIFETIME_UNSUPPORTED")
    begin = birth - timedelta(seconds=1)
    end = current + timedelta(minutes=1)
    return begin.isoformat().replace("+00:00", "Z"), end.isoformat().replace("+00:00", "Z"), begin, end


def _money(change: Any) -> Decimal:
    """Protobuf Money optional nanos=0; exact RUB finite signed amount."""
    if not isinstance(change, dict) or not set(change).issubset({"currency_code", "units", "nanos"}):
        raise M15RiskAuthorityError("M15_CAPITAL_MONEY_SCHEMA_INVALID")
    if change.get("currency_code") != "RUB":
        raise M15RiskAuthorityError("M15_CAPITAL_NONRUB_INVALID")
    units = change.get("units", "0")
    nanos = change.get("nanos", 0)
    if not isinstance(units, str) or type(nanos) is not int or abs(nanos) >= 1000000000:
        raise M15RiskAuthorityError("M15_CAPITAL_MONEY_SCHEMA_INVALID")
    try:
        money = Decimal(units)
    except InvalidOperation:
        raise M15RiskAuthorityError("M15_CAPITAL_MONEY_INVALID") from None
    if not money.is_finite() or money != money.to_integral_value() or (money > 0 and nanos < 0) or (money < 0 and nanos > 0):
        raise M15RiskAuthorityError("M15_CAPITAL_MONEY_INVALID")
    return money + Decimal(nanos) / Decimal(1000000000)


@dataclass(frozen=True)
class InitialCapitalProof:
    deposit_count: int
    basis: Decimal
    authority: str = "INITIAL_CASHFLOW_ONLY"


def prove_initial_basis(
    *, account: dict, funds: M15AccountSnapshot, trades: dict,
    transactions: dict, begin: datetime, end: datetime, limit: int = 1000,
) -> InitialCapitalProof:
    """Only positive RUB deposits/transfers, no deals; exact broker equity."""
    if not isinstance(account, dict) or not isinstance(funds, M15AccountSnapshot):
        raise M15RiskAuthorityError("M15_CAPITAL_ACCOUNT_UNPROVEN")
    if account.get("first_trade_date"):
        raise M15RiskAuthorityError("M15_CAPITAL_PAST_TRADE_UNPROVEN")
    if not isinstance(trades, dict) or not isinstance(trades.get("trades"), list) or trades["trades"]:
        raise M15RiskAuthorityError("M15_CAPITAL_TRADES_NOT_ZERO")
    if not isinstance(transactions, dict) or not isinstance(transactions.get("transactions"), list):
        raise M15RiskAuthorityError("M15_CAPITAL_TRANSACTIONS_SCHEMA_INVALID")
    rows = transactions["transactions"]
    if not rows or len(rows) >= limit:
        raise M15RiskAuthorityError("M15_CAPITAL_TRANSACTIONS_EMPTY_OR_SATURATED")
    if funds.unrealized_profit != 0 or funds.equity <= 0:
        raise M15RiskAuthorityError("M15_CAPITAL_NONFLAT_FINANCIAL_STATE")
    total = Decimal("0")
    seen = set()
    for row in rows:
        if not isinstance(row, dict) or not isinstance(row.get("id"), str) or not row["id"] or row["id"] in seen:
            raise M15RiskAuthorityError("M15_CAPITAL_TRANSACTION_ID_INVALID")
        seen.add(row["id"])
        if not begin <= _timestamp(row.get("timestamp")) < end:
            raise M15RiskAuthorityError("M15_CAPITAL_TRANSACTION_OUT_OF_INTERVAL")
        if row.get("trade") or row.get("transaction_category") not in ("DEPOSIT", "TRANSFER", 1, 11):
            raise M15RiskAuthorityError("M15_CAPITAL_NONDEPOSIT_TRANSACTION")
        amount = _money(row.get("change"))
        if amount <= 0:
            raise M15RiskAuthorityError("M15_CAPITAL_NONPOSITIVE_DEPOSIT")
        total += amount
    if total != funds.broker_equity_minus_unrealized:
        raise M15RiskAuthorityError("M15_CAPITAL_DEPOSITS_EQUITY_MISMATCH")
    return InitialCapitalProof(len(rows), total)
