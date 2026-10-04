param(
    [Parameter(Mandatory=$true)][string]$RuntimeRoot,
    [Parameter(Mandatory=$true)][ValidatePattern('^[0-9a-f]{40}$')][string]$AcceptedRecoveryCommit,
    [string]$Python = "py.exe"
)
$ErrorActionPreference = "Stop"
$productionId = "PROD_STAGE7_46DB784378797C7FB04636892350AFF21006D71A31F2CED9D4B974EDA2DC36B8"
$acceptedPhysicalCommit = "069806355fc6931470d7f68d5ca6db20b06358fa"
$evidenceSha = "9FEFC5469F2C97F1EB36A5B5C99D323FA37BB948CF53C8A8745A27A06AB3B324"
$intent = "stage8.11:CNYRUBF:entry"
$taskName = "TradingSystemLab-Stage8-Readonly"
$repo = (Resolve-Path (Join-Path $PSScriptRoot "..\..\..\..")).Path
$runtime = [IO.Path]::GetFullPath($RuntimeRoot)
$physicalEvidence = Join-Path $runtime "diagnostics\stage8_11_physical_acceptance.json"
$lock = $null
$lockOwned = $false
$locationPushed = $false

# This manual boundary is intentionally order-incapable: it loads only the
# CurrentUser REAL_READONLY credential, keeps the Scheduled Task disabled, and
# invokes no trading, cancellation, modification, arming, or authorization path.
try {
    # Code authority and local evidence are proven before any credential is loaded.
    $head = (& git -C $repo rev-parse HEAD).Trim()
    if ($LASTEXITCODE -ne 0 -or $head -cne $AcceptedRecoveryCommit) { throw "STAGE8_11_RECOVERY_HEAD_MISMATCH" }
    $worktree = @(& git -C $repo status --porcelain)
    if ($LASTEXITCODE -ne 0 -or $worktree.Count -ne 0) { throw "STAGE8_11_RECOVERY_WORKTREE_NOT_CLEAN" }
    if (-not (Test-Path -LiteralPath $physicalEvidence -PathType Leaf)) { throw "STAGE8_11_PHYSICAL_EVIDENCE_MISSING" }
    $actualEvidenceSha = (Get-FileHash -LiteralPath $physicalEvidence -Algorithm SHA256).Hash
    if ($actualEvidenceSha -cne $evidenceSha) { throw "STAGE8_11_PHYSICAL_EVIDENCE_HASH_MISMATCH" }
    $switchPath = Join-Path $runtime "safety\stage8-trading-kill-switch.json"
    if (-not (Test-Path -LiteralPath $switchPath -PathType Leaf)) { throw "STAGE8_11_KILL_SWITCH_MISSING" }
    $switch = Get-Content -LiteralPath $switchPath -Raw | ConvertFrom-Json
    if ($switch.production_specification_id -cne $productionId -or $switch.state -cne "HALTED") {
        throw "STAGE8_11_KILL_SWITCH_NOT_HALTED"
    }
    $lock = [Threading.Mutex]::new($false, "Global\TradingSystemLab-Stage8-11-Failed-Intent-Recovery")
    try { $lockOwned = $lock.WaitOne(0) } catch [Threading.AbandonedMutexException] { $lockOwned = $true }
    if (-not $lockOwned) { throw "STAGE8_11_RECOVERY_INSTANCE_CONFLICT" }
    $task = Get-ScheduledTask -TaskName $taskName -ErrorAction SilentlyContinue
    if ($task -and $task.State -ne "Disabled") { throw "STAGE8_11_SCHEDULED_TASK_NOT_DISABLED" }
    $conflicts = @(Get-CimInstance Win32_Process | Where-Object {
        $_.ProcessId -ne $PID -and $_.CommandLine -and
        ($_.CommandLine -match "readonly_supervisor|stage8_robot\.runner|stage8_11_physical_acceptance|stage8_11_failed_attempt_recovery")
    })
    if ($conflicts.Count -ne 0) { throw "STAGE8_11_RUNTIME_OWNER_CONFLICT" }
    & $Python -c "import sys; assert sys.prefix != sys.base_prefix, 'VENV_REQUIRED'"
    if ($LASTEXITCODE -ne 0) { throw "STAGE8_11_VENV_REQUIRED" }
    . (Join-Path $PSScriptRoot "credential-store.ps1")
    $readonly = Get-ReadonlyCredential $runtime $productionId
    $env:STAGE8_11_READONLY_SECRET = [string]$readonly.finam_api_secret
    $env:STAGE8_11_READONLY_ACCOUNT_ID = [string]$readonly.finam_real_account_id
    Push-Location $repo
    $locationPushed = $true
    & $Python -m TradingSystemLab.stage8_robot.stage8_11_failed_attempt_recovery `
        --runtime-root $runtime --account-id $env:STAGE8_11_READONLY_ACCOUNT_ID `
        --accepted-recovery-commit $AcceptedRecoveryCommit --physical-evidence $physicalEvidence `
        --physical-evidence-sha256 $evidenceSha --intent-key $intent
    if ($LASTEXITCODE -ne 0) { throw "STAGE8_11_RECOVERY_CHILD_FAILED" }
} finally {
    if ($locationPushed) { Pop-Location; $locationPushed = $false }
    Remove-Item Env:STAGE8_11_READONLY_SECRET -ErrorAction SilentlyContinue
    Remove-Item Env:STAGE8_11_READONLY_ACCOUNT_ID -ErrorAction SilentlyContinue
    $readonly = $null
    if ($lockOwned) { $lock.ReleaseMutex(); $lockOwned = $false }
    if ($null -ne $lock) { $lock.Dispose(); $lock = $null }
}
