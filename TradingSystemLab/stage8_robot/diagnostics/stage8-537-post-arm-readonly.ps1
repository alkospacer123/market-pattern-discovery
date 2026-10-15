# One-shot Roadmap 3.6 post-ARM operational observation. This script changes
# neither the Task nor the worker nor SQLite, order state or kill switch.
param(
    [string]$TaskName = 'TradingSystemLab-Stage8-Production',
    [string]$PythonProbe = (Join-Path $PSScriptRoot 'stage8-537-post-arm-readonly.py')
)
$ErrorActionPreference = 'Stop'
$expectedCommit = '3a18c8c24301c866a60f5d725de227288d48f7ec'
$expectedStage5 = '50f1fd2178c18b7ab3bd969be82ad01f47a34745'
$expectedSpec = 'PROD_STAGE7_46DB784378797C7FB04636892350AFF21006D71A31F2CED9D4B974EDA2DC36B8'
$expectedPythonHash = 'b613d7b757f5bf39734e8b75d535a8ca52b1cc56fad364c019dd1e0e3791fa7a'
$oldBytecode = [Environment]::GetEnvironmentVariable('PYTHONDONTWRITEBYTECODE', 'Process')
$credential = $null
Write-Output '=== Roadmap 3.6: one-shot post-ARM READONLY observer ==='
Write-Output 'NO_TRADING_TOKEN_NO_ORDER_OR_CANCEL_NO_TASK_RESTART_NO_REARM_NO_SQLITE_RECOVERY'
try {
    if (-not (Test-Path -LiteralPath $PythonProbe -PathType Leaf) -or
        (Get-FileHash -LiteralPath $PythonProbe -Algorithm SHA256).Hash.ToLowerInvariant() -cne $expectedPythonHash) {
        throw 'READONLY_PYTHON_HASH_INVALID'
    }
    $task = Get-ScheduledTask -TaskName $TaskName -ErrorAction Stop
    if ([string]$task.State -cne 'Running' -or $task.Settings.Enabled -cne $true -or
        @($task.Actions).Count -ne 1) { throw 'PRODUCTION_TASK_NOT_EXACT_RUNNING_ENABLED' }
    $action = $task.Actions[0]
    if ([string]$action.Execute -notmatch '(?i)powershell\.exe$') { throw 'PRODUCTION_TASK_ACTION_NOT_POWERSHELL' }
    $taskArguments = [string]$action.Arguments
    function BoundArg([string]$Name) {
        $pattern = '(?i)(?:^|\s)-' + [Regex]::Escape($Name) + '\s+"([^"]+)"'
        $match = [regex]::Match($taskArguments, $pattern)
        if (-not $match.Success) { throw 'PRODUCTION_TASK_BINDING_MISSING' }
        return $match.Groups[1].Value
    }
    $checkout = BoundArg 'Checkout'
    $runtime = BoundArg 'RuntimeRoot'
    $stage5 = BoundArg 'Stage5DataRoot'
    $python = BoundArg 'Python'
    if ($taskArguments.IndexOf("-ExpectedCommit $expectedCommit", [StringComparison]::OrdinalIgnoreCase) -lt 0 -or
        $taskArguments.IndexOf('run-production.ps1', [StringComparison]::OrdinalIgnoreCase) -lt 0) {
        throw 'PRODUCTION_TASK_SOURCE_NOT_PINNED'
    }
    foreach ($path in @($checkout, $runtime, $stage5)) {
        if (-not (Test-Path -LiteralPath $path -PathType Container)) { throw 'TASK_BOUND_DIRECTORY_MISSING' }
    }
    if (-not (Test-Path -LiteralPath $python -PathType Leaf)) { throw 'TASK_BOUND_PYTHON_MISSING' }
    $commit = @(& git -C $checkout rev-parse HEAD)
    if ($LASTEXITCODE -ne 0 -or $commit.Count -ne 1 -or $commit[0].Trim() -cne $expectedCommit) {
        throw 'INSTALLED_PRODUCTION_COMMIT_MISMATCH'
    }
    $stage5Commit = @(& git -C $stage5 rev-parse HEAD)
    if ($LASTEXITCODE -ne 0 -or $stage5Commit.Count -ne 1 -or $stage5Commit[0].Trim() -cne $expectedStage5) {
        throw 'PINNED_STAGE5_COMMIT_MISMATCH'
    }
    $dirty = @(& git -C $checkout status --porcelain)
    if ($LASTEXITCODE -ne 0 -or $dirty.Count -ne 0) { throw 'PRODUCTION_CHECKOUT_DIRTY' }

    # Exactly one Windows Task PowerShell wrapper and one Python parent-child
    # pair; the two Python PIDs are one worker tree, not duplicate robots.
    $processes = @(Get-CimInstance -ClassName Win32_Process -ErrorAction Stop)
    $wrappers = @($processes | Where-Object {
        $_.Name -ieq 'powershell.exe' -and $_.CommandLine -and
        $_.CommandLine.IndexOf('run-production.ps1', [StringComparison]::OrdinalIgnoreCase) -ge 0 -and
        $_.CommandLine.IndexOf($checkout, [StringComparison]::OrdinalIgnoreCase) -ge 0 -and
        $_.CommandLine.IndexOf($expectedCommit, [StringComparison]::OrdinalIgnoreCase) -ge 0
    })
    if ($wrappers.Count -ne 1) { throw 'TASK_WRAPPER_NOT_EXACTLY_ONE' }
    $workers = @($processes | Where-Object {
        $_.Name -in @('python.exe', 'pythonw.exe') -and $_.CommandLine -and
        $_.CommandLine.IndexOf($expectedCommit, [StringComparison]::OrdinalIgnoreCase) -ge 0 -and
        $_.CommandLine.IndexOf('production_service', [StringComparison]::OrdinalIgnoreCase) -ge 0 -and
        $_.CommandLine.IndexOf($runtime, [StringComparison]::OrdinalIgnoreCase) -ge 0
    })
    if ($workers.Count -ne 2) { throw 'EXACT_PYTHON_WORKER_TREE_NOT_TWO' }
    $parentLinks = @($workers | Where-Object {
        $id = [int]$_.ParentProcessId
        @($workers | Where-Object { [int]$_.ProcessId -eq $id }).Count -eq 1
    })
    if ($parentLinks.Count -ne 1) { throw 'PYTHON_PAIR_NOT_PARENT_CHILD' }
    $parent = @($workers | Where-Object { [int]$_.ProcessId -eq [int]$parentLinks[0].ParentProcessId })
    if ($parent.Count -ne 1 -or [int]$parent[0].ParentProcessId -ne [int]$wrappers[0].ProcessId) {
        throw 'WORKER_TREE_NOT_TASK_OWNED'
    }
    Write-Output 'TASK_ENABLED_RUNNING_EXACT_COMMIT=PASS'
    Write-Output 'SINGLE_WRAPPER_TWO_PYTHON_PARENT_CHILD=PASS'

    # Decrypt only the separate DPAPI REAL_READONLY credential, never Trading Token.
    . (Join-Path $checkout 'TradingSystemLab\stage8_robot\deploy\windows\credential-store.ps1')
    $credential = Get-ReadonlyCredential $runtime $expectedSpec
    $env:TSL36_READONLY_SECRET = [string]$credential.finam_api_secret
    $env:TSL36_READONLY_ACCOUNT = [string]$credential.finam_real_account_id
    $credential = $null
    $env:PYTHONDONTWRITEBYTECODE = '1'
    & $python -B $PythonProbe --runtime-root $runtime --checkout $checkout
    if ($LASTEXITCODE -ne 0) { throw 'POST_ARM_FINAM_AND_LEDGER_READONLY_NOT_PASS' }

    $taskAfter = Get-ScheduledTask -TaskName $TaskName -ErrorAction Stop
    if ([string]$taskAfter.State -cne 'Running' -or $taskAfter.Settings.Enabled -cne $true -or
        [string]$taskAfter.Actions[0].Arguments -cne $taskArguments) { throw 'TASK_CHANGED_DURING_OBSERVATION' }
    Write-Output 'TASK_STILL_RUNNING_UNMODIFIED=PASS'
    Write-Output 'FINAL_POST_ARM_READONLY=PASS'
} catch {
    $code = [string]$_.Exception.Message
    if ($code -cnotmatch '^[A-Z0-9_]{4,120}$') { $code = 'POST_ARM_READONLY_OBSERVER_FAILED' }
    Write-Output "FINAL_POST_ARM_READONLY=BLOCKED:$code"
    Write-Output 'NO_AUTO_HALT_NO_AUTO_RECOVERY_NO_AUTO_REARM=YES'
    exit 1
} finally {
    $credential = $null
    Remove-Item Env:TSL36_READONLY_SECRET -ErrorAction SilentlyContinue
    Remove-Item Env:TSL36_READONLY_ACCOUNT -ErrorAction SilentlyContinue
    [Environment]::SetEnvironmentVariable('PYTHONDONTWRITEBYTECODE', $oldBytecode, 'Process')
}
