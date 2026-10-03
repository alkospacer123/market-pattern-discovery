param([Parameter(Mandatory=$true)][string]$RuntimeRoot,
      [string]$Python = "py.exe",
      [string]$ReportPath = "C:\TradingSystemLab\runtime\diagnostics\stage8_10_4_permission_boundary.json")
$ErrorActionPreference = "Stop"
. (Join-Path $PSScriptRoot "credential-store.ps1")
. (Join-Path $PSScriptRoot "trading-credential-store.ps1")
$readonlyCredential = $null
$tradingCredential = $null
$productionId = "PROD_STAGE7_46DB784378797C7FB04636892350AFF21006D71A31F2CED9D4B974EDA2DC36B8"
try {
    try { $readonlyCredential = Get-ReadonlyCredential $RuntimeRoot $productionId }
    catch { throw "PERMISSION_BOUNDARY_READONLY_CREDENTIAL_UNAVAILABLE" }
    try { $tradingCredential = Get-TradingCredential $RuntimeRoot $productionId }
    catch { throw "PERMISSION_BOUNDARY_TRADING_CREDENTIAL_UNAVAILABLE" }
    if ($readonlyCredential.production_id -cne $productionId -or $tradingCredential.production_id -cne $productionId) {
        throw "PERMISSION_BOUNDARY_PRODUCTION_ID_MISMATCH"
    }
    if ([string]$readonlyCredential.finam_real_account_id -cne [string]$tradingCredential.finam_real_account_id) {
        throw "PERMISSION_BOUNDARY_LOCAL_ACCOUNT_MISMATCH"
    }
    if ([string]::IsNullOrWhiteSpace([string]$readonlyCredential.finam_api_secret)) {
        throw "PERMISSION_BOUNDARY_READONLY_SECRET_MISSING"
    }
    if ([string]::IsNullOrWhiteSpace([string]$tradingCredential.finam_trading_api_secret)) {
        throw "PERMISSION_BOUNDARY_TRADING_SECRET_MISSING"
    }
    Write-Output "STAGE_8_10_4_LOCAL_ACCOUNT_BINDING_PASS"
    $env:FINAM_PERMISSION_READONLY_API_SECRET = [string]$readonlyCredential.finam_api_secret
    $env:FINAM_PERMISSION_TRADING_API_SECRET = [string]$tradingCredential.finam_trading_api_secret
    $env:FINAM_PERMISSION_ACCOUNT_ID = [string]$tradingCredential.finam_real_account_id
    $env:STAGE8_10_4_PERMISSION_BOUNDARY = "true"
    & $Python -m TradingSystemLab.stage8_robot.trading_permission_boundary --report $ReportPath
    if ($LASTEXITCODE -ne 0) { throw "PERMISSION_BOUNDARY_CHILD_DIAGNOSTIC_FAILED" }
} catch {
    $code = $_.Exception.Message
    if ($code -notmatch '^PERMISSION_BOUNDARY_') { $code = "PERMISSION_BOUNDARY_VALIDATION_FAILED" }
    Write-Error $code
    exit 1
} finally {
    Remove-Item Env:FINAM_PERMISSION_READONLY_API_SECRET -ErrorAction SilentlyContinue
    Remove-Item Env:FINAM_PERMISSION_TRADING_API_SECRET -ErrorAction SilentlyContinue
    Remove-Item Env:FINAM_PERMISSION_ACCOUNT_ID -ErrorAction SilentlyContinue
    Remove-Item Env:STAGE8_10_4_PERMISSION_BOUNDARY -ErrorAction SilentlyContinue
    $readonlyCredential = $null
    $tradingCredential = $null
}
