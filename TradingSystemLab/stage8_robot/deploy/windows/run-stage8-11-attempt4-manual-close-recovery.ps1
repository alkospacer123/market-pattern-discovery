param(
    [Parameter(Mandatory=$true)][string]$RuntimeRoot,
    [Parameter(Mandatory=$true)][ValidatePattern('^[0-9a-f]{40}$')][string]$AcceptedRecoveryCommit,
    [string]$Python = "py.exe"
)
$ErrorActionPreference = "Stop"
$taskName = "TradingSystemLab-Stage8-Readonly"
$productionId = "PROD_STAGE7_46DB784378797C7FB04636892350AFF21006D71A31F2CED9D4B974EDA2DC36B8"
$evidenceSha = "F0EADA84724509A197BE7F851B2530535DAA7B1A8EC062D8943CCB905C5BA2EF"
$repo = (Resolve-Path (Join-Path $PSScriptRoot "..\..\..\..")).Path
$runtime = [IO.Path]::GetFullPath($RuntimeRoot)
$physicalEvidence = Join-Path $runtime "diagnostics\stage8_11_physical_acceptance_attempt4.json"
$recoveryEvidence = Join-Path $runtime "diagnostics\stage8_11_attempt4_manual_close_recovery.json"
$readonly = $null
$locationPushed = $false

try {
    $head = (& git -C $repo rev-parse HEAD).Trim()
    if ($LASTEXITCODE -ne 0 -or $head -cne $AcceptedRecoveryCommit) { throw "STAGE8_11_ATTEMPT4_RECOVERY_HEAD_MISMATCH" }
    $dirty = @(& git -C $repo status --porcelain)
    if ($LASTEXITCODE -ne 0 -or $dirty.Count -ne 0) { throw "STAGE8_11_ATTEMPT4_RECOVERY_WORKTREE_NOT_CLEAN" }
    if (-not (Test-Path -LiteralPath $physicalEvidence -PathType Leaf)) { throw "STAGE8_11_ATTEMPT4_EVIDENCE_MISSING" }
    if ((Get-FileHash -LiteralPath $physicalEvidence -Algorithm SHA256).Hash -cne $evidenceSha) { throw "STAGE8_11_ATTEMPT4_EVIDENCE_HASH_MISMATCH" }
    $task = Get-ScheduledTask -TaskName $taskName -ErrorAction SilentlyContinue
    if (-not $task -or $task.State -ne "Disabled") { throw "STAGE8_11_ATTEMPT4_RECOVERY_TASK_NOT_DISABLED" }
    $conflicts = @(Get-CimInstance Win32_Process | Where-Object {
        $_.ProcessId -ne $PID -and $_.CommandLine -and
        ($_.CommandLine -match "readonly_supervisor|stage8_robot\.runner|stage8_11_physical_acceptance|stage8_11_attempt4_manual_close_recovery")
    })
    if ($conflicts.Count -ne 0) { throw "STAGE8_11_ATTEMPT4_RECOVERY_RUNTIME_OWNER_CONFLICT" }
    Push-Location $repo
    $locationPushed = $true
    & $Python -c "from TradingSystemLab.stage8_robot.trading_safety_gate import load_kill_switch; from TradingSystemLab.stage8_robot.specification import PRODUCTION_SPECIFICATION_ID as P; s,e=load_kill_switch(r'''$runtime'''); assert e is None and s['production_specification_id']==P and s['state']=='HALTED'"
    if ($LASTEXITCODE -ne 0) { throw "STAGE8_11_ATTEMPT4_RECOVERY_KILL_SWITCH_NOT_HALTED" }
    & $Python -c "import sys; assert sys.prefix != sys.base_prefix, 'VENV_REQUIRED'"
    if ($LASTEXITCODE -ne 0) { throw "STAGE8_11_ATTEMPT4_RECOVERY_VENV_REQUIRED" }
    . (Join-Path $PSScriptRoot "credential-store.ps1")
    $readonly = Get-ReadonlyCredential $runtime $productionId
    $env:STAGE8_11_RECOVERY_READONLY_SECRET = [string]$readonly.finam_api_secret
    $env:STAGE8_11_RECOVERY_ACCOUNT_ID = [string]$readonly.finam_real_account_id
    & $Python -m TradingSystemLab.stage8_robot.stage8_11_attempt4_manual_close_recovery --runtime-root $runtime --accepted-recovery-commit $AcceptedRecoveryCommit
    if ($LASTEXITCODE -ne 0) { throw "STAGE8_11_ATTEMPT4_MANUAL_CLOSE_RECOVERY_FAILED" }
    if (-not (Test-Path -LiteralPath $recoveryEvidence -PathType Leaf)) { throw "STAGE8_11_ATTEMPT4_RECOVERY_EVIDENCE_MISSING" }
    Write-Output "=== ATTEMPT4_MANUAL_CLOSE_RECOVERY_EVIDENCE_BEGIN ==="
    Get-Content -LiteralPath $recoveryEvidence -Raw
    Write-Output "=== ATTEMPT4_MANUAL_CLOSE_RECOVERY_EVIDENCE_END ==="
    Write-Output ("ATTEMPT4_MANUAL_CLOSE_RECOVERY_EVIDENCE_SHA256=" + (Get-FileHash -LiteralPath $recoveryEvidence -Algorithm SHA256).Hash)
} finally {
    if ($locationPushed) { Pop-Location; $locationPushed = $false }
    Remove-Item Env:STAGE8_11_RECOVERY_READONLY_SECRET -ErrorAction SilentlyContinue
    Remove-Item Env:STAGE8_11_RECOVERY_ACCOUNT_ID -ErrorAction SilentlyContinue
    $readonly = $null
    try { Disable-ScheduledTask -TaskName $taskName -ErrorAction SilentlyContinue | Out-Null } catch {}
}
