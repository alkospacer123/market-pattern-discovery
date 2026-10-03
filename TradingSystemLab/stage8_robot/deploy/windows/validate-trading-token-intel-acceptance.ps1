param(
    [Parameter(Mandatory=$true)][string]$RuntimeRoot,
    [string]$Python = "py.exe",
    [string]$ReportPath = ""
)
$ErrorActionPreference = "Stop"
$taskName = "TradingSystemLab-Stage8-Readonly"
$productionId = "PROD_STAGE7_46DB784378797C7FB04636892350AFF21006D71A31F2CED9D4B974EDA2DC36B8"
$stageEnvironment = @(
    "FINAM_8107_TRADING_API_SECRET", "FINAM_8107_ACCOUNT_ID",
    "STAGE8_10_7_LOCAL_ACCOUNT_BINDING_CONFIRMED", "STAGE8_10_7_INTEL_TRADING_TOKEN_ACCEPTANCE"
)
$forbiddenEnvironment = @(
    "FINAM_API_SECRET", "FINAM_REAL_ACCOUNT_ID", "FINAM_TRADING_API_SECRET", "FINAM_TRADING_ACCOUNT_ID",
    "FINAM_PERMISSION_READONLY_API_SECRET", "FINAM_PERMISSION_TRADING_API_SECRET", "FINAM_PERMISSION_ACCOUNT_ID",
    "FINAM_8107_TRADING_API_SECRET", "FINAM_8107_ACCOUNT_ID", "STAGE8_10_3_IDENTITY_BINDING",
    "STAGE8_10_4_PERMISSION_BOUNDARY", "STAGE8_10_5_ORDER_PATH_DRY",
    "STAGE8_10_7_INTEL_TRADING_TOKEN_ACCEPTANCE", "STAGE8_10_7_LOCAL_ACCOUNT_BINDING_CONFIRMED"
)
$repo = (Resolve-Path (Join-Path $PSScriptRoot "..\..\..\..")).Path
$runtime = [IO.Path]::GetFullPath($RuntimeRoot)
if (-not $ReportPath) { $ReportPath = Join-Path $runtime "diagnostics\stage8_10_7_intel_trading_token_acceptance.json" }
$readonlyCredential = $null
$tradingCredential = $null

function Assert-HostSafe {
    $task = Get-ScheduledTask -TaskName $taskName -ErrorAction SilentlyContinue
    if ($task -and $task.State -ne "Disabled") { throw "STAGE8_10_7_SCHEDULED_TASK_NOT_DISABLED" }
    $robots = @(Get-CimInstance Win32_Process | Where-Object {
        $_.CommandLine -and $_.CommandLine -match "TradingSystemLab\.stage8_robot"
    })
    if ($robots.Count -ne 0) { throw "STAGE8_10_7_ROBOT_PROCESS_RUNNING" }
}

function Assert-KillSwitchHalted {
    & $Python -c "from TradingSystemLab.stage8_robot.specification import PRODUCTION_SPECIFICATION_ID as p; from TradingSystemLab.stage8_robot.trading_safety_gate import load_kill_switch; s,e=load_kill_switch(r'''$runtime'''); assert not e and s['production_specification_id']==p and s['state']=='HALTED'"
    if ($LASTEXITCODE -ne 0) { throw "STAGE8_10_7_KILL_SWITCH_HALTED_REQUIRED" }
}

# Host/task/process/environment checks and HALTED observation precede DPAPI loading.
foreach ($name in $forbiddenEnvironment) {
    if ([Environment]::GetEnvironmentVariable($name)) { throw "STAGE8_10_7_CREDENTIAL_ENVIRONMENT_NOT_EMPTY" }
}
Assert-HostSafe
Push-Location $repo
try {
    Assert-KillSwitchHalted
    . (Join-Path $PSScriptRoot "credential-store.ps1")
    . (Join-Path $PSScriptRoot "trading-credential-store.ps1")
    try { $readonlyCredential = Get-ReadonlyCredential $runtime $productionId }
    catch { throw "STAGE8_10_7_READONLY_CREDENTIAL_UNAVAILABLE" }
    try { $tradingCredential = Get-TradingCredential $runtime $productionId }
    catch { throw "STAGE8_10_7_TRADING_CREDENTIAL_UNAVAILABLE" }
    if ($readonlyCredential.production_id -cne $productionId -or $tradingCredential.production_id -cne $productionId) {
        throw "STAGE8_10_7_PRODUCTION_ID_MISMATCH"
    }
    if ([string]$readonlyCredential.finam_real_account_id -cne [string]$tradingCredential.finam_real_account_id) {
        throw "STAGE8_10_7_LOCAL_ACCOUNT_MISMATCH"
    }
    if ([string]::IsNullOrWhiteSpace([string]$readonlyCredential.finam_api_secret) -or
        [string]::IsNullOrWhiteSpace([string]$tradingCredential.finam_trading_api_secret)) {
        throw "STAGE8_10_7_CREDENTIAL_SECRET_MISSING"
    }
    Write-Output "STAGE_8_10_7_LOCAL_ACCOUNT_BINDING_PASS"
    $env:FINAM_8107_TRADING_API_SECRET = [string]$tradingCredential.finam_trading_api_secret
    $env:FINAM_8107_ACCOUNT_ID = [string]$tradingCredential.finam_real_account_id
    $env:STAGE8_10_7_LOCAL_ACCOUNT_BINDING_CONFIRMED = "true"
    $env:STAGE8_10_7_INTEL_TRADING_TOKEN_ACCEPTANCE = "true"
    & $Python -m TradingSystemLab.stage8_robot.trading_token_intel_acceptance --runtime-root $runtime --report $ReportPath
    if ($LASTEXITCODE -ne 0) { throw "STAGE8_10_7_CHILD_DIAGNOSTIC_FAILED" }
    Assert-KillSwitchHalted
    Assert-HostSafe
} catch {
    $code = $_.Exception.Message
    if ($code -notmatch '^STAGE8_10_7_') { $code = "STAGE8_10_7_VALIDATION_FAILED" }
    Write-Error $code
    exit 1
} finally {
    foreach ($name in $stageEnvironment) { Remove-Item "Env:$name" -ErrorAction SilentlyContinue }
    $readonlyCredential = $null
    $tradingCredential = $null
    Pop-Location
}
foreach ($name in $stageEnvironment) {
    if ([Environment]::GetEnvironmentVariable($name)) { throw "STAGE8_10_7_ENVIRONMENT_CLEANUP_FAILED" }
}
