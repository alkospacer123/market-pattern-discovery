from pathlib import Path
import json
import sys

import pytest

from TradingSystemLab.stage8_robot import final_operational_audit as final
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from TradingSystemLab.stage8_robot import audit_stage8 as stage8


ROOT = Path(__file__).resolve().parents[3]
PASS_STAGE7 = {
    "status": "PASS", "errors": [], "checks": 22, "mutation_test_count": 19,
    "production_specification_id": final.SPEC_ID,
}
PASS_STAGE8 = {
    "status": "PASS", "errors": [], "checks": 139,
    "production_specification_id": final.SPEC_ID, "live_trading_activated": False,
}


def run_audit(overrides=None, tracked=None):
    return final.audit(
        ROOT,
        write_result=False,
        text_overrides=overrides,
        tracked_files=tracked if tracked is not None else git_files(),
        stage7_result=PASS_STAGE7,
        stage8_result=PASS_STAGE8,
    )


def git_files():
    import subprocess
    output = subprocess.run(["git", "ls-files"], cwd=ROOT, check=True, capture_output=True, text=True).stdout
    return output.splitlines()


def source(relative):
    return (ROOT / relative).read_text()


def test_clean_repository_authority_passes():
    result = run_audit()
    assert result["status"] == "PASS"
    assert result["checks"] > 0
    assert result["intel_final_acceptance_performed"] is True
    assert result["stage8_8_7_accepted_code_commit"] == final.STAGE_8_8_7_CODE
    assert result["stage8_8_7_external_evidence_sha256"] == final.STAGE_8_8_7_EVIDENCE


def test_wrong_production_id_fails():
    path = "TradingSystemLab/results/post_v3_analysis/stage7_production_specification_freeze/production_specification.json"
    result = run_audit({path: source(path).replace(final.SPEC_ID, "PROD_STAGE7_WRONG")})
    assert "PRODUCTION_SPECIFICATION_ID_EXACT" in result["errors"]


def test_changed_protected_implementation_hash_fails():
    path = "TradingSystemLab/stage8_robot/readonly_supervisor.py"
    result = run_audit({path: source(path) + "\n# mutation\n"})
    assert any(error.startswith("PROTECTED_IMPLEMENTATION_HASHES:") for error in result["errors"])


def test_crlf_protected_implementation_hashes_pass():
    paths = (
        "TradingSystemLab/stage8_robot/readonly_supervisor.py",
        "TradingSystemLab/stage8_robot/deploy/windows/run-readonly.ps1",
        "TradingSystemLab/results/post_v3_analysis/stage7_production_specification_freeze/production_specification.json",
        "TradingSystemLab/stage8_robot/production_instrument_registry.csv",
    )
    overrides = {path: source(path).replace("\n", "\r\n") for path in paths}

    result = run_audit(overrides)

    assert result["protected_implementation_status"] == "PASS"
    assert not any(error.startswith("PROTECTED_IMPLEMENTATION_HASHES:") for error in result["errors"])


STAGE_8_10_3_IMPLEMENTATION_PATHS = (
    Path("trading_identity_binding.py"),
    Path("deploy/windows/validate-trading-identity-binding.ps1"),
)

STAGE_8_10_4_IMPLEMENTATION_PATHS = (
    Path("trading_permission_boundary.py"),
    Path("deploy/windows/validate-trading-permission-boundary.ps1"),
)

STAGE_8_10_5_IMPLEMENTATION_PATHS = (
    Path("order_path_dry_validation.py"),
    Path("deploy/windows/validate-order-path-dry.ps1"),
)


@pytest.mark.parametrize("newline", [b"\n", b"\r\n"])
def test_stage8_independent_audit_accepts_canonical_and_crlf_implementation_files(
        monkeypatch, newline):
    original_read_bytes = Path.read_bytes
    protected = {stage8.HERE / relative for relative in STAGE_8_10_3_IMPLEMENTATION_PATHS}

    def read_bytes_with_newlines(path):
        raw = original_read_bytes(path)
        if path in protected:
            canonical = raw.replace(b"\r\n", b"\n")
            return canonical.replace(b"\n", newline)
        return raw

    monkeypatch.setattr(Path, "read_bytes", read_bytes_with_newlines)
    result = stage8.audit(write_result=False)

    assert result["status"] == "PASS"
    assert "STAGE_8_10_3_IMPLEMENTATION_HASHES" not in result["errors"]


def test_stage8_independent_audit_rejects_content_mutation_despite_canonical_hashing(
        monkeypatch):
    original_read_bytes = Path.read_bytes
    protected = {stage8.HERE / relative for relative in STAGE_8_10_3_IMPLEMENTATION_PATHS}

    def read_bytes_with_mutation(path):
        raw = original_read_bytes(path)
        if path in protected:
            return raw + b"# semantic mutation\n"
        return raw

    monkeypatch.setattr(Path, "read_bytes", read_bytes_with_mutation)
    result = stage8.audit(write_result=False)

    assert "STAGE_8_10_3_IMPLEMENTATION_HASHES" in result["errors"]


@pytest.mark.parametrize("newline", [b"\n", b"\r\n"])
def test_stage8_8104_hashes_accept_lf_and_crlf(monkeypatch, newline):
    original_read_bytes = Path.read_bytes
    protected = {stage8.HERE / relative for relative in STAGE_8_10_4_IMPLEMENTATION_PATHS}

    def read_bytes_with_newlines(path):
        raw = original_read_bytes(path)
        if path in protected:
            return raw.replace(b"\r\n", b"\n").replace(b"\n", newline)
        return raw

    monkeypatch.setattr(Path, "read_bytes", read_bytes_with_newlines)
    result = stage8.audit(write_result=False)
    assert "STAGE_8_10_4_IMPLEMENTATION_HASHES" not in result["errors"]


def test_stage8_8104_hashes_reject_semantic_mutation(monkeypatch):
    original_read_bytes = Path.read_bytes
    protected = {stage8.HERE / relative for relative in STAGE_8_10_4_IMPLEMENTATION_PATHS}

    def read_bytes_with_mutation(path):
        raw = original_read_bytes(path)
        return raw + b"# semantic mutation\n" if path in protected else raw

    monkeypatch.setattr(Path, "read_bytes", read_bytes_with_mutation)
    result = stage8.audit(write_result=False)
    assert "STAGE_8_10_4_IMPLEMENTATION_HASHES" in result["errors"]


