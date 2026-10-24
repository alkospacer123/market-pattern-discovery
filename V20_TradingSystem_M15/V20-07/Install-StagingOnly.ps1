# V20-07.1: install pinned source and empty isolated directories only.
# Does not start robots, touch H1/M15 tasks, read trading tokens, or place orders.
[CmdletBinding()]
param()
$ErrorActionPreference = 'Stop'
Set-StrictMode -Version Latest
$root = 'C:\V20Lab'
$raw = Join-Path $root 'source-raw'
$python = Join-Path $root '.venv-raw\scripts\python.exe'
$stage = Join-Path $root 'staging-07'
$checkout = Join-Path $stage 'checkout'
$instances = Join-Path $root 'robots'
$report = Join-Path $stage 'INSTALL_07_1_REPORT.json'
$funded = Join-Path $root 'readonly-06\BROKER_READONLY_REPORT_FUNDED.json'
$pin = '610109b736c53a5cc1025657291e272b1136b254'
$repo = 'https://github.com/alkospacer123/market-pattern-discovery.git'
$expectedRunnerBlob = '41c17be3469fd371d0288db78914ecc492197464'
function require([bool]$condition, [string]$code) {
    if (-not $condition) { throw $code }
}
function folder([string]$path) {
    if (Test-Path -LiteralPath $path) {
        $item = Get-Item -LiteralPath $path -Force
        require ($item.PSIsContainer -and -not ($item.Attributes -band [IO.FileAttributes]::ReparsePoint)) "REPARSE_OR_NON_DIRECTORY_FORBIDDEN"
    } else {
        [void](New-Item -ItemType Directory -Path $path -ErrorAction Stop)
    }
}
function gitrun([string[]]$arguments) {
    & git.exe @arguments
    require ($LASTEXITCODE -eq 0) 'GIT_COMMAND_FAILED'
}
require ($env:OS -eq 'Windows_NT' -and $env:COMPUTERNAME -eq 'URIU-PC') 'WRONG_WINDOWS_HOST'
$os = Get-CimInstance Win32_OperatingSystem -ErrorAction Stop
require ($os.Version -eq '10.0.19045' -and $os.Caption -match 'Windows 10 Pro') 'UNEXPECTED_WINDOWS_BUILD'
require (Test-Path -LiteralPath $root -PathType Container) 'V20_ROOT_MISSING'
folder $root
require (Test-Path -LiteralPath (Join-Path $raw 'TradingSystemLab\stage8_robot\finam_api.py') -PathType Leaf) 'H1_RAW_DEPENDENCY_MISSING'
require (Test-Path -LiteralPath (Join-Path $raw 'IntradayLab\core\execution.py') -PathType Leaf) 'M15_RAW_DEPENDENCY_MISSING'
require (Test-Path -LiteralPath $python -PathType Leaf) 'PINNED_PYTHON_MISSING'
require (Test-Path -LiteralPath $funded -PathType Leaf) 'V20_06_FUNDED_REPORT_MISSING'
$proof = Get-Content -LiteralPath $funded -Encoding UTF8 -Raw | ConvertFrom-Json
require ($proof.schema -eq 'v20.finam.broker_readonly_report.v1' -and $proof.status -eq 'PASS_READONLY_3_OF_3' -and $proof.entry_authorized -eq $false) 'V20_06_FUNDED_READONLY_NOT_PASS'
$rows = @($proof.accounts)
require ($rows.Count -eq 3) 'ACCOUNT_PROOF_COUNT_MISMATCH'
$names = @('v20-shallow','v20-obv','v20-inside')
foreach ($name in $names) {
    $match = @($rows | Where-Object { $_.robot -eq $name })
    require ($match.Count -eq 1 -and $match[0].readonly_result -eq 'PASS_READONLY' -and $match[0].account_clean -eq $true) 'ACCOUNT_PROOF_NOT_CLEAN'
}
require ($null -ne (Get-Command git.exe -ErrorAction SilentlyContinue)) 'GIT_MISSING'
require (-not (Test-Path -LiteralPath $report)) 'STAGING_REPORT_EXISTS_NO_OVERWRITE'
folder $stage
require (-not (Test-Path -LiteralPath $checkout)) 'CHECKOUT_EXISTS_NO_OVERWRITE'
folder $checkout
# Sparse-filter avoids copying multi-GB IntradayLab history. H1/M15 reuse source-raw.
gitrun @('-C',$checkout,'init','-q')
gitrun @('-C',$checkout,'remote','add','origin',$repo)
gitrun @('-C',$checkout,'sparse-checkout','init','--cone')
gitrun @('-C',$checkout,'sparse-checkout','set','V20_TradingSystem_M15')
gitrun @('-C',$checkout,'fetch','--depth','1','--filter=blob:none','origin',$pin)
gitrun @('-C',$checkout,'checkout','--detach','--quiet',$pin)
$sha = (& git.exe -C $checkout rev-parse HEAD).Trim()
require ($LASTEXITCODE -eq 0 -and $sha -eq $pin) 'PINNED_COMMIT_MISMATCH'
$runner = Join-Path $checkout 'V20_TradingSystem_M15\v20_runtime\m15_runner.py'
require (Test-Path -LiteralPath $runner -PathType Leaf) 'V20_RUNNER_MISSING'
$blob = (& git.exe hash-object -- $runner).Trim()
require ($LASTEXITCODE -eq 0 -and $blob -eq $expectedRunnerBlob) 'RUNNER_BLOB_MISMATCH'
$dirty = @(& git.exe -C $checkout status --porcelain | Where-Object { $_ })
require ($LASTEXITCODE -eq 0 -and $dirty.Count -eq 0) 'STAGING_CHECKOUT_DIRTY'
$previousPath = $env:PYTHONPATH
try {
    $env:PYTHONPATH = "$checkout;$raw"
    & $python -B -c 'import V20_TradingSystem_M15.v20_runtime.m15_runner; print("V20_07_1_IMPORT_CHECK=PASS_OFFLINE_ONLY")'
    require ($LASTEXITCODE -eq 0) 'OFFLINE_IMPORT_FAILED'
} finally {
    $env:PYTHONPATH = $previousPath
}
folder $instances
$installed = @()
foreach ($name in $names) {
    $short = $name.Substring(4)
    $home = Join-Path $instances $short
    folder $home
    foreach ($dir in @('config','state','logs','secrets')) { folder (Join-Path $home $dir) }
    $conf = Join-Path $home 'config\staging.json'
    require (-not (Test-Path -LiteralPath $conf)) 'STAGING_CONFIG_EXISTS_NO_OVERWRITE'
    $match = @($rows | Where-Object { $_.robot -eq $name })[0]
    $entry = [ordered]@{
        schema = 'v20.intel.staging.v1'
        robot_id = $name
        account_sha256 = $match.account_sha256
        symbols = @('USDRUBF','CNYRUBF','GLDRUBF','IMOEXF')
        source_commit = $pin
        execution_mode = 'DISABLED_NOT_LIVE'
        trading_token = 'NOT_CONFIGURED'
        windows_task = 'NOT_REGISTERED_07_1'
        live_enabled = $false
    }
    $entry | ConvertTo-Json -Depth 6 | Set-Content -LiteralPath $conf -Encoding UTF8
    $installed += [ordered]@{ robot = $name; directory = $home; source_sha = $pin; live_enabled = $false; task_registered = $false }
    Write-Output ("V20_07_1_" + $name + "=INSTALLED_LIVE_OFF")
}
$record = [ordered]@{
    schema = 'v20.intel.stage07.install.1'
    result = 'PASS_STAGING_ONLY_3_OF_3'
    source_commit = $pin
    root = $root
    source_directory = $checkout
    h1_m15_source = $raw
    python = $python
    finam_used = $false
    orders_sent = 0
    trading_tokens_used = $false
    tasks_modified = $false
    h1_m15_modified = $false
    live_enabled = $false
    machines = @($env:COMPUTERNAME)
    robots = $installed
    next_roadmap = 'V20-07.2'
}
$record | ConvertTo-Json -Depth 8 | Set-Content -LiteralPath $report -Encoding UTF8
Write-Output 'V20_07_1_RESULT=PASS_STAGING_ONLY_3_OF_3'
Write-Output ("V20_07_1_PINNED_SHA=" + $pin)
Write-Output ("V20_07_1_REPORT=" + $report)
Write-Output 'V20_07_1_NO_ORDERS_NO_FINAM_NO_TASK_MUTATION_NO_H1_M15_CHANGES=YES'
