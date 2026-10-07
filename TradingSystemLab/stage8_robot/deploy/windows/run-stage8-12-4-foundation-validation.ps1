param(
    [Parameter(Mandatory=$true)][string]$RuntimeRoot,
    [Parameter(Mandatory=$true)][string]$AcceptedCommit,
    [string]$Python = ""
)

$ErrorActionPreference = "Stop"
$repo = (Resolve-Path (Join-Path $PSScriptRoot "..\..\..\..")).Path
if ([string]::IsNullOrWhiteSpace($Python)) {
    $Python = Join-Path $RuntimeRoot "venv\Scripts\python.exe"
}
$productionTaskName = "TradingSystemLab-Stage8-Production"
$readonlyTaskName = "TradingSystemLab-Stage8-Readonly"
$productionId = "PROD_STAGE7_46DB784378797C7FB04636892350AFF21006D71A31F2CED9D4B974EDA2DC36B8"

function Require-DisabledOrAbsentTask([string]$Name) {
    $task = Get-ScheduledTask -TaskName $Name -ErrorAction SilentlyContinue
    if ($null -ne $task -and $task.State -ne "Disabled") {
        throw "STAGE8_12_4_TASK_NOT_DISABLED:${Name}:$($task.State)"
    }
}

function Require-FoundationInactive {
    Require-DisabledOrAbsentTask $readonlyTaskName
    Require-DisabledOrAbsentTask $productionTaskName
    $authPath = Join-Path $RuntimeRoot "safety\stage8-12-4-production-authorization.json"
    if (Test-Path $authPath) { throw "STAGE8_12_4_AUTHORIZATION_MUST_BE_ABSENT" }
    $killPath = Join-Path $RuntimeRoot "safety\stage8-trading-kill-switch.json"
    if (-not (Test-Path $killPath -PathType Leaf)) { throw "STAGE8_12_4_KILL_SWITCH_MISSING" }
    try { $kill = Get-Content $killPath -Raw | ConvertFrom-Json -ErrorAction Stop }
    catch { throw "STAGE8_12_4_KILL_SWITCH_INVALID" }
    if ($kill.schema_id -cne "stage8_trading_kill_switch.v1") { throw "STAGE8_12_4_KILL_SWITCH_INVALID" }
    if ($kill.production_specification_id -cne $productionId) { throw "STAGE8_12_4_KILL_SWITCH_PRODUCTION_ID_MISMATCH" }
    if ($kill.state -cne "HALTED") { throw "STAGE8_12_4_KILL_SWITCH_NOT_HALTED" }
    Write-Output "STAGE8_12_4_FOUNDATION_INACTIVE=true"
}

if (-not (Test-Path $Python -PathType Leaf)) { throw "STAGE8_12_4_PYTHON_VENV_MISSING" }

Set-Location $repo
$head = (git rev-parse HEAD).Trim()
if ($LASTEXITCODE -ne 0) { throw "STAGE8_12_4_GIT_HEAD_FAILED" }
if ($head -cne $AcceptedCommit) { throw "STAGE8_12_4_WRONG_COMMIT:$head" }
$status = git status --porcelain
if ($LASTEXITCODE -ne 0) { throw "STAGE8_12_4_GIT_STATUS_FAILED" }
if ($status) { throw "STAGE8_12_4_REPOSITORY_NOT_CLEAN" }

Require-FoundationInactive

Write-Output "=== Stage 8.12.4 foundation zero-order tests ==="
$tests = @(
    "TradingSystemLab\stage8_robot\tests\test_stage8_12_4_authorization_foundation.py",
    "TradingSystemLab\stage8_robot\tests\test_stage8_12_production_runtime.py",
    "TradingSystemLab\stage8_robot\tests\test_stage8_12_production_conformance.py",
    "TradingSystemLab\stage8_robot\tests\test_stage8_12_3_intel_preflight.py",
    "TradingSystemLab\stage8_robot\tests\test_funding_margin_diagnostic.py",
    "TradingSystemLab\stage8_robot\tests\test_real_readonly_margin.py"
)
& $Python -m pytest @tests -q
if ($LASTEXITCODE -ne 0) { throw "STAGE8_12_4_FOUNDATION_PYTEST_FAILED" }

Write-Output "=== Independent Stage 8 audit ==="
& $Python "TradingSystemLab\stage8_robot\audit_stage8.py" --check-only
if ($LASTEXITCODE -ne 0) { throw "STAGE8_12_4_STAGE8_AUDIT_FAILED" }

Write-Output "=== Final operational audit ==="
& $Python "TradingSystemLab\stage8_robot\final_operational_audit.py" --check-only
if ($LASTEXITCODE -ne 0) { throw "STAGE8_12_4_FINAL_OPERATIONAL_AUDIT_FAILED" }

Require-FoundationInactive

Write-Output "STAGE8_12_4_FOUNDATION_VALIDATION_PASS=true"
Write-Output "STAGE8_12_4_ACCEPTED_COMMIT=$AcceptedCommit"
Write-Output "STAGE8_12_4_DURABLE_AUTHORIZATION_CREATED=false"
Write-Output "STAGE8_12_4_EXECUTION_AUTHORIZED=false"
Write-Output "STAGE8_12_4_KILL_SWITCH=HALTED"
Write-Output "STAGE8_12_4_PRODUCTION_TASK=DisabledOrAbsent"
Write-Output "STAGE8_12_4_REAL_ORDER_COUNT=0"
