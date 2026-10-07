from pathlib import Path


VALIDATOR = Path(
    "TradingSystemLab/stage8_robot/deploy/windows/"
    "run-stage8-12-4-package3-zero-order-validation.ps1"
)


def source() -> str:
    return VALIDATOR.read_text(encoding="utf-8")


def test_package3_validator_requires_exact_clean_code_and_stage5_authorities():
    text = source()
    assert "ValidatePattern('^[0-9a-f]{40}$')" in text
    assert "rev-parse HEAD" in text
    assert "STAGE8_12_4_PACKAGE3_ACCEPTED_COMMIT_MISMATCH" in text
    assert "STAGE8_12_4_PACKAGE3_REPOSITORY_NOT_CLEAN" in text
    assert "50f1fd2178c18b7ab3bd969be82ad01f47a34745" in text
    assert "STAGE8_12_4_PACKAGE3_STAGE5_COMMIT_MISMATCH" in text
    assert "STAGE8_12_4_PACKAGE3_STAGE5_NOT_CLEAN" in text
    assert "STAGE8_12_4_PACKAGE3_REPORT_REPOSITORY_FORBIDDEN" in text


def test_package3_validator_requires_inactive_safety_and_disabled_tasks():
    text = source()
    assert "STAGE8_12_4_PACKAGE3_AUTHORIZATION_MUST_BE_ABSENT" in text
    assert '$kill.state -cne "HALTED"' in text
    assert "STAGE8_12_4_PACKAGE3_KILL_SWITCH_NOT_HALTED" in text
    assert "TradingSystemLab-Stage8-Production" in text
    assert "TradingSystemLab-Stage8-Readonly" in text
    assert "STAGE8_12_4_PACKAGE3_PRODUCTION_TASK_MISSING" in text
    assert "STAGE8_12_4_PACKAGE3_PRODUCTION_TASK_NOT_DISABLED" in text
    assert "STAGE8_12_4_PACKAGE3_PRODUCTION_TASK_BINDING_MISMATCH" in text
    assert "STAGE8_12_4_PACKAGE3_PRODUCTION_TASK_PRINCIPAL_MISMATCH" in text
    assert "run-production.ps1" in text
    assert "-ExpectedCommit $AcceptedCommit" in text


def test_package3_validator_compares_production_principal_by_windows_sid():
    text = source()
    assert "[Security.Principal.WindowsIdentity]::GetCurrent()" in text
    assert ".User.Value" in text
    assert "System.Security.Principal.NTAccount" in text
    assert "System.Security.Principal.SecurityIdentifier" in text
    assert ".Translate(" in text
    assert "[string]$task.Principal.UserId -cne $currentName" not in text


def test_package3_foundation_audits_use_canonical_broker_constants_and_current_handoff():
    audit = Path("TradingSystemLab/stage8_robot/audit_stage8.py").read_text(encoding="utf-8")
    final = Path("TradingSystemLab/stage8_robot/final_operational_audit.py").read_text(encoding="utf-8")
    roadmap = Path("TradingSystemLab/ROADMAP.md").read_text(encoding="utf-8")
    for source_text in (audit, final):
        assert "from .protective_stop_contract import QTY_MEASURE, QTY_PERCENT" in source_text
        assert "measure != QTY_MEASURE" in source_text
        assert "quantity_sl != QTY_PERCENT" in source_text
        assert "'\"SLTP_QTY_MEASURE_PERCENT\"'" not in source_text
    handoff = roadmap.split("## Current handoff", 1)[1].split("\n## ", 1)[0]
    assert "205/205 PASS" in handoff
    assert "no authorization record has been created" in handoff.lower()
    assert "kill switch remains `HALTED`" in handoff
    assert "production Scheduled Task remains disabled" in handoff


def test_package3_final_audit_preserves_historical_hash_and_allows_exact_stage8124_finam_hash():
    final = Path("TradingSystemLab/stage8_robot/final_operational_audit.py").read_text(encoding="utf-8")
    assert '"TradingSystemLab/stage8_robot/finam_api.py": "15c97d5557021ec50702bd9e2abf1bde4e76faf90063b973fd61f9cf9d096cb0"' in final
    assert "POST_STAGE8_12_4_CORRECTED_SHA256" in final
    assert '"TradingSystemLab/stage8_robot/finam_api.py": "d1bce44e9b66b4a2936e89f70891f2f4d203cbdd340d0412d08e3aba2cd0b369"' in final
    assert "stage8124_corrected = POST_STAGE8_12_4_CORRECTED_SHA256.get(path)" in final