@pytest.mark.parametrize("newline", [b"\n", b"\r\n"])
def test_stage8_8105_hashes_accept_lf_and_crlf(monkeypatch, newline):
    original = Path.read_bytes
    protected = {stage8.HERE / relative for relative in STAGE_8_10_5_IMPLEMENTATION_PATHS}
    monkeypatch.setattr(Path, "read_bytes", lambda path: (
        original(path).replace(b"\r\n", b"\n").replace(b"\n", newline)
        if path in protected else original(path)))
    assert "STAGE_8_10_5_IMPLEMENTATION_HASHES" not in stage8.audit(write_result=False)["errors"]


def test_stage8_8105_hashes_reject_semantic_mutation(monkeypatch):
    original = Path.read_bytes
    protected = {stage8.HERE / relative for relative in STAGE_8_10_5_IMPLEMENTATION_PATHS}
    monkeypatch.setattr(Path, "read_bytes", lambda path: (
        original(path) + b"# semantic mutation\n" if path in protected else original(path)))
    assert "STAGE_8_10_5_IMPLEMENTATION_HASHES" in stage8.audit(write_result=False)["errors"]


def test_stage_8_10_5_machine_authority_mutations_fail_independent_audit():
    path = ROOT / "TradingSystemLab/stage8_robot/authority_provenance.json"
    authority = json.loads(path.read_text())
    mutations = [
        ("status", "STAGE_8_10_5_ORDER_PATH_DRY_VALIDATION_CODE_READY_PENDING_PHYSICAL_VALIDATION"),
        ("status", "NOT_STARTED"), ("accepted_code_commit", "changed"),
        ("external_evidence_sha256", "changed"), ("physical_result", "changed"),
        ("physical_validation_performed", False), ("offline_dry_validation_performed", False),
        ("order_path_dry_validation_validated", False), ("mode", "changed"),
        ("frozen_n4_symbol_count", 3), ("broker_payload_case_count", 15),
        ("broker_payload_validation", "FAIL"), ("client_order_id_validation", "FAIL"),
        ("market_order_type", "LIMIT"), ("transport_serialization_validation", "FAIL"),
        ("synthetic_order_post_constructed", False), ("synthetic_order_post_count", 2),
        ("uncertain_submission_validation", "FAIL"),
        ("uncertain_submission_order_post_count", 2), ("automatic_order_post_retry_count", 1),
        ("external_network_calls", 1), ("real_account_id_used", True),
        ("readonly_token_used_for_stage8_10_5", True),
        ("trading_token_used_for_stage8_10_5", True),
        ("finam_authentication_performed_for_stage8_10_5", True),
        ("real_order_endpoint_called", True), ("real_order_count", 1),
        ("live_trading_authorized", True), ("real_order_transmission_authorized", True),
        ("stage8_10_status", "COMPLETE"), ("stage8_10_6_status", "STARTED"),
        ("stage8_10_7_through_8_status", "STARTED"),
        ("stage8_11_status", "AUTHORIZED"), ("stage8_12_status", "AUTHORIZED"),
    ]
    for key, value in mutations:
        changed = json.loads(json.dumps(authority))
        changed["stage8_10_5"][key] = value
        result = stage8.audit(write_result=False, authority_text=json.dumps(changed))
        assert "STAGE_8_10_5_MACHINE_AUTHORITY_EXACT" in result["errors"], key


def test_stage_8_10_5_physical_report_tracking_fails_independent_audit():
    tracked = git_files() + ["external/stage8_10_5_order_path_dry_validation.json"]
    result = stage8.audit(write_result=False, tracked_files=tracked)
    assert "STAGE_8_10_5_PHYSICAL_EVIDENCE_NOT_TRACKED" in result["errors"]


@pytest.mark.parametrize("relative,mutation", [
    ("deploy/windows/validate-order-path-dry.ps1", "\n. .\\credential-store.ps1\n"),
    ("deploy/windows/validate-order-path-dry.ps1", "\nInvoke-WebRequest https://example.invalid\n"),
    ("order_path_dry_validation.py", "\n# transport=transport removed\n"),
    ("deploy/windows/validate-order-path-dry.ps1",
     "\n& $Python -m TradingSystemLab.stage8_robot.readonly_supervisor "
     "--runtime-root C:\\TradingSystemLab\\runtime\\robot.sqlite3-wal-shm\n"),
])
def test_stage_8_10_5_semantic_offline_guard_mutations_fail(
        monkeypatch, relative, mutation):
    target = stage8.HERE / relative
    original_read_text = Path.read_text

    def mutated_read_text(path, *args, **kwargs):
        text = original_read_text(path, *args, **kwargs)
        if path == target:
            if relative == "order_path_dry_validation.py":
                return text.replace("transport=transport", "transport = synthetic")
            return text + mutation
        return text

    monkeypatch.setattr(Path, "read_text", mutated_read_text)
    result = stage8.audit(write_result=False)
    assert "STAGE_8_10_5_OFFLINE_NOT_RUNTIME_WIRED" in result["errors"]


def test_stage_8_10_5_repository_output_guard_is_required(monkeypatch):
    target = stage8.HERE / "order_path_dry_validation.py"
    original_read_text = Path.read_text

    def mutated_read_text(path, *args, **kwargs):
        text = original_read_text(path, *args, **kwargs)
        return text.replace("REPOSITORY_OUTPUT_FORBIDDEN", "OUTPUT_GUARD_REMOVED") if path == target else text

    monkeypatch.setattr(Path, "read_text", mutated_read_text)
    assert "STAGE_8_10_5_OFFLINE_NOT_RUNTIME_WIRED" in stage8.audit(write_result=False)["errors"]


def test_missing_stage_8_8_5_evidence_sha_fails():
    path = "TradingSystemLab/CURRENT_STATE.md"
    result = run_audit({path: source(path).replace(final.STAGE_8_8_5_EVIDENCE, "MISSING")})
    assert "STAGE_8_8_5_PROVENANCE_SYNCHRONIZED" in result["errors"]


def test_missing_stage_8_8_6_evidence_sha_fails():
    path = "TradingSystemLab/ROADMAP.md"
    result = run_audit({path: source(path).replace(final.STAGE_8_8_6_EVIDENCE, "MISSING")})
    assert "STAGE_8_8_6_PROVENANCE_SYNCHRONIZED" in result["errors"]


def test_operational_hardening_completion_regression_fails():
    overrides = {
        path: source(path).replace(final.HARDENING_COMPLETE, "Stage 8.8 operational hardening is INCOMPLETE.")
        for path in (
            "TradingSystemLab/CURRENT_STATE.md",
            "TradingSystemLab/ROADMAP.md",
            "TradingSystemLab/stage8_robot/README.md",
        )
    }
    result = run_audit(overrides)
    assert result["status"] == "FAIL"
    assert "STAGE_8_8_OPERATIONAL_HARDENING_COMPLETE" in result["errors"]


