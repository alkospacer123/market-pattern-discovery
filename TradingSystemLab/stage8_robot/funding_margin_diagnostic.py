"""Order-incapable Stage 8.9 REAL_READONLY funding and margin diagnostic.

The emitted JSON is deliberately sanitized.  Raw broker responses and account
identifiers are never included; the operator keeps the report outside Git.
"""
from __future__ import annotations

import hashlib
import json
import os
from datetime import datetime, timedelta, timezone
from decimal import Decimal
from pathlib import Path

from .finam_api import FinamAPI, completed_h1_bars
from .instrument_resolver import MOEX_REFERENCE, N4, discover_finam_asset, validate_finam_binding
from .margin import (AVAILABLE_CASH_SEMANTICS, MarginBatchBudget,
                     cap_r15_by_margin, directional_initial_margin, forts_funds,
                     parse_rest_decimal_value_object)
from .readonly_supervisor import trading_h1_windows
from .risk import ContractEconomics, size_position
from .specification import ACTIVE_IDENTITY, PRODUCTION_SPECIFICATION_ID

SCHEMA = "stage8-8-9-funding-margin-validation/v1"
REPOSITORY_STATUS = "STAGE_8_9_FUNDING_MARGIN_DIAGNOSTIC_READY_PENDING_INTEL_VALIDATION"
READY = "STAGE_8_9_FUNDING_MARGIN_VALIDATED"
REPOSITORY_ROOT = Path(__file__).resolve().parents[2]


def _blocked(status: str, reason: str, base: dict) -> dict:
    return {**base, "funding_classification": status, "reason_code": reason,
            "funding_margin_feasibility": "BLOCKED"}


