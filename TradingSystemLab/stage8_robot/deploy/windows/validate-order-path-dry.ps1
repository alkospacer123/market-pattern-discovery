param(
    [Parameter(Mandatory=$true)][string]$OutputPath,
    [string]$Python = "python"
)
$ErrorActionPreference = "Stop"
$forbidden = @(
    "FINAM_API_SECRET", "FINAM_REAL_ACCOUNT_ID", "FINAM_TRADING_API_SECRET",
    "FINAM_TRADING_ACCOUNT_ID", "FINAM_PERMISSION_READONLY_API_SECRET",
    "FINAM_PERMISSION_TRADING_API_SECRET", "FINAM_PERMISSION_ACCOUNT_ID",
    "STAGE8_10_4_PERMISSION_BOUNDARY"
)
foreach ($name in $forbidden) {
    if ([Environment]::GetEnvironmentVariable($name)) {
        throw "STAGE_8_10_5_CREDENTIAL_ENVIRONMENT_NOT_EMPTY:$name"
    }
}
$env:STAGE8_10_5_ORDER_PATH_DRY = "true"
try {
    $repo = (Resolve-Path (Join-Path $PSScriptRoot "..\..\..\..")).Path
    Push-Location $repo
    try {
        & $Python -m TradingSystemLab.stage8_robot.order_path_dry_validation --output $OutputPath
        if ($LASTEXITCODE -ne 0) { throw "STAGE_8_10_5_DIAGNOSTIC_FAILED" }
    } finally {
        Pop-Location
    }
} finally {
    Remove-Item Env:STAGE8_10_5_ORDER_PATH_DRY -ErrorAction SilentlyContinue
}