def test_individual_stage_lifecycle_regression_fails():
    paths = (
        "TradingSystemLab/CURRENT_STATE.md",
        "TradingSystemLab/ROADMAP.md",
        "TradingSystemLab/stage8_robot/README.md",
    )
    overrides = {
        path: source(path).replace("8.8.2,", "8.8.2 (INCOMPLETE),")
        for path in paths
    }

    assert all(final.HARDENING_COMPLETE in doc for doc in overrides.values())
    assert all(
        "8.8.5, 8.8.6, and 8.8.7 are COMPLETE." in " ".join(doc.split())
        for doc in overrides.values()
    )
    assert all(final.STAGE_8_9_STATUS in doc
               for doc in overrides.values())

    result = run_audit(overrides)
    assert result["status"] == "FAIL"
    assert "STAGE_8_8_1_THROUGH_8_8_7_COMPLETE" in result["errors"]
    assert "STAGE_8_8_OPERATIONAL_HARDENING_COMPLETE" not in result["errors"]


def test_tracked_runtime_and_raw_acceptance_artifacts_fail():
    forbidden = [
        "state/live.sqlite3", "state/live.sqlite3-wal", "state/live.sqlite3-shm",
        "secrets/live.dpapi", "stage8_8_7_intel_acceptance.json",
    ]
    result = run_audit(tracked=git_files() + forbidden)
    assert result["runtime_artifacts_tracked"] == sorted(forbidden)
    assert "RUNTIME_OR_SECRET_ARTIFACT_TRACKED" in result["errors"]


def test_live_authorization_mutation_fails():
    path = "TradingSystemLab/stage8_robot/config.py"
    result = run_audit({path: source(path).replace("LIVE_TRADING_NOT_AUTHORIZED", "LIVE_TRADING_AUTHORIZED")})
    assert "LIVE_TRADING_BLOCKED" in result["errors"]


def test_real_order_authorization_mutation_fails():
    path = "TradingSystemLab/stage8_robot/broker.py"
    result = run_audit({path: source(path).replace("REAL_ORDER_TRANSMISSION_NOT_AUTHORIZED", "REAL_ORDER_TRANSMISSION_AUTHORIZED")})
    assert "REAL_ORDER_TRANSMISSION_BLOCKED" in result["errors"]


def test_stage_8_9_completed_status_removed_fails():
    path = "TradingSystemLab/CURRENT_STATE.md"
    result = run_audit({path: source(path).replace(final.STAGE_8_9_STATUS, "MISSING")})
    assert "STAGE_8_9_10_COMPLETED_PROVENANCE_SYNCHRONIZED" in result["errors"]


def test_stage_8_9_10_physical_provenance_mutations_fail():
    path = "TradingSystemLab/CURRENT_STATE.md"
    for value in (final.STAGE_8_9_CODE, final.STAGE_8_9_REPORT,
                  final.STAGE_8_9_SUMMARY, final.STAGE_8_9_REASON):
        result = run_audit({path: source(path).replace(value, "WRONG")})
        assert "STAGE_8_9_10_COMPLETED_PROVENANCE_SYNCHRONIZED" in result["errors"]


def test_stage_8_9_capacity_counts_mutations_fail():
    path = "TradingSystemLab/CURRENT_STATE.md"
    for value in ("sizing_case_count = 8", "positive_capacity_case_count = 4", "zero_capacity_case_count = 4",
                  "positive_batch_reservation_count = 1"):
        result = run_audit({path: source(path).replace(value, "capacity count missing")})
        assert "STAGE_8_9_10_COMPLETED_PROVENANCE_SYNCHRONIZED" in result["errors"]


def test_stage_8_9_marked_incomplete_fails():
    path = "TradingSystemLab/CURRENT_STATE.md"
    result = run_audit({path: source(path).replace(
        "Stage 8.9 is **COMPLETE**", "Stage 8.9 is **NOT COMPLETE**")})
    assert "STAGE_8_9_COMPLETE_SYNCHRONIZED" in result["errors"]


def test_stage_8_9_appended_active_incomplete_contradiction_fails():
    path = "TradingSystemLab/CURRENT_STATE.md"
    mutation = source(path) + "\n\nStage 8.9 is **NOT COMPLETE**.\n"
    result = run_audit({path: mutation})
    assert "STAGE_8_9_NO_ACTIVE_LIFECYCLE_CONTRADICTION" in result["errors"]


def test_stage_8_10_1_status_removed_or_changed_fails():
    path = "TradingSystemLab/CURRENT_STATE.md"
    result = run_audit({path: source(path).replace(final.STAGE_8_10_1_STATUS, "MISSING")})
    assert "STAGE_8_10_1_COMPLETE_SYNCHRONIZED" in result["errors"]


def test_stage_8_10_falsely_complete_fails():
    path = "TradingSystemLab/CURRENT_STATE.md"
    result = run_audit({path: source(path).replace(
        "Stage 8.10 is **IN PROGRESS**", "Stage 8.10 is **COMPLETE**")})
    assert "STAGE_8_10_IN_PROGRESS_NOT_COMPLETE" in result["errors"]


def test_stage_8_10_2_complete_status_mutation_fails():
    path = "TradingSystemLab/CURRENT_STATE.md"
    result = run_audit({path: source(path).replace(
        "Stage 8.10.2 is **COMPLETE**",
        "Stage 8.10.2 is **CODE READY / PENDING PHYSICAL PROVISIONING**")})
    assert "STAGE_8_10_2_COMPLETE_SYNCHRONIZED" in result["errors"]


def test_top_level_readme_current_status_regressions_fail_both_audits():
    path = "TradingSystemLab/stage8_robot/README.md"
    original = source(path)
    rejected = (
        final.STAGE_8_9_STATUS,
        final.STAGE_8_10_1_STATUS,
        "STAGE_8_10_2_SECURE_PROVISIONING_CODE_READY_PENDING_PHYSICAL_PROVISIONING",
        "STAGE_8_10_COMPLETE",
        "STAGE_8_10_3_TRADING_AUTHENTICATION_COMPLETE",
        "STAGE_8_10_3_IDENTITY_ACCOUNT_BINDING_CODE_READY_PENDING_PHYSICAL_VALIDATION",
        "NOT_STARTED",
    )
    for status in rejected:
        mutation = original.replace(final.STAGE_8_10_7_STATUS, status, 1)
        result = run_audit({path: mutation})
        assert "STAGE_8_ROBOT_README_CURRENT_STATUS_EXACT" in result["errors"]
        stage8_result = stage8.audit(write_result=False, readme_text=mutation)
        assert "STAGE_8_ROBOT_README_CURRENT_STATUS_EXACT" in stage8_result["errors"]


