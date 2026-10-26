# V20-08.4: install ONE shared V20-only live executor, never arm, never run.
# Reuse accepted 08.2 frozen source bundle in a separate V20 live workspace.
[CmdletBinding()]
param([ValidateSet('install','verify')][string]$mode='verify')
$ErrorActionPreference='Stop'
Set-StrictMode -Version Latest
$root='C:\V20Lab'
$trial=Join-Path $root 'pretrade-08\trial-runtime-08'
$live=Join-Path $root 'pretrade-08\live-runtime-08'
$h1=Join-Path $root 'source-raw'
$python=Join-Path $root '.venv-raw\scripts\python.exe'
$receipt=Join-Path $root 'pretrade-08\DPAPI_TRADING_BINDINGS_REPORT.json'
$pin='eb1595fa68a400996f95beaca9089068aa78f12a'
function need([bool]$yes,[string]$errorCode) {if(-not $yes){throw $errorCode}}
function noguardlink([string]$path){
    if(Test-Path -LiteralPath $path){need (-not ((Get-Item -LiteralPath $path -Force).Attributes -band [IO.FileAttributes]::ReparsePoint)) 'V20_LIVE_REPARSE_BLOCKED'}
}
function blob([string]$path){
    $val=(& git.exe hash-object -- $path).Trim().ToLowerInvariant()
    need ($LASTEXITCODE -eq 0) 'V20_LIVE_GIT_HASH_FAILED'
    return $val
}
need ($env:OS -eq 'Windows_NT' -and $env:COMPUTERNAME -eq 'URIU-PC') 'V20_LIVE_WRONG_INTEL'
foreach($f in @($root,$trial,$h1,$python,$receipt)){
    need (Test-Path -LiteralPath $f) 'V20_LIVE_PRIOR_SOURCE_MISSING'
    noguardlink $f
}
$data=Get-Content -LiteralPath $receipt -Raw -Encoding UTF8 | ConvertFrom-Json
$sid=[Security.Principal.WindowsIdentity]::GetCurrent().User.Value
need ($data.schema -eq 'v20.08.1.dpapi_trading_bindings.v1' -and
      $data.status -eq 'PASS_3_OF_3_DPAPI_LIVE_OFF' -and
      $data.principal_sid -eq $sid) 'V20_LIVE_ACCOUNT_SID_RECEIPT_INVALID'
