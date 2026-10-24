# V20-07.3: install 12 thin H1-style operator wrappers + one V20 controller.
# Does not create/enable/start tasks or contact FINAM. 07.2 remains Disabled.
[CmdletBinding()]
param()
$ErrorActionPreference = 'Stop'
Set-StrictMode -Version Latest
$root = 'C:\V20Lab'
$stage = Join-Path $root 'staging-07'
$receiptPath = Join-Path $stage 'TASKS_07_2_REPORT.json'
$installPath = Join-Path $stage 'INSTALL_07_1_REPORT.json'
$output = Join-Path $stage 'OPERATOR_07_3_REPORT.json'
$ops = Join-Path $root 'operator'
$controller = Join-Path $ops 'operator-v20.ps1'
$sourceCommit = 'f2b39a64f2277369c93d77d892990880235c9d79'
$controllerBlob = '6905945c34bb14da119f6a1f7a6e3e79edf46be0'
$pin = '610109b736c53a5cc1025657291e272b1136b254'
$robots = @('v20-shallow','v20-obv','v20-inside')
$modes = @('check','start','stop','restart')
function require([bool]$condition, [string]$reason) {
    if (-not $condition) { throw $reason }
}
function git-blob([string]$path) {
    $value = (& git.exe hash-object -- $path)
    require ($LASTEXITCODE -eq 0 -and $value -match '^[0-9a-f]{40}$') 'V20_07_3_HASH_FAILED'
    return $value.Trim()
}
require ($env:OS -eq 'Windows_NT' -and $env:COMPUTERNAME -eq 'URIU-PC') 'V20_07_3_WRONG_HOST'
require ((Test-Path -LiteralPath $receiptPath -PathType Leaf) -and
         (Test-Path -LiteralPath $installPath -PathType Leaf)) 'V20_07_3_PREVIOUS_RECEIPT_MISSING'
require (-not (Test-Path -LiteralPath $output)) 'V20_07_3_REPORT_ALREADY_EXISTS'
$receipt = Get-Content -LiteralPath $receiptPath -Raw -Encoding UTF8 | ConvertFrom-Json
$prior = Get-Content -LiteralPath $installPath -Raw -Encoding UTF8 | ConvertFrom-Json
require ($receipt.schema -eq 'v20.intel.stage07.disabled_tasks.v1' -and
         $receipt.status -eq 'PASS_3_OF_3_DISABLED' -and
         $receipt.source_commit -eq $pin -and
         $receipt.live_enabled -eq $false -and
         $receipt.trading_authorized -eq $false -and
         $prior.result -eq 'PASS_STAGING_ONLY_3_OF_3' -and
         $prior.source_commit -eq $pin) 'V20_07_3_PREVIOUS_STAGES_NOT_PASS'
