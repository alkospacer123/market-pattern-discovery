# V20-08.2 supervised single real trial. Reuse H1 FINAM / StateStore / SLTP / kill-switch.
# Modes: verify, frozen execute, technical, follow-only, technical_recover (GET+pre-POST only).
[CmdletBinding()]
param(
    [ValidateSet('verify','execute','follow','technical','technical_follow','technical_recover')][string]$Mode='verify',
    [ValidateSet('v20-shallow','v20-obv','v20-inside')][string]$Robot='v20-shallow',
    [ValidateSet('cnyrubf')][string]$Symbol='cnyrubf',
    [ValidatePattern('^[0-9]+(\.[0-9]+)?$')][string]$RoundtripCostPerContract='2.02',
    [switch]$AuthorizeRealTrial
)
$ErrorActionPreference='Stop'
Set-StrictMode -Version Latest
$root='C:\V20Lab'
$trial=Join-Path $root 'pretrade-08\trial-runtime-08'
$h1=Join-Path $root 'source-raw'
$python=Join-Path $root '.venv-raw\scripts\python.exe'
$receipt=Join-Path $root 'pretrade-08\DPAPI_TRADING_BINDINGS_REPORT.json'
$sourceSha='e9de4acd8582009c93d67dcac299cabf51eae08e'
function need([bool]$ok,[string]$code) {if(-not $ok){throw $code}}
function sha([string]$x) {
    $h=[Security.Cryptography.SHA256]::Create()
    try {return ([BitConverter]::ToString($h.ComputeHash([Text.Encoding]::UTF8.GetBytes($x)))).Replace('-','').ToLowerInvariant()}
    finally {$h.Dispose()}
}
need ($env:OS -eq 'Windows_NT' -and $env:COMPUTERNAME -eq 'URIU-PC') 'V20_TRIAL_WRONG_HOST'
need (([decimal]::Parse($RoundtripCostPerContract,[Globalization.CultureInfo]::InvariantCulture)) -gt 0) 'V20_TRIAL_BAD_FULL_FEE'
foreach($f in @($trial,$h1,$python,$receipt)){
    need (Test-Path -LiteralPath $f) 'V20_TRIAL_REQUIRED_PATH_MISSING'
    need (-not ((Get-Item -LiteralPath $f -Force).Attributes -band [IO.FileAttributes]::ReparsePoint)) 'V20_TRIAL_REPARSE_PATH'
}
$r=Get-Content -LiteralPath $receipt -Raw -Encoding UTF8 | ConvertFrom-Json
$sid=[Security.Principal.WindowsIdentity]::GetCurrent().User.Value
need ($r.schema -eq 'v20.08.1.dpapi_trading_bindings.v1' -and $r.status -eq 'PASS_3_OF_3_DPAPI_LIVE_OFF' -and
      $r.live_enabled -eq $false -and $r.principal_sid -eq $sid) 'V20_TRIAL_DPAPI_RECEIPT_INVALID'
