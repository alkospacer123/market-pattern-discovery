# V20-08.4: three V20 tasks in one operator window; H1/M15 tasks untouched.
# verify is offline. activate is explicit already-owner-approved LIVE mutation.
[CmdletBinding()]
param([ValidateSet('verify','activate','check','halt')][string]$mode='verify')
$ErrorActionPreference='Stop'
Set-StrictMode -Version Latest
$root='C:\V20Lab'
$stage=Join-Path $root 'pretrade-08\live-08'
$manifest=Join-Path $stage 'LIVE_PREPARED.json'
$launcher=Join-Path $stage 'v20-08-live-launch.ps1'
$source='dd55f201b3e9a92ce5fa3f927289f5a5ef89366d'
$names=@('v20-shallow','v20-obv','v20-inside')
function need([bool]$ok,[string]$fail){if(-not $ok){throw $fail}}
function sidof([string]$value){
    try{
        if($value -match '^S-[0-9]+(-[0-9]+)+$'){return ([Security.Principal.SecurityIdentifier]::new($value)).Value}
        return ([Security.Principal.NTAccount]::new($value)).Translate([Security.Principal.SecurityIdentifier]).Value
    }catch{return ''}
}
function expected([string]$name){
    return '-noprofile -noninteractive -executionpolicy bypass -file "'+$launcher+'" -mode run -robot '+$name
}
function boundtask([string]$name) {
    $task=Get-ScheduledTask -TaskName $name -TaskPath '\' -ErrorAction Stop
    need ((sidof ([string]$task.Principal.UserId)) -eq $sid -and
          @($task.Actions).Count -eq 1) 'V20_LIVE_TASK_PRINCIPAL_OR_ACTION_INVALID'
    return $task
}
function sourcecheck([string]$name){
    $result=@(& powershell.exe -noprofile -noninteractive -executionpolicy bypass -file $launcher -mode verify -robot $name 2>&1)
    need ($LASTEXITCODE -eq 0 -and
          (($result -join '|') -match ('v20_08_4_'+$name+'=PASS_VERIFY_NO_FINAM'))) 'V20_LIVE_SOURCE_AND_SID_VERIFY_FAILED'
}
function cycleproof([string]$name,[datetimeoffset]$after,[bool]$print=$false) {
    $task=boundtask $name
    $info=Get-ScheduledTaskInfo -TaskName $name -TaskPath '\' -ErrorAction Stop
    $log=Join-Path $root ('robots\'+$name.Substring(4)+'\logs\live-m15.jsonl')
    $latest=$null
    if(Test-Path -LiteralPath $log -PathType Leaf) {
        $lines=@(Get-Content -LiteralPath $log -Tail 10 -Encoding UTF8)
        for($i=$lines.Count-1;$i -ge 0;$i--){
            try{
                $item=$lines[$i] | ConvertFrom-Json -ErrorAction Stop
                if($item.robot -eq $name -and $item.utc -and $item.state) {
                    $at=[datetimeoffset]::Parse([string]$item.utc,[globalization.cultureinfo]::InvariantCulture)
                    $latest=@{utc=$at;state=[string]$item.state}
                    break
                }
            } catch {}
        }
    }
    if($print){
        Write-Output ('v20_08_4_'+$name+'_task='+$task.State)
        Write-Output ('v20_08_4_'+$name+'_last_result='+$info.LastTaskResult)
        Write-Output ('v20_08_4_'+$name+'_action='+$(if($task.Actions[0].Arguments -ieq (expected $name)){'V20_LIVE'}else{'UNEXPECTED'}))
        if($null -eq $latest){Write-Output ('v20_08_4_'+$name+'_last_cycle=MISSING')}
        else{
            Write-Output ('v20_08_4_'+$name+'_last_cycle='+$latest.state)
            Write-Output ('v20_08_4_'+$name+'_last_utc='+$latest.utc.ToString('o'))
        }
    }
    if($task.State -ne 'Running' -or
       $task.Actions[0].Arguments -ine (expected $name) -or
       $null -eq $latest -or $latest.state -match '^HALT' ){return $false}
    $utc=[datetimeoffset]::UtcNow
    $age=($utc-$latest.utc).TotalSeconds
    return ($latest.utc -ge $after.AddSeconds(-5) -and $age -ge -5 -and $age -le 90)
}
function observe([string]$name) {
    # Task Scheduler + fresh per-robot H1-style cycle is the authority.
    # WMI/CIM Python command-line enumeration can omit running child
    # processes and caused a false-negative despite broker cycle logs.
    $ok=cycleproof $name (([datetimeoffset]::UtcNow).AddSeconds(-90)) $true
    Write-Output ('v20_08_4_'+$name+'_healthy='+$ok)
}
function readonly([string]$name) {
    $result=@(& powershell.exe -noprofile -noninteractive -executionpolicy bypass -file $launcher -mode readonly -robot $name 2>&1)
    need ($LASTEXITCODE -eq 0 -and (($result -join '|') -match ('v20_08_4_readonly='+$name+' ACCOUNT_BOUND')) -and
          (($result -join '|') -match 'v20_08_4_order_posts=zero')) 'V20_LIVE_ACCOUNT_GET_ONLY_FAILED'
    return $result
}
function haltall {
    foreach($name in $names) {
        try{
            $result=@(& powershell.exe -noprofile -noninteractive -executionpolicy bypass -file $launcher -mode halt -robot $name 2>&1)
            Write-Output ('v20_08_4_'+$name+'_halt_exit='+$LASTEXITCODE)
        }catch{Write-Output ('v20_08_4_'+$name+'_halt=MANUAL_RECONCILIATION_REQUIRED')}
    }
}
need ($env:COMPUTERNAME -eq 'URIU-PC' -and $env:OS -eq 'Windows_NT') 'V20_LIVE_WRONG_INTEL'
need (Test-Path -LiteralPath $manifest -PathType Leaf) 'V20_LIVE_PREP_MANIFEST_MISSING'
need (Test-Path -LiteralPath $launcher -PathType Leaf) 'V20_LIVE_LAUNCHER_MISSING'
$receipt=Get-Content -LiteralPath $manifest -Raw -Encoding UTF8 | ConvertFrom-Json
$sid=[Security.Principal.WindowsIdentity]::GetCurrent().User.Value
need ($receipt.schema -eq 'v20.08.4.live_prepared.v1' -and
      $receipt.status -eq 'PASS_3_OF_3_OFFLINE_PREPARED' -and
      $receipt.source_commit -eq $source -and
      $receipt.owner_live_authorization_received -eq $true -and
      @($receipt.robots).Count -eq 3) 'V20_LIVE_PREP_NOT_ACCEPTED'
foreach($name in $names) {
    $row=@($receipt.robots | Where-Object {$_.robot -eq $name})
    need ($row.Count -eq 1) 'V20_LIVE_PREP_ROBOT_MISSING'
    [void](boundtask $name)
    sourcecheck $name
}
if($mode -eq 'verify'){
    Write-Output 'v20_08_4_cutover=READY_OFFLINE_3_OF_3'
    Write-Output 'v20_08_4_task_mutations=ZERO'
    Write-Output 'v20_08_4_finam=NO_NETWORK'
    return
}
if($mode -eq 'check'){
    foreach($name in $names){observe $name | Write-Output}
    return
}
if($mode -eq 'halt'){
    haltall
    Write-Output 'v20_08_4_halt=ATTEMPTED_3_OF_3_KEEP_BROKER_STOPS'
    return
}
# 'activate' (the already approved 08.4) is irreversible if a genuine frozen
# NEXT_OPEN signal occurs after the task is armed; broker orders are permitted.
foreach($name in $names){
    $task=boundtask $name
    $staged=($task.State -eq 'Disabled' -and
             $task.Actions[0].Arguments.Contains('v20-task-live-blocked.ps1'))
    $prepared=($task.State -in @('Disabled','Ready','Running') -and
               $task.Actions[0].Execute -ieq 'powershell.exe' -and
               $task.Actions[0].Arguments -ieq (expected $name) -and
               $task.Actions[0].WorkingDirectory -ieq (Join-Path $root ('robots\'+$name.Substring(4))))
    need ($staged -or $prepared) 'V20_LIVE_TASK_NOT_STAGED_OR_EXACT_PREPARED'
}
foreach($name in $names){
    $probe=@(readonly $name)
    need (($probe -join '|') -match 'v20_08_4_positions=0' -and
          ($probe -join '|') -match 'v20_08_4_active_orders=0') 'V20_LIVE_PRECUTOVER_BROKER_NOT_FLAT'
}
$mutated=@()
try {
    # Upgrade all actions while DISABLED. No task is enabled until all 3
    # prove exact principal, source, account-binding and long-running settings.
    foreach($name in $names){
        $dir=Join-Path $root ('robots\'+$name.Substring(4))
        $args=expected $name
        $before=boundtask $name
        if($before.Actions[0].Arguments.Contains('v20-task-live-blocked.ps1')){
            $action=New-ScheduledTaskAction -Execute 'powershell.exe' -Argument $args -WorkingDirectory $dir
            $settings=New-ScheduledTaskSettingsSet -MultipleInstances IgnoreNew -ExecutionTimeLimit ([timespan]::Zero) -RestartCount 3 -RestartInterval (New-TimeSpan -Minutes 1)
            Set-ScheduledTask -TaskName $name -TaskPath '\' -Action $action -Settings $settings -ErrorAction Stop | Out-Null
            Disable-ScheduledTask -TaskName $name -TaskPath '\' -ErrorAction Stop | Out-Null
            $mutated+= $name
        }
        $now=boundtask $name
        need ($now.Actions[0].Arguments -ieq $args -and
              $now.Actions[0].WorkingDirectory -ieq $dir) 'V20_LIVE_TASK_CUTOVER_VERIFICATION_FAILED'
    }
    foreach($name in $names){
        $task=boundtask $name
        if($task.State -eq 'Disabled'){
            Enable-ScheduledTask -TaskName $name -TaskPath '\' -ErrorAction Stop | Out-Null
        }
        $started=[datetimeoffset]::UtcNow
        if((boundtask $name).State -ne 'Running'){
            Start-ScheduledTask -TaskName $name -TaskPath '\' -ErrorAction Stop
        }else {
            # Already running from a previous partial cutover: require a fresh
            # current cycle rather than assert that starting a second was safe.
            $started=$started.AddSeconds(-90)
        }
        $proved=$false
        for($n=0;$n -lt 90;$n++){
            if(cycleproof $name $started){$proved=$true;break}
            Start-Sleep -Seconds 1
        }
        if(-not $proved){$health=cycleproof $name $started $true;Write-Output ('v20_08_4_'+$name+'_healthy='+$health)}
        need $proved 'V20_LIVE_RUNNING_TASK_WITH_FRESH_CYCLE_NOT_CONFIRMED'
        $output=@(& powershell.exe -noprofile -noninteractive -executionpolicy bypass -file $launcher -mode arm -robot $name 2>&1)
        need ($LASTEXITCODE -eq 0 -and
              (($output -join '|') -match ('v20_08_4_switch=ARMED_'+$name+'_BROKER_CLEAN'))) 'V20_LIVE_ARM_BROKER_PROOF_FAILED'
        Write-Output ('v20_08_4_'+$name+'=PASS_TASK_RUNNING_FRESH_CYCLE_ACCOUNT_BOUND_ARMED')
    }
    # Final 3/3 check within the same operator window, not just after each
    # sequential start. Recheck the first and second processes as well.
    foreach($name in $names) {
        need (cycleproof $name (([datetimeoffset]::UtcNow).AddSeconds(-90))) 'V20_LIVE_FINAL_THREE_TASK_CYCLE_PROOF_FAILED'
        $probe=@(readonly $name)
        need (($probe -join '|') -match 'v20_08_4_order_posts=zero') 'V20_LIVE_FINAL_FINAM_GET_FAILED'
    }
    Write-Output 'v20_08_4_live=PASS_ACTIVATED_3_OF_3_TASKS_FRESH_CYCLES_AND_FINAM_READONLY'
} catch {
    # Preserve all broker stops. Existing live processes continue tracking
    # exits while all new entries are halted; never cancel SLTP on failure.
    haltall
    Write-Output 'v20_08_4_activation=HOLD_NO_NEW_ENTRIES_KEEP_BROKER_PROTECTION'
    throw
}
