param(
    [switch]$execute,
    [string]$runtime_root = 'c:\tradingsystemlab\runtime',
    [string]$checkout = 'c:\tradingsystemlab\production\h1-184e8c2-20261012',
    [string]$python = 'c:\tslaudit\fill493\venv\scripts\python.exe',
    [string]$evidence_root = 'c:\tslaudit\fill493'
)
$erroractionpreference = 'stop'
$task_name = 'TradingSystemLab-Stage8-Production'
$spec = 'PROD_STAGE7_46DB784378797C7FB04636892350AFF21006D71A31F2CED9D4B974EDA2DC36B8'
$live_sha = '184e8c2b8fa092a606249ff293a4f507160bff29'
$pre = join-path $psscriptroot 'stage8-493-pre-isolation-readonly.ps1'
$pre_sha = '2d6e66058b80bef0f5c2dd4c6051c9decbb1032b3531fe05f4d668d836a0def9'
$post = join-path $psscriptroot 'stage8-493-post-isolation-readonly.ps1'
$post_sha = '37df9e1a8f4b0b18ee37d1acc8757ad674160e878264b2746ed0e1bb3e66c201'
$mutated = $false
write-output '=== stage8 #493 controlled production Task isolation ==='
write-output 'NO_REAL_ORDERS NO_REARM NO_TRADING_TOKEN NO_LIVE_SQLITE_MUTATION'
try {
    if (-not (test-path -literalpath $evidence_root -pathtype container)) { throw 'EVIDENCE_DIRECTORY_NOT_FOUND' }
    foreach ($file in @(@($pre,$pre_sha),@($post,$post_sha))) {
        if (-not (test-path -literalpath $file[0] -pathtype leaf) -or
            (get-filehash -literalpath $file[0] -algorithm sha256).hash.tolowerinvariant() -cne $file[1]) {
            throw 'ISOLATION_SCRIPT_HASH_INVALID'
        }
    }
    if (-not (test-path -literalpath $python -pathtype leaf)) { throw 'ISOLATED_PYTHON_MISSING' }
    $task = get-scheduledtask -taskname $task_name -taskpath '\' -erroraction stop
    $readonly = get-scheduledtask -taskname 'TradingSystemLab-Stage8-Readonly' -erroraction silentlycontinue
    if ([string]$task.state -cne 'Running' -or -not [bool]$task.settings.enabled) { throw 'PRODUCTION_TASK_NOT_ENABLED_RUNNING' }
    if ($null -ne $readonly -and [string]$readonly.state -cne 'Disabled') { throw 'READONLY_TASK_NOT_DISABLED' }
    if ($task.actions.count -ne 1 -or $task.actions[0].execute -notmatch '(?i)(^|\\)powershell\.exe$') { throw 'TASK_ACTION_EXECUTABLE_INVALID' }
    $args = [string]$task.actions[0].arguments
    foreach ($exact in @('run-production.ps1',$runtime_root,$checkout,$live_sha)) {
        if ($args.indexof($exact,[stringcomparison]::ordinalignorecase) -lt 0) { throw 'TASK_ACTION_IDENTITY_INVALID' }
    }
    if ($task.settings.restartcount -ne 10 -or
        @($task.triggers | where-object { $_.enabled }).count -ne 1) { throw 'TASK_RESTART_OR_TRIGGER_PROFILE_UNEXPECTED' }
    $switch = get-content -literalpath (join-path $runtime_root 'safety\stage8-trading-kill-switch.json') -raw | convertfrom-json
    if ($switch.state -cne 'HALTED' -or $switch.production_specification_id -cne $spec) { throw 'KILL_SWITCH_INVALID' }
    # The non-mutating v3 test checks actual process chain, SQLite and fresh FINAM.
    $fresh = @(& powershell.exe -noprofile -executionpolicy bypass -file $pre -runtime_root $runtime_root -checkout $checkout -python $python)
    if ($lastexitcode -ne 0 -or $fresh -notcontains 'CLASSIFICATION=PRE_ISOLATION_READONLY_PASS_OPERATOR_REVIEW_REQUIRED') {
        throw 'FRESH_PRE_ISOLATION_GATE_BLOCKED'
    }
    write-output 'FRESH_PROCESS_SQLITE_FINAM_HALTED=PASS'
    $all = @(get-ciminstance -classname win32_process -erroraction stop)
    $matches = @($all | where-object {
        $cmd = [string]$_.commandline
        ($_.name -ieq 'python.exe' -or $_.name -ieq 'pythonw.exe') -and
        $cmd.indexof('production_service',[stringcomparison]::ordinalignorecase) -ge 0 -and
        $cmd.indexof($runtime_root,[stringcomparison]::ordinalignorecase) -ge 0
    })
    if ($matches.count -ne 2) { throw 'SERVICE_PROCESS_COUNT_CHANGED' }
    $root = @($matches | where-object { $item=$_; @($matches | where-object { [int]$_.processid -eq [int]$item.parentprocessid }).count -eq 0 })
    if ($root.count -ne 1) { throw 'SERVICE_ROOT_AMBIGUOUS' }
    $child = @($matches | where-object { [int]$_.parentprocessid -eq [int]$root[0].processid })
    if ($child.count -ne 1) { throw 'SERVICE_CHILD_NOT_UNIQUE' }
    $parent = @($all | where-object { [int]$_.processid -eq [int]$root[0].parentprocessid })
    if ($parent.count -ne 1 -or $parent[0].name -ine 'powershell.exe') { throw 'SERVICE_POWERSHELL_MISSING' }
    foreach ($entry in $matches) {
        if ([string]$entry.commandline -notlike ('*'+$live_sha+'*')) { throw 'SERVICE_PROCESS_COMMIT_INVALID' }
    }
    $pscmd = [string]$parent[0].commandline
    foreach ($piece in @('run-production.ps1',$checkout,$runtime_root,$live_sha)) {
        if ($pscmd.indexof($piece,[stringcomparison]::ordinalignorecase) -lt 0) { throw 'SERVICE_POWERSHELL_IDENTITY_INVALID' }
    }
    $known = @([int]$parent[0].processid,[int]$root[0].processid,[int]$child[0].processid)
    write-output "IDENTIFIED_TASK_POWERSHELL_PID=$($known[0])"
    write-output "IDENTIFIED_SERVICE_ROOT_PID=$($known[1])"
    write-output "IDENTIFIED_SERVICE_CHILD_PID=$($known[2])"
    if (-not $execute) {
        write-output 'CLASSIFICATION=CHECK_ONLY_PASS_NO_MUTATION'
        return
    }
    # An exact original Task export is kept OUTSIDE runtime/state, without printing principal.
    $export = export-scheduledtask -taskname $task_name -taskpath '\' -erroraction stop
    if (-not $export -or $export.indexof($live_sha,[stringcomparison]::ordinalignorecase) -lt 0) { throw 'TASK_BACKUP_CONTENT_INVALID' }
    $tag = [datetime]::utcnow.tostring('yyyyMMddTHHmmssfffZ')
    $backup = join-path $evidence_root ('stage8-493-original-production-task-'+$tag+'.xml')
    $stream = [system.io.file]::open($backup,[system.io.filemode]::createnew,[system.io.fileaccess]::write,[system.io.fileshare]::none)
    try {
        $bytes = [system.text.encoding]::utf8.getbytes($export)
        $stream.write($bytes,0,$bytes.length)
        $stream.flush($true)
    } finally { $stream.dispose() }
    write-output "TASK_DEFINITION_BACKUP_SHA256=$((get-filehash -literalpath $backup -algorithm sha256).hash)"
    # Authorized production mutation: suppress all Task starts, then stop this Task.
    disable-scheduledtask -taskname $task_name -taskpath '\' -erroraction stop | out-null
    $mutated = $true
    $disabled = get-scheduledtask -taskname $task_name -taskpath '\' -erroraction stop
    if ([bool]$disabled.settings.enabled) { throw 'TASK_DISABLE_DID_NOT_PERSIST' }
    write-output 'TASK_DISABLED_RESTART_SUPPRESSED=PASS'
    stop-scheduledtask -taskname $task_name -taskpath '\' -erroraction stop | out-null
    write-output 'TASK_STOP_COMMAND_COMPLETED=YES'
    $exited = $false
    for ($i=0; $i -lt 12; $i++) {
        start-sleep -seconds 2
        $nowtask = get-scheduledtask -taskname $task_name -taskpath '\' -erroraction stop
        $running = @(get-ciminstance -classname win32_process -erroraction stop | where-object {
            $cmd = [string]$_.commandline
            $cmd.indexof($runtime_root,[stringcomparison]::ordinalignorecase) -ge 0 -and
            ($cmd.indexof('production_service',[stringcomparison]::ordinalignorecase) -ge 0 -or
             $cmd.indexof('run-production.ps1',[stringcomparison]::ordinalignorecase) -ge 0)
        })
        $old = @(get-ciminstance -classname win32_process -erroraction stop | where-object { $known -contains [int]$_.processid })
        if ([string]$nowtask.state -ceq 'Disabled' -and -not [bool]$nowtask.settings.enabled -and
            $running.count -eq 0 -and $old.count -eq 0) { $exited = $true; break }
    }
    if (-not $exited) { throw 'TASK_OR_CHILD_PROCESS_NOT_QUIESCENT' }
    write-output 'TASK_AND_ALL_IDENTIFIED_PROCESSES_EXITED=PASS'
    $post_result = @(& powershell.exe -noprofile -executionpolicy bypass -file $post -runtime_root $runtime_root -checkout $checkout -python $python)
    if ($lastexitcode -ne 0 -or $post_result -notcontains 'CLASSIFICATION=POST_ISOLATION_READONLY_PASS_NO_TRADE_AUTHORITY') {
        throw 'POST_ISOLATION_READONLY_GATE_BLOCKED'
    }
    write-output 'POST_STOP_FINAM_SQLITE_LOCK_GATE=PASS'
    write-output 'CLASSIFICATION=ISOLATED_HALTED_PENDING_GITHUB_OPERATIONAL_SYNC'
} catch {
    $reason = [string]$_.exception.message
    if ($reason -cnotmatch '^[A-Z0-9_]{4,120}$') { $reason='ISOLATION_UNEXPECTED' }
    if ($mutated) {
        write-output "CLASSIFICATION=BLOCKED_OPERATOR_RECOVERY_REQUIRED:$reason"
        write-output 'TASK_MAY_BE_DISABLED_OR_PARTIALLY_STOPPED; NEVER_AUTO_RESTART_OR_KILL_PID'
    } else { write-output "CLASSIFICATION=BLOCKED_NO_TASK_MUTATION:$reason" }
    exit 1
} finally {
    write-output "TASK_MUTATION_ATTEMPTED=$mutated"
    write-output 'REAL_ORDER_AUTHORIZED=NO'
    write-output 'REARM_PERFORMED=NO'
}
