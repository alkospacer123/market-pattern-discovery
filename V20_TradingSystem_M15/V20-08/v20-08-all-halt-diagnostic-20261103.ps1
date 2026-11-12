# V20 incident 2026-11-03: collect evidence for all 3 robots, no trading actions.
# READONLY FINAM snapshots, WAL-safe SQLite copies, worker logs, task and switch state.
[CmdletBinding()]
param()
$ErrorActionPreference='Continue' # Capture expected HALT/error output from child commands; explicit file operations still fail closed.
Set-StrictMode -Version Latest
$root='c:\v20lab'
$stage=Join-Path $root 'pretrade-08\live-08'
$operator=Join-Path $stage 'v20-08-live-operator.ps1'
$launcher=Join-Path $stage 'v20-08-live-launch.ps1'
$names=@('v20-shallow','v20-obv','v20-inside')
if($env:OS -ne 'Windows_NT'){throw 'v20_incident_windows_required'}
foreach($file in @($operator,$launcher)){if(!(Test-Path -LiteralPath $file -PathType Leaf)){throw ('v20_incident_missing='+$file)}}
$stamp=([datetimeoffset]::UtcNow).ToString('yyyyMMddTHHmmssZ')
$out=Join-Path $env:userprofile ('downloads\v20-halt-all3-'+$stamp+'.zip')
$tmp=Join-Path $env:TEMP ('v20-halt-all3-'+$stamp)
if(Test-Path -LiteralPath $tmp){throw 'v20_incident_existing_temp'}
New-Item -ItemType Directory -Path $tmp -ErrorAction Stop | Out-Null
$summary=New-Object System.Collections.Generic.List[string]
$allflat=$true
try {
    $b=@(& powershell.exe -noprofile -noninteractive -executionpolicy bypass -file $operator -mode backup -robot all 2>&1 | ForEach-Object {[string]$_})
    $backupExit=$LASTEXITCODE
    $b | Set-Content -LiteralPath (Join-Path $tmp 'operator-backup-output.txt') -Encoding UTF8
    if($backupExit -ne 0){throw ('v20_incident_backup_failed_exit='+$backupExit)}
    $matches=@($b|Where-Object {$_ -match '^v20_08_5_backup=PASS path='})
    if($matches.Count -ne 1){throw 'v20_incident_backup_path_unproven'}
    $backupDir=$matches[0].Substring('v20_08_5_backup=PASS path='.Length)
    if(!(Test-Path -LiteralPath $backupDir -PathType Container)){throw 'v20_incident_backup_folder_missing'}
    Copy-Item -LiteralPath $backupDir -Destination (Join-Path $tmp 'sqlite-backup') -Recurse -ErrorAction Stop
    $summary.Add('sqlite_backup=PASS')
    $s=@(& powershell.exe -noprofile -noninteractive -executionpolicy bypass -file $operator -mode check -robot all 2>&1|ForEach-Object {[string]$_})
    $checkExit=$LASTEXITCODE
    $s|Set-Content -LiteralPath (Join-Path $tmp 'operator-check.txt') -Encoding UTF8
    $summary.Add('operator_check_exit='+$checkExit)
    foreach($name in $names){
        $dir=Join-Path $root ('robots\'+$name.Substring(4))
        $dest=Join-Path $tmp $name
        New-Item -ItemType Directory -Path $dest -ErrorAction Stop | Out-Null
        $log=Join-Path $dir 'logs\live-m15.jsonl'
        if(Test-Path -LiteralPath $log -PathType Leaf){
            Copy-Item -LiteralPath $log -Destination (Join-Path $dest 'live-m15.jsonl') -ErrorAction Stop
            $summary.Add($name+'_jsonl=PASS')
        } else {$summary.Add($name+'_jsonl=MISSING')}
        $switch=Join-Path $dir 'safety\stage8-trading-kill-switch.json'
        if(Test-Path -LiteralPath $switch -PathType Leaf){
            Copy-Item -LiteralPath $switch -Destination (Join-Path $dest 'kill-switch.json') -ErrorAction Stop
        }
        try{
            $task=Get-ScheduledTask -TaskName $name -TaskPath '\' -ErrorAction Stop
            $info=Get-ScheduledTaskInfo -TaskName $name -TaskPath '\' -ErrorAction Stop
            @('task='+$name,'task_state='+$task.State,'last_result='+$info.LastTaskResult,'last_run='+$info.LastRunTime) |
                Set-Content -LiteralPath (Join-Path $dest 'task.txt') -Encoding UTF8
        }catch{[string]$_|Set-Content -LiteralPath (Join-Path $dest 'task-error.txt') -Encoding UTF8}
        $ro=@(& powershell.exe -noprofile -noninteractive -executionpolicy bypass -file $launcher -mode readonly -robot $name 2>&1|ForEach-Object {[string]$_})
        $roExit=$LASTEXITCODE
        $ro|Set-Content -LiteralPath (Join-Path $dest 'finam-readonly.txt') -Encoding UTF8
        $clean=($roExit -eq 0 -and
            @($ro|Where-Object {$_ -eq 'v20_08_4_positions=0'}).Count -eq 1 -and
            @($ro|Where-Object {$_ -eq 'v20_08_4_active_orders=0'}).Count -eq 1)
        if(-not $clean){$allflat=$false}
        $state=if($clean){'PASS_BROKER_FLAT_NO_ACTIVE_ORDER'}else{'NOT_CONFIRMED'}
        $summary.Add($name+'_finam='+$state+'_exit_'+$roExit)
    }
    $summary.Add('no_orders_no_cancels_no_rearm_no_task_mutation=YES')
    $summary.Add('local_sqlite_and_logs_collected=YES')
    $summary.Add('finam_all_three_flat='+$(if($allflat){'PASS'}else{'NOT_CONFIRMED'}))
    $summary|Set-Content -LiteralPath (Join-Path $tmp 'SUMMARY.txt') -Encoding UTF8
    Compress-Archive -Path (Join-Path $tmp '*') -DestinationPath $out -CompressionLevel Optimal -ErrorAction Stop
    if(!(Test-Path -LiteralPath $out -PathType Leaf)){throw 'v20_incident_zip_missing'}
    $hash=(Get-FileHash -LiteralPath $out -Algorithm SHA256).Hash.ToLowerInvariant()
    $summary|Write-Output
    Write-Output ('v20_incident_zip='+$out)
    Write-Output ('v20_incident_sha256='+$hash)
} finally {
    if(Test-Path -LiteralPath $tmp){Remove-Item -LiteralPath $tmp -Recurse -Force -ErrorAction SilentlyContinue}
}
