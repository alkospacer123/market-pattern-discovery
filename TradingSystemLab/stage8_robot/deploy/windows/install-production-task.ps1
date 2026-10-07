param(
  [Parameter(Mandatory=$true)][string]$Checkout,
  [Parameter(Mandatory=$true)][string]$RuntimeRoot,
  [Parameter(Mandatory=$true)][string]$AcceptedCommit,
  [string]$Python = "py.exe",
  [string]$TaskName = "TradingSystemLab-Stage8-Production"
)
$ErrorActionPreference = "Stop"
Set-Location $Checkout
$head = (git rev-parse HEAD).Trim()
if ($LASTEXITCODE -ne 0 -or $head -cne $AcceptedCommit) { throw "STAGE8_12_4_WRONG_PRODUCTION_COMMIT" }
$status = git status --porcelain
if ($LASTEXITCODE -ne 0 -or $status) { throw "STAGE8_12_4_PRODUCTION_REPOSITORY_NOT_CLEAN" }

. (Join-Path $PSScriptRoot "trading-credential-store.ps1")
. (Join-Path $PSScriptRoot "credential-store.ps1")
$principal = Get-CurrentPrincipalInfo
$productionId = (& $Python -c "from TradingSystemLab.stage8_robot.specification import PRODUCTION_SPECIFICATION_ID,load_frozen_specification; s=load_frozen_specification(); assert s.production_id == PRODUCTION_SPECIFICATION_ID; print(PRODUCTION_SPECIFICATION_ID)")
if ($LASTEXITCODE -ne 0) { throw "STAGE8_12_4_PRODUCTION_AUTHORITY_UNAVAILABLE" }
$verified = Get-TradingCredential $RuntimeRoot $productionId.Trim()
if ([string]::IsNullOrWhiteSpace([string]$verified.finam_real_account_id)) { throw "STAGE8_12_4_TRADING_DPAPI_ACCOUNT_MISSING" }
$verified = $null

$dirs = @("state", "audit", "logs", "diagnostics", "backups", "locks", "safety")
foreach ($dir in $dirs) { New-Item -ItemType Directory -Force -Path (Join-Path $RuntimeRoot $dir) | Out-Null }

$script = Join-Path $Checkout "TradingSystemLab\stage8_robot\deploy\windows\run-production.ps1"
$action = New-ScheduledTaskAction -Execute "powershell.exe" -Argument "-NoProfile -ExecutionPolicy RemoteSigned -File `"$script`" -Checkout `"$Checkout`" -RuntimeRoot `"$RuntimeRoot`" -AcceptedCommit `"$AcceptedCommit`" -Python `"$Python`""
$trigger = New-ScheduledTaskTrigger -AtStartup
$settings = New-ScheduledTaskSettingsSet -RestartCount 10 -RestartInterval (New-TimeSpan -Minutes 2) -ExecutionTimeLimit (New-TimeSpan -Days 3650) -MultipleInstances IgnoreNew
$taskPrincipal = New-ScheduledTaskPrincipal -UserId $principal.Name -LogonType Password -RunLevel Limited
$task = New-ScheduledTask -Action $action -Trigger $trigger -Settings $settings -Principal $taskPrincipal -Description "TradingSystemLab Stage 8.12.4 FULL/R15 production. Installed disabled; activation requires separate explicit authorization."

$taskCredential = Get-Credential -UserName $principal.Name -Message "Enter the password for this exact DPAPI credential owner; Windows LSA stores the task logon credential."
if ($taskCredential.UserName -ne $principal.Name) { throw "DPAPI_PRINCIPAL_MISMATCH" }
$passwordPtr = [Runtime.InteropServices.Marshal]::SecureStringToBSTR($taskCredential.Password)
try {
  $password = [Runtime.InteropServices.Marshal]::PtrToStringBSTR($passwordPtr)
  Register-ScheduledTask -TaskName $TaskName -InputObject $task -User $principal.Name -Password $password -Force | Out-Null
  Disable-ScheduledTask -TaskName $TaskName | Out-Null
} finally {
  $password = $null
  [Runtime.InteropServices.Marshal]::ZeroFreeBSTR($passwordPtr)
  $taskCredential = $null
}
$state = (Get-ScheduledTask -TaskName $TaskName).State
if ($state -ne "Disabled") { throw "STAGE8_12_4_PRODUCTION_TASK_NOT_DISABLED_AFTER_INSTALL" }
Write-Host "Installed $TaskName for exact commit $AcceptedCommit; state=Disabled; no authorization or activation performed."
