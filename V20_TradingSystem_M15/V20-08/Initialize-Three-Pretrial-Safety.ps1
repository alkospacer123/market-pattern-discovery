# V20-08.1: initialize only missing local V20 H1 StateStores + HALTED Kill Switch.
# Does not decrypt DPAPI, contact FINAM, submit orders, enable Tasks or arm a switch.
[CmdletBinding()]
param()
$ErrorActionPreference = 'Stop'
Set-StrictMode -Version Latest
$root = 'C:\V20Lab'
$source = Join-Path $root 'source-raw'
$python = Join-Path $root '.venv-raw\scripts\python.exe'
$binding = Join-Path $root 'pretrade-08\DPAPI_TRADING_BINDINGS_REPORT.json'
function need([bool]$condition,[string]$reason) { if (-not $condition) { throw $reason } }
need ($env:OS -eq 'Windows_NT' -and $env:COMPUTERNAME -eq 'URIU-PC') 'V20_08_1_WRONG_HOST'
foreach ($path in @($root,$source,$python,$binding)) {
    need (Test-Path -LiteralPath $path) 'V20_08_1_INIT_REQUIRED_FILE_MISSING'
    need (-not ((Get-Item -LiteralPath $path -Force).Attributes -band [IO.FileAttributes]::ReparsePoint)) 'V20_08_1_INIT_REPARSE_FORBIDDEN'
}
# Protect the unchanged H1 SQL and kill-switch mechanics from local drift.
foreach ($check in @(
    @('TradingSystemLab\stage8_robot\state.py','4f12e1cb61eccb0b14c1efb9ff0cdf2532a7b22b'),
    @('TradingSystemLab\stage8_robot\trading_safety_gate.py','e938048a8dc3caa9db29209489a7050e64d0bb5a'),
    @('TradingSystemLab\stage8_robot\operations.py','0d7ba1f2f9f4e6fa2f772921846bc334469dd3d5')
)) {
    $f = Join-Path $source $check[0]
    need (Test-Path -LiteralPath $f -PathType Leaf) 'V20_08_1_H1_SOURCE_MISSING'
    need (-not ((Get-Item -LiteralPath $f -Force).Attributes -band [IO.FileAttributes]::ReparsePoint)) 'V20_08_1_H1_SOURCE_REPARSE'
    $sha = (& git.exe hash-object -- $f).Trim().ToLowerInvariant()
    need ($LASTEXITCODE -eq 0 -and $sha -eq $check[1]) 'V20_08_1_H1_SOURCE_DRIFT'
}
$report = Get-Content -LiteralPath $binding -Raw -Encoding UTF8 | ConvertFrom-Json
$sid = [Security.Principal.WindowsIdentity]::GetCurrent().User.Value
need ($report.schema -eq 'v20.08.1.dpapi_trading_bindings.v1' -and
      $report.status -eq 'PASS_3_OF_3_DPAPI_LIVE_OFF' -and
      $report.live_enabled -eq $false -and $report.principal_sid -eq $sid) 'V20_08_1_ACCOUNT_BINDING_INVALID'
$hashes = @()
foreach ($name in @('v20-shallow','v20-obv','v20-inside')) {
    $rows = @($report.robots | Where-Object { $_.robot -eq $name })
    need ($rows.Count -eq 1 -and $rows[0].status -eq 'DPAPI_SID_BOUND_LIVE_OFF' -and
          [string]$rows[0].account_sha256 -match '^[0-9a-f]{64}$') 'V20_08_1_ACCOUNT_BINDING_MISSING'
    $hashes += [string]$rows[0].account_sha256
    $task = Get-ScheduledTask -TaskName $name -TaskPath '\' -ErrorAction Stop
    need ($task.State -eq 'Disabled' -and @($task.Actions).Count -eq 1 -and
          $task.Actions[0].Arguments.Contains('v20-task-live-blocked.ps1')) 'V20_08_1_TASK_NOT_DISABLED'
}
need (@($hashes | Select-Object -Unique).Count -eq 3) 'V20_08_1_ACCOUNTS_NOT_DISTINCT'
$program = @'
import json
import sqlite3
import sys
from pathlib import Path
from TradingSystemLab.stage8_robot.operations import InstanceLock
from TradingSystemLab.stage8_robot.state import StateStore
from TradingSystemLab.stage8_robot.trading_safety_gate import emergency_halt, load_kill_switch

root=Path(sys.argv[1])
hashes=sys.argv[2:]
slugs=('shallow','obv','inside')
strategies={'shallow':'SHALLOW_PULLBACK','obv':'OBV_PRESSURE','inside':'INSIDE_DAY_RELEASE'}
if root.name.casefold()!='v20lab' or len(hashes)!=3 or len(set(hashes))!=3:
    raise RuntimeError('V20_08_1_INIT_ROOT_OR_SCOPE_INVALID')