def test_stage_8_10_6_machine_authority_mutations_fail_independent_audit():
    authority = json.loads((ROOT / "TradingSystemLab/stage8_robot/authority_provenance.json").read_text())
    mutations = [
        ("status", "STAGE_8_10_6_KILL_SWITCH_SAFETY_GATES_CODE_READY_PENDING_PHYSICAL_VALIDATION"),
        ("status", "NOT_STARTED"), ("accepted_code_commit", "0" * 40),
        ("external_evidence_sha256", "0" * 64), ("physical_result", "FAIL"),
        ("physical_validation_performed", False), ("production_kill_switch_initialized", False),
        ("production_kill_switch_halted_observed", False), ("production_kill_switch_final_state", "ARMED"),
        ("production_kill_switch_valid", False), ("synthetic_safety_matrix_validated", False),
        ("synthetic_case_count", 24), ("synthetic_open_case_count", 2),
        ("synthetic_blocked_case_count", 23), ("synthetic_matrix_validation", "FAIL"),
        ("emergency_halt_validated", False), ("missing_switch_fail_closed", False),
        ("malformed_switch_fail_closed", False), ("execution_authorization_required", False),
        ("heartbeat_health_gate_validated", False), ("reconciliation_gate_validated", False),
        ("unresolved_order_gate_validated", False), ("heartbeat_freshness_gate_validated", False),
        ("api_contact_freshness_gate_validated", False), ("account_hash_shape_gate_validated", False),
        ("execution_authorized", True), ("real_account_id_used", True),
        ("readonly_token_used_for_stage8_10_6", True), ("trading_token_used_for_stage8_10_6", True),
        ("finam_authentication_performed_for_stage8_10_6", True),
        ("external_network_calls", 1), ("real_order_endpoint_called", True), ("real_order_count", 1),
        ("live_trading_authorized", True), ("real_order_transmission_authorized", True),
        ("stage8_10_status", "COMPLETE"), ("stage8_10_7_status", "STARTED"),
        ("stage8_10_8_status", "STARTED"), ("stage8_11_status", "AUTHORIZED"),
        ("stage8_12_status", "AUTHORIZED"),
    ]
    for key, value in mutations:
        changed = json.loads(json.dumps(authority)); changed["stage8_10_6"][key] = value
        result = stage8.audit(write_result=False, authority_text=json.dumps(changed))
        assert "STAGE_8_10_6_MACHINE_AUTHORITY_EXACT" in result["errors"], key


def test_stage_8_10_6_external_files_are_rejected():
    for name in ("stage8-trading-kill-switch.json", "stage8_10_6_safety_gate_validation.json"):
        result = stage8.audit(write_result=False, tracked_files=git_files() + ["external/" + name])
        assert "STAGE_8_10_6_EXTERNAL_ARTIFACTS_NOT_TRACKED" in result["errors"]


def test_stage_8_10_7_machine_authority_mutations_fail_independent_audit():
    authority = json.loads((ROOT / "TradingSystemLab/stage8_robot/authority_provenance.json").read_text())
    mutations = [
        ("status", "STAGE_8_10_7_INTEL_TRADING_TOKEN_ACCEPTANCE_CODE_READY_PENDING_PHYSICAL_VALIDATION"),
        ("status", "NOT_STARTED"), ("accepted_code_commit", "0" * 40),
        ("external_evidence_sha256", "0" * 64), ("physical_result", "FAIL"),
        ("physical_validation_performed", False), ("trading_dpapi_current_user_validated", False),
        ("local_readonly_trading_account_binding_validated", False),
        ("production_kill_switch_pre_halted_observed", False), ("trading_session_created", False),
        ("expected_account_enumerated", False), ("expected_account_occurrence_count", 0),
        ("trading_token_readonly_false_observed", False), ("trading_token_write_boundary_confirmed", False),
        ("remote_call_scope", "SESSION_CREATE_ONLY"),
        ("production_kill_switch_post_halted_observed", False), ("trading_token_used", False),
        ("readonly_token_used_for_remote_auth", True), ("finam_authentication_performed", False),
        ("order_endpoint_called", True), ("order_count", 1), ("execution_authorized", True),
        ("live_trading_authorized", True), ("real_order_transmission_authorized", True),
        ("stage8_10_status", "COMPLETE"), ("stage8_10_8_status", "STARTED"),
        ("stage8_11_status", "AUTHORIZED"), ("stage8_12_status", "AUTHORIZED"),
    ]
    for key, value in mutations:
        changed = json.loads(json.dumps(authority)); changed["stage8_10_7"][key] = value
        result = stage8.audit(write_result=False, authority_text=json.dumps(changed))
        assert "STAGE_8_10_7_MACHINE_AUTHORITY_EXACT" in result["errors"], key


def _assert_stage_8_10_7_semantic_failure(relative, mutation, error):
    full = "TradingSystemLab/stage8_robot/" + relative
    assert error in run_audit({full: mutation})["errors"]
    assert error in stage8.audit(write_result=False, source_overrides={relative: mutation})["errors"]


def _stage_8_10_7_source(relative):
    return source("TradingSystemLab/stage8_robot/" + relative)


@pytest.mark.parametrize("payload", [
    "api.orders()", "api.order()", "api.place_order()", "api.cancel_order()", "api.submit_order()",
    "api.modify_order()", "from . import broker", "from . import runner", "from . import operations",
    "from . import reconciliation", "import requests", "import httpx",
    "import socket", "import http.client", "import urllib.request\nurllib.request.urlopen('https://invalid')",
])
def test_stage_8_10_7_forbidden_session_capability_mutations_fail(payload):
    relative = "trading_token_intel_acceptance.py"
    mutation = _stage_8_10_7_source(relative) + "\n" + payload + "\n"
    _assert_stage_8_10_7_semantic_failure(relative, mutation, "STAGE_8_10_7_SESSION_ONLY_NO_ORDER_CAPABILITY")


