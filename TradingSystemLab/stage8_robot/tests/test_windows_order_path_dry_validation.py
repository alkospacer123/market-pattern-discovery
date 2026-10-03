from pathlib import Path


WRAPPER = Path(__file__).parents[1] / "deploy/windows/validate-order-path-dry.ps1"


def test_wrapper_is_credential_free_offline_and_fail_closed():
    text = WRAPPER.read_text()
    lower = text.lower()
    for variable in (
        "FINAM_API_SECRET", "FINAM_REAL_ACCOUNT_ID", "FINAM_TRADING_API_SECRET",
        "FINAM_TRADING_ACCOUNT_ID", "FINAM_PERMISSION_READONLY_API_SECRET",
        "FINAM_PERMISSION_TRADING_API_SECRET", "FINAM_PERMISSION_ACCOUNT_ID",
        "STAGE8_10_4_PERMISSION_BOUNDARY",
    ):
        assert variable in text
    assert "order_path_dry_validation" in text
    for forbidden in (
        "credential-store", "trading-credential-store", "invoke-webrequest",
        "invoke-restmethod", "curl", "run-readonly", "install-task", "scheduledtask",
        "runner.py", "readonly_supervisor", ".sqlite", ".sqlite3", "-wal", "-shm",
    ):
        assert forbidden not in lower


def test_wrapper_establishes_and_restores_repository_working_directory():
    text = WRAPPER.read_text()
    resolve = text.index('$repo = (Resolve-Path (Join-Path $PSScriptRoot "..\\..\\..\\.."))')
    push = text.index("Push-Location $repo")
    invoke = text.index("-m TradingSystemLab.stage8_robot.order_path_dry_validation")
    pop = text.index("Pop-Location")
    cleanup = text.index("Remove-Item Env:STAGE8_10_5_ORDER_PATH_DRY")
    assert resolve < push < invoke < pop < cleanup
    assert "finally" in text[push:pop]
