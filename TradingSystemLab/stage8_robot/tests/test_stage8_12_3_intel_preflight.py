from __future__ import annotations

import ast
import json
import sqlite3
from datetime import datetime, timezone
from decimal import Decimal
from pathlib import Path

import pytest

from TradingSystemLab.stage8_robot.n4_capacity import N4CapacityInput
from TradingSystemLab.stage8_robot.production_runtime import MODE as RUNTIME_MODE, RUNTIME_SCHEMA
from TradingSystemLab.stage8_robot.specification import ACTIVE_IDENTITY, PRODUCTION_SPECIFICATION_ID
from TradingSystemLab.stage8_robot.stage8_12_intel_preflight import (
    FROZEN_T3_H1_ATR_CROSSES_TRADING_DAYS,
    PRODUCTION_STATE_FILENAME,
    PreflightBlocked,
    _capacity_report,
    _collect_strategy_loss,
    _read_production_state,
    _require_broker_clean_snapshot,
    _require_current_h1_watermark,
    _stage8_11_unresolved_for_account,
    _strategy_loss_per_contract,
)
from TradingSystemLab.stage8_robot.state import (
    StateStore,
    initialize_stage8_11_acceptance_ledger,
)


def capacity_inputs():
    return {
        "USDRUBF": N4CapacityInput(Decimal("100"), 1, Decimal("1000"), Decimal("1500")),
        "CNYRUBF": N4CapacityInput(Decimal("200"), 1, Decimal("2000"), Decimal("1800")),
        "GLDRUBF": N4CapacityInput(Decimal("300"), 1, Decimal("3000"), Decimal("3500")),
        "IMOEXF": N4CapacityInput(Decimal("400"), 1, Decimal("4000"), Decimal("4500")),
    }


def test_stage8_12_3_capacity_report_uses_existing_frozen_calculator():
    report = _capacity_report(
        capacity_inputs(),
        realized_equity=Decimal("20000"),
        available_cash=Decimal("9000"),
    )
    assert report["r15_equity_floor"] == str(Decimal("400") / Decimal("0.015"))
    assert report["all_long_margin_floor"] == "10000"
    assert report["all_short_margin_floor"] == "11300"
    assert report["worst_direction_margin_floor"] == "11500"
    assert report["base_required_capital"] == str(Decimal("400") / Decimal("0.015"))
    assert report["r15_equity_shortfall"] == str(
        Decimal("400") / Decimal("0.015") - Decimal("20000")
    )
    assert report["worst_direction_margin_shortfall"] == "2500"
    assert report["additional_funding_required"] == report["r15_equity_shortfall"]
    assert set(report["reserve_scenarios"]) == {"0pct", "10pct", "20pct", "30pct"}
    assert report["reserve_scenarios"]["20pct"]["reserve_fraction"] == "0.20"


def test_stage8_12_3_reserve_shortfall_keeps_equity_and_margin_separate():
    margin_bound = _capacity_report(
        capacity_inputs(),
        realized_equity=Decimal("50000"),
        available_cash=Decimal("10000"),
    )
    scenario = margin_bound["reserve_scenarios"]["20pct"]
    assert scenario["required_equity_with_reserve"] == "32000.00000000000000000000000"
    assert scenario["required_margin_cash_with_reserve"] == "13800.00"
    assert scenario["r15_equity_shortfall"] == "0"
    assert scenario["margin_cash_shortfall"] == "3800.00"
    assert scenario["additional_funding_required"] == "3800.00"

    equity_bound = _capacity_report(
        capacity_inputs(),
        realized_equity=Decimal("20000"),
        available_cash=Decimal("50000"),
    )
    scenario = equity_bound["reserve_scenarios"]["10pct"]
    assert Decimal(scenario["r15_equity_shortfall"]) > 0
    assert scenario["margin_cash_shortfall"] == "0"
    assert (
        scenario["additional_funding_required"]
        == scenario["r15_equity_shortfall"]
    )


