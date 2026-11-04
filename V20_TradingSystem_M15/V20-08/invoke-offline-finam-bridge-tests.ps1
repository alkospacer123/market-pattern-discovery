# v20-08.1 / offline-only python tests for newly added h1 finam read adapter.
# no finam calls, token reads, live state writes, task changes, order routes.
$ErrorActionPreference = 'Stop'
$pin = '6ddcaf39c71a496af25354f5c785052b7508de4e'
$root = 'c:\v20lab'
$source = Join-Path $root 'source-raw'
$python = Join-Path $root '.venv-raw\scripts\python.exe'
$workspace = Join-Path $root 'pretrade-08\bridge-tests'
if (-not (Test-Path -LiteralPath $source -PathType Container)) { throw 'v20_08_1_pinned_h1_source_missing' }
if (-not (Test-Path -LiteralPath $python -PathType Leaf)) { throw 'v20_08_1_python_missing' }
if (Test-Path -LiteralPath $workspace -PathType Leaf) { throw 'v20_08_1_workspace_invalid' }
$package = Join-Path $workspace 'V20_TradingSystem_M15\v20_runtime'
$tests = Join-Path $package 'tests'
New-Item -ItemType Directory -Force -Path $tests | Out-Null
$rows = @(
    @('v20_runtime/finam_execution.py','ea95905f6d31b5f8a6e1575e3721d634640806a3','finam_execution.py',$package),
    @('v20_runtime/tests/test_finam_execution.py','350e687b01603419c6956352471874ee12e34135','test_finam_execution.py',$tests)
)
foreach ($row in $rows) {
    $filename = $row[0]; $expected = $row[1]; $dest = Join-Path $row[3] $row[2]
    $url = 'https://raw.githubusercontent.com/alkospacer123/market-pattern-discovery/' + $pin + '/V20_TradingSystem_M15/' + $filename
    $temp = $dest + '.download'
    if (Test-Path -LiteralPath $temp) { throw 'v20_08_1_stale_download_detected' }
    try {
        Invoke-WebRequest -Uri $url -OutFile $temp -UseBasicParsing
        $hash = (& git.exe hash-object -- $temp).Trim().ToLowerInvariant()
        if ($LASTEXITCODE -ne 0 -or $hash -ne $expected) { throw 'v20_08_1_exact_git_blob_mismatch' }
        if (Test-Path -LiteralPath $dest) {
            $existing = (& git.exe hash-object -- $dest).Trim().ToLowerInvariant()
            if ($LASTEXITCODE -ne 0 -or $existing -ne $expected) { throw 'v20_08_1_existing_file_mismatch' }
        } else { Move-Item -LiteralPath $temp -Destination $dest }
    } finally {
        if (Test-Path -LiteralPath $temp) { Remove-Item -LiteralPath $temp -Force }
    }
}
$deps = @('__init__.py','account_risk.py','h1_state_journal.py','offline_planner.py')
foreach ($name in $deps) {
    $from = Join-Path $source ('V20_TradingSystem_M15\v20_runtime\' + $name)
    $to = Join-Path $package $name
    if (-not (Test-Path -LiteralPath $from -PathType Leaf)) { throw 'v20_08_1_pinned_v20_dependency_missing' }
    if (Test-Path -LiteralPath $to) {
        if ((Get-FileHash -LiteralPath $to -Algorithm SHA256).Hash -ne (Get-FileHash -LiteralPath $from -Algorithm SHA256).Hash) { throw 'v20_08_1_dependency_changed' }
    } else { Copy-Item -LiteralPath $from -Destination $to }
}
$oldPythonPath = $env:pythonpath
try {
    $env:pythonpath = $workspace + [IO.Path]::PathSeparator + $source
    $env:pythondontwritebytecode = '1'
    & $python -B -m unittest discover -s $tests -p 'test_finam_execution.py' -v
    if ($LASTEXITCODE -ne 0) { throw 'v20_08_1_finam_bridge_tests_failed' }
    Write-Output 'v20_08_1_bridge_tests=pass_7_of_7'
    Write-Output 'v20_08_1_live=off'
    Write-Output 'v20_08_1_orders=zero'
    Write-Output ('v20_08_1_source_pin=' + $pin)
} finally {
    $env:pythonpath = $oldPythonPath
}
