param(
    [string]$runtime_root = 'c:\tradingsystemlab\runtime',
    [string]$checkout = 'c:\tradingsystemlab\production\h1-184e8c2-20261012'
)
$erroractionpreference = 'stop'
$expected_commit = '184e8c2b8fa092a606249ff293a4f507160bff29'
$expected_spec = 'PROD_STAGE7_46DB784378797C7FB04636892350AFF21006D71A31F2CED9D4B974EDA2DC36B8'
write-output '=== stage8 #493 local process lineage read-only ==='
write-output 'NO_FINAM_NO_CREDENTIALS_NO_SQLITE_NO_TASK_OR_PROCESS_MUTATION_NO_REARM'
try {
    $task = get-scheduledtask -taskname 'TradingSystemLab-Stage8-Production' -erroraction stop
    $readonly_task = get-scheduledtask -taskname 'TradingSystemLab-Stage8-Readonly' -erroraction silentlycontinue
    if ([string]$task.state -cne 'Running') { throw 'PRODUCTION_TASK_NOT_RUNNING' }
    if ($null -ne $readonly_task -and [string]$readonly_task.state -cne 'Disabled') { throw 'READONLY_TASK_NOT_DISABLED' }
    $switch_file = join-path $runtime_root 'safety\stage8-trading-kill-switch.json'
    $switch = get-content -literalpath $switch_file -raw -erroraction stop | convertfrom-json
    if ($switch.state -cne 'HALTED' -or $switch.production_specification_id -cne $expected_spec) { throw 'KILL_SWITCH_NOT_HALTED_OR_IDENTITY_INVALID' }
    $task_arguments = (@($task.actions | foreach-object { [string]$_.arguments }) -join ' ')
    if ($task_arguments.indexof($expected_commit, [stringcomparison]::ordinalignorecase) -lt 0 -or
        $task_arguments.indexof($checkout, [stringcomparison]::ordinalignorecase) -lt 0 -or
        $task_arguments.indexof($runtime_root, [stringcomparison]::ordinalignorecase) -lt 0) { throw 'TASK_BINDING_NOT_VERIFIED' }
    $all_processes = @(get-ciminstance -classname win32_process -erroraction stop)
    $python_processes = @($all_processes | where-object { $_.name -ieq 'python.exe' -or $_.name -ieq 'pythonw.exe' })
    $candidates = @($python_processes | where-object {
        $command = [string]$_.commandline
        $command -and $command.indexof($runtime_root, [stringcomparison]::ordinalignorecase) -ge 0 -and
        ($command.indexof('production_service', [stringcomparison]::ordinalignorecase) -ge 0 -or
         $command.indexof('stage8-12-production', [stringcomparison]::ordinalignorecase) -ge 0)
    })
    write-output "TASK_STATE=$($task.state)"
    write-output "TASK_RESTART_LIMIT_CONFIGURED=$($task.settings.restartcount)"
    write-output "TASK_MULTIPLE_INSTANCES=$($task.settings.multipleinstances)"
    write-output "TASK_ENABLED_TRIGGERS=$(@($task.triggers | where-object { $_.enabled }).count)"
    write-output "MATCHING_PYTHON_PROCESSES=$($candidates.count)"
    $i = 0
    foreach ($process in ($candidates | sort-object processid)) {
        $i++
        $process_id = [int]$process.processid
        $parent_id = [int]$process.parentprocessid
        $parent = @($all_processes | where-object { [int]$_.processid -eq $parent_id } | select-object -first 1)
        $parent_name = if ($parent.count -eq 1) { [string]$parent[0].name } else { 'NOT_FOUND' }
        $grandparent_id = if ($parent.count -eq 1) { [string]$parent[0].parentprocessid } else { 'UNKNOWN' }
        $related = @($candidates | where-object { [int]$_.processid -eq $parent_id }).count -eq 1
        $cmd = [string]$process.commandline
        $has_commit = $cmd.indexof($expected_commit, [stringcomparison]::ordinalignorecase) -ge 0
        $has_module = $cmd.indexof('production_service', [stringcomparison]::ordinalignorecase) -ge 0
        $executable = if ($process.executablepath) { split-path -leaf ([string]$process.executablepath) } else { 'UNKNOWN' }
        write-output "CANDIDATE_${i}_PID=$process_id"
        write-output "CANDIDATE_${i}_PARENT_PID=$parent_id"
        write-output "CANDIDATE_${i}_PARENT_NAME=$parent_name"
        write-output "CANDIDATE_${i}_GRANDPARENT_PID=$grandparent_id"
        write-output "CANDIDATE_${i}_PARENT_IS_MATCHING_PYTHON=$related"
        write-output "CANDIDATE_${i}_EXECUTABLE_BASENAME=$executable"
        write-output "CANDIDATE_${i}_EXACT_COMMIT_IN_COMMAND=$has_commit"
        write-output "CANDIDATE_${i}_SERVICE_MODULE_IN_COMMAND=$has_module"
    }
    $switch_after = get-content -literalpath $switch_file -raw -erroraction stop | convertfrom-json
    $task_after = get-scheduledtask -taskname 'TradingSystemLab-Stage8-Production' -erroraction stop
    if ($switch_after.state -cne 'HALTED' -or $switch_after.production_specification_id -cne $expected_spec -or
        [string]$task_after.state -cne 'Running') { throw 'SAFETY_STATE_CHANGED_DURING_READ' }
    write-output 'CLASSIFICATION=READONLY_PROCESS_LINEAGE_COLLECTED_NOT_ISOLATED'
} catch {
    $code = [string]$_.exception.message
    if ($code -cnotmatch '^[A-Z0-9_]{4,120}$') { $code = 'READONLY_PROCESS_INVENTORY_FAILED' }
    write-output "CLASSIFICATION=BLOCKED:$code"
    exit 1
} finally {
    write-output 'NO_TASK_STOP_OR_DISABLE=YES'
    write-output 'NO_ORDER_ENDPOINTS=YES'
    write-output 'STOP_TASK_AUTHORIZED_BY_THIS_PROBE=NO'
}
