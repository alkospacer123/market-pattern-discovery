# Shared validation only. No broker, H1 Task, authorization or ACL mutations.
Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'
# Operator-approved Intel-only project root. Never infer roots from the current
# working directory, production robot checkout, or external environment.
$script:ControlCenterRoot = 'C:\Control Center'
$script:AppRoot = Join-Path $script:ControlCenterRoot 'app'
$script:VenvRoot = Join-Path $script:ControlCenterRoot 'venv'
$script:DataRoot = Join-Path $script:ControlCenterRoot 'data'
$script:PackageRoot = Split-Path $PSScriptRoot -Parent

function Assert-PlainPath([string]$Path) {
    $full = [IO.Path]::GetFullPath($Path)
    if ($full -notmatch '^[A-Za-z]:\\' -or $full.Contains('..') -or $full.Substring(2).Contains(':')) { throw 'LOCAL_PATH_REQUIRED' }
    $current = [IO.DirectoryInfo]::new($full)
    while ($null -ne $current) {
        if (Test-Path -LiteralPath $current.FullName) {
            $item = Get-Item -Force -LiteralPath $current.FullName
            if ($item.Attributes -band [IO.FileAttributes]::ReparsePoint) { throw 'REPARSE_POINT_FORBIDDEN' }
        }
        $current = $current.Parent
    }
    $drive = [IO.DriveInfo]::new([IO.Path]::GetPathRoot($full))
    if ($drive.DriveType -ne 'Fixed' -or $drive.DriveFormat -ne 'NTFS') { throw 'LOCAL_NTFS_REQUIRED' }
}

