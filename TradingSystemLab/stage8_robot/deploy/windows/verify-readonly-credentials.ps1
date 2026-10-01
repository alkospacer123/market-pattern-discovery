param([Parameter(Mandatory=$true)][string]$RuntimeRoot,
      [string]$Python = "py.exe")
$ErrorActionPreference = "Stop"
. (Join-Path $PSScriptRoot "credential-store.ps1")
try {
    $productionId = (& $Python -c "from TradingSystemLab.stage8_robot.specification import PRODUCTION_SPECIFICATION_ID,load_frozen_specification; s=load_frozen_specification(); assert s.production_id == PRODUCTION_SPECIFICATION_ID; print(PRODUCTION_SPECIFICATION_ID)")
    if ($LASTEXITCODE -ne 0 -or [string]::IsNullOrWhiteSpace($productionId)) { throw "DPAPI_PRODUCTION_AUTHORITY_UNAVAILABLE" }
    $payload = Get-ReadonlyCredential $RuntimeRoot $productionId.Trim()
    Write-Output "DPAPI_CREDENTIAL_STORE_PASS`nprincipal_match=true`nproduction_match=true`nsecret_present=true`naccount_present=true"
} catch {
    $code = $_.Exception.Message; if ($code -notmatch '^DPAPI_') { $code = "DPAPI_VERIFICATION_FAILED" }; Write-Error $code
} finally { $payload = $null }
