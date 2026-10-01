# Reusable CurrentUser DPAPI credential-store functions.  This file must never
# contain credentials or write decrypted material to disk.
try {
    $null = Add-Type -AssemblyName System.Security -ErrorAction Stop
} catch {
    throw "DPAPI_SYSTEM_SECURITY_UNAVAILABLE"
}

$script:ReadonlyCredentialSchema = 1
$script:ReadonlyCredentialMode = "REAL_READONLY"
$script:ReadonlyCredentialFile = "finam-real-readonly.dpapi"
$script:ReadonlyCredentialMetadataFile = "finam-real-readonly.metadata.json"
$script:ReadonlyCredentialEntropy = [Text.Encoding]::UTF8.GetBytes("TradingSystemLab.Stage8.RealReadonly.v1")

function Assert-WindowsCredentialHost {
    if ([Environment]::OSVersion.Platform -ne [PlatformID]::Win32NT) { throw "DPAPI_WINDOWS_REQUIRED" }
}

function Get-CurrentPrincipalInfo {
    Assert-WindowsCredentialHost
    $identity = [Security.Principal.WindowsIdentity]::GetCurrent()
    if (-not $identity.User) { throw "DPAPI_PRINCIPAL_UNAVAILABLE" }
    @{ Name = $identity.Name; Sid = $identity.User.Value }
}

function Get-SidSha256([Parameter(Mandatory=$true)][string]$Sid) {
    $sha = [Security.Cryptography.SHA256]::Create()
    try { ([BitConverter]::ToString($sha.ComputeHash([Text.Encoding]::UTF8.GetBytes($Sid)))).Replace("-", "").ToLowerInvariant() }
    finally { $sha.Dispose() }
}

function Protect-ReadonlyCredentialPayload([Parameter(Mandatory=$true)]$Payload) {
    Assert-WindowsCredentialHost
    $plain = $null
    try {
        $plain = [Text.Encoding]::UTF8.GetBytes(($Payload | ConvertTo-Json -Compress))
        [Security.Cryptography.ProtectedData]::Protect($plain, $script:ReadonlyCredentialEntropy,
            [Security.Cryptography.DataProtectionScope]::CurrentUser)
    } catch { throw "DPAPI_ENCRYPT_FAILED" }
    finally { if ($plain) { [Array]::Clear($plain, 0, $plain.Length) } }
}

function Assert-ReadonlyCredentialPayload([Parameter(Mandatory=$true)]$Payload,
                                           [Parameter(Mandatory=$true)][string]$ExpectedProductionId) {
    if ($null -eq $Payload -or $Payload.schema_version -ne $script:ReadonlyCredentialSchema) { throw "DPAPI_PAYLOAD_INVALID" }
    if ($Payload.mode -ne $script:ReadonlyCredentialMode) { throw "DPAPI_MODE_INVALID" }
    if ($Payload.production_id -ne $ExpectedProductionId) { throw "DPAPI_PRODUCTION_ID_MISMATCH" }
    if ([string]::IsNullOrWhiteSpace([string]$Payload.finam_api_secret)) { throw "DPAPI_SECRET_MISSING" }
    if ([string]::IsNullOrWhiteSpace([string]$Payload.finam_real_account_id)) { throw "DPAPI_ACCOUNT_MISSING" }
}

function Unprotect-ReadonlyCredentialBytes([Parameter(Mandatory=$true)][byte[]]$Ciphertext,
                                           [Parameter(Mandatory=$true)][string]$ExpectedProductionId) {
    Assert-WindowsCredentialHost
    $plain = $null
    try {
        $plain = [Security.Cryptography.ProtectedData]::Unprotect($Ciphertext, $script:ReadonlyCredentialEntropy,
            [Security.Cryptography.DataProtectionScope]::CurrentUser)
        try { $payload = ([Text.Encoding]::UTF8.GetString($plain) | ConvertFrom-Json -ErrorAction Stop) }
        catch { throw "DPAPI_PAYLOAD_INVALID" }
        Assert-ReadonlyCredentialPayload $payload $ExpectedProductionId
        $payload
    } catch {
        if ($_.Exception.Message -match '^DPAPI_') { throw $_.Exception.Message }
        throw "DPAPI_DECRYPT_FAILED"
    } finally { if ($plain) { [Array]::Clear($plain, 0, $plain.Length) } }
}