@pytest.mark.parametrize(("before", "after"), [
    ("api.create_session()", "pass"), ("api.session_details()", "{}"),
    ("local_account_binding_confirmed is not True", "False"),
    ('type(details["readonly"]) is not bool', "False"),
    ('details["readonly"] is not False', "False"), ("occurrences != 1", "False"),
    ("occurrences = [str(value) for value in account_ids].count(str(expected_account))", "occurrences = 1"),
    ("REPOSITORY_OUTPUT_FORBIDDEN", "REPOSITORY_OUTPUT_ALLOWED"),
])
def test_stage_8_10_7_fail_closed_diagnostic_mutations_fail(before, after):
    relative = "trading_token_intel_acceptance.py"
    original = _stage_8_10_7_source(relative)
    assert before in original
    _assert_stage_8_10_7_semantic_failure(relative, original.replace(before, after), "STAGE_8_10_7_SESSION_ONLY_NO_ORDER_CAPABILITY")


@pytest.mark.parametrize("payload", [
    "$env:FINAM_API_SECRET = 'x'", "$env:FINAM_REAL_ACCOUNT_ID = 'x'",
    "$env:FINAM_TRADING_API_SECRET = 'x'", "$env:FINAM_TRADING_ACCOUNT_ID = 'x'",
    "$env:FINAM_PERMISSION_READONLY_API_SECRET = 'x'",
    "$env:FINAM_API_SECRET = $readonlyCredential.finam_api_secret",
    "$env:FINAM_8107_READONLY_API_SECRET = $readonlyCredential.finam_api_secret",
    "$env:FINAM_8107_TRADING_API_SECRET = $readonlyCredential.finam_api_secret",
])
def test_stage_8_10_7_wrapper_capability_mutations_fail(payload):
    relative = "deploy/windows/validate-trading-token-intel-acceptance.ps1"
    mutation = _stage_8_10_7_source(relative) + "\n" + payload + "\n"
    _assert_stage_8_10_7_semantic_failure(relative, mutation, "STAGE_8_10_7_WRAPPER_CREDENTIAL_BOUNDARY")


@pytest.mark.parametrize("payload", [
    "Enable-ScheduledTask x", "Start-ScheduledTask x", "Register-ScheduledTask x", "Set-ScheduledTask x",
    "write_kill_switch", "emergency_halt", "$allow_arm=$true", "$execution_authorized=true",
    "place_order()", "submit_order()", "cancel_order()", "modify_order()", "orders()",
    "run-readonly", "install-task", "readonly_supervisor", "runner", "broker",
    "order_path_dry_validation", "validate-order-path-dry", "Invoke-WebRequest https://invalid",
    "Invoke-RestMethod https://invalid", "curl https://invalid", "wget https://invalid",
])
def test_stage_8_10_7_wrapper_runtime_mutations_fail(payload):
    relative = "deploy/windows/validate-trading-token-intel-acceptance.ps1"
    mutation = _stage_8_10_7_source(relative) + "\n" + payload + "\n"
    _assert_stage_8_10_7_semantic_failure(relative, mutation, "STAGE_8_10_7_WRAPPER_NOT_RUNTIME_WIRED")


def test_stage_8_10_7_wrapper_binding_and_ordering_mutations_fail():
    relative = "deploy/windows/validate-trading-token-intel-acceptance.ps1"
    original = _stage_8_10_7_source(relative)
    for term in ("finam_real_account_id -cne", "$env:FINAM_8107_TRADING_API_SECRET"):
        _assert_stage_8_10_7_semantic_failure(relative, original.replace(term, "removed", 1),
                                              "STAGE_8_10_7_WRAPPER_CREDENTIAL_BOUNDARY")
    source = "$env:FINAM_8107_TRADING_API_SECRET = [string]$tradingCredential.finam_trading_api_secret"
    mutation = original.replace(source, "$env:FINAM_8107_TRADING_API_SECRET = [string]$readonlyCredential.finam_api_secret")
    _assert_stage_8_10_7_semantic_failure(relative, mutation, "STAGE_8_10_7_WRAPPER_CREDENTIAL_BOUNDARY")


def test_stage_8_10_7_kill_switch_mutations_fail():
    relative = "trading_token_intel_acceptance.py"
    original = _stage_8_10_7_source(relative)
    for term in ('_halted_switch(runtime_root)\n', '_halted_switch(runtime_root, post=True)\n'):
        assert term in original
        _assert_stage_8_10_7_semantic_failure(relative, original.replace(term, "", 1),
                                              "STAGE_8_10_7_KILL_SWITCH_HALTED_REQUIRED")


def test_stage_8_10_7_wrapper_ordering_mutations_fail():
    relative = "deploy/windows/validate-trading-token-intel-acceptance.ps1"
    original = _stage_8_10_7_source(relative)
    halt = "    Assert-KillSwitchHalted\n"
    store = '    . (Join-Path $PSScriptRoot "credential-store.ps1")\n'
    moved_credentials = original.replace(halt, "", 1).replace(store, store + halt, 1)
    _assert_stage_8_10_7_semantic_failure(relative, moved_credentials, "STAGE_8_10_7_WRAPPER_NOT_RUNTIME_WIRED")
    child = "    & $Python -m TradingSystemLab.stage8_robot.trading_token_intel_acceptance --runtime-root $runtime --report $ReportPath\n"
    comparison = "    if ([string]$readonlyCredential.finam_real_account_id -cne [string]$tradingCredential.finam_real_account_id) {\n        throw \"STAGE8_10_7_LOCAL_ACCOUNT_MISMATCH\"\n    }\n"
    moved_child = original.replace(child, "", 1).replace(comparison, child + comparison, 1)
    _assert_stage_8_10_7_semantic_failure(relative, moved_child, "STAGE_8_10_7_WRAPPER_NOT_RUNTIME_WIRED")
    post = original.rfind(halt)
    _assert_stage_8_10_7_semantic_failure(relative, original[:post] + original[post + len(halt):],
                                          "STAGE_8_10_7_WRAPPER_NOT_RUNTIME_WIRED")
    post_host = original.rfind("    Assert-HostSafe\n")
    _assert_stage_8_10_7_semantic_failure(relative, original[:post_host] + original[post_host + 20:],
                                          "STAGE_8_10_7_WRAPPER_NOT_RUNTIME_WIRED")


@pytest.mark.parametrize("term", ['foreach ($name in $stageEnvironment) { Remove-Item "Env:$name" -ErrorAction SilentlyContinue }',
                                  '$readonlyCredential = $null\n    $tradingCredential = $null', '    Pop-Location\n'])
def test_stage_8_10_7_wrapper_cleanup_mutations_fail(term):
    relative = "deploy/windows/validate-trading-token-intel-acceptance.ps1"
    original = _stage_8_10_7_source(relative)
    assert term in original
    _assert_stage_8_10_7_semantic_failure(relative, original.replace(term, "", 1),
                                          "STAGE_8_10_7_CLEANUP_CONTRACT")


