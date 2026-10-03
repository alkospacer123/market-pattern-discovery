from pathlib import Path

from TradingSystemLab.stage8_robot import final_operational_audit as final


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


def test_stage_8_10_2_started_or_authorized_fails():
    path = "TradingSystemLab/CURRENT_STATE.md"
    result = run_audit({path: source(path).replace(
        "Stage 8.10.2 is **NOT STARTED / NOT AUTHORIZED**",
        "Stage 8.10.2 is **STARTED / AUTHORIZED**")})
    assert "STAGE_8_10_2_NOT_STARTED_NOT_AUTHORIZED" in result["errors"]


def test_later_execution_stages_started_or_authorized_fail():
    path = "TradingSystemLab/CURRENT_STATE.md"
    for stage, error in (("8.11", "STAGE_8_11_NOT_STARTED_NOT_AUTHORIZED"),
                         ("8.12", "STAGE_8_12_NOT_STARTED_NOT_AUTHORIZED")):
        result = run_audit({path: source(path).replace(
            f"Stage {stage} is **NOT STARTED / NOT AUTHORIZED**",
            f"Stage {stage} is **STARTED / AUTHORIZED**")})
        assert error in result["errors"]


def test_false_trading_token_and_real_order_claims_fail():
    path = "TradingSystemLab/CURRENT_STATE.md"
    for claim in ("A trading token has been provisioned.",
                  "Real-order transmission is authorized."):
        result = run_audit({path: source(path) + "\n\n" + claim + "\n"})
        assert "STAGE_8_10_FALSE_AUTHORIZATION_OR_TOKEN_CLAIM" in result["errors"]


def test_tracked_trading_token_and_account_artifacts_fail():
    forbidden = ["secrets/trading-token.json", "runtime/account_id.txt"]
    result = run_audit(tracked=git_files() + forbidden)
    assert all(path in result["runtime_artifacts_tracked"] for path in forbidden)
    assert "RUNTIME_OR_SECRET_ARTIFACT_TRACKED" in result["errors"]


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
