# V20-08.1: 3 isolated DPAPI secrets, bound to the existing V20 Task SID.
# NO FINAM HTTP, no order, no launch, no Task mutation or H1 environment change.
[CmdletBinding()]
param()
$ErrorActionPreference = 'Stop'
Set-StrictMode -Version Latest
$root = 'C:\V20Lab'
$robots = @('v20-shallow','v20-obv','v20-inside')
$tokenProof = Join-Path $root 'pretrade-08\TRADING_TOKEN_ACCOUNT_READONLY_REPORT.json'
$taskProof = Join-Path $root 'staging-07\TASKS_07_2_REPORT.json'
$output = Join-Path $root 'pretrade-08\DPAPI_TRADING_BINDINGS_REPORT.json'
function need([bool]$ok,[string]$why) { if (-not $ok) { throw $why } }
function digest([string]$v) {
    $sha = [Security.Cryptography.SHA256]::Create()
    try { return ([BitConverter]::ToString($sha.ComputeHash([Text.Encoding]::UTF8.GetBytes($v)))).Replace('-','').ToLowerInvariant() }
    finally { $sha.Dispose() }
}
function require-own-path([string]$path) {
    if (Test-Path -LiteralPath $path) {
        $item = Get-Item -LiteralPath $path -Force
        need (-not (($item.Attributes -band [IO.FileAttributes]::ReparsePoint) -ne 0)) 'V20_08_1_REPARSE_FORBIDDEN'
    }
}
function sid-of([string]$user) {
    try {
        if ($user -match '^S-[0-9]+(-[0-9]+)+$') {
            return ([Security.Principal.SecurityIdentifier]::new($user)).Value
        }
        return ([Security.Principal.NTAccount]::new($user)).Translate([Security.Principal.SecurityIdentifier]).Value
    } catch { throw 'V20_08_1_TASK_SID_UNRESOLVED' }
}
function secure-fingerprint([Security.SecureString]$secret) {
    $ptr = [IntPtr]::Zero
    try {
        $ptr = [Runtime.InteropServices.Marshal]::SecureStringToBSTR($secret)
        $value = [Runtime.InteropServices.Marshal]::PtrToStringBSTR($ptr)
        try { return (digest $value) } finally { $value = $null }
    } finally {
        if ($ptr -ne [IntPtr]::Zero) { [Runtime.InteropServices.Marshal]::ZeroFreeBSTR($ptr) }
    }
}
function secure-acl([string]$path,[string]$sid,[bool]$directory) {
    $rule = if ($directory) { "*${sid}:(OI)(CI)F" } else { "*${sid}:F" }
    $system = if ($directory) { '*S-1-5-18:(OI)(CI)F' } else { '*S-1-5-18:F' }
    $admins = if ($directory) { '*S-1-5-32-544:(OI)(CI)F' } else { '*S-1-5-32-544:F' }
    & icacls.exe $path '/inheritance:r' '/grant:r' $rule $system $admins | Out-Null
    need ($LASTEXITCODE -eq 0) 'V20_08_1_DPAPI_ACL_FAILED'
}
need ($env:OS -eq 'Windows_NT' -and $env:COMPUTERNAME -eq 'URIU-PC') 'V20_08_1_WRONG_HOST'
foreach ($p in @($root, (Join-Path $root 'robots'), (Join-Path $root 'pretrade-08'))) {
    need (Test-Path -LiteralPath $p -PathType Container) 'V20_08_1_DIRECTORY_MISSING'
    require-own-path $p
}
need ((Test-Path -LiteralPath $tokenProof -PathType Leaf) -and (Test-Path -LiteralPath $taskProof -PathType Leaf)) 'V20_08_1_PRIOR_PROOFS_MISSING'
need (-not (Test-Path -LiteralPath $output)) 'V20_08_1_DPAPI_REPORT_EXISTS'
$proof = Get-Content -LiteralPath $tokenProof -Raw -Encoding UTF8 | ConvertFrom-Json
$tasks = Get-Content -LiteralPath $taskProof -Raw -Encoding UTF8 | ConvertFrom-Json
need ($proof.schema -eq 'v20.finam.trading_tokens_get_only.v1' -and
      $proof.status -eq 'PASS_3_OF_3_GET_ONLY' -and $proof.live_enabled -eq $false -and
      $tasks.schema -eq 'v20.intel.stage07.disabled_tasks.v1' -and
      $tasks.status -eq 'PASS_3_OF_3_DISABLED' -and $tasks.live_enabled -eq $false) 'V20_08_1_PRIOR_STATUS_INVALID'
