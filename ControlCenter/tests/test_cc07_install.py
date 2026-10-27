"""CC-07 Intel installer contract: CC-owned only and no V20 mutation."""
from pathlib import Path
import os
import subprocess
import pytest

ROOT = Path(__file__).resolve().parents[1]
INSTALL = ROOT / "deployment" / "cc07-install-operator.ps1"
S = INSTALL.read_text(encoding="utf-8")


def test_installer_only_cc_owned_paths_and_exact_pins():
    assert "91a83e388978ded33525357397716d5fd509fc2a" in S
    assert "c:\\control center" in S.lower()
    assert "control-audit" in S
    assert "cc07-v20-operator.ps1" in S
    assert "cc07_release=not_created" in S
    assert "cc07_no_arm_no_task_no_broker_mutation=yes" in S
    assert "-mode check" not in S
    for banned in ("stop-scheduledtask", "start-scheduledtask",
                   "register-scheduledtask", "kill-switch",
                   "c:\\tradingsystemlab", "c:\\intradaylab",
                   "c:\\v20lab", "-mode execute"):
        assert banned not in S.lower()


def test_installer_must_fail_on_pin_acl_or_existing_paths():
    for guard in (
        "cc07_operator_pin_mismatch",
        "cc07_operator_exists_use_check",
        "cc07_audit_exists_use_check",
        "cc07_admin_install_required",
        "cc07_owner_not_admin",
        "cc07_untrusted_writer",
        "cc07_operator_untrusted_writer",
        "cc07_download_not_pinned",
        "cc07_wrong_intel",
        "cc07_reparse_forbidden",
        "cc07_acl_inheritance_not_protected",
        "cc07_release=not_created",
    ):
        assert guard in S
    assert "https://api.github.com/repos/" in S
    assert "/git/blobs/" in S
    assert S.index("pinned $script $pin") > S.index("[io.file]::writeallbytes($script,$bytes)")


def test_install_native_powershell_parser_only():
    if os.name != "nt":
        pytest.skip("native Windows PowerShell syntax")
    code=("$errors=$null;$tokens=$null;[void]"
          "[system.management.automation.language.parser]::parsefile('"
          + str(INSTALL).replace("'", "''") +
          "',[ref]$tokens,[ref]$errors);"
          "if($errors.count -ne 0){$errors|out-string|write-output;exit 1}")
    got = subprocess.run(["powershell.exe","-noprofile","-noninteractive","-command",code],
                         capture_output=True,text=True,timeout=20,check=False)
    assert got.returncode == 0, got.stdout + got.stderr
