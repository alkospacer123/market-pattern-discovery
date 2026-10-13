param(
    [string]$runtime_root = 'c:\tradingsystemlab\runtime',
    [string]$checkout = 'c:\tradingsystemlab\production\h1-184e8c2-20261012',
    [string]$python = 'c:\tslaudit\fill493\venv\scripts\python.exe'
)
$erroractionpreference = 'stop'
$live_sha = '184e8c2b8fa092a606249ff293a4f507160bff29'
$audit = join-path $psscriptroot 'stage8_493_isolation_sqlite_readonly.py'
$broker_probe = join-path $psscriptroot 'stage8-493-finam-broker-flat-readonly.ps1'
$audit_sha = '0f102987ca04a56abd62f6f3fe54e8cb3266ccfbe3c3852ccb9c7cb47d28f51b'
write-output '=== stage8 #493 pre-isolation audit: readonly, no task stop ==='
write-output 'NO_TRADING_TOKEN NO_LIVE_SQLITE_WRITES NO_ORDER_OR_CANCEL NO_TASK_MUTATION NO_REARM'
try {
    if (-not (test-path -literalpath $runtime_root -pathtype container) -or
        -not (test-path -literalpath $checkout -pathtype container) -or
        -not (test-path -literalpath $python -pathtype leaf) -or
        -not (test-path -literalpath $audit -pathtype leaf) -or
        -not (test-path -literalpath $broker_probe -pathtype leaf)) { throw 'LOCAL_INPUT_MISSING' }
    $actual_sha = (get-filehash -literalpath $audit -algorithm sha256).hash.tolowerinvariant()
    if ($actual_sha -cne $audit_sha) { throw 'SQLITE_AUDIT_HASH_INVALID' }
    push-location -literalpath $checkout
    try {
        $commit = (& git rev-parse @).trim()
        if ($lastexitcode -ne 0 -or $commit -cne $live_sha) { throw 'LIVE_COMMIT_MISMATCH' }
        $dirty = @(& git status --porcelain)
        if ($lastexitcode -ne 0 -or $dirty.count -ne 0) { throw 'LIVE_CHECKOUT_DIRTY' }
    } finally {
        pop-location
    }
    $task = get-scheduledtask -taskname 'TradingSystemLab-Stage8-Production' -erroraction stop
    $readonly_task = get-scheduledtask -taskname 'TradingSystemLab-Stage8-Readonly' -erroraction silentlycontinue
    if ([string]$task.state -cne 'Running') { throw 'PRODUCTION_TASK_NOT_RUNNING' }
    if ($null -ne $readonly_task -and [string]$readonly_task.state -cne 'Disabled') { throw 'READONLY_TASK_NOT_DISABLED' }
    $task_args = (@($task.actions | foreach-object { [string]$_.arguments }) -join ' ')
    if ($task_args.indexof($live_sha, [stringcomparison]::ordinalignorecase) -lt 0 -or
        $task_args.indexof($checkout, [stringcomparison]::ordinalignorecase) -lt 0 -or
        $task_args.indexof($runtime_root, [stringcomparison]::ordinalignorecase) -lt 0) { throw 'TASK_BINDING_UNVERIFIED' }
    $candidates = @(get-ciminstance -classname win32_process -filter "name = 'python.exe' or name = 'pythonw.exe'" |
        where-object { $_.commandline -and
            $_.commandline.indexof($runtime_root, [stringcomparison]::ordinalignorecase) -ge 0 -and
            ($_.commandline.indexof('production_service', [stringcomparison]::ordinalignorecase) -ge 0 -or
             $_.commandline.indexof('stage8-12-production', [stringcomparison]::ordinalignorecase) -ge 0) })
    write-output "PRODUCTION_SERVICE_PROCESS_CANDIDATES=$($candidates.count)"
    write-output "TASK_RESTART_COUNT=$($task.settings.restartcount)"
    write-output "TASK_START_WHEN_AVAILABLE=$($task.settings.startwhenavailable)"
    write-output "TASK_MULTIPLE_INSTANCES=$($task.settings.multipleinstances)"
    write-output "TASK_ENABLED_TRIGGER_COUNT=$(@($task.triggers | where-object { $_.enabled }).count)"
    if ($candidates.count -ne 1) { throw 'PRODUCTION_PROCESS_NOT_UNIQUELY_IDENTIFIED' }
    $before = @(& $python -b $audit --runtime-root $runtime_root)
    if ($lastexitcode -ne 0 -or $before[-1] -cne 'SQLITE_ISOLATION_GATE=PASS_READONLY_NOT_STOP_AUTHORITY') { throw 'SQLITE_PRE_BROKER_AUDIT_BLOCKED' }
    $broker = @(& powershell.exe -noprofile -executionpolicy bypass -file $broker_probe -runtime_root $runtime_root -checkout $checkout -python $python)
    if ($lastexitcode -ne 0 -or $broker[-1] -cne 'FINAL_READONLY_BROKER_GATE=PASS') { throw 'FRESH_BROKER_GATE_BLOCKED' }
    $after = @(& $python -b $audit --runtime-root $runtime_root)
    if ($lastexitcode -ne 0 -or $after[-1] -cne 'SQLITE_ISOLATION_GATE=PASS_READONLY_NOT_STOP_AUTHORITY') { throw 'SQLITE_POST_BROKER_AUDIT_BLOCKED' }
    $task_after = get-scheduledtask -taskname 'TradingSystemLab-Stage8-Production' -erroraction stop
    if ([string]$task_after.state -cne 'Running') { throw 'TASK_CHANGED_DURING_AUDIT' }
    $switch = get-content -literalpath (join-path $runtime_root 'safety\stage8-trading-kill-switch.json') -raw | convertfrom-json
    if ($switch.state -cne 'HALTED') { throw 'KILL_SWITCH_NOT_HALTED' }
    write-output 'SQLITE_BEFORE_AFTER=PASS'
    write-output 'FRESH_BROKER_DOUBLE_SNAPSHOT=PASS'
    write-output 'KILL_SWITCH_HALTED=PASS'
    write-output 'CLASSIFICATION=PRE_ISOLATION_READONLY_PASS_OPERATOR_REVIEW_REQUIRED'
} catch {
    $code = [string]$_.exception.message
    if ($code -cnotmatch '^[A-Z0-9_]{4,120}$') { $code = 'PRE_ISOLATION_UNEXPECTED' }
    write-output "CLASSIFICATION=BLOCKED:$code"
    exit 1
} finally {
    write-output 'STOP_TASK_AUTHORIZED_BY_THIS_SCRIPT=NO'
    write-output 'PRODUCTION_TASK_CHANGED_BY_THIS_SCRIPT=NO'
    write-output 'SLTP_REAL_ORDER_AUTHORIZED=NO'
}
