# CC-07 Intel install: CC-owned controller/audit only.
# This installer DOES NOT call the operator in execute mode, FINAM, Task, ARM.
[CmdletBinding()]
param([ValidateSet('check','install')][string]$mode='check')
$ErrorActionPreference='Stop'
Set-StrictMode -Version Latest
$repo='alkospacer123/market-pattern-discovery'
$pin='f08cd032d365a4b31aab0e51949973b564cd1030'
$root='c:\control center'
$dest=Join-Path $root 'cc07-operator'
$script=Join-Path $dest 'cc07-v20-operator.ps1'
$audit=Join-Path $root 'data\control-audit'
function need([bool]$ok,[string]$code){if(-not $ok){throw $code}}
function isplain([string]$path){
 $item=get-item -literalpath $path -force -erroraction stop
 need (-not [bool]($item.attributes -band [io.fileattributes]::reparsepoint)) 'cc07_reparse_forbidden'
}
function pinned([string]$path,[string]$hash){
 need (test-path -literalpath $path -pathtype leaf) 'cc07_operator_missing'
 isplain $path
 $actual=(& git.exe hash-object -- $path).trim()
 need ($lastexitcode -eq 0 -and $actual -ceq $hash) 'cc07_operator_pin_mismatch'
}
function aclprotected([string]$path){
 $a=get-acl -literalpath $path -erroraction stop
 need ($a.getowner([security.principal.securityidentifier]).value -in @('S-1-5-18','S-1-5-32-544')) 'cc07_owner_not_admin'
 need ($a.areaccessrulesprotected) 'cc07_acl_inheritance_not_protected'
 $mutation=[int64][security.accesscontrol.filesystemrights]::write -bor [int64][security.accesscontrol.filesystemrights]::delete -bor [int64][security.accesscontrol.filesystemrights]::changepermissions -bor [int64][security.accesscontrol.filesystemrights]::takeownership
 foreach($ace in $a.getaccessrules($true,$true,[security.principal.securityidentifier])){
  if($ace.accesscontroltype -eq 'Allow' -and $ace.identityreference.value -notin @('S-1-5-18','S-1-5-32-544') -and ([int64]$ace.filesystemrights -band $mutation)){throw 'cc07_untrusted_writer'}
 }
}
function lockfolder([string]$path){
 & icacls.exe $path /inheritance:r /grant:r '*S-1-5-18:(oi)(ci)f' '*S-1-5-32-544:(oi)(ci)f' | out-null
 need ($lastexitcode -eq 0) 'cc07_folder_acl_failed'
}
need ($env:os -ceq 'Windows_NT' -and $env:computername -ceq 'URIU-PC') 'cc07_wrong_intel'
need (test-path -literalpath $root -pathtype container) 'cc07_control_center_missing'
need (test-path -literalpath (join-path $root 'data') -pathtype container) 'cc07_data_root_missing'
isplain $root
isplain (join-path $root 'data')
if($mode -eq 'check'){
 if(test-path -literalpath $dest){
  isplain $dest
  pinned $script $pin
  aclprotected $dest
  aclprotected $script
  write-output 'cc07_operator=installed_pinned'
 }else{write-output 'cc07_operator=not_installed'}
 if(test-path -literalpath $audit){
  isplain $audit
  aclprotected $audit
  write-output 'cc07_audit=protected'
 }else{write-output 'cc07_audit=not_installed'}
 write-output 'cc07_check=no_task_no_broker_no_arm'
 return
}
$identity=[security.principal.windowsprincipal]::new([security.principal.windowsidentity]::getcurrent())
need ($identity.isinrole([security.principal.windowsbuiltinrole]::administrator)) 'cc07_admin_install_required'
# Require both independent child roots to be absent. No overwrite of any existing data.
need (-not (test-path -literalpath $dest)) 'cc07_operator_exists_use_check'
need (-not (test-path -literalpath $audit)) 'cc07_audit_exists_use_check'
# Retrieve and pin exact immutable Git blob; no remote branch evaluation.
$b=invoke-restmethod -uri ('https://api.github.com/repos/'+$repo+'/git/blobs/'+$pin) -headers @{'user-agent'='control-center-cc07'} -timeoutsec 25
need ($b.sha -ceq $pin -and $b.encoding -ceq 'base64') 'cc07_download_not_pinned'
$bytes=[convert]::frombase64string($b.content)
need ($bytes.length -gt 5000 -and $bytes.length -lt 20000) 'cc07_source_size_invalid'
$madeDest=$false
$madeAudit=$false
try{
 new-item -itemtype directory -path $dest -erroraction stop | out-null
 $madeDest=$true
 lockfolder $dest
 new-item -itemtype directory -path $audit -erroraction stop | out-null
 $madeAudit=$true
 lockfolder $audit
 [io.file]::writeallbytes($script,$bytes)
 & icacls.exe $script /inheritance:r /grant:r '*S-1-5-18:f' '*S-1-5-32-544:f' | out-null
 need ($lastexitcode -eq 0) 'cc07_operator_acl_failed'
 pinned $script $pin
 aclprotected $dest
 aclprotected $audit
 # New file inherits admin/SYSTEM only from the protected CC07 folder.
 $a=get-acl -literalpath $script
 need ($a.getowner([security.principal.securityidentifier]).value -in @('S-1-5-18','S-1-5-32-544')) 'cc07_operator_owner_not_admin'
 $mutation=[int64][security.accesscontrol.filesystemrights]::write -bor [int64][security.accesscontrol.filesystemrights]::delete -bor [int64][security.accesscontrol.filesystemrights]::changepermissions
 foreach($ace in $a.getaccessrules($true,$true,[security.principal.securityidentifier])){
  if($ace.accesscontroltype -eq 'Allow' -and $ace.identityreference.value -notin @('S-1-5-18','S-1-5-32-544') -and ([int64]$ace.filesystemrights -band $mutation)){throw 'cc07_operator_untrusted_writer'}
 }
 write-output 'cc07_install=pass_cc_owned'
 write-output ('cc07_source_git_blob='+$pin)
 write-output 'cc07_audit=protected'
 write-output 'cc07_release=not_created'
 write-output 'cc07_actions=not_executed'
 write-output 'cc07_no_arm_no_task_no_broker_mutation=yes'
}catch{
 # Do not delete unknown pre-existing content; retain CC-owned evidence on failure.
 throw
}
