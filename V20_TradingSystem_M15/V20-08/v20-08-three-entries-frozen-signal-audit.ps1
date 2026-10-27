# Frozen V20 three-entry signal replay on Intel. FINAM session auth + M15 GET only.
# No market orders, no cancel, no SQLite mutation, no Task changes, no ARM.
[CmdletBinding()]
param()
$ErrorActionPreference='Stop'
Set-StrictMode -Version Latest
function need([bool]$ok,[string]$why){if(-not $ok){throw $why}}
function gitblob([string]$p){
    $sha=(& git.exe hash-object -- $p).Trim()
    need ($LASTEXITCODE -eq 0) 'V20_AUDIT_GIT_HASH_UNAVAILABLE'
    return $sha
}
$root='C:\V20Lab'
need ($env:OS -eq 'Windows_NT' -and $env:COMPUTERNAME -ceq 'URIU-PC') 'V20_AUDIT_INTEL_SCOPE_INVALID'
$launcher=Join-Path $root 'pretrade-08\live-08\v20-08-live-launch.ps1'
$python=Join-Path $root '.venv-raw\scripts\python.exe'
$live=Join-Path $root 'pretrade-08\live-runtime-08'
$h1=Join-Path $root 'source-raw'
$script=Join-Path $env:USERPROFILE 'downloads\v20-08-three-entries-frozen-signal-audit.py'
$expected='d9e5d9013f6d74c997e53308969aef84e94ab688'
need ((Test-Path -LiteralPath $python -PathType Leaf) -and
      (Test-Path -LiteralPath $launcher -PathType Leaf) -and
      (Test-Path -LiteralPath $h1 -PathType Container)) 'V20_AUDIT_DEPENDENCIES_MISSING'
if(-not (Test-Path -LiteralPath $script -PathType Leaf)){
    $blob=Invoke-RestMethod -Uri ('https://api.github.com/repos/alkospacer123/market-pattern-discovery/git/blobs/'+$expected) -Headers @{'user-agent'='v20lab'}
    need ($blob.sha -eq $expected -and $blob.encoding -eq 'base64') 'V20_AUDIT_SOURCE_MISMATCH'
    [IO.File]::WriteAllBytes($script,[Convert]::FromBase64String($blob.content))
}
need ((gitblob $script) -eq $expected) 'V20_AUDIT_PYTHON_SOURCE_HASH_CONFLICT'
$sid=[Security.Principal.WindowsIdentity]::GetCurrent().User.Value
$oldPath=$env:PYTHONPATH
$oldAccount=$env:V20_FINAM_ACCOUNT
$oldToken=$env:V20_FINAM_TOKEN
$oldHash=$env:V20_FINAM_ACCOUNT_SHA256
$oldNoBytes=$env:PYTHONDONTWRITEBYTECODE
$successful=0
try{
    foreach($robot in @('v20-shallow','v20-obv','v20-inside')){
        $preflight=@(& powershell.exe -noprofile -noninteractive -executionpolicy bypass -file $launcher -mode verify -robot $robot)
        need ($LASTEXITCODE -eq 0 -and ($preflight -join '|') -match ('v20_08_4_'+$robot+'=PASS_VERIFY_NO_FINAM')) 'V20_AUDIT_LIVE_SOURCE_OR_IDENTITY_INVALID'
        $secretfile=Join-Path $root ('robots\'+$robot.Substring(4)+'\secrets\finam.dpapi.json')
        need (Test-Path -LiteralPath $secretfile -PathType Leaf) 'V20_AUDIT_DPAPI_FILE_MISSING'
        $secret=Get-Content -LiteralPath $secretfile -Raw -Encoding UTF8 | ConvertFrom-Json
        need ($secret.schema -eq 'v20.08.1.dpapi_finam_pair.v1' -and $secret.robot_id -eq $robot -and
              $secret.principal_sid -eq $sid -and $secret.account_sha256 -match '^[0-9a-f]{64}$') 'V20_AUDIT_SECRET_SCOPE_MISMATCH'
        $account=ConvertTo-SecureString -String ([string]$secret.account_dpapi)
        $token=ConvertTo-SecureString -String ([string]$secret.token_dpapi)
        $env:V20_FINAM_ACCOUNT=[Net.NetworkCredential]::new('', $account).Password
        $env:V20_FINAM_TOKEN=[Net.NetworkCredential]::new('', $token).Password
        $env:V20_FINAM_ACCOUNT_SHA256=[string]$secret.account_sha256
        $env:PYTHONPATH=$live+[IO.Path]::PathSeparator+$h1
        $env:PYTHONDONTWRITEBYTECODE='1'
        Write-Output ('=== '+$robot+' FROZEN HISTORICAL SIGNAL AUDIT ===')
        & $python -B $script $robot
        need ($LASTEXITCODE -eq 0) ('V20_AUDIT_SIGNAL_MISMATCH_'+$robot)
        $successful++
    }
    need ($successful -eq 3) 'V20_AUDIT_PARTIAL'
    Write-Output 'v20_three_frozen_entry_signal_audit=PASS_3_OF_3_GET_ONLY_NO_ORDER_NO_TASK_MUTATION'
} finally {
    $env:PYTHONPATH=$oldPath
    $env:V20_FINAM_ACCOUNT=$oldAccount
    $env:V20_FINAM_TOKEN=$oldToken
    $env:V20_FINAM_ACCOUNT_SHA256=$oldHash
    $env:PYTHONDONTWRITEBYTECODE=$oldNoBytes
}
