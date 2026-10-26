# V20-08.1: one read-only physical readiness check; no orders, permits, Task mutations.
[CmdletBinding()]
param()
$ErrorActionPreference = 'Stop'
Set-StrictMode -Version Latest
$root = 'C:\V20Lab'
$launcher = Join-Path $root 'pretrade-08\invoke-dpapi-finam-readonly.ps1'
$python = Join-Path $root '.venv-raw\scripts\python.exe'
$source = Join-Path $root 'source-raw'
$binding = Join-Path $root 'pretrade-08\DPAPI_TRADING_BINDINGS_REPORT.json'
$expectedLauncher = '179abdd8b2de81b747bc35144cc4cb972e7b1d40'
function need([bool]$ok,[string]$reason) { if (-not $ok) { throw $reason } }
need ($env:OS -eq 'Windows_NT' -and $env:COMPUTERNAME -eq 'URIU-PC') 'V20_08_1_WRONG_HOST'
foreach ($path in @($root,$launcher,$python,$source,$binding)) {
    need (Test-Path -LiteralPath $path) 'V20_08_1_REQUIRED_PATH_MISSING'
    need (-not ((Get-Item -LiteralPath $path -Force).Attributes -band [IO.FileAttributes]::ReparsePoint)) 'V20_08_1_REPARSE_POINT_FORBIDDEN'
}
$hash = (& git.exe hash-object -- $launcher).Trim().ToLowerInvariant()
need ($LASTEXITCODE -eq 0 -and $hash -eq $expectedLauncher) 'V20_08_1_READER_PIN_MISMATCH'
$report = Get-Content -LiteralPath $binding -Raw -Encoding UTF8 | ConvertFrom-Json
$sid = [Security.Principal.WindowsIdentity]::GetCurrent().User.Value
need ($report.schema -eq 'v20.08.1.dpapi_trading_bindings.v1' -and
      $report.status -eq 'PASS_3_OF_3_DPAPI_LIVE_OFF' -and
      $report.principal_sid -eq $sid -and $report.live_enabled -eq $false) 'V20_08_1_BINDING_REPORT_MISMATCH'
$names = @('v20-shallow','v20-obv','v20-inside')
$hashes = @()
foreach ($name in $names) {
    $entries = @($report.robots | Where-Object { $_.robot -eq $name })
    need ($entries.Count -eq 1 -and $entries[0].status -eq 'DPAPI_SID_BOUND_LIVE_OFF' -and
          [string]$entries[0].account_sha256 -match '^[0-9a-f]{64}$') 'V20_08_1_ACCOUNT_SCOPE_UNPROVEN'
    $hashes += [string]$entries[0].account_sha256
    $task = Get-ScheduledTask -TaskName $name -TaskPath '\' -ErrorAction Stop
    need ($task.State -eq 'Disabled' -and @($task.Actions).Count -eq 1 -and
          $task.Actions[0].Arguments.Contains('v20-task-live-blocked.ps1')) 'V20_08_1_TASK_NOT_DISABLED'
}
# The existing, previously accepted one-shot FINAM worker checks all 3 OWN
# account GET+orders, monetary snapshot and absence of broker position/orders.
# It authenticates via each existing SID-bound DPAPI secret, no POST routes.
& powershell.exe -noprofile -noninteractive -executionpolicy bypass -file $launcher -mode preflight -robot all
need ($LASTEXITCODE -eq 0) 'V20_08_1_REAL_ACCOUNT_GET_HOLD'
$program = @'
import json
import sqlite3
import sys
from pathlib import Path
from TradingSystemLab.stage8_robot.trading_safety_gate import load_kill_switch

root = Path(sys.argv[1])
robots = ('shallow', 'obv', 'inside')
hashes = sys.argv[2:]
if len(hashes) != 3:
    raise RuntimeError('V20_08_1_READINESS_BINDINGS_INVALID')
