import ast
import json
from datetime import datetime, timezone
from pathlib import Path

import pytest

from TradingSystemLab.stage8_robot import trading_permission_boundary as boundary


READONLY_SECRET = "synthetic-readonly-secret"
TRADING_SECRET = "synthetic-trading-secret"
ACCOUNT = "SYNTHETIC-ACCOUNT-8104"


class FakeAPI:
    details_by_secret = {}
    fail_create = set()
    fail_details = set()
    calls = {}

    def __init__(self, secret):
        self.secret = secret
        self.calls.setdefault(secret, [])

    def create_session(self):
        self.calls[self.secret].append("create_session")
        if self.secret in self.fail_create:
            raise RuntimeError("sensitive transport detail")

    def session_details(self):
        self.calls[self.secret].append("session_details")
        if self.secret in self.fail_details:
            raise RuntimeError("sensitive transport detail")
        return self.details_by_secret[self.secret]


@pytest.fixture(autouse=True)
def reset_fake():
    FakeAPI.details_by_secret = {
        READONLY_SECRET: {"account_ids": [ACCOUNT], "readonly": True},
        TRADING_SECRET: {"account_ids": [ACCOUNT], "readonly": False},
    }
    FakeAPI.fail_create = set()
    FakeAPI.fail_details = set()
    FakeAPI.calls = {}


def run():
    return boundary.validate_permission_boundary(
        READONLY_SECRET,
        TRADING_SECRET,
        ACCOUNT,
        api_factory=FakeAPI,
        observed_utc=datetime(2026, 10, 3, tzinfo=timezone.utc),
    )


def test_exact_permission_boundary_pass_is_sanitized_and_session_only():
    report = run()
    serialized = json.dumps(report)
    assert report["readonly_token_readonly"] is True
    assert report["trading_token_readonly"] is False
    assert report["token_permission_boundary"] == "PASS"
    assert report["order_count"] == 0
    assert report["order_endpoint_called"] is False
    assert report["order_path_validation_performed"] is False
    assert report["stage8_10_5_status"] == "NOT_STARTED"
    assert READONLY_SECRET not in serialized and TRADING_SECRET not in serialized
    assert ACCOUNT not in serialized and "jwt" not in serialized.lower()
    assert FakeAPI.calls == {
        READONLY_SECRET: ["create_session", "session_details"],
        TRADING_SECRET: ["create_session", "session_details"],
    }


def test_additional_unrelated_scalar_accounts_pass():
    FakeAPI.details_by_secret[READONLY_SECRET]["account_ids"] = [42, ACCOUNT, "OTHER"]
    FakeAPI.details_by_secret[TRADING_SECRET]["account_ids"] = ["OTHER", ACCOUNT]
    assert run()["token_permission_boundary"] == "PASS"


@pytest.mark.parametrize(("secret", "value", "code"), [
    (READONLY_SECRET, False, "PERMISSION_BOUNDARY_READONLY_TOKEN_NOT_READONLY"),
    (TRADING_SECRET, True, "PERMISSION_BOUNDARY_TRADING_TOKEN_IS_READONLY"),
    (READONLY_SECRET, 1, "PERMISSION_BOUNDARY_READONLY_READONLY_NOT_EXACT_BOOL"),
    (READONLY_SECRET, "true", "PERMISSION_BOUNDARY_READONLY_READONLY_NOT_EXACT_BOOL"),
    (TRADING_SECRET, 0, "PERMISSION_BOUNDARY_TRADING_READONLY_NOT_EXACT_BOOL"),
    (TRADING_SECRET, "false", "PERMISSION_BOUNDARY_TRADING_READONLY_NOT_EXACT_BOOL"),
])
def test_readonly_value_fails_closed(secret, value, code):
    FakeAPI.details_by_secret[secret]["readonly"] = value
    with pytest.raises(boundary.PermissionBoundaryError, match=f"^{code}$"):
        run()


@pytest.mark.parametrize(("secret", "code"), [
    (READONLY_SECRET, "PERMISSION_BOUNDARY_READONLY_READONLY_MISSING"),
    (TRADING_SECRET, "PERMISSION_BOUNDARY_TRADING_READONLY_MISSING"),
])
def test_readonly_field_is_required(secret, code):
    del FakeAPI.details_by_secret[secret]["readonly"]
    with pytest.raises(boundary.PermissionBoundaryError, match=f"^{code}$"):
        run()


