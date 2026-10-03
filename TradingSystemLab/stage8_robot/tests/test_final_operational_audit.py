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
        mutation = original.replace(final.STAGE_8_10_3_STATUS, status, 1)
        result = run_audit({path: mutation})
        assert "STAGE_8_ROBOT_README_CURRENT_STATUS_EXACT" in result["errors"]
        stage8_result = stage8.audit(write_result=False, readme_text=mutation)
        assert "STAGE_8_ROBOT_README_CURRENT_STATUS_EXACT" in stage8_result["errors"]


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
    for claim in ("Trading permission validation occurred.",
                  "Order permission was validated.",
                  "Real-order transmission is authorized."):
        result = run_audit({path: source(path) + "\n\n" + claim + "\n"})
        assert "STAGE_8_10_FALSE_AUTHORIZATION_OR_TOKEN_CLAIM" in result["errors"]


def test_tracked_trading_token_and_account_artifacts_fail():
    forbidden = ["secrets/trading-token.json", "runtime/account_id.txt",
                 "runtime/finam-trading-token.dpapi",
                 "stage8_10_2_physical_provisioning_acceptance.json",
                 "stage8_10_3_identity_account_binding.json", "runtime/token1.txt",
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
