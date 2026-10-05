from copy import deepcopy
from datetime import datetime, timedelta, timezone
from decimal import Decimal, InvalidOperation
import json
from pathlib import Path

import pytest

from TradingSystemLab.stage8_robot.funding_margin_diagnostic import (
    READY, ZERO_CAPACITY, evaluate, load_production_registry, run)
from TradingSystemLab.stage8_robot.instrument_resolver import (
    MOEX_REFERENCE, N4, parse_rest_value_object)
from TradingSystemLab.stage8_robot.specification import PRODUCTION_SPECIFICATION_ID


def money(value="100"):
    units, _, fraction = value.partition(".")
    return {"currency_code": "RUB", "units": units, "nanos": int((fraction+"000000000")[:9])}


def inputs(cash="1000", equity="10000", r15=8, lot=1):
    production_registry=load_production_registry()
    live_registry={code:{"research_symbol":code,
                         "finam_symbol":row["finam_symbol"], "mic":row["mic"],
                         "security_id":row["security_id"],
                         "status":"AUTHENTICATED_REAL_READONLY", "is_tradable":True}
                   for code,row in production_registry.items()}
    return dict(account={"type":"UNION", "status":"ACCOUNT_ACTIVE", "positions":[],
                         "portfolio_mc":{"available_cash":{"value":cash},
                                          "initial_margin":{"value":"700"},
                                          "maintenance_margin":{"value":"600"}},
                         "equity":{"value":equity}},
                orders={"orders":[]}, details={"readonly":True,"account_ids":["synthetic"]},
                account_id="synthetic", production_id=PRODUCTION_SPECIFICATION_ID,
                registry=live_registry, production_registry=production_registry,
                params={x:{"long_initial_margin":money(),"short_initial_margin":money()} for x in N4},
                sizing={x:{"entry":Decimal("100"),"stop":Decimal("99"),
                           "price_step":Decimal("1"),"tick_value":Decimal("1"),
                           "r15_quantity":r15,"trade_lot_size":lot} for x in N4},
                timestamp="2030-01-01T00:00:00+00:00")


def result(**changes):
    data=inputs()
    data.update(changes)
    return evaluate(**data)


def test_clean_valid_union_mc_account_ready_and_sanitized():
    report=result()
    assert report["funding_classification"]==READY
    assert report["funding_margin_feasibility"]=="PASS"
    assert report["no_order_call_assertion"] is True
    assert report["account_identity_sha256"] != "synthetic"
    assert report["sizing_case_count"] == 8
    assert report["positive_capacity_case_count"] == 8
    assert report["zero_capacity_case_count"] == 0
    assert report["positive_batch_reservation_count"] > 0


def test_committed_registry_is_exact_canonical_authenticated_n4():
    registry=load_production_registry()
    assert {code:(row["finam_symbol"],row["mic"],row["security_id"],
                         row["binding_status"],row["trading_status"])
            for code,row in registry.items()}=={
        "USDRUBF":("USDRUBF@RTSX","RTSX","3447194","AUTHENTICATED_REAL_READONLY","TRADABLE"),
        "CNYRUBF":("CNYRUBF@RTSX","RTSX","3447192","AUTHENTICATED_REAL_READONLY","TRADABLE"),
        "GLDRUBF":("GLDRUBF@RTSX","RTSX","4454911","AUTHENTICATED_REAL_READONLY","TRADABLE"),
        "IMOEXF":("IMOEXF@RTSX","RTSX","4631091","AUTHENTICATED_REAL_READONLY","TRADABLE"),
    }


@pytest.mark.parametrize("value",[pytest.param("missing",id="missing"),pytest.param(None,id="null")])
def test_missing_or_null_mc_fails_closed(value):
    data=inputs()
    if value=="missing": data["account"].pop("portfolio_mc")
    else: data["account"]["portfolio_mc"]=None
    report=evaluate(**data)
    assert report["funding_classification"]=="BLOCKED_ACCOUNT_FINANCIALS_INVALID"
    assert report["reason_code"] in {"PORTFOLIO_ONEOF_MISSING","PORTFOLIO_ONEOF_NULL_OR_INVALID"}


