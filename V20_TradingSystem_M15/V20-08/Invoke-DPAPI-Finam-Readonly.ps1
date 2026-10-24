# V20-08.1: one common H1 FINAM GET-only worker for three V20 DPAPI identities.
# Does not touch Tasks, H1/M15, order/SLTP APIs or any production state.
[CmdletBinding()]
param(
    [ValidateSet('preflight','witness')][string]$Mode = 'preflight',
    [ValidateSet('all','v20-shallow','v20-obv','v20-inside')][string]$Robot = 'all'
)
$ErrorActionPreference = 'Stop'
Set-StrictMode -Version Latest
$root = 'C:\V20Lab'
$source = Join-Path $root 'source-raw'
$workspace = Join-Path $root 'pretrade-08\dpapi-finam-readonly'
$python = Join-Path $root '.venv-raw\scripts\python.exe'
$receipt = Join-Path $root 'pretrade-08\DPAPI_TRADING_BINDINGS_REPORT.json'
$tasksReceipt = Join-Path $root 'staging-07\TASKS_07_2_REPORT.json'
$pin = '25d1630ce51629b5139ef708c6c2a1864e06cd1d'
function need([bool]$okay,[string]$code) { if (-not $okay) { throw $code } }
function digest([string]$val) {
    $sha=[Security.Cryptography.SHA256]::Create()
    try { return ([BitConverter]::ToString($sha.ComputeHash([Text.Encoding]::UTF8.GetBytes($val)))).Replace('-','').ToLowerInvariant() }
    finally { $sha.Dispose() }
}
function sid-of([string]$user) {
    if ($user -match '^S-[0-9]+(-[0-9]+)+$') { return ([Security.Principal.SecurityIdentifier]::new($user)).Value }
    return ([Security.Principal.NTAccount]::new($user)).Translate([Security.Principal.SecurityIdentifier]).Value
}
function no-link([string]$path) {
    if (Test-Path -LiteralPath $path) {
        need (-not ((Get-Item -LiteralPath $path -Force).Attributes -band [IO.FileAttributes]::ReparsePoint)) 'V20_08_1_PATH_LINK_FORBIDDEN'
    }
}
function plain([string]$cipher) {
    $secret = ConvertTo-SecureString -String $cipher -ErrorAction Stop
    $pointer = [IntPtr]::Zero
    try {
        $pointer = [Runtime.InteropServices.Marshal]::SecureStringToBSTR($secret)
        return [Runtime.InteropServices.Marshal]::PtrToStringBSTR($pointer)
    } finally {
        if ($pointer -ne [IntPtr]::Zero) { [Runtime.InteropServices.Marshal]::ZeroFreeBSTR($pointer) }
        $secret.Dispose()
    }
}
need ($env:OS -eq 'Windows_NT' -and $env:COMPUTERNAME -eq 'URIU-PC') 'V20_08_1_WRONG_INTEL'
need (Test-Path -LiteralPath $receipt -PathType Leaf) 'V20_08_1_DPAPI_RECEIPT_MISSING'
need (Test-Path -LiteralPath $tasksReceipt -PathType Leaf) 'V20_08_1_TASK_RECEIPT_MISSING'
need (Test-Path -LiteralPath $source -PathType Container) 'V20_08_1_SOURCE_MISSING'
need (Test-Path -LiteralPath $python -PathType Leaf) 'V20_08_1_PYTHON_MISSING'
foreach ($path in @($root,$source,(Join-Path $root 'pretrade-08'),$receipt,$tasksReceipt)) { no-link $path }
$report = Get-Content -LiteralPath $receipt -Raw -Encoding UTF8 | ConvertFrom-Json
$tasks = Get-Content -LiteralPath $tasksReceipt -Raw -Encoding UTF8 | ConvertFrom-Json
$sid = [Security.Principal.WindowsIdentity]::GetCurrent().User.Value
need ($report.schema -eq 'v20.08.1.dpapi_trading_bindings.v1' -and
      $report.status -eq 'PASS_3_OF_3_DPAPI_LIVE_OFF' -and
      $report.live_enabled -eq $false -and
      $report.principal_sid -eq $sid -and
      $tasks.status -eq 'PASS_3_OF_3_DISABLED' -and
      $tasks.principal_sid -eq $sid) 'V20_08_1_DPAPI_OR_SID_RECEIPT_INVALID'