def test_stage8_11_ledger_identity_must_match_current_account(tmp_path):
    initialize_stage8_11_acceptance_ledger(tmp_path, "account-A")
    assert _stage8_11_unresolved_for_account(tmp_path, "account-A") == 0
    with pytest.raises(
        PreflightBlocked, match="STAGE8_12_3_STAGE8_11_LEDGER_ACCOUNT_MISMATCH"
    ):
        _stage8_11_unresolved_for_account(tmp_path, "account-B")


def test_h1_watermark_must_match_current_schedule_expectation():
    schedule = {
        "sessions": [{
            "type": "CORE_TRADING",
            "interval": {
                "start_time": "2026-01-05T04:00:00Z",
                "end_time": "2026-01-05T12:00:00Z",
            },
        }]
    }
    observed = datetime(2026, 1, 5, 11, 30, tzinfo=timezone.utc)
    current = datetime(2026, 1, 5, 10, 0, tzinfo=timezone.utc)
    stale = datetime(2026, 1, 5, 9, 0, tzinfo=timezone.utc)
    _require_current_h1_watermark(current, schedule, observed)
    with pytest.raises(PreflightBlocked, match="STAGE8_12_3_H1_WATERMARK_STALE"):
        _require_current_h1_watermark(stale, schedule, observed)


def test_benchmark_loss_obeys_exact_production_tick_grid():
    distance, loss = _strategy_loss_per_contract(
        "USDRUBF", Decimal("0.04")
    )
    assert distance == Decimal("0.100")
    assert loss == Decimal("100")
    with pytest.raises(
        PreflightBlocked, match="STAGE8_12_3_BENCHMARK_STOP_NOT_ON_TICK_GRID"
    ):
        _strategy_loss_per_contract("USDRUBF", Decimal("0.041"))


def test_benchmark_atr_explicitly_mirrors_frozen_cross_day_t3_source():
    assert FROZEN_T3_H1_ATR_CROSSES_TRADING_DAYS is True
    source = Path("TradingSystemLab/strategies/trend/T3_MTF_Trend.py").read_text()
    assert 'low["ATR"] = atr(low, p.atr_period)' in source


def _h1_bar(timestamp):
    return {
        "timestamp": timestamp,
        "open": {"value": "100"},
        "high": {"value": "100.02"},
        "low": {"value": "99.98"},
        "close": {"value": "100"},
    }


class _BarsOnlyAPI:
    def __init__(self, rows):
        self.rows = rows

    def bars(self, symbol, start, end):
        return {"bars": list(self.rows)}


def _benchmark_schedule():
    return {
        "sessions": [{
            "type": "CORE_TRADING",
            "interval": {
                "start_time": "2026-01-05T04:00:00Z",
                "end_time": "2026-01-05T20:00:00Z",
            },
        }]
    }


def test_benchmark_h1_response_rejects_duplicate_and_off_session_rows():
    rows = [
        _h1_bar(f"2026-01-05T{hour:02d}:00:00Z")
        for hour in range(4, 18)
    ]
    watermark = datetime(2026, 1, 5, 17, 0, tzinfo=timezone.utc)
    observed = datetime(2026, 1, 5, 18, 30, tzinfo=timezone.utc)
    common = dict(
        instrument="USDRUBF",
        symbol="USDRUBF@RTSX",
        watermark=watermark,
        params={},
        binding={},
        schedule=_benchmark_schedule(),
        now=observed,
    )
    with pytest.raises(PreflightBlocked, match="STAGE8_12_3_H1_DUPLICATE_BAR"):
        _collect_strategy_loss(
            api=_BarsOnlyAPI(rows + [rows[-1]]),
            **common,
        )
    with pytest.raises(
        PreflightBlocked, match="STAGE8_12_3_H1_BAR_OUTSIDE_VALIDATED_SCHEDULE"
    ):
        _collect_strategy_loss(
            api=_BarsOnlyAPI([_h1_bar("2026-01-05T03:00:00Z")] + rows),
            **common,
        )


