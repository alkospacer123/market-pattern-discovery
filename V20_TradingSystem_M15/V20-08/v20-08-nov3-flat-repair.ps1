# V20 2026-11-03 — FLAT-only combined WATCHING stop + GO risk fix.
# No trading calls, no ARM. Stop/restart ONLY V20 Windows Tasks; keep switches HALTED.
# No modifications or restarts of TradingSystemLab H1, IntradayLab M15, Control Center.
[CmdletBinding()]
param([ValidateSet('verify','install')][string]$mode='verify')
$ErrorActionPreference='Stop'
Set-StrictMode -Version Latest
$root='C:\V20Lab'
$names=@('v20-shallow','v20-obv','v20-inside')
$stage=Join-Path $root 'pretrade-08\live-08'
$launcher=Join-Path $stage 'v20-08-live-launch.ps1'
$operator=Join-Path $stage 'v20-08-live-operator.ps1'
$live=Join-Path $root 'pretrade-08\live-runtime-08\V20_TradingSystem_M15\v20_runtime'
$execution=Join-Path $live 'finam_execution.py'
$worker=Join-Path $live 'finam_live.py'
$python=Join-Path $root '.venv-raw\scripts\python.exe'
$oldExec='4ea5cec17a31413c96531dd4f80f77e2a96f3f00'
$newExec='c7e62495fcc64d613693174492659f62df5c0af1'
$oldWorker='2a1814a5aecb2a586e839b14f20076a98de0c1e0'
$newWorker='c4c576189510a847ce20c43f5bb39d0e517eb0b4'
$oldLauncher='3beac63e0e8985485bb43bb1627aabc96fbd107a'
$newLauncher='2b47dab60c5494e8265d3ba1aed57a550f0d4ed7'
$operatorBlob='b06957ea7833daeda65296eb372890951860c008'
function need([bool]$ok,[string]$code){if(-not $ok){throw $code}}
function hash([string]$p){
    need (Test-Path -LiteralPath $p -PathType Leaf) 'V20_NOV3_REQUIRED_FILE_MISSING'
    need (-not ((Get-Item -LiteralPath $p -Force).Attributes -band [io.fileattributes]::ReparsePoint)) 'V20_NOV3_REPARSE_FORBIDDEN'
    $got=(& git.exe hash-object -- $p).Trim().ToLowerInvariant()
    need ($LASTEXITCODE -eq 0) 'V20_NOV3_GIT_HASH_FAILED'
    return $got
}
function task([string]$name){
    $t=Get-ScheduledTask -TaskName $name -TaskPath '\' -ErrorAction Stop
    $action=@($t.Actions)
    $expected='-noprofile -noninteractive -executionpolicy bypass -file "'+$launcher+'" -mode run -robot '+$name
    $dir=Join-Path $root ('robots\'+$name.Substring(4))
    $sid=[Security.Principal.WindowsIdentity]::GetCurrent().User.Value
    $owner=[string]$t.Principal.UserId
    try {
        $principalSid=if($owner -match '^S-[0-9]+(-[0-9]+)+$'){$owner}else{([Security.Principal.NTAccount]::new($owner)).Translate([Security.Principal.SecurityIdentifier]).Value}
    }catch{$principalSid=''}
    need ($action.Count -eq 1 -and $action[0].Execute -ieq 'powershell.exe' -and
          $action[0].Arguments -ieq $expected -and
          $action[0].WorkingDirectory -ieq $dir -and
          $principalSid -eq $sid) ('V20_NOV3_TASK_IDENTITY_MISMATCH_'+$name)
    return $t
}
function halted([string]$name){
    $file=Join-Path $root ('robots\'+$name.Substring(4)+'\safety\stage8-trading-kill-switch.json')
    need (Test-Path -LiteralPath $file -PathType Leaf) ('V20_NOV3_SWITCH_MISSING_'+$name)
    $state=Get-Content -LiteralPath $file -Raw -Encoding UTF8 | ConvertFrom-Json
    need ($state.state -eq 'HALTED') ('V20_NOV3_SWITCH_NOT_HALTED_'+$name)
}
function flat([string]$name){
    $result=@(& powershell.exe -noprofile -noninteractive -executionpolicy bypass -file $launcher -mode readonly -robot $name 2>&1)
    need ($LASTEXITCODE -eq 0 -and
          ($result -join '|') -match ('v20_08_4_readonly='+$name+' ACCOUNT_BOUND') -and
          ($result -join '|') -match 'v20_08_4_positions=0' -and
          ($result -join '|') -match 'v20_08_4_active_orders=0' -and
          ($result -join '|') -match 'v20_08_4_order_posts=zero') ('V20_NOV3_FINAM_NOT_FLAT_'+$name)
    Write-Output ('v20_nov3_'+$name+'_finam=PASS_GET_ONLY_FLAT')
}
function workers(){
    $processes=@(Get-CimInstance Win32_Process -Filter "Name='python.exe' OR Name='pythonw.exe'" -ErrorAction Stop)
    return @($processes | Where-Object {$_.CommandLine -and
        $_.CommandLine -match 'V20_TradingSystem_M15[.]v20_runtime[.]finam_live' -and
        $_.CommandLine -match '--robot\s+v20-(shallow|obv|inside)'})
}
function prefetch([string]$path,[string]$new){
    # Download while all V20 processes still run HALTED: network failure
    # must not stop the already-running existing-position management.
    $temp=$path+'.v20-nov3-download'
    if(Test-Path -LiteralPath $temp){
        need ((hash $temp) -eq $new) 'V20_NOV3_STAGED_BLOB_CONFLICT'
        return
    }
    $blob=Invoke-RestMethod -Uri ('https://api.github.com/repos/alkospacer123/market-pattern-discovery/git/blobs/'+$new) -Headers @{'user-agent'='v20lab'} -ErrorAction Stop
    need ($blob.sha -eq $new -and $blob.encoding -eq 'base64') 'V20_NOV3_REMOTE_BLOB_MISMATCH'
    [IO.File]::WriteAllBytes($temp,[convert]::FromBase64String($blob.content))
    need ((hash $temp) -eq $new) 'V20_NOV3_DOWNLOADED_HASH_MISMATCH'
}
function patch([string]$path,[string]$old,[string]$new){
    need ((hash $path) -eq $old) 'V20_NOV3_CURRENT_BLOB_CHANGED'
    $temp=$path+'.v20-nov3-download'
    need ((hash $temp) -eq $new) 'V20_NOV3_STAGED_BLOB_MISMATCH'
    Move-Item -LiteralPath $temp -Destination $path -Force -ErrorAction Stop
    need ((hash $path) -eq $new) 'V20_NOV3_INSTALLED_HASH_MISMATCH'
}
need ($env:OS -eq 'Windows_NT' -and $env:COMPUTERNAME -ceq 'URIU-PC') 'V20_NOV3_WRONG_HOST'
need ((Test-Path -LiteralPath $python -PathType Leaf) -and
      (hash $operator) -eq $operatorBlob) 'V20_NOV3_OPERATOR_NOT_ACCEPTED'
$actualExec=hash $execution;$actualWorker=hash $worker;$actualLauncher=hash $launcher
$oldSet=(($actualLauncher -eq $oldLauncher -and $actualExec -eq $oldExec -and $actualWorker -eq $oldWorker) -or
         ($actualLauncher -eq '8e7ff959901d42e89755f5ba2f80563d2745bab5' -and
          $actualExec -eq '4a362059691bf2e902b2be11d4ff365788d76ae6' -and
          $actualWorker -eq 'bd1858ad63de00bd6b142f5678848ed6d83e63e9'))
$newSet=($actualLauncher -eq $newLauncher -and $actualExec -eq $newExec -and $actualWorker -eq $newWorker)
need ($oldSet -or $newSet) 'V20_NOV3_MIXED_OR_UNRECOGNIZED_INSTALLED_RELEASE'
if($oldSet){$oldExec=$actualExec;$oldWorker=$actualWorker;$oldLauncher=$actualLauncher}
foreach($name in $names){
    halted $name
    $t=task $name
    need ($t.State -in @('Running','Ready')) ('V20_NOV3_TASK_STATE_UNKNOWN_'+$name)
}
Write-Output 'v20_nov3_scope=PASS_V20_ONLY_H1_AND_M15_UNTOUCHED'
Write-Output 'v20_nov3_switches=PASS_HALTED_3_OF_3'
foreach($name in $names){flat $name}
if($mode -eq 'verify'){
    Write-Output ('v20_nov3_verify=PASS_3_OF_3_FLAT_'+$(if($oldSet){'OLD_PINNED_RELEASE'}else{'NEW_PINNED_RELEASE'}))
    Write-Output 'v20_nov3_no_changes=YES'
    return
}
if($newSet){
    Write-Output 'v20_nov3_install=ALREADY_PINNED_NEW_RELEASE_NO_TASK_MUTATION'
    return
}
# Critical: consistent online SQLite snapshots BEFORE stopping any V20 worker.
$back=@(& powershell.exe -noprofile -noninteractive -executionpolicy bypass -file $operator -mode backup -robot all 2>&1)
$back | Write-Output
need ($LASTEXITCODE -eq 0 -and ($back -join '|') -match 'v20_08_5_backup=PASS path=') 'V20_NOV3_PREBACKUP_FAILED'
Write-Output 'v20_nov3_prebackup=PASS_3_OF_3_SQLITE'
prefetch $execution $newExec
prefetch $worker $newWorker
prefetch $launcher $newLauncher
Write-Output 'v20_nov3_new_blobs=PASS_3_OF_3_STAGED_BEFORE_TASK_STOP'
foreach($name in $names){halted $name;flat $name}
# Keep the three kill switches HALTED while stopping ONLY their own Tasks.
foreach($name in $names){
    $t=task $name
    if($t.State -eq 'Running'){Stop-ScheduledTask -TaskName $name -TaskPath '\' -ErrorAction Stop}
}
$stopped=$false
for($i=0;$i -lt 40;$i++){
    $pending=@($names | Where-Object {(task $_).State -eq 'Running'})
    $remaining=@(workers)
    if($pending.Count -eq 0 -and $remaining.Count -eq 0){$stopped=$true;break}
    Start-Sleep -Seconds 1
}
need $stopped 'V20_NOV3_OLD_WORKER_REMAINS_DO_NOT_START_DUPLICATE'
foreach($name in $names){halted $name}
# Store rollback-safe copies of old V20 code (not token files).
$archive=Join-Path $root ('backup-08\v20-code-before-nov3-repair-'+([datetimeoffset]::UtcNow).ToString('yyyyMMddTHHmmssZ'))
New-Item -ItemType Directory -Path $archive -ErrorAction Stop | Out-Null
Copy-Item -LiteralPath $execution -Destination (Join-Path $archive 'finam_execution.py') -ErrorAction Stop
Copy-Item -LiteralPath $worker -Destination (Join-Path $archive 'finam_live.py') -ErrorAction Stop
Copy-Item -LiteralPath $launcher -Destination (Join-Path $archive 'v20-08-live-launch.ps1') -ErrorAction Stop
patch $execution $oldExec $newExec
patch $worker $oldWorker $newWorker
patch $launcher $oldLauncher $newLauncher
Write-Output 'v20_nov3_blobs=PASS_3_OF_3_H1_PARITY_PINNED'
foreach($source in @($execution,$worker)){
    & $python -B -m ast $source | Out-Null
    need ($LASTEXITCODE -eq 0) 'V20_NOV3_PYTHON_SYNTAX_FAILED'
}
$tokens=$null;$errs=$null
[void][Management.Automation.Language.Parser]::ParseFile($launcher,[ref]$tokens,[ref]$errs)
need (@($errs).Count -eq 0) 'V20_NOV3_LAUNCHER_SYNTAX_FAILED'
foreach($name in $names){
    $result=@(& powershell.exe -noprofile -noninteractive -executionpolicy bypass -file $launcher -mode verify -robot $name 2>&1)
    need ($LASTEXITCODE -eq 0 -and ($result -join '|') -match ('v20_08_4_'+$name+'=PASS_VERIFY_NO_FINAM')) ('V20_NOV3_PINNED_VERIFY_FAILED_'+$name)
}
Write-Output 'v20_nov3_launcher=PASS_3_OF_3_PINNED_NO_NETWORK'
# Revalidate FINAM FLAT with NEW release; if any broker difference, keep tasks stopped.
foreach($name in $names){halted $name;flat $name}
foreach($name in $names){
    need ((task $name).State -eq 'Ready') ('V20_NOV3_TASK_NOT_READY_'+$name)
    Start-ScheduledTask -TaskName $name -TaskPath '\' -ErrorAction Stop
}
$fresh=@{}
$started=[datetimeoffset]::UtcNow
for($i=0;$i -lt 80;$i++){
    foreach($name in $names){
        if($fresh.ContainsKey($name)){continue}
        $t=task $name
        $log=Join-Path $root ('robots\'+$name.Substring(4)+'\logs\live-m15.jsonl')
        if($t.State -ne 'Running' -or -not (Test-Path -LiteralPath $log)){continue}
        try{
            $row=Get-Content -LiteralPath $log -Tail 1 -Encoding UTF8 | ConvertFrom-Json
            $utc=[datetimeoffset]::Parse([string]$row.utc)
            if($row.robot -eq $name -and $utc -ge $started.AddSeconds(-5) -and
               $row.state -eq 'HALTED_NO_NEW_ENTRIES'){$fresh[$name]=$utc}
        }catch{}
    }
    if($fresh.Count -eq 3){break}
    Start-Sleep -Seconds 1
}
need ($fresh.Count -eq 3) 'V20_NOV3_FRESH_HALTED_CYCLE_MISSING_CHECK_LOGS_NO_ARM'
foreach($name in $names){
    halted $name
    flat $name
    Write-Output ('v20_nov3_'+$name+'=PASS_RUNNING_HALTED_FRESH_NO_NEW_ENTRIES')
}
Write-Output 'v20_nov3_install=PASS_3_OF_3_NEW_H1_PARITY_RELEASE_RUNNING_HALTED_FINAM_FLAT'
Write-Output 'v20_nov3_auto_arm=NO'
