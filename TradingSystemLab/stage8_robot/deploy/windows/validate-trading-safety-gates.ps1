param(
    [Parameter(Mandatory=$true)][string]$RuntimeRoot,
    [string]$Python = "python",
    [string]$ReportPath = ""
)
$ErrorActionPreference = "Stop"
$taskName = "TradingSystemLab-Stage8-Readonly"
$forbidden = @(
    "FINAM_API_SECRET", "FINAM_REAL_ACCOUNT_ID", "FINAM_TRADING_API_SECRET",
    "FINAM_TRADING_ACCOUNT_ID", "FINAM_PERMISSION_READONLY_API_SECRET",
    "FINAM_PERMISSION_TRADING_API_SECRET", "FINAM_PERMISSION_ACCOUNT_ID",
    "STAGE8_10_4_PERMISSION_BOUNDARY", "STAGE8_10_5_ORDER_PATH_DRY"
)

# This wrapper deliberately offers no Arm action and never sets execution authorization.
$repo = (Resolve-Path (Join-Path $PSScriptRoot "..\..\..\..")).Path
$runtime = [IO.Path]::GetFullPath($RuntimeRoot)
if (-not $ReportPath) { $ReportPath = Join-Path $runtime "diagnostics\stage8_10_6_safety_gate_validation.json" }
foreach ($name in $forbidden) {
    if ([Environment]::GetEnvironmentVariable($name)) { throw "STAGE8_10_6_CREDENTIAL_ENVIRONMENT_NOT_EMPTY:$name" }
}
$task = Get-ScheduledTask -TaskName $taskName -ErrorAction SilentlyContinue
if ($task -and $task.State -ne "Disabled") { throw "STAGE8_10_6_SCHEDULED_TASK_NOT_DISABLED" }
$robots = @(Get-CimInstance Win32_Process | Where-Object {
    $_.CommandLine -and $_.CommandLine -match "TradingSystemLab\.stage8_robot"
})
if ($robots.Count -ne 0) { throw "STAGE8_10_6_ROBOT_PROCESS_RUNNING" }

$temporary = Join-Path ([IO.Path]::GetTempPath()) ("stage8-10-6-" + [guid]::NewGuid().ToString("N"))
Push-Location $repo
try {
    # Actual runtime action is HALT only.  Synthetic ARMED fixtures remain isolated.
    & $Python -c "from pathlib import Path; from TradingSystemLab.stage8_robot.trading_safety_gate import emergency_halt,load_kill_switch; p=Path(r'''$runtime'''); emergency_halt(p); s,e=load_kill_switch(p); assert not e and s['state']=='HALTED'"
    if ($LASTEXITCODE -ne 0) { throw "STAGE8_10_6_PRODUCTION_HALT_FAILED" }
    & $Python -m TradingSystemLab.stage8_robot.safety_gate_validation --runtime-root $temporary --report $ReportPath
    if ($LASTEXITCODE -ne 0) { throw "STAGE8_10_6_VALIDATION_FAILED" }
    & $Python -c "from pathlib import Path; from TradingSystemLab.stage8_robot.trading_safety_gate import load_kill_switch; s,e=load_kill_switch(Path(r'''$runtime''')); assert not e and s['state']=='HALTED'"
    if ($LASTEXITCODE -ne 0) { throw "STAGE8_10_6_FINAL_HALT_INVALID" }
} finally {
    Pop-Location
    Remove-Item -LiteralPath $temporary -Recurse -Force -ErrorAction SilentlyContinue
}
