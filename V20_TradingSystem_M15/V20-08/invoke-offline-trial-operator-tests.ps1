# V20-08.2 new-operator targeted fake-only tests; no FINAM, DPAPI, Task calls.
$ErrorActionPreference = 'Stop'
Set-StrictMode -Version Latest
$pin = '4d8f09b8853ffedc80eba5ecfc0a7bd868a96d6c'
$root = 'c:\v20lab'
$source = Join-Path $root 'source-raw'
$python = Join-Path $root '.venv-raw\scripts\python.exe'
$workspace = Join-Path $root 'pretrade-08\trial-operator-fake-4d8f09b8'
if (-not (Test-Path -LiteralPath $source -PathType Container)) { throw 'v20_08_2_source_missing' }
if (-not (Test-Path -LiteralPath $python -PathType Leaf)) { throw 'v20_08_2_python_missing' }
$pkg = Join-Path $workspace 'V20_TradingSystem_M15\v20_runtime'
$tests = Join-Path $pkg 'tests'
New-Item -ItemType Directory -Path $tests -Force | Out-Null
$files = @(
    @('v20_runtime/finam_execution.py','2313556c8348de891bc27f472e6d4f48043f3c66',$pkg,'finam_execution.py'),
    @('v20_runtime/h1_state_journal.py','68988932c11241cb34273b745dda7764e35d9e62',$pkg,'h1_state_journal.py'),
    @('v20_runtime/finam_trial_operator.py','ac6671bebbea8d2bbe8389d4b4ee166ae1b13b39',$pkg,'finam_trial_operator.py'),
    @('v20_runtime/tests/test_finam_trial_operator.py','150e6074cae2fce30c14ec8d91140527bbc4a0b6',$tests,'test_finam_trial_operator.py')
)
foreach ($entry in $files) {
    $target = Join-Path $entry[2] $entry[3]
    if (Test-Path -LiteralPath $target) {
        $existing = (& git.exe hash-object -- $target).Trim().ToLowerInvariant()
        if ($LASTEXITCODE -ne 0 -or $existing -ne $entry[1]) { throw 'v20_08_2_target_file_conflict' }
        continue
    }
    $tmp = $target + '.download'
    if (Test-Path -LiteralPath $tmp) { throw 'v20_08_2_prior_download_exists' }
    try {
        $url = 'https://raw.githubusercontent.com/alkospacer123/market-pattern-discovery/'+$pin+'/V20_TradingSystem_M15/'+$entry[0]
        Invoke-WebRequest -Uri $url -OutFile $tmp -UseBasicParsing
        $sha = (& git.exe hash-object -- $tmp).Trim().ToLowerInvariant()
        if ($LASTEXITCODE -ne 0 -or $sha -ne $entry[1]) { throw 'v20_08_2_source_pin_mismatch' }
        Move-Item -LiteralPath $tmp -Destination $target
    } finally {
        if (Test-Path -LiteralPath $tmp) { Remove-Item -LiteralPath $tmp -Force }
    }
}
foreach ($name in @('__init__.py','offline_planner.py','account_risk.py','frozen_adapter.py')) {
    $from = Join-Path $source ('V20_TradingSystem_M15\v20_runtime\' + $name)
    $target = Join-Path $pkg $name
    if (-not (Test-Path -LiteralPath $from -PathType Leaf)) { throw 'v20_08_2_dependency_missing' }
    if (Test-Path -LiteralPath $target) {
        if ((Get-FileHash -LiteralPath $from -Algorithm SHA256).Hash -ne (Get-FileHash -LiteralPath $target -Algorithm SHA256).Hash) { throw 'v20_08_2_dependency_drift' }
    } else {
        Copy-Item -LiteralPath $from -Destination $target
    }
}
$oldPath = $env:PYTHONPATH
$oldNoBytecode = $env:PYTHONDONTWRITEBYTECODE
try {
    $env:PYTHONPATH = $workspace + [IO.Path]::PathSeparator + $source
    $env:PYTHONDONTWRITEBYTECODE = '1'
    & $python -B -m unittest discover -s $tests -p 'test_finam_trial_operator.py' -v
    if ($LASTEXITCODE -ne 0) { throw 'v20_08_2_trial_operator_fake_tests_failed' }
    Write-Output 'v20_08_2_trial_operator=PASS_FAKE_7_OF_7'
    Write-Output 'v20_08_2_finam=NO_NETWORK'
    Write-Output 'v20_08_2_live=off'
    Write-Output 'v20_08_2_orders=zero'
    Write-Output 'v20_08_2_source_pin=4d8f09b8853ffedc80eba5ecfc0a7bd868a96d6c'
} finally {
    $env:PYTHONPATH = $oldPath
    $env:PYTHONDONTWRITEBYTECODE = $oldNoBytecode
}