$sid = [Security.Principal.WindowsIdentity]::GetCurrent().User.Value
need ($sid -eq $tasks.principal_sid -and $sid -notin @('S-1-5-18','S-1-5-19','S-1-5-20')) 'V20_08_1_DPAPI_TASK_SID_MISMATCH'
need (@($proof.accounts).Count -eq 3 -and @($tasks.tasks).Count -eq 3) 'V20_08_1_PRIOR_ACCOUNT_COUNT_INVALID'
$entries = @()
$uniqueTokens = @{}
foreach ($robot in $robots) {
    $name = $robot.Substring(4)
    $dir = Join-Path $root ('robots\' + $name)
    require-own-path $dir
    need (Test-Path -LiteralPath $dir -PathType Container) 'V20_08_1_ROBOT_DIRECTORY_MISSING'
    $secretDir = Join-Path $dir 'secrets'
    $target = Join-Path $secretDir 'finam.dpapi.json'
    need (-not (Test-Path -LiteralPath $target)) 'V20_08_1_SECRET_ALREADY_PRESENT_NO_OVERWRITE'
    require-own-path $secretDir
    $bindings = @($proof.accounts | Where-Object { $_.robot -eq $robot })
    $trows = @($tasks.tasks | Where-Object { $_.robot -eq $robot })
    need ($bindings.Count -eq 1 -and $trows.Count -eq 1 -and
          $bindings[0].account_clean -eq $true -and
          $bindings[0].n4_margin_status -eq 'PASS_4_OF_4' -and
          $trows[0].task_state -eq 'Disabled') 'V20_08_1_ROBOT_PROOF_INVALID'
    $t = Get-ScheduledTask -TaskName $robot -TaskPath '\' -ErrorAction Stop
    need ($t.State -eq 'Disabled' -and @($t.Actions).Count -eq 1 -and
          $t.Actions[0].Arguments.Contains('v20-task-live-blocked.ps1') -and
          (sid-of ([string]$t.Principal.UserId)) -eq $sid) 'V20_08_1_TASK_NOT_PROTECTED'
    Write-Output ('v20_08_1_dpapi_input=' + $robot)
    $account = (Read-Host ('finam account for ' + $robot + ' (visible)')).Trim()
    need ($account -match '^[A-Za-z0-9_.-]{1,128}$' -and
          (digest $account) -ceq $bindings[0].account_sha256) 'V20_08_1_ACCOUNT_MISMATCH'
    $token = Read-Host ('finam trading token for ' + $robot + ' (masked)') -AsSecureString
    need ($null -ne $token -and $token.Length -gt 0) 'V20_08_1_TOKEN_EMPTY'
    $fingerprint = secure-fingerprint $token
    need (-not $uniqueTokens.ContainsKey($fingerprint)) 'V20_08_1_TRADING_TOKENS_NOT_DISTINCT'
    $uniqueTokens[$fingerprint] = $true
    $accountProtected = (ConvertTo-SecureString -String $account -AsPlainText -Force) | ConvertFrom-SecureString
    $tokenProtected = $token | ConvertFrom-SecureString
    $entries += [pscustomobject]@{ robot=$robot; dir=$secretDir; target=$target; hash=$bindings[0].account_sha256; account=$accountProtected; secret=$tokenProtected }
    $account = $null
    $token.Dispose()
    $token = $null
}
# All account identities, distinct secrets and Disabled Tasks were checked
# before the first protected credential file is written.
$rows = @()
foreach ($entry in $entries) {
    if (-not (Test-Path -LiteralPath $entry.dir)) { New-Item -ItemType Directory -Path $entry.dir -ErrorAction Stop | Out-Null }
    secure-acl $entry.dir $sid $true
    $record = [ordered]@{
        schema='v20.08.1.dpapi_finam_pair.v1'; robot_id=$entry.robot
        account_sha256=$entry.hash; principal_sid=$sid
        mode='DPAPI_CURRENT_WINDOWS_USER_NO_LIVE_PERMISSION'
        account_dpapi=$entry.account; token_dpapi=$entry.secret
        live_enabled=$false
    }
    $body = $record | ConvertTo-Json -Depth 5
    $stream = [IO.File]::Open($entry.target,[IO.FileMode]::CreateNew,[IO.FileAccess]::Write,[IO.FileShare]::None)
    try {
        $bytes = [Text.UTF8Encoding]::new($false).GetBytes($body)
        $stream.Write($bytes,0,$bytes.Length)
        $stream.Flush()
    } finally { $stream.Dispose() }
    secure-acl $entry.target $sid $false
    $rows += [ordered]@{robot=$entry.robot;account_sha256=$entry.hash;status='DPAPI_SID_BOUND_LIVE_OFF'}
    Write-Output ('v20_08_1_dpapi_' + $entry.robot + '=PASS_SID_BOUND_LIVE_OFF')
}
$report = [ordered]@{
    schema='v20.08.1.dpapi_trading_bindings.v1'
    status='PASS_3_OF_3_DPAPI_LIVE_OFF'
    principal_sid=$sid; robots=$rows
    broker_orders=0; tasks_modified=$false; live_enabled=$false
    next_roadmap='V20-08.1'
}
$report | ConvertTo-Json -Depth 6 | Set-Content -LiteralPath $output -Encoding UTF8 -ErrorAction Stop
Write-Output 'v20_08_1_dpapi=pass_3_of_3_live_off'
Write-Output ('v20_08_1_dpapi_report=' + $output)
