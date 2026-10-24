# V20-07.4: native Windows staging acceptance; READONLY, no real broker calls.
[CmdletBinding()]
param()
$ErrorActionPreference = 'Stop'
Set-StrictMode -Version Latest
$root = 'C:\V20Lab'
$stage = Join-Path $root 'staging-07'
$report = Join-Path $stage 'INTEL_STAGING_REPORT.json'
$pin = '610109b736c53a5cc1025657291e272b1136b254'
$checkout = Join-Path $stage 'checkout'
$operatorDir = Join-Path $root 'operator'
$controller = Join-Path $operatorDir 'operator-v20.ps1'
$controllerBlob = '6905945c34bb14da119f6a1f7a6e3e79edf46be0'
$blocker = Join-Path $stage 'v20-task-live-blocked.ps1'
$robots = @('v20-shallow','v20-obv','v20-inside')
$modes = @('check','start','stop','restart')
$inputs = [ordered]@{
    funded = Join-Path $root 'readonly-06\BROKER_READONLY_REPORT_FUNDED.json'
    staging = Join-Path $stage 'INSTALL_07_1_REPORT.json'
    disabled_tasks = Join-Path $stage 'TASKS_07_2_REPORT.json'
    operators = Join-Path $stage 'OPERATOR_07_3_REPORT.json'
}
function require([bool]$ok,[string]$message) {
    if (-not $ok) { throw $message }
}
function read-json([string]$path) {
    require (Test-Path -LiteralPath $path -PathType Leaf) 'V20_07_4_RECEIPT_MISSING'
    return (Get-Content -LiteralPath $path -Raw -Encoding UTF8 | ConvertFrom-Json)
}
function safe-folder([string]$path) {
    require (Test-Path -LiteralPath $path -PathType Container) 'V20_07_4_FOLDER_MISSING'
    $folder = Get-Item -LiteralPath $path -Force -ErrorAction Stop
    require (-not ($folder.Attributes -band [IO.FileAttributes]::ReparsePoint)) 'V20_07_4_REPARSE_FORBIDDEN'
    [void](Get-Acl -LiteralPath $path -ErrorAction Stop)
}
function resolve-sid([string]$text) {
    if ([string]::IsNullOrWhiteSpace($text)) { return $null }
    try {
        if ($text -match '^S-[0-9]+(-[0-9]+)+$') {
            return ([Security.Principal.SecurityIdentifier]::new($text)).Value
        }
        return ([Security.Principal.NTAccount]::new($text)).Translate([Security.Principal.SecurityIdentifier]).Value
    } catch { return $null }
}
require ($env:OS -eq 'Windows_NT' -and $env:COMPUTERNAME -eq 'URIU-PC') 'V20_07_4_WRONG_HOST'
$os = Get-CimInstance Win32_OperatingSystem -ErrorAction Stop
require ($os.Version -eq '10.0.19045' -and $os.Caption -match 'Windows 10 Pro') 'V20_07_4_WRONG_OS'
require (-not (Test-Path -LiteralPath $report)) 'V20_07_4_REPORT_ALREADY_EXISTS'
foreach ($path in @($root,$stage,$checkout,$operatorDir)) { safe-folder $path }
$funded = read-json $inputs.funded
$installed = read-json $inputs.staging
$taskReceipt = read-json $inputs.disabled_tasks
$operatorReceipt = read-json $inputs.operators
require ($funded.schema -eq 'v20.finam.broker_readonly_report.v1' -and
         $funded.status -eq 'PASS_READONLY_3_OF_3' -and
         $funded.stage_06_status -eq 'PASS' -and
         $funded.entry_authorized -eq $false) 'V20_07_4_FUNDING_RECEIPT_INVALID'
require ($installed.schema -eq 'v20.intel.stage07.install.1' -and
         $installed.result -eq 'PASS_STAGING_ONLY_3_OF_3' -and
         $installed.source_commit -eq $pin -and $installed.live_enabled -eq $false -and
         $installed.tasks_modified -eq $false) 'V20_07_4_INSTALL_RECEIPT_INVALID'
require ($taskReceipt.schema -eq 'v20.intel.stage07.disabled_tasks.v1' -and
         $taskReceipt.status -eq 'PASS_3_OF_3_DISABLED' -and
         $taskReceipt.source_commit -eq $pin -and $taskReceipt.live_enabled -eq $false -and
         $taskReceipt.trading_authorized -eq $false -and
         $taskReceipt.tasks_started -eq $false) 'V20_07_4_TASK_RECEIPT_INVALID'
require ($operatorReceipt.schema -eq 'v20.intel.stage07.operators.v1' -and
         $operatorReceipt.result -eq 'PASS_3_ROBOTS_4_COMMANDS_LIVE_OFF' -and
         $operatorReceipt.source_commit -eq $pin -and
         $operatorReceipt.live_enabled -eq $false -and
         $operatorReceipt.trading_authorized -eq $false -and
         $operatorReceipt.start_restart -eq 'FAIL_CLOSED_REFUSED') 'V20_07_4_OPERATOR_RECEIPT_INVALID'
