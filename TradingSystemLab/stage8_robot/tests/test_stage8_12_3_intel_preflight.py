from __future__ import annotations

import ast
from decimal import Decimal
from pathlib import Path

import pytest

from TradingSystemLab.stage8_robot.n4_capacity import N4CapacityInput
from TradingSystemLab.stage8_robot.production_runtime import MODE as RUNTIME_MODE, RUNTIME_SCHEMA
from TradingSystemLab.stage8_robot.specification import ACTIVE_IDENTITY, PRODUCTION_SPECIFICATION_ID
from TradingSystemLab.stage8_robot.stage8_12_intel_preflight import (
    PRODUCTION_STATE_FILENAME,
    PreflightBlocked,
    _capacity_report,
    _read_production_state,
)
from TradingSystemLab.stage8_robot.state import StateStore


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
    assert "w32tm /query /status" in source
    assert "w32tm /query /source" in source
    assert "Get-FileHash $ReportPath -Algorithm SHA256" in source
    assert "STAGE8_12_3_REAL_ORDER_COUNT=0" in source
    assert "STAGE8_12_3_EXECUTION_AUTHORIZED=false" in source
    assert not any(token in source for token in (
        "place_order", "cancel_order", "submit_order", "modify_order"
    ))
