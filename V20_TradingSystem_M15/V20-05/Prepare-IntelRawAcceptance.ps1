# V20-05.5: direct pinned RAW transport; no clone and no interaction with H1/M15.
# Fresh isolated C:\V20Lab\source-raw, .venv-raw, acceptance-raw.
[CmdletBinding()]
param()
$ErrorActionPreference = 'Stop'
Set-StrictMode -Version Latest
$root = 'C:\V20Lab'
$source = Join-Path $root 'source-raw'
$venv = Join-Path $root '.venv-raw'
$scratch = Join-Path $root 'acceptance-raw'
$repo = 'alkospacer123/market-pattern-discovery'
$manifestCommit = '7d8701795c65023ce564e48f8c25d2e0e34c45cb'
$manifestGitBlob = '1caf543ad547503bf4ce8c14c1a5a52212c22b7a'
$sourceCommit = '52e8be3bb11eb5e968abab502acfebaa200b2b62'
$mainCommit = '6f352acfac7ebdfabba73e143c4dfea3a6e48507'

function checked {
    param([string]$executable, [string[]]$argumentlist)
    # Powershell reserves $args as an automatic variable. Never use it
    # as a user-defined parameter: positional arguments can disappear.
    & $executable @argumentlist
    if ($LASTEXITCODE -ne 0) {
        throw "COMMAND_FAILED: $executable; exit=$LASTEXITCODE; args=$($argumentlist -join ' ')"
    }
}
function verified-blob {
    param([string]$path, [string]$sha)
    if (-not (Test-Path -LiteralPath $path -PathType Leaf)) { return $false }
    $actual = (& git.exe hash-object -- $path)
    if ($LASTEXITCODE -ne 0) { throw "GIT_HASH_OBJECT_FAILED: $path" }
    return [string]::Equals($actual.Trim(), $sha, [StringComparison]::OrdinalIgnoreCase)
}
function pinned-download {
    param([string]$url, [string]$target, [string]$sha)
    if (verified-blob $target $sha) { return }
    $dir = Split-Path -Parent $target
    if (-not (Test-Path -LiteralPath $dir)) {
        New-Item -ItemType Directory -Path $dir -Force | Out-Null
    }
    $temp = "$target.download-$PID"
    if (Test-Path -LiteralPath $temp) {
        throw "PREEXISTING_DOWNLOAD_TEMP_REQUIRES_DIAGNOSIS: $temp"
    }
    try {
        Invoke-WebRequest -Uri $url -OutFile $temp -UseBasicParsing -ErrorAction Stop
        if (-not (verified-blob $temp $sha)) { throw "PINNED_GIT_BLOB_MISMATCH: $target" }
        Move-Item -LiteralPath $temp -Destination $target -Force -ErrorAction Stop
    } finally {
        if (Test-Path -LiteralPath $temp) {
            Remove-Item -LiteralPath $temp -Force -ErrorAction SilentlyContinue
        }
    }
}

