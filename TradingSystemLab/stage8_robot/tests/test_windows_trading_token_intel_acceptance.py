from pathlib import Path


WRAPPER = Path(__file__).parents[1] / "deploy/windows/validate-trading-token-intel-acceptance.ps1"


def source():
    return WRAPPER.read_text(encoding="utf-8")


def test_wrapper_orders_safety_credentials_binding_child_and_post_checks():
    text = source()
    positions = [
        text.index("foreach ($name in $forbiddenEnvironment)"),
        text.index("Assert-KillSwitchHalted", text.index("try {")),
        text.index('credential-store.ps1'),
        text.index("finam_real_account_id -cne"),
        text.index("$env:FINAM_8107_TRADING_API_SECRET"),
        text.index("-m TradingSystemLab.stage8_robot.trading_token_intel_acceptance"),
        text.rindex("Assert-KillSwitchHalted"),
        text.index("foreach ($name in $stageEnvironment)", text.index("finally")),
    ]
    assert positions == sorted(positions)


def test_wrapper_has_required_host_and_local_credential_boundaries():
    text = source()
    for required in (
        "Get-ScheduledTask", "Disabled", "Get-CimInstance Win32_Process", "load_kill_switch",
        "credential-store.ps1", "trading-credential-store.ps1", "Get-ReadonlyCredential",
        "Get-TradingCredential", "finam_api_secret", "finam_trading_api_secret",
        "STAGE_8_10_7_LOCAL_ACCOUNT_BINDING_PASS", "Push-Location $repo", "Pop-Location",
        "$readonlyCredential = $null", "$tradingCredential = $null",
    ):
        assert required in text


def test_wrapper_exports_only_stage_specific_trading_auth_environment():
    text = source()
    assignments = [line.strip() for line in text.splitlines() if line.strip().startswith("$env:")]
    assert assignments == [
        "$env:FINAM_8107_TRADING_API_SECRET = [string]$tradingCredential.finam_trading_api_secret",
        "$env:FINAM_8107_ACCOUNT_ID = [string]$tradingCredential.finam_real_account_id",
        '$env:STAGE8_10_7_LOCAL_ACCOUNT_BINDING_CONFIRMED = "true"',
        '$env:STAGE8_10_7_INTEL_TRADING_TOKEN_ACCEPTANCE = "true"',
    ]
    assert "readonlyCredential.finam_api_secret\n    $env:" not in text


def test_wrapper_has_no_mutating_or_execution_capability():
    lowered = source().lower()
    forbidden = (
        "set-processreadonlycredentials", "enable-scheduledtask", "start-scheduledtask",
        "register-scheduledtask", "write_kill_switch", "emergency_halt", "allow_arm",
        "place_order", "submit_order", "cancel_order", "execution_authorized=true",
        "run-readonly", "install-task",
    )
    assert not any(value in lowered for value in forbidden)
    assert '"armed"' not in lowered and "'armed'" not in lowered


def test_wrapper_never_prints_secret_or_account_values():
    text = source()
    output_lines = [line for line in text.splitlines() if "Write-Output" in line or "Write-Error" in line]
    assert output_lines == [
        '    Write-Output "STAGE_8_10_7_LOCAL_ACCOUNT_BINDING_PASS"',
        "    Write-Error $code",
    ]
