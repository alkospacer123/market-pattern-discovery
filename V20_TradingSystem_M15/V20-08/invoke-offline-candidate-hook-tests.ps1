# 08.1 offline-only targeted check: no FINAM, DPAPI, V20 Task, H1/M15 mutation.
$ErrorActionPreference = 'Stop'
Set-StrictMode -Version Latest
$pin = 'd927d183c5c7de3b903236006450c2bf01e73a7d'
$root = 'c:\v20lab'
$source = Join-Path $root 'source-raw'
$python = Join-Path $root '.venv-raw\scripts\python.exe'
$workspace = Join-Path $root 'pretrade-08\candidate-hook-test-d927d183'
if (-not (Test-Path -LiteralPath $source -PathType Container)) { throw 'v20_08_1_source_missing' }
if (-not (Test-Path -LiteralPath $python -PathType Leaf)) { throw 'v20_08_1_python_missing' }
$pkg = Join-Path $workspace 'V20_TradingSystem_M15\v20_runtime'
$tests = Join-Path $pkg 'tests'
New-Item -ItemType Directory -Path $tests -Force | Out-Null
$files = @(
    @('v20_runtime/finam_worker.py','8a45b3bba575f882f01fd9fe9aafab8cdb280b58',$pkg,'finam_worker.py'),
    @('v20_runtime/finam_execution.py','f91d3c6c0dff517274809c676bd332417aafa80f',$pkg,'finam_execution.py'),
    @('v20_runtime/h1_state_journal.py','68988932c11241cb34273b745dda7764e35d9e62',$pkg,'h1_state_journal.py'),
    @('v20_runtime/tests/test_finam_candidate_worker.py','9b25b75d943860d900c402cdc11353af0464cedf',$tests,'test_finam_candidate_worker.py'),
    @('v20_runtime/tests/test_finam_next_open_bridge.py','f4bc65b1ff54f8940be9db818de35d09d3252100',$tests,'test_finam_next_open_bridge.py')
)
foreach ($entry in $files) {
    $target = Join-Path $entry[2] $entry[3]
    $tmp = $target + '.download'
    if (Test-Path -LiteralPath $tmp) { throw 'v20_08_1_incomplete_previous_download' }
    try {
        $url='https://raw.githubusercontent.com/alkospacer123/market-pattern-discovery/'+$pin+'/V20_TradingSystem_M15/'+$entry[0]
        Invoke-WebRequest -Uri $url -OutFile $tmp -UseBasicParsing
        $sha = (& git.exe hash-object -- $tmp).Trim().ToLowerInvariant()
        if ($LASTEXITCODE -ne 0 -or $sha -ne $entry[1]) { throw 'v20_08_1_candidate_pin_mismatch' }
        if (Test-Path -LiteralPath $target) {
            $existing = (& git.exe hash-object -- $target).Trim().ToLowerInvariant()
            if ($LASTEXITCODE -ne 0 -or $existing -ne $entry[1]) { throw 'v20_08_1_candidate_file_conflict' }
        } else { Move-Item -LiteralPath $tmp -Destination $target }
    } finally { if (Test-Path -LiteralPath $tmp) { Remove-Item -LiteralPath $tmp -Force } }
}
foreach ($name in @('__init__.py','offline_planner.py','account_risk.py','frozen_adapter.py')) {
    $from = Join-Path $source ('V20_TradingSystem_M15\v20_runtime\' + $name)
    $target = Join-Path $pkg $name
    if (-not (Test-Path -LiteralPath $from -PathType Leaf)) { throw 'v20_08_1_dependency_missing' }
    if (Test-Path -LiteralPath $target) {
        if ((Get-FileHash -LiteralPath $from -Algorithm SHA256).Hash -ne (Get-FileHash -LiteralPath $target -Algorithm SHA256).Hash) { throw 'v20_08_1_dependency_conflict' }
    } else { Copy-Item -LiteralPath $from -Destination $target }
}
$oldPath=$env:pythonpath
$oldBytecode=$env:pythondontwritebytecode
try {
    $env:pythonpath = $workspace + [IO.Path]::PathSeparator + $source
    $env:pythondontwritebytecode = '1'
    & $python -B -m unittest discover -s $tests -p 'test_finam_candidate_worker.py' -v
    if ($LASTEXITCODE -ne 0) { throw 'v20_08_1_candidate_fake_tests_failed' }
    Write-Output 'v20_08_1_candidate_hook=PASS_FAKE_3_OF_3'
    Write-Output 'v20_08_1_finam=NO_NETWORK'
    Write-Output 'v20_08_1_live=off'
    Write-Output 'v20_08_1_orders=zero'
    Write-Output ('v20_08_1_source_pin='+$pin)
} finally {
    $env:pythonpath=$oldPath
    $env:pythondontwritebytecode=$oldBytecode
}
