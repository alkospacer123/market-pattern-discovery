param(
  [Parameter(Mandatory=$true)][string]$RuntimeRoot,
  [Parameter(Mandatory=$true)][string]$DataRoot,
  [Parameter(Mandatory=$true)][string]$AcceptedCommit,
  [string]$Python = "",
  [string]$ReportPath = ""
)

$ErrorActionPreference = "Stop"
$repo = (Resolve-Path (Join-Path $PSScriptRoot "..\..\..\..")).Path
$expectedDataCommit = "50f1fd2178c18b7ab3bd969be82ad01f47a34745"
$productionId = "PROD_STAGE7_46DB784378797C7FB04636892350AFF21006D71A31F2CED9D4B974EDA2DC36B8"
$productionTaskName = "TradingSystemLab-Stage8-Production"
$readonlyTaskName = "TradingSystemLab-Stage8-Readonly"

if ([string]::IsNullOrWhiteSpace($Python)) {
  $Python = Join-Path $RuntimeRoot "venv\Scripts\python.exe"
}
if ([string]::IsNullOrWhiteSpace($ReportPath)) {
  $ReportPath = Join-Path $RuntimeRoot "diagnostics\stage8_12_4_service_preflight.json"
}
if (-not (Test-Path $Python -PathType Leaf)) { throw "STAGE8_12_4_PYTHON_VENV_MISSING" }

function Require-ExactCleanCheckout([string]$Path,[string]$Expected,[string]$Code) {
  if (-not (Test-Path $Path -PathType Container)) { throw ($Code + "_MISSING") }
  $head = (& git -C $Path rev-parse HEAD).Trim()
  if ($LASTEXITCODE -ne 0 -or $head -cne $Expected) { throw ($Code + "_WRONG_COMMIT:" + $head) }
  $status = & git -C $Path status --porcelain
  if ($LASTEXITCODE -ne 0) { throw ($Code + "_GIT_STATUS_FAILED") }
  if ($status) { throw ($Code + "_NOT_CLEAN") }
}

function Require-DisabledOrAbsentTask([string]$Name) {
  $task = Get-ScheduledTask -TaskName $Name -ErrorAction SilentlyContinue
  if ($null -ne $task -and $task.State -ne "Disabled") {
    throw "STAGE8_12_4_TASK_NOT_DISABLED:${Name}:$($task.State)"
  }
}

function Require-Inactive {
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
}

Require-ExactCleanCheckout $repo $AcceptedCommit "STAGE8_12_4_CODE"
Require-ExactCleanCheckout $DataRoot $expectedDataCommit "STAGE8_12_4_DATA"
Require-Inactive
Set-Location $repo

Write-Output "=== Stage 8.12.4 production-service zero-order regression ==="
$tests = @(
  "TradingSystemLab\stage8_robot\tests\test_stage8_12_4_authorization_foundation.py",
  "TradingSystemLab\stage8_robot\tests\test_stage8_12_4_production_broker_state.py",
  "TradingSystemLab\stage8_robot\tests\test_stage8_12_4_production_history.py",
  "TradingSystemLab\stage8_robot\tests\test_stage8_12_4_production_service.py",
  "TradingSystemLab\stage8_robot\tests\test_stage8_12_4_service_preflight.py",
  "TradingSystemLab\stage8_robot\tests\test_stage8_12_production_runtime.py",
  "TradingSystemLab\stage8_robot\tests\test_stage8_12_production_conformance.py",
  "TradingSystemLab\stage8_robot\tests\test_stage8_12_3_intel_preflight.py",
  "TradingSystemLab\stage8_robot\tests\test_funding_margin_diagnostic.py",
  "TradingSystemLab\stage8_robot\tests\test_real_readonly_margin.py"
)
& $Python -m pytest @tests -q
if ($LASTEXITCODE -ne 0) { throw "STAGE8_12_4_SERVICE_REGRESSION_FAILED" }

Write-Output "=== Independent Stage 8 audit ==="
& $Python "TradingSystemLab\stage8_robot\audit_stage8.py" --check-only
if ($LASTEXITCODE -ne 0) { throw "STAGE8_12_4_STAGE8_AUDIT_FAILED" }

