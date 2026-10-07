param(
  [Parameter(Mandatory=$true)][string]$Checkout,
  [Parameter(Mandatory=$true)][string]$RuntimeRoot,
  [Parameter(Mandatory=$true)][string]$DataRoot,
  [Parameter(Mandatory=$true)][string]$AcceptedCommit,
  [string]$Python = "",
  [string]$TaskName = "TradingSystemLab-Stage8-Production"
)

$ErrorActionPreference = "Stop"
$expectedDataCommit = "50f1fd2178c18b7ab3bd969be82ad01f47a34745"
$productionId = "PROD_STAGE7_46DB784378797C7FB04636892350AFF21006D71A31F2CED9D4B974EDA2DC36B8"

if ([string]::IsNullOrWhiteSpace($Python)) {
  $Python = Join-Path $RuntimeRoot "venv\Scripts\python.exe"
}
if (-not (Test-Path $Python -PathType Leaf)) { throw "PRODUCTION_PYTHON_VENV_MISSING" }

function Require-ExactCleanCheckout([string]$Path,[string]$Expected,[string]$Code) {
  if (-not (Test-Path $Path -PathType Container)) { throw ($Code + "_MISSING") }
  $head = (& git -C $Path rev-parse HEAD).Trim()
  if ($LASTEXITCODE -ne 0 -or $head -cne $Expected) { throw ($Code + "_WRONG_COMMIT:" + $head) }
  $status = & git -C $Path status --porcelain
  if ($LASTEXITCODE -ne 0) { throw ($Code + "_GIT_STATUS_FAILED") }
  if ($status) { throw ($Code + "_NOT_CLEAN") }
}

Require-ExactCleanCheckout $Checkout $AcceptedCommit "PRODUCTION_CHECKOUT"
Require-ExactCleanCheckout $DataRoot $expectedDataCommit "PRODUCTION_DATA_CHECKOUT"

$readonly = Get-ScheduledTask -TaskName "TradingSystemLab-Stage8-Readonly" -ErrorAction SilentlyContinue
if ($null -ne $readonly -and $readonly.State -ne "Disabled") { throw "READONLY_TASK_MUST_BE_DISABLED" }

. (Join-Path $PSScriptRoot "trading-credential-store.ps1")
$principal = Get-TradingPrincipal
$credential = Get-TradingCredential $RuntimeRoot $productionId
$credential = $null

$dirs = @("state","audit","logs","diagnostics","backups","safety","locks")
foreach ($dir in $dirs) { New-Item -ItemType Directory -Force -Path (Join-Path $RuntimeRoot $dir) | Out-Null }

$runner = Join-Path $Checkout "TradingSystemLab\stage8_robot\deploy\windows\run-production.ps1"
if (-not (Test-Path $runner -PathType Leaf)) { throw "PRODUCTION_RUNNER_MISSING" }
$args = "-NoProfile -ExecutionPolicy RemoteSigned -File ```"$runner```" -Checkout ```"$Checkout```" -RuntimeRoot ```"$RuntimeRoot```" -DataRoot ```"$DataRoot```" -AcceptedCommit $AcceptedCommit -Python ```"$Python```""
$action = New-ScheduledTaskAction -Execute "powershell.exe" -Argument $args
$trigger = New-ScheduledTaskTrigger -AtStartup
$settings = New-ScheduledTaskSettingsSet -RestartCount 10 -RestartInterval (New-TimeSpan -Minutes 2) -ExecutionTimeLimit (New-TimeSpan -Days 3650) -MultipleInstances IgnoreNew
$taskPrincipal = New-ScheduledTaskPrincipal -UserId ([Security.Principal.WindowsIdentity]::GetCurrent().Name) -LogonType Password -RunLevel Limited
$task = New-ScheduledTask -Action $action -Trigger $trigger -Settings $settings -Principal $taskPrincipal -Description "Stage 8.12.4 FULL/R15 production; exact authorization + ARMED gate required by service"
$taskCredential = Get-Credential -UserName ([Security.Principal.WindowsIdentity]::GetCurrent().Name) -Message "Enter the password for this exact DPAPI credential owner; Windows LSA stores the task logon credential."
if ($taskCredential.UserName -ne ([Security.Principal.WindowsIdentity]::GetCurrent().Name)) { throw "DPAPI_PRINCIPAL_MISMATCH" }
$passwordPtr = [Runtime.InteropServices.Marshal]::SecureStringToBSTR($taskCredential.Password)
try {
  $password = [Runtime.InteropServices.Marshal]::PtrToStringBSTR($passwordPtr)
  Register-ScheduledTask -TaskName $TaskName -InputObject $task -User $taskCredential.UserName -Password $password -Force | Out-Null
}
finally {
  $password = $null
  [Runtime.InteropServices.Marshal]::ZeroFreeBSTR($passwordPtr)
  $taskCredential = $null
}
Disable-ScheduledTask -TaskName $TaskName | Out-Null
$installed = Get-ScheduledTask -TaskName $TaskName
if ($installed.State -ne "Disabled") { throw "PRODUCTION_TASK_NOT_DISABLED_AFTER_INSTALL" }
Write-Output "STAGE8_12_4_PRODUCTION_TASK_INSTALLED=true"
Write-Output "STAGE8_12_4_PRODUCTION_TASK_STATE=Disabled"
Write-Output "STAGE8_12_4_EXECUTION_AUTHORIZED=false"
