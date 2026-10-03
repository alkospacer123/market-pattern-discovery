from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "deploy/windows/validate-trading-permission-boundary.ps1"


def test_wrapper_uses_separate_stores_and_stage_specific_environment():
    script = SCRIPT.read_text()
    assert '"credential-store.ps1"' in script
    assert '"trading-credential-store.ps1"' in script
    assert "Get-ReadonlyCredential" in script and "Get-TradingCredential" in script
    assert "PROD_STAGE7_46DB784378797C7FB04636892350AFF21006D71A31F2CED9D4B974EDA2DC36B8" in script
    assert "production_id -cne $productionId" in script
    assert script.index("LOCAL_ACCOUNT_MISMATCH") < script.index("FINAM_PERMISSION_READONLY_API_SECRET")
    assert "--report $ReportPath" in script
    assert "--secret" not in script and "--account" not in script
    for name in (
        "FINAM_PERMISSION_READONLY_API_SECRET",
        "FINAM_PERMISSION_TRADING_API_SECRET",
        "FINAM_PERMISSION_ACCOUNT_ID",
        "STAGE8_10_4_PERMISSION_BOUNDARY",
    ):
        assert f"$env:{name}" in script
        assert f"Remove-Item Env:{name}" in script
    assert "$readonlyCredential = $null" in script
    assert "$tradingCredential = $null" in script


def test_mismatch_precedes_child_and_console_is_sanitized():
    script = SCRIPT.read_text()
    assert script.index("PERMISSION_BOUNDARY_LOCAL_ACCOUNT_MISMATCH") < script.index(
        "TradingSystemLab.stage8_robot.trading_permission_boundary"
    )
    output = [line for line in script.splitlines() if "Write-Output" in line or "Write-Error" in line]
    assert all("account_id" not in line and "api_secret" not in line for line in output)


def test_wrapper_has_no_runtime_task_or_execution_wiring():
    lowered = SCRIPT.read_text().lower()
    for forbidden in (
        "/orders", "place_order", "cancel_order", "submit_order", "runner", "broker",
        "run-readonly", "install-task", "scheduledtask",
    ):
        assert forbidden not in lowered