$names = if ($Robot -eq 'all') { @('v20-shallow','v20-obv','v20-inside') } else { @($Robot) }
if ($Mode -eq 'witness') { need ($names.Count -eq 1) 'V20_08_1_WITNESS_ONE_ACCOUNT_ONLY' }
$pkg = Join-Path $workspace 'V20_TradingSystem_M15\v20_runtime'
New-Item -ItemType Directory -Path $pkg -Force | Out-Null
$files = @(
    @('finam_worker.py','4d9de12e0b3e9d0d0ec72d058840bb259e2ed30d'),
    @('finam_execution.py','5e76df4085665559e4056f07f4ddf8b6574048ef'),
    @('h1_state_journal.py','f9fb32a50eb712aeae4690dd85d4e7aa512ef15c')
)
foreach ($entry in $files) {
    $to = Join-Path $pkg $entry[0]
    no-link $to
    if (Test-Path -LiteralPath $to) {
        $hash = (& git.exe hash-object -- $to).Trim().ToLowerInvariant()
        need ($LASTEXITCODE -eq 0 -and $hash -eq $entry[1]) 'V20_08_1_WORKER_CODE_CONFLICT'
        continue
    }
    $url = 'https://raw.githubusercontent.com/alkospacer123/market-pattern-discovery/' + $pin + '/V20_TradingSystem_M15/v20_runtime/' + $entry[0]
    $tmp = $to + '.download'
    need (-not (Test-Path -LiteralPath $tmp)) 'V20_08_1_PARTIAL_DOWNLOAD'
    try {
        Invoke-WebRequest -Uri $url -OutFile $tmp -UseBasicParsing
        $hash = (& git.exe hash-object -- $tmp).Trim().ToLowerInvariant()
        need ($LASTEXITCODE -eq 0 -and $hash -eq $entry[1]) 'V20_08_1_WORKER_GIT_BLOB_MISMATCH'
        Move-Item -LiteralPath $tmp -Destination $to
    } finally {
        if (Test-Path -LiteralPath $tmp) { Remove-Item -LiteralPath $tmp -Force }
    }
}
foreach ($name in @('__init__.py','account_risk.py','offline_planner.py','frozen_adapter.py')) {
    $from = Join-Path $source ('V20_TradingSystem_M15\v20_runtime\' + $name)
    $to = Join-Path $pkg $name
    need (Test-Path -LiteralPath $from -PathType Leaf) 'V20_08_1_PINNED_DEPENDENCY_MISSING'
    no-link $to
    if (Test-Path -LiteralPath $to) {
        need ((Get-FileHash -LiteralPath $from -Algorithm SHA256).Hash -eq
              (Get-FileHash -LiteralPath $to -Algorithm SHA256).Hash) 'V20_08_1_DEPENDENCY_CONFLICT'
    } else { Copy-Item -LiteralPath $from -Destination $to }
}
$previousPath=$env:PYTHONPATH
$previousAccount=$env:V20_FINAM_ACCOUNT
$previousToken=$env:V20_FINAM_TOKEN
$previousHash=$env:V20_FINAM_ACCOUNT_SHA256
$previousNoBytecode=$env:PYTHONDONTWRITEBYTECODE
try {
    $env:PYTHONPATH=$workspace + [IO.Path]::PathSeparator + $source
    $env:PYTHONDONTWRITEBYTECODE='1'
    # Before decrypting any real token, prove the H1 REST adapter denies all
    # order/SLTP/DELETE and cross-account routes with synthetic credentials.
    & $python -B -m V20_TradingSystem_M15.v20_runtime.finam_worker --self-test
    need ($LASTEXITCODE -eq 0) 'V20_08_1_WORKER_SELFTEST_FAILED'
    foreach ($name in $names) {
        $rows = @($report.robots | Where-Object { $_.robot -eq $name })
        need ($rows.Count -eq 1 -and $rows[0].status -eq 'DPAPI_SID_BOUND_LIVE_OFF') 'V20_08_1_DPAPI_ROBOT_NOT_BOUND'
        $task=Get-ScheduledTask -TaskName $name -TaskPath '\' -ErrorAction Stop
        need ($task.State -eq 'Disabled' -and @($task.Actions).Count -eq 1 -and
              $task.Actions[0].Arguments.Contains('v20-task-live-blocked.ps1') -and
              (sid-of ([string]$task.Principal.UserId)) -eq $sid) 'V20_08_1_TASK_NOT_DISABLED_OR_WRONG_SID'
        $secretPath=Join-Path (Join-Path $root ('robots\' + $name.Substring(4))) 'secrets\finam.dpapi.json'
        need (Test-Path -LiteralPath $secretPath -PathType Leaf) 'V20_08_1_DPAPI_FILE_MISSING'
        no-link $secretPath
        $secret=Get-Content -LiteralPath $secretPath -Raw -Encoding UTF8 | ConvertFrom-Json
        need ($secret.schema -eq 'v20.08.1.dpapi_finam_pair.v1' -and
              $secret.robot_id -eq $name -and $secret.live_enabled -eq $false -and
              $secret.principal_sid -eq $sid -and
              $secret.account_sha256 -eq $rows[0].account_sha256) 'V20_08_1_DPAPI_FILE_SCOPE_INVALID'
        $env:V20_FINAM_ACCOUNT=plain ([string]$secret.account_dpapi)
        $env:V20_FINAM_TOKEN=plain ([string]$secret.token_dpapi)
        $env:V20_FINAM_ACCOUNT_SHA256=[string]$secret.account_sha256
        need ((digest $env:V20_FINAM_ACCOUNT) -ceq $env:V20_FINAM_ACCOUNT_SHA256) 'V20_08_1_DPAPI_ACCOUNT_DECRYPT_MISMATCH'
        try {
            $args=@('-B','-m','V20_TradingSystem_M15.v20_runtime.finam_worker','--robot',$name)
            if ($Mode -eq 'witness') { $args += '--witness-current-open' }
            & $python @args
            need ($LASTEXITCODE -eq 0) 'V20_08_1_WORKER_READONLY_CHECK_FAILED'
        } finally {
            Remove-Item Env:\V20_FINAM_ACCOUNT -ErrorAction SilentlyContinue
            Remove-Item Env:\V20_FINAM_TOKEN -ErrorAction SilentlyContinue
            Remove-Item Env:\V20_FINAM_ACCOUNT_SHA256 -ErrorAction SilentlyContinue
        }
    }
    Write-Output ('v20_08_1_worker=' + $(if($Mode -eq 'preflight') {'pass_get_only_'+$names.Count+'_of_'+$names.Count} else {'pass_one_account_witness_mode'}))
    Write-Output 'v20_08_1_live=off'
    Write-Output 'v20_08_1_tasks_modified=no'
} finally {
    $env:PYTHONPATH=$previousPath
    $env:PYTHONDONTWRITEBYTECODE=$previousNoBytecode
    $env:V20_FINAM_ACCOUNT=$previousAccount
    $env:V20_FINAM_TOKEN=$previousToken
    $env:V20_FINAM_ACCOUNT_SHA256=$previousHash
}
