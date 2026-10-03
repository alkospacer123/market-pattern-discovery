import os
import shutil
import subprocess
from pathlib import Path

import pytest


WINDOWS = Path(__file__).parents[1] / "deploy" / "windows"
STORE = (WINDOWS / "trading-credential-store.ps1").read_text()
INIT = (WINDOWS / "initialize-trading-credentials.ps1").read_text()
VERIFY = (WINDOWS / "verify-trading-credentials.ps1").read_text()
READONLY_STORE = (WINDOWS / "credential-store.ps1").read_text()
LAUNCHER = (WINDOWS / "run-readonly.ps1").read_text()
INSTALLER = (WINDOWS / "install-task.ps1").read_text()


def run_windows_powershell(script):
    shell = shutil.which("pwsh") or shutil.which("powershell")
    assert shell
    return subprocess.run(
        [shell, "-NoProfile", "-NonInteractive", "-Command", script],
        capture_output=True, text=True,
    )


def test_store_has_distinct_current_user_authority():
    assert "DataProtectionScope]::CurrentUser" in STORE
    assert "DataProtectionScope]::LocalMachine" not in STORE
    assert "TradingSystemLab.Stage8.TradingToken.v1" in STORE
    assert "TradingSystemLab.Stage8.RealReadonly.v1" not in STORE
    assert 'TradingCredentialSchema = 1' in STORE
    assert 'TradingCredentialMode = "TRADING_CAPABLE_NOT_AUTHORIZED"' in STORE
    assert "finam_trading_api_secret" in STORE
    assert "finam_api_secret" not in STORE
    assert "REAL_READONLY" not in STORE


def test_initializer_is_interactive_atomic_and_acl_hardened():
    assert INIT.count("Read-Host") == 2
    assert INIT.count("-AsSecureString") == 2
    assert "finam_trading_api_secret" in INIT
    assert ".tmp" in INIT and "Move-Item -Force" in INIT
    assert "Set-TradingPrivateAcl" in INIT
    assert "Get-TradingCredential" in INIT
    assert "[Array]::Clear" in INIT and "ZeroFreeBSTR" in INIT
    parameters = INIT.split("$ErrorActionPreference", 1)[0]
    assert "secret" not in parameters.lower()
    assert "account" not in parameters.lower()


def test_no_persistent_environment_or_credential_output():
    joined = STORE + INIT + VERIFY
    assert "setx" not in joined.lower()
    assert "EnvironmentVariableTarget" not in joined
    assert "$env:" not in joined
    output_lines = [line for line in joined.splitlines() if "Write-Output" in line or "Write-Host" in line]
    assert output_lines
    assert all("$secret" not in line and "$account" not in line and "$payload" not in line for line in output_lines)


def test_metadata_is_sanitized_and_runtime_files_are_distinct():
    assert 'TradingCredentialFile = "finam-trading-token.dpapi"' in STORE
    assert 'TradingCredentialMetadataFile = "finam-trading-token.metadata.json"' in STORE
    metadata = INIT.split("$metadata =", 1)[1].split("$metadataPath", 1)[0]
    for prohibited in ("secret", "account", "token", "balance", "response", "jwt", "bearer"):
        assert prohibited not in metadata.lower()
    for allowed in ("schema_version", "mode", "scope", "creation_utc", "production_id", "principal_sid_sha256"):
        assert allowed in metadata


def test_local_only_and_not_runtime_integrated():
    joined = INIT + VERIFY
    for prohibited in ("Invoke-WebRequest", "Invoke-RestMethod", "api.finam", "/orders", "submit_order", "FINAM_MODE=LIVE"):
        assert prohibited.lower() not in joined.lower()
    for operational in (LAUNCHER, INSTALLER):
        assert "trading-credential" not in operational.lower()
        assert "finam-trading-token" not in operational.lower()