@pytest.mark.parametrize("mutation,reason",[
    (lambda f:f.pop("available_cash"),"REST_DECIMAL_VALUE_OBJECT_INVALID"),
    (lambda f:f.pop("initial_margin"),"REST_DECIMAL_VALUE_OBJECT_INVALID"),
    (lambda f:f.pop("maintenance_margin"),"REST_DECIMAL_VALUE_OBJECT_INVALID"),
    (lambda f:f.update(available_cash={"value":12}),"REST_DECIMAL_VALUE_INVALID"),
    (lambda f:f.update(available_cash={"value":"-1"}),"NEGATIVE_MC_FINANCIAL"),
    (lambda f:f.update(initial_margin={"value":"-1"}),"NEGATIVE_MC_FINANCIAL"),
    (lambda f:f.update(maintenance_margin={"value":"-1"}),"NEGATIVE_MC_FINANCIAL")])
def test_invalid_mc_fails_closed(mutation,reason):
    data=inputs(); mutation(data["account"]["portfolio_mc"]); report=evaluate(**data)
    assert report["funding_classification"]=="BLOCKED_ACCOUNT_FINANCIALS_INVALID"
    assert report["reason_code"]==reason


@pytest.mark.parametrize("bad", [12,"12",{"num":12,"scale":0},{"value":"12","extra":0},
                                  {"value":"NaN"},{"value":"Infinity"}])
def test_noncanonical_mc_decimal_fails_closed(bad):
    data=inputs(); data["account"]["portfolio_mc"]["available_cash"]=bad
    assert evaluate(**data)["funding_classification"]=="BLOCKED_ACCOUNT_FINANCIALS_INVALID"


@pytest.mark.parametrize("portfolios,reason", [
    ({"portfolio_mc":{},"portfolio_forts":{}},"PORTFOLIO_ONEOF_MULTIPLE"),
    ({"portfolio_mc":{},"portfolio_mct":{}},"PORTFOLIO_ONEOF_MULTIPLE"),
    ({"portfolio_mc":{},"portfolio_forts":{},"portfolio_mct":{}},"PORTFOLIO_ONEOF_MULTIPLE"),
    ({"portfolio_mct":{}},"PORTFOLIO_MCT_UNSUPPORTED"),
])
def test_portfolio_oneof_rejected(portfolios,reason):
    data=inputs(); data["account"]={k:v for k,v in data["account"].items() if not k.startswith("portfolio_")}
    data["account"].update(portfolios)
    assert evaluate(**data)["reason_code"]==reason


def test_account_portfolio_mismatches_and_unknown_type_rejected():
    data=inputs(); mc=data["account"].pop("portfolio_mc")
    data["account"]["portfolio_forts"]={"available_cash":{"value":"1"},"money_reserved":{"value":"0"}}
    assert evaluate(**data)["reason_code"]=="ACCOUNT_PORTFOLIO_MISMATCH"
    data=inputs(); data["account"]["type"]="ACCOUNT_TYPE_FORTS"
    assert evaluate(**data)["reason_code"]=="ACCOUNT_PORTFOLIO_MISMATCH"
    data=inputs(); data["account"]["type"]="UNKNOWN"
    assert evaluate(**data)["reason_code"]=="ACCOUNT_TYPE_UNSUPPORTED"


def test_mc_account_margins_are_evidence_not_capacity_deductions():
    data=inputs(cash="500",r15=8)
    data["account"]["portfolio_mc"]["initial_margin"]={"value":"499999"}
    data["account"]["portfolio_mc"]["maintenance_margin"]={"value":"499998"}
    report=evaluate(**data)
    assert report["per_instrument"]["USDRUBF:LONG"]["margin_quantity"]==5
    assert report["available_cash"]=="500"


@pytest.mark.parametrize("equity",[None,{"value":12},{"value":"0"}])
def test_invalid_equity_is_distinct(equity):
    data=inputs(); data["account"]["equity"]=equity
    assert evaluate(**data)["funding_classification"]=="BLOCKED_ACCOUNT_EQUITY_INVALID"


@pytest.mark.parametrize("direction",["long_initial_margin","short_initial_margin"])
def test_malformed_directional_margin(direction):
    data=inputs(); data["params"][N4[0]][direction]={"bad":"shape"}
    assert evaluate(**data)["funding_classification"]=="BLOCKED_DIRECTIONAL_MARGIN_INVALID"


def test_non_rub_margin_and_missing_fourth_margin_fail():
    data=inputs(); data["params"][N4[0]]["long_initial_margin"]["currency_code"]="USD"
    assert evaluate(**data)["reason_code"]=="MARGIN_CURRENCY_MISMATCH"
    data=inputs(); data["params"].pop(N4[-1])
    assert evaluate(**data)["funding_classification"]=="BLOCKED_DIRECTIONAL_MARGIN_INVALID"


