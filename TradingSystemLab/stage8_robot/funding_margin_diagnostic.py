"""Order-incapable Stage 8.9 REAL_READONLY funding and margin diagnostic.

The emitted JSON is deliberately sanitized.  Raw broker responses and account
identifiers are never included; the operator keeps the report outside Git.
"""
from __future__ import annotations

import csv
import hashlib
import json
import os
from datetime import datetime, timedelta, timezone
from decimal import Decimal
from pathlib import Path

from .finam_api import FinamAPI, completed_h1_bars
from .instrument_resolver import (MOEX_REFERENCE, N4, discover_finam_asset,
                                  parse_rest_value_object, validate_finam_binding)
from .margin import (AVAILABLE_CASH_SEMANTICS, MarginBatchBudget,
                     cap_r15_by_margin, directional_initial_margin, portfolio_authority,
                     parse_rest_decimal_value_object)
from .readonly_supervisor import SafetyFault, trading_h1_windows
from .risk import ContractEconomics, size_position
from .specification import ACTIVE_IDENTITY, PRODUCTION_SPECIFICATION_ID

SCHEMA = "stage8-8-9-funding-margin-validation/v1"
REPOSITORY_STATUS = "STAGE_8_9_REAL_ACCOUNT_FUNDING_MARGIN_VALIDATION_COMPLETE"
READY = "STAGE_8_9_FUNDING_MARGIN_VALIDATED"
ZERO_CAPACITY = "BLOCKED_INSUFFICIENT_CONTRACT_CAPACITY"
REPOSITORY_ROOT = Path(__file__).resolve().parents[2]
PRODUCTION_REGISTRY_PATH = Path(__file__).with_name("production_instrument_registry.csv")
ACTIVE_ACCOUNT_STATUSES = frozenset({"ACCOUNT_ACTIVE", "ACCOUNT_STATUS_ACTIVE"})
FROZEN_N4_IDENTITIES = {
    "USDRUBF": ("USDRUBF@RTSX", "RTSX", "3447194"),
    "CNYRUBF": ("CNYRUBF@RTSX", "RTSX", "3447192"),
    "GLDRUBF": ("GLDRUBF@RTSX", "RTSX", "4454911"),
    "IMOEXF": ("IMOEXF@RTSX", "RTSX", "4631091"),
}


def load_production_registry(path: Path = PRODUCTION_REGISTRY_PATH) -> dict[str, dict[str, str]]:
    """Load the frozen registry without repairing, replacing, or defaulting rows."""
    try:
        with path.open(newline="", encoding="utf-8") as handle:
            rows = list(csv.DictReader(handle))
    except (OSError, csv.Error):
        return {}
    if len(rows) != len(N4) or any(not row.get("research_symbol") for row in rows):
        return {}
    return {row["research_symbol"]: row for row in rows}


def _frozen_registry_valid(production_registry: dict) -> bool:
    if set(production_registry) != set(N4):
        return False
    for code in N4:
        frozen = production_registry.get(code)
        if not isinstance(frozen, dict):
            return False
        finam_symbol, mic, security_id = FROZEN_N4_IDENTITIES[code]
        if (frozen.get("research_symbol") != code
                or frozen.get("finam_symbol") != finam_symbol
                or frozen.get("mic") != mic
                or frozen.get("security_id") != security_id
                or frozen.get("binding_status") != "AUTHENTICATED_REAL_READONLY"
                or frozen.get("trading_status") != "TRADABLE"):
            return False
    return True


def _registry_matches_frozen_authority(production_registry: dict, live_registry: dict) -> bool:
    if not _frozen_registry_valid(production_registry) or set(live_registry) != set(N4):
        return False
    for code in N4:
        frozen = production_registry[code]
        live = live_registry.get(code)
        if not isinstance(live, dict):
            return False
        if (live.get("research_symbol") != frozen["research_symbol"]
                or live.get("finam_symbol") != frozen["finam_symbol"]
                or live.get("mic") != frozen["mic"]
                or str(live.get("security_id")) != frozen["security_id"]
                or live.get("status") != frozen["binding_status"]
                or live.get("is_tradable") is not True):
            return False
    return True


def _blocked(status: str, reason: str, base: dict) -> dict:
    return {**base, "funding_classification": status, "reason_code": reason,
            "funding_margin_feasibility": "BLOCKED"}


