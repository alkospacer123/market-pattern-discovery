# v20-08.1: four new offline tests only, artificial approval file in a temp directory.
$ErrorActionPreference = 'Stop'
$pin = '7151c69a9652bd9adddb36a0a4374740e0e73f7f'
$root = 'c:\v20lab'
$source = Join-Path $root 'source-raw'
$python = Join-Path $root '.venv-raw\scripts\python.exe'
$workspace = Join-Path $root 'pretrade-08\single-trial-tests'
if (-not (Test-Path -LiteralPath $source -PathType Container)) { throw 'v20_08_1_source_raw_missing' }
if (-not (Test-Path -LiteralPath $python -PathType Leaf)) { throw 'v20_08_1_python_missing' }
$pkg = Join-Path $workspace 'V20_TradingSystem_M15\v20_runtime'
$tests = Join-Path $pkg 'tests'
New-Item -ItemType Directory -Path $tests -Force | Out-Null
$files = @(
    @('v20_runtime/finam_execution.py','cd84d1e22f8a473e3473509bdce3fa3efa4d5cdb',$pkg,'finam_execution.py'),
    @('v20_runtime/h1_state_journal.py','f9fb32a50eb712aeae4690dd85d4e7aa512ef15c',$pkg,'h1_state_journal.py'),
    @('v20_runtime/tests/test_finam_trial_transport.py','509adfef1a0bfad75e8a2232fa2b00bdef2f8c28',$tests,'test_finam_trial_transport.py')
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
foreach ($name in @('__init__.py','offline_planner.py','account_risk.py')) {
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
    & $python -B -m unittest discover -s $tests -p 'test_finam_trial_transport.py' -v
    if ($LASTEXITCODE -ne 0) { throw 'v20_08_1_trial_fake_failed' }
    Write-Output 'v20_08_1_trial_fake=pass_4_of_4'
    Write-Output 'v20_08_1_live=off'
    Write-Output 'v20_08_1_orders=zero'
    Write-Output ('v20_08_1_source_pin=' + $pin)
} finally {
    $env:pythonpath = $priorPath
    $env:pythondontwritebytecode = $priorBytes
}