if ($env:OS -ne 'Windows_NT') { throw 'WINDOWS_REQUIRED' }
$os = Get-CimInstance Win32_OperatingSystem -ErrorAction Stop
if (-not ($os.ProductType -eq 1 -and $os.Version -eq '10.0.19045' -and
        $os.Caption -match 'Windows 10 Pro')) {
    throw "UNEXPECTED_WINDOWS: $($os.Caption) / $($os.Version)"
}
if ($env:COMPUTERNAME -ne 'URIU-PC') { throw "WRONG_INTEL_MACHINE: $env:COMPUTERNAME" }
if (-not (Get-Command git.exe -ErrorAction SilentlyContinue)) { throw 'GIT_NOT_INSTALLED' }
if (Test-Path -LiteralPath $root) {
    if ((Get-Item -LiteralPath $root).Attributes -band [IO.FileAttributes]::ReparsePoint) {
        throw 'ROOT_IS_REPARSE_POINT'
    }
} else {
    New-Item -ItemType Directory -Path $root | Out-Null
}
foreach ($directory in @($source,$scratch)) {
    if (Test-Path -LiteralPath $directory) {
        if ((Get-Item -LiteralPath $directory).Attributes -band [IO.FileAttributes]::ReparsePoint) {
            throw "REPARSE_POINT_FORBIDDEN: $directory"
        }
    } else {
        New-Item -ItemType Directory -Path $directory -Force | Out-Null
    }
}
if (Test-Path -LiteralPath (Join-Path $source '.git')) {
    throw 'RAW_SOURCE_MUST_NOT_BE_GIT_CHECKOUT'
}
$manifestRel = 'V20_TradingSystem_M15/V20-05/RAW_FILE_MANIFEST.json'
$manifestTarget = Join-Path $source ($manifestRel.Replace('/', '\'))
$manifestUrl = "https://raw.githubusercontent.com/$repo/$manifestCommit/$manifestRel"
pinned-download $manifestUrl $manifestTarget $manifestGitBlob
$manifest = Get-Content -LiteralPath $manifestTarget -Raw -Encoding UTF8 | ConvertFrom-Json
if ($manifest.schema -ne 'v20.windows.raw_pinned_manifest.v1' -or
    $manifest.source_commit -ne $sourceCommit -or
    $manifest.main_commit -ne $mainCommit -or
    $manifest.repository -ne $repo -or
    $manifest.mode -ne 'OFFLINE_FAKE_ONLY') {
    throw 'RAW_MANIFEST_IDENTITY_MISMATCH'
}
$items = @($manifest.files)
if ($items.Count -lt 30 -or $items.Count -gt 250) {
    throw 'RAW_MANIFEST_FILE_COUNT_INVALID'
}
Write-Output "V20_PINNED_RAW_START files=$($items.Count)"
$counter=0
foreach ($item in $items) {
    $relative = [string]$item.path
    $blob = [string]$item.sha
    if ($relative -notmatch '^(TradingSystemLab|IntradayLab|V20_TradingSystem_M15)/[a-zA-Z0-9_./-]+$' -or
        $relative.Contains('..') -or $blob -notmatch '^[a-f0-9]{40}$') {
        throw "UNSAFE_RAW_MANIFEST_ENTRY: $relative"
    }
    $target = Join-Path $source ($relative.Replace('/', '\'))
    $url = "https://raw.githubusercontent.com/$repo/$sourceCommit/$relative"
    pinned-download $url $target $blob
    $counter++
    if (($counter % 20) -eq 0 -or $counter -eq $items.Count) {
        Write-Output "V20_PINNED_RAW=$counter/$($items.Count)"
    }
}
$python = Join-Path $venv 'Scripts\python.exe'
if (-not (Test-Path -LiteralPath $python -PathType Leaf)) {
    if (Test-Path -LiteralPath $venv) {
        throw 'EXISTING_PARTIAL_VENV_REQUIRES_DIAGNOSIS'
    }
    $pyLauncher = Get-Command py.exe -ErrorAction SilentlyContinue
    if ($pyLauncher) {
        checked -executable $pyLauncher.Source -argumentlist @('-3.12','-m','venv',$venv)
    } else {
        $pyLauncher = Get-Command python.exe -ErrorAction SilentlyContinue
        if (-not $pyLauncher) { throw 'PYTHON_3_12_NOT_FOUND' }
        checked -executable $pyLauncher.Source -argumentlist @('-m','venv',$venv)
    }
}
$pyVersion = & $python -c 'import sys;print(sys.version_info.major,sys.version_info.minor,sep=chr(46))'
if ($LASTEXITCODE -ne 0 -or $pyVersion.Trim() -ne '3.12') {
    throw "PYTHON_3_12_REQUIRED: $pyVersion"
}
checked -executable $python -argumentlist @('-m','pip','install','--disable-pip-version-check',
    'numpy==2.3.5','pandas==2.2.3','jsonschema>=4.0,<5','tabulate>=0.9,<1')
$env:V20_MAIN_SHA_PIN = $mainCommit
$env:V20_SOURCE_SHA_PIN = $sourceCommit
$env:PYTHONDONTWRITEBYTECODE = '1'
$runner = Join-Path $source 'V20_TradingSystem_M15\V20-05\Invoke-OfflineAcceptance.ps1'
$report = Join-Path $scratch 'WINDOWS_ACCEPTANCE_REPORT.json'
Write-Output 'V20_NO_CLONE_NO_FINAM_NO_TASKS_NO_H1_MUTATION=YES'
& powershell.exe -NoProfile -ExecutionPolicy Bypass -File $runner -Checkout $source -Python $python -ScratchBase $scratch -ReportPath $report
if ($LASTEXITCODE -ne 0) { throw "V20_WINDOWS_ACCEPTANCE_FAILED; report=$report" }
$data = Get-Content -LiteralPath $report -Raw -Encoding UTF8 | ConvertFrom-Json
if ($data.stages.'V20-05.5' -ne 'PASS_NATIVE_WINDOWS' -or $data.tests.failed -ne 0 -or
    $data.tests.errors -ne 0 -or $data.tests.skipped -ne 0) {
    throw "V20_WINDOWS_ACCEPTANCE_NOT_PASS: $report"
}
Write-Output "V20_05_5_NATIVE_WINDOWS=PASS"
Write-Output "V20_05_5_TESTS=$($data.tests.run)_PASS"
Write-Output "V20_05_5_REPORT=$report"
