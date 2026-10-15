# Shared validation only. No broker, H1 Task, authorization or ACL mutations.
Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'
$script:AppRoot = 'C:\TSLControlCenterApp'
$script:VenvRoot = 'C:\TSLControlCenterVenv'
$script:DataRoot = 'C:\TSLControlCenterData'
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

function Assert-ACL([string]$Path, [string]$PanelSid, [string]$ExporterSid, [string]$Kind) {
    Assert-PlainPath $Path
    if ($PanelSid -eq $ExporterSid -or $PanelSid -notmatch '^S-1-5-21-' -or $ExporterSid -notmatch '^S-1-5-21-') { throw 'DISTINCT_LOW_PRIVILEGE_SIDS_REQUIRED' }
    $acl = Get-Acl -LiteralPath $Path
    if (-not $acl.AreAccessRulesProtected) { throw 'ACL_INHERITANCE_MUST_BE_DISABLED' }
    $owner = $acl.GetOwner([Security.Principal.SecurityIdentifier]).Value
    if ($owner -notin @('S-1-5-18','S-1-5-32-544')) { throw 'TRUSTED_OWNER_REQUIRED' }
    $allowed = @('S-1-5-18','S-1-5-32-544',$PanelSid,$ExporterSid)
    $panelRead = $false; $exporterRead = $false
    $mutation = [Security.AccessControl.FileSystemRights]::Write -bor [Security.AccessControl.FileSystemRights]::Delete -bor [Security.AccessControl.FileSystemRights]::ChangePermissions -bor [Security.AccessControl.FileSystemRights]::TakeOwnership -bor [Security.AccessControl.FileSystemRights]::DeleteSubdirectoriesAndFiles
    foreach ($rule in $acl.GetAccessRules($true,$true,[Security.Principal.SecurityIdentifier])) {
        $sid = $rule.IdentityReference.Value
        if ($rule.IsInherited -or $sid -notin $allowed -or $rule.AccessControlType -ne 'Allow') { throw 'UNREVIEWED_ACL_RULE' }
        if ($sid -in @($PanelSid,$ExporterSid)) {
            $maxRights = [Security.AccessControl.FileSystemRights]::ReadAndExecute -bor [Security.AccessControl.FileSystemRights]::Synchronize
            if (($sid -eq $PanelSid -and $Kind -eq 'logs') -or ($sid -eq $ExporterSid -and $Kind -eq 'export')) {
                $maxRights = [Security.AccessControl.FileSystemRights]::Modify -bor [Security.AccessControl.FileSystemRights]::Synchronize
            }
            if ([int64]$rule.FileSystemRights -band (-bnot [int64]$maxRights)) { throw 'EXCESS_CUSTOM_SID_RIGHTS' }
        }
        if ($sid -eq $PanelSid) {
            if ($Kind -eq 'private' -or ($Kind -ne 'logs' -and ($rule.FileSystemRights -band $mutation))) { throw 'PANEL_EXCESS_PERMISSION' }
            $requiredRights = [Security.AccessControl.FileSystemRights]::ReadAndExecute
            if ($Kind -eq 'logs') { $requiredRights = [Security.AccessControl.FileSystemRights]::Modify }
            if (($rule.FileSystemRights -band $requiredRights) -eq $requiredRights) { $panelRead = $true }
        }
        if ($sid -eq $ExporterSid) {
            if ($Kind -ne 'export' -and ($rule.FileSystemRights -band $mutation)) { throw 'EXPORTER_EXCESS_PERMISSION' }
            $requiredRights = [Security.AccessControl.FileSystemRights]::ReadAndExecute
            if ($Kind -eq 'export') { $requiredRights = [Security.AccessControl.FileSystemRights]::Modify }
            if (($rule.FileSystemRights -band $requiredRights) -eq $requiredRights) { $exporterRead = $true }
        }
    }
    if ($Kind -ne 'private' -and -not $panelRead) { throw 'PANEL_READ_RULE_REQUIRED' }
    if ($Kind -ne 'logs' -and -not $exporterRead) { throw 'EXPORTER_READ_RULE_REQUIRED' }
}

function Assert-LayoutACL([string]$PanelSid, [string]$ExporterSid) {
    foreach ($pair in @(@($script:AppRoot,'app'), @($script:VenvRoot,'venv'),
                        @($script:DataRoot,'parent'), @("$script:DataRoot\export",'export'),
                        @("$script:DataRoot\logs",'logs'), @("$script:DataRoot\private",'private'))) {
        Assert-ACL $pair[0] $PanelSid $ExporterSid $pair[1]
    }
}

function Assert-CurrentIdentity([string]$ExpectedSid) {
    $identity = [Security.Principal.WindowsIdentity]::GetCurrent()
    if ($identity.User.Value -ne $ExpectedSid) { throw 'DEDICATED_IDENTITY_REQUIRED' }
    if (@($identity.Groups | Where-Object { $_.Value -eq 'S-1-5-32-544' }).Count -ne 0) { throw 'NON_ADMINISTRATOR_REQUIRED' }
}
