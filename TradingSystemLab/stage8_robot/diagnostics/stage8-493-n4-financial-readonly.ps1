param(
    [string]$Python = 'c:\tslaudit\fill493\venv\scripts\python.exe',
    [string]$Output = 'c:\tslaudit\fill493\stage8-493-n4-financial-readonly-20261013.json'
)
$ErrorActionPreference = 'Stop'
$root = 'c:\tradingsystemlab\runtime'
$checkout = 'c:\tradingsystemlab\production\h1-184e8c2-20261012'
$source = 'c:\tradingsystemlab\stage8-493-n4-financial-readonly.py'
$source_sha256 = '8ABAE05EB541DC5236266E314BFE0CB38601EF8EDD0E2F84445A30EB75617CA6'
$probe = 'c:\tradingsystemlab\stage8-493-post-isolation-readonly.ps1'
$probe_sha256 = '37DF9E1A8F4B0B18EE37D1ACC8757AD674160E878264B2746ED0E1BB3E66C201'
$spec = 'PROD_STAGE7_46DB784378797C7FB04636892350AFF21006D71A31F2CED9D4B974EDA2DC36B8'
$credential = $null
$priorBytecode = [Environment]::GetEnvironmentVariable('PYTHONDONTWRITEBYTECODE','Process')
Write-Output '=== Stage8 #493 N4 financial readonly evidence ==='
Write-Output 'NO_TRADING_TOKEN NO_ORDER_OR_CANCEL NO_TASK_MUTATION NO_REARM NO_LIVE_SQLITE_WRITE'
try {
    if (-not (Test-Path -LiteralPath $source -PathType Leaf) -or
        (Get-FileHash -LiteralPath $source -Algorithm SHA256).Hash -cne $source_sha256) {
        throw 'EXACT_FINANCIAL_PYTHON_SOURCE_HASH_MISMATCH'
    }
    if (-not (Test-Path -LiteralPath $probe -PathType Leaf) -or
        (Get-FileHash -LiteralPath $probe -Algorithm SHA256).Hash -cne $probe_sha256) {
        throw 'EXACT_POST_ISOLATION_SOURCE_HASH_MISMATCH'
    }
    Write-Output 'EXACT_READONLY_SOURCE_HASHES=PASS'
    if (-not (Test-Path -LiteralPath $Python -PathType Leaf)) { throw 'EXISTING_PYTHON_NOT_FOUND' }
    if (Test-Path -LiteralPath $Output) { throw 'CREATE_ONLY_FINANCIAL_REPORT_ALREADY_EXISTS' }
    $head = (& git -C $checkout rev-parse HEAD).Trim()
    if ($LASTEXITCODE -ne 0 -or $head -cne '184e8c2b8fa092a606249ff293a4f507160bff29') { throw 'PINNED_LIVE_CHECKOUT_CHANGED' }

    # The physically proven wrapper checks disabled Task, HALTED, process-zero,
    # lock release, read-only production SQLite, and two fresh account/orders GETs.
    $before = @(& powershell.exe -NoProfile -ExecutionPolicy Bypass -File $probe -python $Python)
    $beforeCode = $LASTEXITCODE
    $markers = @('TASK_DISABLED_AND_PROCESS_ZERO=PASS', 'LOCK_HANDLE_QUIESCENT=PASS',
                 'SQLITE_POST_STOP_BEFORE_AFTER=PASS', 'FINAM_POST_STOP_TWO_SNAPSHOTS=PASS',
                 'CLASSIFICATION=POST_ISOLATION_READONLY_PASS_NO_TRADE_AUTHORITY')
    $good = ($beforeCode -eq 0)
    foreach ($marker in $markers) {
        if (@($before | Where-Object { $_ -ceq $marker }).Count -ne 1) { $good = $false }
    }
    if (-not $good) { throw 'FRESH_POST_ISOLATION_READONLY_GATE_FAILED' }
    Write-Output 'FRESH_POST_ISOLATION_READONLY_GATE=PASS'

    # Only the existing exact CurrentUser REAL_READONLY store is permitted.
    . (Join-Path $checkout 'TradingSystemLab\stage8_robot\deploy\windows\credential-store.ps1')
    $credential = Get-ReadonlyCredential $root $spec
    $env:stage8_493_readonly_secret = [string]$credential.finam_api_secret
    $env:stage8_493_readonly_account = [string]$credential.finam_real_account_id
    [Environment]::SetEnvironmentVariable('PYTHONDONTWRITEBYTECODE','1','Process')
    $result = @(& $Python -B $source --runtime-root $root --checkout $checkout --output $Output)
    $resultCode = $LASTEXITCODE
    if ($resultCode -ne 0 -or
        @($result | Where-Object { $_ -ceq 'CLASSIFICATION=BROKER_N4_ACCOUNT_ASSET_PARAMS_READONLY_PASS_NO_TRADE_AUTHORITY' }).Count -ne 1 -or
        @($result | Where-Object { $_ -ceq 'REAL_ORDER_AUTHORIZED=NO' }).Count -ne 1) {
        # The Python child reports a sanitized uppercase error only. Never echo
        # arbitrary stdout/stderr, which could contain sensitive broker details.
        $safe = @($result | Where-Object { $_ -cmatch '^CLASSIFICATION=BLOCKED:[A-Z0-9_]{4,120}
    $task = Get-ScheduledTask -TaskName 'TradingSystemLab-Stage8-Production' -TaskPath '\' -ErrorAction Stop
    $sw = Get-Content -LiteralPath (Join-Path $root 'safety\stage8-trading-kill-switch.json') -Raw | ConvertFrom-Json
    if ([string]$task.State -cne 'Disabled' -or [bool]$task.Settings.Enabled -ne $false -or
        $sw.state -cne 'HALTED' -or $sw.production_specification_id -cne $spec) {
        throw 'POST_FINANCIAL_PRODUCTION_AUTHORITY_CHANGED'
    }
    if (-not (Test-Path -LiteralPath $Output -PathType Leaf)) { throw 'FINANCIAL_REPORT_NOT_CREATED' }
    Write-Output 'FINAM_N4_FINANCIAL_GET_READONLY=PASS'
    Write-Output ('REPORT_SHA256=' + (Get-FileHash -LiteralPath $Output -Algorithm SHA256).Hash)
    Write-Output 'CLASSIFICATION=STAGE8_493_N4_FINANCIAL_READONLY_REPORT_CREATED_NOT_TRADE_AUTHORITY'
    Write-Output 'FEES_REALIZED_R15_AND_TWO_CONTRACT_ELIGIBILITY=NOT_VERIFIED'
} catch {
    $code = [string]$_.Exception.Message
    if ($code -cnotmatch '^[A-Z0-9_]{4,120}$') { $code = 'FINANCIAL_READONLY_UNEXPECTED' }
    Write-Output "CLASSIFICATION=BLOCKED:$code"
    exit 1
} finally {
    Remove-Item Env:stage8_493_readonly_secret -ErrorAction SilentlyContinue
    Remove-Item Env:stage8_493_readonly_account -ErrorAction SilentlyContinue
    $credential = $null
    [Environment]::SetEnvironmentVariable('PYTHONDONTWRITEBYTECODE',$priorBytecode,'Process')
    Write-Output 'NO_REAL_ORDER_AUTHORIZATION=YES'
}
 })
        if ($safe.Count -eq 1) { Write-Output ('FINANCIAL_CHILD_' + $safe[0]) }
        throw 'FINANCIAL_READONLY_COLLECTION_BLOCKED'
    }
    $task = Get-ScheduledTask -TaskName 'TradingSystemLab-Stage8-Production' -TaskPath '\' -ErrorAction Stop
    $sw = Get-Content -LiteralPath (Join-Path $root 'safety\stage8-trading-kill-switch.json') -Raw | ConvertFrom-Json
    if ([string]$task.State -cne 'Disabled' -or [bool]$task.Settings.Enabled -ne $false -or
        $sw.state -cne 'HALTED' -or $sw.production_specification_id -cne $spec) {
        throw 'POST_FINANCIAL_PRODUCTION_AUTHORITY_CHANGED'
    }
    if (-not (Test-Path -LiteralPath $Output -PathType Leaf)) { throw 'FINANCIAL_REPORT_NOT_CREATED' }
    Write-Output 'FINAM_N4_FINANCIAL_GET_READONLY=PASS'
    Write-Output ('REPORT_SHA256=' + (Get-FileHash -LiteralPath $Output -Algorithm SHA256).Hash)
    Write-Output 'CLASSIFICATION=STAGE8_493_N4_FINANCIAL_READONLY_REPORT_CREATED_NOT_TRADE_AUTHORITY'
    Write-Output 'FEES_REALIZED_R15_AND_TWO_CONTRACT_ELIGIBILITY=NOT_VERIFIED'
} catch {
    $code = [string]$_.Exception.Message
    if ($code -cnotmatch '^[A-Z0-9_]{4,120}$') { $code = 'FINANCIAL_READONLY_UNEXPECTED' }
    Write-Output "CLASSIFICATION=BLOCKED:$code"
    exit 1
} finally {
    Remove-Item Env:stage8_493_readonly_secret -ErrorAction SilentlyContinue
    Remove-Item Env:stage8_493_readonly_account -ErrorAction SilentlyContinue
    $credential = $null
    [Environment]::SetEnvironmentVariable('PYTHONDONTWRITEBYTECODE',$priorBytecode,'Process')
    Write-Output 'NO_REAL_ORDER_AUTHORIZATION=YES'
}