def test_r15_below_cap_and_margin_below_r15():
    low_risk=evaluate(**inputs(cash="10000",r15=3))
    assert low_risk["per_instrument"]["USDRUBF:LONG"]["final_quantity"]==3
    low_cash=evaluate(**inputs(cash="250",r15=8))
    assert low_cash["per_instrument"]["USDRUBF:LONG"]["final_quantity"]==2


def test_zero_capacity_lot_floor_and_cap_never_increases():
    zero=evaluate(**inputs(cash="0",r15=8))
    assert zero["funding_classification"]==ZERO_CAPACITY
    assert zero["reason_code"]=="ZERO_CONTRACT_CAPACITY"
    assert zero["funding_margin_feasibility"]=="BLOCKED"
    assert zero["sizing_case_count"]==8
    assert zero["positive_capacity_case_count"]==0
    assert zero["zero_capacity_case_count"]==8
    assert zero["positive_batch_reservation_count"]==0
    assert all(case["final_quantity"]==0 for case in zero["per_instrument"].values())
    assert all(item["quantity"]==0 for item in zero["batch_budget"]["reservations"])
    assert Decimal(zero["batch_budget"]["remaining_cash"])>=0
    assert zero["per_instrument"]["USDRUBF:LONG"]["final_quantity"]==0
    floored=evaluate(**inputs(cash="550",r15=9,lot=3))
    case=floored["per_instrument"]["USDRUBF:LONG"]
    assert case["final_quantity"]==3 and case["final_quantity"]%3==0
    assert case["final_quantity"]<=case["r15_quantity"]


def test_mixed_capacity_can_reach_ready_without_changing_authorities():
    data=inputs(cash="150",r15=8)
    data["params"][N4[0]]["long_initial_margin"]=money("100")
    for code in N4:
        data["params"][code]["short_initial_margin"]=money("200")
    for code in N4[1:]:
        data["params"][code]["long_initial_margin"]=money("200")
    report=evaluate(**data)
    assert report["funding_classification"]==READY
    assert report["positive_capacity_case_count"]==1
    assert report["zero_capacity_case_count"]==7
    assert report["financial_schema_valid"] is True
    assert report["n4_binding_valid"] is True
    assert report["directional_margins_valid"] is True


def test_regression_zero_capacity_must_never_be_ready():
    report=evaluate(**inputs(cash="99",r15=8))
    assert report["positive_capacity_case_count"]==0
    assert report["funding_classification"]!=READY


def test_batch_budget_never_reuses_stale_cash():
    report=evaluate(**inputs(cash="500",r15=3))
    remaining=[Decimal(x["remaining_cash"]) for x in report["batch_budget"]["reservations"]]
    assert remaining==sorted(remaining,reverse=True) and min(remaining)>=0
    assert sum(x["quantity"] for x in report["batch_budget"]["reservations"])<=5


@pytest.mark.parametrize("field",["positions","orders"])
def test_dirty_account_fails_closed(field):
    data=inputs()
    if field=="positions":
        data["account"]["positions"]=[{"symbol":"CNYRUBF@RTSX","quantity":{"value":"1"}}]
    else:
        data["orders"]={"orders":[{"status":"ACTIVE"}]}
    assert evaluate(**data)["funding_classification"]=="BLOCKED_ACCOUNT_NOT_CLEAN"


def test_zero_quantity_position_and_terminal_order_history_are_clean():
    data=inputs()
    data["account"]["positions"]=[{"symbol":"CNYRUBF@RTSX","quantity":{"value":"0.0"}}]
    data["orders"]={"orders":[{"status":"FILLED"},{"status":"ORDER_STATUS_CANCELLED"}]}
    report=evaluate(**data)
    assert report["funding_classification"]==READY
    assert report["account_clean"] is True


@pytest.mark.parametrize("field",["positions","orders"])
def test_malformed_cleanliness_state_is_schema_failure(field):
    data=inputs()
    if field=="positions":
        data["account"]["positions"]=[{"symbol":"CNYRUBF@RTSX","quantity":{"value":"NaN"}}]
    else:
        data["orders"]={"orders":[{"status":"UNKNOWN"}]}
    report=evaluate(**data)
    assert report["funding_classification"]=="BLOCKED_ACCOUNT_SCHEMA_INVALID"
    assert report["reason_code"]=="CLEANLINESS_SCHEMA_INVALID"


