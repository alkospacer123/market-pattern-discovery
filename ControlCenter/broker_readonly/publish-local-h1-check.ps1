# Publish the existing H1 operator check to a CC-owned file. Never called by Streamlit.
[CmdletBinding()]
param([switch]$execute)
$erroractionpreference='stop'
if(-not $execute){write-output 'cc03_h1_local_publish=preview_no_h1_read_no_write';return}
$root='c:\control center\data\broker-readonly'
$source='c:\tradingsystemlab\tsl-h1-01-check.ps1'
$expectedsha='66630f23e83ee6df30ce5ca402a15795159a38ae7f9c4156b355980ede7ddb81'
$dest=join-path $root 'h1-local-report.txt'
$tmp=$null
try {
  $who=[security.principal.windowsprincipal]::new([security.principal.windowsidentity]::getcurrent())
  if(-not $who.isinrole([security.principal.windowsbuiltinrole]::administrator)){throw 'ADMIN_REQUIRED'}
  foreach($path in @('c:\control center','c:\control center\data',$root,$source)){
    if(-not [io.file]::Exists($path) -and -not [io.directory]::Exists($path)){throw 'SOURCE_OR_ROOT_MISSING'}
    if(([io.file]::GetAttributes($path) -band [io.fileattributes]::ReparsePoint) -ne 0){throw 'REPARSE_FORBIDDEN'}
  }
  if(([io.driveinfo]::new('c:\')).DriveFormat -cne 'NTFS'){throw 'LOCAL_NTFS_REQUIRED'}
  $acl=get-acl -literalpath $root
  $trusted=@('S-1-5-18','S-1-5-32-544')
  if($trusted -cnotcontains $acl.getowner([security.principal.securityidentifier]).value){throw 'ROOT_OWNER_UNTRUSTED'}
  foreach($rule in $acl.access){
    if($rule.accesscontroltype -ne [security.accesscontrol.accesscontroltype]::Allow){continue}
    $sid=$rule.identityreference.translate([security.principal.securityidentifier]).value
    $rights=[long]$rule.filesystemrights
    if((($rights -band 0x000d0156) -ne 0 -or ($rights -band 0x50000000) -ne 0) -and $trusted -cnotcontains $sid){throw 'UNTRUSTED_WRITER'}
  }
  if([io.file]::Exists($dest) -and ([io.file]::GetAttributes($dest) -band [io.fileattributes]::ReparsePoint) -ne 0){throw 'DEST_REPARSE_FORBIDDEN'}
  if((get-filehash -literalpath $source -algorithm sha256).hash.tolowerinvariant() -ne $expectedsha){throw 'H1_CHECK_SOURCE_HASH_MISMATCH'}
  $lines=@(& powershell.exe -noprofile -noninteractive -executionpolicy bypass -file $source 2>&1)
  if($lastexitcode -ne 0){throw 'EXISTING_H1_CHECK_FAILED'}
  $raw=($lines -join "`n")+"`n"
  if($raw.length -gt 50000 -or $raw -notmatch '(?m)^TRADINGSYSTEMLAB_LIVE_LOCAL_READONLY_CHECK=PASS$' -or
     $raw -notmatch '(?m)^NO_CHANGES_MADE_BY_THIS_SCRIPT=YES$' -or
     $raw -notmatch '(?m)^LAST_10_PRODUCTION_CYCLE_ATTEMPTS_PRESENT=PASS$'){throw 'H1_OPERATOR_EVIDENCE_UNVERIFIED'}
  $bytes=[text.encoding]::utf8.getbytes($raw)
  if($bytes.length -gt 65536){throw 'REPORT_TOO_LARGE'}
  $tmp=join-path $root ('.cc03-local-'+[guid]::newguid().tostring('n')+'.tmp')
  $stream=[io.filestream]::new($tmp,[io.filemode]::createnew,[io.fileaccess]::write,[io.fileshare]::none)
  try{$stream.write($bytes,0,$bytes.length);$stream.flush($true)}finally{$stream.dispose()}
  if([io.file]::Exists($dest)){[io.file]::replace($tmp,$dest,$null,$true)}
  else{[io.file]::move($tmp,$dest)}
  $tmp=$null
  write-output 'cc03_h1_local_publish=pass'
  write-output 'cc03_local_h1_health_is_reported_not_broker_authority=yes'
  write-output 'cc03_refresh=click_existing_button'
  write-output 'cc03_no_h1_m15_task_order_cancel_mutation=yes'
} catch {
  write-output 'cc03_h1_local_publish=blocked'
  exit 1
} finally {
  if($null -ne $tmp -and [io.file]::Exists($tmp)){[io.file]::delete($tmp)}
}
