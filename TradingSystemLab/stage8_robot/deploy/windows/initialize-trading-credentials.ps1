param([Parameter(Mandatory=$true)][string]$RuntimeRoot,
      [string]$Python = "py.exe")
$ErrorActionPreference = "Stop"
. (Join-Path $PSScriptRoot "trading-credential-store.ps1")

function Convert-TradingSecureInput([Security.SecureString]$Value) {
    $ptr = [Runtime.InteropServices.Marshal]::SecureStringToBSTR($Value)
    try { [Runtime.InteropServices.Marshal]::PtrToStringBSTR($ptr) }
    finally { [Runtime.InteropServices.Marshal]::ZeroFreeBSTR($ptr) }
}

$secret = $account = $payload = $selfTest = $ciphertext = $null
try {
    $productionId = (& $Python -c "from TradingSystemLab.stage8_robot.specification import PRODUCTION_SPECIFICATION_ID,load_frozen_specification; s=load_frozen_specification(); assert s.production_id == PRODUCTION_SPECIFICATION_ID; print(PRODUCTION_SPECIFICATION_ID)")
    if ($LASTEXITCODE -ne 0 -or [string]::IsNullOrWhiteSpace($productionId)) { throw "TRADING_DPAPI_PRODUCTION_AUTHORITY_UNAVAILABLE" }
    $secretSecure = Read-Host "Future FINAM trading token (does not authorize trading)" -AsSecureString
    $accountSecure = Read-Host "Expected real account ID (not remotely validated)" -AsSecureString
    $secret = Convert-TradingSecureInput $secretSecure
    $account = Convert-TradingSecureInput $accountSecure
    if ([string]::IsNullOrWhiteSpace($secret)) { throw "TRADING_DPAPI_SECRET_MISSING" }
    if ([string]::IsNullOrWhiteSpace($account)) { throw "TRADING_DPAPI_ACCOUNT_MISSING" }
    $productionId = $productionId.Trim(); $principal = Get-TradingPrincipal
    $payload = [ordered]@{ schema_version=1; mode=$script:TradingCredentialMode; production_id=$productionId; finam_trading_api_secret=$secret; finam_real_account_id=$account }
    $ciphertext = Protect-TradingPayload $payload
    $secrets = Join-Path $RuntimeRoot "secrets"; New-Item -ItemType Directory -Force -Path $secrets | Out-Null
    Set-TradingPrivateAcl $secrets $principal.Sid
    $blob = Join-Path $secrets $script:TradingCredentialFile; $blobTemp = "$blob.$([Guid]::NewGuid().ToString('N')).tmp"
    [IO.File]::WriteAllBytes($blobTemp, $ciphertext); Set-TradingPrivateAcl $blobTemp $principal.Sid
    Move-Item -Force -LiteralPath $blobTemp -Destination $blob
    $metadata = [ordered]@{ schema_version=1; mode=$script:TradingCredentialMode; scope="CurrentUser"; creation_utc=[DateTime]::UtcNow.ToString("o"); production_id=$productionId; principal_sid_sha256=(Get-TradingSidHash $principal.Sid) }
    $metadataPath = Join-Path $secrets $script:TradingCredentialMetadataFile; $metadataTemp = "$metadataPath.$([Guid]::NewGuid().ToString('N')).tmp"
    [IO.File]::WriteAllText($metadataTemp, ($metadata | ConvertTo-Json -Compress), (New-Object Text.UTF8Encoding($false)))
    Set-TradingPrivateAcl $metadataTemp $principal.Sid; Move-Item -Force -LiteralPath $metadataTemp -Destination $metadataPath
    Set-TradingPrivateAcl $blob $principal.Sid; Set-TradingPrivateAcl $metadataPath $principal.Sid
    $selfTest = Get-TradingCredential $RuntimeRoot $productionId
    if ($selfTest.finam_trading_api_secret -cne $secret -or $selfTest.finam_real_account_id -cne $account) { throw "TRADING_DPAPI_SELF_TEST_FAILED" }
    Write-Output "TRADING_DPAPI_CREDENTIAL_BOOTSTRAP_PASS`nscope=CurrentUser`nprincipal_match=true`nproduction_match=true`nmode_match=true`nsecret_present=true`naccount_present=true"
} catch {
    $code = $_.Exception.Message; if ($code -notmatch '^TRADING_DPAPI_') { $code = "TRADING_DPAPI_BOOTSTRAP_FAILED" }; Write-Error $code
} finally {
    $secret = $account = $payload = $selfTest = $null
    if ($secretSecure) { $secretSecure.Dispose() }; if ($accountSecure) { $accountSecure.Dispose() }
    if ($ciphertext) { [Array]::Clear($ciphertext, 0, $ciphertext.Length) }
}
