# V20-08.5: V20-only operations over the EXISTING H1-style V20 Tasks and
# kill switches. No modifications to H1, IntradayLab M15 or Control Center.
[CmdletBinding()]
param(
    [ValidateSet('check','start','stop','restart','backup')][string]$mode='check',
    [ValidateSet('v20-shallow','v20-obv','v20-inside','all')][string]$robot='all'
)
$ErrorActionPreference='Stop'
Set-StrictMode -Version Latest
$root='C:\V20Lab'
$stage=Join-Path $root 'pretrade-08\live-08'
$launcher=Join-Path $stage 'v20-08-live-launch.ps1'
$prepared=Join-Path $stage 'LIVE_PREPARED.json'
$python=Join-Path $root '.venv-raw\scripts\python.exe'
$source='dd55f201b3e9a92ce5fa3f927289f5a5ef89366d'
$names=@('v20-shallow','v20-obv','v20-inside')
$selected=@(if($robot -eq 'all'){$names}else{$robot})
function need([bool]$ok,[string]$code){if(-not $ok){throw $code}}
function id-sid([string]$value){
    try{
        if($value -match '^S-[0-9]+(-[0-9]+)+$'){return ([Security.Principal.SecurityIdentifier]::new($value)).Value}
        return ([Security.Principal.NTAccount]::new($value)).Translate([Security.Principal.SecurityIdentifier]).Value
    }catch{return ''}
}
function exact-task([string]$name){
    $task=Get-ScheduledTask -TaskName $name -TaskPath '\' -ErrorAction Stop
    $expected='-noprofile -noninteractive -executionpolicy bypass -file "'+$launcher+'" -mode run -robot '+$name
    $dir=Join-Path $root ('robots\'+$name.Substring(4))
    need (@($task.Actions).Count -eq 1 -and
          $task.Actions[0].Execute -ieq 'powershell.exe' -and
          $task.Actions[0].Arguments -ieq $expected -and
          $task.Actions[0].WorkingDirectory -ieq $dir -and
          (id-sid ([string]$task.Principal.UserId)) -eq $sid) 'V20_08_5_TASK_OR_SID_MISMATCH'
    return $task
}
function call-launcher([string]$name,[string]$action){
    $lines=@(& powershell.exe -noprofile -noninteractive -executionpolicy bypass -file $launcher -mode $action -robot $name 2>&1)
    need ($LASTEXITCODE -eq 0) ('V20_08_5_'+$action.ToUpperInvariant()+'_FAILED')
    return $lines
}
function proof([string]$name,[bool]$verbose=$false){
    $t=exact-task $name
    $instance=Join-Path $root ('robots\'+$name.Substring(4))
    $switchPath=Join-Path $instance 'safety\stage8-trading-kill-switch.json'
    $log=Join-Path $instance 'logs\live-m15.jsonl'
    need ((Test-Path -LiteralPath $switchPath -PathType Leaf) -and
          (Test-Path -LiteralPath $log -PathType Leaf)) 'V20_08_5_LOG_OR_SWITCH_MISSING'
    $switch=Get-Content -LiteralPath $switchPath -Raw -Encoding UTF8 | ConvertFrom-Json
    $lines=@(Get-Content -LiteralPath $log -Tail 10 -Encoding UTF8)
    $last=$null
    for($i=$lines.Count-1;$i -ge 0;$i--){
        try{
            $candidate=$lines[$i] | ConvertFrom-Json -ErrorAction Stop
            if($candidate.robot -eq $name -and $candidate.utc -and $candidate.state){$last=$candidate;break}
        }catch{}
    }
    need ($null -ne $last) 'V20_08_5_LAST_CYCLE_MISSING'
    $age=([datetimeoffset]::UtcNow-[datetimeoffset]::Parse([string]$last.utc,[globalization.cultureinfo]::InvariantCulture)).TotalSeconds
    $healthy=($t.State -eq 'Running' -and $switch.state -eq 'ARMED' -and
              [string]$last.state -notmatch '^HALT' -and $age -ge -5 -and $age -le 90)
    Write-Output ('v20_08_5_'+$name+'_task='+$t.State)
    Write-Output ('v20_08_5_'+$name+'_switch='+$switch.state)
    Write-Output ('v20_08_5_'+$name+'_cycle='+[string]$last.state)
    Write-Output ('v20_08_5_'+$name+'_age_seconds='+[math]::Round($age))
    Write-Output ('v20_08_5_'+$name+'_healthy='+$healthy)
    if($verbose){
        foreach($line in $lines){
            try{
                $row=$line | ConvertFrom-Json -ErrorAction Stop
                if($row.robot -eq $name -and $row.utc -and $row.state){
                    Write-Output ('v20_08_5_'+$name+'_history='+$row.utc+' '+$row.state)
                }
            }catch{}
        }
    }
    return $healthy
}
function await-cycle([string]$name,[datetimeoffset]$started){
    for($i=0;$i -lt 95;$i++){
        $t=exact-task $name
        $path=Join-Path $root ('robots\'+$name.Substring(4)+'\logs\live-m15.jsonl')
        if($t.State -eq 'Running' -and (Test-Path -LiteralPath $path)){
            $last=Get-Content -LiteralPath $path -Tail 1 -Encoding UTF8 | ConvertFrom-Json
            $stamp=[datetimeoffset]::Parse([string]$last.utc,[globalization.cultureinfo]::InvariantCulture)
            if($last.robot -eq $name -and $stamp -ge $started.AddSeconds(-5) -and
               [string]$last.state -notmatch '^HALT'){return}
        }
        Start-Sleep -Seconds 1
    }
    throw 'V20_08_5_TASK_FRESH_CYCLE_MISSING'
}
need ($env:OS -eq 'Windows_NT' -and $env:COMPUTERNAME -eq 'URIU-PC') 'V20_08_5_WRONG_INTEL'
need ((Test-Path -LiteralPath $prepared -PathType Leaf) -and
      (Test-Path -LiteralPath $launcher -PathType Leaf)) 'V20_08_5_LIVE_FILES_MISSING'
$sid=[Security.Principal.WindowsIdentity]::GetCurrent().User.Value
$receipt=Get-Content -LiteralPath $prepared -Raw -Encoding UTF8 | ConvertFrom-Json
need ($receipt.schema -eq 'v20.08.4.live_prepared.v1' -and
      $receipt.status -eq 'PASS_3_OF_3_OFFLINE_PREPARED' -and
      $receipt.source_commit -eq $source -and
      @($receipt.robots).Count -eq 3) 'V20_08_5_PREP_NOT_AUTHORIZED'
foreach($name in $selected){[void](exact-task $name)}
if($mode -eq 'check'){
    $valid=0
    foreach($name in $selected){
        $lines=@(proof $name $true)
        $lines | Write-Output
        if(($lines -join '|') -match ('v20_08_5_'+$name+'_healthy=True')){$valid++}
    }
    need ($valid -eq $selected.Count) 'V20_08_5_HEALTH_PARTIAL'
    Write-Output ('v20_08_5_check=PASS_'+$valid+'_OF_'+$selected.Count)
    return
}
if($mode -eq 'stop'){
    # Stop NEW ENTRIES only; workers keep managing actual positions and SLTP.
    foreach($name in $selected){
        $lines=@(call-launcher $name 'halt')
        need (($lines -join '|') -match ('v20_08_4_switch=HALTED_'+$name)) 'V20_08_5_STOP_SWITCH_NOT_PROVEN'
        Write-Output ('v20_08_5_'+$name+'=HALTED_NEW_ENTRIES_WORKER_UNTOUCHED')
    }
    return
}
if($mode -eq 'backup'){
    # Only consistent SQLite snapshots and stripped operational evidence.
    # Never back up DPAPI token files or H1/M15 source/state.
    need (Test-Path -LiteralPath $python -PathType Leaf) 'V20_08_5_PYTHON_MISSING'
    $destRoot=Join-Path $root 'backup-08'
    if(-not (Test-Path -LiteralPath $destRoot)){New-Item -ItemType Directory -Path $destRoot -Force | Out-Null}
    $stamp=([datetimeoffset]::UtcNow).ToString('yyyyMMddTHHmmssZ')
    $destination=Join-Path $destRoot ('v20-live-'+$stamp)
    need (-not (Test-Path -LiteralPath $destination)) 'V20_08_5_BACKUP_ALREADY_EXISTS'
    New-Item -ItemType Directory -Path $destination | Out-Null
    $code=@'
import json,sqlite3,sys
from pathlib import Path
source,target=sys.argv[1:]
src=Path(source);dst=Path(target)
if not src.is_file() or src.is_symlink() or dst.exists():
    raise SystemExit("V20_08_5_BACKUP_INVALID_PATH")
with sqlite3.connect(src.as_uri()+"?mode=ro",uri=True) as original:
    with sqlite3.connect(dst) as copy:
        original.backup(copy)
        if copy.execute("PRAGMA integrity_check").fetchone()!=("ok",):
            raise SystemExit("V20_08_5_BACKUP_INTEGRITY_FAIL")
        identity=copy.execute("SELECT value FROM state WHERE key='database_identity'").fetchone()
        if identity is None or not isinstance(json.loads(identity[0]),dict):
            raise SystemExit("V20_08_5_BACKUP_IDENTITY_FAIL")
print("V20_08_5_SQLITE_SNAPSHOT_PASS")
'@
    foreach($name in $selected){
        $sourceDb=Join-Path $root ('robots\'+$name.Substring(4)+'\state\v20-real-intents.sqlite3')
        $targetDb=Join-Path $destination ($name+'.sqlite3')
        & $python -B -c $code $sourceDb $targetDb
        need ($LASTEXITCODE -eq 0) 'V20_08_5_BACKUP_DB_FAILED'
        $sourceLog=Join-Path $root ('robots\'+$name.Substring(4)+'\logs\live-m15.jsonl')
        if(Test-Path -LiteralPath $sourceLog){Get-Content -LiteralPath $sourceLog -Tail 100 -Encoding UTF8 | Set-Content -LiteralPath (Join-Path $destination ($name+'-last100.jsonl')) -Encoding UTF8}
        $copySwitch=Join-Path $root ('robots\'+$name.Substring(4)+'\safety\stage8-trading-kill-switch.json')
        Copy-Item -LiteralPath $copySwitch -Destination (Join-Path $destination ($name+'-kill-switch.json'))
        Write-Output ('v20_08_5_'+$name+'_backup=PASS')
    }
    $metadata=@{schema='v20.08.5.backup.v1';date_utc=[datetimeoffset]::UtcNow.ToString('o');robots=$selected;source_commit=$source;dpapi_secrets_included=$false}
    [io.file]::WriteAllText((Join-Path $destination 'manifest.json'),($metadata|ConvertTo-Json -Depth 5),[text.utf8encoding]::new($false))
    Write-Output ('v20_08_5_backup=PASS path='+$destination)
    return
}
# START is a logical unpause or a checked restart of an already registered
# V20-only Task; no backup/secret/Task principal changes.
foreach($name in $selected){
    if($mode -eq 'restart'){
        # Restart only on a proven clean FINAM account: never abandon active
        # protection or forcibly kill an open-position managing worker.
        $w=@(call-launcher $name 'readonly')
        need (($w -join '|') -match 'v20_08_4_positions=0' -and
              ($w -join '|') -match 'v20_08_4_active_orders=0') 'V20_08_5_RESTART_REQUIRES_FINAM_FLAT'
        $stopped=@(call-launcher $name 'halt')
        need (($stopped -join '|') -match ('v20_08_4_switch=HALTED_'+$name)) 'V20_08_5_RESTART_HALT_FAIL'
        if((exact-task $name).State -eq 'Running'){
            Stop-ScheduledTask -TaskName $name -TaskPath '\' -ErrorAction Stop
            for($i=0;$i -lt 40 -and (exact-task $name).State -eq 'Running';$i++){Start-Sleep -Seconds 1}
        }
        need ((exact-task $name).State -ne 'Running') 'V20_08_5_RESTART_OLD_WORKER_ALIVE'
    }
    $task=exact-task $name
    if($task.State -eq 'Disabled'){Enable-ScheduledTask -TaskName $name -TaskPath '\' -ErrorAction Stop | Out-Null}
    $started=[datetimeoffset]::UtcNow
    if((exact-task $name).State -ne 'Running'){
        Start-ScheduledTask -TaskName $name -TaskPath '\' -ErrorAction Stop
        await-cycle $name $started
    }
    $up=@(call-launcher $name 'arm')
    need (($up -join '|') -match ('v20_08_4_switch=ARMED_'+$name+'_BROKER_CLEAN')) 'V20_08_5_START_ARM_FAIL'
    Write-Output ('v20_08_5_'+$name+'=PASS_RUNNING_ARMED')
}
