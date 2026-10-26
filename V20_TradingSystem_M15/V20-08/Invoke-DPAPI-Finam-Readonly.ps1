# V20-08.1: one common H1 FINAM GET-only worker for three V20 DPAPI identities.
# Does not touch Tasks, H1/M15, order/SLTP APIs or any production state.
[CmdletBinding()]
param(
    [ValidateSet('preflight','witness','frozen','authority')][string]$Mode = 'preflight',
    [ValidateSet('all','v20-shallow','v20-obv','v20-inside')][string]$Robot = 'all'
)
$ErrorActionPreference = 'Stop'
Set-StrictMode -Version Latest
$root = 'C:\V20Lab'
$source = Join-Path $root 'source-raw'
$workspace = Join-Path $root 'pretrade-08\dpapi-finam-readonly'
$python = Join-Path $root '.venv-raw\scripts\python.exe'
$receipt = Join-Path $root 'pretrade-08\DPAPI_TRADING_BINDINGS_REPORT.json'
$tasksReceipt = Join-Path $root 'staging-07\TASKS_07_2_REPORT.json'
$pin = '9c14f56ad867c1eb12eb589e80782674b78355bc'
function need([bool]$okay,[string]$code) { if (-not $okay) { throw $code } }
function digest([string]$val) {
    $sha=[Security.Cryptography.SHA256]::Create()
    try { return ([BitConverter]::ToString($sha.ComputeHash([Text.Encoding]::UTF8.GetBytes($val)))).Replace('-','').ToLowerInvariant() }
    finally { $sha.Dispose() }
}
function sid-of([string]$user) {
    if ($user -match '^S-[0-9]+(-[0-9]+)+$') { return ([Security.Principal.SecurityIdentifier]::new($user)).Value }
    return ([Security.Principal.NTAccount]::new($user)).Translate([Security.Principal.SecurityIdentifier]).Value
}
function no-link([string]$path) {
    if (Test-Path -LiteralPath $path) {
        need (-not ((Get-Item -LiteralPath $path -Force).Attributes -band [IO.FileAttributes]::ReparsePoint)) 'V20_08_1_PATH_LINK_FORBIDDEN'
    }
}
function plain([string]$cipher) {
    $secret = ConvertTo-SecureString -String $cipher -ErrorAction Stop
    $pointer = [IntPtr]::Zero
    try {
        $pointer = [Runtime.InteropServices.Marshal]::SecureStringToBSTR($secret)
        return [Runtime.InteropServices.Marshal]::PtrToStringBSTR($pointer)
    } finally {
        if ($pointer -ne [IntPtr]::Zero) { [Runtime.InteropServices.Marshal]::ZeroFreeBSTR($pointer) }
        $secret.Dispose()
    }
}
need ($env:OS -eq 'Windows_NT' -and $env:COMPUTERNAME -eq 'URIU-PC') 'V20_08_1_WRONG_INTEL'
need (Test-Path -LiteralPath $receipt -PathType Leaf) 'V20_08_1_DPAPI_RECEIPT_MISSING'
need (Test-Path -LiteralPath $tasksReceipt -PathType Leaf) 'V20_08_1_TASK_RECEIPT_MISSING'
need (Test-Path -LiteralPath $source -PathType Container) 'V20_08_1_SOURCE_MISSING'
need (Test-Path -LiteralPath $python -PathType Leaf) 'V20_08_1_PYTHON_MISSING'
foreach ($path in @($root,$source,(Join-Path $root 'pretrade-08'),$receipt,$tasksReceipt)) { no-link $path }
$report = Get-Content -LiteralPath $receipt -Raw -Encoding UTF8 | ConvertFrom-Json
$tasks = Get-Content -LiteralPath $tasksReceipt -Raw -Encoding UTF8 | ConvertFrom-Json
$sid = [Security.Principal.WindowsIdentity]::GetCurrent().User.Value
need ($report.schema -eq 'v20.08.1.dpapi_trading_bindings.v1' -and
      $report.status -eq 'PASS_3_OF_3_DPAPI_LIVE_OFF' -and
      $report.live_enabled -eq $false -and
      $report.principal_sid -eq $sid -and
      $tasks.status -eq 'PASS_3_OF_3_DISABLED' -and
      $tasks.principal_sid -eq $sid) 'V20_08_1_DPAPI_OR_SID_RECEIPT_INVALID'
