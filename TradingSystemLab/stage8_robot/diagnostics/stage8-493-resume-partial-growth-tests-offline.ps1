$erroractionpreference = 'stop'
$repo = 'c:\tradingsystemlab\market-pattern-discovery'
$runtime_root = 'c:\tradingsystemlab\runtime'
$worktree = 'c:\tslaudit\fill493\stage8-493-partial-growth-offline'
$expected = '2c262d629ee7607f2bc546b84a21d27b46346904'
$bootstrap = 'c:\tslaudit\fill493\venv\scripts\python.exe'
$venv = 'c:\tslaudit\fill493\venv-stage8-493-offline-pytest'
$python = join-path $venv 'scripts\python.exe'
$test_temp = 'c:\tslaudit\fill493\stage8-493-pytest-scratch'
$original_bytecode = [environment]::getenvironmentvariable('pythondontwritebytecode', 'process')
write-output '=== stage8 #493 resume isolated OFFLINE pytest after missing pytest ==='
write-output 'NO_FINAM NO_REAL_ORDERS NO_TASK_MUTATION NO_REARM NO_LIVE_SQLITE NO_PRODUCTION_CHECKOUT_CHANGE'
try {
    if (-not (test-path -literalpath $repo -pathtype container) -or
        -not (test-path -literalpath $worktree -pathtype container) -or
        -not (test-path -literalpath $bootstrap -pathtype leaf)) {
        throw 'ISOLATED_TEST_INPUT_MISSING'
    }
    $task = get-scheduledtask -taskname 'TradingSystemLab-Stage8-Production' -erroraction stop
    $switch = get-content -literalpath (join-path $runtime_root 'safety\stage8-trading-kill-switch.json') -raw -erroraction stop | convertfrom-json
    if ([string]$task.state -cne 'Disabled' -or $switch.state -cne 'HALTED') {
        throw 'PRODUCTION_NOT_ISOLATED_HALTED'
    }
    $original = (& git -C $repo rev-parse '@').trim()
    $pin = (& git -C $worktree rev-parse '@').trim()
    if ($lastexitcode -ne 0 -or -not $original -or $pin -cne $expected) {
        throw 'PINNED_WORKTREE_SHA_MISMATCH'
    }
    $tracked_changes = @(& git -C $worktree status --porcelain --untracked-files=no)
    if ($lastexitcode -ne 0 -or $tracked_changes.count -ne 0) {
        throw 'PINNED_WORKTREE_TRACKED_FILES_CHANGED'
    }
    write-output "ISOLATED_CANDIDATE_SHA=$pin"
    write-output "OPERATOR_REPO_HEAD_BEFORE=$original"
    if (-not (test-path -literalpath $python -pathtype leaf)) {
        if (test-path -literalpath $venv) { throw 'TEST_VENV_INCOMPLETE_REVIEW_REQUIRED' }
        write-output 'CREATING_SEPARATE_TEST_VENV=YES'
        & $bootstrap -m venv $venv
        if ($lastexitcode -ne 0 -or -not (test-path -literalpath $python -pathtype leaf)) {
            throw 'ISOLATED_TEST_VENV_CREATION_FAILED'
        }
    }
    $env:pythondontwritebytecode = '1'
    & $python -B -c 'import pytest,pandas,numpy,jsonschema,tabulate'
    if ($lastexitcode -ne 0) {
        write-output 'INSTALLING_TEST_DEPENDENCIES_ONLY_IN_SEPARATE_VENV=YES'
        & $python -B -m pip --disable-pip-version-check --no-input install 'pytest>=8,<10' 'pandas>=2,<3' 'numpy>=1.24,<3' 'jsonschema>=4,<5' 'tabulate>=0.9,<1'
        if ($lastexitcode -ne 0) { throw 'ISOLATED_TEST_DEPENDENCY_INSTALL_FAILED' }
        & $python -B -c 'import pytest,pandas,numpy,jsonschema,tabulate; print("TEST_ENV_PYTEST="+pytest.__version__); print("TEST_ENV_PANDAS="+pandas.__version__)'
        if ($lastexitcode -ne 0) { throw 'ISOLATED_TEST_DEPENDENCIES_MISSING' }
    } else {
        & $python -B -c 'import pytest,pandas; print("TEST_ENV_PYTEST="+pytest.__version__); print("TEST_ENV_PANDAS="+pandas.__version__)'
        if ($lastexitcode -ne 0) { throw 'ISOLATED_TEST_DEPENDENCIES_MISSING' }
    }
    $test_files = @(
        'TradingSystemLab/stage8_robot/tests/test_stage8_493_partial_growth_candidate.py',
        'TradingSystemLab/stage8_robot/tests/test_stop_tick_grid_amendment.py',
        'TradingSystemLab/stage8_robot/tests/test_stage8_493_multifill_offline_acceptance.py'
    )
    foreach ($rel in $test_files) {
        if (-not (test-path -literalpath (join-path $worktree $rel) -pathtype leaf)) {
            throw 'PINNED_TEST_FILE_MISSING'
        }
    }
    push-location $worktree
    try {
        & $python -B -m pytest -q -p no:cacheprovider --basetemp $test_temp @test_files
        if ($lastexitcode -ne 0) { throw 'CANDIDATE_REGRESSION_TESTS_FAILED' }
    } finally { pop-location }
    $post_task = get-scheduledtask -taskname 'TradingSystemLab-Stage8-Production' -erroraction stop
    $post_switch = get-content -literalpath (join-path $runtime_root 'safety\stage8-trading-kill-switch.json') -raw | convertfrom-json
    $after_repo = (& git -C $repo rev-parse '@').trim()
    $after_pin = (& git -C $worktree rev-parse '@').trim()
    if ($lastexitcode -ne 0 -or [string]$post_task.state -cne 'Disabled' -or
        $post_switch.state -cne 'HALTED' -or $after_repo -cne $original -or $after_pin -cne $expected) {
        throw 'POST_TEST_PRODUCTION_OR_WORKTREE_AUTHORITY_CHANGED'
    }
    write-output 'CLASSIFICATION=OFFLINE_CANDIDATE_GROWTH_TESTS_PASS_NOT_REAL_AUTHORITY'
} catch {
    $error_code = [string]$_.exception.message
    if ($error_code -cnotmatch '^[A-Z0-9_]{4,120}$') { $error_code = 'OFFLINE_TEST_UNEXPECTED' }
    write-output "CLASSIFICATION=BLOCKED:$error_code"
    exit 1
} finally {
    [environment]::setenvironmentvariable('pythondontwritebytecode', $original_bytecode, 'process')
    write-output 'LIVE_TASK_MUTATED=NO'
    write-output 'REAL_ORDER_AUTHORIZED=NO'
    write-output 'PRODUCTION_CHECKOUT_MUTATED=NO'
}
