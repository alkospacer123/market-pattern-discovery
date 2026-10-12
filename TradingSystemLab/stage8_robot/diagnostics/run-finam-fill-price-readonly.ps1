param(
    [Parameter(Mandatory=$true)][string]$RuntimeRoot,
    [Parameter(Mandatory=$true)][ValidatePattern('^[0-9a-f]{40}$')][string]$ExpectedDiagnosticCommit,
    [Parameter(Mandatory=$true)][string]$LedgerCopy,
    [Parameter(Mandatory=$true)][ValidatePattern('^[0-9a-fA-F]{64}$')][string]$LedgerSha256,
    [Parameter(Mandatory=$true)][string]$IntentKey,
    [Parameter(Mandatory=$true)][string]$StartTime,
    [Parameter(Mandatory=$true)][string]$EndTime,
    [Parameter(Mandatory=$true)][string]$Output,
    [Parameter(Mandatory=$true)][string]$Python,
    [int]$Limit = 50,
    [string]$PreviousReport,
    [string]$PreviousSha256
)
$ErrorActionPreference = 'Stop'
$checkout = (Resolve-Path (Join-Path $PSScriptRoot '..\..\..')).Path
$runtime = [IO.Path]::GetFullPath($RuntimeRoot).TrimEnd('\')
$outputPath = [IO.Path]::GetFullPath($Output)
$copyPath = [IO.Path]::GetFullPath($LedgerCopy)
$credential = $null
$locationPushed = $false

try {
    # Diagnostic runs from an isolated checkout. Never update the LIVE checkout.
    if ($checkout.Equals($runtime, [StringComparison]::OrdinalIgnoreCase) -or
        $checkout.StartsWith($runtime+'\', [StringComparison]::OrdinalIgnoreCase)) { throw 'ISOLATED_DIAGNOSTIC_CHECKOUT_REQUIRED' }
    foreach ($path in @($outputPath, $copyPath)) {
        if ($path.Equals($runtime, [StringComparison]::OrdinalIgnoreCase) -or
            $path.StartsWith($runtime+'\', [StringComparison]::OrdinalIgnoreCase) -or
            $path.StartsWith($checkout+'\', [StringComparison]::OrdinalIgnoreCase)) { throw 'ISOLATED_DIAGNOSTIC_PATH_REQUIRED' }
    }
    if (Test-Path -LiteralPath $outputPath) { throw 'DIAGNOSTIC_OUTPUT_ALREADY_EXISTS' }
    if (-not (Test-Path -LiteralPath (Split-Path -Parent $outputPath) -PathType Container)) { throw 'EXISTING_SCRATCH_DIRECTORY_REQUIRED' }
    $head = (& git -C $checkout rev-parse HEAD).Trim()
    if ($LASTEXITCODE -ne 0 -or $head -cne $ExpectedDiagnosticCommit) { throw 'DIAGNOSTIC_HEAD_MISMATCH' }
    $dirty = @(& git -C $checkout status --porcelain)
    if ($LASTEXITCODE -ne 0 -or $dirty.Count -ne 0) { throw 'DIAGNOSTIC_CHECKOUT_NOT_CLEAN' }
    if ((Get-FileHash -LiteralPath $copyPath -Algorithm SHA256).Hash -ine $LedgerSha256) { throw 'LEDGER_COPY_HASH_MISMATCH' }
    Push-Location $checkout
    $locationPushed = $true
    & $Python -c "import sys; assert sys.prefix != sys.base_prefix, 'EXISTING_VENV_REQUIRED'"
    if ($LASTEXITCODE -ne 0) { throw 'EXISTING_VENV_REQUIRED' }
    # Reuse the existing read-only getter. No credential provisioning or ACL write.
    . (Join-Path $checkout 'TradingSystemLab\stage8_robot\deploy\windows\credential-store.ps1')
    $credential = Get-ReadonlyCredential $runtime 'PROD_STAGE7_46DB784378797C7FB04636892350AFF21006D71A31F2CED9D4B974EDA2DC36B8'
    $env:FINAM_FILL_READONLY_SECRET = [string]$credential.finam_api_secret
    $env:FINAM_FILL_READONLY_ACCOUNT = [string]$credential.finam_real_account_id
    $arguments = @('-m', 'TradingSystemLab.stage8_robot.finam_fill_price_readonly',
        '--ledger-copy', $copyPath, '--ledger-sha256', $LedgerSha256, '--intent-key', $IntentKey,
        '--start-time', $StartTime, '--end-time', $EndTime, '--limit', [string]$Limit, '--output', $outputPath)
    if ($PreviousReport) {
        if (-not $PreviousSha256) { throw 'PREVIOUS_REPORT_HASH_REQUIRED' }
        $arguments += @('--previous-report', $PreviousReport, '--previous-sha256', $PreviousSha256)
    }
    & $Python @arguments
    if ($LASTEXITCODE -ne 0) { throw 'READONLY_FILL_DIAGNOSTIC_BLOCKED' }
    Write-Output ('READONLY_DIAGNOSTIC_REPORT_SHA256='+(Get-FileHash -LiteralPath $outputPath -Algorithm SHA256).Hash)
} finally {
    if ($locationPushed) { Pop-Location }
    Remove-Item Env:FINAM_FILL_READONLY_SECRET -ErrorAction SilentlyContinue
    Remove-Item Env:FINAM_FILL_READONLY_ACCOUNT -ErrorAction SilentlyContinue
    $credential = $null
}
