# 08.2 only new H1 own-kill-switch ARM/HALT lifecycle fake cases. No broker or Tasks.
$ErrorActionPreference='Stop'
Set-StrictMode -Version Latest
$pin='786fbaf31bfebf9fadcabea4ed351060b5fb5196'
$root='c:\v20lab'
$source=Join-Path $root 'source-raw'
$python=Join-Path $root '.venv-raw\scripts\python.exe'
$workspace=Join-Path $root 'pretrade-08\trial-arming-tests-786fbaf3'
if (-not (Test-Path -LiteralPath $source -PathType Container)) {throw 'v20_08_2_source_missing'}
if (-not (Test-Path -LiteralPath $python -PathType Leaf)) {throw 'v20_08_2_python_missing'}
$pkg=Join-Path $workspace 'V20_TradingSystem_M15\v20_runtime'
$tests=Join-Path $pkg 'tests'
New-Item -ItemType Directory -Path $tests -Force | Out-Null
$files=@(
  @('v20_runtime/finam_execution.py','2313556c8348de891bc27f472e6d4f48043f3c66',$pkg,'finam_execution.py'),
  @('v20_runtime/finam_trial_operator.py','829d657212942dd7d7ae8f406c28ba67d34fc5c5',$pkg,'finam_trial_operator.py'),
  @('v20_runtime/h1_state_journal.py','68988932c11241cb34273b745dda7764e35d9e62',$pkg,'h1_state_journal.py'),
  @('v20_runtime/tests/test_finam_trial_arming.py','b6f402c3efe1889c7f4d082089c3121e8baac4fb',$tests,'test_finam_trial_arming.py')
)
foreach ($entry in $files) {
    $target=Join-Path $entry[2] $entry[3]
    if (Test-Path -LiteralPath $target -PathType Leaf) {
        $h=(& git.exe hash-object -- $target).Trim().ToLowerInvariant()
        if ($LASTEXITCODE -ne 0 -or $h -ne $entry[1]) {throw 'v20_08_2_fake_conflicting_source'}
        continue
    }
    $tmp=$target+'.download'
    if (Test-Path -LiteralPath $tmp) {throw 'v20_08_2_fake_prior_partial_download'}
    try {
        $url='https://raw.githubusercontent.com/alkospacer123/market-pattern-discovery/'+$pin+'/V20_TradingSystem_M15/'+$entry[0]
        Invoke-WebRequest -Uri $url -OutFile $tmp -UseBasicParsing
        $h=(& git.exe hash-object -- $tmp).Trim().ToLowerInvariant()
        if ($LASTEXITCODE -ne 0 -or $h -ne $entry[1]) {throw 'v20_08_2_fake_source_mismatch'}
        Move-Item -LiteralPath $tmp -Destination $target
    } finally {
        if (Test-Path -LiteralPath $tmp) {Remove-Item -LiteralPath $tmp -Force}
    }
}
foreach ($name in @('__init__.py','offline_planner.py','account_risk.py','frozen_adapter.py')) {
    $from=Join-Path $source ('V20_TradingSystem_M15\v20_runtime\'+$name)
    $target=Join-Path $pkg $name
    if (-not (Test-Path -LiteralPath $from -PathType Leaf)) {throw 'v20_08_2_fake_dependency_missing'}
    if (Test-Path -LiteralPath $target -PathType Leaf) {
        if ((Get-FileHash -LiteralPath $from -Algorithm SHA256).Hash -ne (Get-FileHash -LiteralPath $target -Algorithm SHA256).Hash) {throw 'v20_08_2_fake_dependency_conflict'}
    } else {Copy-Item -LiteralPath $from -Destination $target}
}
$oldPath=$env:PYTHONPATH
$oldBytecode=$env:PYTHONDONTWRITEBYTECODE
try {
    $env:PYTHONPATH=$workspace+[IO.Path]::PathSeparator+$source
    $env:PYTHONDONTWRITEBYTECODE='1'
    & $python -B -m unittest discover -s $tests -p 'test_finam_trial_arming.py' -v
    if ($LASTEXITCODE -ne 0) {throw 'v20_08_2_fake_trial_arming_failed'}
    Write-Output 'v20_08_2_trial_arm=PASS_FAKE_2_OF_2'
    Write-Output 'v20_08_2_finam=NO_NETWORK'
    Write-Output 'v20_08_2_live=off'
    Write-Output 'v20_08_2_orders=zero'
    Write-Output ('v20_08_2_arm_source_pin='+$pin)
} finally {
    $env:PYTHONPATH=$oldPath
    $env:PYTHONDONTWRITEBYTECODE=$oldBytecode
}
