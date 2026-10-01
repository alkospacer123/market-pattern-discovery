param([Parameter(Mandatory=$true)][string]$RuntimeRoot,
      [string]$Python = "py.exe")
$ErrorActionPreference = "Stop"
. (Join-Path $PSScriptRoot "credential-store.ps1")

function Convert-SecureInput([Security.SecureString]$Value) {
    $ptr = [Runtime.InteropServices.Marshal]::SecureStringToBSTR($Value)
    try { [Runtime.InteropServices.Marshal]::PtrToStringBSTR($ptr) }
    finally { [Runtime.InteropServices.Marshal]::ZeroFreeBSTR($ptr) }
}

$secret = $account = $payload = $selfTest = $null
try {
    Assert-WindowsCredentialHost
    $productionId = (& $Python -c "from TradingSystemLab.stage8_robot.specification import PRODUCTION_SPECIFICATION_ID,load_frozen_specification; s=load_frozen_specification(); assert s.production_id == PRODUCTION_SPECIFICATION_ID; print(PRODUCTION_SPECIFICATION_ID)")
    if ($LASTEXITCODE -ne 0 -or [string]::IsNullOrWhiteSpace($productionId)) { throw "DPAPI_PRODUCTION_AUTHORITY_UNAVAILABLE" }
    $secretSecure = Read-Host "FINAM read-only API token" -AsSecureString
    $accountSecure = Read-Host "FINAM real account ID" -AsSecureString
    $secret = Convert-SecureInput $secretSecure; $account = Convert-SecureInput $accountSecure
    if ([string]::IsNullOrWhiteSpace($secret)) { throw "DPAPI_SECRET_MISSING" }
    if ([string]::IsNullOrWhiteSpace($account)) { throw "DPAPI_ACCOUNT_MISSING" }
    $principal = Get-CurrentPrincipalInfo
    $payload = [ordered]@{ schema_version=1; mode="REAL_READONLY"; production_id=$productionId.Trim(); finam_api_secret=$secret; finam_real_account_id=$account }
    $ciphertext = Protect-ReadonlyCredentialPayload $payload
    $secrets = Join-Path $RuntimeRoot "secrets"; New-Item -ItemType Directory -Force -Path $secrets | Out-Null
    Set-PrivateCredentialAcl $secrets $principal.Sid
    $blob = Join-Path $secrets $script:ReadonlyCredentialFile; $temp = "$blob.$([Guid]::NewGuid().ToString('N')).tmp"
    [IO.File]::WriteAllBytes($temp, $ciphertext); Set-PrivateCredentialAcl $temp $principal.Sid; Move-Item -Force -LiteralPath $temp -Destination $blob
    $metadata = [ordered]@{ schema_version=1; scope="CurrentUser"; creation_utc=[DateTime]::UtcNow.ToString("o"); production_id=$productionId.Trim(); principal_sid_sha256=(Get-SidSha256 $principal.Sid) }
    $metadataPath = Join-Path $secrets $script:ReadonlyCredentialMetadataFile; $metadataTemp = "$metadataPath.$([Guid]::NewGuid().ToString('N')).tmp"
    [IO.File]::WriteAllText($metadataTemp, ($metadata | ConvertTo-Json -Compress), (New-Object Text.UTF8Encoding($false)))
    Set-PrivateCredentialAcl $metadataTemp $principal.Sid; Move-Item -Force -LiteralPath $metadataTemp -Destination $metadataPath
    Set-PrivateCredentialAcl $blob $principal.Sid; Set-PrivateCredentialAcl $metadataPath $principal.Sid
    $selfTest = Get-ReadonlyCredential $RuntimeRoot $productionId.Trim()
    if ($selfTest.finam_api_secret -cne $secret -or $selfTest.finam_real_account_id -cne $account) { throw "DPAPI_SELF_TEST_FAILED" }
    Write-Output "DPAPI_CREDENTIAL_BOOTSTRAP_PASS`nscope=CurrentUser`nprincipal_match=true`nsecret_present=true`naccount_present=true"
} catch {
    $code = $_.Exception.Message; if ($code -notmatch '^DPAPI_') { $code = "DPAPI_BOOTSTRAP_FAILED" }; Write-Error $code
} finally {
    $secret = $account = $payload = $selfTest = $null
    if ($secretSecure) { $secretSecure.Dispose() }; if ($accountSecure) { $accountSecure.Dispose() }
    if ($ciphertext) { [Array]::Clear($ciphertext, 0, $ciphertext.Length) }
}