$hashes=@()
foreach($name in @('v20-shallow','v20-obv','v20-inside')){
    $task=Get-ScheduledTask -TaskName $name -TaskPath '\' -ErrorAction Stop
    need ($task.State -eq 'Disabled' -and @($task.Actions).Count -eq 1 -and
          $task.Actions[0].Arguments.Contains('v20-task-live-blocked.ps1')) 'V20_LIVE_TASK_NOT_DISABLED_STAGING'
    $rows=@($data.robots | Where-Object {$_.robot -eq $name})
    need ($rows.Count -eq 1 -and $rows[0].status -eq 'DPAPI_SID_BOUND_LIVE_OFF') 'V20_LIVE_ACCOUNT_RECEIPT_MISSING'
    $hashes += [string]$rows[0].account_sha256
}
need (@($hashes | Select-Object -Unique).Count -eq 3) 'V20_LIVE_ACCOUNTS_NOT_DISTINCT'
$trialpkg=Join-Path $trial 'V20_TradingSystem_M15\v20_runtime'
need ((blob (Join-Path $trialpkg 'finam_execution.py')) -eq '9d12eee5fd718f0f81716adfd81b45a6e5844df6') 'V20_LIVE_ACCEPTED_TRIAL_SOURCE_CHANGED'
if($mode -eq 'install' -and -not (Test-Path -LiteralPath $live)){
    noguardlink (Split-Path $live)
    Copy-Item -LiteralPath $trial -Destination $live -Recurse -ErrorAction Stop
}
need (Test-Path -LiteralPath $live -PathType Container) 'V20_LIVE_NOT_INSTALLED'
noguardlink $live
$package=Join-Path $live 'V20_TradingSystem_M15\v20_runtime'
need (Test-Path -LiteralPath $package -PathType Container) 'V20_LIVE_PACKAGE_MISSING'
$objects=@(
    @('v20_runtime/finam_execution.py','9ca194c61aa9db003d298fd1a3e93cc7f8bb23c4'),
    @('v20_runtime/finam_live.py','3bc157d70e7528d0d3191ff89ea0d2f2e33f539a'),
    @('v20_runtime/tests/test_finam_live.py','af1822891d4d600a78ac53fea3ddd5479e06cf4b')
)
foreach($row in $objects){
    $rel=[string]$row[0]
    $expected=[string]$row[1]
    $dest=Join-Path (Join-Path $live 'V20_TradingSystem_M15') ($rel.Replace('/','\'))
    noguardlink $dest
    if(Test-Path -LiteralPath $dest -PathType Leaf){
        $cur=blob $dest
        if($cur -eq $expected){continue}
        # In copied 08.2 input, only the original execution module may be
        # upgraded. Reject any foreign local changes rather than overwrite.
        need ($mode -eq 'install' -and $rel -eq 'v20_runtime/finam_execution.py' -and
              $cur -eq '9d12eee5fd718f0f81716adfd81b45a6e5844df6') 'V20_LIVE_INSTALLED_SOURCE_CONFLICT'
    } else {
        need ($mode -eq 'install') 'V20_LIVE_FILE_NOT_INSTALLED'
    }
    $raw='https://raw.githubusercontent.com/alkospacer123/market-pattern-discovery/'+$pin+'/V20_TradingSystem_M15/'+$rel
    $tmp=$dest+'.download'
    need (-not (Test-Path -LiteralPath $tmp)) 'V20_LIVE_PARTIAL_DOWNLOAD'
    try {
        Invoke-WebRequest -Uri $raw -OutFile $tmp -UseBasicParsing -ErrorAction Stop
        need ((blob $tmp) -eq $expected) 'V20_LIVE_REMOTE_BLOB_MISMATCH'
        Move-Item -LiteralPath $tmp -Destination $dest -Force -ErrorAction Stop
    } finally {
        if(Test-Path -LiteralPath $tmp){Remove-Item -LiteralPath $tmp -Force}
    }
    need ((blob $dest) -eq $expected) 'V20_LIVE_INSTALLED_BLOB_MISMATCH'
}
# Verify the accepted H1 and frozen research bundle stayed byte-identical.
foreach($check in @(
    @('TradingSystemLab\stage8_robot\state.py','4f12e1cb61eccb0b14c1efb9ff0cdf2532a7b22b'),
    @('TradingSystemLab\stage8_robot\trading_safety_gate.py','e938048a8dc3caa9db29209489a7050e64d0bb5a'),
    @('TradingSystemLab\stage8_robot\operations.py','0d7ba1f2f9f4e6fa2f772921846bc334469dd3d5')
)){
    need ((blob (Join-Path $h1 $check[0])) -eq $check[1]) 'V20_LIVE_ORIGINAL_H1_SOURCE_MISMATCH'
}
$oldPath=$env:PYTHONPATH
$oldBytecode=$env:PYTHONDONTWRITEBYTECODE
try {
    $env:PYTHONPATH=$live+[IO.Path]::PathSeparator+$h1
    $env:PYTHONDONTWRITEBYTECODE='1'
    & $python -B -m unittest -v V20_TradingSystem_M15.v20_runtime.tests.test_finam_live
    need ($LASTEXITCODE -eq 0) 'V20_LIVE_NEW_ONLY_TESTS_FAIL'
} finally {
    $env:PYTHONPATH=$oldPath
    $env:PYTHONDONTWRITEBYTECODE=$oldBytecode
}
# Only after all existing tests pass, create exact V20-only LIVE receipt
# and approvals for three accounts that the owner already explicitly authorized.
$prepared=Join-Path $root 'pretrade-08\live-08'
New-Item -ItemType Directory -Path $prepared -Force | Out-Null
noguardlink $prepared
$launchPath=Join-Path $prepared 'v20-08-live-launch.ps1'
$launcherBlob='1f56e14902ad5f74798fc929203fb428988329dc'
if($mode -eq 'install' -and -not (Test-Path -LiteralPath $launchPath)){
    $tmp=$launchPath+'.download'
    need (-not (Test-Path -LiteralPath $tmp)) 'V20_LIVE_LAUNCHER_PARTIAL'
    try {
        Invoke-WebRequest -Uri ('https://raw.githubusercontent.com/alkospacer123/market-pattern-discovery/f57a13e0395463e912ef831342c145604957b4b4/V20_TradingSystem_M15/V20-08/v20-08-live-launch.ps1') -OutFile $tmp -UseBasicParsing -ErrorAction Stop
        need ((blob $tmp) -eq $launcherBlob) 'V20_LIVE_LAUNCHER_REMOTE_HASH'
        Move-Item -LiteralPath $tmp -Destination $launchPath
    } finally {
        if(Test-Path -LiteralPath $tmp){Remove-Item -LiteralPath $tmp -Force}
    }
}
need (Test-Path -LiteralPath $launchPath -PathType Leaf) 'V20_LIVE_LAUNCHER_MISSING'
noguardlink $launchPath
need ((blob $launchPath) -eq $launcherBlob) 'V20_LIVE_LAUNCHER_CHANGED'
$cutoverPath=Join-Path $prepared 'v20-08-live-cutover.ps1'
$cutoverBlob='2c1cbda7de3abd64dc1fc9ee16f463ed5e5e82cd'
if($mode -eq 'install' -and -not (Test-Path -LiteralPath $cutoverPath)){
    $tmp=$cutoverPath+'.download'
    need (-not (Test-Path -LiteralPath $tmp)) 'V20_LIVE_CUTOVER_PARTIAL'
    try {
        Invoke-WebRequest -Uri ('https://raw.githubusercontent.com/alkospacer123/market-pattern-discovery/3bf0e85748db675aa481f2d6afd030ade4a2b5e3/V20_TradingSystem_M15/V20-08/v20-08-live-cutover.ps1') -OutFile $tmp -UseBasicParsing -ErrorAction Stop
        need ((blob $tmp) -eq $cutoverBlob) 'V20_LIVE_CUTOVER_REMOTE_HASH'
        Move-Item -LiteralPath $tmp -Destination $cutoverPath
    } finally {
        if(Test-Path -LiteralPath $tmp){Remove-Item -LiteralPath $tmp -Force}
    }
}
need (Test-Path -LiteralPath $cutoverPath -PathType Leaf) 'V20_LIVE_CUTOVER_MISSING'
noguardlink $cutoverPath
need ((blob $cutoverPath) -eq $cutoverBlob) 'V20_LIVE_CUTOVER_CHANGED'
$utf8=New-Object System.Text.UTF8Encoding($false)
$costs=[ordered]@{USDRUBF='8.34';CNYRUBF='2.02';GLDRUBF='3.64';IMOEXF='4.16'}
$observed=@()
foreach($name in @('v20-shallow','v20-obv','v20-inside')){
    $rows=@($data.robots | Where-Object {$_.robot -eq $name})
    need ($rows.Count -eq 1) 'V20_LIVE_APPROVAL_ACCOUNT_MISSING'
    $hash=[string]$rows[0].account_sha256
    $instance=Join-Path $root ('robots\'+$name.Substring(4))
    $safety=Join-Path $instance 'safety'
    need (Test-Path -LiteralPath $safety -PathType Container) 'V20_LIVE_SAFETY_MISSING'
    noguardlink $safety
    $approval=Join-Path $safety 'v20-live-authorization.json'
    $record=[ordered]@{
        schema='v20.08.4.live_authorization.v1'
        robot_id=$name
        account_sha256=$hash
        source_commit=$pin
        owner_approved=$true
        execution_mode='V20_FROZEN_M15_LIVE'
        risk_fraction='0.015'
        initial_stop_atr='2'
        signals='FROZEN_COMPLETED_M15_NEXT_OPEN'
        symbols=@('USDRUBF','CNYRUBF','GLDRUBF','IMOEXF')
        roundtrip_cost_rub=$costs
    }
    $json=ConvertTo-Json -InputObject $record -Depth 8
    if(Test-Path -LiteralPath $approval){
        noguardlink $approval
        $old=Get-Content -LiteralPath $approval -Raw -Encoding UTF8 | ConvertFrom-Json
        need ($old.schema -eq $record.schema -and
              $old.robot_id -eq $name -and $old.account_sha256 -eq $hash -and
              $old.source_commit -eq $pin -and
              $old.owner_approved -eq $true -and
              $old.execution_mode -eq $record.execution_mode) 'V20_LIVE_PREVIOUS_APPROVAL_CONFLICT'
        # Python performs the full exact key and tariff check on startup.
    } else {
        need ($mode -eq 'install') 'V20_LIVE_APPROVAL_NOT_INSTALLED'
        [IO.File]::WriteAllText($approval,$json,$utf8)
    }
    $observed += [ordered]@{robot=$name;account_sha256=$hash}
}
$manifest=Join-Path $prepared 'LIVE_PREPARED.json'
$summary=[ordered]@{
    schema='v20.08.4.live_prepared.v1'
    status='PASS_3_OF_3_OFFLINE_PREPARED'
    source_commit=$pin
    owner_live_authorization_received=$true
    tasks_enabled=$false
    broker_contacts=0
    new_orders=0
    robots=$observed
}
$receiptJson=ConvertTo-Json -InputObject $summary -Depth 6
if(Test-Path -LiteralPath $manifest){
    noguardlink $manifest
    $existing=Get-Content -LiteralPath $manifest -Raw -Encoding UTF8 | ConvertFrom-Json
    need ($existing.schema -eq $summary.schema -and
          $existing.status -eq $summary.status -and
          $existing.source_commit -eq $pin -and
          $existing.tasks_enabled -eq $false) 'V20_LIVE_MANIFEST_CONFLICT'
} else {
    need ($mode -eq 'install') 'V20_LIVE_MANIFEST_NOT_INSTALLED'
    [IO.File]::WriteAllText($manifest,$receiptJson,$utf8)
}
Write-Output ('v20_08_4_source_pin='+$pin)
Write-Output ('v20_08_4_'+$mode+'=PASS_NEW_ONLY_OFFLINE')
Write-Output 'v20_08_4_finam=NO_NETWORK'
Write-Output 'v20_08_4_tasks=DISABLED_BLOCKER_UNCHANGED'
Write-Output 'v20_08_4_orders=ZERO'
Write-Output 'v20_08_4_live=OFF'
