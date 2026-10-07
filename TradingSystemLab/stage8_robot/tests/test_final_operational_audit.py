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
    return (ROOT / relative).read_bytes().replace(b"\r\n", b"\n").decode("utf-8")


def test_clean_repository_authority_passes():
    result = run_audit()
    assert result["status"] == "PASS"
    assert result["checks"] > 0
    assert result["intel_final_acceptance_performed"] is True
    assert result["stage8_8_7_accepted_code_commit"] == final.STAGE_8_8_7_CODE
    assert result["stage8_8_7_external_evidence_sha256"] == final.STAGE_8_8_7_EVIDENCE


def test_stage8_repository_text_decode_is_explicit_utf8():
    audit_source = source("TradingSystemLab/stage8_robot/audit_stage8.py")
    final_source = source("TradingSystemLab/stage8_robot/final_operational_audit.py")
    assert 'path.read_bytes().replace(b"\\r\\n", b"\\n").decode("utf-8")' in audit_source
    assert 'content(relative).replace(b"\\r\\n", b"\\n").decode("utf-8")' in final_source


def test_wrong_production_id_fails():
    path = "TradingSystemLab/results/post_v3_analysis/stage7_production_specification_freeze/production_specification.json"
    result = run_audit({path: source(path).replace(final.SPEC_ID, "PROD_STAGE7_WRONG")})
    assert "PRODUCTION_SPECIFICATION_ID_EXACT" in result["errors"]


def test_changed_protected_implementation_hash_fails():
    path = "TradingSystemLab/stage8_robot/readonly_supervisor.py"
    result = run_audit({path: source(path) + "\n# mutation\n"})
    assert any(error.startswith("PROTECTED_IMPLEMENTATION_HASHES:") for error in result["errors"])


def test_stage8_11_cleanliness_correction_preserves_historical_hash_authority():
    path = "TradingSystemLab/stage8_robot/readonly_supervisor.py"
    assert final.PROTECTED_SHA256[path] == "1455fee5fe207c617676a0463ce3034247c5534578555cac293807da22bcaab8"
    assert final.POST_STAGE8_11_CORRECTED_SHA256[path] == "c4dee8d488dc6379b80a31aca39256b89c3d8e9ae76269267381cd357fe073e5"
    assert final.POST_STAGE8_11_CORRECTED_SHA256[
        "TradingSystemLab/stage8_robot/account_cleanliness.py"
    ] == "7ab8b91483f7e37605f3a4962281fcdc338bf649cee96f141f06ac20294a2184"
    assert final.POST_STAGE8_11_CORRECTED_SHA256[
        "TradingSystemLab/stage8_robot/stage8_11_attempt2_manual_recovery.py"
    ] == "9ceda04454f22608761671335dae221a2c978948e95e4f9e355e4950388cdb84"
    assert final.POST_STAGE8_11_CORRECTED_SHA256[
        "TradingSystemLab/stage8_robot/funding_margin_diagnostic.py"
    ] == "2443f8cab7fafe5b4ab1cb9cb5673e71a9f7bf74b51608425e55f41b1b3645c9"
    assert final.POST_STAGE8_11_CORRECTED_SHA256[
        "TradingSystemLab/stage8_robot/stage8_11_physical_acceptance_attempt3.py"
    ] == "65e832d7c61d27ce8feefe1d41621749a7f376b53d58c478241dcfdbaefc4be9"
    assert final.POST_STAGE8_11_CORRECTED_SHA256[
        "TradingSystemLab/stage8_robot/deploy/windows/run-stage8-11-physical-acceptance-attempt3.ps1"
    ] == "ccdef47390c4c755f65c601db083876b37eb5db633aff79dbfd83e99c2444b41"
    result = run_audit()
    assert result["protected_implementation_status"] == "PASS"
    assert not any(error.startswith("PROTECTED_IMPLEMENTATION_HASHES:") for error in result["errors"])


