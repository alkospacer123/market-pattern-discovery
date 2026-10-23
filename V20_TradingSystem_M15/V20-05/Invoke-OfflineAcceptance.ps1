# Manual FakeBroker acceptance only. Creates no Task and contacts no FINAM API.
[CmdletBinding()]
param(
    [Parameter(Mandatory=$true)][string]$Checkout,
    [string]$Python = "python",
    [string]$ScratchBase = "C:\V20Lab\acceptance",
    [string]$ReportPath = ""
)
$ErrorActionPreference = "Stop"
if ($env:OS -ne "Windows_NT") { throw "Native Windows required; Linux is NOT Windows acceptance" }
$osInfo = Get-CimInstance Win32_OperatingSystem
if ($osInfo.Caption -notmatch 'Windows Server 2022') {
    throw "Target is Intel Windows Server 2022; detected $($osInfo.Caption)"
}
$repo = (Resolve-Path -LiteralPath $Checkout).Path
if (!(Test-Path -LiteralPath (Join-Path $repo "V20_TradingSystem_M15\v20_runtime\m15_runner.py"))) {
    throw "Existing V20 checkout required"
}
$scratchPath = [IO.Path]::GetFullPath($ScratchBase)
if ($scratchPath.StartsWith($repo + '\', [StringComparison]::OrdinalIgnoreCase) -or $scratchPath -eq $repo) {
    throw "Scratch must be outside checkout"
}
if (!$ReportPath) { $ReportPath = Join-Path $scratchPath "WINDOWS_ACCEPTANCE_REPORT.json" }
Push-Location -LiteralPath $repo
try {
    & $Python -m V20_TradingSystem_M15.v20_runtime.offline_acceptance --offline --windows `
        --scratch-base $scratchPath --report $ReportPath
    if ($LASTEXITCODE -ne 0) { throw "Offline acceptance failed: exit $LASTEXITCODE" }
    $report = Get-Content -LiteralPath $ReportPath -Raw -Encoding UTF8 | ConvertFrom-Json
    if ($report.stages.'V20-05.5' -ne "PASS_NATIVE_WINDOWS") { throw "Windows acceptance not confirmed" }
    Write-Output "PASS FakeBroker on $($osInfo.Caption); report: $ReportPath"
} finally { Pop-Location }
