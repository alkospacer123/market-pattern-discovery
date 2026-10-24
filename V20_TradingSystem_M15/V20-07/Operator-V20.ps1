# V20-07.3: standalone V20-only operator, reuse H1 check/stop conventions.
# "start" and "restart" deliberately refuse until a separately approved LIVE release.
[CmdletBinding()]
param(
    [Parameter(Mandatory=$true)][ValidateSet('v20-shallow','v20-obv','v20-inside')][string]$Robot,
    [Parameter(Mandatory=$true)][ValidateSet('check','start','stop','restart')][string]$Mode
)
$ErrorActionPreference = 'Stop'
Set-StrictMode -Version Latest
$root = 'C:\V20Lab'
$stage = Join-Path $root 'staging-07'
$pin = '610109b736c53a5cc1025657291e272b1136b254'
$taskReceipt = Join-Path $stage 'TASKS_07_2_REPORT.json'
$blocker = Join-Path $stage 'v20-task-live-blocked.ps1'
function require([bool]$condition, [string]$reason) {
    if (-not $condition) { throw $reason }
}
function bound-sid([string]$user) {
    if ([string]::IsNullOrWhiteSpace($user)) { return $null }
    try {
        if ($user -match '^S-[0-9]+(-[0-9]+)+$') {
            return ([Security.Principal.SecurityIdentifier]::new($user)).Value
        }
        return ([Security.Principal.NTAccount]::new($user)).Translate([Security.Principal.SecurityIdentifier]).Value
    } catch { return $null }
}
function task-proof {
    require (Test-Path -LiteralPath $taskReceipt -PathType Leaf) 'V20_OP_TASK_RECEIPT_MISSING'
    $receipt = Get-Content -LiteralPath $taskReceipt -Raw -Encoding UTF8 | ConvertFrom-Json
    require ($receipt.schema -eq 'v20.intel.stage07.disabled_tasks.v1' -and
             $receipt.status -eq 'PASS_3_OF_3_DISABLED' -and
             $receipt.source_commit -eq $pin -and
             $receipt.live_enabled -eq $false -and $receipt.trading_authorized -eq $false) 'V20_OP_TASK_RECEIPT_INVALID'
    $rows = @($receipt.tasks)
    require ($rows.Count -eq 3) 'V20_OP_TASK_COUNT_INVALID'
    $one = @($rows | Where-Object { $_.robot -eq $Robot })
    require ($one.Count -eq 1 -and $one[0].live_enabled -eq $false -and
             $one[0].source_commit -eq $pin) 'V20_OP_WRONG_ROBOT_RECEIPT'
    $short = $Robot.Substring(4)
    $expectedDirectory = Join-Path $root ('robots\' + $short)
    $config = Join-Path $expectedDirectory 'config\staging.json'
    require (Test-Path -LiteralPath $config -PathType Leaf) 'V20_OP_CONFIG_MISSING'
    $settings = Get-Content -LiteralPath $config -Raw -Encoding UTF8 | ConvertFrom-Json
    require ($settings.schema -eq 'v20.intel.staging.v1' -and
             $settings.robot_id -eq $Robot -and $settings.live_enabled -eq $false -and
             $settings.execution_mode -eq 'DISABLED_NOT_LIVE' -and
             $settings.trading_token -eq 'NOT_CONFIGURED' -and
             $settings.source_commit -eq $pin -and
             $settings.account_sha256 -eq $one[0].account_sha256) 'V20_OP_CONFIG_LIVE_OR_UNBOUND'
    # The 07.2 task report intentionally omits raw account IDs; staging report
    # must still provide the same account hash. Never persist or print secrets.
    $task = Get-ScheduledTask -TaskName $Robot -TaskPath '\' -ErrorAction Stop
    $actions = @($task.Actions)
    $expectedArgs = '-NoProfile -NonInteractive -ExecutionPolicy RemoteSigned -File "' + $blocker + '" -Robot ' + $Robot
    require ($actions.Count -eq 1 -and
             $actions[0].Execute -ieq 'powershell.exe' -and
             $actions[0].Arguments -ceq $expectedArgs -and
             $actions[0].WorkingDirectory -ieq $expectedDirectory -and
             (bound-sid ([string]$task.Principal.UserId)) -eq $receipt.principal_sid) 'V20_OP_TASK_ACTION_OR_SID_MISMATCH'
    return $task
}
function observe {
    param($task)
    $short = $Robot.Substring(4)
    $instance = Join-Path $root ('robots\' + $short)
    Write-Output ('V20_OP_ROBOT=' + $Robot)
    Write-Output ('V20_OP_TASK_STATE=' + $task.State)
    Write-Output ('V20_OP_TASK_PRINCIPAL_SID_MATCH=PASS')
    Write-Output ('V20_OP_SOURCE_SHA=' + $pin)
    Write-Output 'V20_OP_LIVE=OFF'
    Write-Output 'V20_OP_TRADING_TOKEN=NOT_CONFIGURED'
    Write-Output 'V20_OP_EXECUTION=BLOCKED_PLACEHOLDER'
    # Task state and worker state are separate; a disabled task does not
    # prove there are no unrelated manually started processes.
    $workers = @()
    try {
        $workers = @(Get-CimInstance Win32_Process -Filter "Name='python.exe' OR Name='pythonw.exe'" -ErrorAction Stop |
            Where-Object { $_.CommandLine -and $_.CommandLine.Contains('V20_TradingSystem_M15.v20_runtime') -and
                $_.CommandLine.Contains($Robot) })
        Write-Output ('V20_OP_WORKER_PROCESS_COUNT=' + $workers.Count)
    } catch { Write-Output 'V20_OP_WORKER_PROCESS_COUNT=UNAVAILABLE' }
    $status = Join-Path $instance 'status.json'
    if (Test-Path -LiteralPath $status -PathType Leaf) {
        try {
            $state = Get-Content -LiteralPath $status -Raw -Encoding UTF8 | ConvertFrom-Json
            Write-Output ('V20_OP_LAST_STATUS=' + [string]$state.reason)
            Write-Output ('V20_OP_KILL_SWITCH=' + [string]$state.kill_switch)
        } catch {
            Write-Output 'V20_OP_LAST_STATUS=UNREADABLE'
            Write-Output 'V20_OP_KILL_SWITCH=UNVERIFIED'
        }
    } else {
        Write-Output 'V20_OP_LAST_STATUS=NOT_CONFIGURED_STAGING'
        Write-Output 'V20_OP_KILL_SWITCH=NOT_CONFIGURED_STAGING'
    }
    $log = Join-Path $instance 'logs\m15.jsonl'
    if (Test-Path -LiteralPath $log -PathType Leaf) {
        $recent = @(Get-Content -LiteralPath $log -Tail 10 -Encoding UTF8)
        Write-Output ('V20_OP_LAST_CYCLE_LINES=' + $recent.Count)
        foreach ($line in $recent) {
            try {
                $record = $line | ConvertFrom-Json -ErrorAction Stop
                Write-Output ('V20_OP_CYCLE_AT=' + [string]$record.observed_at + ' REASON=' + [string]$record.reason)
            } catch { Write-Output 'V20_OP_CYCLE=UNREADABLE' }
        }
    } else {
        Write-Output 'V20_OP_LAST_CYCLES=NOT_AVAILABLE_STAGING'
    }
    # No LIVE ledger, stops or broker reconciliation runs in 07.3.
    # Do not imply 0 actual trades or PASS reconciliation from absent data.
    Write-Output 'V20_OP_TRADES=NOT_AVAILABLE_STAGING'
    Write-Output 'V20_OP_STOPS=NOT_AVAILABLE_STAGING'
    Write-Output 'V20_OP_WARNINGS=NOT_AVAILABLE_STAGING'
    Write-Output 'V20_OP_RECONCILIATION=NOT_AVAILABLE_STAGING'
}
try {
    require ($env:OS -eq 'Windows_NT' -and $env:COMPUTERNAME -eq 'URIU-PC') 'V20_OP_WRONG_HOST'
    $task = task-proof
    if ($Mode -eq 'start' -or $Mode -eq 'restart') {
        Write-Output ('V20_OP_' + $Mode.ToUpperInvariant() + '=REFUSED_LIVE_OFF')
        Write-Output 'V20_OP_TASK_MUTATED=NO'
        exit 3
    }
    if ($Mode -eq 'stop') {
        if ($task.State -ne 'Disabled') {
            Stop-ScheduledTask -TaskName $Robot -TaskPath '\' -ErrorAction SilentlyContinue
            Disable-ScheduledTask -TaskName $Robot -TaskPath '\' -ErrorAction Stop | Out-Null
            Write-Output 'V20_OP_STOP=DISABLED'
        } else {
            Write-Output 'V20_OP_STOP=ALREADY_DISABLED'
        }
        $task = task-proof
        require ($task.State -eq 'Disabled') 'V20_OP_STOP_NOT_DISABLED'
    }
    observe -task $task
    if ($task.State -ne 'Disabled') {
        Write-Output 'V20_OP_TASK_DISABLED=FAIL'
        exit 4
    }
    Write-Output 'V20_OP_TASK_DISABLED=PASS'
    exit 0
} catch {
    $err = [string]$_.Exception.Message
    if ($err -match '^V20_OP_[A-Z0-9_]{1,100}$') {
        Write-Output ('V20_OP_FAIL=' + $err)
    } else {
        Write-Output 'V20_OP_FAIL=UNEXPECTED_OPERATOR_ERROR'
    }
    exit 1
}
