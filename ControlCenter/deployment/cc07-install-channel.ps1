# CC-07 channel provisioning. Installs CC-only paths; never starts a worker
# and NEVER invokes V20 operator, FINAM, Tasks, or release/ARM.
[CmdletBinding()]
param([ValidateSet('check','install')][string]$mode='check')
$ErrorActionPreference='Stop'
Set-StrictMode -Version Latest
$root='c:\control center'
$data=join-path $root 'data'
$worker=join-path $root 'cc07-operator\cc07_command_worker.py'
$operator=join-path $root 'cc07-operator\cc07-v20-operator.ps1'
$inbox=join-path $data 'cc07-inbox'
$public=join-path $data 'cc07-public'
$private=join-path $data 'private'
$policy=join-path $private 'cc07-gateway-policy.json'
$hash='8ac883f48f79f8b2b5e7b90abd57e13d5cd9b942'
$source='https://api.github.com/repos/alkospacer123/market-pattern-discovery/git/blobs/'
function need([bool]$ok,[string]$code){if(-not $ok){throw $code}}
function plain([string]$path){
 $p=get-item -literalpath $path -force -erroraction stop
 need (-not [bool]($p.attributes -band [io.fileattributes]::reparsepoint)) 'cc07_channel_reparse'
}
function gitpin([string]$path,[string]$expected){
 need (test-path -literalpath $path -pathtype leaf) 'cc07_worker_missing'
 plain $path
 $g=(& git.exe hash-object -- $path).trim()
 need ($lastexitcode -eq 0 -and $g -ceq $expected) 'cc07_channel_hash_mismatch'
}
function lock([string]$path,[string]$perms){
 if($perms -eq 'read'){
  & icacls.exe $path /inheritance:r /grant:r '*S-1-5-18:(oi)(ci)f' '*S-1-5-32-544:(oi)(ci)f' ("*"+$panelSid+":(oi)(ci)rx") | out-null
 }elseif($perms -eq 'write'){
  & icacls.exe $path /inheritance:r /grant:r '*S-1-5-18:(oi)(ci)f' '*S-1-5-32-544:(oi)(ci)f' ("*"+$panelSid+":(oi)(ci)m") | out-null
 }else{
  & icacls.exe $path /inheritance:r /grant:r '*S-1-5-18:(oi)(ci)f' '*S-1-5-32-544:(oi)(ci)f' | out-null
 }
 need ($lastexitcode -eq 0) 'cc07_channel_acl_failed'
}
function trustedprivate([string]$path){
 need (test-path -literalpath $path -pathtype container) 'cc07_private_not_directory'
 plain $path
 $acl=get-acl -literalpath $path -erroraction stop
 need ($acl.getowner([security.principal.securityidentifier]).value -in @('S-1-5-18','S-1-5-32-544')) 'cc07_private_owner_untrusted'
 need ($acl.areaccessrulesprotected) 'cc07_private_acl_inherited'
 $write=[int64][security.accesscontrol.filesystemrights]::write -bor [int64][security.accesscontrol.filesystemrights]::delete -bor [int64][security.accesscontrol.filesystemrights]::changepermissions -bor [int64][security.accesscontrol.filesystemrights]::takeownership
 foreach($ace in $acl.getaccessrules($true,$true,[security.principal.securityidentifier])){
  if($ace.accesscontroltype -eq 'Allow' -and ([int64]$ace.filesystemrights -band $write) -and $ace.identityreference.value -notin @('S-1-5-18','S-1-5-32-544')){throw 'cc07_private_untrusted_writer'}
 }
}
need ($env:os -ceq 'Windows_NT' -and $env:computername -ceq 'URIU-PC') 'cc07_channel_wrong_host'
need (test-path -literalpath $root -pathtype container) 'cc07_channel_root_missing'
need (test-path -literalpath $data -pathtype container) 'cc07_channel_data_missing'
gitpin $operator '91a83e388978ded33525357397716d5fd509fc2a'
$panelSid=([security.principal.ntaccount]::new(($env:computername+'\ccpanel'))).translate([security.principal.securityidentifier]).value
need ($panelSid -match '^S-[0-9]+(-[0-9]+)+$') 'cc07_channel_panel_sid_invalid'
if($mode -eq 'check'){
 if(test-path -literalpath $worker){gitpin $worker $hash;write-output 'cc07_worker=installed_pinned'}else{write-output 'cc07_worker=not_installed'}
 if(test-path -literalpath $policy){
  plain $policy
  $v=get-content -literalpath $policy -raw -encoding utf8|convertfrom-json
  need ($v.approved -ceq $false) 'cc07_channel_already_active'
  write-output 'cc07_policy=inactive'
 }else{write-output 'cc07_policy=not_installed'}
 write-output 'cc07_channel_check=no_orders_no_arm_no_task_mutation'
 return
}
$identity=[security.principal.windowsprincipal]::new([security.principal.windowsidentity]::getcurrent())
need ($identity.isinrole([security.principal.windowsbuiltinrole]::administrator)) 'cc07_channel_admin_required'
foreach($path in @($worker,$inbox,$public,$policy)){
 need (-not (test-path -literalpath $path)) ('cc07_channel_target_exists_'+(split-path -leaf $path))
}
$privateExisting=[bool](test-path -literalpath $private)
if($privateExisting){trustedprivate $private}
$b=invoke-restmethod -uri ($source+$hash) -headers @{'user-agent'='control-center-cc07'} -timeoutsec 25
need ($b.sha -ceq $hash -and $b.encoding -ceq 'base64') 'cc07_channel_download_mismatch'
$bytes=[convert]::frombase64string($b.content)
need ($bytes.length -gt 10000 -and $bytes.length -lt 25000) 'cc07_channel_worker_size'
# Only CC-owned fresh files/directories. No replacement of existing objects.
if(-not $privateExisting){
 new-item -itemtype directory -path $private -erroraction stop | out-null
 lock $private 'admin'
}else{trustedprivate $private}
foreach($folder in @($public,$inbox)){
 $kind=if($folder -eq $public){'read'}else{'write'}
 new-item -itemtype directory -path $folder -erroraction stop | out-null
 lock $folder $kind
}
$processed=join-path $inbox 'processed'
new-item -itemtype directory -path $processed -erroraction stop | out-null
lock $processed 'admin'
[io.file]::writeallbytes($worker,$bytes)
& icacls.exe $worker /inheritance:r /grant:r '*S-1-5-18:f' '*S-1-5-32-544:f' | out-null
need ($lastexitcode -eq 0) 'cc07_worker_acl_failed'
gitpin $worker $hash
$report=[ordered]@{schema='cc.v20.gateway-policy.v1';approved=$false;operator_sid=[security.principal.windowsidentity]::getcurrent().user.value;panel_sid=$panelSid;expires_at=[datetimeoffset]::utcnow.addhours(12).tostring('o')}
[io.file]::writealltext($policy,($report|convertto-json -compress),[text.utf8encoding]::new($false))
& icacls.exe $policy /inheritance:r /grant:r '*S-1-5-18:f' '*S-1-5-32-544:f' | out-null
need ($lastexitcode -eq 0) 'cc07_policy_acl_failed'
write-output 'cc07_channel_install=pass_cc_only'
if($privateExisting){write-output 'cc07_private=trusted_reused_no_acl_change'}else{write-output 'cc07_private=created_cc_only'}
write-output ('cc07_worker_blob='+$hash)
write-output 'cc07_gateway_policy=inactive'
write-output 'cc07_gateway_process=not_started'
write-output 'cc07_no_arm_no_task_no_order=yes'
