# V20-07.2: install THREE disabled Task Scheduler entries, never a live runner.
# Adapt H1's Windows Task registration; actions are intentionally blocked.
[CmdletBinding()]
param()
$ErrorActionPreference = 'Stop'
Set-StrictMode -Version Latest
$root = 'C:\V20Lab'
$stage = Join-Path $root 'staging-07'
$installReport = Join-Path $stage 'INSTALL_07_1_REPORT.json'
$readonlyReport = Join-Path $root 'readonly-06\BROKER_READONLY_REPORT_FUNDED.json'
$taskReport = Join-Path $stage 'TASKS_07_2_REPORT.json'
$blocker = Join-Path $stage 'v20-task-live-blocked.ps1'
$pin = '610109b736c53a5cc1025657291e272b1136b254'
$robotNames = @('v20-shallow','v20-obv','v20-inside')
function require([bool]$condition, [string]$reason) {
    if (-not $condition) { throw $reason }
}
require ($env:COMPUTERNAME -eq 'URIU-PC' -and $env:OS -eq 'Windows_NT') 'V20_07_2_WRONG_HOST'
$os = Get-CimInstance Win32_OperatingSystem -ErrorAction Stop
require ($os.Version -eq '10.0.19045' -and $os.Caption -match 'Windows 10 Pro') 'V20_07_2_WRONG_OS'
require ((Test-Path -LiteralPath $installReport -PathType Leaf) -and
         (Test-Path -LiteralPath $readonlyReport -PathType Leaf)) 'V20_07_2_PROOF_MISSING'
require (-not (Test-Path -LiteralPath $taskReport)) 'V20_07_2_REPORT_ALREADY_EXISTS'
$install = Get-Content -LiteralPath $installReport -Raw -Encoding UTF8 | ConvertFrom-Json
$broker = Get-Content -LiteralPath $readonlyReport -Raw -Encoding UTF8 | ConvertFrom-Json
require ($install.schema -eq 'v20.intel.stage07.install.1' -and
         $install.result -eq 'PASS_STAGING_ONLY_3_OF_3' -and
         $install.source_commit -eq $pin -and $install.live_enabled -eq $false -and
         $broker.schema -eq 'v20.finam.broker_readonly_report.v1' -and
         $broker.status -eq 'PASS_READONLY_3_OF_3' -and $broker.entry_authorized -eq $false) 'V20_07_2_PRIOR_STAGE_NOT_PASS'
$checkout = Join-Path $stage 'checkout'
require ((Test-Path -LiteralPath (Join-Path $checkout '.git') -PathType Container) -and
         $install.source_directory -eq $checkout) 'V20_07_2_CHECKOUT_MISMATCH'
