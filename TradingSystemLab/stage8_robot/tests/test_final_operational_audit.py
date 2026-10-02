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
    assert all("STAGE_8_9_FUNDING_MARGIN_DIAGNOSTIC_READY_PENDING_INTEL_VALIDATION" in doc
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


def test_stage_8_9_pending_status_removed_fails():
    path = "TradingSystemLab/CURRENT_STATE.md"
    result = run_audit({path: source(path).replace(
        "STAGE_8_9_FUNDING_MARGIN_DIAGNOSTIC_READY_PENDING_INTEL_VALIDATION", "MISSING")})
    assert "STAGE_8_9_DIAGNOSTIC_PENDING_SYNCHRONIZED" in result["errors"]


def test_stage_8_8_7_missing_external_provenance_fails():
    path = "TradingSystemLab/CURRENT_STATE.md"
    result = run_audit({path: source(path).replace(final.STAGE_8_8_7_EVIDENCE, "MISSING")})
    assert "STAGE_8_8_7_EXTERNAL_PROVENANCE_SYNCHRONIZED" in result["errors"]


def test_stage_8_8_7_wrong_accepted_commit_fails():
    path = "TradingSystemLab/ROADMAP.md"
    result = run_audit({path: source(path).replace(final.STAGE_8_8_7_CODE, "WRONG")})
    assert "STAGE_8_8_7_EXTERNAL_PROVENANCE_SYNCHRONIZED" in result["errors"]