@pytest.mark.parametrize(("secret", "accounts", "suffix"), [
    (READONLY_SECRET, "bad", "ACCOUNT_IDS_MALFORMED"),
    (TRADING_SECRET, [None], "ACCOUNT_IDS_MALFORMED"),
    (READONLY_SECRET, ["OTHER"], "EXPECTED_ACCOUNT_NOT_ENUMERATED"),
    (TRADING_SECRET, ["OTHER"], "EXPECTED_ACCOUNT_NOT_ENUMERATED"),
    (READONLY_SECRET, [ACCOUNT, ACCOUNT], "EXPECTED_ACCOUNT_DUPLICATED"),
    (TRADING_SECRET, [ACCOUNT, ACCOUNT], "EXPECTED_ACCOUNT_DUPLICATED"),
])
def test_account_enumeration_fails_closed(secret, accounts, suffix):
    FakeAPI.details_by_secret[secret]["account_ids"] = accounts
    role = "READONLY" if secret == READONLY_SECRET else "TRADING"
    with pytest.raises(boundary.PermissionBoundaryError, match=f"^PERMISSION_BOUNDARY_{role}_{suffix}$"):
        run()


@pytest.mark.parametrize(("secret", "failure_set", "suffix"), [
    (READONLY_SECRET, "fail_create", "SESSION_CREATE_FAILED"),
    (TRADING_SECRET, "fail_create", "SESSION_CREATE_FAILED"),
    (READONLY_SECRET, "fail_details", "SESSION_DETAILS_FAILED"),
    (TRADING_SECRET, "fail_details", "SESSION_DETAILS_FAILED"),
])
def test_api_failures_are_sanitized(secret, failure_set, suffix):
    getattr(FakeAPI, failure_set).add(secret)
    role = "READONLY" if secret == READONLY_SECRET else "TRADING"
    with pytest.raises(boundary.PermissionBoundaryError, match=f"^PERMISSION_BOUNDARY_{role}_{suffix}$"):
        run()


def test_non_object_and_missing_account_ids_fail_closed():
    FakeAPI.details_by_secret[READONLY_SECRET] = []
    with pytest.raises(boundary.PermissionBoundaryError, match="SESSION_DETAILS_NOT_OBJECT"):
        run()
    FakeAPI.details_by_secret[READONLY_SECRET] = {"readonly": True}
    with pytest.raises(boundary.PermissionBoundaryError, match="ACCOUNT_IDS_MISSING"):
        run()


def test_required_inputs_fail_closed():
    for args, code in [
        (("", TRADING_SECRET, ACCOUNT), "READONLY_SECRET_MISSING"),
        ((READONLY_SECRET, "", ACCOUNT), "TRADING_SECRET_MISSING"),
        ((READONLY_SECRET, TRADING_SECRET, ""), "EXPECTED_ACCOUNT_MISSING"),
    ]:
        with pytest.raises(boundary.PermissionBoundaryError, match=code):
            boundary.validate_permission_boundary(*args, api_factory=FakeAPI)


def test_report_writer_enforces_external_reserved_filename(tmp_path):
    with pytest.raises(boundary.PermissionBoundaryError, match="REPORT_PATH_INVALID"):
        boundary.write_report(run(), tmp_path / "wrong.json")
    destination = tmp_path / boundary.REPORT_NAME
    boundary.write_report(run(), destination)
    body = destination.read_text()
    assert READONLY_SECRET not in body and TRADING_SECRET not in body
    assert ACCOUNT not in body and "jwt" not in body.lower()


def test_module_ast_has_exact_session_interaction_surface():
    source = Path(boundary.__file__).read_text()
    attributes = {
        node.func.attr for node in ast.walk(ast.parse(source))
        if isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute)
    }
    forbidden = {"orders", "order", "place_order", "cancel_order", "submit_order", "account",
                 "assets", "assets_all_active", "asset", "asset_params", "schedule", "bars"}
    assert not attributes.intersection(forbidden)
    assert {"create_session", "session_details"}.issubset(attributes)
    assert not hasattr(FakeAPI, "place_order")