@pytest.mark.parametrize("relative,before,after,final_error,stage8_error", [
    ("finam_api.py", "class FinamOrderRejected", "class RemovedOrderRejected",
     "STAGE8_11_REJECTION_TAXONOMY", "STAGE8_11_DETERMINISTIC_REJECT_UNCERTAIN_TAXONOMY"),
    ("controlled_real_acceptance.py", 'transition_intent(request.idempotency_key, "REJECTED")',
     'transition_intent(request.idempotency_key, "UNCERTAIN")',
     "STAGE8_11_REJECTED_VS_UNCERTAIN", "STAGE8_11_HTTP400_TERMINAL_REJECTED"),
    ("controlled_real_acceptance.py", "self.api.schedule(finam_symbol)", "{}",
     "STAGE8_11_LIVE_EXACT_SYMBOL_SESSION_GATE", "STAGE8_11_EXACT_SCHEDULE_SESSION_GATE"),
    ("controlled_real_acceptance.py", "flatten_observed = time_source()", "flatten_observed = observed",
     "STAGE8_11_FRESH_PER_POST_CLOCK_AND_ENTRY_MARGIN", "STAGE8_11_FRESH_PER_POST_CLOCK_AND_ENTRY_MARGIN"),
    ("controlled_real_acceptance.py", "minimum_remaining=ENTRY_MINIMUM_REMAINING_SESSION", "minimum_remaining=None",
     "STAGE8_11_FRESH_PER_POST_CLOCK_AND_ENTRY_MARGIN", "STAGE8_11_FRESH_PER_POST_CLOCK_AND_ENTRY_MARGIN"),
    ("stage8_11_failed_attempt_recovery.py", "backup, manifest = create_stage8_11_acceptance_backup", "backup, manifest = removed_backup",
     "STAGE8_11_RECOVERY_NO_ORDER_CAPABILITY", "STAGE8_11_BOUND_ORDER_INCAPABLE_RECOVERY"),
    ("stage8_11_failed_attempt_recovery.py", "readonly_api.orders(account_id)",
     "readonly_api.place_order(account_id, {})",
     "STAGE8_11_RECOVERY_NO_ORDER_CAPABILITY", "STAGE8_11_BOUND_ORDER_INCAPABLE_RECOVERY"),
    ("stage8_11_failed_attempt_recovery.py", "BEGIN IMMEDIATE", "BEGIN",
     "STAGE8_11_RECOVERY_DURABLE_COMMIT_PROTOCOL", "STAGE8_11_RECOVERY_DURABLE_COMMIT_PROTOCOL"),
    ("stage8_11_attempt2_manual_recovery.py", "count_active_orders(orders)", "0",
     "STAGE8_11_ATTEMPT2_MANUAL_RECOVERY_BOUNDARY", "STAGE8_11_ATTEMPT2_MANUAL_RECOVERY_BOUNDARY"),
    ("stage8_11_attempt2_manual_recovery.py", "UPDATE intents SET status='CLOSED'", "UPDATE intents SET status='RECONCILED'",
     "STAGE8_11_ATTEMPT2_MANUAL_RECOVERY_BOUNDARY", "STAGE8_11_ATTEMPT2_MANUAL_RECOVERY_BOUNDARY"),
    ("stage8_11_attempt2_manual_recovery.py", "broker_status not in ATTEMPT2_EXECUTED_STATUSES", "False",
     "STAGE8_11_ATTEMPT2_MANUAL_RECOVERY_BOUNDARY", "STAGE8_11_ATTEMPT2_MANUAL_RECOVERY_BOUNDARY"),
    ("stage8_11_attempt2_manual_recovery.py", '"final_position_quantity": 1', '"final_position_quantity": 0',
     "STAGE8_11_ATTEMPT2_MANUAL_RECOVERY_BOUNDARY", "STAGE8_11_ATTEMPT2_MANUAL_RECOVERY_BOUNDARY"),
    ("controlled_real_acceptance.py",
     "expected_position=expected_position, pending_position=0",
     "expected_position=0, pending_position=0",
     "STAGE_8_11_POSITION_AUTHORITATIVE_RECONCILIATION",
     "STAGE_8_11_POSITION_AUTHORITATIVE_RECONCILIATION"),
    ("controlled_real_acceptance.py", "finally:\n        emergency_halt(runtime_root", "finally:\n        pass #",
     "STAGE8_11_CLEAN_PROOF_AND_HALT", "STAGE8_11_PARENT_CHILD_HALT_MAX_TWO_POST_CAPABILITY"),
])
def test_stage8_11_corrective_guard_mutations_fail_both_auditors(
        relative, before, after, final_error, stage8_error):
    full = "TradingSystemLab/stage8_robot/" + relative
    mutation = source(full).replace(before, after, 1)
    assert mutation != source(full)
    assert final_error in run_audit({full: mutation})["errors"]
    assert stage8_error in stage8.audit(
        write_result=False, source_overrides={relative: mutation})["errors"]


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


def test_stage_8_10_completion_regression_fails():
    path = "TradingSystemLab/CURRENT_STATE.md"
    result = run_audit({path: source(path).replace(
        "Stage 8.10 is **COMPLETE**", "Stage 8.10 is **IN PROGRESS**")})
    assert "STAGE_8_10_COMPLETE_SYNCHRONIZED" in result["errors"]


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
        mutation = original.replace(final.STAGE_8_10_COMPLETE_STATUS, status, 1)
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
    for old, replacement, error in (
            ("The physical authorization used for attempt7 is consumed",
             "The physical authorization used for attempt7 is active",
             "STAGE_8_11_LIFECYCLE_CLOSEOUT_SYNCHRONIZED"),
            ("Stage 8.12 — **STARTED / CODE-ONLY / NOT AUTHORIZED**",
             "Stage 8.12 — **STARTED / AUTHORIZED**", "STAGE_8_12_1_CURRENT_HANDOFF")):
        result = run_audit({path: source(path).replace(
            old, replacement)})
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


