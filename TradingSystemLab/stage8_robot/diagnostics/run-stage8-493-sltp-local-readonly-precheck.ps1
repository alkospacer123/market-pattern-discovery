param(
    [string]$runtime_root = 'c:\tradingsystemlab\runtime'
)
$ErrorActionPreference = 'Stop'
$expected_spec = 'PROD_STAGE7_46DB784378797C7FB04636892350AFF21006D71A31F2CED9D4B974EDA2DC36B8'
$expected_live_commit = '184e8c2b8fa092a606249ff293a4f507160bff29'
Write-Output '=== TradingSystemLab Stage8 #493 physical SLTP acceptance LOCAL READONLY gate ==='
Write-Output 'NO_FINAM_NO_SQLITE_NO_CREDENTIALS_NO_ORDER_POST_NO_TASK_CHANGE_NO_HALT_NO_REARM'
Write-Output 'THIS_IS_NOT_PHYSICAL_BROKER_ACCEPTANCE'
try {
    $root = [System.IO.Path]::GetFullPath($runtime_root)
    if (-not (Test-Path -LiteralPath $root -PathType Container)) { throw 'RUNTIME_ROOT_MISSING' }
    $prod_task = Get-ScheduledTask -TaskName 'TradingSystemLab-Stage8-Production' -ErrorAction Stop
    $ro_task = Get-ScheduledTask -TaskName 'TradingSystemLab-Stage8-Readonly' -ErrorAction SilentlyContinue
    $switch_file = Join-Path $root 'safety\stage8-trading-kill-switch.json'
    $heartbeat_file = Join-Path $root 'diagnostics\stage8-12-4-production-heartbeat.json'
    if (-not (Test-Path -LiteralPath $switch_file -PathType Leaf)) { throw 'KILL_SWITCH_MISSING' }
    if (-not (Test-Path -LiteralPath $heartbeat_file -PathType Leaf)) { throw 'PRODUCTION_HEARTBEAT_MISSING' }
    $switch = Get-Content -LiteralPath $switch_file -Raw -Encoding UTF8 | ConvertFrom-Json
    $hb = Get-Content -LiteralPath $heartbeat_file -Raw -Encoding UTF8 | ConvertFrom-Json
    if ($switch.schema_id -cne 'stage8_trading_kill_switch.v1' -or
        $switch.production_specification_id -cne $expected_spec -or
        $switch.state -cnotin @('ARMED','HALTED') -or
        $hb.schema_id -cne 'stage8_12_4_production_heartbeat.v1' -or
        $hb.production_specification_id -cne $expected_spec -or
        $hb.active_identity -cne 'TRAIL1__N4_01__FULL__R15') { throw 'FROZEN_RUNTIME_IDENTITY_INVALID' }
    if ($hb.accepted_code_commit -cne $expected_live_commit) { throw 'LIVE_CODE_COMMIT_UNEXPECTED' }
    if ($hb.open_position_count -isnot [int] -and $hb.open_position_count -isnot [long]) { throw 'POSITION_COUNT_INVALID' }
    if ($hb.unresolved_intent_count -isnot [int] -and $hb.unresolved_intent_count -isnot [long]) { throw 'INTENT_COUNT_INVALID' }
    if ($hb.active_protective_stop_count -isnot [int] -and $hb.active_protective_stop_count -isnot [long]) { throw 'STOP_COUNT_INVALID' }
    $time = [DateTimeOffset]::Parse([string]$hb.timestamp)
    $age = ([DateTimeOffset]::UtcNow - $time).TotalSeconds
    $fresh = $age -ge -60 -and $age -le 900
    $prod_state = [string]$prod_task.State
    $ro_state = if ($null -eq $ro_task) { 'MISSING' } else { [string]$ro_task.State }
    Write-Output "PRODUCTION_TASK_STATE=$prod_state"
    Write-Output "READONLY_TASK_STATE=$ro_state"
    Write-Output "KILL_SWITCH_STATE=$($switch.state)"
    Write-Output "PRODUCTION_HEALTH=$($hb.health_status)"
    Write-Output "RECONCILIATION=$($hb.reconciliation_status)"
    Write-Output "LAST_CYCLE=$($hb.cycle_count)"
    Write-Output "LOCAL_OPEN_POSITION_COUNT=$($hb.open_position_count)"
    Write-Output "LOCAL_UNRESOLVED_INTENT_COUNT=$($hb.unresolved_intent_count)"
    Write-Output "LOCAL_ACTIVE_STOP_COUNT=$($hb.active_protective_stop_count)"
    Write-Output "HEARTBEAT_FRESH=$fresh"
    if ($switch.state -eq 'ARMED' -or $prod_state -ne 'Disabled') {
        Write-Output 'classification=BLOCKED_LIVE_PRODUCTION_NOT_ISOLATED'
    } elseif ($hb.open_position_count -ne 0 -or $hb.unresolved_intent_count -ne 0 -or $hb.active_protective_stop_count -ne 0) {
        Write-Output 'classification=BLOCKED_LAST_HEARTBEAT_NOT_FLAT'
    } elseif ($hb.health_status -cne 'HEALTHY' -or $hb.reconciliation_status -cne 'PASS') {
        Write-Output 'classification=BLOCKED_LAST_HEARTBEAT_UNHEALTHY'
    } elseif (-not $fresh) {
        Write-Output 'classification=LOCAL_ONLY_PREVIOUS_HEARTBEAT_STALE'
    } else {
        Write-Output 'classification=LOCAL_READONLY_GATE_PASS_NOT_BROKER_ACCEPTANCE'
    }
    Write-Output 'FRESH_FINAM_POSITION_ORDER_AND_MARGIN_AUTHORITY=NOT_COLLECTED'
    Write-Output 'REAL_PARTIAL_FILL_SLTP_ACCEPTANCE=NOT_RUN'
    Write-Output 'REAL_ORDER_AUTHORIZATION=NOT_GRANTED_BY_THIS_SCRIPT'
    Write-Output 'NO_LIVE_CHANGES=YES'
} catch {
    $error_code = [string]$_.Exception.Message
    if ($error_code -notmatch '^[A-Z0-9_]{4,100}$') { $error_code = 'LOCAL_PREFLIGHT_EXCEPTION' }
    Write-Output "classification=BLOCKED_LOCAL_PREFLIGHT:$error_code"
    Write-Output 'NO_LIVE_CHANGES=YES'
    exit 1
}
