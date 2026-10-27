# V20-08.4 shared isolated DPAPI launcher for three V20-only live tasks.
# verify: no FINAM and no token decryption. readonly: GET-only. run: owner-armed autonomous M15.
[CmdletBinding()]
param(
    [ValidateSet('verify','readonly','run','arm','halt')][string]$mode='verify',
    [ValidateSet('v20-shallow','v20-obv','v20-inside')][string]$robot='v20-shallow'
)
$ErrorActionPreference='Stop'
Set-StrictMode -Version Latest
$root='C:\V20Lab'
$source='dd55f201b3e9a92ce5fa3f927289f5a5ef89366d'
$live=Join-Path $root 'pretrade-08\live-runtime-08'
$manifest=Join-Path $root 'pretrade-08\live-08\LIVE_PREPARED.json'
$self=Join-Path $root 'pretrade-08\live-08\v20-08-live-launch.ps1'
$receipt=Join-Path $root 'pretrade-08\DPAPI_TRADING_BINDINGS_REPORT.json'
$python=Join-Path $root '.venv-raw\scripts\python.exe'
$h1=Join-Path $root 'source-raw'
function need([bool]$v,[string]$msg){if(-not $v){throw $msg}}
function blob([string]$p) {
    $s=(& git.exe hash-object -- $p).Trim().ToLowerInvariant()
    need ($LASTEXITCODE -eq 0) 'V20_LIVE_HASH_EXEC_FAILED'
    return $s
}
function sidof([string]$value) {
    try {
        if($value -match '^S-[0-9]+(-[0-9]+)+$'){return ([Security.Principal.SecurityIdentifier]::new($value)).Value}
        return ([Security.Principal.NTAccount]::new($value)).Translate([Security.Principal.SecurityIdentifier]).Value
    } catch {return ''}
}
function hashtext([string]$text) {
    $h=[Security.Cryptography.SHA256]::Create()
    try {return ([BitConverter]::ToString($h.ComputeHash([Text.Encoding]::UTF8.GetBytes($text)))).Replace('-','').ToLowerInvariant()}
    finally {$h.Dispose()}
}
need ($env:OS -eq 'Windows_NT' -and $env:COMPUTERNAME -eq 'URIU-PC') 'V20_LIVE_WRONG_INTEL'
foreach($item in @($live,$receipt,$python,$h1,$manifest)){
    need (Test-Path -LiteralPath $item) 'V20_LIVE_REQUIRED_FILE_MISSING'
    need (-not ((Get-Item -LiteralPath $item -Force).Attributes -band [IO.FileAttributes]::ReparsePoint)) 'V20_LIVE_REPARSE_PATH'
}
$installed=Get-Content -LiteralPath $manifest -Raw -Encoding UTF8 | ConvertFrom-Json
$bindings=Get-Content -LiteralPath $receipt -Raw -Encoding UTF8 | ConvertFrom-Json
$sid=[Security.Principal.WindowsIdentity]::GetCurrent().User.Value
need ($installed.schema -eq 'v20.08.4.live_prepared.v1' -and
      $installed.source_commit -eq $source -and $installed.status -eq 'PASS_3_OF_3_OFFLINE_PREPARED' -and
      $bindings.schema -eq 'v20.08.1.dpapi_trading_bindings.v1' -and
      $bindings.status -eq 'PASS_3_OF_3_DPAPI_LIVE_OFF' -and
      $bindings.principal_sid -eq $sid) 'V20_LIVE_PREP_BINDINGS_INVALID'
$br=@($bindings.robots | Where-Object {$_.robot -eq $robot})
$ir=@($installed.robots | Where-Object {$_.robot -eq $robot})
need ($br.Count -eq 1 -and $ir.Count -eq 1 -and
      $br[0].account_sha256 -eq $ir[0].account_sha256 -and
      $br[0].status -eq 'DPAPI_SID_BOUND_LIVE_OFF') 'V20_LIVE_ROBOT_ACCOUNT_SCOPE_MISMATCH'