def evaluate(*, account: dict, orders: object, details: dict, account_id: str,
             production_id: str, registry: dict, params: dict,
             sizing: dict, timestamp: str) -> dict:
    """Evaluate synthetic/read-only inputs and return sanitized evidence only."""
    base = {"schema": SCHEMA, "timestamp": timestamp,
            "production_specification_id": production_id,
            "account_identity_sha256": hashlib.sha256(account_id.encode()).hexdigest(),
            "account_type": account.get("type") if isinstance(account, dict) else None,
            "account_status": account.get("status") if isinstance(account, dict) else None,
            "readonly_token": details.get("readonly") is True,
            "account_clean": False, "portfolio_forts_present": False,
            "n4_binding_valid": False, "no_order_call_assertion": True,
            "available_cash_semantics": AVAILABLE_CASH_SEMANTICS}
    if production_id != PRODUCTION_SPECIFICATION_ID:
        return _blocked("BLOCKED_PRODUCTION_AUTHORITY_INVALID", "PRODUCTION_ID_MISMATCH", base)
    if details.get("readonly") is not True:
        return _blocked("BLOCKED_SAFETY_PREREQUISITE", "TOKEN_NOT_READONLY", base)
    if account_id not in {str(value) for value in details.get("account_ids", [])}:
        return _blocked("BLOCKED_SAFETY_PREREQUISITE", "ACCOUNT_NOT_ENUMERATED", base)
    if account.get("status") != "ACTIVE":
        return _blocked("BLOCKED_ACCOUNT_INACTIVE", "ACCOUNT_NOT_ACTIVE", base)
    positions = account.get("positions") if isinstance(account, dict) else None
    active_orders = orders.get("orders") if isinstance(orders, dict) else orders
    if not isinstance(positions, list) or not isinstance(active_orders, list):
        return _blocked("BLOCKED_ACCOUNT_SCHEMA_INVALID", "CLEANLINESS_SCHEMA_INVALID", base)
    if positions or active_orders:
        return _blocked("BLOCKED_ACCOUNT_NOT_CLEAN", "POSITIONS_PRESENT" if positions else "ACTIVE_ORDERS_PRESENT", base)
    base["account_clean"] = True
    expected = set(N4)
    if (set(registry) != expected or any(not isinstance(registry[x], dict) or
            registry[x].get("status") != "AUTHENTICATED_REAL_READONLY" for x in N4)):
        return _blocked("BLOCKED_N4_AUTHORITY_INVALID", "N4_REGISTRY_NOT_EXACT_AUTHENTICATED_4_OF_4", base)
    base["n4_binding_valid"] = True
    base["portfolio_forts_present"] = isinstance(account.get("portfolio_forts"), dict)
    if not base["portfolio_forts_present"]:
        return _blocked("BLOCKED_ACCOUNT_FINANCIALS_UNAVAILABLE", "FORTS_PORTFOLIO_MISSING", base)
    try:
        available, reserved = forts_funds(account)
    except ValueError as exc:
        return _blocked("BLOCKED_ACCOUNT_FINANCIALS_INVALID", str(exc), base)
    try:
        equity = parse_rest_decimal_value_object(account.get("equity"), positive=True)
    except ValueError as exc:
        return _blocked("BLOCKED_ACCOUNT_EQUITY_INVALID", str(exc), base)
    margins = {}
    try:
        for code in N4:
            margins[code] = {direction: directional_initial_margin(params[code], direction)
                             for direction in ("LONG", "SHORT")}
    except (KeyError, TypeError, ValueError) as exc:
        reason = str(exc) if isinstance(exc, ValueError) else "N4_DIRECTIONAL_MARGIN_MISSING"
        return _blocked("BLOCKED_DIRECTIONAL_MARGIN_INVALID", reason, base)
    cases = {}; budget = MarginBatchBudget(available); reservations = []
    try:
        for code in N4:
            evidence = sizing[code]
            lot = evidence["trade_lot_size"]
            for direction in ("LONG", "SHORT"):
                result = cap_r15_by_margin(realized_equity=equity, entry=evidence["entry"],
                    stop=evidence["stop"], price_step=evidence["price_step"],
                    tick_value=evidence["tick_value"], r15_quantity=evidence["r15_quantity"],
                    available_cash=available, direction=direction,
                    initial_margin=margins[code][direction], trade_lot_size=lot)
                valid = (result.final_quantity <= result.r15_quantity and
                         result.final_quantity <= result.margin_quantity and
                         result.final_quantity % lot == 0 and
                         result.initial_margin * result.final_quantity <= available)
                if not valid: raise ValueError("FUNDING_ARITHMETIC_INVARIANT_FAILED")
                cases[f"{code}:{direction}"] = result.evidence()
            batch = budget.size_and_reserve(realized_equity=equity, entry=evidence["entry"],
                stop=evidence["stop"], price_step=evidence["price_step"], tick_value=evidence["tick_value"],
                r15_quantity=evidence["r15_quantity"], direction="LONG",
                initial_margin=margins[code]["LONG"], trade_lot_size=lot)
            reservations.append({"instrument": code, "quantity": batch.final_quantity,
                                 "remaining_cash": str(budget.remaining)})
        if budget.remaining < 0: raise ValueError("LOCAL_MARGIN_OVERALLOCATION")
    except (KeyError, TypeError, ValueError) as exc:
        reason = str(exc) if isinstance(exc, ValueError) else "SIZING_EVIDENCE_INVALID"
        return _blocked("BLOCKED_FUNDING_FEASIBILITY_INVALID", reason, base)
    return {**base, "funding_classification": READY, "reason_code": "ALL_AUTHORITIES_VALID",
            "financial_schema_valid": True, "equity_valid": True,
            "directional_margins_valid": True, "forts_available_cash": str(available),
            "forts_money_reserved": str(reserved), "realized_equity": str(equity),
            "per_instrument": cases,
            "batch_budget": {"status": "PASS", "sequence": list(N4),
                             "reservations": reservations, "remaining_cash": str(budget.remaining)},
            "funding_margin_feasibility": "PASS"}


