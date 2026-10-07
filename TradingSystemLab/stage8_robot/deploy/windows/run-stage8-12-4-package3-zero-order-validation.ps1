param(
    [Parameter(Mandatory=$true)][string]$RuntimeRoot,
    [Parameter(Mandatory=$true)][string]$Stage5DataRoot,
    [Parameter(Mandatory=$true)][ValidatePattern('^[0-9a-f]{40}$')][string]$AcceptedCommit,
    [string]$Python = "",
    [string]$ReportPath = ""
)

$ErrorActionPreference = "Stop"
$productionId = "PROD_STAGE7_46DB784378797C7FB04636892350AFF21006D71A31F2CED9D4B974EDA2DC36B8"
$productionIdentity = "TRAIL1__N4_01__FULL__R15"
$stage5Commit = "50f1fd2178c18b7ab3bd969be82ad01f47a34745"
$productionTaskName = "TradingSystemLab-Stage8-Production"
$readonlyTaskName = "TradingSystemLab-Stage8-Readonly"
$repo = (Resolve-Path (Join-Path $PSScriptRoot "..\..\..\..")).Path
$runtime = [IO.Path]::GetFullPath($RuntimeRoot)
$stage5 = [IO.Path]::GetFullPath($Stage5DataRoot)
if (-not $Python) { $Python = Join-Path $runtime "venv\Scripts\python.exe" }
if (-not $ReportPath) { $ReportPath = Join-Path $runtime "diagnostics\stage8_12_4_package3_zero_order_validation.json" }
$report = [IO.Path]::GetFullPath($ReportPath)

function Require-ReadonlyDisabledOrAbsent {
    $task = Get-ScheduledTask -TaskName $readonlyTaskName -ErrorAction SilentlyContinue
    if ($task -and $task.State -ne "Disabled") { throw "STAGE8_12_4_PACKAGE3_READONLY_TASK_NOT_DISABLED" }
    return $(if ($task) { "Disabled" } else { "Absent" })
}

function Require-ProductionTaskDisabledExact {
    $task = Get-ScheduledTask -TaskName $productionTaskName -ErrorAction SilentlyContinue
    if (-not $task) { throw "STAGE8_12_4_PACKAGE3_PRODUCTION_TASK_MISSING" }
    if ($task.State -ne "Disabled") { throw "STAGE8_12_4_PACKAGE3_PRODUCTION_TASK_NOT_DISABLED" }
    if (@($task.Actions).Count -ne 1) { throw "STAGE8_12_4_PACKAGE3_PRODUCTION_TASK_ACTION_INVALID" }
    $action = @($task.Actions)[0]
    $arguments = [string]$action.Arguments
    if (
        [string]::IsNullOrWhiteSpace($arguments) -or
        $arguments -notlike "*run-production.ps1*" -or
        $arguments -notlike "*-ExpectedCommit $AcceptedCommit*" -or
        $arguments -notlike "*$runtime*" -or
        $arguments -notlike "*$stage5*"
    ) {
        throw "STAGE8_12_4_PACKAGE3_PRODUCTION_TASK_BINDING_MISMATCH"
    }
    $currentName = [Security.Principal.WindowsIdentity]::GetCurrent().Name
    if ([string]$task.Principal.UserId -cne $currentName) { throw "STAGE8_12_4_PACKAGE3_PRODUCTION_TASK_PRINCIPAL_MISMATCH" }
    return $task
}

function Require-InactiveSafety {
    $authPath = Join-Path $runtime "safety\stage8-12-4-production-authorization.json"
    if (Test-Path $authPath) { throw "STAGE8_12_4_PACKAGE3_AUTHORIZATION_MUST_BE_ABSENT" }
    $killPath = Join-Path $runtime "safety\stage8-trading-kill-switch.json"
    if (-not (Test-Path $killPath -PathType Leaf)) { throw "STAGE8_12_4_PACKAGE3_KILL_SWITCH_MISSING" }
    try { $kill = Get-Content $killPath -Raw | ConvertFrom-Json -ErrorAction Stop }
    catch { throw "STAGE8_12_4_PACKAGE3_KILL_SWITCH_INVALID" }
    if (
        $kill.schema_id -cne "stage8_trading_kill_switch.v1" -or
        $kill.production_specification_id -cne $productionId -or
        $kill.state -cne "HALTED"
    ) {
        throw "STAGE8_12_4_PACKAGE3_KILL_SWITCH_NOT_HALTED"
    }
    return $kill
}