foreach($name in @('v20-shallow','v20-obv','v20-inside')){
    $task=Get-ScheduledTask -TaskName $name -TaskPath '\' -ErrorAction Stop
    need ($task.State -eq 'Disabled' -and @($task.Actions).Count -eq 1 -and
          $task.Actions[0].Arguments.Contains('v20-task-live-blocked.ps1')) 'V20_TRIAL_TASK_NOT_DISABLED'
}
$row=@($r.robots | Where-Object {$_.robot -eq $Robot})
need ($row.Count -eq 1 -and $row[0].status -eq 'DPAPI_SID_BOUND_LIVE_OFF') 'V20_TRIAL_ROBOT_SCOPE_MISMATCH'
$accHash=[string]$row[0].account_sha256
need ($accHash -cmatch '^[0-9a-f]{64}$') 'V20_TRIAL_ACCOUNT_SHA_INVALID'
$slug=$Robot.Substring(4)
$instance=Join-Path $root ('robots\'+$slug)
$grant=Join-Path $instance 'safety\v20-first-signal-approval.json'
$secretPath=Join-Path $instance 'secrets\finam.dpapi.json'
$state=Join-Path $instance 'state\v20-real-intents.sqlite3'
foreach($f in @($grant,$secretPath,$state)){
    need (Test-Path -LiteralPath $f -PathType Leaf) 'V20_TRIAL_ISOLATED_FILE_MISSING'
    need (-not ((Get-Item -LiteralPath $f -Force).Attributes -band [IO.FileAttributes]::ReparsePoint)) 'V20_TRIAL_ISOLATED_LINK'
}
$a=Get-Content -LiteralPath $grant -Raw -Encoding UTF8 | ConvertFrom-Json
need ($a.schema -eq 'v20.08.2.first_signal_approval.v1' -and
      $a.scope -eq 'ONE_FIRST_REAL_FROZEN_TRIAL_ONLY' -and
      $a.robot_id -eq $Robot -and $a.account_sha256 -ceq $accHash -and
      $a.source_commit -ceq $sourceSha -and
      $a.instrument -eq $Symbol.ToUpperInvariant() -and
      $a.max_risk_fraction -eq '0.015' -and
      $a.explicit_owner_approval -eq $true) 'V20_TRIAL_OWNER_SCOPE_INVALID'
$files=@(
    @('finam_execution.py','ffa7014046f92a9aecb4c94047ec94bd0bb963f9'),
    @('finam_trial_operator.py','589489e5a488ae8ecf5d162f4fb0df79ff5b9cdc'),
    @('account_risk.py','50d0a924b0eccef45746c0111fa0df4803aed125'),
    @('h1_state_journal.py','68988932c11241cb34273b745dda7764e35d9e62')
)
foreach($item in $files){
    $target=Join-Path $trial ('V20_TradingSystem_M15\v20_runtime\'+$item[0])
    need (Test-Path -LiteralPath $target -PathType Leaf) 'V20_TRIAL_MODULE_MISSING'
    $got=(& git.exe hash-object -- $target).Trim().ToLowerInvariant()
    need ($LASTEXITCODE -eq 0 -and $got -ceq $item[1]) 'V20_TRIAL_MODULE_NOT_PINNED'
}
if($Mode -eq 'verify'){
    Write-Output ('v20_08_2_'+$slug+'_operator=PASS_VERIFY_NO_FINAM')
    Write-Output 'v20_08_2_orders=zero'
    Write-Output 'v20_08_2_live=off'
    return
}
need ($Mode -notin @('execute','technical') -or $AuthorizeRealTrial.IsPresent) 'V20_TRIAL_EXPLICIT_EXECUTE_SWITCH_REQUIRED'
$record=Get-Content -LiteralPath $secretPath -Raw -Encoding UTF8 | ConvertFrom-Json
need ($record.schema -eq 'v20.08.1.dpapi_finam_pair.v1' -and
      $record.robot_id -eq $Robot -and $record.principal_sid -eq $sid -and
      $record.account_sha256 -ceq $accHash -and $record.live_enabled -eq $false) 'V20_TRIAL_DPAPI_RECORD_INVALID'
$oldPath=$env:PYTHONPATH
$oldAccount=$env:V20_FINAM_ACCOUNT
$oldToken=$env:V20_FINAM_TOKEN
$oldHash=$env:V20_FINAM_ACCOUNT_SHA256
try {
    $secretAccount=ConvertTo-SecureString -String ([string]$record.account_dpapi)
    $secretToken=ConvertTo-SecureString -String ([string]$record.token_dpapi)
    $env:V20_FINAM_ACCOUNT=[Net.NetworkCredential]::new('', $secretAccount).Password
    $env:V20_FINAM_TOKEN=[Net.NetworkCredential]::new('', $secretToken).Password
    $env:V20_FINAM_ACCOUNT_SHA256=$accHash
    need ((sha $env:V20_FINAM_ACCOUNT) -ceq $accHash) 'V20_TRIAL_DECRYPT_ACCOUNT_MISMATCH'
    $env:PYTHONPATH=$trial+[IO.Path]::PathSeparator+$h1
    $params=@('-B','-m','V20_TradingSystem_M15.v20_runtime.finam_trial_operator',
      '--root',$root,'--robot',$Robot,'--symbol',$Symbol.ToUpperInvariant(),
      '--full-roundtrip-cost',$RoundtripCostPerContract,'--source-sha',$sourceSha,
      '--mode',$(if($Mode -eq 'execute'){'trial'}elseif($Mode -eq 'technical'){'technical'}elseif($Mode -eq 'technical_follow'){'technical_follow'}elseif($Mode -eq 'technical_recover'){'technical_recover'}else{'follow'}))
    if($Mode -in @('execute','technical')){$params+='--arm-for-trial'}
    & $python @params
    need ($LASTEXITCODE -eq 0) 'V20_TRIAL_BROKER_RECONCILIATION_REQUIRED'
} finally {
    $env:PYTHONPATH=$oldPath
    $env:V20_FINAM_ACCOUNT=$oldAccount
    $env:V20_FINAM_TOKEN=$oldToken
    $env:V20_FINAM_ACCOUNT_SHA256=$oldHash
}