def test_non_readonly_wrong_production_and_registry_fail_closed():
    data=inputs(); data["details"]["readonly"]=False
    assert evaluate(**data)["reason_code"]=="TOKEN_NOT_READONLY"
    data=inputs(); data["production_id"]="wrong"
    assert evaluate(**data)["reason_code"]=="PRODUCTION_ID_MISMATCH"
    data=inputs(); data["registry"].pop(N4[-1])
    assert evaluate(**data)["reason_code"]=="PRODUCTION_REGISTRY_BINDING_MISMATCH"


@pytest.mark.parametrize("status", ["ACCOUNT_ACTIVE", "ACCOUNT_STATUS_ACTIVE"])
def test_production_active_account_statuses_are_accepted(status):
    data=inputs(); data["account"]["status"]=status
    assert evaluate(**data)["funding_classification"]==READY


@pytest.mark.parametrize("status", ["ACTIVE", "ACCOUNT_INACTIVE", "UNKNOWN"])
def test_unknown_or_inactive_account_status_fails_closed(status):
    data=inputs(); data["account"]["status"]=status
    assert evaluate(**data)["reason_code"]=="ACCOUNT_NOT_ACTIVE"


@pytest.mark.parametrize("field,value", [
    ("finam_symbol", "WRONG@RTSX"),
    ("mic", "WRONG"),
    ("security_id", "999"),
    ("binding_status", "BLOCKED_UNAUTHENTICATED"),
    ("trading_status", "NOT_TRADABLE"),
])
def test_mutated_production_registry_fails_closed(field, value):
    data=inputs(); data["production_registry"][N4[0]][field]=value
    report=evaluate(**data)
    assert report["funding_classification"]=="BLOCKED_N4_AUTHORITY_INVALID"
    assert report["reason_code"]=="PRODUCTION_REGISTRY_BINDING_MISMATCH"


def test_production_registry_requires_exact_four_rows():
    data=inputs(); data["production_registry"].pop(N4[-1])
    assert evaluate(**data)["reason_code"]=="PRODUCTION_REGISTRY_BINDING_MISMATCH"


@pytest.mark.parametrize("field,value", [
    ("finam_symbol", "REPLACEMENT@RTSX"), ("mic", "MISX"),
    ("security_id", "9999999"), ("status", "BLOCKED_UNAUTHENTICATED"),
    ("is_tradable", False),
])
def test_live_binding_must_equal_frozen_registry(field, value):
    data=inputs(); data["registry"][N4[0]][field]=value
    assert evaluate(**data)["reason_code"]=="PRODUCTION_REGISTRY_BINDING_MISMATCH"


def test_diagnostic_source_has_no_order_capable_api_attribute_calls():
    import ast
    source=Path("TradingSystemLab/stage8_robot/funding_margin_diagnostic.py").read_text()
    called={node.func.attr for node in ast.walk(ast.parse(source))
            if isinstance(node,ast.Call) and isinstance(node.func,ast.Attribute)}
    assert called.isdisjoint({"place_order","submit_order","cancel_order","modify_order"})