if (-not (Test-Path $runtime -PathType Container)) { throw "STAGE8_12_4_PACKAGE3_RUNTIME_MISSING" }
if (-not (Test-Path $stage5 -PathType Container)) { throw "STAGE8_12_4_PACKAGE3_STAGE5_DATA_ROOT_MISSING" }
if (-not (Test-Path $Python -PathType Leaf)) { throw "STAGE8_12_4_PACKAGE3_PYTHON_MISSING" }
$reportParent = Split-Path $report -Parent
New-Item -ItemType Directory -Force -Path $reportParent | Out-Null
if ($report.StartsWith($repo, [StringComparison]::OrdinalIgnoreCase)) { throw "STAGE8_12_4_PACKAGE3_REPORT_REPOSITORY_FORBIDDEN" }

$head = (& git -C $repo rev-parse HEAD).Trim()
if ($LASTEXITCODE -ne 0 -or $head -cne $AcceptedCommit) { throw "STAGE8_12_4_PACKAGE3_ACCEPTED_COMMIT_MISMATCH" }
if (& git -C $repo status --porcelain) { throw "STAGE8_12_4_PACKAGE3_REPOSITORY_NOT_CLEAN" }
$dataHead = (& git -C $stage5 rev-parse HEAD).Trim()
if ($LASTEXITCODE -ne 0 -or $dataHead -cne $stage5Commit) { throw "STAGE8_12_4_PACKAGE3_STAGE5_COMMIT_MISMATCH" }
if (& git -C $stage5 status --porcelain) { throw "STAGE8_12_4_PACKAGE3_STAGE5_NOT_CLEAN" }

$readonlyState = Require-ReadonlyDisabledOrAbsent
$productionTask = Require-ProductionTaskDisabledExact
$kill = Require-InactiveSafety

$timeService = Get-Service -Name W32Time -ErrorAction Stop
if ($timeService.Status -ne "Running") { throw "STAGE8_12_4_PACKAGE3_TIME_SERVICE_INVALID" }
$timeStatus = (& w32tm /query /status 2>&1 | Out-String)
if ($LASTEXITCODE -ne 0 -or [string]::IsNullOrWhiteSpace($timeStatus)) { throw "STAGE8_12_4_PACKAGE3_TIME_STATUS_INVALID" }
$timeSource = (& w32tm /query /source 2>&1 | Out-String).Trim()
if ($LASTEXITCODE -ne 0 -or [string]::IsNullOrWhiteSpace($timeSource) -or $timeSource -match '^(Local CMOS Clock|Free-running System Clock)$') {
    throw "STAGE8_12_4_PACKAGE3_TIME_SOURCE_INVALID"
}

& $Python -c "import sys; assert sys.prefix != sys.base_prefix, 'VENV_REQUIRED'"
if ($LASTEXITCODE -ne 0) { throw "STAGE8_12_4_PACKAGE3_VENV_REQUIRED" }

Write-Output "=== Stage 8.12.4 Package 3 foundation validation ==="
& (Join-Path $PSScriptRoot "run-stage8-12-4-foundation-validation.ps1") -RuntimeRoot $runtime -AcceptedCommit $AcceptedCommit -Python $Python
if ($LASTEXITCODE -ne 0) { throw "STAGE8_12_4_PACKAGE3_FOUNDATION_VALIDATION_FAILED" }

