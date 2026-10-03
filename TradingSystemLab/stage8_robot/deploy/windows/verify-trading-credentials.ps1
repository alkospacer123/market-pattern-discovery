param([Parameter(Mandatory=$true)][string]$RuntimeRoot,
      [string]$Python = "py.exe")
$ErrorActionPreference = "Stop"
. (Join-Path $PSScriptRoot "trading-credential-store.ps1")
try {
    $productionId = (& $Python -c "from TradingSystemLab.stage8_robot.specification import PRODUCTION_SPECIFICATION_ID,load_frozen_specification; s=load_frozen_specification(); assert s.production_id == PRODUCTION_SPECIFICATION_ID; print(PRODUCTION_SPECIFICATION_ID)")
    if ($LASTEXITCODE -ne 0 -or [string]::IsNullOrWhiteSpace($productionId)) { throw "TRADING_DPAPI_PRODUCTION_AUTHORITY_UNAVAILABLE" }
    $payload = Get-TradingCredential $RuntimeRoot $productionId.Trim()
    Write-Output "TRADING_DPAPI_CREDENTIAL_STORE_PASS`nprincipal_match=true`nproduction_match=true`nmode_match=true`nsecret_present=true`naccount_present=true"
} catch {
    $code = $_.Exception.Message; if ($code -notmatch '^TRADING_DPAPI_') { $code = "TRADING_DPAPI_VERIFICATION_FAILED" }; Write-Error $code
} finally { $payload = $null }
