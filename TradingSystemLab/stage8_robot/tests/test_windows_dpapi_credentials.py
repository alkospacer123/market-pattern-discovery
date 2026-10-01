"""Structural and real Windows execution tests for the DPAPI deployment."""
import os
from pathlib import Path
import re
import shutil
import subprocess

import pytest

WINDOWS = Path(__file__).parents[1] / "deploy" / "windows"
HELPER = (WINDOWS / "credential-store.ps1").read_text()
INIT = (WINDOWS / "initialize-readonly-credentials.ps1").read_text()
VERIFY = (WINDOWS / "verify-readonly-credentials.ps1").read_text()
RUN = (WINDOWS / "run-readonly.ps1").read_text()
INSTALL = (WINDOWS / "install-task.ps1").read_text()
ALL = "\n".join((HELPER, INIT, VERIFY, RUN, INSTALL))
WINDOWS_DPAPI_UNAVAILABLE = "Windows CurrentUser DPAPI unavailable on this platform"


def _windows_powershell() -> str:
    if os.name != "nt":
        pytest.skip(WINDOWS_DPAPI_UNAVAILABLE)
    # Windows PowerShell is the production deployment environment. PowerShell 7
    # is a supported fallback, but absence of both on Windows is infrastructure
    # failure rather than a reason to turn an execution test into a static test.
    executable = shutil.which("powershell.exe") or shutil.which("pwsh.exe")
    if executable is None:
        pytest.fail("Windows DPAPI test infrastructure requires powershell.exe or pwsh.exe")
    return executable


def _run_actual_dpapi_test(tmp_path: Path, operation: str, expected_marker: str) -> None:
    _windows_powershell()  # Skip before importing the Windows runtime authority.
    from TradingSystemLab.stage8_robot.specification import (
        PRODUCTION_SPECIFICATION_ID,
        load_frozen_specification,
    )

    production_id = load_frozen_specification().production_id
    assert production_id == PRODUCTION_SPECIFICATION_ID
    secrets = tmp_path / "secrets"
    secrets.mkdir()
    blob = secrets / "test-only-credential.dpapi"

    # Equality and failure-code checks deliberately happen in PowerShell so the
    # only successful output is a sanitized marker. Credentials are generated
    # locally, are unmistakably synthetic, and never come from operator env vars.
    script = rf"""
$ErrorActionPreference = "Stop"
. '{str(WINDOWS / "credential-store.ps1").replace("'", "''")}'
$productionId = '{production_id.replace("'", "''")}'
$secret = "FINAM_TEST_TOKEN_$([Guid]::NewGuid().ToString('N'))"
$account = "REAL_TEST_ACCOUNT_$([Guid]::NewGuid().ToString('N'))"
$payload = [ordered]@{{
    schema_version = 1
    mode = "REAL_READONLY"
    production_id = $productionId
    finam_api_secret = $secret
    finam_real_account_id = $account
}}
$ciphertext = Protect-ReadonlyCredentialPayload $payload
[IO.File]::WriteAllBytes('{str(blob).replace("'", "''")}', $ciphertext)
$ciphertext = [IO.File]::ReadAllBytes('{str(blob).replace("'", "''")}')

switch ('{operation}') {{
    'roundtrip' {{
        $decoded = Unprotect-ReadonlyCredentialBytes $ciphertext $productionId
        if ($decoded.schema_version -ne 1 -or $decoded.mode -ne 'REAL_READONLY' -or
            $decoded.production_id -ne $productionId -or
            $decoded.finam_api_secret -cne $secret -or
            $decoded.finam_real_account_id -cne $account) {{ throw 'TEST_ROUNDTRIP_MISMATCH' }}
        Write-Output 'ROUNDTRIP_PASS'
    }}
    'tamper' {{
        $ciphertext[[Math]::Floor($ciphertext.Length / 2)] =
            $ciphertext[[Math]::Floor($ciphertext.Length / 2)] -bxor 1
        try {{ $null = Unprotect-ReadonlyCredentialBytes $ciphertext $productionId }}
        catch {{
            if ($_.Exception.Message -ceq 'DPAPI_DECRYPT_FAILED') {{
                Write-Output 'TAMPER_REJECTED'
                break
            }}
            throw
        }}
        throw 'TEST_TAMPER_ACCEPTED'
    }}
    'wrong-production-id' {{
        try {{ $null = Unprotect-ReadonlyCredentialBytes $ciphertext ($productionId + '_WRONG') }}
        catch {{
            if ($_.Exception.Message -ceq 'DPAPI_PRODUCTION_ID_MISMATCH') {{
                Write-Output 'PRODUCTION_ID_REJECTED'
                break
            }}
            throw
        }}
        throw 'TEST_WRONG_PRODUCTION_ID_ACCEPTED'
    }}
}}
"""
    completed = subprocess.run(
        [_windows_powershell(), "-NoProfile", "-NonInteractive", "-Command", script],
        check=False,
        capture_output=True,
        text=True,
    )
    assert completed.returncode == 0, (
        f"PowerShell DPAPI execution failed with exit code {completed.returncode}; "
        "credential-bearing output withheld"
    )
    assert completed.stdout.strip() == expected_marker


def test_dpapi_is_current_user_only_and_has_stable_entropy():
    assert "Add-Type -AssemblyName System.Security -ErrorAction Stop" in HELPER
    assert "DPAPI_SYSTEM_SECURITY_UNAVAILABLE" in HELPER
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


def test_actual_dpapi_current_user_round_trip_on_windows(tmp_path):
    _run_actual_dpapi_test(tmp_path, "roundtrip", "ROUNDTRIP_PASS")


def test_actual_dpapi_tamper_is_rejected_on_windows(tmp_path):
    _run_actual_dpapi_test(tmp_path, "tamper", "TAMPER_REJECTED")


def test_actual_dpapi_wrong_production_id_is_rejected_on_windows(tmp_path):
    _run_actual_dpapi_test(tmp_path, "wrong-production-id", "PRODUCTION_ID_REJECTED")
