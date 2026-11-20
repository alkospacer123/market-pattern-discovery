# V20-08.2: 8 fake-only tests -> exact V20-only offline source upgrade -> 3 narrow owner grants.
# Run after owner authorized all 3 first trials; does NOT contact FINAM, arm switches or enable Tasks.
[CmdletBinding()]
param([ValidateSet('cnyrubf','usdrubf','gldrubf','imoexf')][string]$Symbol='cnyrubf')
$ErrorActionPreference='Stop'
Set-StrictMode -Version Latest
$pin='1e6b8cc89c9c8d7b66b7cfeea7837e464cb03f78'
$root='C:\V20Lab'
$workspace=Join-Path $root 'pretrade-08\offline-prep-approved-08'
function need([bool]$condition,[string]$code) { if (-not $condition) { throw $code } }
need ($env:OS -eq 'Windows_NT' -and $env:COMPUTERNAME -eq 'URIU-PC') 'V20_08_2_WRONG_HOST'
need (Test-Path -LiteralPath (Join-Path $root 'pretrade-08') -PathType Container) 'V20_08_2_PRETRADE_DIR_MISSING'
foreach ($n in @('v20-shallow','v20-obv','v20-inside')) {
    $task=Get-ScheduledTask -TaskName $n -TaskPath '\' -ErrorAction Stop
    need ($task.State -eq 'Disabled' -and @($task.Actions).Count -eq 1 -and
          $task.Actions[0].Arguments.Contains('v20-task-live-blocked.ps1')) 'V20_08_2_TASK_NOT_DISABLED'
}
New-Item -ItemType Directory -Path $workspace -Force | Out-Null
need (-not ((Get-Item -LiteralPath $workspace -Force).Attributes -band [IO.FileAttributes]::ReparsePoint)) 'V20_08_2_WORKSPACE_LINK_FORBIDDEN'
$files=@(
  @('invoke-offline-trial-operator-tests.ps1','23397a966aeda13de3659e9e2a8c819fc94b5753'),
  @('Install-Offline-Trial-Operator.ps1','e9b18cc3a5614172e3c677d7005876b0d4e4ae5f'),
  @('Approve-Three-First-Frozen-Trials.ps1','903f3b96663753697d75335176e85e1bdf13c28f')
)
foreach ($entry in $files) {
    $name=[string]$entry[0]
    $expected=[string]$entry[1]
    $to=Join-Path $workspace $name
    if (Test-Path -LiteralPath $to) {
        need (-not ((Get-Item -LiteralPath $to -Force).Attributes -band [IO.FileAttributes]::ReparsePoint)) 'V20_08_2_EXISTING_SCRIPT_LINK'
        $h=(& git.exe hash-object -- $to).Trim().ToLowerInvariant()
        need ($LASTEXITCODE -eq 0 -and $h -eq $expected) 'V20_08_2_PINNED_SCRIPT_CONFLICT'
        continue
    }
    $tmp=$to+'.download'
    need (-not (Test-Path -LiteralPath $tmp)) 'V20_08_2_PARTIAL_DOWNLOAD'
    try {
        $url='https://raw.githubusercontent.com/alkospacer123/market-pattern-discovery/'+$pin+'/V20_TradingSystem_M15/V20-08/'+$name
        Invoke-WebRequest -Uri $url -OutFile $tmp -UseBasicParsing
        $h=(& git.exe hash-object -- $tmp).Trim().ToLowerInvariant()
        need ($LASTEXITCODE -eq 0 -and $h -eq $expected) 'V20_08_2_DOWNLOADED_BLOB_WRONG'
        Move-Item -LiteralPath $tmp -Destination $to -ErrorAction Stop
    } finally { if (Test-Path -LiteralPath $tmp) { Remove-Item -LiteralPath $tmp -Force } }
}
# The three operations are safe offline only; stop immediately if new tests FAIL.
& powershell.exe -noprofile -noninteractive -executionpolicy bypass -file (Join-Path $workspace $files[0][0])
need ($LASTEXITCODE -eq 0) 'V20_08_2_TARGETED_OFFLINE_TEST_FAILED'
& powershell.exe -noprofile -noninteractive -executionpolicy bypass -file (Join-Path $workspace $files[1][0])
need ($LASTEXITCODE -eq 0) 'V20_08_2_PINNED_OFFLINE_SOURCE_UPGRADE_FAILED'
& powershell.exe -noprofile -noninteractive -executionpolicy bypass -file (Join-Path $workspace $files[2][0]) -symbol $Symbol
need ($LASTEXITCODE -eq 0) 'V20_08_2_FIRST_FROZEN_SCOPE_NOT_ACCEPTED'
Write-Output 'v20_08_2_offline_prep=PASS_3_ACTIONS'
Write-Output 'v20_08_2_finam=NO_NETWORK'
Write-Output 'v20_08_2_orders=zero'
Write-Output 'v20_08_2_live=off'
Write-Output 'v20_08_2_tasks_modified=no'