$taskRows = @($receipt.tasks)
require ($taskRows.Count -eq 3) 'V20_07_3_TASK_COUNT_INVALID'
foreach ($robot in $robots) {
    $matched = @($taskRows | Where-Object { $_.robot -eq $robot })
    require ($matched.Count -eq 1) 'V20_07_3_TASK_RECEIPT_MISMATCH'
    $task = Get-ScheduledTask -TaskPath '\' -TaskName $robot -ErrorAction Stop
    require ($task.State -eq 'Disabled' -and @($task.Actions).Count -eq 1 -and
             $task.Actions[0].Execute -ieq 'powershell.exe' -and
             $task.Actions[0].Arguments -eq $matched[0].action_arguments) 'V20_07_3_TASK_NOT_DISABLED_OR_CHANGED'
}
if (Test-Path -LiteralPath $ops) {
    $dir = Get-Item -LiteralPath $ops -Force
    require ($dir.PSIsContainer -and -not ($dir.Attributes -band [IO.FileAttributes]::ReparsePoint)) 'V20_07_3_OPERATOR_DIR_NOT_SAFE'
} else {
    [void](New-Item -ItemType Directory -Path $ops -ErrorAction Stop)
}
if (Test-Path -LiteralPath $controller) {
    require ((git-blob $controller) -eq $controllerBlob) 'V20_07_3_CONTROLLER_CONFLICT'
} else {
    $relative = ([char]86+'20_'+[char]84+'rading'+[char]83+'ystem_'+[char]77+'15/'+[char]86+'20-07/'+[char]79+'perator-'+[char]86+'20.ps1')
    $url = 'https://raw.githubusercontent.com/alkospacer123/market-pattern-discovery/' + $sourceCommit + '/' + $relative
    $temp = $controller + '.download'
    require (-not (Test-Path -LiteralPath $temp)) 'V20_07_3_TEMP_CONFLICT'
    try {
        Invoke-WebRequest -Uri $url -OutFile $temp -UseBasicParsing -ErrorAction Stop
        require ((git-blob $temp) -eq $controllerBlob) 'V20_07_3_CONTROLLER_HASH_MISMATCH'
        Move-Item -LiteralPath $temp -Destination $controller -ErrorAction Stop
    } finally {
        if (Test-Path -LiteralPath $temp) { Remove-Item -LiteralPath $temp -Force -ErrorAction SilentlyContinue }
    }
}
$wrappers = @()
foreach ($robot in $robots) {
    foreach ($mode in $modes) {
        $path = Join-Path $ops ($robot + '-' + $mode + '.ps1')
        # A thin wrapper passes only fixed robot/mode to the shared controller.
        $legacy = "& (Join-Path "+'$PSScriptRoot'+" 'operator-v20.ps1') -Robot '$robot' -Mode '$mode'"
        # Windows PowerShell -File will otherwise return 0 when the outer
        # wrapper ends, even if the invoked controller used 'exit 3'.
        # Propagate the controller's explicit result from this process.
        $wrapper = $legacy + [Environment]::NewLine + 'exit $LASTEXITCODE'
        if (Test-Path -LiteralPath $path) {
            $previous = (Get-Content -LiteralPath $path -Raw -Encoding UTF8).Trim()
            if ($previous -ceq $legacy.Trim()) {
                # Idempotent, narrow repair of only the 12 original wrappers;
                # no arbitrary existing scripts are overwritten.
                $wrapper | Set-Content -LiteralPath $path -Encoding UTF8 -ErrorAction Stop
                Write-Output ('V20_07_3_WRAPPER_EXIT_PROPAGATION_FIXED=' + $robot + '_' + $mode)
            } else {
                require ($previous -ceq $wrapper.Trim()) 'V20_07_3_EXISTING_WRAPPER_CHANGED'
            }
        } else {
            $wrapper | Set-Content -LiteralPath $path -Encoding UTF8 -ErrorAction Stop
        }
        $wrappers += $path
    }
}
foreach ($robot in $robots) {
    $check = Join-Path $ops ($robot + '-check.ps1')
    $log = @(& powershell.exe -NoProfile -ExecutionPolicy Bypass -File $check)
    require ($LASTEXITCODE -eq 0 -and
             $log -contains 'V20_OP_TASK_DISABLED=PASS' -and
             $log -contains 'V20_OP_LIVE=OFF' -and
             $log -contains 'V20_OP_RECONCILIATION=NOT_AVAILABLE_STAGING') 'V20_07_3_CHECK_NOT_PASS'
    Write-Output ('V20_07_3_' + $robot + '_CHECK=PASS_LIVE_OFF')
}
# Explicitly verify blocked start/restart; no attempt to enable/start Task.
foreach ($mode in @('start','restart')) {
    $guard = Join-Path $ops ('v20-shallow-' + $mode + '.ps1')
    $seen = @(& powershell.exe -NoProfile -ExecutionPolicy Bypass -File $guard)
    require ($LASTEXITCODE -eq 3 -and
             $seen -contains ('V20_OP_' + $mode.ToUpperInvariant() + '=REFUSED_LIVE_OFF') -and
             $seen -contains 'V20_OP_TASK_MUTATED=NO') 'V20_07_3_LIVE_START_GUARD_FAILED'
    Write-Output ('V20_07_3_' + $mode.ToUpperInvariant() + '=BLOCKED_AS_DESIGNED')
}
$stop = Join-Path $ops 'v20-shallow-stop.ps1'
$stopped = @(& powershell.exe -NoProfile -ExecutionPolicy Bypass -File $stop)
require ($LASTEXITCODE -eq 0 -and
         $stopped -contains 'V20_OP_STOP=ALREADY_DISABLED' -and
         $stopped -contains 'V20_OP_TASK_DISABLED=PASS') 'V20_07_3_STOP_NOT_SAFE'
Write-Output 'V20_07_3_STOP=ALREADY_DISABLED'
$record = [ordered]@{
    schema = 'v20.intel.stage07.operators.v1'
    result = 'PASS_3_ROBOTS_4_COMMANDS_LIVE_OFF'
    source_commit = $pin
    controller_source_commit = $sourceCommit
    controller_blob = $controllerBlob
    controller = $controller
    scripts = $wrappers
    task_mutations = 0
    trading_authorized = $false
    live_enabled = $false
    h1_m15_modified = $false
    finam_used = $false
    orders_sent = 0
    start_restart = 'FAIL_CLOSED_REFUSED'
    stop = 'IDEMPOTENT_DISABLED'
    health = 'STAGING_NOT_LIVE_NO_RECONCILIATION'
    next_roadmap = 'V20-07.4'
}
$record | ConvertTo-Json -Depth 6 | Set-Content -LiteralPath $output -Encoding UTF8 -ErrorAction Stop
Write-Output 'V20_07_3_RESULT=PASS_3_ROBOTS_4_COMMANDS_LIVE_OFF'
Write-Output ('V20_07_3_REPORT=' + $output)
Write-Output 'V20_07_3_NO_FINAM_NO_ORDERS_NO_LIVE_NO_H1_M15_MUTATION=YES'
