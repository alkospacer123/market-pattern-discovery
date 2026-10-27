# V20-08.5 focused recovery: FINAM temporary GET 5xx, 27.10.2026.
# Requires all three V20 Tasks Ready, switches HALTED, FINAM flat 3/3.
# First broker GET-only and live SQLite online backup. No change to H1/M15.
[CmdletBinding()]
param([ValidateSet('verify','recover')][string]$mode='verify')
$ErrorActionPreference='Stop'
Set-StrictMode -Version Latest
$root='C:\V20Lab'
$stage=Join-Path $root 'pretrade-08\live-08'
$launcher=Join-Path $stage 'v20-08-live-launch.ps1'
$operator=Join-Path $stage 'v20-08-live-operator.ps1'
$module=Join-Path $root 'pretrade-08\live-runtime-08\V20_TradingSystem_M15\v20_runtime\finam_live.py'
$names=@('v20-shallow','v20-obv','v20-inside')
$oldModule='fa256995f5f4f100f380fb952f51e2671ba31120'
$newModule='e39a00267c91ea35dbe83d27b26d6b62179b2429'
$oldLauncher='c161a15d87c2bfc85939f4f570b3f79013c3c665'
$newLauncher='5193f70e2c5663077e35653b89f4c28201ff04cb'
$oldOperator='23cd63a460e4e5af17b07e9953e3b14695509cb3'
$newOperator='e0fd05423899a02fee5861a176b0f72f7ee3bf5c'
$expectedSource='dd55f201b3e9a92ce5fa3f927289f5a5ef89366d'
function need([bool]$pass,[string]$reason){if(-not $pass){throw $reason}}
function hash([string]$path){
    need (Test-Path -LiteralPath $path -PathType Leaf) 'V20_08_5_RECOVERY_SOURCE_MISSING'
    $item=Get-Item -LiteralPath $path -Force
    need (-not ($item.Attributes -band [IO.FileAttributes]::ReparsePoint)) 'V20_08_5_RECOVERY_LINK_FORBIDDEN'
    $value=(& git.exe hash-object -- $path).Trim().ToLowerInvariant()
    need ($LASTEXITCODE -eq 0) 'V20_08_5_RECOVERY_HASH_ERROR'
    return $value
}
function sidof([string]$name){
    try {
        if($name -match '^S-[0-9]+(-[0-9]+)+$'){return ([Security.Principal.SecurityIdentifier]::new($name)).Value}
        return ([Security.Principal.NTAccount]::new($name)).Translate([Security.Principal.SecurityIdentifier]).Value
    }catch{return ''}
}
function exact-task([string]$name){
    $task=Get-ScheduledTask -TaskName $name -TaskPath '\' -ErrorAction Stop
    $args='-noprofile -noninteractive -executionpolicy bypass -file "'+$launcher+'" -mode run -robot '+$name
    $dir=Join-Path $root ('robots\'+$name.Substring(4))
    need ($task.State -eq 'Ready' -and
          @($task.Actions).Count -eq 1 -and
          $task.Actions[0].Execute -ieq 'powershell.exe' -and
          $task.Actions[0].Arguments -ieq $args -and
          $task.Actions[0].WorkingDirectory -ieq $dir -and
          (sidof ([string]$task.Principal.UserId)) -eq $sid) 'V20_08_5_RECOVERY_TASK_NOT_READY'
}
function readflat([string]$name) {
    $lines=@(& powershell.exe -noprofile -noninteractive -executionpolicy bypass -file $launcher -mode readonly -robot $name 2>&1)
    need ($LASTEXITCODE -eq 0 -and
          ($lines -join '|') -match ('v20_08_4_readonly='+$name+' ACCOUNT_BOUND') -and
          ($lines -join '|') -match 'v20_08_4_positions=0' -and
          ($lines -join '|') -match 'v20_08_4_active_orders=0' -and
          ($lines -join '|') -match 'v20_08_4_order_posts=zero') 'V20_08_5_RECOVERY_FINAM_NOT_CLEAN'
    Write-Output ('v20_08_5_recovery_'+$name+'_finam=PASS_GET_ONLY_FLAT')
}
function patch-file([string]$path,[string]$old,[string]$new){
    $actual=hash $path
    if($actual -eq $new){return}
    need ($actual -eq $old) 'V20_08_5_RECOVERY_INSTALLED_BLOB_CONFLICT'
    $req=Invoke-RestMethod -Uri ('https://api.github.com/repos/alkospacer123/market-pattern-discovery/git/blobs/'+$new) -Headers @{'user-agent'='v20lab'} -ErrorAction Stop
    need ($req.sha -eq $new -and $req.encoding -eq 'base64') 'V20_08_5_RECOVERY_REMOTE_BLOB_MISMATCH'
    $tmp=$path+'.recovery-download'
    need (-not (Test-Path -LiteralPath $tmp)) 'V20_08_5_RECOVERY_PARTIAL_DOWNLOAD'
    try{
        [IO.File]::WriteAllBytes($tmp,[convert]::FromBase64String($req.content))
        need ((hash $tmp) -eq $new) 'V20_08_5_RECOVERY_REMOTE_HASH_INVALID'
        Move-Item -LiteralPath $tmp -Destination $path -Force -ErrorAction Stop
        need ((hash $path) -eq $new) 'V20_08_5_RECOVERY_LOCAL_HASH_INVALID'
    }finally{if(Test-Path -LiteralPath $tmp){Remove-Item -LiteralPath $tmp -Force}}
}
function healthy([string]$name){
    $task=Get-ScheduledTask -TaskName $name -TaskPath '\' -ErrorAction Stop
    if($task.State -ne 'Running'){return $false}
    $instance=Join-Path $root ('robots\'+$name.Substring(4))
    $switch=Get-Content -LiteralPath (Join-Path $instance 'safety\stage8-trading-kill-switch.json') -Raw -Encoding UTF8 | ConvertFrom-Json
    if($switch.state -ne 'ARMED'){return $false}
    $line=Get-Content -LiteralPath (Join-Path $instance 'logs\live-m15.jsonl') -Tail 1 -Encoding UTF8 | ConvertFrom-Json
    $age=([datetimeoffset]::UtcNow-[datetimeoffset]::Parse([string]$line.utc,[globalization.cultureinfo]::InvariantCulture)).TotalSeconds
    return ($line.robot -eq $name -and [string]$line.state -notmatch '^(HALT|FAULT|FINAM_)' -and $age -ge -5 -and $age -le 90)
}
need ($env:OS -eq 'Windows_NT' -and $env:COMPUTERNAME -eq 'URIU-PC') 'V20_08_5_RECOVERY_WRONG_HOST'
$sid=[Security.Principal.WindowsIdentity]::GetCurrent().User.Value
$manifest=Join-Path $stage 'LIVE_PREPARED.json'
need (Test-Path -LiteralPath $manifest -PathType Leaf) 'V20_08_5_RECOVERY_RECEIPT_MISSING'
$receipt=Get-Content -LiteralPath $manifest -Raw -Encoding UTF8 | ConvertFrom-Json
need ($receipt.schema -eq 'v20.08.4.live_prepared.v1' -and
      $receipt.source_commit -eq $expectedSource -and
      $receipt.status -eq 'PASS_3_OF_3_OFFLINE_PREPARED' -and
      @($receipt.robots).Count -eq 3) 'V20_08_5_RECOVERY_WRONG_SOURCE'
foreach($pair in @(
    @($module,$oldModule,$newModule),
    @($launcher,$oldLauncher,$newLauncher),
    @($operator,$oldOperator,$newOperator)
)){
    $current=hash ([string]$pair[0])
    need ($current -in @([string]$pair[1],[string]$pair[2])) 'V20_08_5_RECOVERY_UNRECOGNIZED_FILE'
}
foreach($name in $names){
    exact-task $name
    $instance=Join-Path $root ('robots\'+$name.Substring(4))
    $switchPath=Join-Path $instance 'safety\stage8-trading-kill-switch.json'
    need (Test-Path -LiteralPath $switchPath -PathType Leaf) 'V20_08_5_RECOVERY_SWITCH_MISSING'
    $switch=Get-Content -LiteralPath $switchPath -Raw -Encoding UTF8 | ConvertFrom-Json
    need ($switch.state -eq 'HALTED') 'V20_08_5_RECOVERY_SWITCH_NOT_HALTED'
}
Write-Output 'v20_08_5_recovery_local=PASS_3_OF_3_HALTED_READY_SOURCE_PINNED'
foreach($name in $names){readflat $name}
if($mode -eq 'verify'){
    Write-Output 'v20_08_5_recovery_verify=PASS_READONLY_NO_MUTATION'
    return
}
# Consistent SQLite snapshot is mandatory BEFORE changing any installed code.
$backup=@(& powershell.exe -noprofile -noninteractive -executionpolicy bypass -file $operator -mode backup -robot all 2>&1)
$backup | Write-Output
need ($LASTEXITCODE -eq 0 -and ($backup -join '|') -match 'v20_08_5_backup=PASS path=') 'V20_08_5_RECOVERY_BACKUP_FAIL'
foreach($pair in @(
    @($module,$oldModule,$newModule),
    @($launcher,$oldLauncher,$newLauncher),
    @($operator,$oldOperator,$newOperator)
)){patch-file ([string]$pair[0]) ([string]$pair[1]) ([string]$pair[2])}
$astErrors=$null
$astTokens=$null
[void][Management.Automation.Language.Parser]::ParseFile($operator,[ref]$astTokens,[ref]$astErrors)
need (@($astErrors).Count -eq 0) 'V20_08_5_RECOVERY_OPERATOR_SYNTAX_ERROR'
$py=Join-Path $root '.venv-raw\scripts\python.exe'
& $py -B -m ast $module | Out-Null
need ($LASTEXITCODE -eq 0) 'V20_08_5_RECOVERY_PY_SYNTAX_ERROR'
foreach($name in $names){
    $ok=@(& powershell.exe -noprofile -noninteractive -executionpolicy bypass -file $launcher -mode verify -robot $name 2>&1)
    need ($LASTEXITCODE -eq 0 -and ($ok -join '|') -match ('v20_08_4_'+$name+'=PASS_VERIFY_NO_FINAM')) 'V20_08_5_RECOVERY_LAUNCHER_HASH_FAIL'
}
Write-Output 'v20_08_5_recovery_patch=PASS_H1_RETRY_SOURCE_AND_LAUNCHER'
# Recheck broker flat immediately before restart. A non-flat account is a HOLD.
foreach($name in $names){readflat $name}
try {
    $start=@(& powershell.exe -noprofile -noninteractive -executionpolicy bypass -file $operator -mode start -robot all 2>&1)
    $start | Write-Output
    need ($LASTEXITCODE -eq 0 -and
          ($start -join '|') -match 'v20_08_5_v20-shallow=PASS_RUNNING_ARMED' -and
          ($start -join '|') -match 'v20_08_5_v20-obv=PASS_RUNNING_ARMED' -and
          ($start -join '|') -match 'v20_08_5_v20-inside=PASS_RUNNING_ARMED') 'V20_08_5_RECOVERY_START_FAILED'
    $allOk=$false
    for($i=0;$i -lt 95;$i++){
        $passing=0
        foreach($name in $names){if(healthy $name){$passing++}}
        if($passing -eq 3){$allOk=$true;break}
        Start-Sleep -Seconds 1
    }
    need $allOk 'V20_08_5_RECOVERY_HEALTH_NOT_CONFIRMED'
    Write-Output 'v20_08_5_recovery=PASS_3_OF_3_RUNNING_ARMED_FRESH_CYCLES'
}catch{
    # Maintain existing broker stops; halt NEW entries only.
    foreach($name in $names){
        try{
            $result=@(& powershell.exe -noprofile -noninteractive -executionpolicy bypass -file $launcher -mode halt -robot $name 2>&1)
            Write-Output ('v20_08_5_recovery_'+$name+'_halt_exit='+$LASTEXITCODE)
        }catch{Write-Output ('v20_08_5_recovery_'+$name+'_halt=REQUIRES_OPERATOR_CHECK')}
    }
    throw
}
