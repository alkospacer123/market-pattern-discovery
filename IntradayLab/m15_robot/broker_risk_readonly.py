"""M15-only public exchange parameters and separate-account FINAM GET evidence.

Pure read-side decoding. Never infer tick value, realized cash-flow basis, or
commission from GO or metadata; no orders, task, H1 runtime or SQLite access.
"""
from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal, InvalidOperation
from typing import Any

from .spec import INSTRUMENTS


class M15RiskAuthorityError(RuntimeError):
    pass


def decimal_value(value: Any, *, positive: bool = False) -> Decimal:
    if not isinstance(value, dict) or set(value) != {"value"} or not isinstance(value["value"], str):
        raise M15RiskAuthorityError("M15_RISK_DECIMAL_SCHEMA_INVALID")
    try:
        result = Decimal(value["value"])
    except InvalidOperation:
        raise M15RiskAuthorityError("M15_RISK_DECIMAL_INVALID") from None
    if not result.is_finite() or (positive and result <= 0):
        raise M15RiskAuthorityError("M15_RISK_DECIMAL_INVALID")
    return result



def _account_decimal(container: dict, field: str, *, positive: bool = False) -> Decimal:
    """Schema-only error detail. Never include broker account values in errors."""
    if field not in {"equity", "unrealized_profit", "available_cash",
                     "money_reserved", "initial_margin", "maintenance_margin"}:
        raise M15RiskAuthorityError("M15_RISK_UNRECOGNIZED_FINANCIAL_FIELD")
    if field not in container:
        raise M15RiskAuthorityError("M15_RISK_DECIMAL_" + field.upper() + "_MISSING")
    try:
        return decimal_value(container[field], positive=positive)
    except M15RiskAuthorityError:
        raise M15RiskAuthorityError("M15_RISK_DECIMAL_" + field.upper() + "_INVALID") from None


def rub_money(value: Any, *, positive: bool = False) -> Decimal:
    if (not isinstance(value, dict) or set(value) != {"currency_code", "units", "nanos"}
            or value["currency_code"] != "RUB"
            or not isinstance(value["units"], str)
            or isinstance(value["nanos"], bool)
            or type(value["nanos"]) is not int
            or abs(value["nanos"]) >= 1_000_000_000):
        raise M15RiskAuthorityError("M15_RISK_MONEY_SCHEMA_INVALID")
    try:
        units = Decimal(value["units"])
    except InvalidOperation:
        raise M15RiskAuthorityError("M15_RISK_MONEY_INVALID") from None
    if (not units.is_finite() or units != units.to_integral_value()
            or (units > 0 and value["nanos"] < 0)
            or (units < 0 and value["nanos"] > 0)):
        raise M15RiskAuthorityError("M15_RISK_MONEY_INVALID")
    result = units + Decimal(value["nanos"]) / Decimal(1_000_000_000)
    if positive and result <= 0:
        raise M15RiskAuthorityError("M15_RISK_MONEY_NOT_POSITIVE")
    return result


@dataclass(frozen=True)
class M15AccountSnapshot:
    available_cash: Decimal
    equity: Decimal
    unrealized_profit: Decimal
    broker_equity_minus_unrealized: Decimal
    portfolio_type: str


def check_account(account: dict, expected_account_id: str) -> M15AccountSnapshot:
    if (not isinstance(account, dict) or account.get("account_id") != expected_account_id
            or account.get("status") not in {"ACCOUNT_ACTIVE", "ACCOUNT_STATUS_ACTIVE"}
            or not isinstance(account.get("positions"), list)):
        raise M15RiskAuthorityError("M15_RISK_ACCOUNT_BINDING_INVALID")
    equity = _account_decimal(account, "equity", positive=True)
    floating = _account_decimal(account, "unrealized_profit")
    fields = [x for x in ("portfolio_forts", "portfolio_mc", "portfolio_mct") if x in account]
    if len(fields) != 1:
        raise M15RiskAuthorityError("M15_RISK_PORTFOLIO_ONEOF_INVALID")
    f = fields[0]
    portfolio = account[f]
    if not isinstance(portfolio, dict):
        raise M15RiskAuthorityError("M15_RISK_PORTFOLIO_INVALID")
    if account.get("type") in {"FORTS", "ACCOUNT_TYPE_FORTS"} and f == "portfolio_forts":
        available = _account_decimal(portfolio, "available_cash")
        reserved = _account_decimal(portfolio, "money_reserved")
        if reserved < 0:
            raise M15RiskAuthorityError("M15_RISK_RESERVED_INVALID")
    elif account.get("type") == "UNION" and f == "portfolio_mc":
        available = _account_decimal(portfolio, "available_cash")
        if _account_decimal(portfolio, "initial_margin") < 0 or _account_decimal(portfolio, "maintenance_margin") < 0:
            raise M15RiskAuthorityError("M15_RISK_MC_MARGIN_INVALID")
    else:
        raise M15RiskAuthorityError("M15_RISK_PORTFOLIO_TYPE_INVALID")
    if available < 0 or equity - floating <= 0:
        raise M15RiskAuthorityError("M15_RISK_FINANCIAL_INVALID")
    return M15AccountSnapshot(available, equity, floating, equity - floating, f)


@dataclass(frozen=True)
class M15InstrumentParams:
    symbol: str
    price_step: Decimal
    trade_lot_size: int
    long_initial_margin_rub: Decimal
    short_initial_margin_rub: Decimal
    tick_value_authority: str = "NOT_PROVEN"


def check_instrument(asset: dict, params: dict, symbol: str, account_id: str) -> M15InstrumentParams:
    if symbol not in tuple(x + "@RTSX" for x in INSTRUMENTS):
        raise M15RiskAuthorityError("M15_RISK_SYMBOL_NOT_N4")
    if not isinstance(asset, dict) or not isinstance(params, dict):
        raise M15RiskAuthorityError("M15_RISK_ASSET_SCHEMA_INVALID")
    if (str(asset.get("ticker")) + "@" + str(asset.get("mic")) != symbol
            or params.get("symbol") != symbol or params.get("account_id") != account_id):
        raise M15RiskAuthorityError("M15_RISK_ASSET_ACCOUNT_OR_SYMBOL_MISMATCH")
    if (not isinstance(asset.get("decimals"), int) or isinstance(asset["decimals"], bool)
            or not 0 <= asset["decimals"] <= 12 or not isinstance(asset.get("min_step"), str)):
        raise M15RiskAuthorityError("M15_RISK_ASSET_STEP_INVALID")
    try:
        step = Decimal(asset["min_step"]).scaleb(-asset["decimals"])
    except InvalidOperation:
        raise M15RiskAuthorityError("M15_RISK_ASSET_STEP_INVALID") from None
    if not step.is_finite() or step <= 0:
        raise M15RiskAuthorityError("M15_RISK_ASSET_STEP_INVALID")
    lot = params.get("trade_lot_size")
    if not isinstance(lot, str) or not lot.isascii() or not lot.isdigit() or int(lot) <= 0:
        raise M15RiskAuthorityError("M15_RISK_ASSET_TRADE_LOT_INVALID")
    long = rub_money(params.get("long_initial_margin"), positive=True)
    short = rub_money(params.get("short_initial_margin"), positive=True)
    return M15InstrumentParams(symbol, step, int(lot), long, short)
