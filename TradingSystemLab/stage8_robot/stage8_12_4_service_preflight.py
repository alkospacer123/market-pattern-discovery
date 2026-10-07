"""Stage 8.12.4 production-service physical preflight.

This preflight proves the exact production data path on the Intel host while
remaining structurally unable to transmit, cancel, or modify any broker order.
It validates the pinned Stage 5 H1 warm-up authority, exact overlap with the
current FINAM 30-day H1 tail, schedule freshness, and frozen T3 indicator
readiness for all N4 instruments.

No production authorization is created, the kill switch must remain HALTED,
and all rolling-cache writes are isolated in a temporary diagnostics directory.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import sqlite3
import tempfile
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any

import pandas as pd

from .account_cleanliness import count_active_orders, count_nonzero_positions
from .context_builder import T3ContextBuilder
from .finam_api import FinamAPI
from .funding_margin_diagnostic import ACTIVE_ACCOUNT_STATUSES, load_production_registry
from .instrument_resolver import N4, discover_finam_asset, validate_finam_binding
from .production_authorization import authorization_path
from .production_history import (
    SEED_FILES,
    SEED_SHA256,
    STAGE5_DATA_COMMIT,
    ProductionHistoryError,
    update_production_h1,
)
from .readonly_supervisor import (
    SUPERVISOR_DATABASE,
    newest_expected_h1_close,
    trading_h1_windows,
)
from .specification import ACTIVE_IDENTITY, PRODUCTION_SPECIFICATION_ID, load_frozen_specification
from .stage8_12_intel_preflight import PreflightReadAPI
from .trading_safety_gate import load_kill_switch

SCHEMA_ID = "stage8_12_4_service_preflight.v1"
MODE = "STAGE8_12_4_SERVICE_PREFLIGHT_READ_ONLY"
H1_LOOKBACK_DAYS = 30
REPOSITORY_ROOT = Path(__file__).resolve().parents[2]


class ServicePreflightBlocked(RuntimeError):
    pass


def _fail(code: str) -> None:
    raise ServicePreflightBlocked(code)


def _external_report(path: Path) -> Path:
    destination = path.expanduser().resolve()
    if destination == REPOSITORY_ROOT or REPOSITORY_ROOT in destination.parents:
        _fail("STAGE8_12_4_SERVICE_REPORT_REPOSITORY_FORBIDDEN")
    destination.parent.mkdir(parents=True, exist_ok=True)
    return destination


def _utc(value: Any, code: str) -> datetime:
    if not isinstance(value, str):
        _fail(code)
    try:
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError:
        _fail(code)
    if parsed.tzinfo is None or parsed.utcoffset() is None:
        _fail(code)
    return parsed.astimezone(timezone.utc)


def _readonly_watermarks(runtime_root: Path) -> dict[str, datetime]:
    path = (runtime_root / "state" / SUPERVISOR_DATABASE).resolve()
    if not path.is_file() or path.is_symlink():
        _fail("STAGE8_12_4_READONLY_STATE_MISSING")
    try:
        connection = sqlite3.connect(path.as_uri() + "?mode=ro", uri=True)
        try:
            if connection.execute("PRAGMA integrity_check").fetchone() != ("ok",):
                _fail("STAGE8_12_4_READONLY_STATE_INVALID")
            tables = {
                row[0] for row in connection.execute(
                    "SELECT name FROM sqlite_master WHERE type='table'"
                )
            }
            if tables != {"operational_state"}:
                _fail("STAGE8_12_4_READONLY_STATE_INVALID")
            rows = dict(connection.execute(
                "SELECT key,value FROM operational_state"
            ))
        finally:
            connection.close()
    except sqlite3.Error:
        _fail("STAGE8_12_4_READONLY_STATE_INVALID")
    if rows.get("last_reconciliation") != "PASS":
        _fail("STAGE8_12_4_READONLY_RECONCILIATION_NOT_PASS")
    result: dict[str, datetime] = {}
    for instrument in N4:
        text = rows.get(f"expected_h1:{instrument}") or rows.get(f"h1:{instrument}")
        if text is None:
            _fail("STAGE8_12_4_READONLY_WATERMARK_MISSING")
        result[instrument] = _utc(
            text, "STAGE8_12_4_READONLY_WATERMARK_INVALID"
        )
    return result


def _frozen_registry_valid(registry: dict[str, dict[str, str]]) -> bool:
    if set(registry) != set(N4):
        return False
    for instrument in N4:
        row = registry.get(instrument)
        if (
            not isinstance(row, dict)
            or row.get("research_symbol") != instrument
            or row.get("finam_symbol") != f"{instrument}@RTSX"
            or row.get("mic") != "RTSX"
            or not row.get("security_id")
            or row.get("binding_status") != "AUTHENTICATED_REAL_READONLY"
            or row.get("trading_status") != "TRADABLE"
        ):
            return False
    return True


def _require_inactive(runtime_root: Path) -> None:
    try:
        if authorization_path(runtime_root).exists():
            _fail("STAGE8_12_4_AUTHORIZATION_MUST_BE_ABSENT")
        switch, error = load_kill_switch(runtime_root)
    except ServicePreflightBlocked:
        raise
    except Exception:
        _fail("STAGE8_12_4_KILL_SWITCH_INVALID")
    if error is not None or not isinstance(switch, dict):
        _fail("STAGE8_12_4_KILL_SWITCH_INVALID")
    if (
        switch.get("production_specification_id") != PRODUCTION_SPECIFICATION_ID
        or switch.get("state") != "HALTED"
    ):
        _fail("STAGE8_12_4_KILL_SWITCH_NOT_HALTED")


def _context_evidence(history: pd.DataFrame, now: datetime) -> dict[str, Any]:
    try:
        execution, context = T3ContextBuilder().build(history, now)
    except Exception:
        _fail("STAGE8_12_4_T3_CONTEXT_BUILD_FAILED")
    if execution.empty or context.empty:
        _fail("STAGE8_12_4_T3_CONTEXT_NOT_READY")
    required_execution = ("ATR", "PriorHigh", "PriorLow")
    required_context = (
        "EMA100", "EMA50", "EMA200", "EMA100Slope", "ADX", "ATR", "ATRMean20"
    )
    latest_execution = execution.iloc[-1]
    eligible = context.loc[context.index <= execution.index[-1]]
    if eligible.empty:
        _fail("STAGE8_12_4_T3_CONTEXT_NOT_READY")
    latest_context = eligible.iloc[-1]
    if any(pd.isna(latest_execution[name]) for name in required_execution):
        _fail("STAGE8_12_4_T3_EXECUTION_INDICATORS_NOT_READY")
    if any(pd.isna(latest_context[name]) for name in required_context):
        _fail("STAGE8_12_4_T3_CONTEXT_INDICATORS_NOT_READY")
    return {
        "closed_h1_rows": int(len(history)),
        "latest_h1_close_moscow": execution.index[-1].isoformat(),
        "latest_context_close_moscow": eligible.index[-1].isoformat(),
        "execution_indicators_ready": True,
        "context_indicators_ready": True,
    }


def preflight(
    *,
    api: PreflightReadAPI,
    account_id: str,
    runtime_root: Path,
    data_root: Path,
    accepted_commit: str,
    now: datetime | None = None,
) -> dict[str, Any]:
    observed = (now or datetime.now(timezone.utc)).astimezone(timezone.utc)
    if not account_id:
        _fail("STAGE8_12_4_ACCOUNT_REQUIRED")
    if any(hasattr(api, name) for name in (
        "place_order", "place_sltp_order", "cancel_order", "submit_order"
    )):
        _fail("STAGE8_12_4_PREFLIGHT_ORDER_CAPABILITY_EXPOSED")

    spec = load_frozen_specification()
    if (
        spec.production_id != PRODUCTION_SPECIFICATION_ID
        or spec.identity != ACTIVE_IDENTITY
        or tuple(spec.instruments) != tuple(N4)
    ):
        _fail("STAGE8_12_4_FROZEN_AUTHORITY_INVALID")
    _require_inactive(runtime_root)

    watermarks = _readonly_watermarks(runtime_root)
    registry = load_production_registry()
    if not _frozen_registry_valid(registry):
        _fail("STAGE8_12_4_FROZEN_REGISTRY_INVALID")

    api.create_session()
    details = api.session_details()
    if (
        not isinstance(details, dict)
        or details.get("readonly") is not False
        or not isinstance(details.get("account_ids"), list)
        or [str(value) for value in details["account_ids"]].count(str(account_id)) != 1
    ):
        _fail("STAGE8_12_4_TRADING_SESSION_AUTHORITY_INVALID")
    account = api.account(account_id)
    if (
        not isinstance(account, dict)
        or account.get("status") not in ACTIVE_ACCOUNT_STATUSES
        or not isinstance(account.get("positions"), list)
    ):
        _fail("STAGE8_12_4_ACCOUNT_AUTHORITY_INVALID")
    orders_response = api.orders(account_id)
    order_rows = (
        orders_response.get("orders")
        if isinstance(orders_response, dict)
        else orders_response
    )
    try:
        if count_nonzero_positions(account["positions"]) != 0:
            _fail("STAGE8_12_4_PREFLIGHT_ACCOUNT_NOT_FLAT")
        if count_active_orders(order_rows) != 0:
            _fail("STAGE8_12_4_PREFLIGHT_ACTIVE_ORDER_PRESENT")
    except ValueError:
        _fail("STAGE8_12_4_ACCOUNT_AUTHORITY_INVALID")

    assets = api.assets_all_active()
    if not isinstance(assets, list):
        _fail("STAGE8_12_4_ACTIVE_ASSET_CATALOG_INVALID")

    per_instrument: dict[str, dict[str, Any]] = {}
    diagnostics_root = runtime_root / "diagnostics"
    diagnostics_root.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(
        prefix="stage8-12-4-service-preflight-", dir=diagnostics_root
    ) as temporary:
        isolated_root = Path(temporary)
        start = (observed - timedelta(days=H1_LOOKBACK_DAYS)).isoformat()
        for instrument in N4:
            frozen = registry[instrument]
            asset, reason = discover_finam_asset(instrument, assets)
            if reason or not isinstance(asset, dict):
                _fail("STAGE8_12_4_N4_BINDING_INVALID")
            symbol = asset.get("symbol")
            if not isinstance(symbol, str):
                _fail("STAGE8_12_4_N4_BINDING_INVALID")
            params = api.asset_params(symbol, account_id)
            schedule = api.schedule(symbol)
            try:
                binding = validate_finam_binding(
                    instrument,
                    asset,
                    params,
                    schedule,
                    api.asset(symbol, account_id),
                ).to_dict()
                windows = trading_h1_windows(schedule)
            except Exception:
                _fail("STAGE8_12_4_N4_BINDING_INVALID")
            if (
                not str(binding.get("status", "")).startswith("AUTHENTICATED_")
                or binding.get("is_tradable") is not True
                or binding.get("finam_symbol") != frozen["finam_symbol"]
                or binding.get("mic") != frozen["mic"]
                or str(binding.get("security_id")) != frozen["security_id"]
                or str(binding.get("trade_lot_size"))
                != frozen["quantity_granularity"]
            ):
                _fail("STAGE8_12_4_N4_BINDING_INVALID")

            derived = newest_expected_h1_close(schedule, observed)
            prior = watermarks[instrument]
            expected = (
                max(derived, prior)
                if derived is not None and prior is not None
                else derived or prior
            )
            if expected is None:
                _fail("STAGE8_12_4_H1_EXPECTED_WATERMARK_UNAVAILABLE")
            response = api.bars(symbol, start, observed.isoformat())
            try:
                history = update_production_h1(
                    runtime_root=isolated_root,
                    data_root=data_root,
                    instrument=instrument,
                    finam_response=response,
                    observed_at=observed,
                    trading_windows=windows,
                    expected_open_utc=expected,
                )
            except ProductionHistoryError as exc:
                _fail(str(exc))
            evidence = _context_evidence(history, observed)
            evidence.update({
                "finam_symbol": symbol,
                "expected_h1_open_utc": expected.isoformat(),
                "seed_file": SEED_FILES[instrument],
                "seed_sha256": SEED_SHA256[instrument],
                "binding": "PASS",
                "h1_seed_finam_overlap": "PASS",
            })
            per_instrument[instrument] = evidence

    return {
        "schema_id": SCHEMA_ID,
        "mode": MODE,
        "status": "PASS",
        "accepted_code_commit": accepted_commit,
        "production_specification_id": PRODUCTION_SPECIFICATION_ID,
        "active_identity": ACTIVE_IDENTITY,
        "sanitized_account_hash": hashlib.sha256(
            account_id.encode("utf-8")
        ).hexdigest(),
        "stage5_data_commit": STAGE5_DATA_COMMIT,
        "n4": list(N4),
        "per_instrument": per_instrument,
        "durable_authorization_created": False,
        "execution_authorized": False,
        "kill_switch": "HALTED",
        "order_capable_methods_exposed": False,
        "order_endpoint_call_count": 0,
        "real_order_count": 0,
        "stage8_12_4_status": "IMPLEMENTATION_VALIDATION_NOT_AUTHORIZED",
        "observed_utc": observed.isoformat(),
    }


def write_report(report: dict[str, Any], output: Path) -> Path:
    destination = _external_report(output)
    temporary = destination.with_suffix(destination.suffix + ".tmp")
    temporary.write_text(
        json.dumps(report, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    os.replace(temporary, destination)
    return destination


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Stage 8.12.4 order-incapable production-service preflight"
    )
    parser.add_argument("--runtime-root", type=Path, required=True)
    parser.add_argument("--data-root", type=Path, required=True)
    parser.add_argument("--accepted-commit", required=True)
    parser.add_argument("--account-id", required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args(argv)
    secret = os.environ.get("FINAM_API_SECRET", "")
    if not secret:
        print("STAGE8_12_4_FINAM_API_SECRET_MISSING")
        return 1
    try:
        report = preflight(
            api=PreflightReadAPI(FinamAPI(secret)),
            account_id=args.account_id,
            runtime_root=args.runtime_root,
            data_root=args.data_root,
            accepted_commit=args.accepted_commit,
        )
        write_report(report, args.output)
    except (ServicePreflightBlocked, RuntimeError, ValueError) as exc:
        print(str(exc))
        return 1
    print("STAGE8_12_4_SERVICE_PREFLIGHT_PASS=true")
    print(f"STAGE8_12_4_ACCEPTED_COMMIT={args.accepted_commit}")
    print(f"STAGE8_12_4_STAGE5_DATA_COMMIT={STAGE5_DATA_COMMIT}")
    print("STAGE8_12_4_ORDER_ENDPOINT_CALL_COUNT=0")
    print("STAGE8_12_4_REAL_ORDER_COUNT=0")
    print("STAGE8_12_4_EXECUTION_AUTHORIZED=false")
    print("STAGE8_12_4_KILL_SWITCH=HALTED")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