def test_stage_8_10_8_closeout_authority_mutations_fail_both_audits():
    path = "TradingSystemLab/stage8_robot/authority_provenance.json"
    authority = json.loads(source(path))
    closeout_mutations = [
        ("status", "WRONG"), ("stage8_10_complete", False), ("completed_gate_count", 6),
        ("stage8_10_1_status", "WRONG"), ("stage8_10_2_status", "WRONG"),
        ("stage8_10_3_status", "WRONG"), ("stage8_10_4_status", "WRONG"),
        ("stage8_10_5_status", "WRONG"), ("stage8_10_6_status", "WRONG"),
        ("stage8_10_7_status", "WRONG"), ("production_kill_switch_final_state", "ARMED"),
        ("execution_authorized", True), ("order_endpoint_called", True), ("order_count", 1),
        ("live_trading_authorized", True), ("real_order_transmission_authorized", True),
        ("stage8_11_status", "STARTED"), ("stage8_12_status", "AUTHORIZED"),
    ]
    variants = []
    missing = json.loads(json.dumps(authority)); del missing["stage8_10_8"]; variants.append(missing)
    for key, value in closeout_mutations:
        changed = json.loads(json.dumps(authority)); changed["stage8_10_8"][key] = value; variants.append(changed)
    for changed in variants:
        payload = json.dumps(changed)
        assert "STAGE_8_10_8_MACHINE_AUTHORITY_EXACT" in stage8.audit(write_result=False, authority_text=payload)["errors"]
        assert "STAGE_8_10_8_MACHINE_AUTHORITY_EXACT" in run_audit({path: payload})["errors"]


def test_stage_8_10_closeout_document_regressions_fail():
    paths = ("TradingSystemLab/CURRENT_STATE.md", "TradingSystemLab/PROJECT_CONTEXT.md",
             "TradingSystemLab/ROADMAP.md", "TradingSystemLab/stage8_robot/README.md")
    for path in paths:
        original = source(path)
        mutations = (
            original.replace("Stage 8.10 is **COMPLETE**", "Stage 8.10 is **IN PROGRESS**"),
            original.replace("Stage 8.10.8 is **COMPLETE**", "Stage 8.10.8 is **NOT STARTED**"),
            original.replace("The physical authorization used for attempt7 is consumed",
                             "The physical authorization used for attempt7 is active"),
            original.replace("Stage 8.12 — **STARTED / CODE-ONLY / NOT AUTHORIZED**",
                             "Stage 8.12 — **STARTED / AUTHORIZED**"),
            original.replace(final.STAGE_8_10_COMPLETE_STATUS, "WRONG_CLOSEOUT_STATUS"),
        )
        for mutation in mutations:
            result = run_audit({path: mutation})
            assert result["status"] == "FAIL", (path, result)


def test_stage_8_12_2_machine_authority_mutations_fail_both_audits():
    path = "TradingSystemLab/stage8_robot/authority_provenance.json"
    authority = json.loads(source(path))
    mutations = (
        ("status", "NOT_STARTED_NOT_AUTHORIZED"),
        ("stage8_12_1_status", "FAIL"),
        ("accepted_code_commit", "0" * 40),
        ("external_test_only_evidence_sha256", "0" * 64),
        ("structural_zero_order_boundary", "FAIL"),
        ("runtime_n4_capacity_pytest", {"passed":24,"failed":1}),
        ("frozen_stage7_risk_margin_regression", {"passed":165,"failed":1}),
        ("stage8_11_position_authority_regression", {"passed":112,"failed":1}),
        ("test_only_real_order_count", 1),
        ("real_order_endpoint_called", True),
        ("execution_authorized", True),
        ("live_trading_authorized", True),
        ("real_order_transmission_authorized", True),
        ("production_kill_switch_final_state", "ARMED"),
        ("production_scheduled_task", "Enabled"),
        ("stage8_12_2_status", "FAIL"),
        ("stage8_12_3_status", "STARTED"),
        ("stage8_12_4_status", "AUTHORIZED"),
        ("next_gate", "STAGE_8_12_4"),
        ("n4_simultaneous_positive_capacity_calculation", "COMPLETE"),
        ("stage8_12_2_accepted_code_commit", "0" * 40),
        ("stage8_12_2_external_test_only_evidence_sha256", "0" * 64),
        ("stage8_12_2_external_test_only_evidence_tracked_in_git", True),
        ("stage8_12_2_conformance_pytest", {"passed":18,"failed":1}),
        ("stage8_12_2_runtime_regression", {"passed":24,"failed":1}),
        ("stage8_12_2_margin_regression", {"passed":143,"failed":1}),
        ("stage8_12_2_safety_regression", {"passed":47,"failed":1}),
        ("stage8_12_2_position_reconciliation_regression", {"passed":112,"failed":1}),
        ("stage8_12_2_frozen_core_conformance", {"passed":110,"failed":1}),
        ("stage8_12_2_independent_stage8_audit", {"status":"FAIL","checks":262}),
        ("stage8_12_2_final_operational_audit", {"status":"FAIL","checks":149}),
    )
    for key, value in mutations:
        changed = json.loads(json.dumps(authority))
        changed["stage8_12"][key] = value
        payload = json.dumps(changed)
        independent = stage8.audit(write_result=False, authority_text=payload)
        operational = run_audit({path: payload})
        assert "STAGE_8_12_2_MACHINE_AUTHORITY_EXACT" in independent["errors"], key
        assert "STAGE_8_12_2_MACHINE_AUTHORITY_EXACT" in operational["errors"], key


