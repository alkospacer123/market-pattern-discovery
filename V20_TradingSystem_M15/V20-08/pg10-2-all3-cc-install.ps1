# PG10.2 coordinated V20 all-three + Control Center package.
# No download, dependency install, deploy or command occurs in check mode.
[CmdletBinding()]
param(
    [ValidateSet('check','install','rollback')][string]$mode='check',
    [Parameter(Mandatory=$true)][string]$PackageRoot,
    [string]$BackupRoot=''
)
$ErrorActionPreference='Stop'
Set-StrictMode -Version Latest
$v20='C:\V20Lab'
$cc='C:\Control Center'
$panel=Join-Path $cc 'v20-preview-d80f2446'
$stage=Join-Path $v20 'pretrade-08\live-08'
$runtime=Join-Path $v20 'pretrade-08\live-runtime-08\V20_TradingSystem_M15\v20_runtime'
$robots=@('v20-shallow','v20-obv','v20-inside')
$manifestPath=Join-Path $PackageRoot 'pg10-2-release-manifest.json'
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
plain $PackageRoot
plain $manifestPath
$release=Get-Content -LiteralPath $manifestPath -Raw -Encoding UTF8 | ConvertFrom-Json
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
function verify-installed([bool]$requireNew){
    foreach($item in @($release.files|Where-Object {$_.install -ne 'none'})){
        $path=target ([string]$item.install) ([string]$item.source_path)
        if(-not (Test-Path -LiteralPath $path)){
            need (-not $requireNew -and ($item.allow_absent -eq $true -or @($item.accepted_installed_filtered).Count -eq 0)) ('PG10_2_INSTALLED_MISSING_'+$path)
            continue
        }
        plain $path
        $actual=filtered-blob $path ([string]$item.source_path)
        if($requireNew){need ($actual -ceq $item.filtered_git_blob) ('PG10_2_NEW_IDENTITY_MISMATCH_'+$path)}
        else{need (@($item.accepted_installed_filtered) -ccontains $actual) ('PG10_2_UNKNOWN_INSTALLED_IDENTITY_'+$path)}
    }
}
function backup-targets([string]$destination){
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
    $doc=[ordered]@{schema='pg10.2.backup.v1';created_utc=[datetimeoffset]::UtcNow.ToString('o');release=$release.schema;files=$records;state_restore='FORBIDDEN_AUTOMATICALLY'}
    [IO.File]::WriteAllText((Join-Path $destination 'backup.json'),($doc|ConvertTo-Json -Depth 6),[Text.UTF8Encoding]::new($false))
}
function restore-targets([string]$source){
    plain (Join-Path $source 'backup.json')
    $backup=Get-Content -LiteralPath (Join-Path $source 'backup.json') -Raw -Encoding UTF8|ConvertFrom-Json
    need ($backup.schema -ceq 'pg10.2.backup.v1' -and $backup.state_restore -ceq 'FORBIDDEN_AUTOMATICALLY') 'PG10_2_BACKUP_IDENTITY_INVALID'
    foreach($item in @($release.files|Where-Object {$_.install -ne 'none'})){
        $record=@($backup.files|Where-Object {$_.id -ceq $item.source_path -and $_.install -ceq $item.install})
        need ($record.Count -eq 1) ('PG10_2_BACKUP_RECORD_MISSING_'+$item.source_path)
        $path=target ([string]$item.install) ([string]$item.source_path)
        if($record[0].existed){
            $saved=Join-Path $source ([string]$record[0].file)
            plain $saved
            $bytes=[IO.File]::ReadAllBytes($saved)
            need ((sha256 $bytes) -ceq $record[0].raw_sha256 -and (raw-blob $saved) -ceq $record[0].raw_git_blob) 'PG10_2_BACKUP_FILE_INTEGRITY_FAILED'
            [IO.File]::WriteAllBytes($path,$bytes)
        }else{
            if(Test-Path -LiteralPath $path){
                plain $path
                need ((filtered-blob $path ([string]$item.source_path)) -ceq $item.filtered_git_blob) 'PG10_2_REFUSE_DELETE_UNKNOWN_FILE'
                [IO.File]::Delete($path)
            }
        }
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
$currentLauncher=Join-Path $stage 'v20-08-live-launch.ps1'
if($mode -eq 'install'){
    verify-installed $false
    all-halted
    broker-flat $currentLauncher
    need (-not [string]::IsNullOrWhiteSpace($BackupRoot) -and -not (Test-Path -LiteralPath $BackupRoot)) 'PG10_2_BACKUP_TARGET_INVALID'
    $oldOperator=Join-Path $stage 'v20-08-live-operator.ps1'
    $snapshot=@(& powershell.exe -noprofile -noninteractive -executionpolicy bypass -file $oldOperator -mode backup -robot all 2>&1)
    need ($LASTEXITCODE -eq 0 -and ($snapshot -join '|') -match 'v20_08_5_backup=PASS') 'PG10_2_SQLITE_BACKUP_FAILED'
    backup-targets $BackupRoot
    broker-flat $currentLauncher
    stop-all
    foreach($item in @($release.files|Where-Object {$_.install -ne 'none'})){
        $source=Join-Path $PackageRoot ([string]$item.package_path).Replace('/','\')
        $destination=target ([string]$item.install) ([string]$item.source_path)
        [IO.Directory]::CreateDirectory((Split-Path $destination -Parent))|Out-Null
        [IO.File]::WriteAllBytes($destination,[IO.File]::ReadAllBytes($source))
    }
    verify-installed $true
    foreach($name in $robots){[void](launcher $name 'verify' $currentLauncher)}
    start-halted
    Write-Output 'PG10_2_INSTALL=PASS_ALL3_AND_CC_RUNNING_HALTED_NO_AUTO_ARM'
    Write-Output ('PG10_2_ROLLBACK_BACKUP='+$BackupRoot)
    Write-Output 'PG10_2_SQLITE_INTENTS_CC_JOURNALS=RETAINED_NOT_RESTORED'
    return
}
need (-not [string]::IsNullOrWhiteSpace($BackupRoot) -and (Test-Path -LiteralPath $BackupRoot -PathType Container)) 'PG10_2_ROLLBACK_SOURCE_INVALID'
verify-installed $true
all-halted
broker-flat $currentLauncher
stop-all
restore-targets $BackupRoot
verify-installed $false
foreach($name in $robots){[void](launcher $name 'verify' $currentLauncher)}
start-halted
Write-Output 'PG10_2_ROLLBACK=PASS_CODE_ONLY_RUNNING_HALTED_NO_AUTO_ARM'
Write-Output 'PG10_2_DURABLE_STATE_AND_UNKNOWN_INTENTS=UNTOUCHED'
