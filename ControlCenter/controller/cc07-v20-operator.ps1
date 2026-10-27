# CC-07 independent Windows operator: NEVER import or launch from Streamlit.
# Staged source only. No production installation/ARM without separate acceptance.
[CmdletBinding()]
param(
 [ValidateSet('preview','execute')][string]$mode='preview',
 [ValidateSet('v20-shallow','v20-obv','v20-inside')][string]$robot='v20-shallow',
 [ValidateSet('start','pause','stop','restart')][string]$action='pause',
 [string]$requestid=''
)
$ErrorActionPreference='Stop'
Set-StrictMode -Version Latest
$operator='c:\v20lab\pretrade-08\live-08\v20-08-live-operator.ps1'
$launcher='c:\v20lab\pretrade-08\live-08\v20-08-live-launch.ps1'
$audit='c:\control center\data\control-audit'
$release='c:\control center\data\private\cc07-v20-release.json'
function need([bool]$ok,[string]$code){if(-not $ok){throw $code}}
function pin([string]$path,[string]$sha){
 need (test-path -literalpath $path -pathtype leaf) 'cc07_script_missing'
 need (-not [bool]((get-item -literalpath $path -force).attributes -band [io.fileattributes]::reparsepoint)) 'cc07_script_reparse'
 $hash=(& git.exe hash-object -- $path).trim()
 need ($lastexitcode -eq 0 -and $hash -ceq $sha) 'cc07_script_hash_mismatch'
}
function trusted([string]$path){
 need (test-path -literalpath $path) 'cc07_trusted_path_missing'
 need (-not [bool]((get-item -literalpath $path -force).attributes -band [io.fileattributes]::reparsepoint)) 'cc07_reparse_forbidden'
 $acl=get-acl -literalpath $path
 need ($acl.getowner([security.principal.securityidentifier]).value -in @('S-1-5-18','S-1-5-32-544')) 'cc07_owner_untrusted'
 $w=[int64][security.accesscontrol.filesystemrights]::write -bor [int64][security.accesscontrol.filesystemrights]::delete -bor [int64][security.accesscontrol.filesystemrights]::changepermissions -bor [int64][security.accesscontrol.filesystemrights]::takeownership
 foreach($ace in $acl.getaccessrules($true,$true,[security.principal.securityidentifier])){
  if($ace.accesscontroltype -eq 'Allow' -and ([int64]$ace.filesystemrights -band $w) -and $ace.identityreference.value -notin @('S-1-5-18','S-1-5-32-544')){throw 'cc07_untrusted_writer'}
 }
}
function proof {
 $rows=@(& powershell.exe -noprofile -noninteractive -executionpolicy bypass -file $operator -mode check -robot $robot 2>&1)
 # Intentional HALTED returns HEALTH_PARTIAL: parse the individual status lines.
 $task=@($rows | where-object {$_ -match ('^v20_08_5_'+$robot+'_task=')})
 $switch=@($rows | where-object {$_ -match ('^v20_08_5_'+$robot+'_switch=')})
 $age=@($rows | where-object {$_ -match ('^v20_08_5_'+$robot+'_age_seconds=')})
 need ($task.count -eq 1 -and [string]$task[0] -match '=Running$') 'cc07_task_not_running'
 need ($switch.count -eq 1 -and [string]$switch[0] -match '=HALTED$|=ARMED$') 'cc07_switch_unknown'
 need ($age.count -eq 1 -and [string]$age[0] -match '=[0-9]+$') 'cc07_cycle_age_unknown'
 need ([int](([string]$age[0]).split('=')[-1]) -le 90) 'cc07_cycle_stale'
 return ([string]$switch[0]).split('=')[-1]
}
function flat {
 $rows=@(& powershell.exe -noprofile -noninteractive -executionpolicy bypass -file $launcher -mode readonly -robot $robot 2>&1)
 need ($lastexitcode -eq 0 -and ($rows -join '|') -match 'v20_08_4_positions=0' -and ($rows -join '|') -match 'v20_08_4_active_orders=0') 'cc07_broker_flat_not_proven'
}
function audit([string]$phase,[string]$result){
 $log=join-path $audit 'v20-control.jsonl'
 if(test-path -literalpath $log){trusted $log}
 $row=[ordered]@{schema='cc.v20.audit.v1';utc=[datetimeoffset]::utcnow.tostring('o');request_id=$requestid;robot=$robot;action=$action;actor_sid=$sid;phase=$phase;result=$result}
 $data=[text.utf8encoding]::new($false).getbytes(($row|convertto-json -compress)+[environment]::newline)
 $stream=[io.filestream]::new($log,[io.filemode]::append,[io.fileaccess]::write,[io.fileshare]::none)
 try{$stream.write($data,0,$data.length);$stream.flush($true)}finally{$stream.dispose()}
}
function release {
 trusted $release
 $r=get-content -literalpath $release -raw -encoding utf8 | convertfrom-json
 need ($r.schema -ceq 'cc.v20.release.v1' -and $r.approved -ceq $true -and $r.robot -ceq $robot -and $r.action -ceq $action -and $r.request_id -ceq $requestid -and $r.actor_sid -ceq $sid) 'cc07_no_matching_release'
 $now=[datetimeoffset]::utcnow
 $issued=[datetimeoffset]::parse([string]$r.issued_utc)
 $expires=[datetimeoffset]::parse([string]$r.expires_utc)
 need ($issued -le $now.addseconds(30) -and $expires -ge $now -and $expires -le $issued.addminutes(5)) 'cc07_release_expired'
}
need ($env:os -ceq 'Windows_NT' -and $env:computername -ceq 'URIU-PC') 'cc07_wrong_host'
pin $operator '6f539f9c421efb56d492f1c903b998b4e8f4a9ca'
pin $launcher '93fc1ce4aded6c40453da14deb4846e10da1b14f'
$sid=[security.principal.windowsidentity]::getcurrent().user.value
$task=get-scheduledtask -taskname $robot -taskpath '\' -erroraction stop
$taskSid=if([string]$task.principal.userid -match '^S-\d+-'){[string]$task.principal.userid}else{([security.principal.ntaccount]::new([string]$task.principal.userid)).translate([security.principal.securityidentifier]).value}
need ($sid -ceq $taskSid) 'cc07_operator_sid_mismatch'
$state=proof
if($mode -eq 'preview'){
 write-output ('cc07_preview=pass robot='+$robot+' action='+$action+' task=running switch='+$state)
 write-output 'cc07_no_finam_no_arm_no_task_mutation=yes'
 return
}
need ($requestid -cmatch '^[a-z0-9][a-z0-9-]{0,47}$') 'cc07_invalid_request_id'
$identity=[security.principal.windowsprincipal]::new([security.principal.windowsidentity]::getcurrent())
need ($identity.isinrole([security.principal.windowsbuiltinrole]::administrator)) 'cc07_admin_required'
trusted $audit
# PAUSE is the only action that cannot ARM or strand a position. All other
# actions REQUIRE a separate fresh admin-owned approval, never UI input alone.
if($action -ne 'pause'){release}
$expected='cc07 '+$action+' '+$robot+' '+$requestid
$typed=read-host ('type exactly: '+$expected)
need ($typed -ceq $expected) 'cc07_confirmation_refused'
$mutex=[threading.mutex]::new($false,'Global\ControlCenter_CC07_V20')
$locked=$false
try{
 try{$locked=$mutex.waitone(0)}catch [threading.abandonedmutexexception]{throw 'cc07_abandoned_mutex'}
 need $locked 'cc07_command_in_progress'
 $log=join-path $audit 'v20-control.jsonl'
 if(test-path -literalpath $log){
  trusted $log
  need ((get-item -literalpath $log).length -le 4194304) 'cc07_audit_full'
  foreach($line in @(get-content -literalpath $log -encoding utf8)){
   if($line){
    $old=$line|convertfrom-json
    need ([string]$old.request_id -cne $requestid) 'cc07_duplicate_request_id'
   }
  }
 }
 $state=proof
 if($action -ne 'pause'){release;flat}
 audit 'began' 'preflight_pass'
 try{
  if($action -eq 'pause' -and $state -ceq 'HALTED'){
   audit 'finished' 'already_halted_no_change'
   write-output 'cc07_result=already_halted_no_change'
   return
  }
  $modeStock=if($action -in @('pause','stop')){'stop'}else{$action}
  $rows=@(& powershell.exe -noprofile -noninteractive -executionpolicy bypass -file $operator -mode $modeStock -robot $robot 2>&1)
  need ($lastexitcode -eq 0) 'cc07_stock_operator_failed'
  if($action -eq 'stop'){
   # Stop is not V20 "stop": first HALT, then fresh broker flat proof.
   flat
   stop-scheduledtask -taskname $robot -taskpath '\' -erroraction stop
   $after=get-scheduledtask -taskname $robot -taskpath '\' -erroraction stop
   need ($after.state -ne 'Running') 'cc07_task_still_running'
  }else{
   $after=proof
   if($action -eq 'pause'){need ($after -ceq 'HALTED') 'cc07_pause_not_verified'}
   if($action -in @('start','restart')){need ($after -ceq 'ARMED') 'cc07_arm_not_verified'}
  }
  audit 'finished' ('verified_'+$action)
  write-output ('cc07_result=verified_'+$action)
 }catch{
  audit 'finished' 'unknown_outcome_reconcile_manually'
  throw
 }
}finally{
 if($locked){$mutex.releasemutex()}
 $mutex.dispose()
}