def test_stage_8_10_7_report_contract_mutation_fails():
    relative = "trading_token_intel_acceptance.py"
    original = _stage_8_10_7_source(relative)
    for term in ("stage8_10_7_intel_trading_token_acceptance.v1", "INTEL_TRADING_TOKEN_SESSION_ACCEPTANCE_NO_ORDER",
                 '"local_readonly_trading_account_match": True', '"trading_dpapi_current_user_validated": True',
                 '"trading_credential_production_id_validated": True', '"production_kill_switch_pre_valid": True',
                 '"production_kill_switch_pre_state": "HALTED"', '"trading_session_created": True',
                 '"expected_account_enumerated": True', '"expected_account_occurrence_count": 1',
                 '"trading_token_readonly": False', '"trading_token_write_boundary_confirmed": True',
                 "SESSION_CREATE_AND_DETAILS_ONLY", '"production_kill_switch_post_valid": True',
                 '"production_kill_switch_post_state": "HALTED"', '"trading_token_used": True',
                 '"readonly_token_used_for_remote_auth": False', '"finam_authentication_performed": True',
                 '"order_endpoint_called": False', '"order_count": 0', '"execution_authorized": False',
                 '"live_trading_authorized": False', '"real_order_transmission_authorized": False',
                 '"scheduled_task_required": False', '"stage8_10_8_status": "NOT_STARTED"',
                 '"stage8_11_status": "NOT_STARTED_NOT_AUTHORIZED"',
                 '"stage8_12_status": "NOT_STARTED_NOT_AUTHORIZED"'):
        _assert_stage_8_10_7_semantic_failure(relative, original.replace(term, "removed", 1),
                                              "STAGE_8_10_7_REPORT_CONTRACT")


def test_stage_8_10_7_external_report_is_rejected():
    tracked = git_files() + ["external/stage8_10_7_intel_trading_token_acceptance.json"]
    assert "STAGE_8_10_7_EXTERNAL_ARTIFACT_NOT_TRACKED" in stage8.audit(write_result=False, tracked_files=tracked)["errors"]
    assert "RUNTIME_OR_SECRET_ARTIFACT_TRACKED" in run_audit(tracked=tracked)["errors"]


def _assert_stage_8_10_6_semantic_failure(relative, mutation, error):
    full = "TradingSystemLab/stage8_robot/" + relative
    final_result = run_audit({full: mutation})
    assert error in final_result["errors"]
    stage8_result = stage8.audit(write_result=False, source_overrides={relative: mutation})
    assert error in stage8_result["errors"]


def _stage_8_10_6_source(relative):
    return source("TradingSystemLab/stage8_robot/" + relative)


@pytest.mark.parametrize("payload", [
    "from . import finam_api", "from . import broker", "from . import runner",
    "import urllib.request\nurllib.request.urlopen('https://invalid')", "import requests\nrequests.get('https://invalid')",
    "import socket\nsocket.socket()",
])
def test_stage_8_10_6_safety_capability_mutations_fail_semantic_audits(payload):
    relative = "trading_safety_gate.py"
    _assert_stage_8_10_6_semantic_failure(relative, _stage_8_10_6_source(relative) + "\n" + payload + "\n", "STAGE_8_10_6_OFFLINE_FAIL_CLOSED")


@pytest.mark.parametrize("payload", ["from . import finam_api", "import requests", "from . import broker\nbroker.place_order()"])
def test_stage_8_10_6_validation_capability_mutations_fail_semantic_audits(payload):
    relative = "safety_gate_validation.py"
    _assert_stage_8_10_6_semantic_failure(relative, _stage_8_10_6_source(relative) + "\n" + payload + "\n", "STAGE_8_10_6_OFFLINE_FAIL_CLOSED")


@pytest.mark.parametrize("payload", [
    ". $PSScriptRoot\\credential-store.ps1", ". $PSScriptRoot\\trading-credential-store.ps1",
    "Get-ReadonlyCredential", "Get-TradingCredential", "Invoke-WebRequest https://invalid",
    "Invoke-RestMethod https://invalid", "curl https://invalid", "Enable-ScheduledTask x",
    "Start-ScheduledTask x", "Register-ScheduledTask x", "$allow_arm = $true", "$execution_authorized=true",
])
def test_stage_8_10_6_wrapper_capability_mutations_fail_semantic_audits(payload):
    relative = "deploy/windows/validate-trading-safety-gates.ps1"
    _assert_stage_8_10_6_semantic_failure(relative, _stage_8_10_6_source(relative) + "\n" + payload + "\n", "STAGE_8_10_6_WRAPPER_HALT_ONLY")


@pytest.mark.parametrize(("before", "after"), [
    ('return None, "KILL_SWITCH_MISSING"', 'return {"state":"ARMED"}, None'),
    ('return None, "KILL_SWITCH_INVALID"', 'return {"state":"ARMED"}, None'),
    ('if switch["state"] == "HALTED": reasons.append("KILL_SWITCH_HALTED")', 'if False: reasons.append("KILL_SWITCH_HALTED")'),
    ('if execution_authorized is not True: reasons.append("EXECUTION_NOT_AUTHORIZED")', 'if False: reasons.append("EXECUTION_NOT_AUTHORIZED")'),
    ('heartbeat.get("health_status") == "HEALTHY"', 'True'),
    ('heartbeat.get("reconciliation_status") == "PASS"', 'True'),
    ('heartbeat.get("entries_enabled") is False', 'True'),
    ('heartbeat.get("unresolved_order_count") == 0', 'heartbeat.get("unresolved_order_count") >= 0'),
    ('heartbeat.get("failure_code") is None', 'True'),
    ('heartbeat.get("consecutive_failures") == 0', 'heartbeat.get("consecutive_failures") >= 0'),
    ('heartbeat.get("cycle_count") >= 1', 'heartbeat.get("cycle_count") >= 0'),
    ('elif age > MAX_HEARTBEAT_AGE_SECONDS: reasons.append("HEARTBEAT_STALE")',
     'elif age > MAX_HEARTBEAT_AGE_SECONDS * 2: reasons.append("HEARTBEAT_STALE")'),
    ('elif age > MAX_HEARTBEAT_AGE_SECONDS: reasons.append("FINAM_CONTACT_STALE")',
     'elif age > MAX_HEARTBEAT_AGE_SECONDS * 2: reasons.append("FINAM_CONTACT_STALE")'),
    ('_HASH.fullmatch', 're.fullmatch'),
    ('REPOSITORY_OUTPUT_FORBIDDEN', 'OUTPUT_ALLOWED_IN_REPOSITORY'),
])
def test_stage_8_10_6_fail_closed_gate_mutations_fail_semantic_audits(before, after):
    relative = "trading_safety_gate.py"
    original = _stage_8_10_6_source(relative)
    assert before in original
    _assert_stage_8_10_6_semantic_failure(relative, original.replace(before, after), "STAGE_8_10_6_OFFLINE_FAIL_CLOSED")


