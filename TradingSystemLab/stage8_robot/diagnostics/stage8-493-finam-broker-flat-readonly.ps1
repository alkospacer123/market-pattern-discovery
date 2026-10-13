param(
    [string]$runtime_root = 'c:\tradingsystemlab\runtime',
    [string]$checkout = 'c:\tradingsystemlab\production\h1-184e8c2-20261012',
    [string]$python = 'c:\tradingsystemlab\runtime\venv\scripts\python.exe'
)
$ErrorActionPreference = 'Stop'
$script_file = Join-Path $PSScriptRoot 'stage8-493-finam-broker-flat-readonly.py'
$python_sha = '02dc0b6ada60ce51bfdc9afbb4d54ca3407d0a3cdd94c3ad88e6eb7a78ab8bbe'
$live_sha = '184e8c2b8fa092a606249ff293a4f507160bff29'
$spec = 'PROD_STAGE7_46DB784378797C7FB04636892350AFF21006D71A31F2CED9D4B974EDA2DC36B8'
$credential = $null
$old_no_bytecode = [Environment]::GetEnvironmentVariable('PYTHONDONTWRITEBYTECODE', 'Process')
Write-Output '=== stage8 #493 fresh broker readonly flatness check ==='
Write-Output 'NO_TRADING_TOKEN NO_LIVE_SQLITE NO_ORDER_POST NO_CANCEL NO_TASK_CHANGE NO_REARM'
try {
    if (-not (Test-Path -LiteralPath $script_file -PathType Leaf) -or
        (Get-FileHash -LiteralPath $script_file -Algorithm SHA256).Hash.ToLowerInvariant() -cne $python_sha) {
        throw 'READONLY_PROBE_PYTHON_HASH_INVALID'
    }
    if (-not (Test-Path -LiteralPath $python -PathType Leaf)) { throw 'ISOLATED_PYTHON_NOT_FOUND' }
    if (-not (Test-Path -LiteralPath $checkout -PathType Container)) { throw 'PINNED_CHECKOUT_NOT_FOUND' }
    if (-not (Test-Path -LiteralPath $runtime_root -PathType Container)) { throw 'RUNTIME_ROOT_NOT_FOUND' }
    $commit = (& git -C $checkout rev-parse HEAD).Trim()
    if ($LASTEXITCODE -ne 0 -or $commit -cne $live_sha) { throw 'PINNED_CHECKOUT_COMMIT_MISMATCH' }
    $dirty = @(& git -C $checkout status --porcelain)
    if ($LASTEXITCODE -ne 0 -or $dirty.Count -ne 0) { throw 'PINNED_CHECKOUT_NOT_CLEAN' }
    $task = Get-ScheduledTask -TaskName 'TradingSystemLab-Stage8-Production' -ErrorAction Stop
    $readonly_task = Get-ScheduledTask -TaskName 'TradingSystemLab-Stage8-Readonly' -ErrorAction SilentlyContinue
    if ([string]$task.State -cne 'Running') { throw 'PRODUCTION_TASK_NOT_RUNNING_FOR_READONLY_OBSERVATION' }
    if ($null -ne $readonly_task -and [string]$readonly_task.State -cne 'Disabled') { throw 'READONLY_TASK_NOT_DISABLED' }
    $arguments = (@($task.Actions | ForEach-Object { [string]$_.Arguments }) -join ' ')
    if ($arguments.IndexOf($live_sha, [StringComparison]::OrdinalIgnoreCase) -lt 0 -or
        $arguments.IndexOf($checkout, [StringComparison]::OrdinalIgnoreCase) -lt 0 -or
        $arguments.IndexOf($runtime_root, [StringComparison]::OrdinalIgnoreCase) -lt 0) {
        throw 'PRODUCTION_TASK_EXACT_BINDING_UNVERIFIED'
    }
    $switch = Get-Content -LiteralPath (Join-Path $runtime_root 'safety\stage8-trading-kill-switch.json') -Raw | ConvertFrom-Json
    if ($switch.production_specification_id -cne $spec -or $switch.state -cne 'HALTED') {
        throw 'KILL_SWITCH_NOT_HALTED'
    }
    # The credential-store source defines methods; only Get-ReadonlyCredential is called.
    . (Join-Path $checkout 'TradingSystemLab\stage8_robot\deploy\windows\credential-store.ps1')
    $credential = Get-ReadonlyCredential $runtime_root $spec
    $env:stage8_493_readonly_secret = [string]$credential.finam_api_secret
    $env:stage8_493_readonly_account = [string]$credential.finam_real_account_id
    $env:PYTHONDONTWRITEBYTECODE = '1'
    & $python -B $script_file --runtime-root $runtime_root --checkout $checkout
    if ($LASTEXITCODE -ne 0) { throw 'FINAM_READONLY_FLAT_PROBE_BLOCKED' }
    $task_after = Get-ScheduledTask -TaskName 'TradingSystemLab-Stage8-Production' -ErrorAction Stop
    if ([string]$task_after.State -cne 'Running') { throw 'PRODUCTION_TASK_CHANGED_DURING_PROBE' }
    $sw_after = Get-Content -LiteralPath (Join-Path $runtime_root 'safety\stage8-trading-kill-switch.json') -Raw | ConvertFrom-Json
    if ($sw_after.state -cne 'HALTED') { throw 'KILL_SWITCH_CHANGED_DURING_PROBE' }
    Write-Output 'LOCAL_PRODUCTION_TASK_STILL_RUNNING=YES'
    Write-Output 'FINAL_READONLY_BROKER_GATE=PASS'
} catch {
    $code = [string]$_.Exception.Message
    if ($code -cnotmatch '^[A-Z0-9_]{4,128}$') { $code = 'READONLY_PRECHECK_EXCEPTION' }
    Write-Output "FINAL_READONLY_BROKER_GATE=BLOCKED:$code"
    Write-Output 'NO_ORDER_ENDPOINTS=YES'
    throw
} finally {
    Remove-Item Env:stage8_493_readonly_secret -ErrorAction SilentlyContinue
    Remove-Item Env:stage8_493_readonly_account -ErrorAction SilentlyContinue
    [Environment]::SetEnvironmentVariable('PYTHONDONTWRITEBYTECODE', $old_no_bytecode, 'Process')
    $credential = $null
}
