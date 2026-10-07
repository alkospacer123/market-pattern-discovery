param(
    [Parameter(Mandatory=$true)][string]$Checkout,
    [Parameter(Mandatory=$true)][string]$RuntimeRoot,
    [Parameter(Mandatory=$true)][string]$Stage5DataRoot,
    [string]$Python = "py.exe",
    [string]$TaskName = "TradingSystemLab-Stage8-Production",
    [string]$ReadonlyTaskName = "TradingSystemLab-Stage8-Readonly"
)
$ErrorActionPreference = "Stop"
$expectedStage5Commit = "50f1fd2178c18b7ab3bd969be82ad01f47a34745"

$existing = Get-ScheduledTask -TaskName $TaskName -ErrorAction SilentlyContinue
if ($existing) { throw "STAGE8_12_4_PRODUCTION_TASK_ALREADY_EXISTS" }
$readonly = Get-ScheduledTask -TaskName $ReadonlyTaskName -ErrorAction SilentlyContinue
if ($readonly -and $readonly.State -ne "Disabled") {
    throw "STAGE8_12_4_READONLY_TASK_MUST_REMAIN_DISABLED"
}

$commit = (& git -C $Checkout rev-parse HEAD).Trim()
if ($LASTEXITCODE -ne 0 -or $commit -notmatch '^[0-9a-f]{40}$') {
    throw "STAGE8_12_4_PRODUCTION_COMMIT_UNAVAILABLE"
}
$dirty = & git -C $Checkout status --porcelain
if ($LASTEXITCODE -ne 0 -or $dirty) {
    throw "STAGE8_12_4_PRODUCTION_CHECKOUT_NOT_CLEAN"
}
$dataCommit = (& git -C $Stage5DataRoot rev-parse HEAD).Trim()
if ($LASTEXITCODE -ne 0 -or $dataCommit -cne $expectedStage5Commit) {
    throw "STAGE8_12_4_STAGE5_DATA_COMMIT_MISMATCH"
}
$dataDirty = & git -C $Stage5DataRoot status --porcelain
if ($LASTEXITCODE -ne 0 -or $dataDirty) {
    throw "STAGE8_12_4_STAGE5_DATA_CHECKOUT_NOT_CLEAN"
}

. (Join-Path $PSScriptRoot "trading-credential-store.ps1")
$productionId = (& $Python -c "from TradingSystemLab.stage8_robot.specification import PRODUCTION_SPECIFICATION_ID,load_frozen_specification; s=load_frozen_specification(); assert s.production_id == PRODUCTION_SPECIFICATION_ID; print(PRODUCTION_SPECIFICATION_ID)")
if ($LASTEXITCODE -ne 0 -or [string]::IsNullOrWhiteSpace($productionId)) {
    throw "TRADING_DPAPI_PRODUCTION_AUTHORITY_UNAVAILABLE"
}
$principal = Get-TradingPrincipal
$credential = Get-TradingCredential $RuntimeRoot $productionId.Trim()
$credential = $null

foreach ($dir in @("state","audit","logs","diagnostics","backups","safety")) {
    New-Item -ItemType Directory -Force -Path (Join-Path $RuntimeRoot $dir) | Out-Null
}
$script = Join-Path $Checkout "TradingSystemLab\stage8_robot\deploy\windows\run-production.ps1"
$arguments = "-NoProfile -ExecutionPolicy RemoteSigned -File `"$script`" -Checkout `"$Checkout`" -RuntimeRoot `"$RuntimeRoot`" -Stage5DataRoot `"$Stage5DataRoot`" -ExpectedCommit $commit -Python `"$Python`""
$action = New-ScheduledTaskAction -Execute "powershell.exe" -Argument $arguments
$trigger = New-ScheduledTaskTrigger -AtStartup
$settings = New-ScheduledTaskSettingsSet -RestartCount 10 -RestartInterval (New-TimeSpan -Minutes 2) -ExecutionTimeLimit (New-TimeSpan -Days 3650) -MultipleInstances IgnoreNew
$currentName = [Security.Principal.WindowsIdentity]::GetCurrent().Name
$taskPrincipal = New-ScheduledTaskPrincipal -UserId $currentName -LogonType Password -RunLevel Limited
$task = New-ScheduledTask -Action $action -Trigger $trigger -Settings $settings -Principal $taskPrincipal -Description "Stage 8.12.4 production service; installation is disabled and activation is a later explicit package"

$taskCredential = Get-Credential -UserName $currentName -Message "Enter the password for the exact DPAPI trading-credential owner."
if ($taskCredential.UserName -cne $currentName) {
    throw "STAGE8_12_4_PRODUCTION_TASK_PRINCIPAL_MISMATCH"
}
$passwordPtr = [Runtime.InteropServices.Marshal]::SecureStringToBSTR($taskCredential.Password)
try {
    $password = [Runtime.InteropServices.Marshal]::PtrToStringBSTR($passwordPtr)
    Register-ScheduledTask -TaskName $TaskName -InputObject $task -User $taskCredential.UserName -Password $password | Out-Null
} finally {
    $password = $null
    [Runtime.InteropServices.Marshal]::ZeroFreeBSTR($passwordPtr)
    $taskCredential = $null
}
Disable-ScheduledTask -TaskName $TaskName | Out-Null
$installed = Get-ScheduledTask -TaskName $TaskName
if ($installed.State -ne "Disabled") {
    throw "STAGE8_12_4_PRODUCTION_TASK_NOT_DISABLED"
}
Write-Output "STAGE8_12_4_PRODUCTION_TASK_INSTALLED_DISABLED"
Write-Output "task_name=$TaskName"
Write-Output "production_commit=$commit"
Write-Output "stage5_data_commit=$dataCommit"
Write-Output "authorization_created=false"
Write-Output "kill_switch_changed=false"
Write-Output "task_started=false"