@pytest.mark.parametrize("field", [
    '"production_kill_switch_initialized": True', '"production_kill_switch_final_state": "HALTED"',
    '"production_kill_switch_valid": True',
])
def test_stage_8_10_6_physical_report_contract_mutations_fail_semantic_audits(field):
    relative = "safety_gate_validation.py"
    original = _stage_8_10_6_source(relative)
    assert field in original
    _assert_stage_8_10_6_semantic_failure(relative, original.replace(field, '"removed": False'), "STAGE_8_10_6_PHYSICAL_REPORT_CONTRACT")


def test_later_execution_stages_started_or_authorized_fail():
    path = "TradingSystemLab/CURRENT_STATE.md"
    for stage, error in (("8.11", "STAGE_8_11_NOT_STARTED_NOT_AUTHORIZED"),
                         ("8.12", "STAGE_8_12_NOT_STARTED_NOT_AUTHORIZED")):
        result = run_audit({path: source(path).replace(
            f"Stage {stage} is **NOT STARTED / NOT AUTHORIZED**",
            f"Stage {stage} is **STARTED / AUTHORIZED**")})
        assert error in result["errors"]


def test_false_permission_and_real_order_claims_fail():
    path = "TradingSystemLab/CURRENT_STATE.md"
    accepted = run_audit({path: source(path) + "\n\nToken permission boundary validation occurred.\n"})
    assert "STAGE_8_10_FALSE_AUTHORIZATION_OR_TOKEN_CLAIM" not in accepted["errors"]
    for claim in ("Broker acceptance was validated.",
                  "FINAM server accepted an order.",
                  "Real-order transmission is authorized."):
        result = run_audit({path: source(path) + "\n\n" + claim + "\n"})
        assert "STAGE_8_10_FALSE_AUTHORIZATION_OR_TOKEN_CLAIM" in result["errors"]


def test_tracked_trading_token_and_account_artifacts_fail():
    forbidden = ["secrets/trading-token.json", "runtime/account_id.txt",
                 "runtime/finam-trading-token.dpapi",
                 "stage8_10_2_physical_provisioning_acceptance.json",
                 "stage8_10_3_identity_account_binding.json",
                 "stage8_10_4_permission_boundary.json", "runtime/token1.txt",
                 "runtime/session.jwt"]
    result = run_audit(tracked=git_files() + forbidden)
    assert all(path in result["runtime_artifacts_tracked"] for path in forbidden)
    assert "RUNTIME_OR_SECRET_ARTIFACT_TRACKED" in result["errors"]


def test_stage_8_10_3_machine_authority_mutations_fail():
    path = "TradingSystemLab/stage8_robot/authority_provenance.json"
    authority = json.loads(source(path))
    mutations = [
        ("status", "STAGE_8_10_3_IDENTITY_ACCOUNT_BINDING_CODE_READY_PENDING_PHYSICAL_VALIDATION"),
        ("status", "NOT_STARTED"),
        ("accepted_code_commit", "0" * 40),
        ("external_evidence_sha256", "0" * 64),
        ("physical_result", "FAIL"),
        ("physical_validation_performed", False),
        ("local_readonly_trading_account_binding_validated", False),
        ("trading_session_created", False),
        ("trading_token_used", False),
        ("finam_authentication_performed", False),
        ("expected_account_enumerated", False),
        ("expected_account_occurrence_count", 2),
        ("enumerated_account_count", 2),
        ("order_count", 1),
        ("order_endpoint_called", True),
        ("live_trading_authorized", True),
        ("real_order_transmission_authorized", True),
        ("stage8_10_status", "COMPLETE"),
        ("stage8_10_4_status", "STARTED"),
        ("stage8_10_5_through_8_status", "STARTED"),
        ("stage8_11_status", "AUTHORIZED"),
        ("stage8_12_status", "AUTHORIZED"),
    ]
    for key, value in mutations:
        changed = json.loads(json.dumps(authority))
        changed["stage8_10_3"][key] = value
        result = run_audit({path: json.dumps(changed)})
        assert "STAGE_8_10_3_MACHINE_AUTHORITY_EXACT" in result["errors"]


def test_identity_module_order_capability_and_wrapper_runtime_wiring_fail():
    module = "TradingSystemLab/stage8_robot/trading_identity_binding.py"
    result = run_audit({module: source(module) + "\ndef unsafe(api):\n    api.place_order('x', {})\n"})
    assert "STAGE_8_10_3_SESSION_ONLY_NO_ORDER_CAPABILITY" in result["errors"]
    wrapper = "TradingSystemLab/stage8_robot/deploy/windows/validate-trading-identity-binding.ps1"
    result = run_audit({wrapper: source(wrapper) + "\n# install-task ScheduledTask runner\n"})
    assert "STAGE_8_10_3_NOT_RUNTIME_OR_TASK_WIRED" in result["errors"]


def test_stage_8_10_4_machine_authority_mutations_fail():
    path = "TradingSystemLab/stage8_robot/authority_provenance.json"
    authority = json.loads(source(path))
    mutations = [
        ("status", "STAGE_8_10_4_PERMISSION_BOUNDARY_CODE_READY_PENDING_PHYSICAL_VALIDATION"),
        ("status", "NOT_STARTED"),
        ("accepted_code_commit", "0" * 40),
        ("external_evidence_sha256", "0" * 64),
        ("physical_result", "FAIL"),
        ("physical_validation_performed", False),
        ("local_readonly_trading_account_binding_validated", False),
        ("readonly_session_created", False),
        ("trading_session_created", False),
        ("readonly_expected_account_enumerated", False),
        ("trading_expected_account_enumerated", False),
        ("readonly_expected_account_occurrence_count", 2),
        ("trading_expected_account_occurrence_count", 2),
        ("readonly_token_readonly_observed", False),
        ("trading_token_readonly_false_observed", False),
        ("token_permission_boundary_validated", False),
        ("readonly_token_used", False),
        ("trading_token_used", False),
        ("finam_authentication_performed", False),
        ("order_count", 1), ("order_endpoint_called", True),
        ("order_path_validation_performed", True),
        ("live_trading_authorized", True),
        ("real_order_transmission_authorized", True),
        ("stage8_10_status", "COMPLETE"),
        ("stage8_10_5_status", "STARTED"),
        ("stage8_10_6_through_8_status", "STARTED"),
        ("stage8_11_status", "AUTHORIZED"),
        ("stage8_12_status", "AUTHORIZED"),
    ]
    for key, value in mutations:
        changed = json.loads(json.dumps(authority))
        changed["stage8_10_4"][key] = value
        result = run_audit({path: json.dumps(changed)})
        assert "STAGE_8_10_4_MACHINE_AUTHORITY_EXACT" in result["errors"]