@pytest.mark.parametrize("path", (
    "TradingSystemLab/CURRENT_STATE.md",
    "TradingSystemLab/PROJECT_CONTEXT.md",
    "TradingSystemLab/ROADMAP.md",
    "TradingSystemLab/stage8_robot/README.md",
))
def test_stage_8_12_2_current_handoff_mutations_fail_both_audits(path):
    original = source(path)
    mutations = (
        original.replace("Stage 8.12 — **STARTED / CODE-ONLY / NOT AUTHORIZED**",
                         "Stage 8.12 — **STARTED / AUTHORIZED**", 1),
        original.replace("2a15f4331afc1433dfbfd0464108e39e59d236f8", "0" * 40, 1),
        original.replace("4F58595E2F62F2A377E5525972B9E88A136B2F9BC51760268D012AF94A70AE9F",
                         "0" * 64, 1),
        original.replace("Stage 8.12.3 — Intel production preflight — is the **NEXT GATE**",
                         "Stage 8.12.4 is the NEXT GATE", 1),
        original.replace("test-only real-order count: `0`", "test-only real-order count: `1`", 1),
    )
    for mutation in mutations:
        _assert_document_mutation_fails_both(
            path, mutation, "STAGE_8_12_2_CURRENT_HANDOFF")


CANONICAL_STAGE_8_10_DOCS = (
    "TradingSystemLab/CURRENT_STATE.md", "TradingSystemLab/PROJECT_CONTEXT.md",
    "TradingSystemLab/ROADMAP.md", "TradingSystemLab/stage8_robot/README.md",
)


def _assert_document_mutation_fails_both(path, mutation, expected_error):
    relative = path.removeprefix("TradingSystemLab/stage8_robot/")
    if path.startswith("TradingSystemLab/") and not path.startswith("TradingSystemLab/stage8_robot/"):
        relative = path.removeprefix("TradingSystemLab/")
    independent = stage8.audit(write_result=False, source_overrides={relative: mutation, path: mutation})
    operational = run_audit({path: mutation})
    assert expected_error in independent["errors"], (path, independent)
    assert expected_error in operational["errors"], (path, operational)


@pytest.mark.parametrize("path", CANONICAL_STAGE_8_10_DOCS)
@pytest.mark.parametrize("bad_paragraph,expected_error", (
    ("Stage 8.10.5 is the next gate.", "STAGE_8_10_NO_STALE_NEXT_GATE"),
    ("Stage 8.10.8 is COMPLETE and is the next separate lifecycle gate.",
     "STAGE_8_10_NO_STALE_NEXT_GATE"),
    ("Stage 8.10.8 is COMPLETE; it was not implemented or executed here.",
     "STAGE_8_10_NO_STALE_NEXT_GATE"),
    ("Stage 8.10.7 is NOT STARTED.", "STAGE_8_10_HISTORICAL_SCOPE_CONSISTENT"),
    ("Stage 8.10.7 is NOT STARTED while Stage 8.10.8 is COMPLETE.",
     "STAGE_8_10_HISTORICAL_SCOPE_CONSISTENT"),
    ("Stage 8.11 is STARTED.", "STAGE_8_10_HISTORICAL_SCOPE_CONSISTENT"),
    ("Stage 8.11 is AUTHORIZED.", "STAGE_8_10_HISTORICAL_SCOPE_CONSISTENT"),
))
def test_stage_8_10_semantic_document_regressions_fail_both_audits(
        path, bad_paragraph, expected_error):
    _assert_document_mutation_fails_both(
        path, source(path) + "\n\n" + bad_paragraph + "\n", expected_error)


@pytest.mark.parametrize("path", CANONICAL_STAGE_8_10_DOCS)
def test_stage_8_10_current_handoff_package4_pass_state_passes_both_audits(path):
    original = source(path)
    independent = stage8.audit(
        write_result=False, source_overrides={path: original}
    )
    operational = run_audit({path: original})
    assert "STAGE_8_10_CURRENT_HANDOFF_EXACT" not in independent["errors"]
    assert "STAGE_8_10_CURRENT_HANDOFF_EXACT" not in operational["errors"]


