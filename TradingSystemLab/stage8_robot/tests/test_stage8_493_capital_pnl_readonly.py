"""Synthetic offline capital/flows reporting. NO client-specific cash data."""
from __future__ import annotations

from copy import deepcopy
import pytest

from TradingSystemLab.stage8_robot.diagnostics.stage8_493_capital_pnl_readonly import (
    Blocked, SCHEMA, SPEC, IDENTITY, classify,
)

ACCOUNT = "a" * 64


def sample():
    return {
        "schema_id": SCHEMA,
        "production_specification_id": SPEC,
        "active_identity": IDENTITY,
        "account_identity_sha256": ACCOUNT,
        "broker_equity_rub": "55000",
        "unrealized_pnl_rub": "0",
        "production_realized_equity_rub": "55000",
        "production_starting_realized_equity_rub": "5000",
        "sizing_explained_external_cash_flows_rub": "0",
        "external_flows": [
            {"flow_id": "synthetic-deposit-1", "kind": "DEPOSIT",
             "amount_rub": "50000", "account_identity_sha256": ACCOUNT,
             "source_classification": "OPERATOR_CONFIRMED"},
        ],
    }


def test_deposit_in_risk_capital_not_in_pnl():
    result = classify(sample())
    assert result["frozen_full_r15_capital_rub"] == "55000"
    assert result["new_position_r15_nominal_cash_rub"] == "825.000"
    assert result["net_external_contributions_rub"] == "50000"
    assert result["contribution_adjusted_account_change_rub"] == "0"
    assert result["deposit_is_trading_profit"] is False
    assert result["broker_statement_and_fee_pnl_audit"] == "NOT_PERFORMED"
    assert result["production_sqlite_writes"] == 0
    assert result["real_order_endpoint_calls"] == 0
    assert result["live_execution_authorized"] is False


def test_multiple_deposits_remain_in_full_r15():
    x = sample()
    x["broker_equity_rub"] = x["production_realized_equity_rub"] = "65000"
    x["external_flows"].append({
        "flow_id": "synthetic-deposit-2", "kind": "DEPOSIT",
        "amount_rub": "10000", "account_identity_sha256": ACCOUNT,
        "source_classification": "BROKER_STATEMENT_OBSERVED",
    })
    result = classify(x)
    assert result["frozen_full_r15_capital_rub"] == "65000"
    assert result["net_external_contributions_rub"] == "60000"
    assert result["contribution_adjusted_account_change_rub"] == "0"
    assert result["source_status"].startswith("OPERATOR_CONFIRMATION_")


def test_withdrawal_and_negative_account_change_are_not_conflated():
    x = sample()
    x["broker_equity_rub"] = x["production_realized_equity_rub"] = "52000"
    x["external_flows"].append({
        "flow_id": "synthetic-withdrawal", "kind": "WITHDRAWAL",
        "amount_rub": "2000", "account_identity_sha256": ACCOUNT,
        "source_classification": "BROKER_STATEMENT_OBSERVED",
    })
    result = classify(x)
    assert result["net_external_contributions_rub"] == "48000"
    assert result["contribution_adjusted_account_change_rub"] == "-1000"


def test_unrealized_profit_not_counted_as_realized_r15():
    x = sample()
    x["broker_equity_rub"] = "57000"
    x["unrealized_pnl_rub"] = "2000"
    result = classify(x)
    assert result["frozen_full_r15_capital_rub"] == "55000"
    assert result["contribution_adjusted_account_change_rub"] == "0"


@pytest.mark.parametrize("key,value,code", [
    ("sizing_explained_external_cash_flows_rub", "50000", "NONZERO_SIZING_DEDUCTION"),
    ("sizing_explained_external_cash_flows_rub", "-1", "NONZERO_SIZING_DEDUCTION"),
    ("production_realized_equity_rub", "5000", "FROZEN_REALIZED_BASIS_NOT_RECONCILED"),
    ("broker_equity_rub", "0", "BROKER_EQUITY_INVALID"),
    ("broker_equity_rub", "NaN", "BROKER_EQUITY_INVALID"),
    ("broker_equity_rub", 55000.0, "BROKER_EQUITY_DECIMAL_STRING_REQUIRED"),
    ("unrealized_pnl_rub", "Infinity", "UNREALIZED_PNL_INVALID"),
    ("production_starting_realized_equity_rub", "-500", "PRODUCTION_STARTING_INVALID"),
    ("account_identity_sha256", "other-account", "CAPITAL_REPORT_IDENTITY_INVALID"),
])
def test_inconsistent_or_unsafe_capital_fails_closed(key, value, code):
    x = sample()
    x[key] = value
    with pytest.raises(Blocked, match=code):
        classify(x)


@pytest.mark.parametrize("change,code", [
    (lambda x: x["external_flows"].append(deepcopy(x["external_flows"][0])), "CASH_FLOW_IDENTITY_OR_DUPLICATE_INVALID"),
    (lambda x: x["external_flows"][0].update(kind="TRADING_PROFIT"), "CASH_FLOW_TYPE_INVALID"),
    (lambda x: x["external_flows"][0].update(amount_rub="0"), "CASH_FLOW_AMOUNT_INVALID"),
    (lambda x: x["external_flows"][0].update(amount_rub="NaN"), "CASH_FLOW_AMOUNT_INVALID"),
    (lambda x: x["external_flows"][0].update(account_identity_sha256="b"*64), "CASH_FLOW_IDENTITY_OR_DUPLICATE_INVALID"),
    (lambda x: x["external_flows"][0].update(source_classification="UNKNOWN"), "CASH_FLOW_SOURCE_INVALID"),
    (lambda x: x.update(external_flows=[]), "EXTERNAL_CONTRIBUTION_EVIDENCE_REQUIRED"),
])
def test_bogus_external_flows_are_rejected(change, code):
    x = sample()
    change(x)
    with pytest.raises(Blocked, match=code):
        classify(x)


def test_invalid_report_schema_is_rejected():
    x = sample()
    x["untrusted_field"] = "override_authorization"
    with pytest.raises(Blocked, match="CAPITAL_REPORT_SCHEMA_INVALID"):
        classify(x)


def test_source_never_accesses_live_or_broker(tmp_path):
    p = tmp_path / "missing-report.json"
    assert not p.exists()
    result = classify(sample())
    assert result["production_sqlite_writes"] == 0
    from pathlib import Path
    source = (Path(__file__).resolve().parents[1] /
              "diagnostics" / "stage8_493_capital_pnl_readonly.py").read_text("utf-8")
    for forbidden in (
        "import FinamAPI", "sqlite3", "requests", "create_session(",
        "place_order(", "place_sltp_order(", "cancel_order(",
        "write_kill_switch(", "start-scheduledtask", "execution_authorized=True",
    ):
        assert forbidden not in source
