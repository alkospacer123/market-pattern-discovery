param(
    [Parameter(Mandatory=$true)][string]$RuntimeRoot,
    [string]$Python = "py.exe"
)
$ErrorActionPreference = "Stop"
$productionId = "PROD_STAGE7_46DB784378797C7FB04636892350AFF21006D71A31F2CED9D4B974EDA2DC36B8"
$acceptedCommit = "069806355fc6931470d7f68d5ca6db20b06358fa"
$evidenceSha = "9FEFC5469F2C97F1EB36A5B5C99D323FA37BB948CF53C8A8745A27A06AB3B324"
$intent = "stage8.11:CNYRUBF:entry"
$taskName = "TradingSystemLab-Stage8-Readonly"
$repo = (Resolve-Path (Join-Path $PSScriptRoot "..\..\..\..")).Path
$runtime = [IO.Path]::GetFullPath($RuntimeRoot)
$physicalEvidence = Join-Path $runtime "diagnostics\stage8_11_physical_acceptance.json"

# This manual boundary is intentionally order-incapable: it loads only the
# CurrentUser REAL_READONLY credential, keeps the Scheduled Task disabled, and
# invokes no trading, cancellation, modification, arming, or authorization path.
try {
    $task = Get-ScheduledTask -TaskName $taskName -ErrorAction SilentlyContinue
    if ($task -and $task.State -ne "Disabled") { throw "STAGE8_11_SCHEDULED_TASK_NOT_DISABLED" }
    $conflicts = @(Get-CimInstance Win32_Process | Where-Object {
        $_.CommandLine -and ($_.CommandLine -match "readonly_supervisor|stage8_robot\.runner")
    })
    if ($conflicts.Count -ne 0) { throw "STAGE8_11_RUNTIME_OWNER_CONFLICT" }
    & $Python -c "import sys; assert sys.prefix != sys.base_prefix, 'VENV_REQUIRED'"
    if ($LASTEXITCODE -ne 0) { throw "STAGE8_11_VENV_REQUIRED" }
    . (Join-Path $PSScriptRoot "credential-store.ps1")
    $readonly = Get-ReadonlyCredential $runtime $productionId
    $env:STAGE8_11_READONLY_SECRET = [string]$readonly.finam_api_secret
    $env:STAGE8_11_READONLY_ACCOUNT_ID = [string]$readonly.finam_real_account_id
    Push-Location $repo
    & $Python -m TradingSystemLab.stage8_robot.stage8_11_failed_attempt_recovery `
        --runtime-root $runtime --account-id $env:STAGE8_11_READONLY_ACCOUNT_ID `
        --accepted-commit $acceptedCommit --physical-evidence $physicalEvidence `
        --physical-evidence-sha256 $evidenceSha --intent-key $intent
    if ($LASTEXITCODE -ne 0) { throw "STAGE8_11_RECOVERY_CHILD_FAILED" }
    Pop-Location
} finally {
    Remove-Item Env:STAGE8_11_READONLY_SECRET -ErrorAction SilentlyContinue
    Remove-Item Env:STAGE8_11_READONLY_ACCOUNT_ID -ErrorAction SilentlyContinue
    $readonly = $null
}
