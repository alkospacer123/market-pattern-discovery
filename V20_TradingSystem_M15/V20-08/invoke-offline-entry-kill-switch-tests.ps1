# V20-08.1 ONE targeted new kill-switch regression plus affected fake FINAM entry/exit cases.
# Never reads DPAPI, FINAM, Windows Tasks or real V20 SQLite. No LIVE entry points.
$ErrorActionPreference = 'Stop'
Set-StrictMode -Version Latest
$pin = 'a7d7d090c377ac04737bff36e7b6f12bca42938b'
$root = 'c:\v20lab'
$source = Join-Path $root 'source-raw'
$python = Join-Path $root '.venv-raw\scripts\python.exe'
$workspace = Join-Path $root 'pretrade-08\kill-switch-tests-a7d7d090'
if (-not (Test-Path -LiteralPath $source -PathType Container)) { throw 'v20_source_raw_missing' }
if (-not (Test-Path -LiteralPath $python -PathType Leaf)) { throw 'v20_python_missing' }
$pkg = Join-Path $workspace 'V20_TradingSystem_M15\v20_runtime'
$tests = Join-Path $pkg 'tests'
New-Item -ItemType Directory -Path $tests -Force | Out-Null
$files = @(
    @('v20_runtime/finam_execution.py','f91d3c6c0dff517274809c676bd332417aafa80f',$pkg,'finam_execution.py'),
    @('v20_runtime/h1_state_journal.py','68988932c11241cb34273b745dda7764e35d9e62',$pkg,'h1_state_journal.py'),
    @('v20_runtime/tests/test_finam_trial_transport.py','c7973b3e1a5c4285525e1a355d1c1d389fdee0a0',$tests,'test_finam_trial_transport.py'),
    @('v20_runtime/tests/test_finam_frozen_exit.py','20fe506f6e709c90ff4bb52b3aa6ddf57d0dcc6d',$tests,'test_finam_frozen_exit.py'),
    @('v20_runtime/tests/test_finam_single_cycle.py','f6394919c6d468a8f99dd7852fb8e160add898c8',$tests,'test_finam_single_cycle.py'),
    @('v20_runtime/tests/test_finam_m15_boundary.py','1daf68c4cb1da2ee1697b3ea26a76122f9c3fa49',$tests,'test_finam_m15_boundary.py')
)
foreach ($entry in $files) {
    $to = Join-Path $entry[2] $entry[3]
    $tmp = $to + '.download'
    if (Test-Path -LiteralPath $tmp) { throw 'v20_partial_download_present' }
    $url = 'https://raw.githubusercontent.com/alkospacer123/market-pattern-discovery/' + $pin + '/V20_TradingSystem_M15/' + $entry[0]
    try {
        Invoke-WebRequest -Uri $url -OutFile $tmp -UseBasicParsing
        $hash = (& git.exe hash-object -- $tmp).Trim().ToLowerInvariant()
        if ($LASTEXITCODE -ne 0 -or $hash -ne $entry[1]) { throw 'v20_kill_switch_source_blob_mismatch' }
        if (Test-Path -LiteralPath $to) {
            $existing = (& git.exe hash-object -- $to).Trim().ToLowerInvariant()
            if ($LASTEXITCODE -ne 0 -or $existing -ne $entry[1]) { throw 'v20_kill_switch_existing_file_conflict' }
        } else {
            Move-Item -LiteralPath $tmp -Destination $to
        }
    } finally {
        if (Test-Path -LiteralPath $tmp) { Remove-Item -LiteralPath $tmp -Force }
    }
}
foreach ($name in @('__init__.py','offline_planner.py','account_risk.py','frozen_adapter.py')) {
    $from = Join-Path $source ('V20_TradingSystem_M15\v20_runtime\' + $name)
    $to = Join-Path $pkg $name
    if (-not (Test-Path -LiteralPath $from -PathType Leaf)) { throw 'v20_missing_original_dependency' }
    if (Test-Path -LiteralPath $to) {
        if ((Get-FileHash -LiteralPath $from -Algorithm SHA256).Hash -ne (Get-FileHash -LiteralPath $to -Algorithm SHA256).Hash) { throw 'v20_dependency_conflict' }
    } else { Copy-Item -LiteralPath $from -Destination $to }
}
$priorPath = $env:pythonpath
$priorBytes = $env:pythondontwritebytecode
try {
    $env:pythonpath = $workspace + [IO.Path]::PathSeparator + $source
    $env:pythondontwritebytecode = '1'
    foreach ($name in @('test_finam_trial_transport.py','test_finam_frozen_exit.py','test_finam_single_cycle.py')) {
        & $python -B -m unittest discover -s $tests -p $name -v
        if ($LASTEXITCODE -ne 0) { throw ('v20_kill_switch_regression_failed_' + $name) }
    }
    Write-Output 'v20_08_1_entry_kill_switch=PASS_TARGETED_FAKE_ONLY'
    Write-Output 'v20_08_1_live=off'
    Write-Output 'v20_08_1_orders=zero'
    Write-Output 'v20_08_1_finam=NO_NETWORK'
    Write-Output ('v20_08_1_source_pin=' + $pin)
} finally {
    $env:pythonpath = $priorPath
    $env:pythondontwritebytecode = $priorBytes
}