def test_fail_closed_validation_and_cross_store_separation_are_explicit():
    for code in ("SCHEMA_INVALID", "MODE_INVALID", "PRODUCTION_ID_MISMATCH", "SECRET_MISSING",
                 "ACCOUNT_MISSING", "PAYLOAD_MALFORMED", "CIPHERTEXT_EMPTY", "DECRYPT_FAILED",
                 "PRINCIPAL_MISMATCH", "METADATA_INVALID", "ACL_HARDENING_FAILED", "ACL_INVALID"):
        assert "TRADING_DPAPI_" + code in STORE
    assert "finam_trading_api_secret" not in READONLY_STORE
    assert "TradingToken.v1" not in READONLY_STORE


@pytest.mark.skipif(os.name != "nt", reason="actual CurrentUser DPAPI execution requires Windows")
def test_synthetic_roundtrip_tamper_and_cross_store_rejection_on_windows(tmp_path):
    store = str(WINDOWS / "trading-credential-store.ps1").replace("'", "''")
    readonly = str(WINDOWS / "credential-store.ps1").replace("'", "''")
    script = f"""
. '{store}'
. '{readonly}'
$id='PROD_STAGE7_46DB784378797C7FB04636892350AFF21006D71A31F2CED9D4B974EDA2DC36B8'
$p=[ordered]@{{schema_version=1;mode='TRADING_CAPABLE_NOT_AUTHORIZED';production_id=$id;finam_trading_api_secret='SYNTHETIC_FAKE_TEST_ONLY';finam_real_account_id='SYNTHETIC_ACCOUNT'}}
$c=Protect-TradingPayload $p
$r=Unprotect-TradingBytes $c $id
if ($r.mode -ne 'TRADING_CAPABLE_NOT_AUTHORIZED') {{ exit 10 }}
$c[0]=$c[0] -bxor 1
try {{ Unprotect-TradingBytes $c $id; exit 11 }} catch {{}}
$c=Protect-TradingPayload $p
try {{ Unprotect-TradingBytes $c 'WRONG'; exit 12 }} catch {{}}
try {{ Unprotect-ReadonlyCredentialBytes $c $id; exit 13 }} catch {{}}
$rp=[ordered]@{{schema_version=1;mode='REAL_READONLY';production_id=$id;finam_api_secret='SYNTHETIC_FAKE_TEST_ONLY';finam_real_account_id='SYNTHETIC_ACCOUNT'}}
$rc=Protect-ReadonlyCredentialPayload $rp
try {{ Unprotect-TradingBytes $rc $id; exit 14 }} catch {{}}
Write-Output 'TRADING_SYNTHETIC_ROUNDTRIP_PASS'
exit 0
"""
    completed = run_windows_powershell(script)
    assert completed.returncode == 0, completed.stderr
    assert completed.stdout.strip() == "TRADING_SYNTHETIC_ROUNDTRIP_PASS"


@pytest.mark.skipif(os.name != "nt", reason="actual CurrentUser DPAPI execution requires Windows")
def test_wrong_trading_mode_is_rejected_independently_on_windows():
    store = str(WINDOWS / "trading-credential-store.ps1").replace("'", "''")
    script = f"""
. '{store}'
$id='PROD_STAGE7_46DB784378797C7FB04636892350AFF21006D71A31F2CED9D4B974EDA2DC36B8'
$payload=[ordered]@{{schema_version=1;mode='REAL_READONLY';production_id=$id;finam_trading_api_secret='SYNTHETIC_FAKE_TEST_ONLY';finam_real_account_id='SYNTHETIC_ACCOUNT'}}
$ciphertext=Protect-TradingPayload $payload
try {{ Unprotect-TradingBytes $ciphertext $id; exit 20 }}
catch {{ if ($_.Exception.Message -cne 'TRADING_DPAPI_MODE_INVALID') {{ exit 21 }} }}
Write-Output 'TRADING_WRONG_MODE_REJECTION_PASS'
exit 0
"""
    completed = run_windows_powershell(script)
    assert completed.returncode == 0, completed.stderr
    assert completed.stdout.strip() == "TRADING_WRONG_MODE_REJECTION_PASS"


