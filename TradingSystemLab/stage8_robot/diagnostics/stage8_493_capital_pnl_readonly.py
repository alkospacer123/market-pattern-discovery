"""Stage8 #493: operator-confirmed capital vs contribution-adjusted result.

PURE READONLY classification. No broker connection, production SQLite,
credential, task, order, or mutable state. Input data is an independently
collected PRIVATE snapshot; this module does not prove broker statement facts.

Frozen sizing continues to use the accepted ProductionService realized basis.
External deposits are accounted for in a separate reporting-only calculation
and MUST NOT be copied into the existing subtractive sizing state field.
"""
from __future__ import annotations

from decimal import Decimal, InvalidOperation


SCHEMA = "stage8_493_capital_pnl_readonly.v1"
SPEC = "PROD_STAGE7_46DB784378797C7FB04636892350AFF21006D71A31F2CED9D4B974EDA2DC36B8"
IDENTITY = "TRAIL1__N4_01__FULL__R15"


class Blocked(ValueError):
    pass


def _money(value: object, field: str, *, strictly_positive: bool = False) -> Decimal:
    if type(value) is not str or not value or value.strip() != value:
        raise Blocked(f"{field}_DECIMAL_STRING_REQUIRED")
    try:
        number = Decimal(value)
    except InvalidOperation:
        raise Blocked(f"{field}_DECIMAL_INVALID") from None
    if not number.is_finite() or (strictly_positive and number <= 0):
        raise Blocked(f"{field}_INVALID")
    return number


def _hash(value: object) -> bool:
    return (type(value) is str and len(value) == 64
            and all(c in "0123456789abcdef" for c in value))


def classify(data: dict) -> dict:
    """Never use the returned result as permission to change LIVE authority."""
    if type(data) is not dict or set(data) != {
        "schema_id", "production_specification_id", "active_identity",
        "account_identity_sha256", "broker_equity_rub", "unrealized_pnl_rub",
        "production_realized_equity_rub", "production_starting_realized_equity_rub",
        "sizing_explained_external_cash_flows_rub", "external_flows",
    }:
        raise Blocked("CAPITAL_REPORT_SCHEMA_INVALID")
    if (data["schema_id"] != SCHEMA or data["production_specification_id"] != SPEC
            or data["active_identity"] != IDENTITY or not _hash(data["account_identity_sha256"])):
        raise Blocked("CAPITAL_REPORT_IDENTITY_INVALID")

    equity = _money(data["broker_equity_rub"], "BROKER_EQUITY", strictly_positive=True)
    unrealized = _money(data["unrealized_pnl_rub"], "UNREALIZED_PNL")
    production = _money(data["production_realized_equity_rub"], "PRODUCTION_REALIZED", strictly_positive=True)
    starting = _money(data["production_starting_realized_equity_rub"], "PRODUCTION_STARTING", strictly_positive=True)
    deduction = _money(data["sizing_explained_external_cash_flows_rub"], "SIZING_DEDUCTION")
    # Current approved policy: 100% of contributed funds remain in risk capital.
    # The legacy field is *subtracted* by the frozen service. Never set deposits here.
    if deduction != 0:
        raise Blocked("NONZERO_SIZING_DEDUCTION_REQUIRES_SEPARATE_ACCOUNTING_REVIEW")
    capital = equity - unrealized - deduction
    if capital <= 0 or production != capital:
        raise Blocked("FROZEN_REALIZED_BASIS_NOT_RECONCILED")

    flows = data["external_flows"]
    if type(flows) is not list or not flows:
        raise Blocked("EXTERNAL_CONTRIBUTION_EVIDENCE_REQUIRED")
    seen = set()
    deposits = Decimal("0")
    withdrawals = Decimal("0")
    operator_only = False
    for flow in flows:
        if type(flow) is not dict or set(flow) != {
            "flow_id", "kind", "amount_rub", "account_identity_sha256",
            "source_classification",
        }:
            raise Blocked("CASH_FLOW_SCHEMA_INVALID")
        ident = flow["flow_id"]
        if (type(ident) is not str or not ident or len(ident) > 128
                or ident in seen or flow["account_identity_sha256"] != data["account_identity_sha256"]):
            raise Blocked("CASH_FLOW_IDENTITY_OR_DUPLICATE_INVALID")
        seen.add(ident)
        value = _money(flow["amount_rub"], "CASH_FLOW_AMOUNT", strictly_positive=True)
        if flow["kind"] == "DEPOSIT":
            deposits += value
        elif flow["kind"] == "WITHDRAWAL":
            withdrawals += value
        else:
            raise Blocked("CASH_FLOW_TYPE_INVALID")
        if flow["source_classification"] == "OPERATOR_CONFIRMED":
            operator_only = True
        elif flow["source_classification"] != "BROKER_STATEMENT_OBSERVED":
            raise Blocked("CASH_FLOW_SOURCE_INVALID")
    net_contributions = deposits - withdrawals
    # This is a capital-adjusted ACCOUNT change, NOT a verified trading PnL.
    # Fees, financing and unclassified flows may remain in the account change.
    adjusted = capital - starting - net_contributions
    return {
        "classification": "READONLY_CAPITAL_AND_EXTERNAL_FLOW_SEPARATED_NOT_PNL_AUTHORITY",
        "source_status": ("OPERATOR_CONFIRMATION_NOT_BROKER_STATEMENT_RECONCILED"
                          if operator_only else "BROKER_STATEMENT_ROWS_ASSERTED_NOT_INDEPENDENTLY_VERIFIED"),
        "account_identity_sha256": data["account_identity_sha256"],
        "frozen_full_r15_capital_rub": str(capital),
        "new_position_r15_nominal_cash_rub": str(capital * Decimal("0.015")),
        "net_external_contributions_rub": str(net_contributions),
        "contribution_adjusted_account_change_rub": str(adjusted),
        "deposit_is_trading_profit": False,
        "broker_statement_and_fee_pnl_audit": "NOT_PERFORMED",
        "frozen_strategy_or_risk_changed": False,
        "production_sqlite_writes": 0,
        "real_order_endpoint_calls": 0,
        "live_execution_authorized": False,
    }
