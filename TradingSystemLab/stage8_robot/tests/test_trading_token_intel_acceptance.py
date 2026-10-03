import ast
import json
from datetime import datetime, timezone
from pathlib import Path

import pytest

from TradingSystemLab.stage8_robot import trading_token_intel_acceptance as acceptance
from TradingSystemLab.stage8_robot.specification import PRODUCTION_SPECIFICATION_ID
from TradingSystemLab.stage8_robot.trading_safety_gate import KILL_SWITCH_FILENAME, KILL_SWITCH_SCHEMA


SECRET = "synthetic-stage-8107-secret"
ACCOUNT = "SYNTHETIC-STAGE-8107-ACCOUNT"


class FakeAPI:
    calls = []
    details = {"account_ids": [ACCOUNT], "readonly": False}
    fail_create = False
    fail_details = False

    def __init__(self, secret):
        assert secret == SECRET

    def create_session(self):
        self.calls.append("create_session")
        if self.fail_create:
            raise RuntimeError("sensitive transport detail")

    def session_details(self):
        self.calls.append("session_details")
        if self.fail_details:
            raise RuntimeError("sensitive transport detail")
        return self.details


def put_switch(root, *, state="HALTED", production_id=PRODUCTION_SPECIFICATION_ID, malformed=False):
    path = root / "safety" / KILL_SWITCH_FILENAME
    path.parent.mkdir(parents=True, exist_ok=True)
    if malformed:
        path.write_text("not-json", encoding="utf-8")
    else:
        path.write_text(json.dumps({
            "schema_id": KILL_SWITCH_SCHEMA,
            "production_specification_id": production_id,
            "state": state,
            "generation": 1,
            "updated_utc": "2026-10-03T00:00:00+00:00",
        }), encoding="utf-8")


@pytest.fixture(autouse=True)
def reset_fake():
    FakeAPI.calls = []
    FakeAPI.details = {"account_ids": [ACCOUNT], "readonly": False}
    FakeAPI.fail_create = False
    FakeAPI.fail_details = False


def run(root, **kwargs):
    return acceptance.validate_intel_trading_token_acceptance(
        kwargs.pop("secret", SECRET), kwargs.pop("account", ACCOUNT), root,
        local_account_binding_confirmed=kwargs.pop("binding", True),
        api_factory=kwargs.pop("factory", FakeAPI),
        observed_utc=datetime(2026, 10, 3, tzinfo=timezone.utc), **kwargs,
    )


def test_valid_halted_session_pass_is_sanitized_and_session_only(tmp_path):
    put_switch(tmp_path)
    report = run(tmp_path)
    body = json.dumps(report)
    assert report["schema_id"] == acceptance.SCHEMA_ID
    assert report["trading_token_readonly"] is False
    assert report["remote_call_scope"] == "SESSION_CREATE_AND_DETAILS_ONLY"
    assert report["order_endpoint_called"] is False and report["order_count"] == 0
    assert report["execution_authorized"] is False
    assert report["stage8_10_8_status"] == "NOT_STARTED"
    assert SECRET not in body and ACCOUNT not in body and "account_ids" not in body
    assert FakeAPI.calls == ["create_session", "session_details"]


@pytest.mark.parametrize(("setup", "code"), [
    (lambda root: None, "STAGE8_10_7_KILL_SWITCH_INVALID"),
    (lambda root: put_switch(root, malformed=True), "STAGE8_10_7_KILL_SWITCH_INVALID"),
    (lambda root: put_switch(root, state="ARMED"), "STAGE8_10_7_KILL_SWITCH_NOT_HALTED"),
    (lambda root: put_switch(root, production_id="WRONG"), "STAGE8_10_7_KILL_SWITCH_INVALID"),
])
def test_pre_auth_switch_failure_prevents_api_factory(tmp_path, setup, code):
    setup(tmp_path)
    constructed = []
    with pytest.raises(acceptance.TradingTokenAcceptanceError, match=f"^{code}$"):
        run(tmp_path, factory=lambda secret: constructed.append(secret))
    assert constructed == []


@pytest.mark.parametrize(("changes", "code"), [
    ({"secret": ""}, "STAGE8_10_7_SECRET_MISSING"),
    ({"account": ""}, "STAGE8_10_7_ACCOUNT_MISSING"),
    ({"binding": False}, "STAGE8_10_7_LOCAL_ACCOUNT_BINDING_NOT_CONFIRMED"),
    ({"binding": 1}, "STAGE8_10_7_LOCAL_ACCOUNT_BINDING_NOT_CONFIRMED"),
])
def test_required_preconditions_fail_closed(tmp_path, changes, code):
    put_switch(tmp_path)
    with pytest.raises(acceptance.TradingTokenAcceptanceError, match=f"^{code}$"):
        run(tmp_path, **changes)


def test_create_and_details_failures_are_sanitized(tmp_path):
    put_switch(tmp_path)
    FakeAPI.fail_create = True
    with pytest.raises(acceptance.TradingTokenAcceptanceError, match="^STAGE8_10_7_SESSION_CREATE_FAILED$"):
        run(tmp_path)
    FakeAPI.fail_create = False
    FakeAPI.fail_details = True
    with pytest.raises(acceptance.TradingTokenAcceptanceError, match="^STAGE8_10_7_SESSION_DETAILS_FAILED$"):
        run(tmp_path)


