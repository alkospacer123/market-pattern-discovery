from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def test_wrapper_is_separate_secret_safe_operator_path():
    script = (ROOT / "deploy/windows/validate-trading-identity-binding.ps1").read_text()
    assert '"credential-store.ps1"' in script
    assert '"trading-credential-store.ps1"' in script
    assert "Get-ReadonlyCredential" in script and "Get-TradingCredential" in script
    assert script.index("LOCAL_ACCOUNT_MISMATCH") < script.index("FINAM_TRADING_API_SECRET")
    assert "production_id -cne $productionId" in script
    assert "--report $ReportPath" in script
    assert "--secret" not in script and "--account" not in script
    assert "finally" in script
    assert "Remove-Item Env:FINAM_TRADING_API_SECRET" in script
    assert "Remove-Item Env:FINAM_TRADING_ACCOUNT_ID" in script
    lowered = script.lower()
    for forbidden in ("run-readonly", "install-task", "scheduledtask", "runner", "broker", "/orders"):
        assert forbidden not in lowered


def test_mismatch_precedes_child_execution_and_output_is_sanitized():
    script = (ROOT / "deploy/windows/validate-trading-identity-binding.ps1").read_text()
    assert script.index("TRADING_IDENTITY_LOCAL_ACCOUNT_MISMATCH") < script.index(
        "TradingSystemLab.stage8_robot.trading_identity_binding")
    output_lines = [line for line in script.splitlines() if "Write-Output" in line or "Write-Error" in line]
    assert all("finam_real_account_id" not in line and "finam_trading_api_secret" not in line
               for line in output_lines)