$source = (& git.exe -C $checkout rev-parse HEAD).Trim()
require ($LASTEXITCODE -eq 0 -and $source -eq $pin) 'V20_07_4_PINNED_SOURCE_MISMATCH'
$dirty = @(& git.exe -C $checkout status --porcelain | Where-Object { $_ })
require ($LASTEXITCODE -eq 0 -and $dirty.Count -eq 0) 'V20_07_4_STAGING_SOURCE_DIRTY'
require ((Test-Path -LiteralPath $controller -PathType Leaf) -and
         $operatorReceipt.controller_blob -eq $controllerBlob) 'V20_07_4_OPERATOR_CONTROLLER_MISSING'
$controllerActual = (& git.exe hash-object -- $controller).Trim()
require ($LASTEXITCODE -eq 0 -and $controllerActual -eq $controllerBlob) 'V20_07_4_OPERATOR_SOURCE_HASH_MISMATCH'
require (Test-Path -LiteralPath $blocker -PathType Leaf) 'V20_07_4_TASK_BLOCKER_MISSING'
$blockerExpected = @'
param([ValidateSet('v20-shallow','v20-obv','v20-inside')][string]$Robot)
Write-Output ('V20_TASK_LIVE_NOT_AUTHORIZED=' + $Robot)
exit 87
'@
$blockerActual = (Get-Content -LiteralPath $blocker -Raw -Encoding UTF8).Replace([string][char]13,'').Trim()
require ($blockerActual -ceq $blockerExpected.Replace([string][char]13,'').Trim()) 'V20_07_4_TASK_BLOCKER_CHANGED'
$currentSid = [Security.Principal.WindowsIdentity]::GetCurrent().User.Value
require ($currentSid -eq $taskReceipt.principal_sid) 'V20_07_4_TASK_PRINCIPAL_SID_MISMATCH'
$accounts = @($funded.accounts)
$installRows = @($installed.robots)
$taskRows = @($taskReceipt.tasks)
require ($accounts.Count -eq 3 -and $installRows.Count -eq 3 -and
         $taskRows.Count -eq 3 -and @($operatorReceipt.scripts).Count -eq 12) 'V20_07_4_INSTANCE_COUNTS_INVALID'