for slug, account_hash in zip(robots, hashes):
    directory = root / 'robots' / slug
    state_dir = directory / 'state'
    safety = directory / 'safety'
    dbfile = state_dir / 'v20-real-intents.sqlite3'
    for p in (directory, state_dir):
        if not p.is_dir() or p.is_symlink():
            raise RuntimeError('V20_08_1_INSTANCE_DIRECTORY_INVALID_' + slug)
    for p in (safety, dbfile):
        if p.is_symlink():
            raise RuntimeError('V20_08_1_INSTANCE_SYMLINK_FORBIDDEN_' + slug)
    if dbfile.exists():
        if not dbfile.is_file():
            raise RuntimeError('V20_08_1_LEDGER_FILE_INVALID_' + slug)
        with sqlite3.connect(dbfile.as_uri() + '?mode=ro', uri=True) as db:
            identity_row = db.execute("SELECT value FROM state WHERE key='database_identity'").fetchone()
            expected = {
                'schema_id': 'v20.h1_state_store.real_intents.v1',
                'robot_id': 'v20-' + slug,
                'strategy': {
                    'shallow': 'SHALLOW_PULLBACK',
                    'obv': 'OBV_PRESSURE',
                    'inside': 'INSIDE_DAY_RELEASE',
                }[slug],
                'account_sha256': account_hash,
                'mode': 'V20_PRETRADE_UNAUTHORIZED',
            }
            if not identity_row or json.loads(identity_row[0]) != expected:
                raise RuntimeError('V20_08_1_LEDGER_ACCOUNT_IDENTITY_MISMATCH_' + slug)
            if db.execute('SELECT COUNT(*) FROM intents').fetchone()[0] != 0:
                raise RuntimeError('V20_08_1_LEDGER_EXISTING_ORDER_INTENT_' + slug)
            if db.execute('SELECT COUNT(*) FROM fills').fetchone()[0] != 0:
                raise RuntimeError('V20_08_1_LEDGER_EXISTING_FILL_' + slug)
            for key in ('execution_halt','trial_authority_consumed','risk_reservations','session_entries'):
                row = db.execute('SELECT value FROM state WHERE key=?', (key,)).fetchone()
                if row is not None and json.loads(row[0]):
                    raise RuntimeError('V20_08_1_LEDGER_DIRTY_' + slug)
        ledger_result = 'PASS_EMPTY_EXISTING'
    else:
        ledger_result = 'PASS_NOT_INITIALIZED_NO_INTENTS'
    switch, error = load_kill_switch(directory)
    if error == 'KILL_SWITCH_MISSING':
        switch_result = 'PASS_UNARMED_NOT_INSTALLED'
    elif error:
        raise RuntimeError('V20_08_1_KILL_SWITCH_INVALID_' + slug)
    elif switch['state'] == 'HALTED':
        switch_result = 'PASS_UNARMED_HALTED'
    else:
        raise RuntimeError('V20_08_1_UNAUTHORIZED_KILL_SWITCH_ARMED_' + slug)
    print('v20_08_1_' + slug + '_ledger=' + ledger_result)
    print('v20_08_1_' + slug + '_kill_switch=' + switch_result)
print('v20_08_1_three_pretrial_readonly=PASS_3_OF_3_NO_ORDER')
'@
$oldPath = $env:PYTHONPATH
$oldNoBytecode = $env:PYTHONDONTWRITEBYTECODE
try {
    $env:PYTHONPATH = $source
    $env:PYTHONDONTWRITEBYTECODE = '1'
    & $python -B -c $program $root @hashes
    need ($LASTEXITCODE -eq 0) 'V20_08_1_LEDGER_OR_KILL_SWITCH_HOLD'
} finally {
    $env:PYTHONPATH = $oldPath
    $env:PYTHONDONTWRITEBYTECODE = $oldNoBytecode
}
Write-Output 'v20_08_1_orders=zero'
Write-Output 'v20_08_1_live=off'
Write-Output 'v20_08_1_tasks_modified=no'