@pytest.mark.parametrize("path", CANONICAL_STAGE_8_10_DOCS)
def test_stage_8_10_current_handoff_stale_gate_and_omission_fail_both_audits(path):
    original = source(path)
    marker = "## Current handoff"
    start = original.index(marker)
    next_section = original.index("\n## ", start + len(marker))
    handoff = original[start:next_section]
    stale_handoff = handoff.replace(
        "Stage 8.10 is **COMPLETE**.",
        "Stage 8.10 is **COMPLETE**, but the next possible lifecycle gate is Stage 8.10.5.",
        1)
    stale = original[:start] + stale_handoff + original[next_section:]
    _assert_document_mutation_fails_both(path, stale, "STAGE_8_10_NO_STALE_NEXT_GATE")
    omitted_handoff = handoff.replace("stage8.11.attempt7", "", 1)
    omitted = original[:start] + omitted_handoff + original[next_section:]
    _assert_document_mutation_fails_both(path, omitted, "STAGE_8_10_CURRENT_HANDOFF_EXACT")
    package3_omitted_handoff = handoff.replace(
        "AB1D22A2BE4A748B5F25C21C56FEAC922CAE03499F6F41DF04A47F192A3E7D30",
        "",
        1,
    )
    package3_omitted = (
        original[:start] + package3_omitted_handoff + original[next_section:]
    )
    _assert_document_mutation_fails_both(
        path, package3_omitted, "STAGE_8_10_CURRENT_HANDOFF_EXACT"
    )
    package4_omitted_handoff = handoff.replace(
        "60D9C3EFEC7D54C50BF188B003DCE06D31647A9D6B6F0ED33BB46FF08475621B",
        "",
        1,
    )
    package4_omitted = (
        original[:start] + package4_omitted_handoff + original[next_section:]
    )
    independent = stage8.audit(
        write_result=False,
        source_overrides={path: package4_omitted},
    )
    operational = run_audit({path: package4_omitted})
    assert "STAGE_8_12_4_POSTFUNDING_PASS_PACKAGE5_NOT_AUTHORIZED_HANDOFF" in independent["errors"]
    assert "STAGE_8_12_4_POSTFUNDING_PASS_PACKAGE5_NOT_AUTHORIZED_HANDOFF" in operational["errors"]

    postfunding_omitted_handoff = handoff.replace(
        "54205165758FF6FC200290E61070D7082DFC13494048AABE7A5A61CDDE3C7F11",
        "",
        1,
    )
    postfunding_omitted = (
        original[:start] + postfunding_omitted_handoff + original[next_section:]
    )
    independent = stage8.audit(
        write_result=False,
        source_overrides={path: postfunding_omitted},
    )
    operational = run_audit({path: postfunding_omitted})
    assert "STAGE_8_12_4_POSTFUNDING_PASS_PACKAGE5_NOT_AUTHORIZED_HANDOFF" in independent["errors"]
    assert "STAGE_8_12_4_POSTFUNDING_PASS_PACKAGE5_NOT_AUTHORIZED_HANDOFF" in operational["errors"]


@pytest.mark.parametrize("path", CANONICAL_STAGE_8_10_DOCS)
def test_stage_8_11_current_handoff_false_authorization_wording_fails_both_audits(path):
    original = source(path)
    mutated = original.replace(
        "real-order transmission remains unauthorized after the Stage 8.11 PASS",
        "additional real-order transmission is authorized by the Stage 8.11 PASS",
        1)
    _assert_document_mutation_fails_both(
        path, mutated, "STAGE_8_10_FALSE_AUTHORIZATION_OR_TOKEN_CLAIM")


@pytest.mark.parametrize("path", CANONICAL_STAGE_8_10_DOCS)
def test_stage_8_10_clearly_scoped_historical_text_passes_both_audits(path):
    historical = source(path) + ("\n\nIn this historical snapshot, Stage 8.10.7 was "
                                 "NOT STARTED. Subsequently, Stage 8.10.8 completed; "
                                 "current authority is recorded below.\n")
    independent = stage8.audit(write_result=False, source_overrides={path: historical})
    operational = run_audit({path: historical})
    assert independent["status"] == "PASS", (path, independent)
    assert operational["status"] == "PASS", (path, operational)

STAGE811_PATH = "TradingSystemLab/stage8_robot/controlled_real_acceptance.py"
STAGE811_SCHEMA = "TradingSystemLab/stage8_robot/stage8_11_physical_evidence.schema.json"
STAGE811_PRECHECK = "TradingSystemLab/stage8_robot/stage8_11_intel_acceptance.py"
STAGE811_STATE = "TradingSystemLab/stage8_robot/state.py"
STAGE811_PHYSICAL = "TradingSystemLab/stage8_robot/stage8_11_physical_acceptance.py"
STAGE811_WRAPPER = "TradingSystemLab/stage8_robot/deploy/windows/run-stage8-11-physical-acceptance.ps1"