plans=[]
for slug,account_hash in zip(slugs,hashes):
    instance=root/'robots'/slug
    state=instance/'state'
    safety=instance/'safety'
    path=state/'v20-real-intents.sqlite3'
    lock_path=instance/'v20-instance.lock'
    for item in (root,root/'robots',instance,state):
        if not item.is_dir() or item.is_symlink():
            raise RuntimeError('V20_08_1_INIT_INSTANCE_PATH_INVALID_'+slug)
    for item in (safety,path,lock_path):
        if item.is_symlink():
            raise RuntimeError('V20_08_1_INIT_SYMLINK_FORBIDDEN_'+slug)
    identity={
        'schema_id':'v20.h1_state_store.real_intents.v1',
        'robot_id':'v20-'+slug,
        'strategy':strategies[slug],
        'account_sha256':account_hash,
        'mode':'V20_PRETRADE_UNAUTHORIZED',
    }
    switch,error=load_kill_switch(instance)
    if error not in (None,'KILL_SWITCH_MISSING'):
        raise RuntimeError('V20_08_1_INIT_KILL_SWITCH_INVALID_'+slug)
    if switch is not None and switch['state']!='HALTED':
        raise RuntimeError('V20_08_1_INIT_SWITCH_NOT_HALTED_'+slug)
    if path.exists():
        if not path.is_file():
            raise RuntimeError('V20_08_1_INIT_DB_NOT_FILE_'+slug)
        with sqlite3.connect(path.as_uri()+'?mode=ro',uri=True) as db:
            row=db.execute('SELECT value FROM state WHERE key=?',('database_identity',)).fetchone()
            if (not row or json.loads(row[0])!=identity or
                    db.execute('PRAGMA integrity_check').fetchone()!=('ok',) or
                    db.execute('SELECT COUNT(*) FROM intents').fetchone()[0]!=0 or
                    db.execute('SELECT COUNT(*) FROM fills').fetchone()[0]!=0):
                raise RuntimeError('V20_08_1_INIT_EXISTING_DB_INVALID_'+slug)
            for key in ('execution_halt','trial_authority_consumed','risk_reservations','session_entries'):
                record=db.execute('SELECT value FROM state WHERE key=?',(key,)).fetchone()
                if record is not None and json.loads(record[0]):
                    raise RuntimeError('V20_08_1_INIT_EXISTING_STATE_DIRTY_'+slug)
    plans.append((slug,instance,path,lock_path,identity,error))
# Local-only write begins only after all 3 scopes and unchanged H1 source pass.
for slug,instance,path,lock_path,identity,switch_error in plans:
    with InstanceLock(lock_path):
        switch,error=load_kill_switch(instance)
        if error not in (None,'KILL_SWITCH_MISSING'):
            raise RuntimeError('V20_08_1_INIT_SWITCH_CHANGED_'+slug)
        if switch is not None and switch['state']!='HALTED':
            raise RuntimeError('V20_08_1_INIT_SWITCH_ARMED_'+slug)
        if switch is None:
            emergency_halt(instance)
        switch,error=load_kill_switch(instance)
        if error or switch['state']!='HALTED':
            raise RuntimeError('V20_08_1_INIT_HALTED_NOT_PROVEN_'+slug)
        existed=path.is_file()
        state=StateStore(path,identity)
        try:
            if state.get('database_identity')!=identity:
                raise RuntimeError('V20_08_1_INIT_IDENTITY_MISMATCH_'+slug)
            if state.all_intents() or state.all_fills() or state.get('execution_halt'):
                raise RuntimeError('V20_08_1_INIT_NONEMPTY_STATE_'+slug)
        finally:
            state.close()
        print('v20_08_1_'+slug+'_ledger='+('PASS_EXISTING_CLEAN' if existed else 'PASS_H1_CREATED_EMPTY'))
        print('v20_08_1_'+slug+'_kill_switch=PASS_HALTED')
print('v20_08_1_three_local_safety=PASS_3_OF_3_HALTED')
'@
$oldPath = $env:PYTHONPATH
$oldNoBytecode = $env:PYTHONDONTWRITEBYTECODE
try {
    $env:PYTHONPATH = $source
    $env:PYTHONDONTWRITEBYTECODE = '1'
    & $python -B -c $program $root @hashes
    need ($LASTEXITCODE -eq 0) 'V20_08_1_LOCAL_SAFETY_INIT_HOLD'
} finally {
    $env:PYTHONPATH = $oldPath
    $env:PYTHONDONTWRITEBYTECODE = $oldNoBytecode
}
Write-Output 'v20_08_1_finam=NO_NETWORK'
Write-Output 'v20_08_1_orders=zero'
Write-Output 'v20_08_1_live=off'
Write-Output 'v20_08_1_tasks_modified=no'
