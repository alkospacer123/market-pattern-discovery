param(
  [Parameter(Mandatory=$true)][string]$Checkout,
  [Parameter(Mandatory=$true)][string]$RuntimeRoot,
  [string]$Python = "py.exe",
  [string]$TaskName = "TradingSystemLab-Stage8-Readonly"
)
$ErrorActionPreference = "Stop"
if ($env:FINAM_MODE -and $env:FINAM_MODE -notin @("DRY_RUN", "REAL_READONLY")) { throw "LIVE_TRADING_NOT_AUTHORIZED" }
$dirs = @("state", "audit", "logs", "diagnostics", "backups")
foreach ($dir in $dirs) { New-Item -ItemType Directory -Force -Path (Join-Path $RuntimeRoot $dir) | Out-Null }
$script = Join-Path $Checkout "TradingSystemLab\stage8_robot\deploy\windows\run-readonly.ps1"
$action = New-ScheduledTaskAction -Execute "powershell.exe" -Argument "-NoProfile -ExecutionPolicy AllSigned -File `"$script`" -Checkout `"$Checkout`" -RuntimeRoot `"$RuntimeRoot`" -Python `"$Python`""
$trigger = New-ScheduledTaskTrigger -AtStartup
$settings = New-ScheduledTaskSettingsSet -RestartCount 10 -RestartInterval (New-TimeSpan -Minutes 2) -ExecutionTimeLimit (New-TimeSpan -Days 3650)
Register-ScheduledTask -TaskName $TaskName -Action $action -Trigger $trigger -Settings $settings -Description "Stage 8 FINAM REAL_READONLY; no order transmission" | Out-Null
Write-Host "Installed $TaskName in REAL_READONLY-safe configuration. Secret is not in the task command line."