class FakeReadonlyAPI:
    """Deterministic FINAM-shaped read-only API used only by run-path tests."""

    ORDER_CAPABLE = {"place_order", "submit_order", "cancel_order", "modify_order"}

    def __init__(self):
        self.calls = []
        self.details = {"readonly": True, "account_ids": ["synthetic-account"]}
        self.account_payload = {
            "type": "UNION", "status": "ACCOUNT_ACTIVE", "positions": [],
            "portfolio_mc": {"available_cash": {"value": "100000"},
                             "initial_margin": {"value": "250"},
                             "maintenance_margin": {"value": "200"}},
            "equity": {"value": "100000"},
        }
        self.orders_payload = {"orders": []}
        registry = load_production_registry()
        self.catalog = [{"ticker": code, "symbol": row["finam_symbol"],
                         "mic": row["mic"], "id": row["security_id"],
                         "type": "FUTURES", "is_archived": False}
                        for code, row in registry.items()]
        self.params = {
            row["finam_symbol"]: {
                "is_tradable": True, "trade_lot_size": "1",
                "long_initial_margin": money("100"),
                "short_initial_margin": money("110"),
            } for row in registry.values()
        }
        self.account_assets = {}
        for code, row in registry.items():
            step, _, contract_size = MOEX_REFERENCE[code]
            self.account_assets[row["finam_symbol"]] = {
                "ticker": code, "symbol": row["finam_symbol"], "mic": row["mic"],
                "id": row["security_id"], "type": "FUTURES", "quote_currency": "RUB",
                "decimals": 0, "min_step": str(step),
                "lot_size": {"value": str(contract_size)},
                "future_details": {"contract_size": {"value": str(contract_size)}},
            }

    def _record(self, name):
        self.calls.append(name)

    def create_session(self): self._record("create_session"); return {}
    def session_details(self): self._record("session_details"); return deepcopy(self.details)
    def account(self, account_id): self._record("account"); return deepcopy(self.account_payload)
    def orders(self, account_id): self._record("orders"); return deepcopy(self.orders_payload)
    def assets_all_active(self): self._record("assets_all_active"); return deepcopy(self.catalog)
    def asset_params(self, symbol, account_id):
        self._record("asset_params"); return deepcopy(self.params[symbol])
    def asset(self, symbol, account_id):
        self._record("asset"); return deepcopy(self.account_assets[symbol])
    def schedule(self, symbol):
        self._record("schedule")
        now = datetime.now(timezone.utc)
        start = now.replace(hour=0, minute=0, second=0, microsecond=0)
        return {"sessions": [{"type": "CORE_TRADING", "interval": {
            "start_time": start.isoformat(), "end_time": (start+timedelta(days=1)).isoformat()}}]}
    def bars(self, symbol, start, end):
        self._record("bars")
        opened = datetime.now(timezone.utc).replace(minute=0, second=0, microsecond=0)-timedelta(hours=1)
        # FINAM REST bars use value objects for open/high/low/close/volume;
        # only timestamp and close are consumed by this diagnostic fixture.
        return {"bars": [{"timestamp": opened.isoformat(),
                           "close": {"value": "100"}}]}


def run_report(tmp_path, api):
    path = tmp_path / "stage8-9-synthetic-report.json"
    report = run(api, "synthetic-account", path)
    assert path.is_file()
    assert json.loads(path.read_text()) == report
    serialized = path.read_text()
    assert "synthetic-account" not in serialized
    assert "secret" not in serialized.lower()
    assert "jwt" not in serialized.lower()
    assert set(api.calls).isdisjoint(FakeReadonlyAPI.ORDER_CAPABLE)
    return report


def assert_no_market_collection(api):
    assert set(api.calls).isdisjoint({"assets_all_active", "asset_params", "schedule", "asset", "bars"})


def test_run_clean_account_validates_and_writes_sanitized_external_report(tmp_path):
    api = FakeReadonlyAPI()
    report = run_report(tmp_path, api)
    assert report["funding_classification"] == READY
    assert api.calls[:5] == ["create_session", "session_details", "account", "orders",
                             "assets_all_active"]
    assert api.calls.count("bars") == len(N4)


@pytest.mark.parametrize("value,expected", [
    ({"value": "100"}, Decimal("100")),
    ({"value": "123.456"}, Decimal("123.456")),
])
def test_rest_h1_close_value_object_parses_exactly(value, expected):
    assert parse_rest_value_object(value) == expected


@pytest.mark.parametrize("close", [
    100,
    "100",
    {"num": 100, "scale": 0},
    {},
    {"value": 100},
    {"value": "100", "extra": "field"},
    {"value": "NaN"},
    {"value": "Infinity"},
    {"value": "-Infinity"},
])
def test_rest_h1_close_noncanonical_values_fail_closed(close):
    with pytest.raises(ValueError):
        parse_rest_value_object(close)


@pytest.mark.parametrize("close", [
    pytest.param(100, id="numeric-json"),
    pytest.param("100", id="bare-string"),
    pytest.param({"num": 100, "scale": 0}, id="protobuf"),
    pytest.param({}, id="malformed-object"),
    pytest.param({"value": "NaN"}, id="nan"),
    pytest.param({"value": "Infinity"}, id="infinity"),
    pytest.param(None, id="missing"),
])
def test_run_invalid_h1_close_writes_sanitized_sizing_blocker(
        tmp_path, close):
    api = FakeReadonlyAPI()
    original_bars = api.bars

    def malformed_bars(symbol, start, end):
        payload = original_bars(symbol, start, end)
        if close is None:
            payload["bars"][0].pop("close")
        else:
            payload["bars"][0]["close"] = close
        return payload

    api.bars = malformed_bars
    try:
        report = run_report(tmp_path, api)
    except InvalidOperation as exc:  # Regression guard for Decimal(str(close)).
        pytest.fail(f"REST close schema error escaped as InvalidOperation: {exc}")
    assert report["funding_classification"] == "BLOCKED_FUNDING_FEASIBILITY_INVALID"
    assert report["reason_code"] == "SIZING_EVIDENCE_INVALID"
    assert report["funding_classification"] != "BLOCKED_ACCOUNT_FINANCIALS_UNAVAILABLE"
    assert set(api.calls).isdisjoint(FakeReadonlyAPI.ORDER_CAPABLE)