@pytest.mark.parametrize("needle,replacement,error", [
    ("request.quantity != MAX_ACCEPTANCE_QUANTITY", "False", "STAGE_8_11_EXACTLY_ONE_HARD_CAP"),
    ("self.store.persist_intent", "self.store.removed_intent", "STAGE_8_11_INTENT_BEFORE_POST"),
    ("no retry: exactly one call", "retry enabled", "STAGE_8_11_NO_POST_RETRY"),
    ("ENTRY_SUBMISSION_UNCERTAIN_POSITION_RECONCILE",
     "ENTRY_SUBMISSION_UNCERTAIN_HALT",
     "STAGE_8_11_POSITION_AUTHORITATIVE_RECONCILIATION"),
    ("_digest(account_id) != accepted_account_hash.lower()", "False", "STAGE_8_11_EXACT_ACCOUNT_BINDING"),
    ("FINAM_SYMBOL_BINDING_INVALID", "SYMBOL_CHECK_REMOVED", "STAGE_8_11_EXACT_N4_SYMBOL_BINDING"),
    ('classification="SYNTHETIC_PASS"',
     'classification="BROKEN_PASS"',
     "STAGE_8_11_FILL_FLAT_HALTED_PASS"),
])
def test_stage811_safety_mutations_fail_both_independent_audits(needle,replacement,error):
    mutated=source(STAGE811_PATH).replace(needle,replacement,1)
    independent=stage8.audit(write_result=False,source_overrides={"controlled_real_acceptance.py":mutated})
    operational=run_audit({STAGE811_PATH:mutated})
    assert error in independent["errors"]
    assert error in operational["errors"]


def test_stage811_evidence_schema_mutation_fails_both_audits():
    mutated=source(STAGE811_SCHEMA).replace('"additionalProperties": false','"additionalProperties": true',1)
    independent=stage8.audit(write_result=False,source_overrides={"stage8_11_physical_evidence.schema.json":mutated})
    operational=run_audit({STAGE811_SCHEMA:mutated})
    assert "STAGE_8_11_EVIDENCE_PRIVACY_SCHEMA" in independent["errors"]
    assert "STAGE_8_11_EVIDENCE_PRIVACY_SCHEMA" in operational["errors"]


def test_stage811_maximum_post_capability_expansion_fails_both_audits():
    mutated=source(STAGE811_SCHEMA).replace('"maximum": 2','"maximum": 3',1)
    independent=stage8.audit(write_result=False,source_overrides={"stage8_11_physical_evidence.schema.json":mutated})
    operational=run_audit({STAGE811_SCHEMA:mutated})
    assert "STAGE_8_11_MAXIMUM_TWO_POST_CAPABILITY" in independent["errors"]
    assert "STAGE_8_11_MAXIMUM_TWO_POST_CAPABILITY" in operational["errors"]


@pytest.mark.parametrize("needle,replacement,error", [
    ('failure_code="DEFINITIVE_REJECTION"',
     'failure_code="BROKEN_REJECTION"',
     "STAGE_8_11_NO_FILL_REQUIRES_CLEAN_ACCOUNT_PROOF"),
    ('final["unexpected_position_count"] == 0', 'True',
     "STAGE_8_11_FINAL_RECONCILIATION_ALL_POSITIONS"),
    ('active = count_active_orders(order_rows)', 'active = 0',
     "STAGE_8_11_FINAL_RECONCILIATION_ALL_ACTIVE_ORDERS"),
])
def test_stage811_final_reconciliation_mutations_fail_both_audits(needle,replacement,error):
    mutated=source(STAGE811_PATH).replace(needle,replacement,1)
    independent=stage8.audit(write_result=False,source_overrides={"controlled_real_acceptance.py":mutated})
    operational=run_audit({STAGE811_PATH:mutated})
    assert error in independent["errors"]
    assert error in operational["errors"]


@pytest.mark.parametrize("needle,error", [
    ("precheck_report.is_file()", "STAGE_8_11_FROZEN_PRECHECK_PROVENANCE"),
    ('final_active_order_count=final.get("active_order_count")',
     "STAGE_8_11_UNKNOWN_FINAL_STATE_NOT_SAFE_ZERO"),
])
def test_stage811_physical_boundary_mutations_fail_both_audits(needle,error):
    original=source(STAGE811_PHYSICAL)
    replacement=("True" if "precheck" in needle else
                 'final_active_order_count=final.get("active_order_count", 0)')
    mutated=original.replace(needle,replacement,1)
    independent=stage8.audit(write_result=False,source_overrides={"stage8_11_physical_acceptance.py":mutated})
    operational=run_audit({STAGE811_PHYSICAL:mutated})
    assert error in independent["errors"]
    assert error in operational["errors"]