@pytest.mark.parametrize(("details", "code"), [
    ([], "STAGE8_10_7_SESSION_DETAILS_NOT_OBJECT"),
    ({"readonly": False}, "STAGE8_10_7_ACCOUNT_IDS_MISSING"),
    ({"account_ids": "bad", "readonly": False}, "STAGE8_10_7_ACCOUNT_IDS_MALFORMED"),
    ({"account_ids": [True], "readonly": False}, "STAGE8_10_7_ACCOUNT_IDS_MALFORMED"),
    ({"account_ids": ["OTHER"], "readonly": False}, "STAGE8_10_7_EXPECTED_ACCOUNT_NOT_ENUMERATED"),
    ({"account_ids": [ACCOUNT, ACCOUNT], "readonly": False}, "STAGE8_10_7_EXPECTED_ACCOUNT_DUPLICATED"),
    ({"account_ids": [ACCOUNT]}, "STAGE8_10_7_READONLY_MISSING"),
    ({"account_ids": [ACCOUNT], "readonly": "false"}, "STAGE8_10_7_READONLY_NOT_EXACT_BOOL"),
    ({"account_ids": [ACCOUNT], "readonly": 0}, "STAGE8_10_7_READONLY_NOT_EXACT_BOOL"),
    ({"account_ids": [ACCOUNT], "readonly": True}, "STAGE8_10_7_TRADING_TOKEN_IS_READONLY"),
])
def test_session_details_fail_closed(tmp_path, details, code):
    put_switch(tmp_path)
    FakeAPI.details = details
    with pytest.raises(acceptance.TradingTokenAcceptanceError, match=f"^{code}$"):
        run(tmp_path)


def test_additional_different_scalar_accounts_are_allowed(tmp_path):
    put_switch(tmp_path)
    FakeAPI.details = {"account_ids": [5, ACCOUNT, "OTHER"], "readonly": False}
    assert run(tmp_path)["expected_account_occurrence_count"] == 1


@pytest.mark.parametrize(("post_action", "code"), [
    (lambda root: (root / "safety" / KILL_SWITCH_FILENAME).unlink(), "STAGE8_10_7_POST_KILL_SWITCH_INVALID"),
    (lambda root: put_switch(root, malformed=True), "STAGE8_10_7_POST_KILL_SWITCH_INVALID"),
    (lambda root: put_switch(root, state="ARMED"), "STAGE8_10_7_POST_KILL_SWITCH_NOT_HALTED"),
])
def test_post_auth_switch_change_fails(tmp_path, post_action, code):
    put_switch(tmp_path)
    class ChangingAPI(FakeAPI):
        def session_details(self):
            value = super().session_details()
            post_action(tmp_path)
            return value
    with pytest.raises(acceptance.TradingTokenAcceptanceError, match=f"^{code}$"):
        run(tmp_path, factory=ChangingAPI)


def test_report_writer_is_atomic_sanitized_and_creates_external_parent(tmp_path):
    runtime = tmp_path / "runtime"
    put_switch(runtime)
    report = run(runtime)
    destination = tmp_path / "evidence" / acceptance.REPORT_NAME
    acceptance.write_report(report, destination)
    body = destination.read_text(encoding="utf-8")
    assert SECRET not in body and ACCOUNT not in body
    assert json.loads(body) == report


def test_report_output_inside_repository_is_rejected_before_creation():
    destination = acceptance.REPOSITORY_ROOT / "should-not-exist" / acceptance.REPORT_NAME
    with pytest.raises(acceptance.TradingTokenAcceptanceError, match="^STAGE8_10_7_REPORT_REPOSITORY_OUTPUT_FORBIDDEN$"):
        acceptance.write_report({}, destination)
    assert not destination.parent.exists()


def test_report_path_requires_absolute_reserved_name(tmp_path):
    with pytest.raises(acceptance.TradingTokenAcceptanceError, match="REPORT_PATH_INVALID"):
        acceptance.write_report({}, tmp_path / "wrong.json")


def test_module_ast_has_only_allowed_finam_session_calls_and_no_network_imports():
    source = Path(acceptance.__file__).read_text(encoding="utf-8")
    tree = ast.parse(source)
    called = {node.func.attr for node in ast.walk(tree)
              if isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute)}
    forbidden = {"orders", "order", "place_order", "cancel_order", "submit_order", "modify_order",
                 "account", "assets", "assets_all_active", "asset", "params", "schedule", "bars"}
    imports = {alias.name for node in ast.walk(tree) if isinstance(node, (ast.Import, ast.ImportFrom))
               for alias in node.names}
    assert {"create_session", "session_details"}.issubset(called)
    assert not called.intersection(forbidden)
    assert not imports.intersection({"requests", "httpx", "socket", "http.client", "urllib.request"})
    assert "load_kill_switch" in source
    assert not hasattr(FakeAPI, "place_order")
