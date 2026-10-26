# V20-08.2: record owner's explicitly approved first genuine trial on 3 own accounts.
# Writes only narrow JSON grants; no FINAM/DPAPI decrypt, order, ARM or Task.
[CmdletBinding()]
param([ValidateSet('cnyrubf','usdrubf','gldrubf','imoexf')][string]$Symbol = 'cnyrubf')
$ErrorActionPreference='Stop'
Set-StrictMode -Version Latest
$root='C:\V20Lab'
$source=Join-Path $root 'source-raw'
$python=Join-Path $root '.venv-raw\scripts\python.exe'
$binding=Join-Path $root 'pretrade-08\DPAPI_TRADING_BINDINGS_REPORT.json'
$pin='e9de4acd8582009c93d67dcac299cabf51eae08e'
function need([bool]$value,[string]$code) { if (-not $value) { throw $code } }
need ($env:OS -eq 'Windows_NT' -and $env:COMPUTERNAME -eq 'URIU-PC') 'V20_08_2_WRONG_HOST'
foreach ($path in @($root,$source,$python,$binding)) {
    need (Test-Path -LiteralPath $path) 'V20_08_2_GRANT_REQUIRED_FILE_MISSING'
    need (-not ((Get-Item -LiteralPath $path -Force).Attributes -band [IO.FileAttributes]::ReparsePoint)) 'V20_08_2_GRANT_REPARSE_PATH'
}
$report=Get-Content -LiteralPath $binding -Raw -Encoding UTF8 | ConvertFrom-Json
$sid=[Security.Principal.WindowsIdentity]::GetCurrent().User.Value
need ($report.schema -eq 'v20.08.1.dpapi_trading_bindings.v1' -and
      $report.status -eq 'PASS_3_OF_3_DPAPI_LIVE_OFF' -and
      $report.principal_sid -eq $sid -and $report.live_enabled -eq $false) 'V20_08_2_GRANT_ACCOUNT_BINDING_INVALID'
$hashes=@()
foreach ($name in @('v20-shallow','v20-obv','v20-inside')) {
    $rows=@($report.robots | Where-Object { $_.robot -eq $name })
    need ($rows.Count -eq 1 -and $rows[0].status -eq 'DPAPI_SID_BOUND_LIVE_OFF' -and
          [string]$rows[0].account_sha256 -match '^[0-9a-f]{64}$') 'V20_08_2_GRANT_ROBOT_BINDING_INVALID'
    $hashes += [string]$rows[0].account_sha256
    $task=Get-ScheduledTask -TaskName $name -TaskPath '\' -ErrorAction Stop
    need ($task.State -eq 'Disabled' -and @($task.Actions).Count -eq 1 -and
          $task.Actions[0].Arguments.Contains('v20-task-live-blocked.ps1')) 'V20_08_2_GRANT_TASK_NOT_DISABLED'
}
need (@($hashes | Select-Object -Unique).Count -eq 3) 'V20_08_2_GRANT_ACCOUNT_NOT_DISTINCT'
$program=@'
import json
import os
import sqlite3
import sys
from pathlib import Path
from TradingSystemLab.stage8_robot.trading_safety_gate import load_kill_switch

root=Path(sys.argv[1])
source_sha=sys.argv[2]
symbol=sys.argv[3].upper()
hashes=sys.argv[4:]
slugs=('shallow','obv','inside')
if (root.name.casefold()!='v20lab' or len(hashes)!=3 or len(set(hashes))!=3
        or symbol not in ('CNYRUBF','USDRUBF','GLDRUBF','IMOEXF')):
    raise RuntimeError('V20_08_2_GRANT_SCOPE_INVALID')
plan=[]
for slug,account_hash in zip(slugs,hashes):
    instance=root/'robots'/slug
    safety=instance/'safety'
    dbfile=instance/'state'/'v20-real-intents.sqlite3'
    grant=safety/'v20-first-signal-approval.json'
    permit=safety/'v20-single-trial-approval.json'
    if not instance.is_dir() or not safety.is_dir() or safety.is_symlink():
        raise RuntimeError('V20_08_2_GRANT_DIRECTORY_INVALID_'+slug)
    for p in (grant,permit,dbfile):
        if p.is_symlink():
            raise RuntimeError('V20_08_2_GRANT_SYMLINK_FORBIDDEN_'+slug)
    switch,error=load_kill_switch(instance)
    if error or not switch or switch['state']!='HALTED':
        raise RuntimeError('V20_08_2_GRANT_KILL_SWITCH_NOT_HALTED_'+slug)
    if not dbfile.is_file():
        raise RuntimeError('V20_08_2_GRANT_LEDGER_NOT_INITIALIZED_'+slug)
    with sqlite3.connect(dbfile.as_uri()+'?mode=ro',uri=True) as db:
        if db.execute('PRAGMA integrity_check').fetchone()!=('ok',):
            raise RuntimeError('V20_08_2_GRANT_LEDGER_INTEGRITY_'+slug)
        row=db.execute('SELECT value FROM state WHERE key=?',('database_identity',)).fetchone()
        identity=json.loads(row[0]) if row else {}
        if (identity.get('account_sha256')!=account_hash
                or identity.get('robot_id')!='v20-'+slug
                or db.execute('SELECT COUNT(*) FROM intents').fetchone()[0]!=0):
            raise RuntimeError('V20_08_2_GRANT_LEDGER_NOT_EMPTY_OR_WRONG_ACCOUNT_'+slug)
    if permit.exists():
        raise RuntimeError('V20_08_2_GRANT_EXACT_PERMIT_ALREADY_EXISTS_'+slug)
    record={
        'schema':'v20.08.2.first_signal_approval.v1',
        'scope':'ONE_FIRST_REAL_FROZEN_TRIAL_ONLY',
        'robot_id':'v20-'+slug,
        'account_sha256':account_hash,
        'source_commit':source_sha,
        'instrument':symbol,
        'max_risk_fraction':'0.015',
        'explicit_owner_approval':True,
    }
    if grant.exists():
        if not grant.is_file() or json.loads(grant.read_text(encoding='utf-8'))!=record:
            raise RuntimeError('V20_08_2_GRANT_CONFLICT_'+slug)
    plan.append((slug,grant,record))
for slug,path,record in plan:
    if not path.exists():
        with path.open('x',encoding='utf-8',newline='\n') as output:
            json.dump(record,output,sort_keys=True,separators=(',',':'))
            output.write('\n')
            output.flush()
            os.fsync(output.fileno())
    print('v20_08_2_'+slug+'_owner_scope=PASS_FIRST_REAL_SIGNAL_ONE_ENTRY')
print('v20_08_2_first_signal_scopes=PASS_3_OF_3_HALTED')
'@
$oldPath=$env:PYTHONPATH
$oldBytecode=$env:PYTHONDONTWRITEBYTECODE
try {
    $env:PYTHONPATH=$source
    $env:PYTHONDONTWRITEBYTECODE='1'
    & $python -B -c $program $root $pin $Symbol @hashes
    need ($LASTEXITCODE -eq 0) 'V20_08_2_GRANT_LOCAL_HOLD'
} finally {
    $env:PYTHONPATH=$oldPath
    $env:PYTHONDONTWRITEBYTECODE=$oldBytecode
}
Write-Output 'v20_08_2_finam=NO_NETWORK'
Write-Output 'v20_08_2_orders=zero'
Write-Output 'v20_08_2_live=off'
Write-Output 'v20_08_2_tasks_modified=no'
