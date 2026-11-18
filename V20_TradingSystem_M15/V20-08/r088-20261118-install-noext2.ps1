# R088 NOEXT2: cutover on confirmed-flat, HALTED V20 only.
# Sources are the physically staged SHA-pinned 7-patch release. NO AUTO ARM.
[CmdletBinding()]
param(
 [ValidateSet('install','rollback')][string]$mode='install',
 [string]$rollback_dir=''
)
$ErrorActionPreference='Stop'
Set-StrictMode -Version Latest
$root='c:\v20lab'
$names=@('v20-shallow','v20-obv','v20-inside')
$launcher=Join-Path $root 'pretrade-08\live-08\v20-08-live-launch.ps1'
$runtime=Join-Path $root 'pretrade-08\live-runtime-08\V20_TradingSystem_M15\v20_runtime'
$stage=Join-Path $root 'r088-candidate\release-20261118-tp6-protect3-hold5-noext2\staged\V20_TradingSystem_M15\v20_runtime'
$zip=Join-Path $root 'r088-candidate\release-20261118-tp6-protect3-hold5-noext2.zip'
$backRoot=Join-Path $root 'backup-08'
$python=Join-Path $root '.venv-raw\scripts\python.exe'
$prepared=Join-Path $root 'pretrade-08\live-08\LIVE_PREPARED.json'
$receipt=Join-Path $root 'pretrade-08\DPAPI_TRADING_BINDINGS_REPORT.json'
$source='dd55f201b3e9a92ce5fa3f927289f5a5ef89366d'
$oldLauncher='4e7498d2eacf0930d0ee1bbf6343883735f3aefb'
$zipSha='d2e9240f9721039d7229aaad82a42ccb938d8548ed7c0100115ead579d6c23ca'
$oldLive='b80fb9eb135f7cdcb4c78337e2b808c4d7135195'
$oldExec='6b600451178b42bd4f8b2037995e7db3a9ad27c8'
$newLive='54ae8e1262482f4ecc80d202c6e9063cf0d6e402'
$newExec='0fc4c454d55f37e4e87fd74e3370cbc1ad83b53f'
$modules=[ordered]@{
 'finam_live.py'=$newLive
 'finam_execution.py'=$newExec
 'tp6_protect3.py'='a578cac629350f2c9fe3409121ac085c8a41eb63'
 'r070_linked_sltp.py'='864d03d8fe467138adf73c6e6216a88fc81e8c21'
 'r088_hold5.py'='f0b9058707230299464f1f6fb5245653a022ec31'
}
function need([bool]$ok,[string]$code){if(-not $ok){throw $code}}
function pin([string]$path,[string]$expected){
 need (Test-Path -LiteralPath $path -PathType Leaf) ('R088_MISSING_'+$path)
 need (-not ((Get-Item -LiteralPath $path -Force).Attributes -band [io.fileattributes]::ReparsePoint)) 'R088_LINK_NOT_ALLOWED'
 $actual=(& git.exe hash-object -- $path).Trim().ToLowerInvariant()
 need ($LASTEXITCODE -eq 0 -and $actual -ceq $expected) ('R088_SHA_MISMATCH_'+$path)
}
function switch-halted(){
 foreach($name in $names) {
   $state=Join-Path $root ('robots\'+$name.Substring(4)+'\safety\stage8-trading-kill-switch.json')
   need (Test-Path -LiteralPath $state -PathType Leaf) 'R088_KILLSWITCH_MISSING'
   $v=Get-Content -LiteralPath $state -Raw -Encoding UTF8 | ConvertFrom-Json
   need ($v.state -eq 'HALTED') ('R088_SWITCH_NOT_HALTED_'+$name)
 }
}
function exact-tasks(){
 $sid=[security.principal.windowsidentity]::GetCurrent().User.Value
 foreach($name in $names) {
  $task=Get-ScheduledTask -TaskName $name -TaskPath '\' -ErrorAction Stop
  $expected='-noprofile -noninteractive -executionpolicy bypass -file "'+$launcher+'" -mode run -robot '+$name
  $dir=Join-Path $root ('robots\'+$name.Substring(4))
  need (@($task.Actions).Count -eq 1 -and $task.Actions[0].Execute -ieq 'powershell.exe' -and
   $task.Actions[0].Arguments -ieq $expected -and $task.Actions[0].WorkingDirectory -ieq $dir) ('R088_TASK_ACTION_CHANGED_'+$name)
  $principal=[security.principal.ntaccount]::new([string]$task.Principal.UserId)
  try{$prSid=$principal.Translate([security.principal.securityidentifier]).Value}
  catch{$prSid=[string]$task.Principal.UserId}
  need ($prSid -eq $sid) ('R088_TASK_SID_CHANGED_'+$name)
 }
}
function stop-tasks(){
 foreach($name in $names){
  $task=Get-ScheduledTask -TaskName $name -TaskPath '\' -ErrorAction Stop
  if($task.State -eq 'Running'){Stop-ScheduledTask -TaskName $name -TaskPath '\' -ErrorAction Stop}
 }
 for($k=0;$k -lt 30;$k++){
  $still=@($names | Where-Object {(Get-ScheduledTask -TaskName $_ -TaskPath '\').State -eq 'Running'})
  if($still.Count -eq 0){break}
  Start-Sleep -Seconds 1
 }
 need (@($names | Where-Object {(Get-ScheduledTask -TaskName $_ -TaskPath '\').State -eq 'Running'}).Count -eq 0) 'R088_TASKS_NOT_QUIESCENT'
 $worker=@(Get-CimInstance Win32_Process -Filter "Name='python.exe'" | Where-Object {
  $_.CommandLine -match 'V20_TradingSystem_M15.v20_runtime.finam_live' -and
  $_.CommandLine -match 'v20-(?:shallow|obv|inside)'
 })
 need ($worker.Count -eq 0) 'R088_OLD_WORKER_STILL_ALIVE'
}
function start-tasks(){
 foreach($name in $names){Start-ScheduledTask -TaskName $name -TaskPath '\' -ErrorAction Stop}
 for($k=0;$k -lt 30;$k++){
  if(@($names | Where-Object {(Get-ScheduledTask -TaskName $_ -TaskPath '\').State -ne 'Running'}).Count -eq 0){break}
  Start-Sleep -Seconds 1
 }
 need (@($names | Where-Object {(Get-ScheduledTask -TaskName $_ -TaskPath '\').State -ne 'Running'}).Count -eq 0) 'R088_RESTARTED_TASK_NOT_RUNNING'
}
function broker-flat(){
 foreach($name in $names){
  $output=@(& powershell.exe -noprofile -noninteractive -executionpolicy bypass -file $launcher -mode readonly -robot $name 2>&1)
  need ($LASTEXITCODE -eq 0 -and ($output -join '|') -match 'v20_08_4_positions=0' -and
   ($output -join '|') -match 'v20_08_4_active_orders=0' -and
   ($output -join '|') -match 'v20_08_4_order_posts=zero') ('R088_BROKER_NOT_PROVEN_FLAT_'+$name)
  Write-Output ('R088_FINAM_FLAT_'+$name+'=PASS_GET_ONLY')
 }
}
$helper=@'
import json,sqlite3,sys
path,robot,account_hash,source,operation=sys.argv[1:]
key="r070_protect3_release_authorization"
expected={"schema":"r070.protect3.live_approval.v1","source_commit":source,"robot":robot,"account_sha256":account_hash,"owner_approved":True}
db=sqlite3.connect(path,timeout=3)
try:
    db.execute("BEGIN IMMEDIATE")
    row=db.execute("SELECT value FROM state WHERE key='database_identity'").fetchone()
    identity=json.loads(row[0]) if row else None
    if not isinstance(identity,dict) or identity.get("robot_id")!=robot or identity.get("account_sha256")!=account_hash or identity.get("schema_id")!="v20.h1_state_store.real_intents.v1":
        raise RuntimeError("R088_REAL_SQLITE_ACCOUNT_IDENTITY_INVALID")
    row=db.execute("SELECT value FROM state WHERE key=?",(key,)).fetchone()
    if operation=="grant":
        if row is not None:
            raise RuntimeError("R088_RELEASE_APPROVAL_ALREADY_EXISTS")
        db.execute("INSERT INTO state (key,value) VALUES (?,?)",(key,json.dumps(expected,sort_keys=True,separators=(",",":"))))
    elif operation=="revoke":
        # Idempotent rollback after an interrupted install that may have
        # authorized only a subset of the three independent accounts.
        if row:
            if json.loads(row[0])!=expected:
                raise RuntimeError("R088_RELEASE_APPROVAL_NOT_OWNED")
            db.execute("DELETE FROM state WHERE key=?",(key,))
    else:
        raise RuntimeError("R088_SQLITE_OPERATION_INVALID")
    db.commit()
    print("R088_PROTECT3_"+operation.upper()+"_"+robot+"=PASS")
except:
    db.rollback()
    raise
finally:
    db.close()
'@
function approve([string]$action,[string]$dir){
 $helperPath=Join-Path $dir 'r088-protect3-approval.py'
 foreach($name in $names){
  $record=Get-Content -LiteralPath $receipt -Raw -Encoding UTF8 | ConvertFrom-Json
  $match=@($record.robots | Where-Object {$_.robot -eq $name})
  need ($match.Count -eq 1 -and [string]$match[0].account_sha256 -match '^[a-f0-9]{64}$') ('R088_ACCOUNT_RECEIPT_INVALID_'+$name)
  $db=Join-Path $root ('robots\'+$name.Substring(4)+'\state\v20-real-intents.sqlite3')
  & $python -B $helperPath $db $name ([string]$match[0].account_sha256) $source $action
  need ($LASTEXITCODE -eq 0) ('R088_APPROVAL_'+$action+'_FAILED_'+$name)
 }
}
need ($env:OS -eq 'Windows_NT' -and $env:COMPUTERNAME -eq 'URIU-PC') 'R088_INTEL_ONLY'
switch-halted
exact-tasks
need (Test-Path -LiteralPath $python -PathType Leaf) 'R088_PYTHON_MISSING'
need (Test-Path -LiteralPath $prepared -PathType Leaf) 'R088_PREPARED_MISSING'
need (Test-Path -LiteralPath $receipt -PathType Leaf) 'R088_DPAPI_BINDINGS_MISSING'
$prep=Get-Content -LiteralPath $prepared -Raw -Encoding UTF8 | ConvertFrom-Json
$identity=Get-Content -LiteralPath $receipt -Raw -Encoding UTF8 | ConvertFrom-Json
need ($prep.source_commit -eq $source -and $prep.status -eq 'PASS_3_OF_3_OFFLINE_PREPARED' -and
 $identity.status -eq 'PASS_3_OF_3_DPAPI_LIVE_OFF' -and
 $identity.principal_sid -eq [security.principal.windowsidentity]::GetCurrent().User.Value) 'R088_CURRENT_AUTH_NOT_PINNED'
if($mode -eq 'rollback'){
 need ($rollback_dir -ne '' -and (Test-Path -LiteralPath $rollback_dir -PathType Container)) 'R088_ROLLBACK_DIR_REQUIRED'
 $backup=(Resolve-Path -LiteralPath $rollback_dir).Path
 need ($backup.StartsWith((Join-Path $backRoot 'r088-noext2-cutover-'),[StringComparison]::OrdinalIgnoreCase)) 'R088_ROLLBACK_SCOPE_INVALID'
 $record=Get-Content -LiteralPath (Join-Path $backup 'release-manifest.json') -Raw | ConvertFrom-Json
 need ($record.schema -eq 'v20.r088.noext2.cutover.v1') 'R088_ROLLBACK_MANIFEST_INVALID'
 pin (Join-Path $backup 'v20-08-live-launch.ps1') $oldLauncher
 pin (Join-Path $runtime 'finam_live.py') $newLive
 pin (Join-Path $runtime 'finam_execution.py') $newExec
 broker-flat
 stop-tasks
 Copy-Item -LiteralPath (Join-Path $backup 'v20-08-live-launch.ps1') -Destination $launcher -Force
 foreach($name in @($modules.Keys)){
  $target=Join-Path $runtime $name
  $prior=Join-Path $backup $name
  if(Test-Path -LiteralPath $prior){Copy-Item -LiteralPath $prior -Destination $target -Force}
  elseif(Test-Path -LiteralPath $target){Remove-Item -LiteralPath $target -Force}
 }
 approve 'revoke' $backup
 pin (Join-Path $runtime 'finam_live.py') $oldLive
 pin (Join-Path $runtime 'finam_execution.py') $oldExec
 foreach($name in $names){& powershell.exe -noprofile -noninteractive -executionpolicy bypass -file $launcher -mode verify -robot $name;need ($LASTEXITCODE -eq 0) 'R088_ROLLBACK_LAUNCHER_VERIFY_FAILED'}
 start-tasks
 switch-halted
 Write-Output 'R088_ROLLBACK=PASS_ORIGINAL_CODE_RUNNING_HALTED_NO_REARM'
 return
}
pin $launcher $oldLauncher
pin (Join-Path $runtime 'finam_live.py') $oldLive
pin (Join-Path $runtime 'finam_execution.py') $oldExec
need ((Get-FileHash -LiteralPath $zip -Algorithm SHA256).Hash.ToLowerInvariant() -ceq $zipSha) 'R088_RELEASE_ZIP_SHA_MISMATCH'
foreach($name in @($modules.Keys)){pin (Join-Path $stage $name) $modules[$name]}
$oldText=[io.file]::ReadAllText($launcher)
need (([regex]::Matches($oldText,[regex]::Escape("'$oldLive'"))).Count -eq 1 -and
 ([regex]::Matches($oldText,[regex]::Escape("'$oldExec'"))).Count -eq 1) 'R088_LAUNCHER_PIN_TEMPLATE_CHANGED'
foreach($name in $names){need ((Get-ScheduledTask -TaskName $name -TaskPath '\').State -eq 'Running') 'R088_PRECHECK_TASK_NOT_RUNNING'}
broker-flat
$backup=Join-Path $backRoot ('r088-noext2-cutover-'+([datetimeoffset]::UtcNow).ToString('yyyyMMddTHHmmssZ'))
need (-not (Test-Path -LiteralPath $backup)) 'R088_BACKUP_EXISTS'
[io.directory]::CreateDirectory($backup)|Out-Null
Copy-Item -LiteralPath $launcher -Destination (Join-Path $backup 'v20-08-live-launch.ps1')
foreach($name in @($modules.Keys)){
 $current=Join-Path $runtime $name
 if(Test-Path -LiteralPath $current){Copy-Item -LiteralPath $current -Destination (Join-Path $backup $name)}
}
[io.file]::WriteAllText((Join-Path $backup 'r088-protect3-approval.py'),$helper,[text.utf8encoding]::new($false))
$manifest=[ordered]@{schema='v20.r088.noext2.cutover.v1';status='BACKUP_BEFORE_INSTALL';package_sha256=$zipSha;operator_backup='v20-live-20261118T184141Z';source_commit=$source;original_launcher_git_sha=$oldLauncher;original_live_git_sha=$oldLive;original_execution_git_sha=$oldExec;target_live_git_sha=$newLive;target_execution_git_sha=$newExec;robot_names=$names;armed=$false}
[io.file]::WriteAllText((Join-Path $backup 'release-manifest.json'),($manifest|ConvertTo-Json -Depth 5),[text.utf8encoding]::new($false))
Write-Output ('R088_ROLLBACK_DIR='+$backup)
# Never replace modules in a running process.
try {
 stop-tasks
 foreach($name in @($modules.Keys)){
   Copy-Item -LiteralPath (Join-Path $stage $name) -Destination (Join-Path $runtime $name) -Force
   pin (Join-Path $runtime $name) $modules[$name]
 }
 $newText=$oldText.Replace("'$oldLive'","'$newLive'").Replace("'$oldExec'","'$newExec'")
 [io.file]::WriteAllText($launcher,$newText,[text.utf8encoding]::new($false))
 approve 'grant' $backup
 foreach($name in $names){
  & powershell.exe -noprofile -noninteractive -executionpolicy bypass -file $launcher -mode verify -robot $name
  need ($LASTEXITCODE -eq 0) ('R088_NEW_LAUNCHER_VERIFY_FAILED_'+$name)
 }
 start-tasks
 switch-halted
 Write-Output 'R088_NOEXT2_INSTALL=PASS_3_RUNNING_HALTED'
 Write-Output 'R088_TP6_PROTECT3_RELEASE_AUTHORIZED_3_OF_3=YES'
 Write-Output 'R088_NO_NEW_ENTRIES_NO_REARM=YES'
 Write-Output ('R088_ROLLBACK_DIR='+$backup)
} catch {
 $problem=$_.Exception.Message
 Write-Output ('R088_INSTALL_HOLD='+$problem)
 # A partial copy or approval failure must not strand an unprotected half
 # release. All tasks are HALTED and the broker was proven FLAT above.
 try {
  stop-tasks
  Copy-Item -LiteralPath (Join-Path $backup 'v20-08-live-launch.ps1') -Destination $launcher -Force
  foreach($name in @($modules.Keys)){
   $target=Join-Path $runtime $name
   $prior=Join-Path $backup $name
   if(Test-Path -LiteralPath $prior){Copy-Item -LiteralPath $prior -Destination $target -Force}
   elseif(Test-Path -LiteralPath $target){Remove-Item -LiteralPath $target -Force}
  }
  approve 'revoke' $backup
  pin $launcher $oldLauncher
  pin (Join-Path $runtime 'finam_live.py') $oldLive
  pin (Join-Path $runtime 'finam_execution.py') $oldExec
  foreach($name in $names){
    & powershell.exe -noprofile -noninteractive -executionpolicy bypass -file $launcher -mode verify -robot $name
    need ($LASTEXITCODE -eq 0) ('R088_AUTO_ROLLBACK_VERIFY_FAILED_'+$name)
  }
  start-tasks
  switch-halted
  Write-Output 'R088_INSTALL_FAILED_AUTO_ROLLBACK=PASS_ORIGINAL_RUNNING_HALTED'
 } catch {
  Write-Output ('R088_AUTO_ROLLBACK_HOLD='+$_.Exception.Message)
  Write-Output 'R088_TASKS_MAY_BE_STOPPED_MANUAL_RECOVERY_REQUIRED=YES'
 }
 Write-Output ('R088_ROLLBACK_DIR='+$backup)
 Write-Output 'R088_DO_NOT_ARM_OR_RETRY_BLINDLY=YES'
 throw
}