Write-Output "=== Stage 8.12.4 Package 3 rolling/service focused tests ==="
Push-Location $repo
try {
    & $Python -m pytest -q "TradingSystemLab\stage8_robot\tests\test_stage8_12_4_rolling_h1_continuity.py" "TradingSystemLab\stage8_robot\tests\test_stage8_12_4_production_service.py" "TradingSystemLab\stage8_robot\tests\test_stage8_12_4_package3_zero_order_validator.py"
    if ($LASTEXITCODE -ne 0) { throw "STAGE8_12_4_PACKAGE3_FOCUSED_PYTEST_FAILED" }
} finally {
    Pop-Location
}

$null = Require-ProductionTaskDisabledExact
$null = Require-InactiveSafety

Write-Output "=== Stage 8.12.4 Package 3 unauthorized production cycle ==="
$productionLauncher = Join-Path $PSScriptRoot "run-production.ps1"
& powershell.exe -NoProfile -ExecutionPolicy RemoteSigned -File $productionLauncher -Checkout $repo -RuntimeRoot $runtime -Stage5DataRoot $stage5 -ExpectedCommit $AcceptedCommit -Python $Python -Once
if ($LASTEXITCODE -ne 0) { throw "STAGE8_12_4_PACKAGE3_PRODUCTION_ONCE_FAILED" }

$readonlyState = Require-ReadonlyDisabledOrAbsent
$productionTask = Require-ProductionTaskDisabledExact
$kill = Require-InactiveSafety

$heartbeatPath = Join-Path $runtime "diagnostics\stage8-12-4-production-heartbeat.json"
if (-not (Test-Path $heartbeatPath -PathType Leaf)) { throw "STAGE8_12_4_PACKAGE3_HEARTBEAT_MISSING" }
try { $heartbeat = Get-Content $heartbeatPath -Raw | ConvertFrom-Json -ErrorAction Stop }
catch { throw "STAGE8_12_4_PACKAGE3_HEARTBEAT_INVALID" }
if (
    $heartbeat.schema_id -cne "stage8_12_4_production_heartbeat.v1" -or
    $heartbeat.production_specification_id -cne $productionId -or
    $heartbeat.active_identity -cne $productionIdentity -or
    $heartbeat.accepted_code_commit -cne $AcceptedCommit -or
    $heartbeat.reconciliation_status -cne "PASS" -or
    $heartbeat.health_status -cne "HEALTHY" -or
    [int]$heartbeat.unresolved_intent_count -ne 0 -or
    [int]$heartbeat.cycle_count -lt 1 -or
    [int]$heartbeat.open_position_count -ne 0 -or
    [int]$heartbeat.active_protective_stop_count -ne 0
) {
    throw "STAGE8_12_4_PACKAGE3_HEARTBEAT_CONTRACT_INVALID"
}
if ([string]$heartbeat.account_hash -notmatch '^[0-9a-f]{64}$') { throw "STAGE8_12_4_PACKAGE3_ACCOUNT_HASH_INVALID" }

$stateDb = Join-Path $runtime "state\stage8-12-production.sqlite3"
if (-not (Test-Path $stateDb -PathType Leaf)) { throw "STAGE8_12_4_PACKAGE3_STATE_DATABASE_MISSING" }
$stateProbe = & $Python -c @'
import json, sqlite3, sys
path=sys.argv[1]
db=sqlite3.connect(path)
try:
    rows=dict(db.execute("SELECT key,value FROM state"))
    keys=sorted(k for k in rows if k.startswith("production_h1_continuation:"))
    unresolved=db.execute("SELECT COUNT(*) FROM intents WHERE status IS NULL OR status NOT IN ('CANCELLED','REJECTED','CLOSED','RECONCILED')").fetchone()[0]
    positions=json.loads(rows.get("production_positions", "{}"))
    cycle=int(json.loads(rows.get("production_service_cycle_count", "0")))
    payloads=[json.loads(rows[k]) for k in keys]
    result={
        "continuation_keys": keys,
        "continuation_count": len(keys),
        "continuation_nonempty": all(
            isinstance(p,dict) and p.get("schema")=="stage8_12_4_h1_continuation.v1"
            and isinstance(p.get("bars"),list) and len(p["bars"])>0
            and isinstance(p.get("bars_sha256"),str) and len(p["bars_sha256"])==64
            for p in payloads
        ),
        "unresolved_intents": unresolved,
        "local_open_positions": len(positions) if isinstance(positions,dict) else -1,
        "cycle_count": cycle,
    }
    print(json.dumps(result,sort_keys=True,separators=(",",":")))
