param(
    [string]$runtime_root = 'c:\tradingsystemlab\runtime',
    [string]$checkout = 'c:\tradingsystemlab\production\h1-184e8c2-20261012',
    [string]$python = 'c:\tslaudit\fill493\venv\scripts\python.exe'
)
$erroractionpreference = 'stop'
$spec = 'PROD_STAGE7_46DB784378797C7FB04636892350AFF21006D71A31F2CED9D4B974EDA2DC36B8'
$live_sha = '184e8c2b8fa092a606249ff293a4f507160bff29'
$source = join-path $psscriptroot 'stage8_493_post_isolation_broker_readonly.py'
$source_sha = '92fc06d2fba9d5d5062d3a3dc14bb74c8c3efd32754a07585dc92d5cb7ea7a13'
$audit = join-path $psscriptroot 'stage8_493_isolation_sqlite_readonly.py'
$audit_sha = '0f102987ca04a56abd62f6f3fe54e8cb3266ccfbe3c3852ccb9c7cb47d28f51b'
$prior_bytecode = [environment]::getenvironmentvariable('pythondontwritebytecode','process')
$credential = $null
write-output '=== stage8 #493 post-isolation readonly verification ==='
write-output 'NO_TRADING_TOKEN NO_SQLITE_WRITES NO_ORDER_OR_CANCEL NO_TASK_MUTATION NO_REARM'
try {
    foreach ($entry in @(@($source,$source_sha),@($audit,$audit_sha))) {
        if (-not (test-path -literalpath $entry[0] -pathtype leaf) -or
            (get-filehash -literalpath $entry[0] -algorithm sha256).hash.tolowerinvariant() -cne $entry[1]) {
            throw 'READONLY_SOURCE_HASH_INVALID'
        }
    }
    if (-not (test-path -literalpath $python -pathtype leaf)) { throw 'PYTHON_NOT_FOUND' }
    $task = get-scheduledtask -taskname 'TradingSystemLab-Stage8-Production' -taskpath '\' -erroraction stop
    $other = get-scheduledtask -taskname 'TradingSystemLab-Stage8-Readonly' -erroraction silentlycontinue
    if ([string]$task.state -cne 'Disabled' -or [bool]$task.settings.enabled -ne $false) { throw 'PRODUCTION_TASK_NOT_DISABLED' }
    if ($null -ne $other -and [string]$other.state -cne 'Disabled') { throw 'SECONDARY_TASK_ENABLED' }
    $task_args = (@($task.actions | foreach-object { [string]$_.arguments }) -join ' ')
    if ($task_args.indexof($live_sha,[stringcomparison]::ordinalignorecase) -lt 0 -or
        $task_args.indexof($checkout,[stringcomparison]::ordinalignorecase) -lt 0 -or
        $task_args.indexof($runtime_root,[stringcomparison]::ordinalignorecase) -lt 0) { throw 'TASK_BINDING_CHANGED' }
    $service_processes = @(get-ciminstance -classname win32_process -erroraction stop | where-object {
        $cmd = [string]$_.commandline
        $cmd.indexof($runtime_root,[stringcomparison]::ordinalignorecase) -ge 0 -and
        ($cmd.indexof('production_service',[stringcomparison]::ordinalignorecase) -ge 0 -or
         $cmd.indexof('run-production.ps1',[stringcomparison]::ordinalignorecase) -ge 0)
    })
    if ($service_processes.count -ne 0) { throw 'PRODUCTION_PROCESS_ORPHAN_PRESENT' }
    $lock = join-path $runtime_root 'state\stage8-12-production.lock'
    if (-not (test-path -literalpath $lock -pathtype leaf)) { throw 'PRODUCTION_LOCK_MISSING' }
    try {
        $handle = [system.io.file]::open($lock,[system.io.filemode]::open,[system.io.fileaccess]::read,[system.io.fileshare]::none)
        $handle.dispose()
    } catch { throw 'PRODUCTION_LOCK_HANDLE_NOT_QUIESCENT' }
    $sw = get-content -literalpath (join-path $runtime_root 'safety\stage8-trading-kill-switch.json') -raw | convertfrom-json
    if ($sw.state -cne 'HALTED' -or $sw.production_specification_id -cne $spec) { throw 'HALTED_IDENTITY_INVALID' }
    $env:pythondontwritebytecode = '1'
    $db = @(& $python -b $audit --runtime-root $runtime_root)
    if ($lastexitcode -ne 0 -or $db[-1] -cne 'SQLITE_ISOLATION_GATE=PASS_READONLY_NOT_STOP_AUTHORITY') { throw 'SQLITE_POST_STOP_INVALID' }
    . (join-path $checkout 'TradingSystemLab\stage8_robot\deploy\windows\credential-store.ps1')
    $credential = get-readonlycredential $runtime_root $spec
    $env:stage8_493_readonly_secret = [string]$credential.finam_api_secret
    $env:stage8_493_readonly_account = [string]$credential.finam_real_account_id
    $broker = @(& $python -b $source --runtime-root $runtime_root --checkout $checkout)
    if ($lastexitcode -ne 0 -or $broker[-2] -cne 'POST_ISOLATION_BROKER_FLAT=PASS' -or
        $broker[-1] -cne 'NO_ORDER_OR_CANCEL=YES') { throw 'FINAM_POST_STOP_BLOCKED' }
    $db2 = @(& $python -b $audit --runtime-root $runtime_root)
    if ($lastexitcode -ne 0 -or $db2[-1] -cne 'SQLITE_ISOLATION_GATE=PASS_READONLY_NOT_STOP_AUTHORITY') { throw 'SQLITE_POST_FINAM_INVALID' }
    $task2 = get-scheduledtask -taskname 'TradingSystemLab-Stage8-Production' -taskpath '\' -erroraction stop
    if ([string]$task2.state -cne 'Disabled' -or [bool]$task2.settings.enabled -ne $false) { throw 'TASK_REENABLED_DURING_VERIFICATION' }
    $active = @(get-ciminstance -classname win32_process -erroraction stop | where-object {
        $cmd = [string]$_.commandline
        $cmd.indexof($runtime_root,[stringcomparison]::ordinalignorecase) -ge 0 -and
        ($cmd.indexof('production_service',[stringcomparison]::ordinalignorecase) -ge 0 -or
         $cmd.indexof('run-production.ps1',[stringcomparison]::ordinalignorecase) -ge 0)
    })
    if ($active.count -ne 0) { throw 'PRODUCTION_PROCESS_REAPPEARED' }
    write-output 'TASK_DISABLED_AND_PROCESS_ZERO=PASS'
    write-output 'LOCK_HANDLE_QUIESCENT=PASS'
    write-output 'SQLITE_POST_STOP_BEFORE_AFTER=PASS'
    write-output 'FINAM_POST_STOP_TWO_SNAPSHOTS=PASS'
    write-output 'CLASSIFICATION=POST_ISOLATION_READONLY_PASS_NO_TRADE_AUTHORITY'
} catch {
    $msg = [string]$_.exception.message
    if ($msg -cnotmatch '^[A-Z0-9_]{4,120}$') { $msg = 'POST_STOP_UNEXPECTED' }
    write-output "CLASSIFICATION=BLOCKED:$msg"
    exit 1
} finally {
    remove-item env:stage8_493_readonly_secret -erroraction silentlycontinue
    remove-item env:stage8_493_readonly_account -erroraction silentlycontinue
    $credential = $null
    [environment]::setenvironmentvariable('pythondontwritebytecode',$prior_bytecode,'process')
    write-output 'NO_REAL_ORDER_AUTHORIZATION=YES'
}