# Rehearsal roots are opt-in and confined to this hosted VM's disposable temp.
# No installation script sets ACLs, provisions identities, or changes H1 paths.
if (-not [string]::IsNullOrWhiteSpace($env:CC03_CI_DISPOSABLE_ROOT)) {
    if ($env:GITHUB_ACTIONS -cne 'true' -or $env:RUNNER_ENVIRONMENT -cne 'github-hosted' -or [string]::IsNullOrWhiteSpace($env:RUNNER_TEMP)) { throw 'HOSTED_DISPOSABLE_REHEARSAL_REQUIRED' }
    $sandbox = [IO.Path]::GetFullPath($env:CC03_CI_DISPOSABLE_ROOT).TrimEnd('\')
    $temporary = [IO.Path]::GetFullPath($env:RUNNER_TEMP).TrimEnd('\') + '\'
    if (-not $sandbox.StartsWith($temporary, [StringComparison]::OrdinalIgnoreCase) -or (Split-Path $sandbox -Leaf) -notmatch '^CC03-[a-f0-9]{32}$') { throw 'DISPOSABLE_ROOT_OUTSIDE_RUNNER_TEMP' }
    Assert-PlainPath $sandbox
    $script:AppRoot = Join-Path $sandbox 'app'
    $script:VenvRoot = Join-Path $sandbox 'venv'
    $script:DataRoot = Join-Path $sandbox 'data'
}

function Get-Manifest([string]$Root, [switch]$AllowMissing) {
    Assert-PlainPath $Root
    $manifestPath = Join-Path $Root 'deployment\manifest.json'
    Assert-PlainPath $manifestPath
    $manifest = Get-Content -Raw -LiteralPath $manifestPath | ConvertFrom-Json
    if ($manifest.schema_id -ne 'cc03.package-manifest.v1') { throw 'MANIFEST_INVALID' }
    $seen = @{}
    foreach ($entry in $manifest.files) {
        if ($entry.path -notmatch '^[A-Za-z0-9_./-]+$' -or $entry.path.Contains('..') -or $entry.path.StartsWith('/') -or $seen.ContainsKey($entry.path)) { throw 'MANIFEST_PATH_INVALID' }
        $seen[$entry.path] = $true
        $file = Join-Path $Root $entry.path
        Assert-PlainPath $file
        if (-not (Test-Path -LiteralPath $file -PathType Leaf)) {
            if ($AllowMissing -and -not (Test-Path -LiteralPath $file)) { continue }
            throw 'MANIFEST_FILE_MISSING'
        }
        if ((Get-FileHash -LiteralPath $file -Algorithm SHA256).Hash.ToLowerInvariant() -ne $entry.sha256) { throw 'MANIFEST_HASH_MISMATCH' }
    }
    return $manifest
}

# Single operator-approved standard user. Private source policy remains admin-only.
# This validates existing ACLs; it never grants permissions or creates accounts.
function Assert-CCPanelSid([string]$PanelSid) {
    if ([string]::IsNullOrWhiteSpace($PanelSid) -or $PanelSid -notmatch '^S-1-5-21-[0-9]+-[0-9]+-[0-9]+-[0-9]+$') { throw 'VALID_CCPANEL_SID_REQUIRED' }
    if ([string]::IsNullOrWhiteSpace($env:CC03_CI_DISPOSABLE_ROOT)) {
        $account = Get-LocalUser -Name 'ccpanel' -ErrorAction SilentlyContinue
        if ($null -eq $account -or $account.SID.Value -ne $PanelSid -or -not $account.Enabled) { throw 'ENABLED_CCPANEL_ACCOUNT_REQUIRED' }
    }
}

function Assert-ACL([string]$Path, [string]$PanelSid, [string]$Kind) {
    Assert-CCPanelSid $PanelSid
    Assert-PlainPath $Path
    if ($Kind -notin @('app','venv','parent','export','logs','private')) { throw 'CC_KIND_INVALID' }
    $acl = Get-Acl -LiteralPath $Path
    if (-not $acl.AreAccessRulesProtected) { throw 'ACL_INHERITANCE_MUST_BE_DISABLED' }
    $owner = $acl.GetOwner([Security.Principal.SecurityIdentifier]).Value
    if ($owner -notin @('S-1-5-18','S-1-5-32-544')) { throw 'TRUSTED_OWNER_REQUIRED' }
    $allowed = @('S-1-5-18','S-1-5-32-544',$PanelSid)
    $panelRead = $false
    $mutation = [Security.AccessControl.FileSystemRights]::Write -bor [Security.AccessControl.FileSystemRights]::Delete -bor [Security.AccessControl.FileSystemRights]::ChangePermissions -bor [Security.AccessControl.FileSystemRights]::TakeOwnership -bor [Security.AccessControl.FileSystemRights]::DeleteSubdirectoriesAndFiles
    foreach ($rule in $acl.GetAccessRules($true,$true,[Security.Principal.SecurityIdentifier])) {
        $sid = $rule.IdentityReference.Value
        if ($rule.IsInherited -or $sid -notin $allowed -or $rule.AccessControlType -ne 'Allow') { throw 'UNREVIEWED_ACL_RULE' }
        if ($sid -eq $PanelSid) {
            if ($Kind -eq 'private') { throw 'CCPANEL_PRIVATE_ACCESS_FORBIDDEN' }
            $maxRights = [Security.AccessControl.FileSystemRights]::ReadAndExecute -bor [Security.AccessControl.FileSystemRights]::Synchronize
            if ($Kind -eq 'logs') {
                $maxRights = [Security.AccessControl.FileSystemRights]::Modify -bor [Security.AccessControl.FileSystemRights]::Synchronize
            }
            if ([int64]$rule.FileSystemRights -band (-bnot [int64]$maxRights)) { throw 'CCPANEL_EXCESS_PERMISSION' }
            if ($Kind -ne 'logs' -and ($rule.FileSystemRights -band $mutation)) { throw 'CCPANEL_WRITE_FORBIDDEN' }
            $requiredRights = [Security.AccessControl.FileSystemRights]::ReadAndExecute
            if ($Kind -eq 'logs') { $requiredRights = [Security.AccessControl.FileSystemRights]::Modify }
            if (($rule.FileSystemRights -band $requiredRights) -eq $requiredRights) { $panelRead = $true }
        }
    }
    if ($Kind -ne 'private' -and -not $panelRead) { throw 'CCPANEL_READ_RULE_REQUIRED' }
}

function Assert-LayoutACL([string]$PanelSid) {
    foreach ($pair in @(@($script:AppRoot,'app'), @($script:VenvRoot,'venv'),
                        @($script:DataRoot,'parent'), @("$script:DataRoot\export",'export'),
                        @("$script:DataRoot\logs",'logs'), @("$script:DataRoot\private",'private'))) {
        Assert-ACL $pair[0] $PanelSid $pair[1]
    }
}

function Assert-CurrentIdentity([string]$ExpectedSid) {
    Assert-CCPanelSid $ExpectedSid
    $identity = [Security.Principal.WindowsIdentity]::GetCurrent()
    if ($identity.User.Value -ne $ExpectedSid) { throw 'DEDICATED_IDENTITY_REQUIRED' }
    if (@($identity.Groups | Where-Object { $_.Value -eq 'S-1-5-32-544' }).Count -ne 0) { throw 'NON_ADMINISTRATOR_REQUIRED' }
}
