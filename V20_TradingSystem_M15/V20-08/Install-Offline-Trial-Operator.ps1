# 08.2: Install pinned supervised V20-only trial Python source OFFLINE.
# No FINAM, DPAPI, approvals, journal, kill-switch, Task or order operations.
[CmdletBinding()]
param()
$ErrorActionPreference = 'Stop'
Set-StrictMode -Version Latest
$pin = 'a9b280b570e1afc401ca4776e3cb81830c2ad31e'
$root = 'C:\V20Lab'
$source = Join-Path $root 'source-raw'
$python = Join-Path $root '.venv-raw\scripts\python.exe'
$readonly = Join-Path $root 'pretrade-08\dpapi-finam-readonly'
$workspace = Join-Path $root 'pretrade-08\trial-runtime-08'
function need([bool]$value,[string]$code) { if (-not $value) { throw $code } }
function no-link([string]$path) {
    if (Test-Path -LiteralPath $path) {
        need (-not ((Get-Item -LiteralPath $path -Force).Attributes -band [IO.FileAttributes]::ReparsePoint)) 'V20_08_2_REPARSE_PATH_FORBIDDEN'
    }
}
function git-sha([string]$path) {
    $h = (& git.exe hash-object -- $path).Trim().ToLowerInvariant()
    need ($LASTEXITCODE -eq 0) 'V20_08_2_GIT_HASH_ERROR'
    return $h
}
need ($env:OS -eq 'Windows_NT' -and $env:COMPUTERNAME -eq 'URIU-PC') 'V20_08_2_WRONG_HOST'
foreach ($p in @($root,$source,$python,$readonly,(Join-Path $root 'pretrade-08'))) {
    need (Test-Path -LiteralPath $p) 'V20_08_2_REQUIRED_PATH_MISSING'
    no-link $p
}
foreach ($name in @('v20-shallow','v20-obv','v20-inside')) {
    $task = Get-ScheduledTask -TaskName $name -TaskPath '\' -ErrorAction Stop
    need ($task.State -eq 'Disabled' -and @($task.Actions).Count -eq 1 -and
          $task.Actions[0].Arguments.Contains('v20-task-live-blocked.ps1')) 'V20_08_2_TRADING_TASK_NOT_DISABLED'
}
$pkg=Join-Path $workspace 'V20_TradingSystem_M15\v20_runtime'
$objects = @(
    @('v20_runtime/__init__.py','9a0512aaf8418df59f26fcfdeb1f181fc38e7139'),
    @('v20_runtime/offline_planner.py','9d42f2517218a4df1296c4188f123a469c6d569a'),
    @('v20_runtime/account_risk.py','50d0a924b0eccef45746c0111fa0df4803aed125'),
    @('v20_runtime/frozen_adapter.py','71d50f3f1227a00c8831e9a7f738dcf0d19ea49e'),
    @('v20_runtime/h1_state_journal.py','68988932c11241cb34273b745dda7764e35d9e62'),
    @('v20_runtime/finam_execution.py','644a5c2fe18275b8da472583d67738f9ab582a7f'),
    @('v20_runtime/finam_trial_operator.py','78c86481e70a99c4e1bfef3ffab9d2a6a7a7706f'),
    @('v20_runtime/tests/test_finam_trial_transport.py','c7973b3e1a5c4285525e1a355d1c1d389fdee0a0'),
    @('v20_runtime/tests/test_finam_preapproved_trial.py','f23d52c2cbe7ae6ccfb9ed2c9c66386f718331de'),
    @('v20_runtime/tests/test_finam_trial_operator.py','8d25ebeb567ad7c613b87eba8e1bc608245b5350')
)
$previous=@{
    'finam_execution.py'=@('7bbd692583bc47346b9a80c6cf505d6dd5a62c6f','2313556c8348de891bc27f472e6d4f48043f3c66','c68bf38c760e82bd0d626632ae6a9ebe5ae3b6f2','ed3f55cea5a5860aae0caf821e1c12c20d785d64')
    'finam_trial_operator.py'=@('27a8afa8746b270d85c4ec17056bc5ff064ecc05','ac6671bebbea8d2bbe8389d4b4ee166ae1b13b39','4ada625363ff2baba92578811d7ed0b45f7408ed','829d657212942dd7d7ae8f406c28ba67d34fc5c5','138bca5f40f1445be5e51b728a1cc6ea86a3057f','09245d1a50754d4116547f73c0d67725b98d1991')
}
$rawroot='https://raw.githubusercontent.com/alkospacer123/market-pattern-discovery/'+$pin+'/V20_TradingSystem_M15/'
New-Item -ItemType Directory -Path $pkg -Force | Out-Null
foreach ($p in @($workspace,(Join-Path $workspace 'V20_TradingSystem_M15'),$pkg)) { no-link $p }
$testDir=Join-Path $pkg 'tests'
no-link $testDir
New-Item -ItemType Directory -Path $testDir -Force | Out-Null
no-link $testDir
foreach ($entry in $objects) {
    $rel=[string]$entry[0]
    $expected=[string]$entry[1]
    $to=Join-Path (Join-Path $workspace 'V20_TradingSystem_M15') ($rel.Replace('/','\'))
    no-link $to
    $oldVersion=$false
    if (Test-Path -LiteralPath $to -PathType Leaf) {
        $existing=git-sha $to
        if ($existing -eq $expected) { continue }
        $leaf=[string]($rel.Split('/')[-1])
        need ($previous.ContainsKey($leaf) -and
              $existing -in @($previous[$leaf])) 'V20_08_2_EXISTING_SOURCE_CONFLICT'
        $oldVersion=$true
    }
    $tmp=$to+'.download'
    need (-not (Test-Path -LiteralPath $tmp)) 'V20_08_2_PREVIOUS_PARTIAL_DOWNLOAD'
    try {
        Invoke-WebRequest -Uri ($rawroot+$rel) -OutFile $tmp -UseBasicParsing
        need ((git-sha $tmp) -eq $expected) 'V20_08_2_SOURCE_HASH_MISMATCH'
        if ($oldVersion) {
            Move-Item -LiteralPath $tmp -Destination $to -Force -ErrorAction Stop
        } else {
            Move-Item -LiteralPath $tmp -Destination $to -ErrorAction Stop
        }
        need ((git-sha $to) -eq $expected) 'V20_08_2_INSTALLED_SOURCE_MISMATCH'
    } finally {
        if (Test-Path -LiteralPath $tmp) { Remove-Item -LiteralPath $tmp -Force }
    }
}
$frozen = @(
    @('V20-03/offline/stress_v20_03.py','f135b42219b816e7925892ac07404c61c4627cbf'),
    @('research_original_v20/base.py','b917cc9c7c99fbad38423d9f4fdfbb82767545be'),
    @('research_original_v20/run.py','7d9ddf0ef498f0c93a139c0104af2a72d0e79151'),
    @('research_original_v20/legacy_v4/study_v4.py','7749f82edcb8a04b4002978b588beeb26e484f71'),
    @('research_original_v20/legacy_v4/dependencies/study.py','1294ff9884f7a1634fab67ee330ec702e0612c31')
)
foreach ($entry in $frozen) {
    $rel=([string]$entry[0]).Replace('/','\')
    $sourceFile=Join-Path (Join-Path $readonly 'V20_TradingSystem_M15') $rel
    $target=Join-Path (Join-Path $workspace 'V20_TradingSystem_M15') $rel
    need (Test-Path -LiteralPath $sourceFile -PathType Leaf) 'V20_08_2_FROZEN_WITNESS_MISSING'
    no-link $sourceFile
    need ((git-sha $sourceFile) -eq $entry[1]) 'V20_08_2_FROZEN_WITNESS_HASH_CHANGED'
    no-link $target
    if (Test-Path -LiteralPath $target -PathType Leaf) {
        need ((git-sha $target) -eq $entry[1]) 'V20_08_2_FROZEN_TARGET_CONFLICT'
    } else {
        $dir=Split-Path $target
        New-Item -ItemType Directory -Path $dir -Force | Out-Null
        no-link $dir
        Copy-Item -LiteralPath $sourceFile -Destination $target -ErrorAction Stop
        need ((git-sha $target) -eq $entry[1]) 'V20_08_2_FROZEN_COPY_MISMATCH'
    }
}
$prior=$env:PYTHONPATH
$bytecode=$env:PYTHONDONTWRITEBYTECODE
try {
    $env:PYTHONPATH=$testDir+[IO.Path]::PathSeparator+$workspace+[IO.Path]::PathSeparator+$source
    $env:PYTHONDONTWRITEBYTECODE='1'
    # Parser/import and exactly three NEW technical-only fake scenarios.
    & $python -B -m V20_TradingSystem_M15.v20_runtime.finam_trial_operator --help | Out-Null
    need ($LASTEXITCODE -eq 0) 'V20_08_2_TRIAL_MODULE_IMPORT_INVALID'
    & $python -B -m unittest test_finam_preapproved_trial.PreapprovedIntentTests.test_technical_single_contract_has_separate_h1_state_and_no_post test_finam_trial_operator.TrialOperatorTests.test_technical_trial_reuses_one_entry_then_follow_only test_finam_trial_operator.TrialOperatorTests.test_technical_grant_creates_one_contract_stop_only_permit
    need ($LASTEXITCODE -eq 0) 'V20_08_2_TECHNICAL_TESTS_FAILED'
} finally {
    $env:PYTHONPATH=$prior
    $env:PYTHONDONTWRITEBYTECODE=$bytecode
}
Write-Output 'v20_08_2_trial_source=PASS_PINNED_IMPORT_ONLY'
Write-Output 'v20_08_2_technical_new_tests=PASS_FAKE_3_OF_3'
Write-Output 'v20_08_2_source_commit=a9b280b570e1afc401ca4776e3cb81830c2ad31e'
Write-Output 'v20_08_2_finam=NO_NETWORK'
Write-Output 'v20_08_2_orders=zero'
Write-Output 'v20_08_2_live=off'
Write-Output 'v20_08_2_tasks_modified=no'
