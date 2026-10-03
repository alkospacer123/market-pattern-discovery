# Isolated, local-only store for a future trading-capable credential. Possession
# of this credential does not authorize trading or any FINAM request.
if ([Environment]::OSVersion.Platform -ne [PlatformID]::Win32NT) { throw "TRADING_DPAPI_WINDOWS_REQUIRED" }
try { $null = Add-Type -AssemblyName System.Security -ErrorAction Stop }
catch { throw "TRADING_DPAPI_SYSTEM_SECURITY_UNAVAILABLE" }

$script:TradingCredentialSchema = 1
$script:TradingCredentialMode = "TRADING_CAPABLE_NOT_AUTHORIZED"
$script:TradingCredentialFile = "finam-trading-token.dpapi"
$script:TradingCredentialMetadataFile = "finam-trading-token.metadata.json"
$script:TradingCredentialEntropy = [Text.Encoding]::UTF8.GetBytes("TradingSystemLab.Stage8.TradingToken.v1")

function Get-TradingPrincipal {
    $identity = [Security.Principal.WindowsIdentity]::GetCurrent()
    if (-not $identity.User) { throw "TRADING_DPAPI_PRINCIPAL_UNAVAILABLE" }
    @{ Sid = $identity.User.Value }
}

function Get-TradingSidHash([Parameter(Mandatory=$true)][string]$Sid) {
    $sha = [Security.Cryptography.SHA256]::Create()
    try { ([BitConverter]::ToString($sha.ComputeHash([Text.Encoding]::UTF8.GetBytes($Sid)))).Replace("-", "").ToLowerInvariant() }
    finally { $sha.Dispose() }
}

function Assert-TradingPayload($Payload, [Parameter(Mandatory=$true)][string]$ExpectedProductionId) {
    if ($null -eq $Payload -or $Payload.schema_version -ne $script:TradingCredentialSchema) { throw "TRADING_DPAPI_SCHEMA_INVALID" }
    if ($Payload.mode -ne $script:TradingCredentialMode) { throw "TRADING_DPAPI_MODE_INVALID" }
    if ($Payload.production_id -cne $ExpectedProductionId) { throw "TRADING_DPAPI_PRODUCTION_ID_MISMATCH" }
    if ([string]::IsNullOrWhiteSpace([string]$Payload.finam_trading_api_secret)) { throw "TRADING_DPAPI_SECRET_MISSING" }
    if ([string]::IsNullOrWhiteSpace([string]$Payload.finam_real_account_id)) { throw "TRADING_DPAPI_ACCOUNT_MISSING" }
}

function Protect-TradingPayload([Parameter(Mandatory=$true)]$Payload) {
    $plain = $null
    try {
        $plain = [Text.Encoding]::UTF8.GetBytes(($Payload | ConvertTo-Json -Compress))
        [Security.Cryptography.ProtectedData]::Protect($plain, $script:TradingCredentialEntropy,
            [Security.Cryptography.DataProtectionScope]::CurrentUser)
    } catch { throw "TRADING_DPAPI_ENCRYPT_FAILED" }
    finally { if ($plain) { [Array]::Clear($plain, 0, $plain.Length) } }
}

function Unprotect-TradingBytes([Parameter(Mandatory=$true)][byte[]]$Ciphertext,
                                [Parameter(Mandatory=$true)][string]$ExpectedProductionId) {
    if (-not $Ciphertext.Length) { throw "TRADING_DPAPI_CIPHERTEXT_EMPTY" }
    $plain = $null
    try {
        $plain = [Security.Cryptography.ProtectedData]::Unprotect($Ciphertext, $script:TradingCredentialEntropy,
            [Security.Cryptography.DataProtectionScope]::CurrentUser)
        try { $payload = ([Text.Encoding]::UTF8.GetString($plain) | ConvertFrom-Json -ErrorAction Stop) }
        catch { throw "TRADING_DPAPI_PAYLOAD_MALFORMED" }
        Assert-TradingPayload $payload $ExpectedProductionId
        $payload
    } catch {
        if ($_.Exception.Message -match '^TRADING_DPAPI_') { throw $_.Exception.Message }
        throw "TRADING_DPAPI_DECRYPT_FAILED"
    } finally { if ($plain) { [Array]::Clear($plain, 0, $plain.Length) } }
}