$accepted = @()
foreach ($robot in $robots) {
    $account = @($accounts | Where-Object { $_.robot -eq $robot })
    $inst = @($installRows | Where-Object { $_.robot -eq $robot })
    $registered = @($taskRows | Where-Object { $_.robot -eq $robot })
    require ($account.Count -eq 1 -and $inst.Count -eq 1 -and
             $registered.Count -eq 1) 'V20_07_4_ACCOUNT_IDENTITY_INCOMPLETE'
    require ($account[0].readonly_result -eq 'PASS_READONLY' -and
             $account[0].account_clean -eq $true -and
             $account[0].money_status -eq 'PASS') 'V20_07_4_BROKER_ACCOUNT_NOT_PASS'
    $instanceDir = Join-Path $root ('robots\' + $robot.Substring(4))
    require ($inst[0].directory -ieq $instanceDir -and
             $inst[0].source_sha -eq $pin -and
             $inst[0].live_enabled -eq $false) 'V20_07_4_INSTANCE_PATH_OR_SHA_INVALID'
    safe-folder $instanceDir
    foreach ($name in @('config','state','logs','secrets')) {
        safe-folder (Join-Path $instanceDir $name)
    }
    require (@(Get-ChildItem -LiteralPath (Join-Path $instanceDir 'secrets') -Force).Count -eq 0) 'V20_07_4_UNEXPECTED_TRADING_SECRET'
    $config = read-json (Join-Path $instanceDir 'config\staging.json')
    require ($config.schema -eq 'v20.intel.staging.v1' -and
             $config.robot_id -eq $robot -and
             $config.account_sha256 -eq $account[0].account_sha256 -and
             $config.source_commit -eq $pin -and
             $config.live_enabled -eq $false -and
             $config.execution_mode -eq 'DISABLED_NOT_LIVE' -and
             $config.trading_token -eq 'NOT_CONFIGURED') 'V20_07_4_LIVE_OFF_CONFIG_CHANGED'
    $task = Get-ScheduledTask -TaskName $robot -TaskPath '\' -ErrorAction Stop
    $wantedArgs = '-NoProfile -NonInteractive -ExecutionPolicy RemoteSigned -File "' + $blocker + '" -Robot ' + $robot
    require ($task.State -eq 'Disabled' -and @($task.Actions).Count -eq 1 -and
             $task.Actions[0].Execute -ieq 'powershell.exe' -and
             $task.Actions[0].Arguments -ceq $wantedArgs -and
             $task.Actions[0].WorkingDirectory -ieq $instanceDir -and
             (resolve-sid ([string]$task.Principal.UserId)) -eq $currentSid -and
             $registered[0].task_state -eq 'Disabled' -and
             $registered[0].action_arguments -ceq $wantedArgs) 'V20_07_4_TASK_ACTION_OR_SID_CHANGED'
    $verified = 0
    foreach ($mode in $modes) {
        $wrapperPath = Join-Path $operatorDir ($robot + '-' + $mode + '.ps1')
        require (Test-Path -LiteralPath $wrapperPath -PathType Leaf) 'V20_07_4_WRAPPER_MISSING'
        $actual = (Get-Content -LiteralPath $wrapperPath -Raw -Encoding UTF8).Replace([string][char]13,'').Trim()
        $call = "& (Join-Path "+'$PSScriptRoot'+" 'operator-v20.ps1') -Robot '$robot' -Mode '$mode'"
        $expected = $call + [string][char]10 + 'exit $LASTEXITCODE'
        require ($actual -ceq $expected -and
                 (@($operatorReceipt.scripts) -contains $wrapperPath)) 'V20_07_4_WRAPPER_CHANGED'
        $verified++
    }
    $checkPath = Join-Path $operatorDir ($robot + '-check.ps1')
    $observed = @(& powershell.exe -NoProfile -ExecutionPolicy Bypass -File $checkPath)
    $checkExit = $LASTEXITCODE
    require ($checkExit -eq 0 -and
             $observed -contains 'V20_OP_TASK_DISABLED=PASS' -and
             $observed -contains 'V20_OP_LIVE=OFF' -and
             $observed -contains 'V20_OP_EXECUTION=BLOCKED_PLACEHOLDER' -and
             $observed -contains 'V20_OP_RECONCILIATION=NOT_AVAILABLE_STAGING') 'V20_07_4_READONLY_CHECK_NOT_PASS'
    $accepted += [ordered]@{
        robot = $robot
        account_sha256 = $account[0].account_sha256
        instance_dir = $instanceDir
        task_state = 'Disabled'
        principal_sid_match = $true
        operator_wrappers_verified = $verified
        check = 'PASS_READONLY_LIVE_OFF'
        live_enabled = $false
        live_trades_stops_reconciliation = 'NOT_AVAILABLE_STAGING'
    }
    Write-Output ('V20_07_4_' + $robot + '=PASS_DISABLED_LIVE_OFF')
}
# Only count identifiable V20 worker command lines; do not claim total
# visibility into processes for which Windows withholds CommandLine.
$workersStatus = 'NOT_QUERIED'
$identifiedCount = $null
try {
    $pythonProcesses = @(Get-CimInstance Win32_Process -Filter "Name='python.exe' OR Name='pythonw.exe'" -ErrorAction Stop)
    $v20Workers = @($pythonProcesses | Where-Object { $_.CommandLine -and
        $_.CommandLine -match 'V20_TradingSystem_M15\.v20_runtime\.(m15_runner|production_service)' })
    $identifiedCount = $v20Workers.Count
    $workersStatus = 'IDENTIFIED_COMMANDLINES_ONLY'
    require ($identifiedCount -eq 0) 'V20_07_4_V20_PROCESS_RUNNING'
} catch {
    if ($_.Exception.Message -eq 'V20_07_4_V20_PROCESS_RUNNING') { throw }
    $workersStatus = 'UNKNOWN_PROCESS_QUERY_FAILED'
    $identifiedCount = $null
}
$digests = [ordered]@{}
foreach ($entry in $inputs.GetEnumerator()) {
    $digests[$entry.Key] = (Get-FileHash -LiteralPath $entry.Value -Algorithm SHA256).Hash.ToLowerInvariant()
}
$record = [ordered]@{
    schema = 'v20.intel.stage07.staging_acceptance.v1'
    status = 'PASS_4_OF_4_STAGING_LIVE_OFF'
    source_commit = $pin
    report_sha256 = $digests
    host = $env:COMPUTERNAME
    windows = $os.Caption
    robots = $accepted
    task_mutations_by_07_4 = 0
    tasks_started_by_07_4 = $false
    finam_used_by_07_4 = $false
    h1_m15_modified_by_07_4 = $false
    live_enabled = $false
    trading_tokens_configured = $false
    real_orders_sent_by_07_4 = 0
    live_execution_verified = $false
    protective_sltp_verified_live = $false
    live_crash_recovery_verified = $false
    broker_reconciliation_verified_live = $false
    worker_observation = $workersStatus
    identified_v20_worker_count = $identifiedCount
    next_roadmap = 'V20-08_ONLY_WITH_SEPARATE_REAL_TRADE_AUTHORIZATION'
}
$record | ConvertTo-Json -Depth 10 | Set-Content -LiteralPath $report -Encoding UTF8 -ErrorAction Stop
Write-Output 'V20_07_4_RESULT=PASS_4_OF_4_STAGING_LIVE_OFF'
Write-Output ('V20_07_4_PINNED_SHA=' + $pin)
Write-Output ('V20_07_4_REPORT=' + $report)
Write-Output 'V20_07_4_NO_FINAM_NO_ORDERS_NO_LIVE_NO_H1_M15_MUTATIONS=YES'
