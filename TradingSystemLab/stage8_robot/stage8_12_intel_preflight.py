"""Stage 8.12.3 Intel production preflight.

REAL ACCOUNT / ZERO ORDERS / STILL NOT AUTHORIZED.

This module performs only session/read operations against FINAM.  It validates
the already-frozen Stage 7 production authority, current account/heartbeat
state, N4 bindings, current directional margins, and the Stage 8.12
simultaneous-capacity funding benchmark.  It never arms the kill switch,
initializes production execution state, or exposes an order endpoint.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import sqlite3
import subprocess
import tempfile
from datetime import datetime, timedelta, timezone
from decimal import Decimal
from pathlib import Path
from typing import Any

import pandas as pd

from TradingSystemLab.core.indicators import atr

from .account_cleanliness import count_active_orders, count_nonzero_positions
from .finam_api import FinamAPI, completed_h1_bars
from .funding_margin_diagnostic import ACTIVE_ACCOUNT_STATUSES, load_production_registry
from .instrument_resolver import (
    MOEX_REFERENCE,
    N4,
    discover_finam_asset,
    parse_rest_value_object,
    validate_finam_binding,
)
from .margin import (
    directional_initial_margin,
    parse_rest_decimal_value_object,
    portfolio_authority,
)
from .n4_capacity import N4CapacityInput, simultaneous_positive_capacity
from .operations import InstanceLock
from .production_runtime import MODE as PRODUCTION_RUNTIME_MODE, RUNTIME_SCHEMA
from .readonly_supervisor import newest_expected_h1_close, trading_h1_windows
from .specification import (
    ACTIVE_IDENTITY,
    PRODUCTION_SPECIFICATION_ID,
    load_frozen_specification,
)
from .state import (
    TERMINAL_INTENT_STATUSES,
    readonly_unresolved_intent_count,
    stage8_11_acceptance_path,
    stage8_11_identity,
)
from .trading_safety_gate import evaluate_new_entry_gate, heartbeat_path

SCHEMA_ID = "stage8_12_3_intel_preflight.v1"
MODE = "STAGE8_12_3_PREFLIGHT_ONLY"
REPORT_NAME = "stage8_12_3_intel_preflight.json"
REPOSITORY_ROOT = Path(__file__).resolve().parents[2]
EXPECTED_GATE_REASONS = ["KILL_SWITCH_HALTED", "EXECUTION_NOT_AUTHORIZED"]
RESERVE_SCENARIOS = (Decimal("0"), Decimal("0.10"), Decimal("0.20"), Decimal("0.30"))
PRODUCTION_STATE_FILENAME = "stage8-12-production.sqlite3"
SUPERVISOR_STATE_FILENAME = "readonly-supervisor.sqlite3"
STOP_ATR_MULTIPLE = Decimal("2.5")
# Frozen Stage 7 T3 source (T3_MTF_Trend.py) computes H1 ATR over the
# continuous H1 series: low["ATR"] = atr(low, p.atr_period).  This benchmark
# intentionally mirrors that cross-trading-day authority.  Resetting ATR at a
# day boundary here would change the frozen production strategy.
FROZEN_T3_H1_ATR_CROSSES_TRADING_DAYS = True
H1_HISTORY_LOOKBACK_DAYS = 30


class PreflightBlocked(RuntimeError):
    pass


class PreflightReadAPI:
    """Capability-limited FINAM facade: session + GET/read methods only."""

    def __init__(self, api: FinamAPI):
        self._api = api

    def create_session(self):
        return self._api.create_session()

    def session_details(self):
        return self._api.session_details()

    def account(self, account_id):
        return self._api.account(account_id)

    def orders(self, account_id):
        return self._api.orders(account_id)

    def assets_all_active(self):
        return self._api.assets_all_active()

    def asset(self, symbol, account_id):
        return self._api.asset(symbol, account_id)

    def asset_params(self, symbol, account_id):
        return self._api.asset_params(symbol, account_id)

    def schedule(self, symbol):
        return self._api.schedule(symbol)

    def bars(self, symbol, start, end):
        return self._api.bars(symbol, start, end)


def _fail(code: str) -> None:
    raise PreflightBlocked(code)


def _external_report(path: Path) -> Path:
    resolved = path.expanduser().resolve()
    if (
        not path.is_absolute()
        or path.name != REPORT_NAME
        or resolved == REPOSITORY_ROOT
        or REPOSITORY_ROOT in resolved.parents
    ):
        _fail("STAGE8_12_3_REPORT_PATH_INVALID")
    return resolved


def _utc_timestamp(value: Any) -> datetime:
    if not isinstance(value, str):
        _fail("STAGE8_12_3_H1_TIMESTAMP_INVALID")
    try:
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError:
        _fail("STAGE8_12_3_H1_TIMESTAMP_INVALID")
    if parsed.tzinfo is None:
        _fail("STAGE8_12_3_H1_TIMESTAMP_INVALID")
    return parsed.astimezone(timezone.utc)


def _read_supervisor_watermarks(runtime_root: Path) -> dict[str, datetime]:
    path = (runtime_root / "state" / SUPERVISOR_STATE_FILENAME).resolve()
    if not path.is_file():
        _fail("STAGE8_12_3_SUPERVISOR_STATE_MISSING")
    connection = sqlite3.connect(path.as_uri() + "?mode=ro", uri=True)
    try:
        tables = {row[0] for row in connection.execute(
            "SELECT name FROM sqlite_master WHERE type='table'"
        )}
        if tables != {"operational_state"}:
            _fail("STAGE8_12_3_SUPERVISOR_STATE_SCHEMA_INVALID")
        rows = dict(connection.execute("SELECT key,value FROM operational_state"))
    finally:
        connection.close()
    if rows.get("last_reconciliation") != "PASS":
        _fail("STAGE8_12_3_RECONCILIATION_NOT_PASS")
    result: dict[str, datetime] = {}
    for instrument in N4:
        value = rows.get(f"h1:{instrument}")
        if value is None:
            _fail("STAGE8_12_3_H1_WATERMARK_MISSING")
        result[instrument] = _utc_timestamp(value)
    return result


def _stage8_11_unresolved_for_account(runtime_root: Path, account_id: str) -> int:
    acceptance_path = stage8_11_acceptance_path(runtime_root)
    if not acceptance_path.is_file():
        _fail("STAGE8_12_3_STAGE8_11_LEDGER_MISSING")
    try:
        connection = sqlite3.connect(
            acceptance_path.resolve().as_uri() + "?mode=ro", uri=True
        )
        try:
            identity_row = connection.execute(
                "SELECT value FROM state WHERE key='database_identity'"
            ).fetchone()
        finally:
            connection.close()
        if identity_row is None:
            _fail("STAGE8_12_3_STAGE8_11_LEDGER_IDENTITY_INVALID")
        try:
            historical_identity = json.loads(identity_row[0])
        except (TypeError, json.JSONDecodeError):
            _fail("STAGE8_12_3_STAGE8_11_LEDGER_IDENTITY_INVALID")
        if historical_identity != stage8_11_identity(account_id):
            _fail("STAGE8_12_3_STAGE8_11_LEDGER_ACCOUNT_MISMATCH")
        unresolved = readonly_unresolved_intent_count(acceptance_path)
    except PreflightBlocked:
        raise
    except Exception:
        _fail("STAGE8_12_3_STAGE8_11_LEDGER_INVALID")
    if unresolved != 0:
        _fail("STAGE8_12_3_STAGE8_11_UNRESOLVED_INTENTS")
    return unresolved


def _require_current_h1_watermark(
    stored: datetime, schedule: Any, observed_now: datetime
) -> None:
    expected_now = newest_expected_h1_close(schedule, observed_now)
    if expected_now is not None and stored != expected_now:
        _fail("STAGE8_12_3_H1_WATERMARK_STALE")


def _require_safety_state(
    runtime_root: Path, observed_now: datetime, account_hash: str
) -> dict[str, Any]:
    gate = evaluate_new_entry_gate(
        runtime_root=runtime_root,
        now=observed_now,
        execution_authorized=False,
    )
    if gate.get("reason_codes") != EXPECTED_GATE_REASONS:
        _fail("STAGE8_12_3_SAFETY_OR_HEALTH_GATE_INVALID")
    try:
        heartbeat = json.loads(
            heartbeat_path(runtime_root).read_text(encoding="utf-8")
        )
    except (OSError, UnicodeError, json.JSONDecodeError):
        _fail("STAGE8_12_3_SAFETY_OR_HEALTH_GATE_INVALID")
    if heartbeat.get("account_hash") != account_hash:
        _fail("STAGE8_12_3_ACCOUNT_MISMATCH")
    if (
        gate.get("kill_switch_state") != "HALTED"
        or gate.get("execution_authorized") is not False
        or gate.get("reconciliation_status") != "PASS"
        or gate.get("heartbeat_fresh") is not True
        or gate.get("api_contact_fresh") is not True
    ):
        _fail("STAGE8_12_3_SAFETY_OR_HEALTH_GATE_INVALID")
    return gate


def _read_production_state(runtime_root: Path, broker_equity: Decimal) -> dict[str, Any]:
    path = (runtime_root / "state" / PRODUCTION_STATE_FILENAME).resolve()
    if not path.exists():
        return {
            "status": "ABSENT_CLEAN_NOT_INITIALIZED",
            "unresolved_production_intents": 0,
            "local_open_position_count": 0,
            "persisted_realized_equity": None,
        }
    if not path.is_file():
        _fail("STAGE8_12_3_PRODUCTION_STATE_INVALID")
    connection = sqlite3.connect(path.as_uri() + "?mode=ro", uri=True)
    try:
        tables = {row[0] for row in connection.execute(
            "SELECT name FROM sqlite_master WHERE type='table'"
        )}
        if tables != {"state", "intents", "fills"}:
            _fail("STAGE8_12_3_PRODUCTION_STATE_SCHEMA_INVALID")
        state_rows = dict(connection.execute("SELECT key,value FROM state"))
        identity_raw = state_rows.get("database_identity")
        if identity_raw is None:
            _fail("STAGE8_12_3_PRODUCTION_STATE_IDENTITY_MISSING")
        try:
            identity = json.loads(identity_raw)
        except json.JSONDecodeError:
            _fail("STAGE8_12_3_PRODUCTION_STATE_IDENTITY_INVALID")
        expected_identity = {
            "schema_id": RUNTIME_SCHEMA,
            "production_specification_id": PRODUCTION_SPECIFICATION_ID,
            "active_identity": ACTIVE_IDENTITY,
            "mode": PRODUCTION_RUNTIME_MODE,
        }
        if identity != expected_identity:
            _fail("STAGE8_12_3_PRODUCTION_STATE_IDENTITY_MISMATCH")
        marks = ",".join("?" for _ in TERMINAL_INTENT_STATUSES)
        unresolved = connection.execute(
            f"SELECT COUNT(*) FROM intents WHERE COALESCE(status, '') NOT IN ({marks})",
            TERMINAL_INTENT_STATUSES,
        ).fetchone()[0]
        positions_raw = state_rows.get("production_positions")
        try:
            positions = {} if positions_raw is None else json.loads(positions_raw)
        except json.JSONDecodeError:
            _fail("STAGE8_12_3_PRODUCTION_POSITION_STATE_INVALID")
        if not isinstance(positions, dict):
            _fail("STAGE8_12_3_PRODUCTION_POSITION_STATE_INVALID")
        realized_raw = state_rows.get("realized_equity")
        realized = None
        if realized_raw is not None:
            try:
                realized = Decimal(str(json.loads(realized_raw)))
            except Exception:
                _fail("STAGE8_12_3_PRODUCTION_REALIZED_EQUITY_INVALID")
            if not realized.is_finite() or realized <= 0:
                _fail("STAGE8_12_3_PRODUCTION_REALIZED_EQUITY_INVALID")
    finally:
        connection.close()
    if unresolved != 0:
        _fail("STAGE8_12_3_UNRESOLVED_PRODUCTION_INTENTS")
    if positions:
        _fail("STAGE8_12_3_LOCAL_PRODUCTION_POSITION_PRESENT")
    if realized is not None and realized != broker_equity:
        _fail("STAGE8_12_3_REALIZED_EQUITY_MISMATCH")
    return {
        "status": "PRESENT_CLEAN",
        "unresolved_production_intents": unresolved,
        "local_open_position_count": 0,
        "persisted_realized_equity": None if realized is None else str(realized),
    }


def _frozen_registry_row_valid(row: dict[str, str], instrument: str) -> bool:
    step, tick, size = MOEX_REFERENCE[instrument]
    try:
        return (
            row.get("research_symbol") == instrument
            and row.get("finam_symbol") == f"{instrument}@RTSX"
            and row.get("mic") == "RTSX"
            and bool(row.get("security_id"))
            and row.get("binding_status") == "AUTHENTICATED_REAL_READONLY"
            and row.get("trading_status") == "TRADABLE"
            and Decimal(row.get("price_step", "")) == step
            and Decimal(row.get("tick_value", "")) == tick
            and Decimal(row.get("contract_size", "")) == size
            and int(Decimal(row.get("quantity_granularity", ""))) == 1
        )
    except Exception:
        return False


def _strategy_loss_per_contract(
    instrument: str, atr_value: Decimal
) -> tuple[Decimal, Decimal, bool]:
    """Return the exact frozen-strategy benchmark without inventing stop rounding.

    Stage 7 deliberately blocks a live entry when the raw 2.5-ATR stop is not
    on the authenticated broker tick grid.  Stage 8.12.3 is a funding benchmark,
    not an entry attempt, so it retains the exact fractional strategy distance
    for loss-per-contract and reports live grid eligibility separately.
    """
    step, tick, _ = MOEX_REFERENCE[instrument]
    stop_distance = atr_value * STOP_ATR_MULTIPLE
    ticks = stop_distance / step
    grid_eligible = ticks == ticks.to_integral_value()
    loss_per_contract = ticks * tick
    if not loss_per_contract.is_finite() or loss_per_contract <= 0:
        _fail("STAGE8_12_3_LOSS_PER_CONTRACT_INVALID")
    return stop_distance, loss_per_contract, grid_eligible


def _expected_completed_h1_opens(
    windows: list[tuple[datetime, datetime]],
    observed_now: datetime,
    watermark: datetime,
) -> list[datetime]:
    """Return the exact schedule-derived completed H1 opens through watermark."""
    now_utc = observed_now.astimezone(timezone.utc)
    expected: list[datetime] = []
    for start, end in windows:
        candidate = start
        while candidate < end:
            completed_at = min(candidate + timedelta(hours=1), end)
            if candidate <= watermark and completed_at <= now_utc:
                expected.append(candidate)
            candidate += timedelta(hours=1)
    return expected


def _collect_strategy_loss(
    *,
    api: Any,
    instrument: str,
    symbol: str,
    watermark: datetime,
    params: dict,
    binding: dict,
    schedule: Any,
    now: datetime,
) -> tuple[N4CapacityInput, dict[str, Any]]:
    try:
        windows = trading_h1_windows(schedule)
    except RuntimeError:
        raise
    if not windows:
        _fail("STAGE8_12_3_H1_TRADING_WINDOW_UNAVAILABLE")

    # The FINAM schedule endpoint can expose only the current trading day.
    # Before that day's first session starts, windows[0][0] is in the future
    # while the canonical readonly supervisor watermark is correctly retained
    # from the previous completed session.  Fetch the same broad historical H1
    # window used by the readonly supervisor, then apply today's schedule only
    # to the schedule-covered portion of that history.
    now_utc = now.astimezone(timezone.utc)
    history_start = (now_utc - timedelta(days=H1_HISTORY_LOOKBACK_DAYS)).isoformat()
    response = api.bars(symbol, history_start, now_utc.isoformat())
    rows = response.get("bars") if isinstance(response, dict) else None
    if not isinstance(rows, list):
        _fail("STAGE8_12_3_H1_BARS_SCHEMA_INVALID")
    try:
        completed_current_schedule = completed_h1_bars(response, now_utc, windows)
    except (TypeError, ValueError):
        _fail("STAGE8_12_3_H1_BARS_SCHEMA_INVALID")

    history_by_timestamp: dict[datetime, dict[str, Any]] = {}
    for row in rows:
        if not isinstance(row, dict):
            _fail("STAGE8_12_3_H1_BARS_SCHEMA_INVALID")
        timestamp = _utc_timestamp(row.get("timestamp"))
        if timestamp <= watermark:
            if timestamp in history_by_timestamp:
                _fail("STAGE8_12_3_H1_DUPLICATE_BAR")
            history_by_timestamp[timestamp] = row

    if watermark not in history_by_timestamp:
        _fail("STAGE8_12_3_H1_WATERMARK_BAR_MISSING")

    expected_opens = _expected_completed_h1_opens(windows, now_utc, watermark)
    schedule_scope_start = windows[0][0].replace(
        hour=0, minute=0, second=0, microsecond=0
    )
    raw_schedule_scope = {
        timestamp
        for timestamp in history_by_timestamp
        if timestamp >= schedule_scope_start
    }
    completed_schedule_scope: dict[datetime, dict[str, Any]] = {}
    for row in completed_current_schedule:
        timestamp = _utc_timestamp(row.get("timestamp"))
        if timestamp <= watermark:
            if timestamp in completed_schedule_scope:
                _fail("STAGE8_12_3_H1_DUPLICATE_BAR")
            completed_schedule_scope[timestamp] = row

    if raw_schedule_scope != set(completed_schedule_scope):
        _fail("STAGE8_12_3_H1_BAR_OUTSIDE_VALIDATED_SCHEDULE")
    if expected_opens:
        if expected_opens[-1] != watermark:
            _fail("STAGE8_12_3_H1_EXPECTED_SEQUENCE_INVALID")
        if sorted(completed_schedule_scope) != expected_opens:
            _fail("STAGE8_12_3_H1_EXPECTED_SEQUENCE_GAP")
    elif watermark >= schedule_scope_start:
        _fail("STAGE8_12_3_H1_EXPECTED_SEQUENCE_INVALID")

    usable = []
    for timestamp in sorted(history_by_timestamp):
        row = history_by_timestamp[timestamp]
        try:
            open_price = float(parse_rest_value_object(row.get("open"), positive=True))
            high = float(parse_rest_value_object(row.get("high"), positive=True))
            low = float(parse_rest_value_object(row.get("low"), positive=True))
            close = float(parse_rest_value_object(row.get("close"), positive=True))
        except (TypeError, ValueError):
            _fail("STAGE8_12_3_H1_BARS_SCHEMA_INVALID")
        if low > high or low > min(open_price, close) or high < max(open_price, close):
            _fail("STAGE8_12_3_H1_OHLC_INVALID")
        usable.append((timestamp, open_price, high, low, close))
    if len(usable) < 14 or usable[-1][0] != watermark:
        _fail("STAGE8_12_3_H1_HISTORY_INSUFFICIENT")
    frame = pd.DataFrame(
        [(o, h, l, c) for _, o, h, l, c in usable],
        columns=["Open", "High", "Low", "Close"],
        index=pd.DatetimeIndex([timestamp for timestamp, *_ in usable]),
    )
    atr_value = atr(frame, 14).iloc[-1]
    if pd.isna(atr_value) or not float(atr_value) > 0:
        _fail("STAGE8_12_3_ATR_INVALID")
    step, tick, _ = MOEX_REFERENCE[instrument]
    benchmark_atr = Decimal(str(float(atr_value)))
    stop_distance, loss_per_contract, live_entry_grid_eligible = (
        _strategy_loss_per_contract(instrument, benchmark_atr)
    )
    try:
        trade_lot_size = int(Decimal(str(binding["trade_lot_size"])))
        long_margin = directional_initial_margin(params, "LONG")
        short_margin = directional_initial_margin(params, "SHORT")
    except (KeyError, TypeError, ValueError):
        _fail("STAGE8_12_3_DIRECTIONAL_MARGIN_INVALID")
    capacity = N4CapacityInput(
        loss_per_contract=loss_per_contract,
        trade_lot_size=trade_lot_size,
        long_initial_margin=long_margin,
        short_initial_margin=short_margin,
    )
    details = {
        "finam_symbol": symbol,
        "latest_completed_h1_open_utc": watermark.isoformat(),
        "benchmark_entry_close": str(Decimal(str(usable[-1][4]))),
        "atr14": str(benchmark_atr),
        "atr_day_boundary_semantics": "CROSS_DAY_AS_FROZEN_STAGE7_T3_SOURCE",
        "h1_history_lookback_days": H1_HISTORY_LOOKBACK_DAYS,
        "h1_current_schedule_scope_validation": "EXACT_WHEN_SCHEDULE_COVERS_WATERMARK_DAY",
        "initial_stop_atr_multiple": str(STOP_ATR_MULTIPLE),
        "strategy_stop_distance": str(stop_distance),
        "strategy_stop_ticks": str(stop_distance / step),
        "live_entry_grid_eligible": live_entry_grid_eligible,
        "live_entry_grid_policy": "BLOCK_ENTRY_NO_ROUNDING_PER_FROZEN_STAGE7",
        "price_step": str(step),
        "tick_value_rub": str(tick),
        "loss_per_contract": str(loss_per_contract),
        "trade_lot_size": trade_lot_size,
        "long_initial_margin": str(long_margin),
        "short_initial_margin": str(short_margin),
    }
    return capacity, details


def _capacity_report(
    inputs: dict[str, N4CapacityInput],
    *,
    realized_equity: Decimal,
    available_cash: Decimal,
) -> dict[str, Any]:
    plans = {
        str(reserve): simultaneous_positive_capacity(inputs, reserve_fraction=reserve)
        for reserve in RESERVE_SCENARIOS
    }
    base = plans[str(Decimal("0"))]
    r15_shortfall = max(Decimal("0"), base.r15_equity_floor - realized_equity)
    margin_shortfall = max(
        Decimal("0"), base.worst_direction_margin_floor - available_cash
    )
    additional = max(r15_shortfall, margin_shortfall)
    scenarios: dict[str, dict[str, Any]] = {}
    for reserve in RESERVE_SCENARIOS:
        plan = plans[str(reserve)]
        evidence = plan.evidence()
        multiplier = Decimal("1") + reserve
        required_equity = base.r15_equity_floor * multiplier
        required_margin_cash = base.worst_direction_margin_floor * multiplier
        scenario_equity_shortfall = max(
            Decimal("0"), required_equity - realized_equity
        )
        scenario_margin_shortfall = max(
            Decimal("0"), required_margin_cash - available_cash
        )
        scenario_additional = max(
            scenario_equity_shortfall, scenario_margin_shortfall
        )
        evidence.update({
            "required_equity_with_reserve": str(required_equity),
            "required_margin_cash_with_reserve": str(required_margin_cash),
            "r15_equity_shortfall": str(scenario_equity_shortfall),
            "margin_cash_shortfall": str(scenario_margin_shortfall),
            "additional_funding_required": str(scenario_additional),
        })
        scenarios[f"{int(reserve * 100)}pct"] = evidence
    return {
        "r15_equity_floor": str(base.r15_equity_floor),
        "all_long_margin_floor": str(base.long_margin_floor),
        "all_short_margin_floor": str(base.short_margin_floor),
        "worst_direction_margin_floor": str(base.worst_direction_margin_floor),
        "base_required_capital": str(base.base_required_capital),
        "current_realized_equity": str(realized_equity),
        "current_available_cash": str(available_cash),
        "r15_equity_shortfall": str(r15_shortfall),
        "worst_direction_margin_shortfall": str(margin_shortfall),
        "additional_funding_required": str(additional),
        "reserve_scenarios": scenarios,
    }


def _require_broker_clean_snapshot(api: Any, account_id: str) -> dict[str, Any]:
    account = api.account(account_id)
    if (
        not isinstance(account, dict)
        or account.get("status") not in ACTIVE_ACCOUNT_STATUSES
    ):
        _fail("STAGE8_12_3_ACCOUNT_SCHEMA_OR_STATUS_INVALID")
    orders = api.orders(account_id)
    order_rows = orders.get("orders") if isinstance(orders, dict) else orders
    positions = account.get("positions")
    if not isinstance(positions, list) or not isinstance(order_rows, list):
        _fail("STAGE8_12_3_ACCOUNT_SCHEMA_OR_STATUS_INVALID")
    try:
        nonzero_positions = count_nonzero_positions(positions)
        active_orders = count_active_orders(order_rows)
    except ValueError:
        _fail("STAGE8_12_3_ACCOUNT_SCHEMA_OR_STATUS_INVALID")
    if nonzero_positions != 0:
        _fail("STAGE8_12_3_BROKER_POSITION_PRESENT")
    if active_orders != 0:
        _fail("STAGE8_12_3_ACTIVE_BROKER_ORDER_PRESENT")
    return account


def preflight_only(
    *,
    api: Any,
    account_id: str,
    runtime_root: Path,
    accepted_commit: str,
    now: datetime | None = None,
) -> dict[str, Any]:
    observed_now = now or datetime.now(timezone.utc)
    if observed_now.tzinfo is None or observed_now.utcoffset() is None:
        _fail("STAGE8_12_3_TIMESTAMP_INVALID")
    spec = load_frozen_specification()
    if (
        spec.production_id != PRODUCTION_SPECIFICATION_ID
        or spec.identity != ACTIVE_IDENTITY
        or tuple(spec.instruments) != tuple(N4)
    ):
        _fail("STAGE8_12_3_FROZEN_AUTHORITY_INVALID")

    account_hash = hashlib.sha256(account_id.encode("utf-8")).hexdigest()
    gate = _require_safety_state(runtime_root, observed_now, account_hash)

    historical_unresolved = _stage8_11_unresolved_for_account(
        runtime_root, account_id
    )

    watermarks = _read_supervisor_watermarks(runtime_root)

    api.create_session()
    details = api.session_details()
    if not isinstance(details, dict) or details.get("readonly") is not False:
        _fail("STAGE8_12_3_TRADING_TOKEN_NOT_WRITE_CAPABLE")
    account_ids = details.get("account_ids")
    if (
        not isinstance(account_ids, list)
        or [str(value) for value in account_ids].count(str(account_id)) != 1
    ):
        _fail("STAGE8_12_3_ACCOUNT_NOT_EXACTLY_ENUMERATED")

    account = _require_broker_clean_snapshot(api, account_id)

    try:
        financial = portfolio_authority(account)
        realized_equity = parse_rest_decimal_value_object(
            account.get("equity"), positive=True
        )
    except ValueError:
        _fail("STAGE8_12_3_FINANCIAL_AUTHORITY_INVALID")
    if financial.available_cash < 0:
        _fail("STAGE8_12_3_FINANCIAL_AUTHORITY_INVALID")

    production_state = _read_production_state(runtime_root, realized_equity)

    production_registry = load_production_registry()
    if set(production_registry) != set(N4) or not all(
        _frozen_registry_row_valid(production_registry[instrument], instrument)
        for instrument in N4
    ):
        _fail("STAGE8_12_3_FROZEN_REGISTRY_INVALID")

    assets = api.assets_all_active()
    if not isinstance(assets, list):
        _fail("STAGE8_12_3_ACTIVE_ASSET_CATALOG_INVALID")
    capacity_inputs: dict[str, N4CapacityInput] = {}
    per_instrument: dict[str, dict[str, Any]] = {}
    for instrument in N4:
        asset, reason = discover_finam_asset(instrument, assets)
        if reason or not isinstance(asset, dict):
            _fail("STAGE8_12_3_N4_BINDING_INVALID")
        symbol = asset.get("symbol")
        if not isinstance(symbol, str):
            _fail("STAGE8_12_3_N4_BINDING_INVALID")
        params = api.asset_params(symbol, account_id)
        schedule = api.schedule(symbol)
        _require_current_h1_watermark(
            watermarks[instrument], schedule, observed_now
        )
        binding = validate_finam_binding(
            instrument,
            asset,
            params,
            schedule,
            api.asset(symbol, account_id),
        ).to_dict()
        frozen = production_registry[instrument]
        if (
            not str(binding.get("status", "")).startswith("AUTHENTICATED_")
            or binding.get("is_tradable") is not True
            or binding.get("finam_symbol") != frozen["finam_symbol"]
            or binding.get("mic") != frozen["mic"]
            or str(binding.get("security_id")) != frozen["security_id"]
            or str(binding.get("trade_lot_size")) != frozen["quantity_granularity"]
        ):
            _fail("STAGE8_12_3_N4_BINDING_INVALID")
        capacity, evidence = _collect_strategy_loss(
            api=api,
            instrument=instrument,
            symbol=symbol,
            watermark=watermarks[instrument],
            params=params,
            binding=binding,
            schedule=schedule,
            now=observed_now,
        )
        capacity_inputs[instrument] = capacity
        per_instrument[instrument] = evidence

    capacity_report = _capacity_report(
        capacity_inputs,
        realized_equity=realized_equity,
        available_cash=financial.available_cash,
    )

    final_now = observed_now if now is not None else datetime.now(timezone.utc)
    _require_safety_state(runtime_root, final_now, account_hash)
    _require_broker_clean_snapshot(api, account_id)

    return {
        "schema_id": SCHEMA_ID,
        "mode": MODE,
        "status": "PASS",
        "accepted_code_commit": accepted_commit,
        "production_specification_id": PRODUCTION_SPECIFICATION_ID,
        "active_identity": ACTIVE_IDENTITY,
        "sanitized_account_hash": account_hash,
        "dpapi_trading_credential_authority": "PASS",
        "trading_session_write_capable": "PASS",
        "account_binding": "PASS",
        "account_schema": "PASS",
        "broker_account_clean": "PASS",
        "broker_nonzero_position_count": 0,
        "active_broker_order_count": 0,
        "historical_stage8_11_unresolved_intents": 0,
        "production_state": production_state,
        "unresolved_production_intents": production_state["unresolved_production_intents"],
        "reconciliation": "PASS",
        "heartbeat_fresh": True,
        "finam_contact_fresh": True,
        "frozen_n4_registry": "PASS",
        "n4_tradable": "PASS",
        "portfolio_variant": financial.variant,
        "current_realized_equity": str(realized_equity),
        "current_available_cash": str(financial.available_cash),
        "money_reserved": (
            None if financial.money_reserved is None else str(financial.money_reserved)
        ),
        "per_instrument": per_instrument,
        "n4_simultaneous_positive_capacity": capacity_report,
        "kill_switch_observed": "HALTED",
        "production_scheduled_task": "DisabledOrAbsent",
        "execution_authorized": False,
        "live_trading_authorized": False,
        "real_order_transmission_authorized": False,
        "order_endpoint_call_count": 0,
        "real_order_count": 0,
        "stage8_12_3_result": "STAGE_8_12_3_INTEL_PRODUCTION_PREFLIGHT_PASS",
        "stage8_12_4_status": "NOT_STARTED_NOT_AUTHORIZED",
    }


def write_report(report: dict[str, Any], output: Path) -> None:
    destination = _external_report(output)
    destination.parent.mkdir(parents=True, exist_ok=True)
    descriptor, temporary = tempfile.mkstemp(
        dir=destination.parent,
        prefix=destination.name + ".",
        suffix=".tmp",
    )
    temp = Path(temporary)
    try:
        with os.fdopen(descriptor, "w", encoding="utf-8", newline="\n") as stream:
            json.dump(report, stream, indent=2, sort_keys=True)
            stream.write("\n")
            stream.flush()
            os.fsync(stream.fileno())
        os.replace(temp, destination)
    finally:
        temp.unlink(missing_ok=True)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--runtime-root", type=Path, required=True)
    parser.add_argument("--report", type=Path, required=True)
    parser.add_argument("--accepted-commit", required=True)
    args = parser.parse_args(argv)
    try:
        root = args.runtime_root.resolve()
        if (
            subprocess.run(
                ["git", "diff", "--quiet"], cwd=REPOSITORY_ROOT
            ).returncode
            or subprocess.run(
                ["git", "diff", "--cached", "--quiet"], cwd=REPOSITORY_ROOT
            ).returncode
        ):
            _fail("STAGE8_12_3_WORKTREE_NOT_CLEAN")
        commit = subprocess.check_output(
            ["git", "rev-parse", "HEAD"],
            cwd=REPOSITORY_ROOT,
            text=True,
        ).strip()
        if len(args.accepted_commit) != 40 or commit != args.accepted_commit:
            _fail("STAGE8_12_3_ACCEPTED_COMMIT_MISMATCH")
        if os.environ.get("STAGE8_12_3_DPAPI_VALIDATED") != "true":
            _fail("STAGE8_12_3_DPAPI_AUTHORITY_INVALID")
        if os.environ.get("STAGE8_12_3_PRODUCTION_TASK_SAFE") != "true":
            _fail("STAGE8_12_3_PRODUCTION_TASK_NOT_DISABLED")
        secret = os.environ.get("STAGE8_12_3_TRADING_SECRET", "")
        account = os.environ.get("STAGE8_12_3_ACCOUNT_ID", "")
        if not secret or not account:
            _fail("STAGE8_12_3_DPAPI_AUTHORITY_INVALID")
        with InstanceLock(root / "locks" / "stage8-12-3-intel-preflight.lock"):
            result = preflight_only(
                api=PreflightReadAPI(FinamAPI(secret)),
                account_id=account,
                runtime_root=root,
                accepted_commit=args.accepted_commit,
            )
            write_report(result, args.report)
    except (
        PreflightBlocked,
        OSError,
        RuntimeError,
        ValueError,
        json.JSONDecodeError,
        sqlite3.Error,
    ) as exc:
        print(str(exc) if isinstance(exc, PreflightBlocked) else "STAGE8_12_3_PREFLIGHT_FAILED")
        return 1
    finally:
        for key in (
            "STAGE8_12_3_TRADING_SECRET",
            "STAGE8_12_3_ACCOUNT_ID",
            "STAGE8_12_3_DPAPI_VALIDATED",
            "STAGE8_12_3_PRODUCTION_TASK_SAFE",
        ):
            os.environ.pop(key, None)
    print("STAGE8_12_3_INTEL_PRODUCTION_PREFLIGHT_PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
