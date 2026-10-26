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
$pin='465a7afa7bba694615080de547e710d307a95ac0'
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
    @('v20_runtime/finam_live.py','f73dc17f546e352ac3789d40c9bb6badcc681fe3'),
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
Write-Output ('v20_08_4_source_pin='+$pin)
Write-Output ('v20_08_4_'+$mode+'=PASS_NEW_ONLY_OFFLINE')
Write-Output 'v20_08_4_finam=NO_NETWORK'
Write-Output 'v20_08_4_tasks=DISABLED_BLOCKER_UNCHANGED'
Write-Output 'v20_08_4_orders=ZERO'
Write-Output 'v20_08_4_live=OFF'
