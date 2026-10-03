param([Parameter(Mandatory=$true)][string]$RuntimeRoot,
      [string]$Python = "py.exe",
      [string]$ReportPath = "C:\TradingSystemLab\runtime\diagnostics\stage8_10_3_identity_account_binding.json")
$ErrorActionPreference = "Stop"
. (Join-Path $PSScriptRoot "credential-store.ps1")
. (Join-Path $PSScriptRoot "trading-credential-store.ps1")
$readonlyCredential = $null
$tradingCredential = $null
try {
    $productionId = (& $Python -c "from TradingSystemLab.stage8_robot.specification import PRODUCTION_SPECIFICATION_ID; print(PRODUCTION_SPECIFICATION_ID)")
    if ($LASTEXITCODE -ne 0 -or [string]::IsNullOrWhiteSpace($productionId)) { throw "TRADING_IDENTITY_PRODUCTION_AUTHORITY_UNAVAILABLE" }
    $productionId = $productionId.Trim()
    try { $readonlyCredential = Get-ReadonlyCredential $RuntimeRoot $productionId }
    catch { throw "TRADING_IDENTITY_READONLY_CREDENTIAL_UNAVAILABLE" }
    try { $tradingCredential = Get-TradingCredential $RuntimeRoot $productionId }
    catch { throw "TRADING_IDENTITY_TRADING_CREDENTIAL_UNAVAILABLE" }
    if ($readonlyCredential.production_id -cne $productionId -or $tradingCredential.production_id -cne $productionId) {
        throw "TRADING_IDENTITY_PRODUCTION_ID_MISMATCH"
    }
    if ([string]$readonlyCredential.finam_real_account_id -cne [string]$tradingCredential.finam_real_account_id) {
        throw "TRADING_IDENTITY_LOCAL_ACCOUNT_MISMATCH"
    }
    Write-Output "STAGE_8_10_3_LOCAL_ACCOUNT_BINDING_PASS"
    $env:FINAM_TRADING_API_SECRET = [string]$tradingCredential.finam_trading_api_secret
    $env:FINAM_TRADING_ACCOUNT_ID = [string]$tradingCredential.finam_real_account_id
    $env:STAGE8_10_3_IDENTITY_BINDING = "true"
    & $Python -m TradingSystemLab.stage8_robot.trading_identity_binding --report $ReportPath
    if ($LASTEXITCODE -ne 0) { throw "TRADING_IDENTITY_CHILD_DIAGNOSTIC_FAILED" }
} catch {
    $code = $_.Exception.Message
    if ($code -notmatch '^TRADING_IDENTITY_') { $code = "TRADING_IDENTITY_VALIDATION_FAILED" }
    Write-Error $code
    exit 1
} finally {
    Remove-Item Env:FINAM_TRADING_API_SECRET -ErrorAction SilentlyContinue
    Remove-Item Env:FINAM_TRADING_ACCOUNT_ID -ErrorAction SilentlyContinue
    Remove-Item Env:STAGE8_10_3_IDENTITY_BINDING -ErrorAction SilentlyContinue
    $readonlyCredential = $null
    $tradingCredential = $null
}
