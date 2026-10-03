import ast
import json
from datetime import datetime, timezone
from pathlib import Path

import pytest

from TradingSystemLab.stage8_robot import trading_identity_binding as binding


SECRET = "synthetic-secret-never-real"
ACCOUNT = "SYNTHETIC-ACCOUNT-8103"


class FakeAPI:
    details = {"account_ids": [ACCOUNT]}
    fail_create = False
    calls = []

    def __init__(self, secret):
        assert secret == SECRET

    def create_session(self):
        self.calls.append("create_session")
        if self.fail_create:
            raise RuntimeError("sensitive transport detail")

    def session_details(self):
        self.calls.append("session_details")
        return self.details


@pytest.fixture(autouse=True)
def reset_fake():
    FakeAPI.details = {"account_ids": [ACCOUNT]}
    FakeAPI.fail_create = False
    FakeAPI.calls = []


def run():
    return binding.validate_identity_binding(
        SECRET, ACCOUNT, api_factory=FakeAPI,
        observed_utc=datetime(2026, 10, 3, tzinfo=timezone.utc),
    )


def test_valid_session_is_sanitized_pass():
    report = run()
    serialized = json.dumps(report)
    assert report["identity_account_binding"] == "PASS"
    assert report["order_count"] == 0
    assert report["stage8_10_4_status"] == "NOT_STARTED"
    assert report["stage8_11_status"] == report["stage8_12_status"] == "NOT_STARTED_NOT_AUTHORIZED"
    assert SECRET not in serialized and ACCOUNT not in serialized and "jwt" not in serialized.lower()
    assert FakeAPI.calls == ["create_session", "session_details"]


def test_expected_account_among_distinct_accounts_passes():
    FakeAPI.details = {"account_ids": ["OTHER", ACCOUNT, 42]}
    assert run()["enumerated_account_count"] == 3


@pytest.mark.parametrize(("details", "code"), [
    ({"account_ids": ["OTHER"]}, "TRADING_IDENTITY_EXPECTED_ACCOUNT_NOT_ENUMERATED"),
    ({"account_ids": [ACCOUNT, ACCOUNT]}, "TRADING_IDENTITY_EXPECTED_ACCOUNT_DUPLICATED"),
    ({}, "TRADING_IDENTITY_ACCOUNT_IDS_MISSING"),
    ({"account_ids": "not-a-list"}, "TRADING_IDENTITY_ACCOUNT_IDS_MALFORMED"),
    ({"account_ids": [None]}, "TRADING_IDENTITY_ACCOUNT_IDS_MALFORMED"),
    ([], "TRADING_IDENTITY_SESSION_DETAILS_NOT_OBJECT"),
])
def test_schema_failures_are_deterministic(details, code):
    FakeAPI.details = details
    with pytest.raises(binding.IdentityBindingError, match=f"^{code}$"):
        run()


def test_session_creation_failure_is_sanitized():
    FakeAPI.fail_create = True
    with pytest.raises(binding.IdentityBindingError, match="^TRADING_IDENTITY_SESSION_CREATE_FAILED$"):
        run()
    assert FakeAPI.calls == ["create_session"]


def test_report_writer_rejects_wrong_filename_and_writes_sanitized_report(tmp_path):
    with pytest.raises(binding.IdentityBindingError, match="REPORT_PATH_INVALID"):
        binding.write_report(run(), tmp_path / "wrong.json")
    destination = tmp_path / "stage8_10_3_identity_account_binding.json"
    binding.write_report(run(), destination)
    body = destination.read_text()
    assert SECRET not in body and ACCOUNT not in body and "jwt" not in body.lower()


def test_module_ast_has_only_session_interaction_surface():
    source = Path(binding.__file__).read_text()
    attributes = {node.func.attr for node in ast.walk(ast.parse(source))
                  if isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute)}
    assert attributes.intersection({"place_order", "cancel_order", "submit_order", "orders", "order",
                                    "account", "assets", "asset", "asset_params", "schedule", "bars"}) == set()
    assert {"create_session", "session_details"}.issubset(attributes)
    assert "/orders" not in source
