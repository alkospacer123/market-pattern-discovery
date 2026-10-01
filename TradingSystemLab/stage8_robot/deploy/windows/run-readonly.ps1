param([string]$Checkout, [string]$RuntimeRoot, [string]$Python = "py.exe")
$ErrorActionPreference = "Stop"
$env:FINAM_MODE = "REAL_READONLY"
$env:NEW_ENTRIES_DISABLED = "true"
$env:ROBOT_STATE_PATH = Join-Path $RuntimeRoot "state\stage8.sqlite3"
$env:ROBOT_AUDIT_LOG = Join-Path $RuntimeRoot "audit\stage8.jsonl"
if (-not $env:FINAM_API_SECRET) { throw "FINAM_API_SECRET must be injected into this service account environment" }
if (-not $env:FINAM_REAL_ACCOUNT_ID) { throw "FINAM_REAL_ACCOUNT_ID must be injected into this service account environment" }
Set-Location $Checkout
& $Python "TradingSystemLab\stage8_robot\server_preflight.py" --state-directory (Join-Path $RuntimeRoot "state")
if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }
# This persistent target is structurally read-only. real_account_smoke remains a
# separate, manually invoked operator diagnostic.
& $Python -m TradingSystemLab.stage8_robot.readonly_supervisor --runtime-root $RuntimeRoot
exit $LASTEXITCODE
