"""CC-07D Intel-only V20 panel bundle: pinned source, segregated identity and no live mutation."""
import os
from pathlib import Path
from hashlib import sha1
import re

ROOT = Path(__file__).resolve().parents[1]
STAGER = ROOT / "deployment" / "cc07-stage-ccpanel-ui.ps1"
SOURCE = STAGER.read_text(encoding="utf-8")
BUNDLE = [
    "v20_app.py", "v20_command_channel.py", "cc/__init__.py",
    "cc/manual_gate.py", "cc/deployment_paths.py", "cc/v20_contract.py",
    "cc/v20_receiver.py", "cc/v20_staging.py", "cc/v20_manual_export.py",
    "cc/providers/__init__.py", "cc/providers/windows_file.py",
]


def test_stage_manifest_exact_git_hashes_and_all_dependencies():
    matches = re.findall(r"'([a-zA-Z0-9_./-]+)\\|([a-f0-9]{40})'", SOURCE)
    assert len(matches) == 11
    assert sorted(path for path, _ in matches) == sorted(BUNDLE)
    for path, pin in matches:
        b = (ROOT / path).read_bytes()
        expected = sha1(b"blob " + str(len(b)).encode() + b"\0" + b).hexdigest()
        assert pin == expected, path


def test_stager_never_replaces_8502_or_sends_any_command():
    lower = SOURCE.lower()
    for marker in ("cc07-panel-13ce0973", "cc07_panel_stage_exists",
                   "cc07_panel_8502=untouched", "cc07_panel_gateway=not_started_no_arm",
                   "cc07_panel_ccpanel_acl=read_execute_only",
                   "cc07_panel_ccpanel_write_forbidden", "cc07_panel_ccpanel_admin",
                   "cc07_panel_source_hash_mismatch", "cc07_panel_blob_invalid"):
        assert marker in SOURCE
    for forbidden in ("stop-process", "stop-scheduledtask", "start-scheduledtask",
                      "register-scheduledtask", "set-acl", "remove-item",
                      "move-item", "rename-item", "start-process",
                      "c:\\v20lab", "c:\\intradaylab", "c:\\tradingsystemlab",
                      "-mode execute", "-mode serve", "8503"):
        assert forbidden not in lower, forbidden
    assert "need (-not (test-path -literalpath $dest))" in SOURCE
    assert "if($mode -eq 'check')" in SOURCE


def test_windows_native_syntax_without_running_installer():
    if os.name != "nt":
        return
    import subprocess
    command = (
        "$t=$null;$e=$null;[void]"
        "[management.automation.language.parser]::parsefile('"
        + str(STAGER).replace("'", "''") + "',[ref]$t,[ref]$e);"
        "if($e.count){$e|out-string|write-output;exit 1}"
    )
    result = subprocess.run(["powershell.exe", "-noprofile", "-noninteractive",
                             "-command", command],
                            capture_output=True, text=True, timeout=25)
    assert result.returncode == 0, result.stdout + result.stderr
