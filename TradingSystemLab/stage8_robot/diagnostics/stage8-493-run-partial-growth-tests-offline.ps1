param(
    [string]$repo = 'c:\tradingsystemlab\market-pattern-discovery',
    [string]$python = 'c:\tslaudit\fill493\venv\scripts\python.exe',
    [string]$runtime_root = 'c:\tradingsystemlab\runtime',
    [string]$scratch = 'c:\tslaudit\fill493\stage8-493-partial-growth-offline'
)
$erroractionpreference = 'stop'
$expected = '2c262d629ee7607f2bc546b84a21d27b46346904'
$ref = 'refs/heads/candidate/stop-tick-grid-20261012'
$previous = [environment]::getenvironmentvariable('pythondontwritebytecode','process')
write-output '=== stage8 #493 isolated candidate-only partial-growth pytest ==='
write-output 'NO_FINAM NO_REAL_ORDERS NO_TASK_MUTATION NO_REARM NO_LIVE_SQLITE NO_PRODUCTION_CHECKOUT_CHANGE'
try {
    if (-not (test-path -literalpath $repo -pathtype container) -or
        -not (test-path -literalpath $python -pathtype leaf) -or
        (test-path -literalpath $scratch)) { throw 'ISOLATED_TEST_INPUT_OR_SCRATCH_INVALID' }
    $task = get-scheduledtask -taskname 'TradingSystemLab-Stage8-Production' -erroraction stop
    if ([string]$task.state -cne 'Disabled') { throw 'PRODUCTION_TASK_NOT_ISOLATED' }
    $switch = get-content -literalpath (join-path $runtime_root 'safety\stage8-trading-kill-switch.json') -raw -erroraction stop | convertfrom-json
    if ($switch.state -cne 'HALTED') { throw 'KILL_SWITCH_NOT_HALTED' }
    $current = (& git -C $repo rev-parse '@').trim()
    if ($lastexitcode -ne 0 -or -not $current) { throw 'OPERATOR_REPO_HEAD_INVALID' }
    write-output "OPERATOR_WORKTREE_HEAD_BEFORE=$current"
    $env:pythondontwritebytecode = '1'
    & git -C $repo fetch --no-tags origin $ref
    if ($lastexitcode -ne 0) { throw 'CANDIDATE_FETCH_FAILED' }
    $remote = (& git -C $repo rev-parse 'FETCH_HEAD').trim()
    if ($lastexitcode -ne 0 -or -not $remote) { throw 'CANDIDATE_FETCH_HEAD_INVALID' }
    & git -C $repo merge-base --is-ancestor $expected $remote
    if ($lastexitcode -ne 0) { throw 'PINNED_CANDIDATE_NOT_IN_REMOTE_HISTORY' }
    & git -C $repo worktree add --detach $scratch $expected
    if ($lastexitcode -ne 0) { throw 'ISOLATED_WORKTREE_CREATION_FAILED' }
    $pin = (& git -C $scratch rev-parse '@').trim()
    if ($lastexitcode -ne 0 -or $pin -cne $expected) { throw 'ISOLATED_WORKTREE_SHA_MISMATCH' }
    $source = join-path $scratch 'TradingSystemLab\stage8_robot\production_runtime.py'
    $tests = join-path $scratch 'TradingSystemLab\stage8_robot\tests\test_stage8_493_partial_growth_candidate.py'
    if (-not (test-path -literalpath $source -pathtype leaf) -or
        -not (test-path -literalpath $tests -pathtype leaf)) { throw 'CANDIDATE_FILES_MISSING' }
    write-output "ISOLATED_CANDIDATE_SHA=$pin"
    $test_paths = @(
        'TradingSystemLab/stage8_robot/tests/test_stage8_493_partial_growth_candidate.py',
        'TradingSystemLab/stage8_robot/tests/test_stop_tick_grid_amendment.py',
        'TradingSystemLab/stage8_robot/tests/test_stage8_493_multifill_offline_acceptance.py'
    )
    push-location $scratch
    try {
        & $python -B -m pytest -q -p no:cacheprovider --basetemp (join-path $scratch 'pytest-scratch') @test_paths
        if ($lastexitcode -ne 0) { throw 'CANDIDATE_REGRESSION_TESTS_FAILED' }
    } finally { pop-location }
    $task_after = get-scheduledtask -taskname 'TradingSystemLab-Stage8-Production' -erroraction stop
    $switch_after = get-content -literalpath (join-path $runtime_root 'safety\stage8-trading-kill-switch.json') -raw | convertfrom-json
    $unchanged = (& git -C $repo rev-parse '@').trim()
    if ([string]$task_after.state -cne 'Disabled' -or $switch_after.state -cne 'HALTED' -or
        $unchanged -cne $current) { throw 'POST_TEST_LIVE_SAFETY_CHANGED' }
    write-output 'CLASSIFICATION=OFFLINE_CANDIDATE_GROWTH_TESTS_PASS_NOT_REAL_AUTHORITY'
} catch {
    $error_code = [string]$_.exception.message
    if ($error_code -cnotmatch '^[A-Z0-9_]{4,120}$') { $error_code = 'OFFLINE_TEST_UNEXPECTED' }
    write-output "CLASSIFICATION=BLOCKED:$error_code"
    exit 1
} finally {
    [environment]::setenvironmentvariable('pythondontwritebytecode',$previous,'process')
    write-output 'LIVE_TASK_MUTATED=NO'
    write-output 'REAL_ORDER_AUTHORIZED=NO'
    write-output 'PRODUCTION_CHECKOUT_MUTATED=NO'
}