def test_permission_module_order_capability_and_wrapper_wiring_fail():
    module = "TradingSystemLab/stage8_robot/trading_permission_boundary.py"
    result = run_audit({module: source(module) + "\ndef unsafe(api):\n    api.place_order('x', {})\n"})
    assert "STAGE_8_10_4_SESSION_ONLY_NO_ORDER_CAPABILITY" in result["errors"]
    wrapper = "TradingSystemLab/stage8_robot/deploy/windows/validate-trading-permission-boundary.ps1"
    result = run_audit({wrapper: source(wrapper) + "\n# install-task ScheduledTask runner\n"})
    assert "STAGE_8_10_4_NOT_RUNTIME_OR_TASK_WIRED" in result["errors"]


def test_historical_blockers_described_as_current_fail():
    path = "TradingSystemLab/CURRENT_STATE.md"
    for status, reason in (("BLOCKED_ACCOUNT_FINANCIALS_UNAVAILABLE", "FORTS_PORTFOLIO_MISSING"),
                           ("BLOCKED_INSUFFICIENT_CONTRACT_CAPACITY", "ZERO_CONTRACT_CAPACITY")):
        mutation = source(path) + f"\n\nThe current blocker is {status}, reason {reason}.\n"
        result = run_audit({path: mutation})
        assert "STAGE_8_9_HISTORICAL_BLOCKERS_NOT_CURRENT" in result["errors"]


def test_false_full_n4_funding_readiness_claim_fails():
    path = "TradingSystemLab/CURRENT_STATE.md"
    mutation = source(path) + "\n\nFULL/N4 funding is validated and ready.\n"
    result = run_audit({path: mutation})
    assert "FULL_N4_FUNDING_READINESS_NOT_CLAIMED" in result["errors"]


def test_stage_8_9_provenance_mutations_fail():
    path = "TradingSystemLab/stage8_robot/authority_provenance.json"
    mutations = (
        (final.STAGE_8_9_CODE, "WRONG"),
        (final.STAGE_8_9_REPORT, "WRONG"),
        (final.STAGE_8_9_SUMMARY, "WRONG"),
        ('"physical_result": "STAGE_8_9_10_POST_FUNDING_REVALIDATION_PASS=1"',
         '"physical_result": "FAIL"'),
        ('"funding_classification": "STAGE_8_9_FUNDING_MARGIN_VALIDATED"',
         '"funding_classification": "WRONG"'),
        ('"reason": "ALL_AUTHORITIES_VALID"', '"reason": "WRONG"'),
        ('"sizing_case_count": 8', '"sizing_case_count": 7'),
        ('"positive_capacity_case_count": 4', '"positive_capacity_case_count": 3'),
        ('"stage8_9_complete": true', '"stage8_9_complete": false'),
        ('"stage8_10_status": "IN_PROGRESS"', '"stage8_10_status": "COMPLETE"'),
    )
    for before, after in mutations:
        result = run_audit({path: source(path).replace(before, after)})
        assert any(name in result["errors"] for name in (
            "STAGE_8_9_LIFECYCLE_COMPLETE", "STAGE_8_9_10_PROVENANCE_EXACT",
            "STAGE_8_9_10_PHYSICAL_PASS_RECORDED",
            "STAGE_8_10_IN_PROGRESS_NOT_COMPLETE"))


def test_stage_8_8_7_missing_external_provenance_fails():
    path = "TradingSystemLab/CURRENT_STATE.md"
    result = run_audit({path: source(path).replace(final.STAGE_8_8_7_EVIDENCE, "MISSING")})
    assert "STAGE_8_8_7_EXTERNAL_PROVENANCE_SYNCHRONIZED" in result["errors"]


def test_stage_8_8_7_wrong_accepted_commit_fails():
    path = "TradingSystemLab/ROADMAP.md"
    result = run_audit({path: source(path).replace(final.STAGE_8_8_7_CODE, "WRONG")})
    assert "STAGE_8_8_7_EXTERNAL_PROVENANCE_SYNCHRONIZED" in result["errors"]


def test_stage_8_10_2_provenance_mutations_fail_closed():
    path = "TradingSystemLab/stage8_robot/authority_provenance.json"
    mutations = (
        ("status", "STAGE_8_10_2_SECURE_PROVISIONING_CODE_READY_PENDING_PHYSICAL_PROVISIONING"),
        ("accepted_code_commit", "WRONG"),
        ("external_evidence_sha256", "WRONG"),
        ("physical_result", "WRONG"),
        ("physical_provisioning_performed", False),
        ("trading_token_provisioned", False),
        ("trading_token_used", True),
        ("finam_authentication_performed", True),
        ("order_count", 1),
        ("stage8_10_status", "COMPLETE"),
        ("stage8_10_3_status", "STARTED"),
        ("stage8_10_3_through_8_status", "STARTED"),
        ("stage8_11_status", "STARTED_AUTHORIZED"),
        ("stage8_12_status", "STARTED_AUTHORIZED"),
    )
    for key, value in mutations:
        authority = json.loads(source(path))
        authority["stage8_10_2"][key] = value
        result = run_audit({path: json.dumps(authority)})
        assert "STAGE_8_10_2_MACHINE_AUTHORITY_EXACT" in result["errors"]


def test_trading_store_integrity_mutations_fail():
    path = "TradingSystemLab/stage8_robot/deploy/windows/trading-credential-store.ps1"
    for before, after in (("CurrentUser", "LocalMachine"),
                          ("TRADING_CAPABLE_NOT_AUTHORIZED", "REAL_READONLY"),
                          ("TradingSystemLab.Stage8.TradingToken.v1", "TradingSystemLab.Stage8.RealReadonly.v1")):
        result = run_audit({path: source(path).replace(before, after)})
        assert any(error.startswith("PROTECTED_IMPLEMENTATION_HASHES") for error in result["errors"])
