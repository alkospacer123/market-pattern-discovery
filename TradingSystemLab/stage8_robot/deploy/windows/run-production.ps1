param(
    [Parameter(Mandatory=$true)][string]$Checkout,
    [Parameter(Mandatory=$true)][string]$RuntimeRoot,
    [Parameter(Mandatory=$true)][string]$AcceptedCommit,
    [string]$Python = "py.exe"
)
$ErrorActionPreference = "Stop"
Set-Location $Checkout
$head = (git rev-parse HEAD).Trim()
if ($LASTEXITCODE -ne 0 -or $head -cne $AcceptedCommit) { throw "STAGE8_12_4_WRONG_PRODUCTION_COMMIT" }
$status = git status --porcelain
if ($LASTEXITCODE -ne 0 -or $status) { throw "STAGE8_12_4_PRODUCTION_REPOSITORY_NOT_CLEAN" }

$productionId = (& $Python -c "from TradingSystemLab.stage8_robot.specification import PRODUCTION_SPECIFICATION_ID,load_frozen_specification; s=load_frozen_specification(); assert s.production_id == PRODUCTION_SPECIFICATION_ID; print(PRODUCTION_SPECIFICATION_ID)")
if ($LASTEXITCODE -ne 0 -or [string]::IsNullOrWhiteSpace($productionId)) { throw "STAGE8_12_4_PRODUCTION_AUTHORITY_UNAVAILABLE" }

. (Join-Path $PSScriptRoot "trading-credential-store.ps1")
$credential = Get-TradingCredential $RuntimeRoot $productionId.Trim()
try {
    $env:FINAM_MODE = "STAGE8_12_4_REAL_PRODUCTION"
    $env:FINAM_API_SECRET = [string]$credential.finam_trading_api_secret
    $env:FINAM_REAL_ACCOUNT_ID = [string]$credential.finam_real_account_id
    if ([string]::IsNullOrWhiteSpace($env:FINAM_API_SECRET) -or [string]::IsNullOrWhiteSpace($env:FINAM_REAL_ACCOUNT_ID)) {
        throw "STAGE8_12_4_TRADING_CREDENTIAL_INVALID"
    }
    & $Python -m TradingSystemLab.stage8_robot.production_service `
        --runtime-root $RuntimeRoot `
        --accepted-commit $AcceptedCommit
    exit $LASTEXITCODE
} finally {
    Remove-Item Env:FINAM_API_SECRET -ErrorAction SilentlyContinue
    Remove-Item Env:FINAM_REAL_ACCOUNT_ID -ErrorAction SilentlyContinue
    Remove-Item Env:FINAM_MODE -ErrorAction SilentlyContinue
    $credential = $null
}
