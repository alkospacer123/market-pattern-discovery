"""CC-07 channel installation never activates LIVE or modifies V20."""
import os
from pathlib import Path
import subprocess
import pytest

ROOT = Path(__file__).resolve().parents[1]
PATH = ROOT / "deployment" / "cc07-install-channel.ps1"
SOURCE = PATH.read_text(encoding="utf-8")


def test_installer_isolated_and_inactive_by_default():
    for marker in ("cc07-gateway-policy.json", "cc07-inbox", "cc07-public",
                   "cc07_command_worker.py", "cc07_channel_install=pass_cc_only",
                   "cc07_gateway_policy=inactive", "cc07_gateway_process=not_started",
                   "cc07_no_arm_no_task_no_order=yes", "approved=$false",
                   "cc07_channel_admin_required", "cc07_channel_wrong_host"):
        assert marker in SOURCE
    for forbidden in ("start-scheduledtask", "stop-scheduledtask",
                      "register-scheduledtask", "-mode execute",
                      "c:\\v20lab", "c:\\tradingsystemlab",
                      "c:\\intradaylab"):
        assert forbidden not in SOURCE.lower()


def test_channel_installer_pins_privileged_worker_blob():
    from controller import cc07_command_worker as worker
    code = (ROOT / "controller" / "cc07_command_worker.py").read_bytes()
    from hashlib import sha1
    digest = sha1(b"blob " + str(len(code)).encode() + b"\0" + code).hexdigest()
    assert ("$hash='" + digest + "'") in SOURCE
    assert "cc07_channel_hash_mismatch" in SOURCE
    assert "cc07_channel_download_mismatch" in SOURCE
    assert "cc07_channel_target_exists" in SOURCE
    assert "cc07_channel_acl_failed" in SOURCE
    assert worker.EXPECTED_BLOB == "91a83e388978ded33525357397716d5fd509fc2a"


def test_channel_installer_native_syntax_only():
    if os.name != "nt":
        pytest.skip("Windows PowerShell native syntax")
    command=("$e=$null;$t=$null;[void]"
             "[system.management.automation.language.parser]::parsefile('"
             +str(PATH).replace("'", "''")+"',[ref]$t,[ref]$e);"
             "if($e.count -ne 0){$e|out-string|write-output;exit 1}")
    result = subprocess.run(["powershell.exe","-noprofile","-noninteractive",
                             "-command",command],
                            capture_output=True, text=True, timeout=20, check=False)
    assert result.returncode == 0, result.stdout + result.stderr
