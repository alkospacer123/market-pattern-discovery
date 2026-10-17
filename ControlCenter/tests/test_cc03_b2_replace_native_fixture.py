"""Prove WinPowerShell File.Replace semantics on disposable hosted-NTFS files only."""
import os
import subprocess
import pytest

pytestmark = pytest.mark.skipif(os.name != "nt", reason="Native Windows test only")


def test_b2_native_replace_disposable_fixture(tmp_path):
    root = tmp_path / "Control Center"
    script = tmp_path / "replacement.ps1"
    script.write_text(r"""
[CmdletBinding()]
param([Parameter(Mandatory=$true)][string]$Root)
$ErrorActionPreference='Stop'
$backup=Join-Path $Root 'data\private\b2-pr543-backup'
$rel='cc/deployment_paths.py'
$src=Join-Path (Join-Path $backup 'incoming') $rel.Replace('/','\')
$dst=Join-Path $Root $rel.Replace('/','\')
$target=Join-Path (Join-Path $backup 'incoming') 'cc\deployment_paths.py.old'
foreach($p in @($src,$dst)){$null=[IO.Directory]::CreateDirectory([IO.Path]::GetDirectoryName($p))}
[IO.File]::WriteAllText($src,'new-value')
[IO.File]::WriteAllText($dst,'old-value')
[IO.File]::Replace($src,$dst,$null)
if([IO.File]::Exists($src) -or [IO.File]::ReadAllText($dst) -cne 'new-value'){throw 'NULL_REPLACE_POSTCONDITION'}
Write-Output 'DISPOSABLE_NULL_BACKUP_REPLACE=PASS'
[IO.File]::WriteAllText($src,'third-value')
[IO.File]::Replace($src,$dst,$target)
if([IO.File]::Exists($src) -or [IO.File]::ReadAllText($dst) -cne 'third-value' -or [IO.File]::ReadAllText($target) -cne 'new-value'){throw 'EXPLICIT_BACKUP_POSTCONDITION'}
Write-Output 'DISPOSABLE_EXPLICIT_BACKUP_REPLACE=PASS'
""", encoding="utf-8")
    result = subprocess.run(
        ["powershell.exe", "-NoProfile", "-NonInteractive", "-File", str(script), "-Root", str(root)],
        capture_output=True, text=True, timeout=45)
    assert result.returncode == 0, (result.stdout, result.stderr)
    assert "DISPOSABLE_NULL_BACKUP_REPLACE=PASS" in result.stdout
    assert "DISPOSABLE_EXPLICIT_BACKUP_REPLACE=PASS" in result.stdout
    assert (root / "cc" / "deployment_paths.py").read_text() == "third-value"
    assert (root / "data" / "private" / "b2-pr543-backup" / "incoming" / "cc" / "deployment_paths.py.old").read_text() == "new-value"