def evaluate(*, account: dict, orders: object, details: dict, account_id: str,
             production_id: str, registry: dict, production_registry: dict, params: dict,
             sizing: dict, timestamp: str) -> dict:
    """Evaluate synthetic/read-only inputs and return sanitized evidence only."""
    base = {"schema": SCHEMA, "timestamp": timestamp,
            "production_specification_id": production_id,
            "account_identity_sha256": hashlib.sha256(account_id.encode()).hexdigest(),
            "account_type": account.get("type") if isinstance(account, dict) else None,
            "account_status": account.get("status") if isinstance(account, dict) else None,
            "readonly_token": details.get("readonly") is True,
            "account_clean": False, "portfolio_variant": None,
            "portfolio_mc_present": False, "portfolio_forts_present": False,
            "financial_schema_valid": False,
            "mc_initial_margin_valid": False, "mc_maintenance_margin_valid": False,
            "n4_binding_valid": False, "no_order_call_assertion": True,
            "available_cash_semantics": AVAILABLE_CASH_SEMANTICS}
    if production_id != PRODUCTION_SPECIFICATION_ID:
        return _blocked("BLOCKED_PRODUCTION_AUTHORITY_INVALID", "PRODUCTION_ID_MISMATCH", base)
    if details.get("readonly") is not True:
        return _blocked("BLOCKED_SAFETY_PREREQUISITE", "TOKEN_NOT_READONLY", base)
    if account_id not in {str(value) for value in details.get("account_ids", [])}:
        return _blocked("BLOCKED_SAFETY_PREREQUISITE", "ACCOUNT_NOT_ENUMERATED", base)
    if account.get("status") not in ACTIVE_ACCOUNT_STATUSES:
        return _blocked("BLOCKED_ACCOUNT_INACTIVE", "ACCOUNT_NOT_ACTIVE", base)
    positions = account.get("positions") if isinstance(account, dict) else None
    active_orders = orders.get("orders") if isinstance(orders, dict) else orders
    if not isinstance(positions, list) or not isinstance(active_orders, list):
        return _blocked("BLOCKED_ACCOUNT_SCHEMA_INVALID", "CLEANLINESS_SCHEMA_INVALID", base)
    if positions or active_orders:
        return _blocked("BLOCKED_ACCOUNT_NOT_CLEAN", "POSITIONS_PRESENT" if positions else "ACTIVE_ORDERS_PRESENT", base)
    base["account_clean"] = True
    if not _registry_matches_frozen_authority(production_registry, registry):
        return _blocked("BLOCKED_N4_AUTHORITY_INVALID", "PRODUCTION_REGISTRY_BINDING_MISMATCH", base)
    base["n4_binding_valid"] = True
    base["portfolio_mc_present"] = isinstance(account.get("portfolio_mc"), dict)
    base["portfolio_forts_present"] = isinstance(account.get("portfolio_forts"), dict)
    try:
        authority = portfolio_authority(account)
    except ValueError as exc:
        return _blocked("BLOCKED_ACCOUNT_FINANCIALS_INVALID", str(exc), base)
    available = authority.available_cash
    base["portfolio_variant"] = authority.variant
    base["financial_schema_valid"] = True
    base["mc_initial_margin_valid"] = authority.initial_margin is not None
    base["mc_maintenance_margin_valid"] = authority.maintenance_margin is not None
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
    sizing_case_count = len(cases)
    positive_capacity_case_count = sum(
        case["final_quantity"] > 0 for case in cases.values())
    zero_capacity_case_count = sum(
        case["final_quantity"] == 0 for case in cases.values())
    positive_batch_reservation_count = sum(
        reservation["quantity"] > 0 for reservation in reservations)
    capacity_evidence = {
        "sizing_case_count": sizing_case_count,
        "positive_capacity_case_count": positive_capacity_case_count,
        "zero_capacity_case_count": zero_capacity_case_count,
        "positive_batch_reservation_count": positive_batch_reservation_count,
    }
    common = {**base,
            "financial_schema_valid": True, "equity_valid": True,
            "directional_margins_valid": True, "available_cash": str(available),
            "money_reserved": (str(authority.money_reserved)
                               if authority.money_reserved is not None else None),
            "realized_equity": str(equity),
            "per_instrument": cases,
            "batch_budget": {"status": "PASS", "sequence": list(N4),
                             "reservations": reservations, "remaining_cash": str(budget.remaining)},
            **capacity_evidence}
    if positive_capacity_case_count < 1:
        return {**common, "funding_classification": ZERO_CAPACITY,
                "reason_code": "ZERO_CONTRACT_CAPACITY",
                "funding_margin_feasibility": "BLOCKED"}
    return {**common, "funding_classification": READY,
            "reason_code": "ALL_AUTHORITIES_VALID",
            "funding_margin_feasibility": "PASS"}


