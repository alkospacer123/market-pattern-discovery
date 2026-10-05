param(
    [Parameter(Mandatory=$true)][string]$RuntimeRoot,
    [Parameter(Mandatory=$true)][ValidatePattern('^[0-9a-f]{40}$')][string]$AcceptedCommit,
    [Parameter(Mandatory=$true)][ValidatePattern('^[0-9A-Fa-f]{64}$')][string]$ExternalEvidenceSha256,
    [Parameter(Mandatory=$true)][string]$Authorization,
    [string]$Python = "py.exe"
)
$ErrorActionPreference = "Stop"
$taskName = "TradingSystemLab-Stage8-Readonly"
$productionId = "PROD_STAGE7_46DB784378797C7FB04636892350AFF21006D71A31F2CED9D4B974EDA2DC36B8"
$expectedAuthorization = "STAGE_8_11_ONE_CONTRACT_ACCEPTANCE_AUTHORIZED"
$repo = (Resolve-Path (Join-Path $PSScriptRoot "..\..\..\..")).Path
$runtime = [IO.Path]::GetFullPath($RuntimeRoot)
$evidence = Join-Path $runtime "diagnostics\stage8_11_physical_acceptance_attempt3.json"

# Manual-only, fixed CNYRUBF/LONG/1 operator boundary.  This script is never a
# Scheduled Task target and has no arbitrary symbol, direction, or quantity.
try {
    if ($Authorization -cne $expectedAuthorization) { throw "STAGE8_11_EXPLICIT_AUTHORIZATION_REQUIRED" }
    if ((git -C $repo rev-parse HEAD) -cne $AcceptedCommit -or (git -C $repo status --porcelain)) {
        throw "STAGE8_11_ACCEPTED_CLEAN_COMMIT_REQUIRED"
    }
    & $Python -c "import sys; assert sys.prefix != sys.base_prefix, 'VENV_REQUIRED'"
    if ($LASTEXITCODE -ne 0) { throw "STAGE8_11_VENV_REQUIRED" }
    if (-not (Test-Path $runtime -PathType Container)) { throw "STAGE8_11_RUNTIME_MISSING" }
    $probe = Join-Path $runtime ".stage8-11-write-probe"; Set-Content $probe "probe"; Remove-Item $probe
    $drive = [IO.Path]::GetPathRoot($runtime).Substring(0,1)
    if ((Get-PSDrive -Name $drive).Free -lt 100MB) { throw "STAGE8_11_DISK_CAPACITY_LOW" }
    if ((Get-Service W32Time -ErrorAction Stop).Status -ne "Running") { throw "STAGE8_11_TIME_SERVICE_INVALID" }
    $timeStatus = (& w32tm /query /status 2>&1 | Out-String)
    $timeStatusExitCode = $LASTEXITCODE
    if ($timeStatusExitCode -ne 0) { throw "STAGE8_11_TIME_STATUS_QUERY_FAILED" }
    $timeSource = (& w32tm /query /source 2>&1 | Out-String).Trim()
    $timeSourceExitCode = $LASTEXITCODE
    if ($timeSourceExitCode -ne 0) { throw "STAGE8_11_TIME_SOURCE_QUERY_FAILED" }
    if ([string]::IsNullOrWhiteSpace($timeStatus) -or [string]::IsNullOrWhiteSpace($timeSource) -or
        $timeSource -match '^(Local CMOS Clock|Free-running System Clock)$') { throw "STAGE8_11_EXTERNAL_TIME_SOURCE_REQUIRED" }
    $task = Get-ScheduledTask -TaskName $taskName -ErrorAction SilentlyContinue
    if (-not $task -or $task.State -ne "Disabled") { throw "STAGE8_11_SCHEDULED_TASK_MUST_BE_DISABLED" }
    $conflicts = @(Get-CimInstance Win32_Process | Where-Object {
        $_.ProcessId -ne $PID -and $_.CommandLine -and
        ($_.CommandLine -match "readonly_supervisor|stage8_robot\.runner|stage8_11_physical_acceptance|stage8_11_physical_acceptance_attempt3|stage8_11_failed_attempt_recovery")
    })
    if ($conflicts.Count -ne 0) { throw "STAGE8_11_RUNTIME_OWNER_CONFLICT" }

    . (Join-Path $PSScriptRoot "credential-store.ps1")
    . (Join-Path $PSScriptRoot "trading-credential-store.ps1")
    $readonly = Get-ReadonlyCredential $runtime $productionId
    $trading = Get-TradingCredential $runtime $productionId
    if ([string]$readonly.finam_real_account_id -cne [string]$trading.finam_real_account_id) {
        throw "STAGE8_11_ACCOUNT_MISMATCH"
    }

    # Independently refresh the safety heartbeat with the structurally
    # order-incapable token.  Trading credentials are not placed in the process
    # environment until every READONLY plaintext value has been removed.
    $env:FINAM_MODE = "REAL_READONLY"
    $env:NEW_ENTRIES_DISABLED = "true"
    $env:FINAM_API_SECRET = [string]$readonly.finam_api_secret
    $env:FINAM_REAL_ACCOUNT_ID = [string]$readonly.finam_real_account_id
    Push-Location $repo
    & $Python -m TradingSystemLab.stage8_robot.readonly_supervisor --runtime-root $runtime --once
    if ($LASTEXITCODE -ne 0) { throw "STAGE8_11_READONLY_REFRESH_FAILED" }
    foreach ($name in @("FINAM_MODE","NEW_ENTRIES_DISABLED","FINAM_API_SECRET","FINAM_REAL_ACCOUNT_ID")) {
        Remove-Item "Env:$name" -ErrorAction SilentlyContinue
    }
    $readonly = $null

    $env:STAGE8_11_PHYSICAL_AUTHORIZATION = $Authorization
    $env:STAGE8_11_DPAPI_VALIDATED = "true"
    $env:STAGE8_11_TRADING_SECRET = [string]$trading.finam_trading_api_secret
    $env:STAGE8_11_ACCOUNT_ID = [string]$trading.finam_real_account_id
    & $Python -m TradingSystemLab.stage8_robot.stage8_11_physical_acceptance_attempt3 `
        --runtime-root $runtime --accepted-commit $AcceptedCommit --evidence $evidence `
        --external-evidence-sha256 $ExternalEvidenceSha256
    if ($LASTEXITCODE -ne 0) { throw "STAGE8_11_PHYSICAL_CHILD_FAILED" }
    Pop-Location
} finally {
    # Defense in depth only: the child remains primary HALT authority.  This is
    # an offline/local write and never authenticates to FINAM or submits an order.
    try {
        & $Python -c "from pathlib import Path; from TradingSystemLab.stage8_robot.trading_safety_gate import emergency_halt; emergency_halt(Path(r'''$runtime'''))"
    } catch {
        Write-Warning "STAGE8_11_PARENT_HALT_FAILED: $($_.Exception.Message)"
    }
    foreach ($name in @("FINAM_MODE","NEW_ENTRIES_DISABLED","FINAM_API_SECRET","FINAM_REAL_ACCOUNT_ID",
        "STAGE8_11_PHYSICAL_AUTHORIZATION","STAGE8_11_DPAPI_VALIDATED","STAGE8_11_TRADING_SECRET","STAGE8_11_ACCOUNT_ID")) {
        Remove-Item "Env:$name" -ErrorAction SilentlyContinue
    }
    $Authorization = $null; $readonly = $null; $trading = $null
    if ((Get-Location).Path -eq $repo) { Pop-Location }
}