def test_benchmark_h1_response_rejects_missing_expected_middle_bar():
    rows = [
        _h1_bar(f"2026-01-05T{hour:02d}:00:00Z")
        for hour in range(4, 18)
    ]
    missing_middle = rows[:6] + rows[7:]
    with pytest.raises(
        PreflightBlocked, match="STAGE8_12_3_H1_EXPECTED_SEQUENCE_GAP"
    ):
        _collect_strategy_loss(
            api=_BarsOnlyAPI(missing_middle),
            instrument="USDRUBF",
            symbol="USDRUBF@RTSX",
            watermark=datetime(2026, 1, 5, 17, 0, tzinfo=timezone.utc),
            params={},
            binding={},
            schedule=_benchmark_schedule(),
            now=datetime(2026, 1, 5, 18, 30, tzinfo=timezone.utc),
        )


def test_absent_production_state_is_clean_and_not_initialized(tmp_path):
    result = _read_production_state(tmp_path, Decimal("100000"))
    assert result == {
        "status": "ABSENT_CLEAN_NOT_INITIALIZED",
        "unresolved_production_intents": 0,
        "local_open_position_count": 0,
        "persisted_realized_equity": None,
    }
    assert not (tmp_path / "state" / PRODUCTION_STATE_FILENAME).exists()


def test_present_production_state_must_be_clean_and_equity_consistent(tmp_path):
    path = tmp_path / "state" / PRODUCTION_STATE_FILENAME
    path.parent.mkdir(parents=True)
    identity = {
        "schema_id": RUNTIME_SCHEMA,
        "production_specification_id": PRODUCTION_SPECIFICATION_ID,
        "active_identity": ACTIVE_IDENTITY,
        "mode": RUNTIME_MODE,
    }
    store = StateStore(path, identity)
    store.put("production_positions", {})
    store.put("realized_equity", "100000")
    store.close()

    clean = _read_production_state(tmp_path, Decimal("100000"))
    assert clean["status"] == "PRESENT_CLEAN"
    assert clean["unresolved_production_intents"] == 0
    assert clean["persisted_realized_equity"] == "100000"

    store = StateStore(path, identity)
    assert store.persist_intent("pending", {"kind": "ENTRY"})
    store.close()
    with pytest.raises(PreflightBlocked, match="UNRESOLVED_PRODUCTION_INTENTS"):
        _read_production_state(tmp_path, Decimal("100000"))


def test_present_production_state_equity_mismatch_fails_closed(tmp_path):
    path = tmp_path / "state" / PRODUCTION_STATE_FILENAME
    path.parent.mkdir(parents=True)
    identity = {
        "schema_id": RUNTIME_SCHEMA,
        "production_specification_id": PRODUCTION_SPECIFICATION_ID,
        "active_identity": ACTIVE_IDENTITY,
        "mode": RUNTIME_MODE,
    }
    store = StateStore(path, identity)
    store.put("production_positions", {})
    store.put("realized_equity", "99999")
    store.close()
    with pytest.raises(PreflightBlocked, match="REALIZED_EQUITY_MISMATCH"):
        _read_production_state(tmp_path, Decimal("100000"))


def test_null_production_intent_status_is_unresolved_fail_closed(tmp_path):
    path = tmp_path / "state" / PRODUCTION_STATE_FILENAME
    path.parent.mkdir(parents=True)
    connection = sqlite3.connect(path)
    try:
        connection.execute(
            "CREATE TABLE state(key TEXT PRIMARY KEY,value TEXT NOT NULL)"
        )
        connection.execute(
            "CREATE TABLE intents("
            "idempotency_key TEXT PRIMARY KEY,payload TEXT NOT NULL,"
            "status TEXT,broker_order_id TEXT,updated_at TEXT)"
        )
        connection.execute("CREATE TABLE fills(fill_id TEXT PRIMARY KEY)")
        identity = {
            "schema_id": RUNTIME_SCHEMA,
            "production_specification_id": PRODUCTION_SPECIFICATION_ID,
            "active_identity": ACTIVE_IDENTITY,
            "mode": RUNTIME_MODE,
        }
        connection.executemany(
            "INSERT INTO state(key,value) VALUES(?,?)",
            [
                ("database_identity", json.dumps(identity)),
                ("production_positions", json.dumps({})),
                ("realized_equity", json.dumps("100000")),
            ],
        )
        connection.execute(
            "INSERT INTO intents(idempotency_key,payload,status) VALUES(?,?,NULL)",
            ("malformed", "{}"),
        )
        connection.commit()
    finally:
        connection.close()
    with pytest.raises(PreflightBlocked, match="UNRESOLVED_PRODUCTION_INTENTS"):
        _read_production_state(tmp_path, Decimal("100000"))