def test_stage811_physical_entrypoint_frozen_clock_mutation_fails_both_audits():
    original=source(STAGE811_PHYSICAL)
    mutated=original.replace("broker=broker, clock=time_source", "broker=broker, now=observed", 1)
    independent=stage8.audit(write_result=False,source_overrides={"stage8_11_physical_acceptance.py":mutated})
    operational=run_audit({STAGE811_PHYSICAL:mutated})
    error="STAGE8_11_PHYSICAL_ENTRYPOINT_FRESH_CLOCK_PROPAGATION"
    assert error in independent["errors"] and error in operational["errors"]


@pytest.mark.parametrize("needle,error", [
    ("$timeStatusExitCode = $LASTEXITCODE", "STAGE_8_11_WINDOWS_TIME_EXIT_CODES"),
    ("$timeSourceExitCode = $LASTEXITCODE", "STAGE_8_11_WINDOWS_TIME_EXIT_CODES"),
    ("emergency_halt(Path", "STAGE_8_11_PARENT_WRAPPER_HALT_DEFENSE"),
])
def test_stage811_wrapper_defense_mutations_fail_both_audits(needle,error):
    mutated=source(STAGE811_WRAPPER).replace(needle,"removed",1)
    relative="deploy/windows/run-stage8-11-physical-acceptance.ps1"
    independent=stage8.audit(write_result=False,source_overrides={relative:mutated})
    operational=run_audit({STAGE811_WRAPPER:mutated})
    assert error in independent["errors"]
    assert error in operational["errors"]

@pytest.mark.parametrize("needle,error",[
    ("evaluate_new_entry_gate", "STAGE_8_11_INTEL_EXISTING_SAFETY_GATE_EXACT_BLOCKERS"),
    ("readonly_unresolved_intent_count", "STAGE_8_11_SEPARATE_PERSISTENCE_AUTHORITIES"),
])
def test_stage811_precheck_authority_removal_fails_both_audits(needle,error):
    mutated=source(STAGE811_PRECHECK).replace(needle,"removed_authority")
    independent=stage8.audit(write_result=False,source_overrides={"stage8_11_intel_acceptance.py":mutated})
    operational=run_audit({STAGE811_PRECHECK:mutated})
    assert error in independent["errors"]
    assert error in operational["errors"]

@pytest.mark.parametrize("needle,replacement",[
    ('tuple(connection.execute(f"PRAGMA table_info({table})")) != expected',
     'tuple(row[1] for row in connection.execute(f"PRAGMA table_info({table})")) != expected'),
    ('"status","TEXT",1,None,0','"status","TEXT",0,None,0'),
    ("COALESCE(status,'') NOT IN","status NOT IN"),
])
def test_stage811_schema_validation_weakening_fails_both_audits(needle,replacement):
    mutated=source(STAGE811_STATE).replace(needle,replacement,1)
    independent=stage8.audit(write_result=False,source_overrides={"state.py":mutated})
    operational=run_audit({STAGE811_STATE:mutated})
    error="STAGE_8_11_EXACT_ACCEPTANCE_SCHEMA_AND_NULL_SAFE_UNRESOLVED"
    assert error in independent["errors"]
    assert error in operational["errors"]

def test_stage811_pr357_provenance_mutation_fails_both_audits():
    path="TradingSystemLab/stage8_robot/authority_provenance.json"
    mutated=source(path).replace('"pull_request": 357','"pull_request": 356',1)
    independent=stage8.audit(write_result=False,authority_text=mutated)
    operational=run_audit({path:mutated})
    error="STAGE_8_11_LIFECYCLE_EVIDENCE_CLOSEOUT"
    assert error in independent["errors"]
    assert error in operational["errors"]


@pytest.mark.parametrize("field,value", [
    ("status", "STAGE_8_11_CONTROLLED_REAL_EXECUTION_ACCEPTANCE_NOT_YET_PASSED"),
    ("stage8_11_1_status", "NOT_RUN"),
    ("stage8_11_2_status", "NOT_COMPLETE"),
    ("stage8_11_3_status", "AUTHORIZED"),
    ("current_gate", "STAGE_8_11_CLOSEOUT_COMPLETE_NEW_EXPLICIT_AUTHORIZATION_REQUIRED_FOR_RETRY"),
    ("latest_physical_precheck_result", "STAGE8_11_SAFETY_GATE_BLOCKED"),
    ("latest_physical_acceptance_result", "OPERATOR_INTERVENTION_REQUIRED"),
    ("latest_authorization_status", "REUSABLE"),
    ("order_endpoint_call_count", 1),
    ("real_order_count", 1),
    ("production_kill_switch_final_state", "ARMED"),
    ("stage8_12_status", "STARTED_AUTHORIZED"),
])
def test_stage811_lifecycle_closeout_mutations_fail_both_audits(field,value):
    path="TradingSystemLab/stage8_robot/authority_provenance.json"
    authority=json.loads(source(path))
    authority["stage8_11"][field]=value
    mutated=json.dumps(authority)
    independent=stage8.audit(write_result=False,authority_text=mutated)
    operational=run_audit({path:mutated})
    error="STAGE_8_11_LIFECYCLE_EVIDENCE_CLOSEOUT"
    assert error in independent["errors"]
    assert error in operational["errors"]


