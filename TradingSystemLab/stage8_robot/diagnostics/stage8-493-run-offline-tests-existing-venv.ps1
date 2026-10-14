$erroractionpreference = 'stop'
$repo = 'c:\tradingsystemlab\market-pattern-discovery'
$worktree = 'c:\tslaudit\fill493\stage8-493-partial-growth-offline'
$runtime_root = 'c:\tradingsystemlab\runtime'
$expected = '2c262d629ee7607f2bc546b84a21d27b46346904'
$python = 'c:\tslaudit\fill493\venv-stage8-493-offline-pytest\scripts\python.exe'
$test_temp = 'c:\tslaudit\fill493\stage8-493-pytest-scratch'
$prior_bytecode = [environment]::getenvironmentvariable('pythondontwritebytecode','process')
write-output '=== stage8 #493 isolated pinned OFFLINE pytest (existing test venv) ==='
write-output 'NO_FINAM NO_ORDER_OR_CANCEL NO_LIVE_SQLITE NO_TASK_MUTATION NO_REARM'
try {
    if (-not (test-path -literalpath $repo -pathtype container) -or
        -not (test-path -literalpath $worktree -pathtype container) -or
        -not (test-path -literalpath $python -pathtype leaf)) {
        throw 'ISOLATED_TEST_INPUT_MISSING'
    }
    $task = get-scheduledtask -taskname 'TradingSystemLab-Stage8-Production' -erroraction stop
    $switch = get-content -literalpath (join-path $runtime_root 'safety\stage8-trading-kill-switch.json') -raw -erroraction stop | convertfrom-json
    if ([string]$task.state -cne 'Disabled' -or $switch.state -cne 'HALTED') {
        throw 'PRODUCTION_NOT_ISOLATED_HALTED'
    }
    $repo_before = (& git -C $repo rev-parse '@').trim()
    if ($lastexitcode -ne 0 -or -not $repo_before) { throw 'OPERATOR_REPO_HEAD_INVALID' }
    $pin = (& git -C $worktree rev-parse '@').trim()
    if ($lastexitcode -ne 0 -or $pin -cne $expected) { throw 'PINNED_WORKTREE_SHA_MISMATCH' }
    $tracked = @(& git -C $worktree status --porcelain --untracked-files=no)
    if ($lastexitcode -ne 0 -or $tracked.count -ne 0) { throw 'PINNED_WORKTREE_TRACKED_FILES_CHANGED' }
    write-output "ISOLATED_CANDIDATE_SHA=$pin"
    write-output "OPERATOR_REPO_HEAD_BEFORE=$repo_before"
    $env:pythondontwritebytecode = '1'
    & $python -B -c 'import pytest,pandas,numpy,jsonschema,tabulate'
    if ($lastexitcode -ne 0) { throw 'ISOLATED_TEST_DEPENDENCIES_MISSING' }
    write-output 'TEST_DEPENDENCIES_IMPORTED=PASS'
    & $python -B -c 'import pytest,pandas; print(pytest.__version__); print(pandas.__version__)'
    if ($lastexitcode -ne 0) { throw 'TEST_VERSION_CHECK_FAILED' }
    $tests = @(
        'TradingSystemLab/stage8_robot/tests/test_stage8_493_partial_growth_candidate.py',
        'TradingSystemLab/stage8_robot/tests/test_stop_tick_grid_amendment.py',
        'TradingSystemLab/stage8_robot/tests/test_stage8_493_multifill_offline_acceptance.py'
    )
    foreach ($path in $tests) {
        if (-not (test-path -literalpath (join-path $worktree $path) -pathtype leaf)) { throw 'PINNED_TEST_FILE_MISSING' }
    }
    push-location $worktree
    try {
        & $python -B -m pytest -q -p no:cacheprovider --basetemp $test_temp @tests
        if ($lastexitcode -ne 0) { throw 'CANDIDATE_REGRESSION_TESTS_FAILED' }
    } finally { pop-location }
    $task_after = get-scheduledtask -taskname 'TradingSystemLab-Stage8-Production' -erroraction stop
    $switch_after = get-content -literalpath (join-path $runtime_root 'safety\stage8-trading-kill-switch.json') -raw | convertfrom-json
    $repo_after = (& git -C $repo rev-parse '@').trim()
    $pin_after = (& git -C $worktree rev-parse '@').trim()
    if ($lastexitcode -ne 0 -or [string]$task_after.state -cne 'Disabled' -or
        $switch_after.state -cne 'HALTED' -or $repo_after -cne $repo_before -or $pin_after -cne $expected) {
        throw 'POST_TEST_PRODUCTION_OR_WORKTREE_AUTHORITY_CHANGED'
    }
    write-output 'CLASSIFICATION=OFFLINE_CANDIDATE_GROWTH_TESTS_PASS_NOT_REAL_AUTHORITY'
} catch {
    $reason = [string]$_.exception.message
    if ($reason -cnotmatch '^[A-Z0-9_]{4,120}$') { $reason = 'OFFLINE_TEST_UNEXPECTED' }
    write-output "CLASSIFICATION=BLOCKED:$reason"
    exit 1
} finally {
    [environment]::setenvironmentvariable('pythondontwritebytecode',$prior_bytecode,'process')
    write-output 'LIVE_TASK_MUTATED=NO'
    write-output 'REAL_ORDER_AUTHORIZED=NO'
    write-output 'PRODUCTION_CHECKOUT_MUTATED=NO'
}
