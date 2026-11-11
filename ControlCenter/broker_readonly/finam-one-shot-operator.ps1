# CC-03 independent H1 FINAM REAL_READONLY one-shot; operator only, no Streamlit.
# FIXED METHODS: POST auth session/details; GET exact account/orders; no trading POST.
[CmdletBinding()]
param([switch]$execute)
$erroractionpreference='stop'
$stage='preflight';$plain=$null;$cipher=$null;$credential=$null;$token=$null;$secret=$null;$accountid=$null
if(-not $execute){write-output 'cc03_finam_one_shot=preview_no_network_no_secrets';write-output 'allowed_requests=post_sessions;post_sessions_details;get_account;get_orders';return}
try{
  if([environment]::osversion.platform -ne [platformid]::win32nt){throw 'WINDOWS_REQUIRED'}
  $root='c:\tradingsystemlab\runtime\secrets'
  $meta=join-path $root 'finam-real-readonly.metadata.json'
  $blob=join-path $root 'finam-real-readonly.dpapi'
  if(-not [io.file]::Exists($meta) -or -not [io.file]::Exists($blob)){throw 'READONLY_DPAPI_ABSENT'}
  foreach($path in @($root,$meta,$blob)){if(([io.file]::GetAttributes($path) -band [io.fileattributes]::ReparsePoint) -ne 0){throw 'REPARSE_FORBIDDEN'}}
  $metadata=[io.file]::ReadAllText($meta,[text.encoding]::utf8)|convertfrom-json
  $spec='PROD_STAGE7_46DB784378797C7FB04636892350AFF21006D71A31F2CED9D4B974EDA2DC36B8'
  if($metadata.schema_version -ne 1 -or $metadata.scope -cne 'CurrentUser' -or $metadata.production_id -cne $spec){throw 'DPAPI_METADATA_UNTRUSTED'}
  $identity=[security.principal.windowsidentity]::GetCurrent();if($null -eq $identity.User){throw 'PRINCIPAL_MISSING'}
  $sha=[security.cryptography.sha256]::Create()
  try{$sidbytes=[text.encoding]::utf8.GetBytes($identity.User.Value);$sidhash=([bitconverter]::ToString($sha.ComputeHash($sidbytes))).Replace('-','').ToLowerInvariant()}finally{$sha.Dispose()}
  if($sidhash -cne $metadata.principal_sid_sha256){throw 'DPAPI_OWNER_MISMATCH'}
  $stage='dpapi'
  add-type -assemblyname system.security
  $cipher=[io.file]::ReadAllBytes($blob)
  if($cipher.Length -lt 16 -or $cipher.Length -gt 65536){throw 'DPAPI_SIZE_INVALID'}
  $entropy=[text.encoding]::utf8.GetBytes('TradingSystemLab.Stage8.RealReadonly.v1')
  $plain=[security.cryptography.protecteddata]::Unprotect($cipher,$entropy,[security.cryptography.dataprotectionscope]::CurrentUser)
  $credential=([text.encoding]::utf8.GetString($plain)|convertfrom-json)
  if($credential.schema_version -ne 1 -or $credential.mode -cne 'REAL_READONLY' -or $credential.production_id -cne $spec){throw 'DPAPI_CREDENTIAL_WRONG_MODE'}
  $secret=[string]$credential.finam_api_secret;$accountid=[string]$credential.finam_real_account_id
  if([string]::IsNullOrWhiteSpace($secret) -or $accountid -cnotmatch '^[A-Za-z0-9_-]{1,80}$'){throw 'CREDENTIAL_INCOMPLETE'}
  $credential=$null
  $stage='session'
  [net.servicepointmanager]::SecurityProtocol=[net.securityprotocoltype]::Tls12
  $base='https://api.finam.ru/v1'
  $sess=invoke-restmethod -uri ($base+'/sessions') -method post -contenttype 'application/json' -body (@{secret=$secret}|convertto-json -compress) -timeoutsec 15 -usebasicparsing
  $secret=$null;$token=[string]$sess.token
  if([string]::IsNullOrWhiteSpace($token)){throw 'SESSION_TOKEN_ABSENT'}
  $stage='session_details'
  $details=invoke-restmethod -uri ($base+'/sessions/details') -method post -contenttype 'application/json' -body (@{token=$token}|convertto-json -compress) -timeoutsec 15 -usebasicparsing
  if($details.readonly -cne $true -or @($details.account_ids|where-object {$_ -ceq $accountid}).count -ne 1){throw 'READONLY_SESSION_AND_ACCOUNT_NOT_CONFIRMED'}
  $headers=@{Authorization=('Bearer '+$token);Accept='application/json'}
  $stage='account'
  $acct=invoke-restmethod -uri ($base+'/accounts/'+$accountid) -method get -headers $headers -timeoutsec 15 -usebasicparsing
  if($acct.account_id -cne $accountid -or @('ACCOUNT_ACTIVE','ACCOUNT_STATUS_ACTIVE') -cnotcontains $acct.status -or $acct.positions -isnot [array]){throw 'ACCOUNT_RESPONSE_INVALID'}
  $stage='orders'
  $orders=invoke-restmethod -uri ($base+'/accounts/'+$accountid+'/orders') -method get -headers $headers -timeoutsec 15 -usebasicparsing
  if($orders.orders -isnot [array]){throw 'ORDERS_COLLECTION_INVALID'}
  $seen=@{};$n4=@{'USDRUBF@RTSX'='USDRUBF';'CNYRUBF@RTSX'='CNYRUBF';'GLDRUBF@RTSX'='GLDRUBF';'IMOEXF@RTSX'='IMOEXF'}
  $n4qty=@{USDRUBF=0;CNYRUBF=0;GLDRUBF=0;IMOEXF=0};$other=0;$culture=[globalization.cultureinfo]::InvariantCulture
  foreach($p in $acct.positions){
    if($null -eq $p -or [string]::IsNullOrWhiteSpace([string]$p.symbol) -or $seen.ContainsKey([string]$p.symbol)){throw 'POSITION_SCHEMA_INVALID'}
    $seen[[string]$p.symbol]=$true;$q=[decimal]0;$val=[string]$p.quantity.value
    if(-not [decimal]::TryParse($val,[globalization.numberstyles]::Number,$culture,[ref]$q) -or $q -ne [decimal]::Truncate($q) -or [math]::Abs($q) -gt 10000000){throw 'POSITION_QUANTITY_INVALID'}
    if($n4.ContainsKey([string]$p.symbol)){$n4qty[$n4[[string]$p.symbol]]=[long]$q}elseif($q -ne 0){$other++}
  }
  $active=@{NEW=1;PARTIAL_FILL=1;DONE_FOR_DAY=1;PENDING_CANCEL=1;SUSPENDED=1;PENDING_NEW=1;FORWARDING=1;WAIT=1;WATCHING=1;LINK_WAIT=1;SL_GUARD_TIME=1;SL_FORWARDING=1;TP_GUARD_TIME=1;TP_CORRECTION=1;TP_FORWARDING=1;TP_CORR_GUARD_TIME=1}
  $terminal=@{FILLED=1;CANCELLED=1;REPLACED=1;REJECTED=1;EXPIRED=1;FAILED=1;DENIED_BY_BROKER=1;REJECTED_BY_EXCHANGE=1;EXECUTED=1;DISABLED=1;SL_EXECUTED=1;TP_EXECUTED=1}
  $seenorder=@{};$activecount=0;$sltpcount=0
  foreach($o in $orders.orders){
    if($null -eq $o -or [string]::IsNullOrWhiteSpace([string]$o.order_id) -or $seenorder.ContainsKey([string]$o.order_id)){throw 'ORDER_SCHEMA_INVALID'}
    $seenorder[[string]$o.order_id]=$true;$status=([string]$o.status).ToUpperInvariant().Replace('ORDER_STATUS_','')
    if($status -ceq 'PARTIALLY_FILLED'){$status='PARTIAL_FILL'};if($status -ceq 'CANCELED'){$status='CANCELLED'}
    if($active.ContainsKey($status)){$activecount++;if($null -ne $o.sltp_order -and @($o.sltp_order.psobject.properties).count -gt 0){$sltpcount++}}
    elseif(-not $terminal.ContainsKey($status)){throw 'ORDER_STATUS_UNKNOWN'}
  }
  write-output 'cc03_finam_one_shot=pass'
  write-output 'readonly_session=verified_true'
  write-output 'readonly_account_in_session=verified_true'
  write-output 'broker_account_identity=pass'
  write-output ('broker_response_received_at_utc='+[datetime]::UtcNow.ToString('yyyy-MM-ddTHH:mm:ssZ'))
  write-output 'broker_original_snapshot_timestamp=not_supplied_by_api_response'
  foreach($n in @('USDRUBF','CNYRUBF','GLDRUBF','IMOEXF')){write-output ('broker_'+$n.ToLowerInvariant()+'_position_contracts='+$n4qty[$n])}
  write-output ('broker_other_nonzero_position_symbols='+$other)
  write-output ('broker_order_rows='+@($orders.orders).count)
  write-output ('broker_active_order_rows='+$activecount)
  write-output ('broker_active_sltp_order_rows='+$sltpcount)
  write-output 'h1_engine_account_ownership=unverified_no_h1_runtime_read'
  write-output 'broker_stop_position_linkage=unverified'
  write-output 'cc_owned_snapshot_published=no'
  write-output 'no_h1_json_sqlite_task_order_cancel_or_write=yes'
}catch{
  write-output ('cc03_finam_one_shot=blocked_'+$stage)
  write-output 'no_h1_json_sqlite_task_order_cancel_or_write=yes'
  exit 1
}finally{
  if($null -ne $plain){[array]::Clear($plain,0,$plain.Length)}
  if($null -ne $cipher){[array]::Clear($cipher,0,$cipher.Length)}
  $credential=$null;$secret=$null;$accountid=$null;$token=$null
}