@pytest.mark.parametrize("field,value", [
    ("attempt_id", "stage8.11.attempt6"),
    ("accepted_code_commit", "WRONG"),
    ("evidence_sha256", "0" * 64),
    ("quantity", 2),
    ("broker_fill_count", 1),
    ("entry_fill_proven", False),
    ("one_contract_position_observed", False),
    ("controlled_flatten_proven", False),
    ("order_endpoint_call_count", 1),
    ("final_position_quantity", 1),
    ("final_active_order_count", 1),
    ("unresolved_intent_count", 1),
    ("reconciliation_result", "UNRESOLVED"),
    ("physical_result_classification", "OPERATOR_INTERVENTION_REQUIRED"),
    ("kill_switch_final_state", "ARMED"),
    ("scheduled_task_final_state", "Ready"),
    ("stage8_12_status", "STARTED_AUTHORIZED"),
])
def test_stage811_attempt7_physical_acceptance_authority_mutations_fail_both_audits(field,value):
    path="TradingSystemLab/stage8_robot/authority_provenance.json"
    authority=json.loads(source(path))
    authority["stage8_11"]["physical_acceptance"][field]=value
    mutated=json.dumps(authority)
    independent=stage8.audit(write_result=False,authority_text=mutated)
    operational=run_audit({path:mutated})
    error="STAGE_8_11_LIFECYCLE_EVIDENCE_CLOSEOUT"
    assert error in independent["errors"]
    assert error in operational["errors"]


def test_stage811_mock_only_api_dependency_fails_both_audits():
    mutated=source(STAGE811_PATH).replace(
        "account = api.account(account_id)",
        "api.mock_only_snapshot(account_id)\n    account = api.account(account_id)")
    independent=stage8.audit(write_result=False,source_overrides={"controlled_real_acceptance.py":mutated})
    operational=run_audit({STAGE811_PATH:mutated})
    assert "STAGE_8_11_PRODUCTION_FINAM_API_CONTRACT" in independent["errors"]
    assert "STAGE_8_11_PRODUCTION_FINAM_API_CONTRACT" in operational["errors"]


def test_stage811_protobuf_timestamp_parser_mutation_fails_both_audits():
    original=source(STAGE811_PATH)
    start=original.index("def _timestamp(value: Any)")
    end=original.index("\n\ndef _status",start)
    protobuf_parser='''def _timestamp(value: Any) -> tuple[int, int]:
    if not isinstance(value, dict) or set(value) != {"seconds", "nanos"}:
        raise OperatorInterventionRequired("OPERATOR_INTERVENTION_REQUIRED")
    return value["seconds"], value["nanos"]'''
    mutated=original[:start]+protobuf_parser+original[end:]
    independent=stage8.audit(write_result=False,source_overrides={"controlled_real_acceptance.py":mutated})
    operational=run_audit({STAGE811_PATH:mutated})
    assert "STAGE_8_11_REST_TIMESTAMP_STRING_AUTHORITY" in independent["errors"]
    assert "STAGE_8_11_REST_TIMESTAMP_STRING_AUTHORITY" in operational["errors"]


@pytest.mark.parametrize("path,relative,needle,replacement,error", [
    (STAGE811_PATH,"controlled_real_acceptance.py",'return _rows(account, "positions")',
     'return _rows(account, "positions"), _rows(account, "trades")',"STAGE_8_11_TRADES_NOT_FROM_ACCOUNT"),
    ("TradingSystemLab/stage8_robot/finam_api.py","finam_api.py","def trades(self,account_id)",
     "def account_trades_removed(self,account_id)","STAGE_8_11_FINAM_TRADES_PRIMITIVE"),
    (STAGE811_PATH,"controlled_real_acceptance.py",'order.get("executed_quantity")','order.get("invented_quantity")',
     "STAGE_8_11_DOCUMENTED_EXECUTED_QUANTITY"),
    ("TradingSystemLab/stage8_robot/tests/test_controlled_real_acceptance_finam_integration.py",
     "tests/test_controlled_real_acceptance_finam_integration.py",'prefix + "/trades"',
     'prefix + "/fake-trades"',"STAGE_8_11_EXACT_REST_SYNTHETIC_TRANSPORT"),
])
def test_stage811_rest_schema_mutations_fail_both_audits(path,relative,needle,replacement,error):
    mutated=source(path).replace(needle,replacement,1)
    independent=stage8.audit(write_result=False,source_overrides={relative:mutated})
    operational=run_audit({path:mutated})
    assert error in independent["errors"]
    assert error in operational["errors"]
