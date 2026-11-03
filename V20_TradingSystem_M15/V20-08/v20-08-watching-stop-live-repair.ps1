# V20 2026-11-03 protected-open emergency repair: FINAM WATCHING SLTP missing client_order_id.
# No order POST/DELETE, no SQLite edits, NO automatic re-ARM of exposed accounts.
[CmdletBinding()]
param([ValidateSet('verify','install')][string]$mode='verify')
$ErrorActionPreference='Stop'
Set-StrictMode -Version Latest
$root='c:\v20lab'
$names=@('v20-shallow','v20-obv','v20-inside')
$stage=Join-Path $root 'pretrade-08\live-08'
$runtime=Join-Path $root 'pretrade-08\live-runtime-08\V20_TradingSystem_M15\v20_runtime'
$files=@{
    execution=(Join-Path $runtime 'finam_execution.py')
    worker=(Join-Path $runtime 'finam_live.py')
    launcher=(Join-Path $stage 'v20-08-live-launch.ps1')
}
$old=@{
    execution='4ea5cec17a31413c96531dd4f80f77e2a96f3f00'
    worker='2a1814a5aecb2a586e839b14f20076a98de0c1e0'
    launcher='3beac63e0e8985485bb43bb1627aabc96fbd107a'
}
$new=@{
    execution='9f59c4746acec3d55ea012a9dad5c513b7113d0b'
    worker='bd1858ad63de00bd6b142f5678848ed6d83e63e9'
    launcher='652b97fe071b1982d89b8ab8771e072436d7c2f0'
}
$operator=Join-Path $stage 'v20-08-live-operator.ps1'
$diag=Join-Path $env:userprofile 'downloads\v20-night-20261103-protection-readonly.ps1'
function need([bool]$ok,[string]$code){if(-not $ok){throw $code}}
function blob([string]$p){
    need (Test-Path -LiteralPath $p -PathType Leaf) ('V20_STOPREPAIR_FILE_MISSING '+$p)
    need (-not ((Get-Item -LiteralPath $p -Force).Attributes -band [io.fileattributes]::ReparsePoint)) 'V20_STOPREPAIR_REPARSE_FORBIDDEN'
    $result=(& git.exe hash-object -- $p).Trim().ToLowerInvariant()
    need ($LASTEXITCODE -eq 0) 'V20_STOPREPAIR_GIT_HASH_FAILED'
    return $result
}
function task-running([string]$n){
    return (Get-ScheduledTask -TaskName $n -TaskPath '\' -ErrorAction Stop).State -eq 'Running'
}
function check-switches(){
    foreach($n in $names){
        $p=Join-Path $root ('robots\'+$n.Substring(4)+'\safety\stage8-trading-kill-switch.json')
        need (Test-Path -LiteralPath $p -PathType Leaf) ('V20_STOPREPAIR_SWITCH_MISSING_'+$n)
        $s=Get-Content -LiteralPath $p -Raw -Encoding UTF8 | ConvertFrom-Json
        need ($s.state -ceq 'HALTED') ('V20_STOPREPAIR_REQUIRES_HALTED_'+$n)
        need (task-running $n) ('V20_STOPREPAIR_TASK_NOT_RUNNING_'+$n)
    }
}
function get-value([string[]]$lines,[string]$name,[string]$field){
    $prefix='v20_orders_'+$name+'_'+$field+'='
    $m=@($lines | Where-Object {$_.StartsWith($prefix,[StringComparison]::Ordinal)})
    need ($m.Count -eq 1) ('V20_STOPREPAIR_DIAG_FIELD_MISSING_'+$name+'_'+$field)
    return $m[0].Substring($prefix.Length)
}
function prove-stop([string[]]$lines,[string]$n,[string]$position,[string]$side){
    need ((get-value $lines $n 'durable_execution_halt') -ceq 'NONE') ('V20_STOPREPAIR_DURABLE_HALT_'+$n)
    need ((get-value $lines $n 'positions') -ceq $position) ('V20_STOPREPAIR_BROKER_POSITION_CHANGED_'+$n)
    need ((get-value $lines $n 'stored_protected_proofs') -ceq '1') ('V20_STOPREPAIR_PROOF_COUNT_'+$n)
    need ((get-value $lines $n 'rows') -ceq '1') ('V20_STOPREPAIR_ORDER_COUNT_'+$n)
    need ((get-value $lines $n 'invalid_rows') -ceq '1') ('V20_STOPREPAIR_INVALID_ROW_COUNT_'+$n)
    need ((get-value $lines $n 'proof_1_broker_stop_id_matches') -ceq '1') ('V20_STOPREPAIR_STOP_ID_MISSING_'+$n)
    $d=@((get-value $lines $n 'proof_1_details' | ConvertFrom-Json))
    need ($d.Count -eq 1) ('V20_STOPREPAIR_STOP_PROOF_AMBIGUOUS_'+$n)
    $x=$d[0]
    need ($x.active -eq $true -and $x.kind -ceq 'sltp' -and
          $x.status -ceq 'ORDER_STATUS_WATCHING' -and
          $x.comment_matches -eq $true -and
          $x.stop_price_matches_durable -eq $true -and
          $x.qty_sl_percent_100 -eq $true -and
          $x.sl_qty_measure -ceq 'SLTP_QTY_MEASURE_PERCENT' -and
          $x.valid_before -ceq 'VALID_BEFORE_GOOD_TILL_CANCEL' -and
          $x.side -ceq $side -and
          $x.client_id_matches -eq $false) ('V20_STOPREPAIR_BROKER_STOP_UNPROVEN_'+$n)
    $a=@((get-value $lines $n 'active_sltps' | ConvertFrom-Json))
    need ($a.Count -eq 1 -and $a[0].client_id_type -ceq 'string' -and
          $a[0].client_id_len -eq 0 -and $a[0].status -ceq 'WATCHING') ('V20_STOPREPAIR_WATCHING_SHAPE_CHANGED_'+$n)
}
function broker-preflight(){
    check-switches
    $lines=@(& powershell.exe -noprofile -noninteractive -executionpolicy bypass -file $diag -robot all 2>&1)
    need ($LASTEXITCODE -eq 0) 'V20_STOPREPAIR_DIAGNOSTIC_READ_FAILED'
    prove-stop $lines 'v20-shallow' '{"IMOEXF@RTSX": -5}' 'SIDE_BUY'
    prove-stop $lines 'v20-inside' '{"USDRUBF@RTSX": 2}' 'SIDE_SELL'
    foreach($field in @('durable_execution_halt','positions','rows','invalid_rows','stored_protected_proofs')){
        $expected=switch($field){'durable_execution_halt'{'NONE'} 'positions'{'{}'} default{'0'}}
        need ((get-value $lines 'v20-obv' $field) -ceq $expected) ('V20_STOPREPAIR_OBV_NOT_FLAT_'+$field)
    }
    Write-Output 'v20_stoprepair_preflight=pass_shallow_inside_exact_watching_sltp_obv_flat'
}
function stage-one([string]$key){
    $target=$files[$key]+'.watching-stage'
    if(Test-Path -LiteralPath $target){
        need ((blob $target) -ceq $new[$key]) ('V20_STOPREPAIR_STAGE_CONFLICT_'+$key)
        return
    }
    $b=Invoke-RestMethod -Uri ('https://api.github.com/repos/alkospacer123/market-pattern-discovery/git/blobs/'+$new[$key]) -Headers @{'user-agent'='v20lab'} -ErrorAction Stop
    need ($b.sha -ceq $new[$key] -and $b.encoding -ceq 'base64') ('V20_STOPREPAIR_SOURCE_MISMATCH_'+$key)
    [io.file]::WriteAllBytes($target,[convert]::FromBase64String($b.content))
    need ((blob $target) -ceq $new[$key]) ('V20_STOPREPAIR_STAGE_HASH_'+$key)
}
need ($env:OS -eq 'Windows_NT' -and $env:COMPUTERNAME -eq 'URIU-PC') 'V20_STOPREPAIR_WRONG_HOST'
need ((blob $diag) -ceq '34ee6bb057012b4f3c5c0348d95cbaec39bceaf6') 'V20_STOPREPAIR_DIAG_PIN_INVALID'
need ((blob $operator) -ceq 'b06957ea7833daeda65296eb372890951860c008') 'V20_STOPREPAIR_OPERATOR_PIN_INVALID'
$have=@{};foreach($key in $files.Keys){$have[$key]=blob $files[$key]}
$oldSet=@($files.Keys | Where-Object {$have[$_] -ceq $old[$_]}).Count -eq 3
$newSet=@($files.Keys | Where-Object {$have[$_] -ceq $new[$_]}).Count -eq 3
need ($oldSet -or $newSet) 'V20_STOPREPAIR_RELEASE_MIXED_OR_UNKNOWN'
if($newSet){Write-Output 'v20_stoprepair_update=already_installed';return}
broker-preflight
if($mode -eq 'verify'){Write-Output 'v20_stoprepair_verify=pass_no_changes';return}
$clock=[timezoneinfo]::ConvertTimeFromUtc([datetime]::UtcNow,[timezoneinfo]::FindSystemTimeZoneById('Russian Standard Time'))
$minutes=$clock.Hour*60+$clock.Minute
need ($minutes -ge 420 -and $minutes -lt 580) 'V20_STOPREPAIR_PROTECTED_INSTALL_ONLY_0700_TO_0940_MSK'
foreach($key in @('execution','worker','launcher')){stage-one $key}
Write-Output 'v20_stoprepair_stage=pass_3_of_3'
# Existing operator backup is SQLite WAL-safe and does not change task or switch.
& powershell.exe -noprofile -noninteractive -executionpolicy bypass -file $operator -mode backup -robot all
need ($LASTEXITCODE -eq 0) 'V20_STOPREPAIR_SQLITE_BACKUP_FAILED'
$backup=Join-Path (Join-Path $root 'backup-08') ('watching-stop-'+([datetimeoffset]::UtcNow).ToString('yyyyMMddTHHmmssZ'))
New-Item -ItemType Directory -Path $backup -ErrorAction Stop | Out-Null
foreach($key in @('execution','worker','launcher')){
    $dest=Join-Path $backup ([io.path]::GetFileName($files[$key]))
    Copy-Item -LiteralPath $files[$key] -Destination $dest -ErrorAction Stop
    need ((blob $dest) -ceq $old[$key]) ('V20_STOPREPAIR_BACKUP_HASH_'+$key)
}
Write-Output 'v20_stoprepair_backup=pass_3_of_3'
# Verify the SAME broker stop identities immediately before brief worker turnover.
broker-preflight
foreach($n in $names){Stop-ScheduledTask -TaskName $n -TaskPath '\' -ErrorAction Stop}
foreach($n in $names){
    for($i=0;$i -lt 40 -and (task-running $n);$i++){Start-Sleep -Seconds 1}
    need (-not (task-running $n)) ('V20_STOPREPAIR_TASK_STILL_RUNNING_'+$n)
}
$workers=@(Get-CimInstance Win32_Process -Filter "Name='python.exe' OR Name='pythonw.exe'" -ErrorAction Stop |
    Where-Object {$_.CommandLine -match 'V20_TradingSystem_M15[.]v20_runtime[.]finam_live' -and
                  $_.CommandLine -match '--robot\s+v20-(shallow|obv|inside)'})
need ($workers.Count -eq 0) 'V20_STOPREPAIR_WORKER_STILL_RUNNING'
foreach($key in @('execution','worker','launcher')){
    Copy-Item -LiteralPath ($files[$key]+'.watching-stage') -Destination $files[$key] -Force -ErrorAction Stop
    need ((blob $files[$key]) -ceq $new[$key]) ('V20_STOPREPAIR_NEW_HASH_'+$key)
}
Write-Output 'v20_stoprepair_runtime=pass_3_of_3'
$start=[datetimeoffset]::UtcNow
foreach($n in $names){Start-ScheduledTask -TaskName $n -TaskPath '\' -ErrorAction Stop}
foreach($n in $names){
    $p=Join-Path $root ('robots\'+$n.Substring(4)+'\logs\live-m15.jsonl')
    $fresh=$false
    for($i=0;$i -lt 60;$i++){
        $t=Get-ScheduledTask -TaskName $n -TaskPath '\' -ErrorAction Stop
        if($t.State -eq 'Running' -and (Test-Path -LiteralPath $p)){
            $last=Get-Content -LiteralPath $p -Tail 1 -Encoding UTF8 | ConvertFrom-Json
            $ts=[datetimeoffset]::Parse([string]$last.utc,[globalization.cultureinfo]::InvariantCulture)
            if($last.robot -eq $n -and $ts -ge $start.AddSeconds(-5)){
                need ([string]$last.state -eq 'HALTED_NO_NEW_ENTRIES' -or
                      [string]$last.state -in @('BROKER_FLAT_NO_ACTIVE_STOP','STOP_EXECUTED_FLAT')) ('V20_STOPREPAIR_FRESH_CYCLE_FAULT_'+$n+'_'+$last.state)
                $fresh=$true;break
            }
        }
        Start-Sleep -Seconds 1
    }
    need $fresh ('V20_STOPREPAIR_NO_FRESH_CYCLE_'+$n)
    Write-Output ('v20_stoprepair_'+$n+'=PASS_RECONCILED_HALTED_NO_NEW_ENTRIES')
}
Write-Output 'v20_stoprepair_cutover=pass_3_of_3_monitored_new_entries_remain_halted'
Write-Output ('v20_stoprepair_rollback_files='+$backup)