def test_package3_sparse_h1_overlap_authority_is_fail_closed():
    history = Path("TradingSystemLab/stage8_robot/production_history.py").read_text(encoding="utf-8")
    audit = Path("TradingSystemLab/stage8_robot/audit_stage8.py").read_text(encoding="utf-8")
    final = Path("TradingSystemLab/stage8_robot/final_operational_audit.py").read_text(encoding="utf-8")
    provenance = Path("TradingSystemLab/stage8_robot/authority_provenance.json").read_text(encoding="utf-8")
    for source_text in (history, audit, final):
        assert "live_overlap.index.difference(authority_overlap.index)" in source_text
        assert "seam = authority_overlap.index.max()" in source_text
        assert "if seam not in live_overlap.index" in source_text
    assert "authority_overlap.index.equals(live_overlap.index)" not in history
    assert "FINAM_OVERLAP_SUBSET_OF_FROZEN_AUTHORITY_EXACT_OHLC_AND_SEAM_REQUIRED" in provenance
    assert "CURRENT_FINAM_WINDOW_MAY_OMIT_AUTHORITY_TIMESTAMPS_BUT_ALL_FINAM_OVERLAP_TIMESTAMPS_MUST_EXIST_IN_STAGE5_OR_PERSISTED_AUTHORITY_WITH_EXACT_OHLC_AND_SEAM" in provenance


def test_package3_validator_runs_existing_audits_and_focused_corrective_tests():
    text = source()
    assert "run-stage8-12-4-foundation-validation.ps1" in text
    assert "test_stage8_12_4_rolling_h1_continuity.py" in text
    assert "test_stage8_12_4_production_service.py" in text
    assert "test_stage8_12_4_package3_zero_order_validator.py" in text
    assert "STAGE8_12_4_PACKAGE3_FOCUSED_PYTEST_FAILED" in text


def test_package3_validator_executes_only_unauthorized_once_service_cycle():
    text = source()
    assert "run-production.ps1" in text
    assert "-Once" in text
    assert "STAGE8_12_4_PACKAGE3_PRODUCTION_ONCE_FAILED" in text
    assert "stage8-12-4-production-heartbeat.json" in text
    assert 'reconciliation_status -cne "PASS"' in text
    assert 'health_status -cne "HEALTHY"' in text
    assert "[int]$heartbeat.unresolved_intent_count -ne 0" in text
    assert "[int]$heartbeat.open_position_count -ne 0" in text
    assert "[int]$heartbeat.active_protective_stop_count -ne 0" in text


def test_package3_validator_proves_rolling_h1_state_for_all_n4():
    text = source()
    assert "stage8-12-production.sqlite3" in text
    assert "production_h1_continuation:CNYRUBF" in text
    assert "production_h1_continuation:GLDRUBF" in text
    assert "production_h1_continuation:IMOEXF" in text
    assert "production_h1_continuation:USDRUBF" in text
    assert "stage8_12_4_h1_continuation.v1" in text
    assert "bars_sha256" in text
    assert "[int]$state.continuation_count -ne 4" in text
    assert "STAGE8_12_4_PACKAGE3_STATE_CONTRACT_INVALID" in text


def test_package3_evidence_is_external_hashed_and_zero_order():
    text = source()
    assert "stage8_12_4_package3_zero_order_validation.v1" in text
    assert (
        "STAGE_8_12_4_PACKAGE3_INTEL_EXACT_COMMIT_ZERO_ORDER_VALIDATION_PASS"
        in text
    )
    assert "Get-FileHash $report -Algorithm SHA256" in text
    assert "durable_authorization_present = $false" in text
    assert 'kill_switch = "HALTED"' in text
    assert "execution_authorized = $false" in text
    assert "live_trading_authorized = $false" in text
    assert "real_order_transmission_authorized = $false" in text
    assert "order_endpoint_call_count = 0" in text
    assert "real_order_count = 0" in text
    assert "STAGE8_12_4_PACKAGE3_REAL_ORDER_COUNT=0" in text


def test_package3_wrapper_has_no_activation_or_direct_order_capability():
    text = source()
    lower = text.lower()
    forbidden = (
        "enable-scheduledtask",
        "start-scheduledtask",
        "write_authorization",
        "allow_arm",
        "place_order",
        "place_sltp_order",
        "cancel_order",
        "get-tradingcredential",
        "finam_api_secret",
    )
    assert not any(token in lower for token in forbidden)