function Set-TradingPrivateAcl([Parameter(Mandatory=$true)][string]$Path,
                               [Parameter(Mandatory=$true)][string]$Sid) {
    try {
        $sidObject = New-Object Security.Principal.SecurityIdentifier($Sid)
        $acl = if (Test-Path -LiteralPath $Path -PathType Leaf) {
            New-Object Security.AccessControl.FileSecurity
        } else { New-Object Security.AccessControl.DirectorySecurity }
        $acl.SetAccessRuleProtection($true, $false)
        $acl.AddAccessRule((New-Object Security.AccessControl.FileSystemAccessRule($sidObject, "FullControl", "Allow")))
        Set-Acl -LiteralPath $Path -AclObject $acl
        $actual = Get-Acl -LiteralPath $Path
        $allowed = @($actual.Access | Where-Object AccessControlType -eq "Allow" | ForEach-Object {
            try { $_.IdentityReference.Translate([Security.Principal.SecurityIdentifier]).Value }
            catch { $_.IdentityReference.Value }
        })
        if (-not $actual.AreAccessRulesProtected -or -not ($allowed -contains $Sid) -or
            ($allowed -contains "S-1-1-0") -or ($allowed -contains "S-1-5-32-545")) { throw "ACL" }
    } catch { throw "TRADING_DPAPI_ACL_HARDENING_FAILED" }
}

function Assert-TradingPrivateAcl([Parameter(Mandatory=$true)][string]$Path,
                                  [Parameter(Mandatory=$true)][string]$Sid) {
    try {
        $actual = Get-Acl -LiteralPath $Path
        $allowed = @($actual.Access | Where-Object AccessControlType -eq "Allow" | ForEach-Object {
            try { $_.IdentityReference.Translate([Security.Principal.SecurityIdentifier]).Value }
            catch { $_.IdentityReference.Value }
        })
        if (-not $actual.AreAccessRulesProtected -or -not ($allowed -contains $Sid) -or
            ($allowed -contains "S-1-1-0") -or ($allowed -contains "S-1-5-32-545")) { throw "ACL" }
    } catch { throw "TRADING_DPAPI_ACL_INVALID" }
}

function Get-TradingCredential([Parameter(Mandatory=$true)][string]$RuntimeRoot,
                               [Parameter(Mandatory=$true)][string]$ExpectedProductionId) {
    $secrets = Join-Path $RuntimeRoot "secrets"
    $blob = Join-Path $secrets $script:TradingCredentialFile
    $metadataPath = Join-Path $secrets $script:TradingCredentialMetadataFile
    if (-not (Test-Path -LiteralPath $blob -PathType Leaf)) { throw "TRADING_DPAPI_CREDENTIAL_MISSING" }
    if (-not (Test-Path -LiteralPath $metadataPath -PathType Leaf)) { throw "TRADING_DPAPI_METADATA_MISSING" }
    try { $metadata = Get-Content -LiteralPath $metadataPath -Raw | ConvertFrom-Json -ErrorAction Stop }
    catch { throw "TRADING_DPAPI_METADATA_INVALID" }
    $principal = Get-TradingPrincipal
    if ($metadata.schema_version -ne $script:TradingCredentialSchema -or
        $metadata.mode -ne $script:TradingCredentialMode) { throw "TRADING_DPAPI_METADATA_INVALID" }
    if ($metadata.scope -ne "CurrentUser") { throw "TRADING_DPAPI_SCOPE_INVALID" }
    if ($metadata.production_id -cne $ExpectedProductionId) { throw "TRADING_DPAPI_PRODUCTION_ID_MISMATCH" }
    if ($metadata.principal_sid_sha256 -cne (Get-TradingSidHash $principal.Sid)) { throw "TRADING_DPAPI_PRINCIPAL_MISMATCH" }
    Assert-TradingPrivateAcl $secrets $principal.Sid
    Assert-TradingPrivateAcl $blob $principal.Sid
    Assert-TradingPrivateAcl $metadataPath $principal.Sid
    try { $ciphertext = [IO.File]::ReadAllBytes($blob) } catch { throw "TRADING_DPAPI_CREDENTIAL_UNREADABLE" }
    Unprotect-TradingBytes $ciphertext $ExpectedProductionId
}