@pytest.mark.skipif(os.name != "nt", reason="actual CurrentUser DPAPI and Windows ACL execution requires Windows")
def test_wrong_principal_metadata_is_rejected_on_windows(tmp_path):
    store = str(WINDOWS / "trading-credential-store.ps1").replace("'", "''")
    root = str(tmp_path).replace("'", "''")
    script = f"""
. '{store}'
$id='PROD_STAGE7_46DB784378797C7FB04636892350AFF21006D71A31F2CED9D4B974EDA2DC36B8'
$root='{root}'
$secrets=New-Item -ItemType Directory -Force -Path (Join-Path $root 'secrets')
$principal=Get-TradingPrincipal
$payload=[ordered]@{{schema_version=1;mode='TRADING_CAPABLE_NOT_AUTHORIZED';production_id=$id;finam_trading_api_secret='SYNTHETIC_FAKE_TEST_ONLY';finam_real_account_id='SYNTHETIC_ACCOUNT'}}
[IO.File]::WriteAllBytes((Join-Path $secrets $script:TradingCredentialFile),(Protect-TradingPayload $payload))
$metadata=[ordered]@{{schema_version=1;mode='TRADING_CAPABLE_NOT_AUTHORIZED';scope='CurrentUser';creation_utc='2000-01-01T00:00:00Z';production_id=$id;principal_sid_sha256=('0' * 64)}}
$metadata | ConvertTo-Json | Set-Content -LiteralPath (Join-Path $secrets $script:TradingCredentialMetadataFile) -Encoding UTF8
Set-TradingPrivateAcl $secrets.FullName $principal.Sid
Set-TradingPrivateAcl (Join-Path $secrets $script:TradingCredentialFile) $principal.Sid
Set-TradingPrivateAcl (Join-Path $secrets $script:TradingCredentialMetadataFile) $principal.Sid
try {{ Get-TradingCredential $root $id; exit 30 }}
catch {{ if ($_.Exception.Message -cne 'TRADING_DPAPI_PRINCIPAL_MISMATCH') {{ exit 31 }} }}
Write-Output 'TRADING_PRINCIPAL_MISMATCH_REJECTION_PASS'
exit 0
"""
    completed = run_windows_powershell(script)
    assert completed.returncode == 0, completed.stderr
    assert completed.stdout.strip() == "TRADING_PRINCIPAL_MISMATCH_REJECTION_PASS"


@pytest.mark.skipif(os.name != "nt", reason="Windows ACL execution requires Windows")
def test_private_acl_accepts_hardened_path_and_rejects_everyone_on_windows(tmp_path):
    store = str(WINDOWS / "trading-credential-store.ps1").replace("'", "''")
    target = str(tmp_path / "private").replace("'", "''")
    script = f"""
. '{store}'
$path=New-Item -ItemType Directory -Force -Path '{target}'
$principal=Get-TradingPrincipal
Set-TradingPrivateAcl $path.FullName $principal.Sid
Assert-TradingPrivateAcl $path.FullName $principal.Sid
$acl=Get-Acl -LiteralPath $path.FullName
$everyone=New-Object Security.Principal.SecurityIdentifier('S-1-1-0')
$acl.AddAccessRule((New-Object Security.AccessControl.FileSystemAccessRule($everyone,'Read','Allow')))
Set-Acl -LiteralPath $path.FullName -AclObject $acl
try {{ Assert-TradingPrivateAcl $path.FullName $principal.Sid; exit 40 }}
catch {{ if ($_.Exception.Message -cne 'TRADING_DPAPI_ACL_INVALID') {{ exit 41 }} }}
Write-Output 'TRADING_ACL_ACCEPTANCE_PASS'
exit 0
"""
    completed = run_windows_powershell(script)
    assert completed.returncode == 0, completed.stderr
    assert completed.stdout.strip() == "TRADING_ACL_ACCEPTANCE_PASS"
