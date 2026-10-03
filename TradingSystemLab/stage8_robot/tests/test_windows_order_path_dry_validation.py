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
        "runner.py", "readonly_supervisor", ".sqlite",
    ):
        assert forbidden not in lower