$sha = (& git.exe -C $checkout rev-parse HEAD).Trim()
require ($LASTEXITCODE -eq 0 -and $sha -eq $pin) 'V20_07_2_SOURCE_SHA_MISMATCH'
$dirty = @(& git.exe -C $checkout status --porcelain | Where-Object { $_ })
require ($LASTEXITCODE -eq 0 -and $dirty.Count -eq 0) 'V20_07_2_SOURCE_DIRTY'
$installRows = @($install.robots)
$brokerRows = @($broker.accounts)
require ($installRows.Count -eq 3 -and $brokerRows.Count -eq 3) 'V20_07_2_ACCOUNT_COUNT_MISMATCH'
foreach ($robot in $robotNames) {
    $ir = @($installRows | Where-Object { $_.robot -eq $robot })
    $br = @($brokerRows | Where-Object { $_.robot -eq $robot })
    require ($ir.Count -eq 1 -and $br.Count -eq 1 -and
             $ir[0].source_sha -eq $pin -and $ir[0].live_enabled -eq $false -and
             $br[0].readonly_result -eq 'PASS_READONLY' -and $br[0].account_clean -eq $true) 'V20_07_2_ACCOUNT_PROOF_MISMATCH'
    $short = $robot.Substring(4)
    $config = Join-Path (Join-Path $root ('robots\' + $short)) 'config\staging.json'
    require (Test-Path -LiteralPath $config -PathType Leaf) 'V20_07_2_CONFIG_MISSING'
    $data = Get-Content -LiteralPath $config -Raw -Encoding UTF8 | ConvertFrom-Json
    require ($data.schema -eq 'v20.intel.staging.v1' -and
             $data.robot_id -eq $robot -and $data.account_sha256 -eq $br[0].account_sha256 -and
             $data.source_commit -eq $pin -and $data.live_enabled -eq $false -and
             $data.execution_mode -eq 'DISABLED_NOT_LIVE' -and
             $data.trading_token -eq 'NOT_CONFIGURED') 'V20_07_2_LIVE_CONFIG_FORBIDDEN'
}
# Each scheduled action calls ONLY this local fail-closed blocker.
# No FINAM import, trader import, token, stop, task mutation or order route.
$blockerText = @'
param([ValidateSet('v20-shallow','v20-obv','v20-inside')][string]$Robot)
Write-Output ('V20_TASK_LIVE_NOT_AUTHORIZED=' + $Robot)
exit 87
'@
if (Test-Path -LiteralPath $blocker) {
    $old = (Get-Content -LiteralPath $blocker -Raw -Encoding UTF8).Trim()
    require ($old -eq $blockerText.Trim()) 'V20_07_2_BLOCKER_CHANGED'
} else {
    $blockerText | Set-Content -LiteralPath $blocker -Encoding UTF8 -ErrorAction Stop
}
$identity = [Security.Principal.WindowsIdentity]::GetCurrent()
$userName = $identity.Name
$userSid = $identity.User.Value
require ($userSid -notin @('S-1-5-18','S-1-5-19','S-1-5-20')) 'V20_07_2_SERVICE_PRINCIPAL_FORBIDDEN'
$taskPrincipal = New-ScheduledTaskPrincipal -UserId $userName -LogonType Interactive -RunLevel Limited -ErrorAction Stop
$settings = New-ScheduledTaskSettingsSet -MultipleInstances IgnoreNew -ExecutionTimeLimit (New-TimeSpan -Minutes 1) -ErrorAction Stop
$trigger = New-ScheduledTaskTrigger -AtStartup -ErrorAction Stop
$rows = @()
foreach ($robot in $robotNames) {
    $short = $robot.Substring(4)
    $workingDirectory = Join-Path $root ('robots\' + $short)
    $args = '-NoProfile -NonInteractive -ExecutionPolicy RemoteSigned -File "' + $blocker + '" -Robot ' + $robot
    $existing = Get-ScheduledTask -TaskName $robot -TaskPath '\' -ErrorAction SilentlyContinue
    if ($null -ne $existing) {
        # Resume a partial install ONLY if the existing task is already
        # disabled, bound to this user and still runs the exact blocker.
        require ($existing.State -eq 'Disabled' -and
                 $existing.Principal.UserId -in @($userName,$userSid) -and
                 @($existing.Actions).Count -eq 1 -and
                 $existing.Actions[0].Execute -ieq 'powershell.exe' -and
                 $existing.Actions[0].Arguments -ceq $args -and
                 $existing.Actions[0].WorkingDirectory -ieq $workingDirectory) 'V20_07_2_EXISTING_TASK_CONFLICT'
        Write-Output ('V20_07_2_' + $robot + '=REUSED_DISABLED')
    } else {
        $action = New-ScheduledTaskAction -Execute 'powershell.exe' -Argument $args -WorkingDirectory $workingDirectory -ErrorAction Stop
        $task = New-ScheduledTask -Action $action -Trigger $trigger -Settings $settings -Principal $taskPrincipal -Description ('V20 '+ $robot +' staging only; LIVE NOT AUTHORIZED; exact source '+$pin) -ErrorAction Stop
        Register-ScheduledTask -TaskName $robot -InputObject $task -ErrorAction Stop | Out-Null
        Disable-ScheduledTask -TaskName $robot -TaskPath '\' -ErrorAction Stop | Out-Null
        Write-Output ('V20_07_2_' + $robot + '=REGISTERED_DISABLED')
    }
    $check = Get-ScheduledTask -TaskName $robot -TaskPath '\' -ErrorAction Stop
    require ($check.State -eq 'Disabled' -and @($check.Actions).Count -eq 1 -and
             $check.Actions[0].Arguments -ceq $args -and
             $check.Principal.UserId -in @($userName,$userSid)) 'V20_07_2_TASK_NOT_SAFE_DISABLED'
    $rows += [ordered]@{
        robot = $robot
        task_name = $robot
        task_path = '\'
        task_state = 'Disabled'
        windows_user = $userName
        windows_sid = $userSid
        logon_type = 'Interactive'
        run_level = 'Limited'
        action_executable = 'powershell.exe'
        action_arguments = $args
        working_directory = $workingDirectory
        source_commit = $pin
        live_enabled = $false
        trading_token_present = $false
    }
}
$summary = [ordered]@{
    schema = 'v20.intel.stage07.disabled_tasks.v1'
    status = 'PASS_3_OF_3_DISABLED'
    source_commit = $pin
    principal_user = $userName
    principal_sid = $userSid
    account_binding_authority = 'FUNDED_READONLY_ACCOUNT_SHA256_ONLY'
    trading_authorized = $false
    live_enabled = $false
    tasks_started = $false
    finam_used = $false
    orders_sent = 0
    h1_m15_task_mutations = 0
    action = 'PERMANENT_FAIL_CLOSED_PLACEHOLDER_UNTIL_SEPARATE_APPROVAL'
    tasks = $rows
    next_roadmap = 'V20-07.3'
}
$summary | ConvertTo-Json -Depth 8 | Set-Content -LiteralPath $taskReport -Encoding UTF8 -ErrorAction Stop
Write-Output 'V20_07_2_RESULT=PASS_3_OF_3_DISABLED'
Write-Output ('V20_07_2_SOURCE_SHA=' + $pin)
Write-Output ('V20_07_2_REPORT=' + $taskReport)
Write-Output 'V20_07_2_NO_FINAM_NO_ORDERS_NO_LIVE_NO_H1_M15_TASK_MUTATION=YES'
