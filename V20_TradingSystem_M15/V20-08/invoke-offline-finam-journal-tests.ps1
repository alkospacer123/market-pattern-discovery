# V20-08.1 isolated H1 SQLite journal new-only tests; no FINAM, tokens or Tasks.
$ErrorActionPreference = 'Stop'
$pin = '78086ffa75279e8cafe9b0baf6585f03150848bb'
$root = 'c:\v20lab'
$source = Join-Path $root 'source-raw'
$python = Join-Path $root '.venv-raw\scripts\python.exe'
$workspace = Join-Path $root 'pretrade-08\journal-tests-path-v2'
if (-not (Test-Path -LiteralPath $source -PathType Container)) { throw 'v20_source_raw_missing' }
if (-not (Test-Path -LiteralPath $python -PathType Leaf)) { throw 'v20_python_missing' }
$package = Join-Path $workspace 'V20_TradingSystem_M15\v20_runtime'
$tests = Join-Path $package 'tests'
New-Item -ItemType Directory -Force -Path $tests | Out-Null
$items = @(
    @('v20_runtime/finam_execution.py','5556e3845262f5a17b9153a16ebed7d834c7092d',$package,'finam_execution.py'),
    @('v20_runtime/h1_state_journal.py','68988932c11241cb34273b745dda7764e35d9e62',$package,'h1_state_journal.py'),
    @('v20_runtime/tests/test_finam_journal.py','e0c4a939a125f3513aad9a8144159ddbabcf996c',$tests,'test_finam_journal.py')
)
foreach ($item in $items) {
    $path = Join-Path $item[2] $item[3]
    $uri = 'https://raw.githubusercontent.com/alkospacer123/market-pattern-discovery/' + $pin + '/V20_TradingSystem_M15/' + $item[0]
    $tmp = $path + '.download'
    if (Test-Path -LiteralPath $tmp) { throw 'v20_partial_download_present' }
    try {
        Invoke-WebRequest -Uri $uri -OutFile $tmp -UseBasicParsing
        $hash = (& git.exe hash-object -- $tmp).Trim().ToLowerInvariant()
        if ($LASTEXITCODE -ne 0 -or $hash -ne $item[1]) { throw 'v20_journal_git_blob_mismatch' }
        if (Test-Path -LiteralPath $path) {
            $old = (& git.exe hash-object -- $path).Trim().ToLowerInvariant()
            if ($LASTEXITCODE -ne 0 -or $old -ne $item[1]) { throw 'v20_journal_existing_file_mismatch' }
        } else { Move-Item -LiteralPath $tmp -Destination $path }
    } finally {
        if (Test-Path -LiteralPath $tmp) { Remove-Item -LiteralPath $tmp -Force }
    }
}
foreach ($name in @('__init__.py','offline_planner.py','account_risk.py','frozen_adapter.py')) {
    $original = Join-Path $source ('V20_TradingSystem_M15\v20_runtime\' + $name)
    $target = Join-Path $package $name
    if (-not (Test-Path -LiteralPath $original -PathType Leaf)) { throw 'v20_required_pinned_dependency_missing' }
    if (Test-Path -LiteralPath $target) {
        if ((Get-FileHash -LiteralPath $original -Algorithm SHA256).Hash -ne (Get-FileHash -LiteralPath $target -Algorithm SHA256).Hash) { throw 'v20_journal_dependency_conflict' }
    } else { Copy-Item -LiteralPath $original -Destination $target }
}
$oldPath = $env:pythonpath
$oldByteCode = $env:pythondontwritebytecode
try {
    $env:pythonpath = $workspace + [IO.Path]::PathSeparator + $source
    $env:pythondontwritebytecode = '1'
    & $python -B -m unittest discover -s $tests -p 'test_finam_journal.py' -v
    if ($LASTEXITCODE -ne 0) { throw 'v20_journal_tests_failed' }
    Write-Output 'v20_08_1_journal_tests=pass_5_of_5'
    Write-Output 'v20_08_1_live=off'
    Write-Output 'v20_08_1_orders=zero'
    Write-Output ('v20_08_1_source_pin=' + $pin)
} finally {
    $env:pythonpath = $oldPath
    $env:pythondontwritebytecode = $oldByteCode
}
