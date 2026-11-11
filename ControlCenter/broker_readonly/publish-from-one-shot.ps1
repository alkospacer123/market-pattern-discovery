# CC-03 operator-side only: publish redacted one-shot output, never called by Streamlit.
[CmdletBinding()]
param([switch]$execute)
$erroractionpreference='stop'
if(-not $execute){write-output 'cc03_broker_publish=preview_no_network_no_file_write';return}
$stage='source'
$tmp=$null
try {
  $probe=join-path $env:userprofile 'downloads\cc03-finam-one-shot.ps1'
  $expected='33668f23c7ffb774e198b4f7ef55c85d73a6d407cd84b2a3cb1ea5bd6a97fc7c'
  if(-not [io.file]::Exists($probe) -or (get-filehash -literalpath $probe -algorithm sha256).hash.tolowerinvariant() -cne $expected){throw 'SOURCE_NOT_PINNED'}
  $stage='credential_binding'
  $root='c:\tradingsystemlab\runtime\secrets'
  $metadatafile=join-path $root 'finam-real-readonly.metadata.json'
  $blob=join-path $root 'finam-real-readonly.dpapi'
  foreach($p in @($root,$metadatafile,$blob)){if(-not [io.file]::Exists($p) -and $p -ne $root){throw 'DPAPI_ABSENT'};if(([io.file]::GetAttributes($p) -band [io.fileattributes]::ReparsePoint) -ne 0){throw 'REPARSE_FORBIDDEN'}}
  $meta=([io.file]::ReadAllText($metadatafile,[text.encoding]::utf8)|convertfrom-json)
  $spec='PROD_STAGE7_46DB784378797C7FB04636892350AFF21006D71A31F2CED9D4B974EDA2DC36B8'
  if($meta.schema_version -ne 1 -or $meta.scope -cne 'CurrentUser' -or $meta.production_id -cne $spec -or [string]$meta.principal_sid_sha256 -cnotmatch '^[a-f0-9]{64}$'){throw 'DPAPI_METADATA_INVALID'}
  $identity=[security.principal.windowsidentity]::GetCurrent()
  $sha=[security.cryptography.sha256]::Create()
  try {
    $ownerhash=([bitconverter]::ToString($sha.ComputeHash([text.encoding]::utf8.GetBytes($identity.User.Value)))).Replace('-','').ToLowerInvariant()
  } finally {$sha.Dispose()}
  if($ownerhash -cne $meta.principal_sid_sha256){throw 'DPAPI_OWNER_MISMATCH'}
  $blobhash=(get-filehash -literalpath $blob -algorithm sha256).hash.tolowerinvariant()
  $stage='target_acl'
  $target='c:\control center\data\broker-readonly'
  if(-not [io.directory]::Exists($target) -or ([io.driveinfo]::new('c:\')).DriveFormat -cne 'NTFS'){throw 'TRUSTED_NTFS_ROOT_REQUIRED'}
  foreach($p in @('c:\control center','c:\control center\data',$target)){if(([io.file]::GetAttributes($p) -band [io.fileattributes]::ReparsePoint) -ne 0){throw 'ROOT_REPARSE_FORBIDDEN'}}
  $acl=get-acl -literalpath $target
  $trusted=@('S-1-5-18','S-1-5-32-544')
  $owner=$acl.getowner([security.principal.securityidentifier]).value
  if($trusted -cnotcontains $owner){throw 'ROOT_OWNER_UNTRUSTED'}
  foreach($rule in $acl.access){
    if($rule.accesscontroltype -ne [security.accesscontrol.accesscontroltype]::Allow){continue}
    $sid=$rule.identityreference.translate([security.principal.securityidentifier]).value
    $rights=[long]$rule.filesystemrights
    if(($rights -band 0x000d0156) -ne 0 -or ($rights -band 0x50000000) -ne 0){
      if($trusted -cnotcontains $sid){throw 'ROOT_WRITABLE_BY_UNTRUSTED_SID'}
    }
  }
  $stage='finam_readonly'
  $lines=@(& powershell.exe -noprofile -noninteractive -executionpolicy bypass -file $probe -execute)
  if($lastexitcode -ne 0){throw 'BROKER_PROBE_FAILED'}
  $items=@{}
  foreach($line in $lines){
    if($line -cnotmatch '^([a-z0-9_]+)=([a-zA-Z0-9_.:-]+)$'){throw 'PROBE_OUTPUT_INVALID'}
    $key=$matches[1];$value=$matches[2]
    if($items.containskey($key)){throw 'PROBE_DUPLICATE_KEY'}
    $items[$key]=$value
  }
  $required=@('cc03_finam_one_shot','readonly_session','readonly_account_in_session','broker_account_identity',
    'broker_response_received_at_utc','broker_original_snapshot_timestamp',
    'broker_usdrubf_position_contracts','broker_cnyrubf_position_contracts',
    'broker_gldrubf_position_contracts','broker_imoexf_position_contracts',
    'broker_other_nonzero_position_symbols','broker_order_rows','broker_active_order_rows',
    'broker_active_sltp_order_rows','h1_engine_account_ownership','broker_stop_position_linkage',
    'cc_owned_snapshot_published','no_h1_json_sqlite_task_order_cancel_or_write')
  if($items.count -ne $required.count){throw 'PROBE_FIELDS_MISMATCH'}
  foreach($key in $required){if(-not $items.containskey($key)){throw 'PROBE_FIELD_MISSING'}}
  if($items['cc03_finam_one_shot'] -cne 'pass' -or
     $items['readonly_session'] -cne 'verified_true' -or
     $items['readonly_account_in_session'] -cne 'verified_true' -or
     $items['broker_account_identity'] -cne 'pass' -or
     $items['broker_original_snapshot_timestamp'] -cne 'not_supplied_by_api_response' -or
     $items['h1_engine_account_ownership'] -cne 'unverified_no_h1_runtime_read' -or
     $items['broker_stop_position_linkage'] -cne 'unverified' -or
     $items['cc_owned_snapshot_published'] -cne 'no' -or
     $items['no_h1_json_sqlite_task_order_cancel_or_write'] -cne 'yes'){throw 'READONLY_PROOF_MISSING'}
  $received=[datetime]::MinValue
  if(-not [datetime]::TryParseExact($items['broker_response_received_at_utc'],'yyyy-MM-ddTHH:mm:ssZ',
      [globalization.cultureinfo]::InvariantCulture,[globalization.datetimestyles]::AssumeUniversal,[ref]$received)){throw 'RECEIPT_CLOCK_INVALID'}
  if([math]::Abs(([datetime]::UtcNow-$received.ToUniversalTime()).TotalSeconds) -gt 120){throw 'RECEIPT_NOT_CURRENT'}
  $quantities=[ordered]@{}
  foreach($symbol in @('usdrubf','cnyrubf','gldrubf','imoexf')){
    $v=[long]0
    if(-not [long]::TryParse($items['broker_'+$symbol+'_position_contracts'],[ref]$v) -or [math]::Abs($v) -gt 10000000){throw 'QUANTITY_INVALID'}
    $quantities[$symbol.toupperinvariant()]=$v
  }
  $numbers=[ordered]@{}
  foreach($name in @('broker_other_nonzero_position_symbols','broker_order_rows','broker_active_order_rows','broker_active_sltp_order_rows')){
    $v=[int]0
    if(-not [int]::TryParse($items[$name],[ref]$v) -or $v -lt 0 -or $v -gt 1000000){throw 'COUNT_INVALID'}
    $numbers[$name]=$v
  }
  if($numbers.broker_active_order_rows -gt $numbers.broker_order_rows -or $numbers.broker_active_sltp_order_rows -gt $numbers.broker_active_order_rows){throw 'ORDER_COUNTS_INVALID'}
  $snapshot=[ordered]@{
    schema_id='cc03.h1-broker-readonly.observation.v1';robot_id='H1'
    source_id='CC03-H1-FINAMREADONLY';production_id=$spec
    probe_sha256=$expected;principal_sid_sha256=$ownerhash;credential_blob_sha256=$blobhash
    received_at_utc=$items['broker_response_received_at_utc']
    broker_original_snapshot_timestamp=$null
    readonly_session_verified=$true;account_response_identity_verified=$true
    position_contracts=$quantities;other_nonzero_position_symbols=$numbers.broker_other_nonzero_position_symbols
    order_rows=$numbers.broker_order_rows;active_order_rows=$numbers.broker_active_order_rows
    active_sltp_order_rows=$numbers.broker_active_sltp_order_rows
    positions_complete=$false;orders_complete=$false;h1_account_ownership_verified=$false
    stop_coverage_verified=$false
  }
  $stage='publish'
  $raw=[text.encoding]::utf8.GetBytes(($snapshot|convertto-json -compress -depth 6))
  if($raw.length -gt 16384){throw 'SNAPSHOT_TOO_LARGE'}
  $sha=[security.cryptography.sha256]::Create()
  try{$digest=([bitconverter]::ToString($sha.ComputeHash($raw))).Replace('-','').ToLowerInvariant()}finally{$sha.Dispose()}
  $guid=[guid]::NewGuid().ToString('n')
  $moment=([datetimeoffset]::UtcNow.ToUnixTimeMilliseconds()).ToString('d20')
  $name='h1-'+$moment+'-'+$guid+'-'+$digest+'.json'
  $tmp=join-path $target ('.cc03-'+$guid+'.tmp')
  $final=join-path $target $name
  $fs=[io.filestream]::new($tmp,[io.filemode]::CreateNew,[io.fileaccess]::Write,[io.fileshare]::None)
  try{$fs.Write($raw,0,$raw.Length);$fs.Flush($true)}finally{$fs.Dispose()}
  [io.file]::Move($tmp,$final)
  $tmp=$null
  write-output 'cc03_broker_publish=pass'
  write-output ('broker_snapshot_sha256='+$digest)
  write-output ('broker_snapshot_filename='+$name)
  write-output 'broker_snapshot_scope=redacted_broker_rows_only_h1_ownership_unknown'
  write-output 'no_h1_task_json_sqlite_order_cancel_or_mutation=yes'
} catch {
  write-output ('cc03_broker_publish=blocked_'+$stage)
  exit 1
} finally {
  if($null -ne $tmp -and [io.file]::Exists($tmp)){[io.file]::Delete($tmp)}
}
