# V20-05.5: prepare a separate pinned V20 checkout, isolated Python and FakeBroker acceptance.
# Does NOT read FINAM credentials, place orders, touch H1/M15 or create/change Windows Tasks.
[CmdletBinding()]
param(
    [string]$Root = 'C:\V20Lab',
    [Parameter(Mandatory=$true)]
    [ValidatePattern('^[0-9a-fA-F]{40}$')]
    [string]$ExpectedSha
)
$ErrorActionPreference = 'Stop'
Set-StrictMode -Version Latest

function Invoke-Checked {
    param([string]$Executable, [string[]]$Arguments)
    & $Executable @Arguments
    if ($LASTEXITCODE -ne 0) {
        throw "COMMAND_FAILED: $Executable ($LASTEXITCODE); args: $($Arguments -join ' ')"
    }
}

if ($env:OS -ne 'Windows_NT') { throw 'NATIVE_WINDOWS_REQUIRED' }
$osInfo = Get-CimInstance Win32_OperatingSystem -ErrorAction Stop
# Verified Intel is URIU-PC: Windows 10 Pro 22H2, build 19045.
# Also allow the originally planned Windows Server 2022 (build 20348).
# ProductType=1 denotes client Windows; >=2 denotes Windows Server.
$isRealIntel = ($osInfo.ProductType -eq 1 -and $osInfo.Version -eq '10.0.19045' -and $osInfo.Caption -match 'Windows 10 Pro')
$isServer2022 = ($osInfo.ProductType -ne 1 -and $osInfo.BuildNumber -eq '20348')
if (-not ($isRealIntel -or $isServer2022)) {
    throw "WRONG_WINDOWS_HOST: $($osInfo.Caption), version=$($osInfo.Version), build=$($osInfo.BuildNumber)"
}
if (-not [Environment]::Is64BitOperatingSystem) { throw 'WINDOWS_X64_REQUIRED' }
$fullRoot = [IO.Path]::GetFullPath($Root).TrimEnd('\')
if (-not [string]::Equals($fullRoot, 'C:\V20Lab', [StringComparison]::OrdinalIgnoreCase)) {
    throw 'EXACT_C_V20LAB_ROOT_REQUIRED'
}
if (-not (Get-Command git.exe -ErrorAction SilentlyContinue)) {
    throw 'GIT_FOR_WINDOWS_NOT_INSTALLED'
}
if (Test-Path -LiteralPath $fullRoot) {
    $item = Get-Item -LiteralPath $fullRoot -Force
    if (-not $item.PSIsContainer -or ($item.Attributes -band [IO.FileAttributes]::ReparsePoint)) {
        throw 'V20_ROOT_INVALID_OR_REPARSE_POINT'
    }
} else {
    New-Item -ItemType Directory -Path $fullRoot -ErrorAction Stop | Out-Null
}
$checkout = Join-Path $fullRoot 'source'
$venv = Join-Path $fullRoot '.venv'
$scratch = Join-Path $fullRoot 'acceptance'
$branch = 'codex/v20-04-all-three-offline-foundation-20261021'
$remote = 'https://github.com/alkospacer123/market-pattern-discovery.git'

# Ctrl+C during a large clone may leave a partial source directory.
# Never remove it automatically. Work in a new private directory instead.
if (Test-Path -LiteralPath $checkout) {
    $existingHead = $null
    if (Test-Path -LiteralPath (Join-Path $checkout '.git')) {
        $existingHead = & git.exe -C $checkout rev-parse --verify HEAD 2>$null
    }
    if (-not $existingHead -or $LASTEXITCODE -ne 0) {
        $checkout = Join-Path $fullRoot 'source-fast'
        if (Test-Path -LiteralPath $checkout) {
            throw 'INTERRUPTED_SOURCE_AND_SOURCE_FAST_EXISTS_REQUIRES_MANUAL_DIAGNOSIS'
        }
        Write-Output "INCOMPLETE_SOURCE_LEFT_UNCHANGED; USING=$checkout"
    }
}
if (-not (Test-Path -LiteralPath $checkout)) {
    # Tree-less partial clone avoids fetching thousands of unrelated trees.
    # Preserve raw LF content: the acceptance receipt verifies byte-level SHA256.
    # Only this NEW checkout is modified. Git global configuration is not touched.
    Invoke-Checked 'git.exe' @('-c','core.autocrlf=false','-c','core.longpaths=true',
        'clone','--filter=tree:0','--sparse','--depth','1','--single-branch',
        '--branch',$branch,'--config','core.autocrlf=false',
        '--config','core.longpaths=true',$remote,$checkout)
} else {
    $item = Get-Item -LiteralPath $checkout -Force
    if (-not $item.PSIsContainer -or ($item.Attributes -band [IO.FileAttributes]::ReparsePoint)) {
        throw 'SOURCE_INVALID_OR_REPARSE_POINT'
    }
}
if (-not (Test-Path -LiteralPath (Join-Path $checkout '.git'))) {
    throw 'V20_SOURCE_IS_NOT_A_GIT_CHECKOUT'
}
# Only the three needed source trees: do not download unrelated research/data.
# Ensure origin/main exists: the pinned acceptance runner reads this ref.
# Fetch only the source files required by the acceptance, not historical CSV,
# archives or unrelated TradingSystemLab/IntradayLab/V20 research trees.
# --no-cone permits exact frozen reference file selection.
Invoke-Checked 'git.exe' @('-C',$checkout,'sparse-checkout','set','--no-cone','--',
    '/TradingSystemLab/stage8_robot/',
    '/IntradayLab/core/',
    '/V20_TradingSystem_M15/v20_runtime/',
    '/V20_TradingSystem_M15/V20-04/',
    '/V20_TradingSystem_M15/V20-05/',
    '/V20_TradingSystem_M15/V20-03/offline/stress_v20_03.py',
    '/V20_TradingSystem_M15/V20-03/comparison/QUOTE_PATH_DIAGNOSTICS.csv',
    '/V20_TradingSystem_M15/research_original_v20/base.py',
    '/V20_TradingSystem_M15/research_original_v20/run.py',
    '/V20_TradingSystem_M15/research_original_v20/legacy_v4/study_v4.py',
    '/V20_TradingSystem_M15/research_original_v20/legacy_v4/dependencies/study.py')
Invoke-Checked 'git.exe' @('-C',$checkout,'fetch','--filter=tree:0','--depth','1','origin',
    'refs/heads/main:refs/remotes/origin/main')
$origin = (& git.exe -C $checkout remote get-url origin)
if ($LASTEXITCODE -ne 0 -or $origin.Trim() -ne $remote) {
    throw 'WRONG_V20_GITHUB_REMOTE'
}
$actual = (& git.exe -C $checkout rev-parse HEAD)
if ($LASTEXITCODE -ne 0 -or $actual.Trim() -ne $ExpectedSha.ToLowerInvariant()) {
    throw "PINNED_COMMIT_MISMATCH: actual=$actual expected=$ExpectedSha; no auto update"
}
$dirty = @(& git.exe -C $checkout status --porcelain)
if ($LASTEXITCODE -ne 0 -or @($dirty | Where-Object { $_ }).Count -gt 0) {
    throw 'V20_SOURCE_DIRTY'
}
$runner = Join-Path $checkout 'V20_TradingSystem_M15\V20-05\Invoke-OfflineAcceptance.ps1'
if (-not (Test-Path -LiteralPath $runner -PathType Leaf)) {
    throw 'PINNED_WINDOWS_ACCEPTANCE_SCRIPT_MISSING'
}

$python = Join-Path $venv 'Scripts\python.exe'
if (-not (Test-Path -LiteralPath $python -PathType Leaf)) {
    if (Test-Path -LiteralPath $venv) {
        throw 'PARTIALLY_CREATED_VENV_REQUIRES_DIAGNOSIS_NOT_DELETION'
    }
    $launcher = Get-Command py.exe -ErrorAction SilentlyContinue
    if ($launcher) {
        Invoke-Checked $launcher.Source @('-3.12','-m','venv',$venv)
    } else {
        $launcher = Get-Command python.exe -ErrorAction SilentlyContinue
        if (-not $launcher) { throw 'PYTHON_3_12_NOT_FOUND' }
        Invoke-Checked $launcher.Source @('-m','venv',$venv)
    }
}
$version = & $python -c 'import sys; print("{}.{}".format(*sys.version_info[:2]))'
if ($LASTEXITCODE -ne 0 -or $version.Trim() -ne '3.12') {
    throw "V20_REQUIRES_ISOLATED_PYTHON_3_12: got=$version"
}
# Only new isolated venv receives dependencies. Never pip-install to H1/M15.
Invoke-Checked $python @('-m','pip','install','--disable-pip-version-check',
    'numpy==2.3.5','pandas==2.2.3','jsonschema>=4.0,<5','tabulate>=0.9,<1')
New-Item -ItemType Directory -Force -Path $scratch | Out-Null

# The wrapper itself requires native Windows Server 2022 and never creates Tasks.
$env:PYTHONDONTWRITEBYTECODE = '1'
$report = Join-Path $scratch 'WINDOWS_ACCEPTANCE_REPORT.json'
Write-Output "V20_GIT_PIN=$actual"
Write-Output "V20_ISOLATED_PYTHON=$python"
Write-Output 'V20_NO_FINAM_NO_TOKENS_NO_TASKS_NO_H1_MUTATION=YES'
& powershell.exe -NoProfile -ExecutionPolicy Bypass -File $runner -Checkout $checkout -Python $python -ScratchBase $scratch -ReportPath $report
if ($LASTEXITCODE -ne 0) { throw "V20_NATIVE_WINDOWS_ACCEPTANCE_FAILED; report=$report" }
if (-not (Test-Path -LiteralPath $report -PathType Leaf)) {
    throw 'WINDOWS_ACCEPTANCE_REPORT_NOT_CREATED'
}
$json = Get-Content -LiteralPath $report -Raw -Encoding UTF8 | ConvertFrom-Json
if ($json.stages.'V20-05.5' -ne 'PASS_NATIVE_WINDOWS' -or $json.tests.failed -ne 0 -or
    $json.tests.errors -ne 0 -or $json.tests.skipped -ne 0) {
    throw "WINDOWS_ACCEPTANCE_NOT_PASS; report=$report"
}
if ((& git.exe -C $checkout rev-parse HEAD).Trim() -ne $ExpectedSha.ToLowerInvariant()) {
    throw 'V20_PIN_CHANGED_DURING_ACCEPTANCE'
}
Write-Output "V20_05_5_NATIVE_WINDOWS=PASS"
Write-Output "V20_05_5_TESTS=$($json.tests.run)_PASS"
Write-Output "V20_05_5_REPORT=$report"
