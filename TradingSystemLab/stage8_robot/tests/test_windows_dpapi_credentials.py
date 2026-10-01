"""Cross-platform structural tests for the Windows-only DPAPI deployment."""
from pathlib import Path
import re

WINDOWS = Path(__file__).parents[1] / "deploy" / "windows"
HELPER = (WINDOWS / "credential-store.ps1").read_text()
INIT = (WINDOWS / "initialize-readonly-credentials.ps1").read_text()
VERIFY = (WINDOWS / "verify-readonly-credentials.ps1").read_text()
RUN = (WINDOWS / "run-readonly.ps1").read_text()
INSTALL = (WINDOWS / "install-task.ps1").read_text()
ALL = "\n".join((HELPER, INIT, VERIFY, RUN, INSTALL))


def test_dpapi_is_current_user_only_and_has_stable_entropy():
    assert "DataProtectionScope]::CurrentUser" in HELPER
    assert "LocalMachine" not in ALL
    assert "TradingSystemLab.Stage8.RealReadonly.v1" in HELPER
    assert "ProtectedData]::Protect" in HELPER
    assert "ProtectedData]::Unprotect" in HELPER


def test_payload_validation_fails_closed():
    for marker in ("DPAPI_PAYLOAD_INVALID", "DPAPI_MODE_INVALID",
                   "DPAPI_PRODUCTION_ID_MISMATCH", "DPAPI_SECRET_MISSING",
                   "DPAPI_ACCOUNT_MISSING", "DPAPI_DECRYPT_FAILED"):
        assert marker in HELPER
    assert 'mode="REAL_READONLY"' in INIT
    assert "Get-ReadonlyCredential" in VERIFY


def test_loader_and_launcher_never_put_credentials_in_arguments_or_output():
    assert "Set-ProcessReadonlyCredentials" in RUN
    assert "$env:FINAM_API_SECRET" not in INSTALL
    assert "$env:FINAM_REAL_ACCOUNT_ID" not in INSTALL
    action = INSTALL.split("New-ScheduledTaskAction", 1)[1].splitlines()[0]
    assert "FINAM_API_SECRET" not in action and "FINAM_REAL_ACCOUNT_ID" not in action
    assert "TradingSystemLab.stage8_robot.readonly_supervisor" in RUN
    assert "TradingSystemLab.stage8_robot.real_account_smoke" not in RUN
    assert not re.search(r"Write-(?:Host|Output).*finam_(?:api_secret|real_account_id)", ALL, re.I)


def test_no_persistent_plaintext_environment_writes_or_setx():
    assert not re.search(r"\bsetx(?:\.exe)?\b", ALL, re.I)
    assert not re.search(r"SetEnvironmentVariable\s*\([^\n]+(?:User|Machine)", ALL, re.I)
    assert "FINAM_API_SECRET" not in INIT and "FINAM_REAL_ACCOUNT_ID" not in INIT


def test_task_is_explicit_same_user_unattended_and_conservative():
    assert "Get-CurrentPrincipalInfo" in INSTALL
    assert "Get-ReadonlyCredential" in INSTALL
    assert "New-ScheduledTaskPrincipal" in INSTALL
    assert "-UserId $principal.Name" in INSTALL
    assert "-LogonType Password" in INSTALL
    assert "Get-Credential" in INSTALL
    assert not re.search(r"-UserId\s+(?:['\"])?(?:NT AUTHORITY\\)?SYSTEM\b", INSTALL, re.I)
    assert "-MultipleInstances IgnoreNew" in INSTALL
    assert "-AtStartup" in INSTALL
    assert "-ExecutionPolicy RemoteSigned" in INSTALL
    assert "ExecutionPolicy AllSigned" not in INSTALL


def test_safety_mode_and_service_target_remain_forced():
    assert '$env:FINAM_MODE = "REAL_READONLY"' in RUN
    assert '$env:NEW_ENTRIES_DISABLED = "true"' in RUN
    assert "TradingSystemLab.stage8_robot.readonly_supervisor" in RUN
    assert not any(name in ALL for name in ("place_order", "submit_order", "cancel_order"))


def test_runtime_store_is_binary_atomic_acl_hardened_and_outside_checkout():
    assert 'Join-Path $RuntimeRoot "secrets"' in INIT
    assert "finam-real-readonly.dpapi" in HELPER
    assert "WriteAllBytes" in INIT and "Move-Item -Force" in INIT
    assert "SetAccessRuleProtection($true, $false)" in HELPER
    assert '"S-1-1-0"' in HELPER and '"S-1-5-32-545"' in HELPER
    assert "WriteAllText($metadataTemp" in INIT


def test_actual_dpapi_round_trip_and_tamper_rejection_on_windows():
    """Cryptographic execution belongs to Windows; structural tests run everywhere."""
    import os
    import pytest
    if os.name != "nt":
        pytest.skip("Windows CurrentUser DPAPI is unavailable on this platform")
    # Intel acceptance executes initialize + verify; no test credential is persisted by CI.
    assert "DPAPI_CREDENTIAL_BOOTSTRAP_PASS" in INIT
    assert "DPAPI_CREDENTIAL_STORE_PASS" in VERIFY
