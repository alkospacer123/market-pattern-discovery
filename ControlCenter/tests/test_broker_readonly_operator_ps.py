"""Guard fixed, operator-only FINAM readonly PowerShell one-shot."""
from pathlib import Path
import os
import subprocess

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / 'broker_readonly' / 'finam-one-shot-operator.ps1'


def test_operator_one_shot_only_has_broker_readonly_requests():
    raw = SCRIPT.read_text(encoding='utf-8')
    source = raw.lower()
    assert raw.count('invoke-restmethod ') == 4
    assert source.count(' -method post ') == 2
    assert source.count(' -method get ') == 2
    assert "'/sessions'" in source and "'/sessions/details'" in source
    assert "'/accounts/'" in source and "'/orders'" in source
    assert "details.readonly -cne $true" in source
    assert "metadata.principal_sid_sha256" in source
    assert "credential.mode -cne 'real_readonly'" in source
    assert "finam-real-readonly.dpapi" in source
    for forbidden in ('start-scheduledtask','stop-scheduledtask',
                      'invoke-expression', 'set-acl', 'out-file',
                      'set-content','add-content','start-process','-method delete ',
                      'place_order','trading-token','sqlite3.connect','kill-switch.json',
                      'production-heartbeat.json','/sltp-orders'):
        assert forbidden not in source, forbidden
    assert "cc_owned_snapshot_published=no" in source
    assert "h1_engine_account_ownership=unverified" in source
    assert "broker_stop_position_linkage=unverified" in source


def test_native_powershell_parser_and_preview():
    if os.name != 'nt':
        return
    code = ("$tokens=$null;$errors=$null;"
            f"[void][system.management.automation.language.parser]::parsefile('{SCRIPT}',"
            "[ref]$tokens,[ref]$errors);"
            "if($null -ne $errors -and @($errors).count -gt 0){exit 1}")
    p = subprocess.run(['powershell.exe','-noprofile','-noninteractive','-command',code],
                       capture_output=True,text=True,timeout=20)
    assert p.returncode == 0, 'OPERATOR_SCRIPT_POWERSHELL_SYNTAX'
    p = subprocess.run(['powershell.exe','-noprofile','-noninteractive','-file',str(SCRIPT)],
                       capture_output=True,text=True,timeout=20)
    assert p.returncode == 0 and 'preview_no_network_no_secrets' in p.stdout
    assert 'allowed_requests=' in p.stdout and not p.stderr.strip()
