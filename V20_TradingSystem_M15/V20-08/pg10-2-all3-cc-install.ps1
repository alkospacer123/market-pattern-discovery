# PG10.2 coordinated V20 all-three + Control Center package.
# No download, dependency install, deploy or command occurs in check mode.
[CmdletBinding()]
param(
    [ValidateSet('check','install','rollback','recover')][string]$mode='check',
    [Parameter(Mandatory=$true)][string]$PackageRoot,
    [string]$BackupRoot='',
    [string]$RecoveryPhrase=''
)
$ErrorActionPreference='Stop'
Set-StrictMode -Version Latest
$v20='C:\V20Lab'
$cc='C:\Control Center'
$panel=Join-Path $cc 'v20-preview-d80f2446'
$stage=Join-Path $v20 'pretrade-08\live-08'
$runtime=Join-Path $v20 'pretrade-08\live-runtime-08\V20_TradingSystem_M15\v20_runtime'
$pythonCC=Join-Path $cc 'venv\Scripts\python.exe'
$pythonBaseCC=Join-Path $cc 'runtime\python312\python.exe'
$robots=@('v20-shallow','v20-obv','v20-inside')
$manifestPath=Join-Path $PackageRoot 'pg10-2-release-manifest.json'
$ccMutex=$null
$ccMutexHeld=$false
function need([bool]$ok,[string]$code){if(-not $ok){throw $code}}
function plain([string]$path){
    need (Test-Path -LiteralPath $path) ('PG10_2_PATH_MISSING_'+$path)
    need (-not ((Get-Item -LiteralPath $path -Force).Attributes -band [IO.FileAttributes]::ReparsePoint)) ('PG10_2_REPARSE_FORBIDDEN_'+$path)
}
function sha256([byte[]]$bytes){
    $h=[Security.Cryptography.SHA256]::Create()
    try{return ([BitConverter]::ToString($h.ComputeHash($bytes))).Replace('-','').ToLowerInvariant()}finally{$h.Dispose()}
}
function raw-blob([string]$path){
    $value=(& git.exe hash-object --no-filters -- $path).Trim().ToLowerInvariant()
    need ($LASTEXITCODE -eq 0) 'PG10_2_RAW_HASH_FAILED'
    return $value
}
function filtered-blob([string]$path,[string]$sourcePath){
    $value=(& git.exe -c core.autocrlf=false hash-object --path=$sourcePath -- $path).Trim().ToLowerInvariant()
    need ($LASTEXITCODE -eq 0) 'PG10_2_FILTERED_HASH_FAILED'
    return $value
}
function target([string]$kind,[string]$sourcePath){
    $name=Split-Path $sourcePath -Leaf
    if($kind -eq 'v20_runtime'){return Join-Path $runtime $name}
    if($kind -eq 'v20_stage'){return Join-Path $stage $name}
    if($kind -eq 'cc_panel'){return Join-Path $panel ($sourcePath.Substring('ControlCenter/'.Length).Replace('/','\'))}
    if($kind -eq 'cc_controller'){return Join-Path $cc 'cc07-operator\cc07-v20-operator.ps1'}
    if($kind -eq 'none'){return ''}
    throw 'PG10_2_INSTALL_TARGET_INVALID'
}
function write-json([string]$path,$document,[bool]$replace=$false){
    $bytes=[Text.UTF8Encoding]::new($false).GetBytes(($document|ConvertTo-Json -Depth 8))
    $temp=$path+'.'+[guid]::NewGuid().ToString('N')+'.tmp'
    $stream=[IO.FileStream]::new($temp,[IO.FileMode]::CreateNew,[IO.FileAccess]::Write,[IO.FileShare]::None)
    try{$stream.Write($bytes,0,$bytes.Length);$stream.Flush($true)}finally{$stream.Dispose()}
    try{
        if(Test-Path -LiteralPath $path){
            need $replace 'PG10_2_JSON_TARGET_EXISTS'
            $backupCopy=$temp+'.backup'
            [IO.File]::Replace($temp,$path,$backupCopy)
            if(Test-Path -LiteralPath $backupCopy){[IO.File]::Delete($backupCopy)}
        }else{[IO.File]::Move($temp,$path)}
    }finally{if(Test-Path -LiteralPath $temp){[IO.File]::Delete($temp)}}
}
plain $PackageRoot
plain $manifestPath
$release=Get-Content -LiteralPath $manifestPath -Raw -Encoding UTF8 | ConvertFrom-Json
$releaseSha=sha256 ([IO.File]::ReadAllBytes($manifestPath))
need ($release.schema -ceq 'pg10.2.release.v1' -and
      $release.baseline_commit -ceq '568b339a1bb3ebc3f025d74762ae66c344278be9' -and
      $release.filter_profile -ceq 'core.autocrlf=false;LF' -and
      @($release.robots).Count -eq 3) 'PG10_2_MANIFEST_IDENTITY_INVALID'
function verify-package{
    foreach($item in @($release.files)+@($release.ordered_patches)){
        $relative=[string]$item.package_path
        $path=Join-Path $PackageRoot $relative.Replace('/','\')
        plain $path
        $bytes=[IO.File]::ReadAllBytes($path)
        need ((sha256 $bytes) -ceq $item.raw_sha256) ('PG10_2_RAW_SHA256_MISMATCH_'+$relative)
        need ((raw-blob $path) -ceq $item.raw_git_blob) ('PG10_2_RAW_GIT_BLOB_MISMATCH_'+$relative)
        need ((filtered-blob $path ([string]$item.source_path)) -ceq $item.filtered_git_blob) ('PG10_2_FILTERED_GIT_BLOB_MISMATCH_'+$relative)
    }
    $orders=@($release.ordered_patches|ForEach-Object {[int]$_.order})
    need (($orders -join ',') -ceq '1,2,3,4,5,6,7,8,9,10,11') 'PG10_2_PATCH_ORDER_INVALID'
}
function switch-state([string]$name){
    $path=Join-Path $v20 ('robots\'+$name.Substring(4)+'\safety\stage8-trading-kill-switch.json')
    plain $path
    return [string](Get-Content -LiteralPath $path -Raw -Encoding UTF8|ConvertFrom-Json).state
}
function task([string]$name){return Get-ScheduledTask -TaskName $name -TaskPath '\' -ErrorAction Stop}
function launcher([string]$name,[string]$action,[string]$path){
    $rows=@(& powershell.exe -noprofile -noninteractive -executionpolicy bypass -file $path -mode $action -robot $name 2>&1)
    need ($LASTEXITCODE -eq 0) ('PG10_2_LAUNCHER_'+$action+'_FAILED_'+$name)
    return $rows
}
function broker-flat([string]$path){
    foreach($name in $robots){
        $rows=@(launcher $name 'readonly' $path)
        need (($rows -join '|') -match 'v20_08_4_positions=0' -and
              ($rows -join '|') -match 'v20_08_4_active_orders=0' -and
              ($rows -join '|') -match 'v20_08_4_order_posts=zero') ('PG10_2_BROKER_FLAT_NOT_PROVEN_'+$name)
    }
}
function all-halted{foreach($name in $robots){need ((switch-state $name) -ceq 'HALTED') ('PG10_2_NOT_HALTED_'+$name)}}
function stop-all{
    foreach($name in $robots){if((task $name).State -eq 'Running'){Stop-ScheduledTask -TaskName $name -TaskPath '\' -ErrorAction Stop}}
    for($i=0;$i -lt 30;$i++){
        if(@($robots|Where-Object {(task $_).State -eq 'Running'}).Count -eq 0){return}
        Start-Sleep -Seconds 1
    }
    throw 'PG10_2_WORKERS_NOT_QUIESCENT'
}
function start-halted{
    foreach($name in $robots){if((task $name).State -ne 'Running'){Start-ScheduledTask -TaskName $name -TaskPath '\' -ErrorAction Stop}}
    $started=[datetimeoffset]::UtcNow
    for($i=0;$i -lt 55;$i++){
        $valid=0
        foreach($name in $robots){
            $path=Join-Path $v20 ('robots\'+$name.Substring(4)+'\logs\live-m15.jsonl')
            try{
                $row=Get-Content -LiteralPath $path -Tail 1 -Encoding UTF8|ConvertFrom-Json
                $at=[datetimeoffset]::Parse([string]$row.utc)
                if($row.robot -eq $name -and $row.state -eq 'HALTED_NO_NEW_ENTRIES' -and $at -ge $started.AddSeconds(-5)){$valid++}
            }catch{}
        }
        if($valid -eq 3){all-halted;return}
        Start-Sleep -Seconds 1
    }
    throw 'PG10_2_FRESH_HALTED_CYCLES_NOT_PROVEN'
}
function installed-identity($item,[string]$path){
    $bytes=[IO.File]::ReadAllBytes($path)
    $raw=raw-blob $path
    if($raw -ceq $item.raw_git_blob){
        need ((sha256 $bytes) -ceq $item.raw_sha256) 'PG10_2_CANONICAL_PACKAGE_IDENTITY_CONTRADICTION'
        return 'NEW'
    }
    if(($item.PSObject.Properties.Name -contains 'accepted_installed_old_raw') -and
       @($item.accepted_installed_old_raw) -ccontains $raw){return 'OLD'}
    $filtered=filtered-blob $path ([string]$item.source_path)
    $old=@($item.accepted_installed_filtered|Where-Object {$_ -cne $item.filtered_git_blob})
    if($old -ccontains $filtered){return 'OLD'}
    return 'UNKNOWN'
}
function verify-installed([bool]$requireNew){
    foreach($item in @($release.files|Where-Object {$_.install -ne 'none'})){
        $path=target ([string]$item.install) ([string]$item.source_path)
        if(-not (Test-Path -LiteralPath $path)){
            need (-not $requireNew -and ($item.allow_absent -eq $true -or @($item.accepted_installed_filtered).Count -eq 0)) ('PG10_2_INSTALLED_MISSING_'+$path)
            continue
        }
        plain $path
        $actual=installed-identity $item $path
        if($requireNew){need ($actual -ceq 'NEW') ('PG10_2_NEW_IDENTITY_MISMATCH_'+$path)}
        else{need ($actual -in @('OLD','NEW')) ('PG10_2_UNKNOWN_INSTALLED_IDENTITY_'+$path)}
    }
}
function backup-record($backup,[string]$id){
    $rows=@($backup.files|Where-Object {$_.id -ceq $id})
    need ($rows.Count -eq 1) ('PG10_2_BACKUP_RECORD_MISSING_'+$id)
    return $rows[0]
}
function backup-verify([string]$source){
    plain (Join-Path $source 'backup.json')
    $backup=Get-Content -LiteralPath (Join-Path $source 'backup.json') -Raw -Encoding UTF8|ConvertFrom-Json
    need ($backup.schema -ceq 'pg10.2.backup.v1' -and
          $backup.release_sha256 -ceq $releaseSha -and
          $backup.state_restore -ceq 'FORBIDDEN_AUTOMATICALLY' -and
          $backup.PSObject.Properties.Name -contains 'coherent_before') 'PG10_2_BACKUP_IDENTITY_INVALID'
    $expected=@($release.files|Where-Object {$_.install -ne 'none'})
    need (@($backup.files).Count -eq $expected.Count) 'PG10_2_BACKUP_FILE_COUNT_INVALID'
    foreach($item in $expected){
        $record=backup-record $backup ([string]$item.source_path)
        need ($record.install -ceq $item.install) 'PG10_2_BACKUP_TARGET_MISMATCH'
        if($record.existed){
            $name=[string]$record.file
            need ([IO.Path]::GetFileName($name) -ceq $name -and $name.Length -gt 0) 'PG10_2_BACKUP_PATH_INVALID'
            $saved=Join-Path $source $name
            plain $saved
            $bytes=[IO.File]::ReadAllBytes($saved)
            need ((sha256 $bytes) -ceq $record.raw_sha256 -and (raw-blob $saved) -ceq $record.raw_git_blob) 'PG10_2_BACKUP_FILE_INTEGRITY_FAILED'
        }
    }
    return $backup
}
function backup-targets([string]$destination,[bool]$coherent){
    [IO.Directory]::CreateDirectory($destination)|Out-Null
    $records=@()
    $index=0
    foreach($item in @($release.files|Where-Object {$_.install -ne 'none'})){
        $index++
        $path=target ([string]$item.install) ([string]$item.source_path)
        $exists=Test-Path -LiteralPath $path
        $record=[ordered]@{id=[string]$item.source_path;install=[string]$item.install;existed=$exists;file='';raw_sha256='';raw_git_blob=''}
        if($exists){
            plain $path
            $bytes=[IO.File]::ReadAllBytes($path)
            $name=('{0:D2}-{1}' -f $index,(Split-Path $path -Leaf))
            [IO.File]::WriteAllBytes((Join-Path $destination $name),$bytes)
            $record.file=$name;$record.raw_sha256=sha256 $bytes;$record.raw_git_blob=raw-blob (Join-Path $destination $name)
        }
        $records+=[pscustomobject]$record
    }
    $doc=[ordered]@{schema='pg10.2.backup.v1';created_utc=[datetimeoffset]::UtcNow.ToString('o');release=$release.schema;release_sha256=$releaseSha;coherent_before=$coherent;files=$records;state_restore='FORBIDDEN_AUTOMATICALLY'}
    write-json (Join-Path $destination 'backup.json') $doc $false
    [void](backup-verify $destination)
}
function transaction-path{return Join-Path $BackupRoot 'transaction.json'}
function transaction-read{
    $path=transaction-path
    plain $path
    $tx=Get-Content -LiteralPath $path -Raw -Encoding UTF8|ConvertFrom-Json
    need ($tx.schema -ceq 'pg10.2.install-transaction.v1' -and
          $tx.id -cmatch '^[a-f0-9]{32}$' -and $tx.release_sha256 -ceq $releaseSha -and
          $tx.status -cin @('PREPARED','INSTALLING','INTERRUPTED','CODE_INSTALLED','COMPLETED','RECOVERED','ROLLED_BACK') -and
          $tx.PSObject.Properties.Name -contains 'coherent_before') 'PG10_2_TRANSACTION_INVALID'
    $backup=backup-verify $BackupRoot
    need ((sha256 ([IO.File]::ReadAllBytes((Join-Path $BackupRoot 'backup.json')))) -ceq $tx.backup_sha256) 'PG10_2_TRANSACTION_BACKUP_MISMATCH'
    need ($tx.coherent_before -eq $backup.coherent_before) 'PG10_2_TRANSACTION_COHERENCE_MISMATCH'
    return $tx
}
function transaction-write($tx,[string]$status){
    $tx.status=$status
    $tx.updated_utc=[datetimeoffset]::UtcNow.ToString('o')
    write-json (transaction-path) $tx $true
}
function identity-state{
    $launcherItem=@($release.files|Where-Object {$_.role -ceq 'LAUNCHER'})
    need ($launcherItem.Count -eq 1) 'PG10_2_LAUNCHER_MANIFEST_INVALID'
    $currentLauncher=target 'v20_stage' ([string]$launcherItem[0].source_path)
    if(-not (Test-Path -LiteralPath $currentLauncher)){return 'MISSING'}
    $launcherState=installed-identity $launcherItem[0] $currentLauncher
    if($launcherState -notin @('OLD','NEW')){return 'MIXED'}
    $old=$launcherState -ceq 'OLD';$new=$launcherState -ceq 'NEW'
    foreach($item in @($release.files|Where-Object {$_.role -ceq 'DERIVED_BASE_PLUS_11'})){
        $path=target 'v20_runtime' ([string]$item.source_path)
        if(-not (Test-Path -LiteralPath $path)){return 'MISSING'}
        $actual=installed-identity $item $path
        $old=$old -and $actual -ceq 'OLD'
        $new=$new -and $actual -ceq 'NEW'
    }
    if($new){return 'NEW'}
    if($old){return 'OLD'}
    return 'MIXED'
}
function broker-flat-for-state([string]$state,[string]$transactionId){
    if($state -in @('OLD','NEW')){
        broker-flat (Join-Path $stage 'v20-08-live-launch.ps1')
        return
    }
    $expected='PG10_2_EXTERNAL_FINAM_READONLY_FLAT_CONFIRMED '+$transactionId
    need ($RecoveryPhrase -ceq $expected) 'PG10_2_MIXED_RUNTIME_REQUIRES_EXTERNAL_FINAM_READONLY_FLAT'
}
function assert-targets-known($backup){
    foreach($item in @($release.files|Where-Object {$_.install -ne 'none'})){
        $record=backup-record $backup ([string]$item.source_path)
        $path=target ([string]$item.install) ([string]$item.source_path)
        if(-not (Test-Path -LiteralPath $path)){
            need (-not $record.existed) ('PG10_2_TARGET_DISAPPEARED_'+$item.source_path)
            continue
        }
        plain $path
        $actual=sha256 ([IO.File]::ReadAllBytes($path))
        $old=$record.existed -and $actual -ceq $record.raw_sha256
        $new=$actual -ceq $item.raw_sha256
        need ($old -or $new) ('PG10_2_UNKNOWN_TARGET_BYTES_'+$item.source_path)
    }
}
function assert-restore-compatible{
    $private=Join-Path $cc 'data\private'
    foreach($name in @('cc07-requests','cc07-release-history')){
        $folder=Join-Path $private $name
        if((Test-Path -LiteralPath $folder) -and @(Get-ChildItem -LiteralPath $folder -File).Count -gt 0){
            throw 'PG10_2_ROLLBACK_NEW_RECOVERY_JOURNALS_FORWARD_RECOVERY_REQUIRED'
        }
    }
    $auditArchive=Join-Path $cc 'data\control-audit\archive'
    if((Test-Path -LiteralPath $auditArchive) -and @(Get-ChildItem -LiteralPath $auditArchive -File).Count -gt 0){
        throw 'PG10_2_ROLLBACK_ROTATED_AUDIT_FORWARD_RECOVERY_REQUIRED'
    }
    foreach($name in $robots){
        $archive=Join-Path $v20 ('robots\'+$name.Substring(4)+'\logs\archive')
        if((Test-Path -LiteralPath $archive) -and @(Get-ChildItem -LiteralPath $archive -File).Count -gt 0){
            throw 'PG10_2_ROLLBACK_ROTATED_LIVE_LOG_FORWARD_RECOVERY_REQUIRED'
        }
    }
}
function cc-process([int]$processId){
    $rows=@(Get-CimInstance Win32_Process -Filter ('ProcessId='+$processId))
    need ($rows.Count -eq 1) 'PG10_2_CC_PROCESS_MISSING'
    $process=$rows[0]
    $launcher=$process.ExecutablePath -ceq $pythonCC
    $base=$process.ExecutablePath -ceq $pythonBaseCC
    if($base){
        $parent=@(Get-CimInstance Win32_Process -Filter ('ProcessId='+$process.ParentProcessId))
        if($parent.Count -eq 1 -and $parent[0].ExecutablePath -ceq $pythonCC){
            need ($parent[0].CommandLine -match '(?i)streamlit\s+run\s+(?:\S+\s+)*v20_app\.py' -and
                  $parent[0].CommandLine -match '(?i)--server\.port(?:=|\s+)8502(?:\s|$)') 'PG10_2_CC_PARENT_IDENTITY_INVALID'
        }
    }
    need ($launcher -or $base) 'PG10_2_CC_PROCESS_EXECUTABLE_INVALID'
    need ($process.CommandLine -match '(?i)streamlit\s+run\s+(?:\S+\s+)*v20_app\.py' -and
          $process.CommandLine -match '(?i)--server\.port(?:=|\s+)8502(?:\s|$)') 'PG10_2_CC_PROCESS_IDENTITY_INVALID'
    return $process
}
function cc-listener{
    $rows=@(Get-NetTCPConnection -LocalAddress '127.0.0.1' -LocalPort 8502 -State Listen -ErrorAction SilentlyContinue)
    if($rows.Count -eq 0){return $null}
    need ($rows.Count -eq 1) 'PG10_2_CC_MULTIPLE_LISTENERS'
    return $rows[0]
}
function cc-running{
    $listener=cc-listener
    if($null -eq $listener){return 0}
    [void](cc-process ([int]$listener.OwningProcess))
    return [int]$listener.OwningProcess
}
function enter-command-quiescence{
    $script:ccMutex=[Threading.Mutex]::new($false,'Global\ControlCenter_CC07_V20')
    try{$script:ccMutexHeld=$script:ccMutex.WaitOne(0)}catch [Threading.AbandonedMutexException]{throw 'PG10_2_CC_MUTEX_ABANDONED'}
    need $script:ccMutexHeld 'PG10_2_CC_COMMAND_IN_PROGRESS'
    $children=@(Get-CimInstance Win32_Process|Where-Object {$_.CommandLine -match '(?i)cc07-v20-operator\.ps1'})
    need ($children.Count -eq 0) 'PG10_2_CC_OPERATOR_CHILD_ACTIVE'
}
function leave-command-quiescence{
    if($script:ccMutexHeld){$script:ccMutex.ReleaseMutex();$script:ccMutexHeld=$false}
    if($null -ne $script:ccMutex){$script:ccMutex.Dispose();$script:ccMutex=$null}
}
function stop-cc{
    $processId=cc-running
    if($processId -eq 0){return $false}
    [void](cc-process $processId)
    Stop-Process -Id $processId -ErrorAction Stop
    for($i=0;$i -lt 30;$i++){
        if($null -eq (cc-listener)){return $true}
        Start-Sleep -Seconds 1
    }
    throw 'PG10_2_CC_LISTENER_STILL_ACTIVE'
}
function started-listener($listener,$process){
    if($null -eq $listener){return $false}
    if([int]$listener.OwningProcess -eq $process.Id){return $true}
    $owner=@(Get-CimInstance Win32_Process -Filter ('ProcessId='+$listener.OwningProcess))
    return ($owner.Count -eq 1 -and [int]$owner[0].ParentProcessId -eq $process.Id)
}
function start-cc([bool]$expectedNew,$backup,$tx){
    if(-not $tx.cc_was_running){
        need ($null -eq (cc-listener)) 'PG10_2_CC_UNEXPECTED_LISTENER'
        Write-Output 'PG10_2_CC=STOPPED_PREEXISTING_NO_AUTO_START'
        return
    }
    plain $pythonCC
    $stdout=Join-Path $BackupRoot ('cc-'+$tx.id+'-stdout.log')
    $stderr=Join-Path $BackupRoot ('cc-'+$tx.id+'-stderr.log')
    $arguments=@('-I','-B','-m','streamlit','run','v20_app.py','--server.address=127.0.0.1','--server.port=8502','--server.enableCORS=true','--server.enableXsrfProtection=true','--server.headless=true')
    $process=Start-Process -FilePath $pythonCC -ArgumentList $arguments -WorkingDirectory $panel -WindowStyle Hidden -RedirectStandardOutput $stdout -RedirectStandardError $stderr -PassThru
    $listener=$null
    for($i=0;$i -lt 60;$i++){
        $listener=cc-listener
        if(started-listener $listener $process){break}
        if($process.HasExited){throw 'PG10_2_CC_PROCESS_EXITED'}
        Start-Sleep -Seconds 1
    }
    need (started-listener $listener $process) 'PG10_2_CC_NEW_LISTENER_NOT_PROVEN'
    [void](cc-process ([int]$listener.OwningProcess))
    $health=Invoke-WebRequest -Uri 'http://127.0.0.1:8502/_stcore/health' -UseBasicParsing -TimeoutSec 5
    need ($health.StatusCode -eq 200 -and [string]$health.Content -match '(?i)^\s*ok\s*$') 'PG10_2_CC_HEALTH_NOT_PROVEN'
    if($expectedNew){verify-installed $true}else{verify-backup-installed $backup}
    Write-Output ('PG10_2_CC_RUNNING=PASS_NEW_PROCESS_LOOPBACK_HEALTH_AND_'+$(if($expectedNew){'NEW'}else{'BACKUP'})+'_SOURCE_IDS')
}
function replace-target([string]$destination,[byte[]]$bytes){
    $temp=$destination+'.'+[guid]::NewGuid().ToString('N')+'.tmp'
    $stream=[IO.FileStream]::new($temp,[IO.FileMode]::CreateNew,[IO.FileAccess]::Write,[IO.FileShare]::None)
    try{$stream.Write($bytes,0,$bytes.Length);$stream.Flush($true)}finally{$stream.Dispose()}
    try{
        if(Test-Path -LiteralPath $destination){
            $backupCopy=$temp+'.backup'
            [IO.File]::Replace($temp,$destination,$backupCopy)
            if(Test-Path -LiteralPath $backupCopy){[IO.File]::Delete($backupCopy)}
        }
        else{[IO.File]::Move($temp,$destination)}
    }finally{if(Test-Path -LiteralPath $temp){[IO.File]::Delete($temp)}}
}
function install-file($item,$tx){
    $source=Join-Path $PackageRoot ([string]$item.package_path).Replace('/','\')
    $destination=target ([string]$item.install) ([string]$item.source_path)
    [IO.Directory]::CreateDirectory((Split-Path $destination -Parent))|Out-Null
    $bytes=[IO.File]::ReadAllBytes($source)
    need ((sha256 $bytes) -ceq $item.raw_sha256) 'PG10_2_INSTALL_SOURCE_CHANGED'
    replace-target $destination $bytes
    $tx.last_write_id=[string]$item.source_path
    transaction-write $tx 'INSTALLING'
}
function restore-targets([string]$source,$backup){
    assert-targets-known $backup
    foreach($item in @($release.files|Where-Object {$_.install -ne 'none'})){
        $record=backup-record $backup ([string]$item.source_path)
        $path=target ([string]$item.install) ([string]$item.source_path)
        if($record.existed){
            $saved=Join-Path $source ([string]$record.file)
            replace-target $path ([IO.File]::ReadAllBytes($saved))
        }elseif(Test-Path -LiteralPath $path){
            plain $path
            need ((sha256 ([IO.File]::ReadAllBytes($path))) -ceq $item.raw_sha256) 'PG10_2_REFUSE_DELETE_UNKNOWN_FILE'
            [IO.File]::Delete($path)
        }
    }
}
function verify-backup-installed($backup){
    assert-targets-known $backup
    foreach($item in @($release.files|Where-Object {$_.install -ne 'none'})){
        $record=backup-record $backup ([string]$item.source_path)
        $path=target ([string]$item.install) ([string]$item.source_path)
        if($record.existed){
            plain $path
            need ((sha256 ([IO.File]::ReadAllBytes($path))) -ceq $record.raw_sha256) 'PG10_2_RESTORED_IDENTITY_MISMATCH'
        }else{need (-not (Test-Path -LiteralPath $path)) 'PG10_2_NEW_FILE_STILL_PRESENT'}
    }
}
verify-package
if($mode -eq 'check'){
    verify-installed $false
    foreach($name in $robots){[void](task $name);[void](switch-state $name)}
    Write-Output 'PG10_2_CHECK=PASS_PACKAGE_AND_KNOWN_OLD_OR_NEW_INSTALLED_BYTES_ONLY'
    Write-Output 'PG10_2_LIVE_BROKER_PROTECTION=NOT_CHECKED'
    return
}
need ($env:OS -eq 'Windows_NT' -and $env:COMPUTERNAME -eq 'URIU-PC') 'PG10_2_WRONG_INTEL'
$identity=[Security.Principal.WindowsPrincipal]::new([Security.Principal.WindowsIdentity]::GetCurrent())
need ($identity.IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)) 'PG10_2_ADMIN_REQUIRED'
need (-not [string]::IsNullOrWhiteSpace($BackupRoot)) 'PG10_2_BACKUP_REQUIRED'
$currentLauncher=Join-Path $stage 'v20-08-live-launch.ps1'
if($mode -eq 'install'){
    verify-installed $false
    all-halted
    $resume=Test-Path -LiteralPath $BackupRoot
    $state=identity-state
    if($resume){
        $backup=backup-verify $BackupRoot
        $tx=transaction-read
        assert-targets-known $backup
        Write-Output ('PG10_2_INSTALL_RESUME_TRANSACTION='+$tx.id)
    }else{
        $oldOperator=Join-Path $stage 'v20-08-live-operator.ps1'
        $snapshot=@(& powershell.exe -noprofile -noninteractive -executionpolicy bypass -file $oldOperator -mode backup -robot all 2>&1)
        need ($LASTEXITCODE -eq 0 -and ($snapshot -join '|') -match 'v20_08_5_backup=PASS') 'PG10_2_SQLITE_BACKUP_FAILED'
        backup-targets $BackupRoot ($state -in @('OLD','NEW'))
        $ccWasRunning=(cc-running) -ne 0
        $tx=[ordered]@{schema='pg10.2.install-transaction.v1';id=[guid]::NewGuid().ToString('N');release_sha256=$releaseSha;backup_sha256=sha256 ([IO.File]::ReadAllBytes((Join-Path $BackupRoot 'backup.json')));status='PREPARED';coherent_before=($state -in @('OLD','NEW'));cc_was_running=$ccWasRunning;last_write_id='';created_utc=[datetimeoffset]::UtcNow.ToString('o');updated_utc=[datetimeoffset]::UtcNow.ToString('o')}
        write-json (transaction-path) $tx $false
        $tx=transaction-read
    }
    try{
        broker-flat-for-state $state $tx.id
        enter-command-quiescence
        [void](stop-cc)
        stop-all
        broker-flat-for-state $state $tx.id
        transaction-write $tx 'INSTALLING'
        foreach($item in @($release.files|Where-Object {$_.install -ne 'none'})){install-file $item $tx}
        verify-installed $true
        broker-flat $currentLauncher
        transaction-write $tx 'CODE_INSTALLED'
        foreach($name in $robots){[void](launcher $name 'verify' $currentLauncher)}
        start-halted
        start-cc $true $null $tx
        transaction-write $tx 'COMPLETED'
        Write-Output 'PG10_2_INSTALL=PASS_ALL3_RUNNING_HALTED_NO_AUTO_ARM'
        Write-Output ('PG10_2_ROLLBACK_BACKUP='+$BackupRoot)
        Write-Output 'PG10_2_SQLITE_INTENTS_CC_JOURNALS=RETAINED_NOT_RESTORED'
    }catch{
        transaction-write $tx 'INTERRUPTED'
        throw
    }finally{leave-command-quiescence}
    return
}
need (Test-Path -LiteralPath $BackupRoot -PathType Container) 'PG10_2_RECOVERY_SOURCE_INVALID'
$backup=backup-verify $BackupRoot
$tx=transaction-read
need ($tx.coherent_before -eq $true) 'PG10_2_RECOVERY_POINT_NOT_COHERENT_FORWARD_INSTALL_REQUIRED'
if($mode -eq 'rollback'){need ($tx.status -ceq 'COMPLETED') 'PG10_2_INTERRUPTED_INSTALL_USE_RECOVER'}
assert-targets-known $backup
all-halted
$state=identity-state
broker-flat-for-state $state $tx.id
assert-restore-compatible
try{
    enter-command-quiescence
    [void](stop-cc)
    stop-all
    broker-flat-for-state $state $tx.id
    restore-targets $BackupRoot $backup
    verify-backup-installed $backup
    foreach($name in $robots){[void](launcher $name 'verify' $currentLauncher)}
    start-halted
    start-cc $false $backup $tx
    transaction-write $tx $(if($mode -eq 'recover'){'RECOVERED'}else{'ROLLED_BACK'})
    Write-Output $(if($mode -eq 'recover'){'PG10_2_RECOVER=PASS_KNOWN_BYTES_RUNNING_HALTED_NO_AUTO_ARM'}else{'PG10_2_ROLLBACK=PASS_CODE_ONLY_RUNNING_HALTED_NO_AUTO_ARM'})
    Write-Output 'PG10_2_DURABLE_STATE_AND_UNKNOWN_INTENTS=UNTOUCHED'
}finally{leave-command-quiescence}