finally:
    db.close()
'@ $stateDb
if ($LASTEXITCODE -ne 0 -or [string]::IsNullOrWhiteSpace($stateProbe)) { throw "STAGE8_12_4_PACKAGE3_STATE_PROBE_FAILED" }
$state = $stateProbe | ConvertFrom-Json
$expectedContinuationKeys = @(
    "production_h1_continuation:CNYRUBF",
    "production_h1_continuation:GLDRUBF",
    "production_h1_continuation:IMOEXF",
    "production_h1_continuation:USDRUBF"
)
if (
    [int]$state.continuation_count -ne 4 -or
    -not [bool]$state.continuation_nonempty -or
    [int]$state.unresolved_intents -ne 0 -or
    [int]$state.local_open_positions -ne 0 -or
    [int]$state.cycle_count -lt 1 -or
    (@($state.continuation_keys) -join "|") -cne ($expectedContinuationKeys -join "|")
) {
    throw "STAGE8_12_4_PACKAGE3_STATE_CONTRACT_INVALID"
}

$evidence = [ordered]@{
    schema_id = "stage8_12_4_package3_zero_order_validation.v1"
    status = "PASS"
    package3_result = "STAGE_8_12_4_PACKAGE3_INTEL_EXACT_COMMIT_ZERO_ORDER_VALIDATION_PASS"
    accepted_code_commit = $AcceptedCommit
    production_specification_id = $productionId
    active_identity = $productionIdentity
    stage5_data_commit = $stage5Commit
    foundation_validation = "PASS"
    focused_rolling_service_tests = "PASS"
    unauthorized_production_cycle = "PASS"
    production_heartbeat = "HEALTHY"
    reconciliation_status = "PASS"
    production_cycle_count = [int]$heartbeat.cycle_count
    rolling_h1_continuation_count = [int]$state.continuation_count
    rolling_h1_continuation_nonempty = [bool]$state.continuation_nonempty
    unresolved_production_intents = [int]$state.unresolved_intents
    local_open_position_count = [int]$state.local_open_positions
    broker_open_position_count = [int]$heartbeat.open_position_count
    active_protective_stop_count = [int]$heartbeat.active_protective_stop_count
    account_identity_sha256 = [string]$heartbeat.account_hash
    production_task_name = $productionTaskName
    production_task_state = "Disabled"
    production_task_exact_commit_binding = $true
    production_task_exact_principal_binding = $true
    readonly_task_state = $readonlyState
    durable_authorization_present = $false
    kill_switch = "HALTED"
    execution_authorized = $false
    live_trading_authorized = $false
    real_order_transmission_authorized = $false
    order_endpoint_call_count = 0
    real_order_count = 0
}
$evidence | ConvertTo-Json -Depth 6 | Set-Content -Path $report -Encoding UTF8
$hash = (Get-FileHash $report -Algorithm SHA256).Hash

Write-Output "STAGE8_12_4_PACKAGE3_PASS=true"
Write-Output "STAGE8_12_4_PACKAGE3_ACCEPTED_COMMIT=$AcceptedCommit"
Write-Output "STAGE8_12_4_PACKAGE3_EVIDENCE_SHA256=$hash"
Write-Output "STAGE8_12_4_PACKAGE3_EXECUTION_AUTHORIZED=false"
Write-Output "STAGE8_12_4_PACKAGE3_KILL_SWITCH=HALTED"
Write-Output "STAGE8_12_4_PACKAGE3_PRODUCTION_TASK=Disabled"
Write-Output "STAGE8_12_4_PACKAGE3_REAL_ORDER_COUNT=0"
