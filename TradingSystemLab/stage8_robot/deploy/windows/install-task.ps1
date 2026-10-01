param(
  [Parameter(Mandatory=$true)][string]$Checkout,
  [Parameter(Mandatory=$true)][string]$RuntimeRoot,
  [string]$Python = "py.exe",
  [string]$TaskName = "TradingSystemLab-Stage8-Readonly"
)
$ErrorActionPreference = "Stop"
if ($env:FINAM_MODE -and $env:FINAM_MODE -notin @("DRY_RUN", "REAL_READONLY")) { throw "LIVE_TRADING_NOT_AUTHORIZED" }
. (Join-Path $PSScriptRoot "credential-store.ps1")
$principal = Get-CurrentPrincipalInfo
$productionId = (& $Python -c "from TradingSystemLab.stage8_robot.specification import PRODUCTION_SPECIFICATION_ID,load_frozen_specification; s=load_frozen_specification(); assert s.production_id == PRODUCTION_SPECIFICATION_ID; print(PRODUCTION_SPECIFICATION_ID)")
if ($LASTEXITCODE -ne 0) { throw "DPAPI_PRODUCTION_AUTHORITY_UNAVAILABLE" }
$verified = Get-ReadonlyCredential $RuntimeRoot $productionId.Trim(); $verified = $null
Write-Host "Task principal: $($principal.Name) (SID $($principal.Sid)); credential principal match: true"
$dirs = @("state", "audit", "logs", "diagnostics", "backups")
foreach ($dir in $dirs) { New-Item -ItemType Directory -Force -Path (Join-Path $RuntimeRoot $dir) | Out-Null }
$script = Join-Path $Checkout "TradingSystemLab\stage8_robot\deploy\windows\run-readonly.ps1"
$action = New-ScheduledTaskAction -Execute "powershell.exe" -Argument "-NoProfile -ExecutionPolicy RemoteSigned -File `"$script`" -Checkout `"$Checkout`" -RuntimeRoot `"$RuntimeRoot`" -Python `"$Python`""
$trigger = New-ScheduledTaskTrigger -AtStartup
$settings = New-ScheduledTaskSettingsSet -RestartCount 10 -RestartInterval (New-TimeSpan -Minutes 2) -ExecutionTimeLimit (New-TimeSpan -Days 3650) -MultipleInstances IgnoreNew
$taskPrincipal = New-ScheduledTaskPrincipal -UserId $principal.Name -LogonType Password -RunLevel Limited
$task = New-ScheduledTask -Action $action -Trigger $trigger -Settings $settings -Principal $taskPrincipal -Description "Stage 8 FINAM REAL_READONLY; no order transmission"
$taskCredential = Get-Credential -UserName $principal.Name -Message "Enter the password for this exact DPAPI credential owner; Windows LSA stores the task logon credential."
if ($taskCredential.UserName -ne $principal.Name) { throw "DPAPI_PRINCIPAL_MISMATCH" }
$passwordPtr = [Runtime.InteropServices.Marshal]::SecureStringToBSTR($taskCredential.Password)
try {
  $password = [Runtime.InteropServices.Marshal]::PtrToStringBSTR($passwordPtr)
  Register-ScheduledTask -TaskName $TaskName -InputObject $task -User $principal.Name -Password $password -Force | Out-Null
} finally {
  $password = $null; [Runtime.InteropServices.Marshal]::ZeroFreeBSTR($passwordPtr); $taskCredential = $null
}
Write-Host "Installed $TaskName in REAL_READONLY-safe configuration. Secret is not in the task command line."
