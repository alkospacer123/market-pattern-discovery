param(
    [string]$runtime_root = 'c:\tradingsystemlab\runtime',
    [string]$python = 'c:\tslaudit\fill493\venv\scripts\python.exe',
    [string]$previously_accepted_probe = 'c:\tradingsystemlab\stage8-493-post-isolation-readonly.ps1'
)
$ErrorActionPreference = 'Stop'
$expected_probe_sha256 = '37DF9E1A8F4B0B18EE37D1ACC8757AD674160E878264B2746ED0E1BB3E66C201'
$spec = 'PROD_STAGE7_46DB784378797C7FB04636892350AFF21006D71A31F2CED9D4B974EDA2DC36B8'
Write-Output '=== Stage 8 #493 real acceptance READONLY preflight only ==='
Write-Output 'NO_TRADE_TOKEN NO_ORDER_OR_CANCEL NO_TASK_MUTATION NO_REARM NO_LIVE_SQLITE_WRITES'
try {
    if (-not (Test-Path -LiteralPath $runtime_root -PathType Container) -or
        -not (Test-Path -LiteralPath $python -PathType Leaf) -or
        -not (Test-Path -LiteralPath $previously_accepted_probe -PathType Leaf)) {
        throw 'READONLY_PREFLIGHT_INPUT_MISSING'
    }
    $sha = (Get-FileHash -LiteralPath $previously_accepted_probe -Algorithm SHA256).Hash
    if ($sha -cne $expected_probe_sha256) { throw 'ACCEPTED_READONLY_PROBE_HASH_MISMATCH' }
    $task = Get-ScheduledTask -TaskName 'TradingSystemLab-Stage8-Production' -TaskPath '\' -ErrorAction Stop
    $readonly_task = Get-ScheduledTask -TaskName 'TradingSystemLab-Stage8-Readonly' -ErrorAction SilentlyContinue
    $switch = Get-Content -LiteralPath (Join-Path $runtime_root 'safety\stage8-trading-kill-switch.json') -Raw -ErrorAction Stop | ConvertFrom-Json
    if ([string]$task.State -cne 'Disabled' -or
        ($null -ne $readonly_task -and [string]$readonly_task.State -cne 'Disabled') -or
        $switch.schema_id -cne 'stage8_trading_kill_switch.v1' -or
        $switch.state -cne 'HALTED' -or
        $switch.production_specification_id -cne $spec) {
        throw 'PRODUCTION_ISOLATION_AUTHORITY_INVALID'
    }
    Write-Output 'PRE_BROKER_TASK_DISABLED_HALTED=PASS'
    Write-Output "ACCEPTED_POST_ISOLATION_PROBE_SHA256=$sha"
    # This hash-pinned prior Intel probe uses only a bound READONLY FINAM session,
    # GET account/orders twice, live SQLite RO and held-lock checking. Its
    # session-authentication POST is NOT a trading-order endpoint.
    $reply = @(& powershell.exe -NoProfile -ExecutionPolicy Bypass -File $previously_accepted_probe -runtime_root $runtime_root -python $python)
    $code = $LASTEXITCODE
    foreach ($line in $reply) {
        if ($line -match '^(===|NO_|FINAM_|SNAPSHOT_|SQLITE_|TASK_|LOCK_|POST_|CLASSIFICATION=|PRODUCTION_|READONLY_|LIVE_)') {
            Write-Output $line
        }
    }
    if ($code -ne 0 -or
        @($reply | Where-Object { $_ -ceq 'CLASSIFICATION=POST_ISOLATION_READONLY_PASS_NO_TRADE_AUTHORITY' }).Count -ne 1 -or
        @($reply | Where-Object { $_ -ceq 'POST_ISOLATION_BROKER_FLAT=PASS' }).Count -ne 1 -or
        @($reply | Where-Object { $_ -ceq 'FINAM_SESSION=EXACT_READONLY_ACCOUNT_BOUND' }).Count -ne 1 -or
        @($reply | Where-Object { $_ -ceq 'NO_ORDER_OR_CANCEL=YES' }).Count -ne 1) {
        throw 'POST_ISOLATION_BROKER_NOT_FRESHLY_VERIFIED'
    }
    $task_after = Get-ScheduledTask -TaskName 'TradingSystemLab-Stage8-Production' -TaskPath '\' -ErrorAction Stop
    $switch_after = Get-Content -LiteralPath (Join-Path $runtime_root 'safety\stage8-trading-kill-switch.json') -Raw | ConvertFrom-Json
    if ([string]$task_after.State -cne 'Disabled' -or $switch_after.state -cne 'HALTED' -or
        $switch_after.production_specification_id -cne $spec) {
        throw 'POST_BROKER_PRODUCTION_AUTHORITY_CHANGED'
    }
    Write-Output 'CLASSIFICATION=STAGE8_493_READONLY_FLAT_ISOLATED_PASS_NOT_REAL_ORDER_AUTHORITY'
    Write-Output 'FRESH_MARGIN_FEES_TICK_FILL_HISTORY=NOT_VERIFIED'
    Write-Output 'REAL_MULTIFILL_SLTP=NOT_TESTED'
} catch {
    $code = [string]$_.Exception.Message
    if ($code -cnotmatch '^[A-Z0-9_]{4,120}$') { $code = 'READONLY_PREFLIGHT_UNEXPECTED' }
    Write-Output "CLASSIFICATION=BLOCKED:$code"
    exit 1
} finally {
    Write-Output 'LIVE_TASK_MUTATED=NO'
    Write-Output 'REAL_ORDER_AUTHORIZED=NO'
    Write-Output 'PRODUCTION_CHECKOUT_MUTATED=NO'
}
