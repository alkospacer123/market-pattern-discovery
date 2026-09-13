[CmdletBinding()]
param(
    [Parameter(Mandatory = $true)][string]$DataRoot,
    [Parameter(Mandatory = $true)][string]$OutputRoot,
    [string]$InstrumentConfigRoot = ""
)

$ErrorActionPreference = "Stop"
$RepoRoot = (Resolve-Path (Join-Path $PSScriptRoot "..\..")).Path
if ([string]::IsNullOrWhiteSpace($InstrumentConfigRoot)) {
    $InstrumentConfigRoot = Join-Path $RepoRoot "bbw_system\config\instruments"
}

Push-Location $RepoRoot
try {
    python -m bbw_system.data_cli freeze --data-root $DataRoot --output-root $OutputRoot --passport-root $InstrumentConfigRoot
    if ($LASTEXITCODE -ne 0) { throw "BBW data freeze failed with exit code $LASTEXITCODE" }
}
finally { Pop-Location }
