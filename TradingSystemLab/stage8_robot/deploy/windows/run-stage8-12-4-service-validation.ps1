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
$readonlyTask = "TradingSystemLab-Stage8-Readonly"
$productionTask = "TradingSystemLab-Stage8-Production"
$productionId = "PROD_STAGE7_46DB784378797C7FB04636892350AFF21006D71A31F2CED9D4B974EDA2DC36B8"

function Require-DisabledOrAbsent([string]$Name) {
    $task = Get-ScheduledTask -TaskName $Name -ErrorAction SilentlyContinue
    if ($null -ne $task -and $task.State -ne "Disabled") {
        throw "STAGE8_12_4_VALIDATION_TASK_NOT_DISABLED:$($Name):$($task.State)"
    }
}

function Require-Inactive {
    Require-DisabledOrAbsent $readonlyTask
    Require-DisabledOrAbsent $productionTask
    $authPath = Join-Path $RuntimeRoot "safety\stage8-12-4-production-authorization.json"
    if (Test-Path $authPath) { throw "STAGE8_12_4_VALIDATION_AUTHORIZATION_MUST_BE_ABSENT" }
    $killPath = Join-Path $RuntimeRoot "safety\stage8-trading-kill-switch.json"
    if (-not (Test-Path $killPath -PathType Leaf)) { throw "STAGE8_12_4_VALIDATION_KILL_SWITCH_MISSING" }
    try { $kill = Get-Content $killPath -Raw | ConvertFrom-Json -ErrorAction Stop }
    catch { throw "STAGE8_12_4_VALIDATION_KILL_SWITCH_INVALID" }
    if ($kill.schema_id -cne "stage8_trading_kill_switch.v1" -or
        $kill.production_specification_id -cne $productionId -or
        $kill.state -cne "HALTED") {
        throw "STAGE8_12_4_VALIDATION_KILL_SWITCH_NOT_HALTED"
    }
}

if (-not (Test-Path $Python -PathType Leaf)) { throw "STAGE8_12_4_VALIDATION_PYTHON_MISSING" }
Set-Location $repo
$head = (git rev-parse HEAD).Trim()
if ($LASTEXITCODE -ne 0 -or $head -cne $AcceptedCommit) { throw "STAGE8_12_4_VALIDATION_WRONG_COMMIT:$head" }
$status = git status --porcelain
if ($LASTEXITCODE -ne 0 -or $status) { throw "STAGE8_12_4_VALIDATION_REPOSITORY_NOT_CLEAN" }

Require-Inactive

Write-Host "=== Stage 8.12.4 production service zero-order regression ==="
$tests = @(
    "TradingSystemLab\stage8_robot\tests\test_stage8_12_4_authorization_foundation.py",
    "TradingSystemLab\stage8_robot\tests\test_stage8_12_4_production_history.py",
    "TradingSystemLab\stage8_robot\tests\test_stage8_12_4_production_broker_state.py",
    "TradingSystemLab\stage8_robot\tests\test_stage8_12_4_production_service.py",
    "TradingSystemLab\stage8_robot\tests\test_stage8_12_production_runtime.py",
    "TradingSystemLab\stage8_robot\tests\test_stage8_12_production_conformance.py",
    "TradingSystemLab\stage8_robot\tests\test_stage8_12_3_intel_preflight.py",
    "TradingSystemLab\stage8_robot\tests\test_funding_margin_diagnostic.py",
    "TradingSystemLab\stage8_robot\tests\test_real_readonly_margin.py"
)
& $Python -m pytest @tests -q
if ($LASTEXITCODE -ne 0) { throw "STAGE8_12_4_SERVICE_VALIDATION_PYTEST_FAILED" }

Write-Host "=== Independent Stage 8 audit ==="
& $Python "TradingSystemLab\stage8_robot\audit_stage8.py" --check-only
if ($LASTEXITCODE -ne 0) { throw "STAGE8_12_4_SERVICE_VALIDATION_STAGE8_AUDIT_FAILED" }

Write-Host "=== Final operational audit ==="
& $Python "TradingSystemLab\stage8_robot\final_operational_audit.py" --check-only
if ($LASTEXITCODE -ne 0) { throw "STAGE8_12_4_SERVICE_VALIDATION_FINAL_AUDIT_FAILED" }

$runner = Get-Content "TradingSystemLab\stage8_robot\deploy\windows\run-production.ps1" -Raw
$installer = Get-Content "TradingSystemLab\stage8_robot\deploy\windows\install-production-task.ps1" -Raw
if ($runner -notmatch "Get-TradingCredential" -or $runner -notmatch "--accepted-commit") {
    throw "STAGE8_12_4_PRODUCTION_RUNNER_CONTRACT_INVALID"
}
if ($installer -notmatch "Disable-ScheduledTask" -or
    $installer -match "Enable-ScheduledTask" -or
    $installer -match "Start-ScheduledTask") {
    throw "STAGE8_12_4_PRODUCTION_TASK_INSTALLER_NOT_INACTIVE"
}

Require-Inactive

Write-Host "STAGE8_12_4_SERVICE_VALIDATION_PASS=true"
Write-Host "STAGE8_12_4_ACCEPTED_COMMIT=$AcceptedCommit"
Write-Host "STAGE8_12_4_DURABLE_AUTHORIZATION_CREATED=false"
Write-Host "STAGE8_12_4_EXECUTION_AUTHORIZED=false"
Write-Host "STAGE8_12_4_KILL_SWITCH=HALTED"
Write-Host "STAGE8_12_4_PRODUCTION_TASK=DisabledOrAbsent"
Write-Host "STAGE8_12_4_REAL_ORDER_COUNT=0"
