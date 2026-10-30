# V20-08: pinned, FLAT-only LIVE worker cutover. No order POST/cancel; no H1, M15 or CC modification.
[CmdletBinding()]
param([ValidateSet('verify','install')][string]$mode='verify')
$ErrorActionPreference='Stop'
Set-StrictMode -Version Latest
$root='c:\v20lab'
$names=@('v20-shallow','v20-obv','v20-inside')
$stage=Join-Path $root 'pretrade-08\live-08'
$operator=Join-Path $stage 'v20-08-live-operator.ps1'
$launcher=Join-Path $stage 'v20-08-live-launch.ps1'
$runtime=Join-Path $root 'pretrade-08\live-runtime-08\V20_TradingSystem_M15\v20_runtime'
$worker=Join-Path $runtime 'finam_live.py'
$execution=Join-Path $runtime 'finam_execution.py'
$oldWorker='20a4cc425dc1b28d0d444349475ad4069fa04434'
$newWorker='e113003c7740d0923a7682242dc233461cb865d3'
$oldLauncher='2a6cce7a6b99a767ecf16fe2508a6f4bba6b36fb'
$newLauncher='220b9f3cc1a468af2bb52beaa0a43e4a6b079df4'
$executionHash='60a00ce58c436fd745f1fcbcb9e7f14b87fec787'
$operatorHash='6f539f9c421efb56d492f1c903b998b4e8f4a9ca'
function need([bool]$ok,[string]$code){if(-not $ok){throw $code}}
function blob([string]$path){
    need (Test-Path -LiteralPath $path -PathType Leaf) ('v20_update_missing '+$path)
    need (-not ((Get-Item -LiteralPath $path -Force).Attributes -band [io.fileattributes]::ReparsePoint)) 'v20_update_reparse_forbidden'
    $got=(& git.exe hash-object -- $path).Trim().ToLowerInvariant()
    need ($lastexitcode -eq 0) 'v20_update_git_hash_failed'
    return $got
}
function stage-blob([string]$sha,[string]$destination){
    if(Test-Path -LiteralPath $destination){need ((blob $destination) -ceq $sha) 'v20_update_staged_blob_conflict';return}
    $uri='https://api.github.com/repos/alkospacer123/market-pattern-discovery/git/blobs/'+$sha
    $r=Invoke-RestMethod -Uri $uri -Headers @{'user-agent'='v20lab'} -ErrorAction Stop
    need ($r.sha -ceq $sha -and $r.encoding -eq 'base64') 'v20_update_download_identity_invalid'
    [io.file]::WriteAllBytes($destination,[convert]::FromBase64String($r.content))
    need ((blob $destination) -ceq $sha) 'v20_update_download_hash_invalid'
}
function run-operator([string]$action){
    $lines=@(& powershell.exe -noprofile -noninteractive -executionpolicy bypass -file $operator -mode $action -robot all 2>&1)
    $lines | Write-Output
    need ($lastexitcode -eq 0) ('v20_update_operator_'+$action+'_failed')
    return $lines
}
function task-running([string]$name){return (Get-ScheduledTask -TaskName $name -TaskPath '\' -ErrorAction Stop).State -eq 'Running'}
function broker-flat([string]$name){
    $lines=@(& powershell.exe -noprofile -noninteractive -executionpolicy bypass -file $launcher -mode readonly -robot $name 2>&1)
    need ($lastexitcode -eq 0 -and
          ($lines -join '|') -match ('v20_08_4_readonly='+$name+' ACCOUNT_BOUND') -and
          ($lines -join '|') -match 'v20_08_4_positions=0' -and
          ($lines -join '|') -match 'v20_08_4_active_orders=0' -and
          ($lines -join '|') -match 'v20_08_4_order_posts=zero') ('v20_update_not_broker_flat_'+$name)
    Write-Output ('v20_update_'+$name+'_finam=flat_no_orders')
}
need ($env:OS -eq 'Windows_NT' -and $env:COMPUTERNAME -eq 'URIU-PC') 'v20_update_wrong_host'
need ((blob $operator) -eq $operatorHash) 'v20_update_operator_pin_mismatch'
need ((blob $execution) -eq $executionHash) 'v20_update_execution_pin_mismatch'
$workerHash=blob $worker
$launcherHash=blob $launcher
$old=($workerHash -eq $oldWorker -and $launcherHash -eq $oldLauncher)
$new=($workerHash -eq $newWorker -and $launcherHash -eq $newLauncher)
need ($old -or $new) 'v20_update_installed_version_unknown_or_mixed'
foreach($name in $names){need (task-running $name) ('v20_update_task_not_running_'+$name)}
if($new){Write-Output 'v20_night_protected=already_installed_pinned';return}
if($mode -eq 'verify'){Write-Output 'v20_night_protected_verify=pass_no_changes';return}
# Never initiate an installation requiring broker GET during the closed MOEX interval.
$msk=[timezoneinfo]::ConvertTimeFromUtc([datetime]::UtcNow,[timezoneinfo]::FindSystemTimeZoneById('Russian Standard Time'))
$minutes=$msk.Hour*60+$msk.Minute
need ($minutes -ge 410 -and $minutes -lt 1430) 'v20_update_moex_closed_install_forbidden'
# Stage immutable Git objects BEFORE touching any switch or task.
# Verify all accounts are FLAT first; an open trade must not halt healthy LIVE.
foreach($name in $names){broker-flat $name}
$stageWorker=$worker+'.protected-stage'
$stageLauncher=$launcher+'.protected-stage'
stage-blob $newWorker $stageWorker
stage-blob $newLauncher $stageLauncher
Write-Output 'v20_update_stage=pass_2_of_2'
# Existing operator stops new entries but keeps position/stop management alive.
[void](run-operator 'stop')
# One full FINAM GET for each account AFTER every V20 switch is HALTED.
foreach($name in $names){broker-flat $name}
[void](run-operator 'backup')
Write-Output 'v20_update_backup=pass'
$folder=Join-Path (Join-Path $root 'backup-08') ('night-protected-'+([datetimeoffset]::UtcNow).ToString('yyyyMMddTHHmmssZ'))
New-Item -ItemType Directory -Path $folder -Force -ErrorAction Stop | Out-Null
Copy-Item -LiteralPath $worker -Destination (Join-Path $folder 'finam_live.py') -ErrorAction Stop
Copy-Item -LiteralPath $launcher -Destination (Join-Path $folder 'v20-08-live-launch.ps1') -ErrorAction Stop
need ((blob (Join-Path $folder 'finam_live.py')) -eq $oldWorker -and
      (blob (Join-Path $folder 'v20-08-live-launch.ps1')) -eq $oldLauncher) 'v20_update_backup_hash_invalid'
foreach($name in $names){Stop-ScheduledTask -TaskName $name -TaskPath '\' -ErrorAction Stop}
foreach($name in $names){
    for($i=0;$i -lt 40 -and (task-running $name);$i++){Start-Sleep -Seconds 1}
    need (-not (task-running $name)) ('v20_update_worker_task_still_running_'+$name)
}
$processes=@(Get-CimInstance Win32_Process -Filter "Name='python.exe' OR Name='pythonw.exe'" -ErrorAction Stop |
    Where-Object {$_.CommandLine -match 'V20_TradingSystem_M15[.]v20_runtime[.]finam_live' -and
                  $_.CommandLine -match '--robot\s+v20-(shallow|obv|inside)'})
need ($processes.Count -eq 0) 'v20_update_old_python_worker_still_running'
Copy-Item -LiteralPath $stageWorker -Destination $worker -Force -ErrorAction Stop
Copy-Item -LiteralPath $stageLauncher -Destination $launcher -Force -ErrorAction Stop
need ((blob $worker) -eq $newWorker -and (blob $launcher) -eq $newLauncher) 'v20_update_new_pin_not_installed'
Write-Output 'v20_update_runtime=pass_2_of_2'
foreach($name in $names){Start-ScheduledTask -TaskName $name -TaskPath '\' -ErrorAction Stop}
foreach($name in $names){
    for($i=0;$i -lt 40 -and -not (task-running $name);$i++){Start-Sleep -Seconds 1}
    need (task-running $name) ('v20_update_new_worker_not_running_'+$name)
}
# Re-arm only with the existing operator's broker-clean authority.
[void](run-operator 'start')
[void](run-operator 'check')
Write-Output ('v20_night_protected_cutover=pass_3_of_3_running_armed_worker_e113003c7740d0923a7682242dc233461cb865d3')
Write-Output ('v20_update_rollback_files='+$folder)
