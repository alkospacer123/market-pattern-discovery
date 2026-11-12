# v20-08.1: two new fake-only third-session exit/cancel-after-flat cases.
$ErrorActionPreference = 'Stop'
$pin = 'b91e87a8944e61dd495f85b77311265d3e700ffb'
$root = 'c:\v20lab'
$source = Join-Path $root 'source-raw'
$python = Join-Path $root '.venv-raw\scripts\python.exe'
$workspace = Join-Path $root 'pretrade-08\frozen-exit-tests'
if (-not (Test-Path -LiteralPath $source -PathType Container)) { throw 'v20_08_1_source_raw_missing' }
if (-not (Test-Path -LiteralPath $python -PathType Leaf)) { throw 'v20_08_1_python_missing' }
$pkg = Join-Path $workspace 'V20_TradingSystem_M15\v20_runtime'
$tests = Join-Path $pkg 'tests'
New-Item -ItemType Directory -Path $tests -Force | Out-Null
$files = @(
    @('v20_runtime/finam_execution.py','e3ea8ad751d7da26f88817c008030e0df7f2ff4f',$pkg,'finam_execution.py'),
    @('v20_runtime/h1_state_journal.py','f9fb32a50eb712aeae4690dd85d4e7aa512ef15c',$pkg,'h1_state_journal.py'),
    @('v20_runtime/tests/test_finam_trial_transport.py','5ec1800b24c3d8a5e51a3141c4f2dafdafe4a252',$tests,'test_finam_trial_transport.py'),
    @('v20_runtime/tests/test_finam_frozen_exit.py','8479b699c10aa7b947be6c1b854e8db836ca673e',$tests,'test_finam_frozen_exit.py')
)
foreach ($entry in $files) {
    $to = Join-Path $entry[2] $entry[3]
    $url = 'https://raw.githubusercontent.com/alkospacer123/market-pattern-discovery/' + $pin + '/V20_TradingSystem_M15/' + $entry[0]
    $tmp = $to + '.download'
    if (Test-Path -LiteralPath $tmp) { throw 'v20_partial_download_present' }
    try {
        Invoke-WebRequest -Uri $url -OutFile $tmp -UseBasicParsing
        $hash = (& git.exe hash-object -- $tmp).Trim().ToLowerInvariant()
        if ($LASTEXITCODE -ne 0 -or $hash -ne $entry[1]) { throw 'v20_trial_pin_mismatch' }
        if (Test-Path -LiteralPath $to) {
            $existing = (& git.exe hash-object -- $to).Trim().ToLowerInvariant()
            if ($LASTEXITCODE -ne 0 -or $existing -ne $entry[1]) { throw 'v20_trial_file_conflict' }
        } else { Move-Item -LiteralPath $tmp -Destination $to }
    } finally {
        if (Test-Path -LiteralPath $tmp) { Remove-Item -LiteralPath $tmp -Force }
    }
}
foreach ($name in @('__init__.py','offline_planner.py','account_risk.py','frozen_adapter.py')) {
    $from = Join-Path $source ('V20_TradingSystem_M15\v20_runtime\' + $name)
    $to = Join-Path $pkg $name
    if (-not (Test-Path -LiteralPath $from -PathType Leaf)) { throw 'v20_missing_pinned_dependency' }
    if (Test-Path -LiteralPath $to) {
        if ((Get-FileHash -LiteralPath $from -Algorithm SHA256).Hash -ne (Get-FileHash -LiteralPath $to -Algorithm SHA256).Hash) { throw 'v20_dependency_hash_conflict' }
    } else { Copy-Item -LiteralPath $from -Destination $to }
}
$priorPath = $env:pythonpath
$priorBytes = $env:pythondontwritebytecode
try {
    $env:pythonpath = $workspace + [IO.Path]::PathSeparator + $source
    $env:pythondontwritebytecode = '1'
    & $python -B -m unittest discover -s $tests -p 'test_finam_frozen_exit.py' -v
    if ($LASTEXITCODE -ne 0) { throw 'v20_08_1_frozen_exit_failed' }
    Write-Output 'v20_08_1_frozen_exit=pass_2_of_2'
    Write-Output 'v20_08_1_live=off'
    Write-Output 'v20_08_1_orders=zero'
    Write-Output ('v20_08_1_source_pin=' + $pin)
} finally {
    $env:pythonpath = $priorPath
    $env:pythondontwritebytecode = $priorBytes
}