def test_run_non_readonly_stops_before_account_or_market_collection(tmp_path):
    api = FakeReadonlyAPI(); api.details["readonly"] = False
    report = run_report(tmp_path, api)
    assert report["funding_classification"] == "BLOCKED_SAFETY_PREREQUISITE"
    assert report["reason_code"] == "TOKEN_NOT_READONLY"
    assert api.calls == ["create_session", "session_details"]


def test_run_unenumerated_account_stops_before_account_collection(tmp_path):
    api = FakeReadonlyAPI(); api.details["account_ids"] = ["different-account"]
    report = run_report(tmp_path, api)
    assert report["reason_code"] == "ACCOUNT_NOT_ENUMERATED"
    assert api.calls == ["create_session", "session_details"]


def test_run_inactive_account_stops_before_orders_or_market_collection(tmp_path):
    api = FakeReadonlyAPI(); api.account_payload["status"] = "ACCOUNT_INACTIVE"
    report = run_report(tmp_path, api)
    assert report["funding_classification"] == "BLOCKED_ACCOUNT_INACTIVE"
    assert api.calls == ["create_session", "session_details", "account"]
    assert_no_market_collection(api)


@pytest.mark.parametrize("dirty", ["positions", "orders"])
def test_run_dirty_account_stops_before_market_and_sizing_collection(tmp_path, dirty):
    api = FakeReadonlyAPI()
    if dirty == "positions":
        api.account_payload["positions"] = [{"symbol": "CNYRUBF@RTSX", "quantity": {"value": "1"}}]
    else:
        api.orders_payload["orders"] = [{"status": "ACTIVE"}]
    report = run_report(tmp_path, api)
    assert report["funding_classification"] == "BLOCKED_ACCOUNT_NOT_CLEAN"
    assert api.calls == ["create_session", "session_details", "account", "orders"]
    assert_no_market_collection(api)


@pytest.mark.parametrize("trade_lot_size", [None, "invalid"])
def test_run_invalid_trade_lot_blocks_binding_without_h1_or_decimal_exception(
        tmp_path, trade_lot_size):
    api = FakeReadonlyAPI(); first = api.catalog[0]["symbol"]
    api.params[first]["trade_lot_size"] = trade_lot_size
    report = run_report(tmp_path, api)
    assert report["funding_classification"] == "BLOCKED_N4_AUTHORITY_INVALID"
    assert report["reason_code"] == "PRODUCTION_REGISTRY_BINDING_MISMATCH"
    assert api.calls.count("bars") == len(N4)-1


@pytest.mark.parametrize("field,value", [
    ("id", "999999"), ("mic", "MISX"), ("ticker", "WRONG")])
def test_run_frozen_identity_mismatch_writes_sanitized_n4_blocker(
        tmp_path, field, value):
    api = FakeReadonlyAPI(); first = api.catalog[0]["symbol"]
    api.account_assets[first][field] = value
    report = run_report(tmp_path, api)
    assert report["funding_classification"] == "BLOCKED_N4_AUTHORITY_INVALID"
    assert report["reason_code"] == "PRODUCTION_REGISTRY_BINDING_MISMATCH"
    assert api.calls.count("bars") == len(N4)-1


def test_run_missing_mc_writes_financials_invalid_report(tmp_path):
    api = FakeReadonlyAPI(); api.account_payload.pop("portfolio_mc")
    report = run_report(tmp_path, api)
    assert report["funding_classification"] == "BLOCKED_ACCOUNT_FINANCIALS_INVALID"
    assert report["reason_code"] == "PORTFOLIO_ONEOF_MISSING"


def test_run_malformed_directional_margin_writes_blocked_report(tmp_path):
    api = FakeReadonlyAPI(); first = api.catalog[0]["symbol"]
    api.params[first]["long_initial_margin"] = {"bad": "shape"}
    report = run_report(tmp_path, api)
    assert report["funding_classification"] == "BLOCKED_DIRECTIONAL_MARGIN_INVALID"
    assert report["reason_code"] == "MALFORMED_MONEY"