$instance=Join-Path $root ('robots\'+$robot.Substring(4))
$state=Join-Path $instance 'state\v20-real-intents.sqlite3'
$secret=Join-Path $instance 'secrets\finam.dpapi.json'
$approval=Join-Path $instance 'safety\v20-live-authorization.json'
foreach($file in @($state,$secret,$approval)){
    need (Test-Path -LiteralPath $file -PathType Leaf) 'V20_LIVE_IDENTITY_FILE_MISSING'
    need (-not ((Get-Item -LiteralPath $file -Force).Attributes -band [IO.FileAttributes]::ReparsePoint)) 'V20_LIVE_IDENTITY_FILE_LINK'
}
$ap=Get-Content -LiteralPath $approval -Raw -Encoding UTF8 | ConvertFrom-Json
need ($ap.schema -eq 'v20.08.4.live_authorization.v1' -and
      $ap.source_commit -eq $source -and $ap.robot_id -eq $robot -and
      $ap.account_sha256 -eq $br[0].account_sha256 -and
      $ap.owner_approved -eq $true -and $ap.risk_fraction -eq '0.015') 'V20_LIVE_APPROVAL_INVALID'
foreach($spec in @(
    @('finam_execution.py','9ca194c61aa9db003d298fd1a3e93cc7f8bb23c4'),
    @('finam_live.py','e39a00267c91ea35dbe83d27b26d6b62179b2429')
)){
    $item=Join-Path $live ('V20_TradingSystem_M15\v20_runtime\'+$spec[0])
    need (Test-Path -LiteralPath $item -PathType Leaf) 'V20_LIVE_MODULE_MISSING'
    need ((blob $item) -eq $spec[1]) 'V20_LIVE_MODULE_HASH_INVALID'
}
$task=Get-ScheduledTask -TaskName $robot -TaskPath '\' -ErrorAction Stop
$action=@($task.Actions)
need ($action.Count -eq 1 -and (sidof ([string]$task.Principal.UserId)) -eq $sid) 'V20_LIVE_TASK_SID_INVALID'
$expected='-noprofile -noninteractive -executionpolicy bypass -file "'+$self+'" -mode run -robot '+$robot
$taskLive=($action[0].Execute -ieq 'powershell.exe' -and
           $action[0].Arguments -ieq $expected -and
           $action[0].WorkingDirectory -ieq $instance)
$taskStaging=($task.State -eq 'Disabled' -and
             $action[0].Arguments.Contains('v20-task-live-blocked.ps1'))
need ($taskLive -or $taskStaging) 'V20_LIVE_TASK_ACTION_UNRECOGNIZED'
if($mode -eq 'run' -or $mode -eq 'arm'){
    need ($taskLive -and $task.State -eq 'Running') 'V20_LIVE_TASK_NOT_RUNNING'
}
if($mode -eq 'verify'){
    Write-Output ('v20_08_4_'+$robot+'=PASS_VERIFY_NO_FINAM')
    Write-Output ('v20_08_4_task_state='+$task.State)
    Write-Output 'v20_08_4_orders=ZERO_NO_NETWORK'
    return
}
$data=Get-Content -LiteralPath $secret -Raw -Encoding UTF8 | ConvertFrom-Json
need ($data.schema -eq 'v20.08.1.dpapi_finam_pair.v1' -and
      $data.robot_id -eq $robot -and $data.account_sha256 -eq $br[0].account_sha256 -and
      $data.principal_sid -eq $sid) 'V20_LIVE_DPAPI_SECRET_SCOPE_INVALID'
$oldPath=$env:PYTHONPATH
$oldNoBytes=$env:PYTHONDONTWRITEBYTECODE
$oldAccount=$env:V20_FINAM_ACCOUNT
$oldToken=$env:V20_FINAM_TOKEN
$oldHash=$env:V20_FINAM_ACCOUNT_SHA256
try {
    $acc=ConvertTo-SecureString -String ([string]$data.account_dpapi)
    $tok=ConvertTo-SecureString -String ([string]$data.token_dpapi)
    $env:V20_FINAM_ACCOUNT=[Net.NetworkCredential]::new('', $acc).Password
    $env:V20_FINAM_TOKEN=[Net.NetworkCredential]::new('', $tok).Password
    $env:V20_FINAM_ACCOUNT_SHA256=[string]$br[0].account_sha256
    need ((hashtext $env:V20_FINAM_ACCOUNT) -ceq $env:V20_FINAM_ACCOUNT_SHA256) 'V20_LIVE_DPAPI_DECRYPT_MISMATCH'
    $env:PYTHONPATH=$live+[IO.Path]::PathSeparator+$h1
    $env:PYTHONDONTWRITEBYTECODE='1'
    $params=@('-B','-m','V20_TradingSystem_M15.v20_runtime.finam_live',
       '--root',$root,'--robot',$robot,'--source-commit',$source)
    if($mode -eq 'readonly'){$params+='--readonly'}
    if($mode -eq 'arm'){$params+='--arm'}
    if($mode -eq 'halt'){$params+='--halt'}
    & $python @params
    need ($LASTEXITCODE -eq 0) 'V20_LIVE_MODULE_RETURNED_FAIL'
} finally {
    $env:PYTHONPATH=$oldPath
    $env:PYTHONDONTWRITEBYTECODE=$oldNoBytes
    $env:V20_FINAM_ACCOUNT=$oldAccount
    $env:V20_FINAM_TOKEN=$oldToken
    $env:V20_FINAM_ACCOUNT_SHA256=$oldHash
}
