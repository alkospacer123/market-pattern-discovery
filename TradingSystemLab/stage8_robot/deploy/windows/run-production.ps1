param(
    [Parameter(Mandatory=$true)][string]$Checkout,
    [Parameter(Mandatory=$true)][string]$RuntimeRoot,
    [Parameter(Mandatory=$true)][string]$Stage5DataRoot,
    [Parameter(Mandatory=$true)][string]$ExpectedCommit,
    [string]$Python = "py.exe",
    [int]$PollSeconds = 30,
    [switch]$Once
)
$ErrorActionPreference = "Stop"
$expectedStage5Commit = "50f1fd2178c18b7ab3bd969be82ad01f47a34745"
$env:FINAM_MODE = "STAGE8_12_PRODUCTION"
$env:ROBOT_AUDIT_LOG = Join-Path $RuntimeRoot "audit\stage8-production.jsonl"

Set-Location $Checkout
$commit = (& git -C $Checkout rev-parse HEAD).Trim()
if ($LASTEXITCODE -ne 0 -or $commit -notmatch '^[0-9a-f]{40}$') {
    throw "STAGE8_12_4_PRODUCTION_COMMIT_UNAVAILABLE"
}
if ($ExpectedCommit -notmatch '^[0-9a-f]{40}$' -or $commit -cne $ExpectedCommit) {
    throw "STAGE8_12_4_PRODUCTION_COMMIT_MISMATCH"
}
$dirty = & git -C $Checkout status --porcelain
if ($LASTEXITCODE -ne 0 -or $dirty) {
    throw "STAGE8_12_4_PRODUCTION_CHECKOUT_NOT_CLEAN"
}

$dataCommit = (& git -C $Stage5DataRoot rev-parse HEAD).Trim()
if ($LASTEXITCODE -ne 0 -or $dataCommit -cne $expectedStage5Commit) {
    throw "STAGE8_12_4_STAGE5_DATA_COMMIT_MISMATCH"
}
$dataDirty = & git -C $Stage5DataRoot status --porcelain
if ($LASTEXITCODE -ne 0 -or $dataDirty) {
    throw "STAGE8_12_4_STAGE5_DATA_CHECKOUT_NOT_CLEAN"
}

$productionId = (& $Python -c "from TradingSystemLab.stage8_robot.specification import PRODUCTION_SPECIFICATION_ID,load_frozen_specification; s=load_frozen_specification(); assert s.production_id == PRODUCTION_SPECIFICATION_ID; print(PRODUCTION_SPECIFICATION_ID)")
if ($LASTEXITCODE -ne 0 -or [string]::IsNullOrWhiteSpace($productionId)) {
    throw "TRADING_DPAPI_PRODUCTION_AUTHORITY_UNAVAILABLE"
}

. (Join-Path $PSScriptRoot "trading-credential-store.ps1")
$credential = $null
try {
    $credential = Get-TradingCredential $RuntimeRoot $productionId.Trim()
    $env:FINAM_API_SECRET = [string]$credential.finam_trading_api_secret
    $env:FINAM_REAL_ACCOUNT_ID = [string]$credential.finam_real_account_id
    if ([string]::IsNullOrWhiteSpace($env:FINAM_API_SECRET) -or
        [string]::IsNullOrWhiteSpace($env:FINAM_REAL_ACCOUNT_ID)) {
        throw "TRADING_DPAPI_CREDENTIAL_MISSING"
    }

    $args = @(
        "-m", "TradingSystemLab.stage8_robot.production_service",
        "--runtime-root", $RuntimeRoot,
        "--stage5-data-root", $Stage5DataRoot,
        "--accepted-commit", $ExpectedCommit,
        "--poll-seconds", [string]$PollSeconds
    )
    if ($Once) { $args += "--once" }
    & $Python @args
    exit $LASTEXITCODE
} finally {
    $credential = $null
    Remove-Item Env:FINAM_API_SECRET -ErrorAction SilentlyContinue
    Remove-Item Env:FINAM_REAL_ACCOUNT_ID -ErrorAction SilentlyContinue
}
