$erroractionpreference = 'stop'
$repo = 'c:\tradingsystemlab\market-pattern-discovery'
$runtime_root = 'c:\tradingsystemlab\runtime'
$worktree = 'c:\tslaudit\fill493\stage8-493-partial-growth-v2-offline'
$python = 'c:\tslaudit\fill493\venv-stage8-493-offline-pytest\scripts\python.exe'
$test_temp = 'c:\tslaudit\fill493\stage8-493-pytest-scratch-v2'
$expected = 'dac0cb789c1cf5f7655c01fb9323296a080da98e'
$ref = 'refs/heads/candidate/stop-tick-grid-20261012'
$old_bytecode = [environment]::getenvironmentvariable('pythondontwritebytecode','process')
$old_nousersite = [environment]::getenvironmentvariable('pythonnousersite','process')
$old_pytest_plugins = [environment]::getenvironmentvariable('pytest_disable_plugin_autoload','process')
write-output '=== stage8 #493 durable STOP coverage growth v2 isolated OFFLINE pytest ==='
write-output 'NO_FINAM NO_REAL_ORDERS NO_CANCEL NO_TASK_MUTATION NO_REARM NO_LIVE_SQLITE'
try {
    if (-not (test-path -literalpath $repo -pathtype container) -or
        -not (test-path -literalpath $python -pathtype leaf)) {
        throw 'OFFLINE_REPO_OR_EXISTING_PYTEST_VENV_MISSING'
    }
    $task = get-scheduledtask -taskname 'TradingSystemLab-Stage8-Production' -erroraction stop
    $switch = get-content -literalpath (join-path $runtime_root 'safety\stage8-trading-kill-switch.json') -raw -erroraction stop | convertfrom-json
    if ([string]$task.state -cne 'Disabled' -or $switch.state -cne 'HALTED') {
        throw 'PRODUCTION_NOT_ISOLATED_HALTED'
    }
    $repo_before = (& git -C $repo rev-parse '@').trim()
    if ($lastexitcode -ne 0 -or -not $repo_before) { throw 'ORIGINAL_WORKTREE_HEAD_INVALID' }
    write-output "OPERATOR_WORKTREE_HEAD_BEFORE=$repo_before"
    $env:pythondontwritebytecode = '1'
    $env:pythonnousersite = '1'
    $env:pytest_disable_plugin_autoload = '1'
    & $python -B -c 'import pytest,pandas,numpy,jsonschema,tabulate'
    if ($lastexitcode -ne 0) { throw 'ISOLATED_PYTEST_VENV_DEPENDENCIES_MISSING' }
    write-output 'ISOLATED_TEST_VENV_DEPENDENCIES=PASS'
    & git -C $repo fetch --no-tags origin $ref
    if ($lastexitcode -ne 0) { throw 'CANDIDATE_FETCH_FAILED' }
    & git -C $repo merge-base --is-ancestor $expected 'FETCH_HEAD'
    if ($lastexitcode -ne 0) { throw 'EXPECTED_CANDIDATE_COMMIT_NOT_IN_REMOTE' }
    if (-not (test-path -literalpath $worktree)) {
        & git -C $repo worktree add --detach $worktree $expected
        if ($lastexitcode -ne 0) { throw 'NEW_ISOLATED_WORKTREE_FAILED' }
        write-output 'NEW_ISOLATED_TEST_WORKTREE=CREATED'
    } else {
        write-output 'NEW_ISOLATED_TEST_WORKTREE=EXISTING_VERIFY_ONLY'
    }
    $pin = (& git -C $worktree rev-parse '@').trim()
    if ($lastexitcode -ne 0 -or $pin -cne $expected) {
        throw 'TEST_WORKTREE_PINNED_SHA_MISMATCH'
    }
    $tracked = @(& git -C $worktree status --porcelain --untracked-files=no)
    if ($lastexitcode -ne 0 -or $tracked.count -ne 0) {
        throw 'TEST_WORKTREE_TRACKED_FILES_CHANGED'
    }
    write-output "ISOLATED_CANDIDATE_SHA=$pin"
    $tests = @(
        'TradingSystemLab/stage8_robot/tests/test_stage8_493_partial_growth_candidate.py',
        'TradingSystemLab/stage8_robot/tests/test_stop_tick_grid_amendment.py',
        'TradingSystemLab/stage8_robot/tests/test_stage8_493_multifill_offline_acceptance.py'
    )
    foreach ($file in $tests) {
        if (-not (test-path -literalpath (join-path $worktree $file) -pathtype leaf)) {
            throw 'PINNED_TEST_SOURCE_NOT_FOUND'
        }
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
        $switch_after.state -cne 'HALTED' -or
        $repo_before -cne $repo_after -or $pin_after -cne $expected) {
        throw 'POST_TEST_PRODUCTION_OR_PINNED_WORKTREE_CHANGED'
    }
    write-output 'CLASSIFICATION=OFFLINE_DURABLE_GROWTH_REGRESSIONS_PASS_NOT_REAL_AUTHORITY'
} catch {
    $reason = [string]$_.exception.message
    if ($reason -cnotmatch '^[A-Z0-9_]{4,120}$') { $reason = 'OFFLINE_RUN_UNEXPECTED' }
    write-output "CLASSIFICATION=BLOCKED:$reason"
    exit 1
} finally {
    [environment]::setenvironmentvariable('pythondontwritebytecode',$old_bytecode,'process')
    [environment]::setenvironmentvariable('pythonnousersite',$old_nousersite,'process')
    [environment]::setenvironmentvariable('pytest_disable_plugin_autoload',$old_pytest_plugins,'process')
    write-output 'LIVE_TASK_MUTATED=NO'
    write-output 'REAL_ORDER_AUTHORIZED=NO'
    write-output 'PRODUCTION_CHECKOUT_MUTATED=NO'
}