Write-Output "=== Final operational audit ==="
& $Python "TradingSystemLab\stage8_robot\final_operational_audit.py" --check-only
if ($LASTEXITCODE -ne 0) { throw "STAGE8_12_4_FINAL_OPERATIONAL_AUDIT_FAILED" }

Require-Inactive
if (Test-Path $ReportPath) { Remove-Item $ReportPath -Force }

. (Join-Path $PSScriptRoot "trading-credential-store.ps1")
$credential = Get-TradingCredential $RuntimeRoot $productionId
$env:FINAM_API_SECRET = [string]$credential.finam_trading_api_secret
$env:FINAM_REAL_ACCOUNT_ID = [string]$credential.finam_real_account_id
$credential = $null
try {
  Write-Output "=== Physical FINAM H1 seed-overlap preflight ==="
  & $Python -m TradingSystemLab.stage8_robot.stage8_12_4_service_preflight `
    --runtime-root $RuntimeRoot `
    --data-root $DataRoot `
    --accepted-commit $AcceptedCommit `
    --output $ReportPath
  if ($LASTEXITCODE -ne 0) { throw "STAGE8_12_4_SERVICE_PREFLIGHT_FAILED" }
}
finally {
  Remove-Item Env:FINAM_API_SECRET -ErrorAction SilentlyContinue
  Remove-Item Env:FINAM_REAL_ACCOUNT_ID -ErrorAction SilentlyContinue
}

if (-not (Test-Path $ReportPath -PathType Leaf)) { throw "STAGE8_12_4_SERVICE_REPORT_MISSING" }
try { $report = Get-Content $ReportPath -Raw | ConvertFrom-Json -ErrorAction Stop }
catch { throw "STAGE8_12_4_SERVICE_REPORT_INVALID" }
if ($report.schema_id -cne "stage8_12_4_service_preflight.v1") { throw "STAGE8_12_4_SERVICE_REPORT_INVALID" }
if ($report.status -cne "PASS") { throw "STAGE8_12_4_SERVICE_REPORT_NOT_PASS" }
if ($report.accepted_code_commit -cne $AcceptedCommit) { throw "STAGE8_12_4_SERVICE_REPORT_COMMIT_MISMATCH" }
if ($report.stage5_data_commit -cne $expectedDataCommit) { throw "STAGE8_12_4_SERVICE_REPORT_DATA_MISMATCH" }
if ($report.durable_authorization_created -ne $false -or $report.execution_authorized -ne $false) { throw "STAGE8_12_4_SERVICE_REPORT_AUTHORIZATION_INVALID" }
if ($report.kill_switch -cne "HALTED") { throw "STAGE8_12_4_SERVICE_REPORT_KILL_SWITCH_INVALID" }
if ([int]$report.order_endpoint_call_count -ne 0 -or [int]$report.real_order_count -ne 0) { throw "STAGE8_12_4_SERVICE_REPORT_ORDER_COUNT_INVALID" }
if ($report.order_capable_methods_exposed -ne $false) { throw "STAGE8_12_4_SERVICE_REPORT_CAPABILITY_INVALID" }
if (@($report.n4).Count -ne 4 -or @($report.per_instrument.PSObject.Properties).Count -ne 4) { throw "STAGE8_12_4_SERVICE_REPORT_N4_INVALID" }

Require-Inactive
$hash = (Get-FileHash $ReportPath -Algorithm SHA256).Hash
Write-Output "STAGE8_12_4_SERVICE_VALIDATION_PASS=true"
Write-Output "STAGE8_12_4_ACCEPTED_COMMIT=$AcceptedCommit"
Write-Output "STAGE8_12_4_STAGE5_DATA_COMMIT=$expectedDataCommit"
Write-Output "STAGE8_12_4_EVIDENCE_SHA256=$hash"
Write-Output "STAGE8_12_4_DURABLE_AUTHORIZATION_CREATED=false"
Write-Output "STAGE8_12_4_EXECUTION_AUTHORIZED=false"
Write-Output "STAGE8_12_4_KILL_SWITCH=HALTED"
Write-Output "STAGE8_12_4_PRODUCTION_TASK=DisabledOrAbsent"
Write-Output "STAGE8_12_4_REAL_ORDER_COUNT=0"
