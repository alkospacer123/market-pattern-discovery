# V20-08: flat-only weekend-entry gate + explicit night status.
# No changes to strategy indicators, SLTP, risk, H1, old M15 or Control Center.
[CmdletBinding()]
param([ValidateSet('verify','install')][string]$mode='verify')
$ErrorActionPreference='Stop'
Set-StrictMode -Version Latest
$root='c:\v20lab'
$names=@('v20-shallow','v20-obv','v20-inside')
$stage=Join-Path $root 'pretrade-08\live-08'
$operator=Join-Path $stage 'v20-08-live-operator.ps1'
$launcher=Join-Path $stage 'v20-08-live-launch.ps1'
$worker=Join-Path $root 'pretrade-08\live-runtime-08\V20_TradingSystem_M15\v20_runtime\finam_live.py'
$old=@{
    worker='e113003c7740d0923a7682242dc233461cb865d3'
    launcher='220b9f3cc1a468af2bb52beaa0a43e4a6b079df4'
    operator='6f539f9c421efb56d492f1c903b998b4e8f4a9ca'
}
$new=@{
    worker='61ab6dea13a9a9c0eeeae2752a565e252966ebfc'
    launcher='73fef366b2ac982dc2db27dea65d3ca9c7ce2a5f'
    operator='869ecc102963e070c704714a38e525215374d4ab'
}
$files=@{worker=$worker;launcher=$launcher;operator=$operator}
function need([bool]$ok,[string]$code){if(-not $ok){throw $code}}
function blob([string]$p){
    need (Test-Path -LiteralPath $p -PathType Leaf) ('v20_weekend_file_missing '+$p)
    need (-not ((Get-Item -LiteralPath $p -Force).Attributes -band [io.fileattributes]::ReparsePoint)) 'v20_weekend_reparse_forbidden'
    $h=(& git.exe hash-object -- $p).Trim().ToLowerInvariant()
    need ($lastexitcode -eq 0) 'v20_weekend_hash_error'
    return $h
}
function task-running([string]$name){
    return (Get-ScheduledTask -TaskName $name -TaskPath '\' -ErrorAction Stop).State -eq 'Running'
}
function call-operator([string]$action){
    $lines=@(& powershell.exe -noprofile -noninteractive -executionpolicy bypass -file $operator -mode $action -robot all 2>&1)
    $lines | Write-Output
    need ($lastexitcode -eq 0) ('v20_weekend_operator_'+$action+'_failed')
}
function broker-flat([string]$name){
    $lines=@(& powershell.exe -noprofile -noninteractive -executionpolicy bypass -file $launcher -mode readonly -robot $name 2>&1)
    need ($lastexitcode -eq 0 -and
          ($lines -join '|') -match ('v20_08_4_readonly='+$name+' ACCOUNT_BOUND') -and
          ($lines -join '|') -match 'v20_08_4_positions=0' -and
          ($lines -join '|') -match 'v20_08_4_active_orders=0' -and
          ($lines -join '|') -match 'v20_08_4_order_posts=zero') ('v20_weekend_broker_not_flat_'+$name)
    Write-Output ('v20_weekend_'+$name+'_broker=flat_no_orders')
}
function stage-file([string]$key){
    $dst=$files[$key]+'.weekend-stage'
    $expected=$new[$key]
    if(Test-Path -LiteralPath $dst){need ((blob $dst) -eq $expected) 'v20_weekend_stage_conflict';return}
    $response=Invoke-RestMethod -Uri ('https://api.github.com/repos/alkospacer123/market-pattern-discovery/git/blobs/'+$expected) -Headers @{'user-agent'='v20lab'} -ErrorAction Stop
    need ($response.sha -ceq $expected -and $response.encoding -eq 'base64') 'v20_weekend_stage_source_invalid'
    [io.file]::WriteAllBytes($dst,[convert]::FromBase64String($response.content))
    need ((blob $dst) -eq $expected) 'v20_weekend_stage_hash_invalid'
}
need ($env:OS -eq 'Windows_NT' -and $env:COMPUTERNAME -eq 'URIU-PC') 'v20_weekend_wrong_host'
$have=@{};foreach($key in $files.Keys){$have[$key]=blob $files[$key]}
$oldSet=@($files.Keys | Where-Object {$have[$_] -eq $old[$_]}).Count -eq 3
$newSet=@($files.Keys | Where-Object {$have[$_] -eq $new[$_]}).Count -eq 3
need ($oldSet -or $newSet) 'v20_weekend_installed_release_unknown_or_mixed'
foreach($name in $names){need (task-running $name) ('v20_weekend_task_not_running_'+$name)}
if($newSet){Write-Output 'v20_weekend_update=already_installed_3_of_3';return}
if($mode -eq 'verify'){Write-Output 'v20_weekend_verify=pass_old_release_no_changes';return}
$clock=[timezoneinfo]::ConvertTimeFromUtc([datetime]::UtcNow,[timezoneinfo]::FindSystemTimeZoneById('Russian Standard Time'))
$minutes=$clock.Hour*60+$clock.Minute
need ($minutes -ge 410 -and $minutes -lt 1430) 'v20_weekend_closed_night_install_forbidden'
# A live position (including one opened Friday) must keep existing worker protection.
foreach($name in $names){broker-flat $name}
foreach($key in @('worker','launcher','operator')){stage-file $key}
Write-Output 'v20_weekend_stage=pass_3_of_3'
# Halt only new entries while old workers continue position/stop management.
call-operator 'stop'
foreach($name in $names){broker-flat $name}
call-operator 'backup'
$folder=Join-Path (Join-Path $root 'backup-08') ('weekend-entry-'+([datetimeoffset]::UtcNow).ToString('yyyyMMddTHHmmssZ'))
New-Item -ItemType Directory -Path $folder -Force -ErrorAction Stop | Out-Null
foreach($key in @('worker','launcher','operator')){
    $backup=Join-Path $folder ([io.path]::GetFileName($files[$key]))
    Copy-Item -LiteralPath $files[$key] -Destination $backup -ErrorAction Stop
    need ((blob $backup) -eq $old[$key]) ('v20_weekend_backup_hash_invalid_'+$key)
}
Write-Output 'v20_weekend_backup=pass_3_of_3'
foreach($name in $names){Stop-ScheduledTask -TaskName $name -TaskPath '\' -ErrorAction Stop}
foreach($name in $names){
    for($i=0;$i -lt 40 -and (task-running $name);$i++){Start-Sleep -Seconds 1}
    need (-not (task-running $name)) ('v20_weekend_old_task_alive_'+$name)
}
$workers=@(Get-CimInstance Win32_Process -Filter "Name='python.exe' OR Name='pythonw.exe'" -ErrorAction Stop |
    Where-Object {$_.CommandLine -match 'V20_TradingSystem_M15[.]v20_runtime[.]finam_live' -and
                  $_.CommandLine -match '--robot\s+v20-(shallow|obv|inside)'})
need ($workers.Count -eq 0) 'v20_weekend_old_python_worker_alive'
foreach($key in @('worker','launcher','operator')){
    Copy-Item -LiteralPath ($files[$key]+'.weekend-stage') -Destination $files[$key] -Force -ErrorAction Stop
    need ((blob $files[$key]) -eq $new[$key]) ('v20_weekend_new_hash_invalid_'+$key)
}
Write-Output 'v20_weekend_runtime=pass_3_of_3'
foreach($name in $names){Start-ScheduledTask -TaskName $name -TaskPath '\' -ErrorAction Stop}
foreach($name in $names){
    for($i=0;$i -lt 40 -and -not (task-running $name);$i++){Start-Sleep -Seconds 1}
    need (task-running $name) ('v20_weekend_new_task_not_running_'+$name)
}
# The operator's START checks broker authority and arms each existing Task.
# Do not run an immediate age<90s CHECK before the first fresh worker cycle.
call-operator 'start'
Write-Output 'v20_weekend_cutover=pass_3_of_3_running_armed'
Write-Output ('v20_weekend_rollback_files='+$folder)