def run(api, account_id: str, report_path: Path) -> dict:
    """Fetch only GET/session authorities, evaluate them, and write external JSON.

    Collection is deliberately staged.  Each session/account safety gate is
    evaluated before the next (more privileged) read is made, and a binding
    that fails validation is never used as sizing evidence.
    """
    destination = report_path.expanduser().resolve()
    if destination == REPOSITORY_ROOT or REPOSITORY_ROOT in destination.parents:
        raise RuntimeError("STAGE8_9_REPORT_REPOSITORY_OUTPUT_FORBIDDEN")
    production_registry = load_production_registry()

    def finish(*, account: dict, orders: object, details: dict,
               registry: dict | None = None, params: dict | None = None,
               sizing: dict | None = None, timestamp: str | None = None) -> dict:
        report = evaluate(account=account, orders=orders, details=details,
                          account_id=account_id,
                          production_id=PRODUCTION_SPECIFICATION_ID,
                          registry=registry or {},
                          production_registry=production_registry,
                          params=params or {}, sizing=sizing or {},
                          timestamp=timestamp or datetime.now(timezone.utc).isoformat())
        destination.write_text(json.dumps(report, indent=2, sort_keys=True)+"\n",
                               encoding="utf-8")
        return report

    api.create_session()
    details = api.session_details()
    if not isinstance(details, dict):
        details = {}
    # Session authority precedes every account-bound request.
    if (details.get("readonly") is not True
            or account_id not in {str(value) for value in details.get("account_ids", [])}):
        return finish(account={}, orders=[], details=details)

    account = api.account(account_id)
    # Do not even enumerate orders for an account whose status is not accepted.
    if (not isinstance(account, dict)
            or account.get("status") not in ACTIVE_ACCOUNT_STATUSES):
        return finish(account=account if isinstance(account, dict) else {},
                      orders=[], details=details)

    orders = api.orders(account_id)
    positions = account.get("positions") if isinstance(account, dict) else None
    active_orders = orders.get("orders") if isinstance(orders, dict) else orders
    if (not isinstance(positions, list) or not isinstance(active_orders, list)
            or positions or active_orders):
        return finish(account=account, orders=orders, details=details)
    if not _frozen_registry_valid(production_registry):
        return finish(account=account, orders=orders, details=details)

    assets = api.assets_all_active(); registry = {}; params = {}; sizing = {}
    now = datetime.now(timezone.utc)
    for code in N4:
        asset, reason = discover_finam_asset(code, assets)
        if reason: registry[code] = {"status": reason}; continue
        symbol = asset["symbol"]
        item = api.asset_params(symbol, account_id)
        schedule = api.schedule(symbol)
        binding = validate_finam_binding(code, asset, item, schedule,
                                         api.asset(symbol, account_id)).to_dict()
        if binding["status"].startswith("AUTHENTICATED_"):
            binding["status"] = "AUTHENTICATED_REAL_READONLY"
        registry[code] = binding; params[code] = item
        # Invalid identity/params/schedule evidence is retained for the exact
        # frozen-authority comparison, but must never flow into H1 or sizing.
        if binding["status"] != "AUTHENTICATED_REAL_READONLY":
            continue
        raw = api.bars(symbol, (now - timedelta(days=2)).isoformat(), now.isoformat())
        try:
            bars = completed_h1_bars(raw, now, trading_h1_windows(schedule))
        except (SafetyFault, TypeError, ValueError):
            # ``evaluate`` owns the sanitized missing/invalid sizing result.
            continue
        if bars:
            try:
                step, tick, _ = MOEX_REFERENCE[code]
                # FINAM GET /v1/instruments/{symbol}/bars represents open,
                # high, low, close, and volume as REST {"value": "decimal"}
                # objects.  This is deliberately not the protobuf num/scale
                # representation and numeric JSON values must fail closed.
                entry = parse_rest_value_object(bars[-1]["close"])
                stop = entry-step*10
                lot = int(Decimal(binding["trade_lot_size"]))
                equity = parse_rest_decimal_value_object(account.get("equity"), positive=True)
                r15 = size_position(equity, entry, stop, ContractEconomics(step, tick, lot, True))
                sizing[code] = {"entry": entry, "stop": stop, "price_step": step,
                                "tick_value": tick, "trade_lot_size": lot, "r15_quantity": r15.quantity}
            except (KeyError, TypeError, ValueError):
                # ``evaluate`` owns the sanitized equity classification.
                pass
    return finish(account=account, orders=orders, details=details, registry=registry,
                  params=params, sizing=sizing, timestamp=now.isoformat())


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
