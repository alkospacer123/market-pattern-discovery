param(
    [Parameter(Mandatory=$true)][string]$RuntimeRoot,
    [Parameter(Mandatory=$true)][ValidatePattern('^[0-9a-f]{40}$')][string]$AcceptedCommit,
    [string]$Python = "",
    [string]$ReportPath = ""
)

$ErrorActionPreference = "Stop"
$productionId = "PROD_STAGE7_46DB784378797C7FB04636892350AFF21006D71A31F2CED9D4B974EDA2DC36B8"
$productionIdentity = "TRAIL1__N4_01__FULL__R15"
$readonlyTaskName = "TradingSystemLab-Stage8-Readonly"
$productionTaskName = "TradingSystemLab-Stage8-Production"
$repo = (Resolve-Path (Join-Path $PSScriptRoot "..\..\..\..")).Path
$runtime = [IO.Path]::GetFullPath($RuntimeRoot)
if (-not $Python) { $Python = Join-Path $runtime "venv\Scripts\python.exe" }
if (-not $ReportPath) { $ReportPath = Join-Path $runtime "diagnostics\stage8_12_3_intel_preflight.json" }

function Require-DisabledOrAbsentTask([string]$Name) {
    $task = Get-ScheduledTask -TaskName $Name -ErrorAction SilentlyContinue
    if ($task -and $task.State -ne "Disabled") {
        throw "STAGE8_12_3_SCHEDULED_TASK_NOT_DISABLED:$Name"
    }
}

