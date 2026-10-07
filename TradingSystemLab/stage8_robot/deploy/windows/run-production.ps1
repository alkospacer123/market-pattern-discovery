param(
  [Parameter(Mandatory=$true)][string]$Checkout,
  [Parameter(Mandatory=$true)][string]$RuntimeRoot,
  [Parameter(Mandatory=$true)][string]$DataRoot,
  [Parameter(Mandatory=$true)][string]$AcceptedCommit,
  [string]$Python = ""
)

$ErrorActionPreference = "Stop"
$expectedDataCommit = "50f1fd2178c18b7ab3bd969be82ad01f47a34745"
$productionId = "PROD_STAGE7_46DB784378797C7FB04636892350AFF21006D71A31F2CED9D4B974EDA2DC36B8"
$identity = "TRAIL1__N4_01__FULL__R15"

if ([string]::IsNullOrWhiteSpace($Python)) {
  $Python = Join-Path $RuntimeRoot "venv\Scripts\python.exe"
}
if (-not (Test-Path $Python -PathType Leaf)) { throw "PRODUCTION_PYTHON_VENV_MISSING" }

function Require-ExactCleanCheckout(
  [Parameter(Mandatory=$true)][string]$Path,
  [Parameter(Mandatory=$true)][string]$ExpectedCommit,
  [Parameter(Mandatory=$true)][string]$Code
) {
  if (-not (Test-Path $Path -PathType Container)) { throw ($Code + "_MISSING") }
  $head = (& git -C $Path rev-parse HEAD).Trim()
  if ($LASTEXITCODE -ne 0 -or $head -cne $ExpectedCommit) {
    throw ($Code + "_WRONG_COMMIT:" + $head)
  }
  $status = & git -C $Path status --porcelain
  if ($LASTEXITCODE -ne 0) { throw ($Code + "_GIT_STATUS_FAILED") }
  if ($status) { throw ($Code + "_NOT_CLEAN") }
}

Require-ExactCleanCheckout $Checkout $AcceptedCommit "PRODUCTION_CHECKOUT"
Require-ExactCleanCheckout $DataRoot $expectedDataCommit "PRODUCTION_DATA_CHECKOUT"

Set-Location $Checkout
. (Join-Path $PSScriptRoot "trading-credential-store.ps1")
$credential = Get-TradingCredential $RuntimeRoot $productionId

$env:FINAM_MODE = "STAGE8_12_4_FULL_R15_PRODUCTION"
$env:PRODUCTION_SPECIFICATION_ID = $productionId
$env:PRODUCTION_IDENTITY = $identity
$env:FINAM_API_SECRET = [string]$credential.finam_trading_api_secret
$env:FINAM_REAL_ACCOUNT_ID = [string]$credential.finam_real_account_id
$credential = $null

try {
  & $Python -m TradingSystemLab.stage8_robot.production_service `
    --runtime-root $RuntimeRoot `
    --data-root $DataRoot `
    --accepted-commit $AcceptedCommit
  exit $LASTEXITCODE
}
finally {
  Remove-Item Env:FINAM_API_SECRET -ErrorAction SilentlyContinue
  Remove-Item Env:FINAM_REAL_ACCOUNT_ID -ErrorAction SilentlyContinue
  Remove-Item Env:FINAM_MODE -ErrorAction SilentlyContinue
  Remove-Item Env:PRODUCTION_SPECIFICATION_ID -ErrorAction SilentlyContinue
  Remove-Item Env:PRODUCTION_IDENTITY -ErrorAction SilentlyContinue
}