function Get-ReadonlyCredential([Parameter(Mandatory=$true)][string]$RuntimeRoot,
                                [Parameter(Mandatory=$true)][string]$ExpectedProductionId) {
    $secrets = Join-Path $RuntimeRoot "secrets"
    $blob = Join-Path $secrets $script:ReadonlyCredentialFile
    $metadataPath = Join-Path $secrets $script:ReadonlyCredentialMetadataFile
    if (-not (Test-Path -LiteralPath $blob -PathType Leaf)) { throw "DPAPI_CREDENTIAL_FILE_MISSING" }
    if (-not (Test-Path -LiteralPath $metadataPath -PathType Leaf)) { throw "DPAPI_METADATA_MISSING" }
    try { $metadata = Get-Content -LiteralPath $metadataPath -Raw | ConvertFrom-Json -ErrorAction Stop }
    catch { throw "DPAPI_METADATA_INVALID" }
    $principal = Get-CurrentPrincipalInfo
    if ($metadata.scope -ne "CurrentUser") { throw "DPAPI_SCOPE_INVALID" }
    if ($metadata.schema_version -ne $script:ReadonlyCredentialSchema) { throw "DPAPI_METADATA_INVALID" }
    if ($metadata.production_id -ne $ExpectedProductionId) { throw "DPAPI_PRODUCTION_ID_MISMATCH" }
    if ($metadata.principal_sid_sha256 -ne (Get-SidSha256 $principal.Sid)) { throw "DPAPI_PRINCIPAL_MISMATCH" }
    try { $ciphertext = [IO.File]::ReadAllBytes($blob) } catch { throw "DPAPI_CREDENTIAL_FILE_UNREADABLE" }
    if (-not $ciphertext.Length) { throw "DPAPI_DECRYPT_FAILED" }
    Unprotect-ReadonlyCredentialBytes $ciphertext $ExpectedProductionId
}

function Set-PrivateCredentialAcl([Parameter(Mandatory=$true)][string]$Path,
                                  [Parameter(Mandatory=$true)][string]$Sid) {
    try {
        $sidObject = New-Object Security.Principal.SecurityIdentifier($Sid)
    } catch {
        throw "DPAPI_PRINCIPAL_INVALID"
    }
    try {
        $acl = New-Object Security.AccessControl.DirectorySecurity
        if (Test-Path -LiteralPath $Path -PathType Leaf) { $acl = New-Object Security.AccessControl.FileSecurity }
        $acl.SetAccessRuleProtection($true, $false)
        $rule = New-Object Security.AccessControl.FileSystemAccessRule($sidObject, "FullControl", "Allow")
        $acl.AddAccessRule($rule)
        Set-Acl -LiteralPath $Path -AclObject $acl
        $actual = Get-Acl -LiteralPath $Path
        $allowedSids = @($actual.Access | Where-Object {
            $_.AccessControlType -eq "Allow"
        } | ForEach-Object {
            try {
                $_.IdentityReference.Translate([Security.Principal.SecurityIdentifier]).Value
            } catch {
                $_.IdentityReference.Value
            }
        })
        if (-not $actual.AreAccessRulesProtected -or -not ($allowedSids -contains $Sid) -or
            ($allowedSids -contains "S-1-1-0") -or ($allowedSids -contains "S-1-5-32-545")) {
            throw "ACL"
        }
    } catch { throw "DPAPI_ACL_HARDENING_FAILED" }
}

function Set-ProcessReadonlyCredentials([Parameter(Mandatory=$true)]$Payload) {
    # Assignment to $env: affects only this PowerShell process and children.
    $env:FINAM_API_SECRET = [string]$Payload.finam_api_secret
    $env:FINAM_REAL_ACCOUNT_ID = [string]$Payload.finam_real_account_id
}