try {
    if (-not (Test-Path $runtime -PathType Container)) {
        throw "STAGE8_12_3_RUNTIME_MISSING"
    }
    if (-not (Test-Path $Python -PathType Leaf)) {
        throw "STAGE8_12_3_PYTHON_MISSING"
    }
    $head = (git -C $repo rev-parse HEAD).Trim()
    if ($head -cne $AcceptedCommit -or (git -C $repo status --porcelain)) {
        throw "STAGE8_12_3_ACCEPTED_CLEAN_COMMIT_REQUIRED"
    }

    Require-DisabledOrAbsentTask $readonlyTaskName
    Require-DisabledOrAbsentTask $productionTaskName

    $timeService = Get-Service -Name W32Time -ErrorAction Stop
    if ($timeService.Status -ne "Running") {
        throw "STAGE8_12_3_TIME_SERVICE_INVALID"
    }
    $timeStatus = (& w32tm /query /status 2>&1 | Out-String)
    if ($LASTEXITCODE -ne 0 -or [string]::IsNullOrWhiteSpace($timeStatus)) {
        throw "STAGE8_12_3_TIME_STATUS_INVALID"
    }
    $timeSource = (& w32tm /query /source 2>&1 | Out-String).Trim()
    if ($LASTEXITCODE -ne 0 -or [string]::IsNullOrWhiteSpace($timeSource)) {
        throw "STAGE8_12_3_TIME_SOURCE_INVALID"
    }
    if ($timeSource -match '^(Local CMOS Clock|Free-running System Clock)$') {
        throw "STAGE8_12_3_TIME_SOURCE_UNSYNCHRONIZED"
    }

    $probe = Join-Path $runtime ".stage8-12-3-write-probe"
    Set-Content $probe "probe"
    Remove-Item $probe
    $driveName = ([IO.Path]::GetPathRoot($runtime).Substring(0,1))
    if ((Get-PSDrive -Name $driveName).Free -lt 100MB) {
        throw "STAGE8_12_3_DISK_CAPACITY_LOW"
    }

    & $Python -c "import sys; assert sys.prefix != sys.base_prefix, 'VENV_REQUIRED'"
    if ($LASTEXITCODE -ne 0) { throw "STAGE8_12_3_VENV_REQUIRED" }

    Push-Location $repo
    try {
        & $Python -m TradingSystemLab.stage8_robot.audit_stage8 --check-only
        if ($LASTEXITCODE -ne 0) { throw "STAGE8_12_3_STAGE8_AUDIT_FAILED" }
        & $Python -m TradingSystemLab.stage8_robot.final_operational_audit --check-only
        if ($LASTEXITCODE -ne 0) { throw "STAGE8_12_3_FINAL_OPERATIONAL_AUDIT_FAILED" }
    } finally {
        Pop-Location
    }

    . (Join-Path $PSScriptRoot "credential-store.ps1")
    . (Join-Path $PSScriptRoot "trading-credential-store.ps1")
    $readonly = Get-ReadonlyCredential $runtime $productionId
    $trading = Get-TradingCredential $runtime $productionId
    if ([string]$readonly.finam_real_account_id -cne [string]$trading.finam_real_account_id) {
        throw "STAGE8_12_3_ACCOUNT_MISMATCH"
    }

    # Refresh health/reconciliation/H1 authority with the order-incapable
    # REAL_READONLY supervisor before using the trading credential for GET-only reads.
    $env:FINAM_MODE = "REAL_READONLY"
    $env:NEW_ENTRIES_DISABLED = "true"
    $env:PRODUCTION_SPECIFICATION_ID = $productionId
    $env:PRODUCTION_IDENTITY = $productionIdentity
    $env:FINAM_API_SECRET = [string]$readonly.finam_api_secret
    $env:FINAM_REAL_ACCOUNT_ID = [string]$readonly.finam_real_account_id
    Push-Location $repo
    try {
        & $Python -m TradingSystemLab.stage8_robot.readonly_supervisor --runtime-root $runtime --once
        if ($LASTEXITCODE -ne 0) { throw "STAGE8_12_3_READONLY_REFRESH_FAILED" }
    } finally {
        Pop-Location
        foreach ($name in @(
            "FINAM_MODE","NEW_ENTRIES_DISABLED","PRODUCTION_SPECIFICATION_ID",
            "PRODUCTION_IDENTITY","FINAM_API_SECRET","FINAM_REAL_ACCOUNT_ID"
        )) {
            Remove-Item "Env:$name" -ErrorAction SilentlyContinue
        }
    }

    $env:STAGE8_12_3_TRADING_SECRET = [string]$trading.finam_trading_api_secret
    $env:STAGE8_12_3_ACCOUNT_ID = [string]$trading.finam_real_account_id
    $env:STAGE8_12_3_DPAPI_VALIDATED = "true"
    $env:STAGE8_12_3_PRODUCTION_TASK_SAFE = "true"

    Push-Location $repo
    try {
        & $Python -m TradingSystemLab.stage8_robot.stage8_12_intel_preflight --runtime-root $runtime --report $ReportPath --accepted-commit $AcceptedCommit
        if ($LASTEXITCODE -ne 0) { throw "STAGE8_12_3_PREFLIGHT_CHILD_FAILED" }
    } finally {
        Pop-Location
    }

    if (-not (Test-Path $ReportPath -PathType Leaf)) {
        throw "STAGE8_12_3_REPORT_MISSING"
    }
    $report = Get-Content $ReportPath -Raw | ConvertFrom-Json
    $contractValid = (
        $report.status -ceq "PASS" -and
        $report.stage8_12_3_result -ceq "STAGE_8_12_3_INTEL_PRODUCTION_PREFLIGHT_PASS" -and
        -not [bool]$report.execution_authorized -and
        -not [bool]$report.live_trading_authorized -and
        -not [bool]$report.real_order_transmission_authorized -and
        [int]$report.order_endpoint_call_count -eq 0 -and
        [int]$report.real_order_count -eq 0 -and
        $report.kill_switch_observed -ceq "HALTED"
    )
    if (-not $contractValid) {
        throw "STAGE8_12_3_REPORT_CONTRACT_INVALID"
    }

    $hash = (Get-FileHash $ReportPath -Algorithm SHA256).Hash
    Write-Output "STAGE8_12_3_INTEL_PREFLIGHT_PASS=true"
    Write-Output "STAGE8_12_3_ACCEPTED_COMMIT=$AcceptedCommit"
    Write-Output "STAGE8_12_3_EVIDENCE_SHA256=$hash"
    Write-Output "STAGE8_12_3_REAL_ORDER_COUNT=0"
    Write-Output "STAGE8_12_3_EXECUTION_AUTHORIZED=false"
    Write-Output "STAGE8_12_3_KILL_SWITCH=HALTED"
    Write-Output ("STAGE8_12_3_BASE_REQUIRED_CAPITAL=" + $report.n4_simultaneous_positive_capacity.base_required_capital)
    Write-Output ("STAGE8_12_3_CURRENT_AVAILABLE_CASH=" + $report.n4_simultaneous_positive_capacity.current_available_cash)
    Write-Output ("STAGE8_12_3_ADDITIONAL_FUNDING_REQUIRED=" + $report.n4_simultaneous_positive_capacity.additional_funding_required)
} finally {
    foreach ($name in @(
        "STAGE8_12_3_TRADING_SECRET","STAGE8_12_3_ACCOUNT_ID",
        "STAGE8_12_3_DPAPI_VALIDATED","STAGE8_12_3_PRODUCTION_TASK_SAFE",
        "FINAM_MODE","NEW_ENTRIES_DISABLED","PRODUCTION_SPECIFICATION_ID",
        "PRODUCTION_IDENTITY","FINAM_API_SECRET","FINAM_REAL_ACCOUNT_ID"
    )) {
        Remove-Item "Env:$name" -ErrorAction SilentlyContinue
    }
    $readonly = $null
    $trading = $null
}