# PowerShell 5.1 unrolls the single pipeline result of a right-hand if:
# one robot otherwise becomes a scalar string, and StrictMode rejects .Count.
# Retain the array type in both the 3-account and 1-account paths.
$names = @('v20-shallow','v20-obv','v20-inside')
if ($Robot -ne 'all') { $names = @($Robot) }
if ($Mode -eq 'witness') { need ($names.Count -eq 1) 'V20_08_1_WITNESS_ONE_ACCOUNT_ONLY' }
$pkg = Join-Path $workspace 'V20_TradingSystem_M15\v20_runtime'
New-Item -ItemType Directory -Path $pkg -Force | Out-Null
$files = @(
    @('finam_worker.py','b268d127241c1ee74bac545ea13b988b0c4983e8'),
    @('finam_execution.py','879c9476a1ad53febf3f368e2b498f009de70d43'),
    @('h1_state_journal.py','f9fb32a50eb712aeae4690dd85d4e7aa512ef15c')
)
$previousPins = @{
    'finam_worker.py'=@('4d9de12e0b3e9d0d0ec72d058840bb259e2ed30d','d0085f8da2d37690eb0396f7999902ee317cff5a')
    'finam_execution.py'=@('5e76df4085665559e4056f07f4ddf8b6574048ef')
}
foreach ($entry in $files) {
    $to = Join-Path $pkg $entry[0]
    no-link $to
    $replaceOld = $false
    if (Test-Path -LiteralPath $to) {
        $hash = (& git.exe hash-object -- $to).Trim().ToLowerInvariant()
        need ($LASTEXITCODE -eq 0) 'V20_08_1_WORKER_GIT_HASH_ERROR'
        if ($hash -eq $entry[1]) { continue }
        # Exactly the previous physically proven read-only worker may be
        # upgraded. All other local modifications remain hard-blocked.
        need ($previousPins.ContainsKey([string]$entry[0]) -and
              $hash -in $previousPins[[string]$entry[0]]) 'V20_08_1_WORKER_CODE_CONFLICT'
        $replaceOld = $true
    }
    $url = 'https://raw.githubusercontent.com/alkospacer123/market-pattern-discovery/' + $pin + '/V20_TradingSystem_M15/v20_runtime/' + $entry[0]
    $tmp = $to + '.download'
    need (-not (Test-Path -LiteralPath $tmp)) 'V20_08_1_PARTIAL_DOWNLOAD'
    try {
        Invoke-WebRequest -Uri $url -OutFile $tmp -UseBasicParsing
        $hash = (& git.exe hash-object -- $tmp).Trim().ToLowerInvariant()
        need ($LASTEXITCODE -eq 0 -and $hash -eq $entry[1]) 'V20_08_1_WORKER_GIT_BLOB_MISMATCH'
        if ($replaceOld) { Remove-Item -LiteralPath $to -Force -ErrorAction Stop }
        Move-Item -LiteralPath $tmp -Destination $to
    } finally {
        if (Test-Path -LiteralPath $tmp) { Remove-Item -LiteralPath $tmp -Force }
    }
}
foreach ($name in @('__init__.py','account_risk.py','offline_planner.py','frozen_adapter.py')) {
    $from = Join-Path $source ('V20_TradingSystem_M15\v20_runtime\' + $name)
    $to = Join-Path $pkg $name
    need (Test-Path -LiteralPath $from -PathType Leaf) 'V20_08_1_PINNED_DEPENDENCY_MISSING'
    no-link $to
    if (Test-Path -LiteralPath $to) {
        need ((Get-FileHash -LiteralPath $from -Algorithm SHA256).Hash -eq
              (Get-FileHash -LiteralPath $to -Algorithm SHA256).Hash) 'V20_08_1_DEPENDENCY_CONFLICT'
    } else { Copy-Item -LiteralPath $from -Destination $to }
}
# The unchanged frozen V20 adapter does not contain any signal formulas.
# Its exact V20-03 AST source and four original research files must sit
# next to the worker package at the original relative paths.
$frozenSources = @(
    @('V20-03/offline/stress_v20_03.py','f135b42219b816e7925892ac07404c61c4627cbf'),
    @('research_original_v20/base.py','b917cc9c7c99fbad38423d9f4fdfbb82767545be'),
    @('research_original_v20/run.py','7d9ddf0ef498f0c93a139c0104af2a72d0e79151'),
    @('research_original_v20/legacy_v4/study_v4.py','7749f82edcb8a04b4002978b588beeb26e484f71'),
    @('research_original_v20/legacy_v4/dependencies/study.py','1294ff9884f7a1634fab67ee330ec702e0612c31')
)
foreach ($entry in $frozenSources) {
    $relative=[string]$entry[0]
    $to=Join-Path (Join-Path $workspace 'V20_TradingSystem_M15') ($relative.Replace('/','\'))
    $from=Join-Path (Join-Path $source 'V20_TradingSystem_M15') ($relative.Replace('/','\'))
    no-link $to
    if (Test-Path -LiteralPath $to -PathType Leaf) {
        $h=(& git.exe hash-object -- $to).Trim().ToLowerInvariant()
        need ($LASTEXITCODE -eq 0 -and $h -eq $entry[1]) 'V20_08_1_FROZEN_FILE_CONFLICT'
        continue
    }
    New-Item -ItemType Directory -Path (Split-Path $to) -Force | Out-Null
    if (Test-Path -LiteralPath $from -PathType Leaf) {
        no-link $from
        $h=(& git.exe hash-object -- $from).Trim().ToLowerInvariant()
        need ($LASTEXITCODE -eq 0 -and $h -eq $entry[1]) 'V20_08_1_FROZEN_INSTALLED_HASH_MISMATCH'
        Copy-Item -LiteralPath $from -Destination $to -ErrorAction Stop
    } else {
        $url='https://raw.githubusercontent.com/alkospacer123/market-pattern-discovery/610109b736c53a5cc1025657291e272b1136b254/V20_TradingSystem_M15/'+$relative
        $tmp=$to+'.download'
        need (-not (Test-Path -LiteralPath $tmp)) 'V20_08_1_FROZEN_PARTIAL_DOWNLOAD'
        try {
            Invoke-WebRequest -Uri $url -OutFile $tmp -UseBasicParsing
            $h=(& git.exe hash-object -- $tmp).Trim().ToLowerInvariant()
            need ($LASTEXITCODE -eq 0 -and $h -eq $entry[1]) 'V20_08_1_FROZEN_REMOTE_HASH_MISMATCH'
            Move-Item -LiteralPath $tmp -Destination $to
        } finally { if (Test-Path -LiteralPath $tmp) { Remove-Item -LiteralPath $tmp -Force } }
    }
}
$frozenSmoke=@'
from datetime import datetime, timedelta
import pandas as pd
from V20_TradingSystem_M15.v20_runtime.frozen_adapter import _frozen_immutable_features
dates=[datetime(2026,9,1)+timedelta(days=day,hours=10,minutes=15*i) for day in range(12) for i in range(32)]
rows=[]
for i,t in enumerate(dates):
    p=100+i/500
    # Windows PowerShell 5.1 strips embedded double quotes from Python -c.
    # Use single-quoted Python literals for the synthetic OHLCV rows.
    rows.append({'Datetime':t,'Open':p,'High':p+0.25,'Low':p-0.25,'Close':p+0.03,'Volume':1000+i%29})
result=_frozen_immutable_features(pd.DataFrame(rows))
need={'SHALLOW_PULLBACK','OBV_PRESSURE','INSIDE_DAY_RELEASE','atr','ema50','ema200'}
assert len(result)==len(rows) and need.issubset(result.columns), 'FROZEN_FORMULA_LOAD_INVALID'
print('v20_08_1_frozen_bundle=pass_exact_locked_sources')
'@
$previousPath=$env:PYTHONPATH
$previousAccount=$env:V20_FINAM_ACCOUNT
$previousToken=$env:V20_FINAM_TOKEN
$previousHash=$env:V20_FINAM_ACCOUNT_SHA256
$previousNoBytecode=$env:PYTHONDONTWRITEBYTECODE
try {
    $env:PYTHONPATH=$workspace + [IO.Path]::PathSeparator + $source
    $env:PYTHONDONTWRITEBYTECODE='1'
    # Before decrypting any real token, prove the H1 REST adapter denies all
    # order/SLTP/DELETE and cross-account routes with synthetic credentials.
    & $python -B -m V20_TradingSystem_M15.v20_runtime.finam_worker --self-test
    need ($LASTEXITCODE -eq 0) 'V20_08_1_WORKER_SELFTEST_FAILED'
    if ($Mode -eq 'frozen') {
        & $python -B -c $frozenSmoke
        need ($LASTEXITCODE -eq 0) 'V20_08_1_FROZEN_FORMULA_SELFTEST_FAILED'
        Write-Output 'v20_08_1_frozen_sources=pass_5_of_5'
        Write-Output 'v20_08_1_live=off'
        Write-Output 'v20_08_1_orders=zero'
        return
    }
    foreach ($name in $names) {
        $rows = @($report.robots | Where-Object { $_.robot -eq $name })
        need ($rows.Count -eq 1 -and $rows[0].status -eq 'DPAPI_SID_BOUND_LIVE_OFF') 'V20_08_1_DPAPI_ROBOT_NOT_BOUND'
        $task=Get-ScheduledTask -TaskName $name -TaskPath '\' -ErrorAction Stop
        need ($task.State -eq 'Disabled' -and @($task.Actions).Count -eq 1 -and
              $task.Actions[0].Arguments.Contains('v20-task-live-blocked.ps1') -and
              (sid-of ([string]$task.Principal.UserId)) -eq $sid) 'V20_08_1_TASK_NOT_DISABLED_OR_WRONG_SID'
        $secretPath=Join-Path (Join-Path $root ('robots\' + $name.Substring(4))) 'secrets\finam.dpapi.json'
        need (Test-Path -LiteralPath $secretPath -PathType Leaf) 'V20_08_1_DPAPI_FILE_MISSING'
        no-link $secretPath
        $secret=Get-Content -LiteralPath $secretPath -Raw -Encoding UTF8 | ConvertFrom-Json
        need ($secret.schema -eq 'v20.08.1.dpapi_finam_pair.v1' -and
              $secret.robot_id -eq $name -and $secret.live_enabled -eq $false -and
              $secret.principal_sid -eq $sid -and
              $secret.account_sha256 -eq $rows[0].account_sha256) 'V20_08_1_DPAPI_FILE_SCOPE_INVALID'
        $env:V20_FINAM_ACCOUNT=plain ([string]$secret.account_dpapi)
        $env:V20_FINAM_TOKEN=plain ([string]$secret.token_dpapi)
        $env:V20_FINAM_ACCOUNT_SHA256=[string]$secret.account_sha256
        need ((digest $env:V20_FINAM_ACCOUNT) -ceq $env:V20_FINAM_ACCOUNT_SHA256) 'V20_08_1_DPAPI_ACCOUNT_DECRYPT_MISMATCH'
        try {
            $launchArgs=@('-B','-m','V20_TradingSystem_M15.v20_runtime.finam_worker','--robot',$name)
            if ($Mode -eq 'witness') { $launchArgs += '--witness-current-open' }
            if ($Mode -eq 'authority') { $launchArgs += '--authority' }
            & $python @launchArgs
            need ($LASTEXITCODE -eq 0) 'V20_08_1_WORKER_READONLY_CHECK_FAILED'
        } finally {
            Remove-Item Env:\V20_FINAM_ACCOUNT -ErrorAction SilentlyContinue
            Remove-Item Env:\V20_FINAM_TOKEN -ErrorAction SilentlyContinue
            Remove-Item Env:\V20_FINAM_ACCOUNT_SHA256 -ErrorAction SilentlyContinue
        }
    }
    $finish = if ($Mode -eq 'preflight') {'pass_get_only_'+$names.Count+'_of_'+$names.Count} elseif ($Mode -eq 'authority') {'pass_n4_authority_'+$names.Count+'_of_'+$names.Count} else {'pass_one_account_witness_mode'}
    Write-Output ('v20_08_1_worker=' + $finish)
    Write-Output 'v20_08_1_live=off'
    Write-Output 'v20_08_1_tasks_modified=no'
} finally {
    $env:PYTHONPATH=$previousPath
    $env:PYTHONDONTWRITEBYTECODE=$previousNoBytecode
    $env:V20_FINAM_ACCOUNT=$previousAccount
    $env:V20_FINAM_TOKEN=$previousToken
    $env:V20_FINAM_ACCOUNT_SHA256=$previousHash
}
