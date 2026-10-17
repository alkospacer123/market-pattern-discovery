# IntradayLab M15 / roadmap 03-04. GitHub+synthetic tests only.
# SAFE: never use or change TradingSystemLab checkout, FINAM token, account,
# SQLite runtime, kill switch, live Task or broker order/cancel endpoints.
[CmdletBinding()]
param(
    [string]$TargetRoot = "C:\IntradayLab-M15-Audit",
    [string]$PythonExe = "python",
    [Parameter(Mandatory = $true)]
    [ValidatePattern('^[a-f0-9]{40}$')]
    [string]$ExpectedHeadSha
)
Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"
Write-Output "M15_OFFLINE_NO_FINAM_NO_TOKEN_NO_ORDER_NO_TASK_NO_H1_MUTATION=YES"

$target = [System.IO.Path]::GetFullPath($TargetRoot.TrimEnd([char]'\'))
if ($target -match '(?i)tradingsystemlab' -or $target -match '(?i)market-pattern-discovery') {
    throw "M15_TEST_TARGET_CANNOT_BE_H1_OR_PRODUCTION_REPOSITORY"
}
if (Test-Path -LiteralPath $target) {
    throw "M15_TEST_TARGET_MUST_NOT_EXIST__CHOOSE_FRESH_ISOLATED_DIRECTORY"
}
if (-not (Get-Command git -ErrorAction SilentlyContinue)) {
    throw "GIT_NOT_FOUND"
}
if (-not (Get-Command $PythonExe -ErrorAction SilentlyContinue)) {
    throw "PYTHON_NOT_FOUND"
}
$pythonMinor = (& $PythonExe -c "import sys; print(str(sys.version_info.major) + '.' + str(sys.version_info.minor))").Trim()
if ($LASTEXITCODE -ne 0 -or $pythonMinor -notin @("3.11", "3.12", "3.13")) {
    throw "M15_OFFLINE_UNSUPPORTED_PYTHON_${pythonMinor}__USE_PYTHON_3_12_OR_3_13"
}
$parent = Split-Path -Parent $target
# The parent can be a drive root such as C:\; never attempt to recreate it.
if (-not (Test-Path -LiteralPath $parent -PathType Container)) {
    [void][System.IO.Directory]::CreateDirectory($parent)
}

& git clone --quiet --no-checkout "https://github.com/alkospacer123/market-pattern-discovery.git" $target
if ($LASTEXITCODE -ne 0) { throw "ISOLATED_GIT_CLONE_FAILED" }
& git -C $target fetch --quiet origin "refs/pull/540/head"
if ($LASTEXITCODE -ne 0) { throw "DRAFT_540_GIT_FETCH_FAILED" }
$commit = (& git -C $target rev-parse FETCH_HEAD).Trim()
if ($commit -notmatch '^[0-9a-f]{40}$') { throw "DRAFT_540_SHA_INVALID" }
& git -C $target checkout --quiet --detach $commit
if ($LASTEXITCODE -ne 0) { throw "ISOLATED_CHECKOUT_FAILED" }
if ($commit -cne $ExpectedHeadSha) {
    throw "M15_DRAFT_540_SHA_CHANGED__EXPECTED_${ExpectedHeadSha}__ACTUAL_${commit}"
}
Write-Output "M15_DRAFT_540_SHA=$commit"

$venv = Join-Path $target ".m15_offline_venv"
& $PythonExe -m venv $venv
if ($LASTEXITCODE -ne 0) { throw "M15_ISOLATED_VENV_FAILED" }
$exe = Join-Path $venv "Scripts\python.exe"
if (-not (Test-Path -LiteralPath $exe)) { throw "M15_ISOLATED_PYTHON_MISSING" }
$req = Join-Path $target "IntradayLab\t3_m15_t1_entry_retest_v1\requirements.txt"
if (-not (Test-Path -LiteralPath $req)) { throw "PINNED_M15_RESEARCH_REQUIREMENTS_MISSING" }
& $exe -m pip install --only-binary=:all: --disable-pip-version-check -r $req
if ($LASTEXITCODE -ne 0) { throw "M15_DEPENDENCY_INSTALL_FAILED" }
$logDir = Join-Path $target "m15_offline_test_reports"
New-Item -Path $logDir -ItemType Directory -Force | Out-Null
$versions = Join-Path $logDir "versions.txt"
& $exe -c "import platform,pandas,numpy; print(platform.python_version()); print('pandas='+pandas.__version__); print('numpy='+numpy.__version__)" | Set-Content -Path $versions -Encoding UTF8
Push-Location $target
try {
    & $exe -m compileall -q "IntradayLab/m15_robot"
    if ($LASTEXITCODE -ne 0) { throw "M15_COMPILEALL_FAILED" }
    # unittest -v writes to stderr. On Windows PowerShell 5.1, redirecting
    # native stderr into a pipeline with ErrorActionPreference=Stop can raise
    # NativeCommandError despite an otherwise successful test process.
    $stdout = Join-Path $logDir "unittest.stdout.txt"
    $stderr = Join-Path $logDir "unittest.stderr.txt"
    $log = Join-Path $logDir "unittest.txt"
    $proc = Start-Process -FilePath $exe `
        -ArgumentList @("-m", "unittest", "discover", "-s", "IntradayLab/m15_robot/tests", "-v") `
        -WorkingDirectory $target -RedirectStandardOutput $stdout `
        -RedirectStandardError $stderr -Wait -PassThru -NoNewWindow
    $status = $proc.ExitCode
    $lines = @()
    if (Test-Path -LiteralPath $stdout) { $lines += @(Get-Content -LiteralPath $stdout) }
    if (Test-Path -LiteralPath $stderr) { $lines += @(Get-Content -LiteralPath $stderr) }
    $lines | Set-Content -LiteralPath $log -Encoding UTF8
    Write-Output "M15_UNITTEST_EXIT_CODE=$status"
    Write-Output "M15_UNITTEST_LOG=$log"
    if ($status -ne 0) {
        Get-Content -LiteralPath $log -Tail 35
        throw "M15_UNITTEST_NOT_PASS"
    }
    Get-Content -LiteralPath $log -Tail 8
    Write-Output "M15_OFFLINE_UNITTEST_PASS=YES"
} finally { Pop-Location }
