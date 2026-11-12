# 08.2 one NEW fake-only test: manual FINAM terminal exit and old SLTP cleanup.
# No FINAM/DPAPI, no Task interaction, no modification to real V20 journals.
$ErrorActionPreference='Stop'
Set-StrictMode -Version Latest
$pin='bcfe576dd37bbc616940475bc1f20258ba9cea6a'
$root='c:\v20lab'
$source=Join-Path $root 'source-raw'
$python=Join-Path $root '.venv-raw\scripts\python.exe'
$workspace=Join-Path $root 'pretrade-08\manual-flat-fake-bcfe576d'
if (-not (Test-Path -LiteralPath $source -PathType Container)) {throw 'v20_08_2_source_missing'}
if (-not (Test-Path -LiteralPath $python -PathType Leaf)) {throw 'v20_08_2_python_missing'}
$pkg=Join-Path $workspace 'V20_TradingSystem_M15\v20_runtime'
$tests=Join-Path $pkg 'tests'
New-Item -ItemType Directory -Path $tests -Force | Out-Null
$files=@(
 @('v20_runtime/finam_execution.py','c68bf38c760e82bd0d626632ae6a9ebe5ae3b6f2',$pkg,'finam_execution.py'),
 @('v20_runtime/h1_state_journal.py','68988932c11241cb34273b745dda7764e35d9e62',$pkg,'h1_state_journal.py'),
 @('v20_runtime/tests/test_finam_trial_transport.py','c7973b3e1a5c4285525e1a355d1c1d389fdee0a0',$tests,'test_finam_trial_transport.py'),
 @('v20_runtime/tests/test_finam_manual_flat.py','515f2cb0c6ad4fa1bd9dd01859f351483d2c0be0',$tests,'test_finam_manual_flat.py')
)
foreach($entry in $files){
 $target=Join-Path $entry[2] $entry[3]
 if(Test-Path -LiteralPath $target -PathType Leaf){
  $hash=(& git.exe hash-object -- $target).Trim().ToLowerInvariant()
  if($lastexitcode -ne 0 -or $hash -ne $entry[1]){throw 'v20_08_2_test_source_conflict'}
  continue
 }
 $tmp=$target+'.download'
 if(Test-Path -LiteralPath $tmp){throw 'v20_08_2_test_partial_exists'}
 try {
  $url='https://raw.githubusercontent.com/alkospacer123/market-pattern-discovery/'+$pin+'/V20_TradingSystem_M15/'+$entry[0]
  Invoke-WebRequest -Uri $url -OutFile $tmp -UseBasicParsing
  $hash=(& git.exe hash-object -- $tmp).Trim().ToLowerInvariant()
  if($lastexitcode -ne 0 -or $hash -ne $entry[1]){throw 'v20_08_2_test_source_hash_mismatch'}
  Move-Item -LiteralPath $tmp -Destination $target
 } finally {if(Test-Path -LiteralPath $tmp){Remove-Item -LiteralPath $tmp -Force}}
}
foreach($name in @('__init__.py','offline_planner.py','account_risk.py','frozen_adapter.py')){
 $from=Join-Path $source ('V20_TradingSystem_M15\v20_runtime\'+$name)
 $target=Join-Path $pkg $name
 if(-not (Test-Path -LiteralPath $from -PathType Leaf)){throw 'v20_08_2_dependency_missing'}
 if(Test-Path -LiteralPath $target){
  if((Get-FileHash -LiteralPath $from -Algorithm SHA256).Hash -ne (Get-FileHash -LiteralPath $target -Algorithm SHA256).Hash){throw 'v20_08_2_dependency_conflict'}
 } else {Copy-Item -LiteralPath $from -Destination $target}
}
$oldPath=$env:PYTHONPATH
$oldBytecode=$env:PYTHONDONTWRITEBYTECODE
try {
 $env:PYTHONPATH=$workspace+[IO.Path]::PathSeparator+$source
 $env:PYTHONDONTWRITEBYTECODE='1'
 & $python -B -m unittest discover -s $tests -p 'test_finam_manual_flat.py' -v
 if($lastexitcode -ne 0){throw 'v20_08_2_manual_flat_fake_failed'}
 Write-Output 'v20_08_2_manual_flat=PASS_FAKE_1_OF_1'
 Write-Output 'v20_08_2_finam=NO_NETWORK'
 Write-Output 'v20_08_2_orders=zero'
 Write-Output 'v20_08_2_live=off'
 Write-Output ('v20_08_2_source_pin='+$pin)
} finally {
 $env:PYTHONPATH=$oldPath
 $env:PYTHONDONTWRITEBYTECODE=$oldBytecode
}