class _BrokerCleanAPI:
    def __init__(self, *, positions=None, orders=None):
        self._positions = [] if positions is None else positions
        self._orders = [] if orders is None else orders

    def account(self, account_id):
        return {
            "status": "ACCOUNT_ACTIVE",
            "positions": self._positions,
        }

    def orders(self, account_id):
        return {"orders": self._orders}


def test_broker_clean_snapshot_is_fail_closed():
    clean = _require_broker_clean_snapshot(_BrokerCleanAPI(), "account")
    assert clean["status"] == "ACCOUNT_ACTIVE"
    with pytest.raises(PreflightBlocked, match="BROKER_POSITION_PRESENT"):
        _require_broker_clean_snapshot(
            _BrokerCleanAPI(
                positions=[{
                    "symbol": "USDRUBF@RTSX",
                    "quantity": {"value": "1"},
                }]
            ),
            "account",
        )


def test_stage8_12_3_preflight_has_no_order_transmission_calls():
    source = Path("TradingSystemLab/stage8_robot/stage8_12_intel_preflight.py").read_text()
    tree = ast.parse(source)
    called_attributes = {
        node.func.attr
        for node in ast.walk(tree)
        if isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute)
    }
    assert not called_attributes.intersection({
        "place_order", "cancel_order", "submit_order", "modify_order", "query_order",
    })
    assert "execution_authorized=False" in source
    assert '"order_endpoint_call_count": 0' in source
    assert '"real_order_count": 0' in source
    assert '"stage8_12_4_status": "NOT_STARTED_NOT_AUTHORIZED"' in source
    assert source.count("_require_safety_state(") >= 3
    assert source.count("_require_broker_clean_snapshot(api, account_id)") >= 2
    assert "COALESCE(status, '') NOT IN" in source
    assert "STAGE8_12_3_H1_EXPECTED_SEQUENCE_GAP" in source


def test_windows_wrapper_enforces_zero_order_preflight_boundaries():
    path = Path(
        "TradingSystemLab/stage8_robot/deploy/windows/"
        "run-stage8-12-3-intel-preflight.ps1"
    )
    source = path.read_text()
    assert "Get-ReadonlyCredential" in source
    assert "Get-TradingCredential" in source
    assert "readonly_supervisor --runtime-root $runtime --once" in source
    assert "Require-DisabledOrAbsentTask $readonlyTaskName" in source
    assert "Require-DisabledOrAbsentTask $productionTaskName" in source
    assert "STAGE8_12_3_PRODUCTION_TASK_SAFE" in source
    assert source.count("Require-DisabledOrAbsentTask $readonlyTaskName") >= 2
    assert source.count("Require-DisabledOrAbsentTask $productionTaskName") >= 2
    assert "Remove-Item $ReportPath -Force -ErrorAction SilentlyContinue" in source
    assert "w32tm /query /status" in source
    assert "w32tm /query /source" in source
    assert "Get-FileHash $ReportPath -Algorithm SHA256" in source
    assert "$repo\\TradingSystemLab\\stage8_robot\\audit_stage8.py" in source
    assert "$repo\\TradingSystemLab\\stage8_robot\\final_operational_audit.py" in source
    assert "-m TradingSystemLab.stage8_robot.audit_stage8" not in source
    assert "-m TradingSystemLab.stage8_robot.final_operational_audit" not in source
    assert "STAGE8_12_3_REAL_ORDER_COUNT=0" in source
    assert "STAGE8_12_3_EXECUTION_AUTHORIZED=false" in source
    assert not any(token in source for token in (
        "place_order", "cancel_order", "submit_order", "modify_order"
    ))