def run(api, account_id: str, report_path: Path) -> dict:
    """Fetch only GET/session authorities, evaluate them, and write external JSON."""
    destination = report_path.expanduser().resolve()
    if destination == REPOSITORY_ROOT or REPOSITORY_ROOT in destination.parents:
        raise RuntimeError("STAGE8_9_REPORT_REPOSITORY_OUTPUT_FORBIDDEN")
    api.create_session(); details = api.session_details()
    account = api.account(account_id); orders = api.orders(account_id)
    positions = account.get("positions") if isinstance(account, dict) else None
    active_orders = orders.get("orders") if isinstance(orders, dict) else orders
    if (not isinstance(positions, list) or not isinstance(active_orders, list)
            or positions or active_orders or details.get("readonly") is not True):
        report = evaluate(account=account, orders=orders, details=details, account_id=account_id,
                          production_id=PRODUCTION_SPECIFICATION_ID, registry={}, params={}, sizing={},
                          timestamp=datetime.now(timezone.utc).isoformat())
        destination.write_text(json.dumps(report, indent=2, sort_keys=True)+"\n", encoding="utf-8")
        return report
    assets = api.assets_all_active(); registry = {}; params = {}; sizing = {}
    now = datetime.now(timezone.utc)
    for code in N4:
        asset, reason = discover_finam_asset(code, assets)
        if reason: registry[code] = {"status": reason}; continue
        symbol = asset["symbol"]; item = api.asset_params(symbol, account_id)
        binding = validate_finam_binding(code, asset, item, api.schedule(symbol),
                                         api.asset(symbol, account_id)).to_dict()
        if binding["status"].startswith("AUTHENTICATED_"):
            binding["status"] = "AUTHENTICATED_REAL_READONLY"
        registry[code] = binding; params[code] = item
        raw = api.bars(symbol, (now - timedelta(days=2)).isoformat(), now.isoformat())
        bars = completed_h1_bars(raw, now, trading_h1_windows(api.schedule(symbol)))
        if bars:
            step, tick, _ = MOEX_REFERENCE[code]; entry = Decimal(str(bars[-1]["close"])); stop = entry-step*10
            lot = int(Decimal(binding["trade_lot_size"]))
            try:
                equity = parse_rest_decimal_value_object(account.get("equity"), positive=True)
                r15 = size_position(equity, entry, stop, ContractEconomics(step, tick, lot, True))
                sizing[code] = {"entry": entry, "stop": stop, "price_step": step,
                                "tick_value": tick, "trade_lot_size": lot, "r15_quantity": r15.quantity}
            except ValueError:
                # ``evaluate`` owns the sanitized equity classification.
                pass
    report = evaluate(account=account, orders=orders, details=details, account_id=account_id,
                      production_id=PRODUCTION_SPECIFICATION_ID, registry=registry, params=params,
                      sizing=sizing, timestamp=now.isoformat())
    destination.write_text(json.dumps(report, indent=2, sort_keys=True)+"\n", encoding="utf-8")
    return report


def main() -> None:
    if os.getenv("FINAM_MODE") != "REAL_READONLY": raise RuntimeError("REAL_READONLY_MODE_REQUIRED")
    if os.getenv("NEW_ENTRIES_DISABLED", "").lower() != "true": raise RuntimeError("NEW_ENTRIES_MUST_BE_DISABLED")
    if os.getenv("PRODUCTION_SPECIFICATION_ID") != PRODUCTION_SPECIFICATION_ID: raise RuntimeError("PRODUCTION_ID_REQUIRED")
    if os.getenv("PRODUCTION_IDENTITY") != ACTIVE_IDENTITY: raise RuntimeError("PRODUCTION_IDENTITY_REQUIRED")
    account_id = os.environ["FINAM_REAL_ACCOUNT_ID"]
    report = run(FinamAPI(os.environ["FINAM_API_SECRET"]), account_id,
                 Path(os.environ["STAGE8_9_REPORT_PATH"]))
    if report["funding_classification"] != READY:
        raise RuntimeError(f"{report['funding_classification']}:{report['reason_code']}")


if __name__ == "__main__": main()
