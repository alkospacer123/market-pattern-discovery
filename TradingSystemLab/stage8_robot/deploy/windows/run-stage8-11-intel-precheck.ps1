param(
    [Parameter(Mandatory=$true)][string]$RuntimeRoot,
    [Parameter(Mandatory=$true)][ValidateSet("LONG","SHORT")][string]$Direction,
    [Parameter(Mandatory=$true)][ValidatePattern('^[0-9a-f]{40}$')][string]$AcceptedCommit,
    [Parameter(Mandatory=$true)][ValidatePattern('^[0-9A-Fa-f]{64}$')][string]$ExternalEvidenceSha256,
    [string]$Python = "py.exe",
    [string]$ReportPath = ""
)
$ErrorActionPreference = "Stop"
$taskName = "TradingSystemLab-Stage8-Readonly"
$productionId = "PROD_STAGE7_46DB784378797C7FB04636892350AFF21006D71A31F2CED9D4B974EDA2DC36B8"
$repo = (Resolve-Path (Join-Path $PSScriptRoot "..\..\..\..")).Path
$runtime = [IO.Path]::GetFullPath($RuntimeRoot)
if (-not $ReportPath) { $ReportPath = Join-Path $runtime "diagnostics\stage8_11_intel_precheck.json" }

# Manual operator entrypoint only.  Frozen N4 order is the deterministic
# feasibility tie-break; Direction is explicit acceptance-test authority and
# is never inferred from T3 or performance.  This script exposes no execute flag.
try {
    if ((git -C $repo rev-parse HEAD) -cne $AcceptedCommit -or (git -C $repo status --porcelain)) {
        throw "STAGE8_11_ACCEPTED_CLEAN_COMMIT_REQUIRED"
    }
    $task = Get-ScheduledTask -TaskName $taskName -ErrorAction SilentlyContinue
    if ($task -and $task.State -ne "Disabled") { throw "STAGE8_11_SCHEDULED_TASK_NOT_DISABLED" }
    $conflicts = @(Get-CimInstance Win32_Process | Where-Object {
        $_.CommandLine -and ($_.CommandLine -match "readonly_supervisor|stage8_robot\.runner")
    })
    if ($conflicts.Count -ne 0) { throw "STAGE8_11_RUNTIME_OWNER_CONFLICT" }
    if (-not (Test-Path $runtime -PathType Container)) { throw "STAGE8_11_RUNTIME_MISSING" }
    $probe = Join-Path $runtime ".stage8-11-write-probe"; Set-Content $probe "probe"; Remove-Item $probe
    if ((Get-PSDrive -Name ([IO.Path]::GetPathRoot($runtime).Substring(0,1))).Free -lt 100MB) { throw "STAGE8_11_DISK_CAPACITY_LOW" }
    $clock = (Get-Date).ToUniversalTime(); if ([Math]::Abs(((Get-Date).ToUniversalTime()-$clock).TotalSeconds) -gt 2) { throw "STAGE8_11_CLOCK_INVALID" }
    & $Python -c "import sys; assert sys.prefix != sys.base_prefix, 'VENV_REQUIRED'"
    if ($LASTEXITCODE -ne 0) { throw "STAGE8_11_VENV_REQUIRED" }
    # Backup is mandatory preparation for the later physical run, and harmless now.
    & $Python -m TradingSystemLab.stage8_robot.backup_state --runtime-root $runtime
    if ($LASTEXITCODE -ne 0) { throw "STAGE8_11_STATE_BACKUP_FAILED" }
    . (Join-Path $PSScriptRoot "credential-store.ps1")
    . (Join-Path $PSScriptRoot "trading-credential-store.ps1")
    $readonly = Get-ReadonlyCredential $runtime $productionId
    $trading = Get-TradingCredential $runtime $productionId
    if ([string]$readonly.finam_real_account_id -cne [string]$trading.finam_real_account_id) { throw "STAGE8_11_ACCOUNT_MISMATCH" }
    $env:STAGE8_11_TRADING_SECRET = [string]$trading.finam_trading_api_secret
    $env:STAGE8_11_ACCOUNT_ID = [string]$trading.finam_real_account_id
    $env:STAGE8_11_DPAPI_VALIDATED = "true"
    $env:STAGE8_11_EXTERNAL_EVIDENCE_SHA256 = $ExternalEvidenceSha256.ToLowerInvariant()
    Push-Location $repo
    & $Python -m TradingSystemLab.stage8_robot.stage8_11_intel_acceptance --runtime-root $runtime --report $ReportPath --direction $Direction --accepted-commit $AcceptedCommit
    if ($LASTEXITCODE -ne 0) { throw "STAGE8_11_PRECHECK_CHILD_FAILED" }
    Pop-Location
} finally {
    foreach ($name in @("STAGE8_11_TRADING_SECRET","STAGE8_11_ACCOUNT_ID","STAGE8_11_DPAPI_VALIDATED","STAGE8_11_EXTERNAL_EVIDENCE_SHA256")) {
        Remove-Item "Env:$name" -ErrorAction SilentlyContinue
    }
    $readonly=$null; $trading=$null
}
