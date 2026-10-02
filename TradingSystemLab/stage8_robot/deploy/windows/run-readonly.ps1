param([string]$Checkout, [string]$RuntimeRoot, [string]$Python = "py.exe")
$ErrorActionPreference = "Stop"
$env:FINAM_MODE = "REAL_READONLY"
$env:NEW_ENTRIES_DISABLED = "true"
$env:ROBOT_AUDIT_LOG = Join-Path $RuntimeRoot "audit\stage8.jsonl"
Set-Location $Checkout
$productionId = (& $Python -c "from TradingSystemLab.stage8_robot.specification import PRODUCTION_SPECIFICATION_ID,load_frozen_specification; s=load_frozen_specification(); assert s.production_id == PRODUCTION_SPECIFICATION_ID; print(PRODUCTION_SPECIFICATION_ID)")
if ($LASTEXITCODE -ne 0 -or [string]::IsNullOrWhiteSpace($productionId)) { throw "DPAPI_PRODUCTION_AUTHORITY_UNAVAILABLE" }
. (Join-Path $PSScriptRoot "credential-store.ps1")
$credential = Get-ReadonlyCredential $RuntimeRoot $productionId.Trim()
Set-ProcessReadonlyCredentials $credential
$credential = $null
& $Python "TradingSystemLab\stage8_robot\server_preflight.py" --state-directory (Join-Path $RuntimeRoot "state")
if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }
# This persistent target is structurally read-only. real_account_smoke remains a
# separate, manually invoked operator diagnostic.
& $Python -m TradingSystemLab.stage8_robot.readonly_supervisor --runtime-root $RuntimeRoot
exit $LASTEXITCODE
