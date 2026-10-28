# CC-07D: stage strictly pinned V20 GUI code in new CC-only folder.
# No edit of existing 8502, no FINAM/V20/Task/controller invocation.
[CmdletBinding()]
param([ValidateSet('check','install')][string]$mode='check')
$ErrorActionPreference='Stop'
Set-StrictMode -Version Latest
$root='c:\control center'
$dest=join-path $root 'cc07-panel-13ce0973'
$python=join-path $root 'runtime\python312\python.exe'
$source='https://api.github.com/repos/alkospacer123/market-pattern-discovery/git/blobs/'
$files=@(
 'v20_app.py|35eb04290a326c9167db7c1efc218f5815fef9bc',
 'v20_command_channel.py|66c2061339214c49ec9f9b9e201037d63522791f',
 'cc/__init__.py|68772ec08a8badf8fc5edbf24bfa8af70c4ac002',
 'cc/manual_gate.py|caa9db85ed1ea14a990f44a9428269369df0a890',
 'cc/deployment_paths.py|727e4ac49b6f24f296d5bf5720ef947a24b0efb8',
 'cc/v20_contract.py|365065026de1031cdb888798a4419458523dcb20',
 'cc/v20_receiver.py|6661b746a19b58b4f810fbda2dc04e4809bcd518',
 'cc/v20_staging.py|b91aae83326fa9498a35168bdc52f3bd79adac4c',
 'cc/v20_manual_export.py|ca5149e61d0c90d00c11e59590eb6dcd0edddb52',
 'cc/providers/__init__.py|27ce6a15a69f9c6d7cfb5b369024e5b5e05be912',
 'cc/providers/windows_file.py|aa2034f026d797b6f12ccfdfcc7ab159f50100e6'
)
function need([bool]$ok,[string]$code){if(-not $ok){throw $code}}
function plain([string]$p){
 need (test-path -literalpath $p) 'cc07_panel_path_missing'
 need (-not [bool]((get-item -literalpath $p -force).attributes -band [io.fileattributes]::reparsepoint)) 'cc07_panel_reparse'
}
function pin([string]$file,[string]$sha){
 plain $file
 need (test-path -literalpath $file -pathtype leaf) 'cc07_panel_file_missing'
 $got=(& git.exe hash-object -- $file).trim()
 need ($lastexitcode -eq 0 -and $got -ceq $sha) 'cc07_panel_source_hash_mismatch'
}
function safeacl([string]$folder,[string]$panel){
 $acl=get-acl -literalpath $folder -erroraction stop
 need $acl.areaccessrulesprotected 'cc07_panel_acl_inherited'
 need ($acl.getowner([security.principal.securityidentifier]).value -ne $panel) 'cc07_panel_owned_by_ccpanel'
 $write=[int64][security.accesscontrol.filesystemrights]::write -bor [int64][security.accesscontrol.filesystemrights]::delete -bor [int64][security.accesscontrol.filesystemrights]::changepermissions -bor [int64][security.accesscontrol.filesystemrights]::takeownership
 $read=$false
 foreach($a in $acl.getaccessrules($true,$true,[security.principal.securityidentifier])){
  if($a.accesscontroltype -eq 'Allow'){
   need ($a.identityreference.value -in @('S-1-5-18','S-1-5-32-544',$panel)) 'cc07_panel_untrusted_ace'
   if($a.identityreference.value -eq $panel){
    need (-not [bool]([int64]$a.filesystemrights -band $write)) 'cc07_panel_ccpanel_write_forbidden'
    if(($a.filesystemrights -band [security.accesscontrol.filesystemrights]::readandexecute) -eq [security.accesscontrol.filesystemrights]::readandexecute){$read=$true}
   }
  }
 }
 need $read 'cc07_panel_no_ccpanel_read'
}
need ($env:os -ceq 'Windows_NT' -and $env:computername -ceq 'URIU-PC') 'cc07_panel_wrong_host'
plain $root
need (test-path -literalpath $python -pathtype leaf) 'cc07_panel_python_missing'
$account=get-localuser -name 'ccpanel' -erroraction stop
need $account.enabled 'cc07_panel_ccpanel_disabled'
$panel=[string]$account.sid.value
need ($panel -match '^S-1-5-21-([0-9]+-){3}[0-9]+$') 'cc07_panel_sid_invalid'
$admins=@(get-localgroupmember -sid 'S-1-5-32-544' -erroraction stop)
need (-not [bool](@($admins|where-object {$_.sid.value -eq $panel}).count)) 'cc07_panel_ccpanel_admin'
if($mode -eq 'check'){
 if(-not (test-path -literalpath $dest)){write-output 'cc07_panel_stage=not_installed';write-output 'cc07_panel_no_task_no_arm=yes';return}
 plain $dest
 safeacl $dest $panel
 foreach($line in $files){
  $a=$line.split('|')
  need ($a.length -eq 2 -and $a[0] -match '^[A-Za-z0-9_./-]+$' -and $a[1] -match '^[a-f0-9]{40}$') 'cc07_panel_manifest_invalid'
  pin (join-path $dest ($a[0].replace('/','\'))) $a[1]
 }
 write-output 'cc07_panel_stage=pinned_11_of_11'
 write-output 'cc07_panel_ccpanel_acl=read_execute_only'
 write-output 'cc07_panel_8502=untouched'
 write-output 'cc07_panel_gateway=not_started_no_arm'
 return
}
$admin=[security.principal.windowsprincipal]::new([security.principal.windowsidentity]::getcurrent())
need $admin.isinrole([security.principal.windowsbuiltinrole]::administrator) 'cc07_panel_admin_install_required'
need (-not (test-path -literalpath $dest)) 'cc07_panel_stage_exists'
$buffer=@()
foreach($line in $files){
 $a=$line.split('|')
 need ($a.length -eq 2 -and $a[0] -match '^[A-Za-z0-9_./-]+$' -and $a[1] -match '^[a-f0-9]{40}$') 'cc07_panel_manifest_invalid'
 $b=invoke-restmethod -uri ($source+$a[1]) -headers @{'user-agent'='control-center-cc07'} -timeoutsec 25
 need ($b.sha -ceq $a[1] -and $b.encoding -ceq 'base64') 'cc07_panel_blob_invalid'
 $body=[convert]::frombase64string($b.content)
 need ($body.length -gt 0 -and $body.length -lt 20000) 'cc07_panel_blob_size'
 $buffer+=,[pscustomobject]@{name=$a[0];hash=$a[1];body=$body}
}
new-item -itemtype directory -path $dest -erroraction stop|out-null
& icacls.exe $dest /inheritance:r /grant:r '*S-1-5-18:(oi)(ci)f' '*S-1-5-32-544:(oi)(ci)f' ("*"+$panel+":(oi)(ci)rx") | out-null
need ($lastexitcode -eq 0) 'cc07_panel_stage_acl_failed'
safeacl $dest $panel
foreach($item in $buffer){
 $out=join-path $dest ($item.name.replace('/','\'))
 $parent=split-path -parent $out
 if(-not (test-path -literalpath $parent)){new-item -itemtype directory -path $parent -force -erroraction stop|out-null}
 need (-not (test-path -literalpath $out)) 'cc07_panel_unexpected_existing_file'
 [io.file]::writeallbytes($out,[byte[]]$item.body)
 pin $out $item.hash
}
# The staged panel is not started. No requests to live broker/Tasks.
write-output 'cc07_panel_stage_install=pass_cc_owned'
write-output 'cc07_panel_files=pinned_11_of_11'
write-output 'cc07_panel_ccpanel_acl=read_execute_only'
write-output 'cc07_panel_8502=untouched'
write-output 'cc07_panel_gateway=not_started_no_arm'
