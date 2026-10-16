# Only own CC directory attributes and exact existing SID translation. No H1 paths.
Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'
$ProgressPreference = 'SilentlyContinue'
try {
    $p = [Console]::In.ReadToEnd() | ConvertFrom-Json
    $identity = [Security.Principal.WindowsIdentity]::GetCurrent()
    # Deny even a filtered administrator token, including deny-only Administrators SID.
    $standard = ($identity.User.Value -match '^S-1-5-21-') -and
        (-not (@($identity.Groups | ForEach-Object { $_.Value }) -contains 'S-1-5-32-544'))
    $identities = 'EXISTING_SIDS_OBSERVED'
    foreach ($sid in @($p.cc_panel_sid, $p.cc_exporter_sid)) {
        if ($null -eq $sid) { $identities = 'CC_IDENTITIES_NOT_PROVISIONED'; continue }
        try { $null = ([Security.Principal.SecurityIdentifier]::new([string]$sid)).Translate([Security.Principal.NTAccount]) }
        catch [Security.Principal.IdentityNotMappedException] { $identities = 'CC_IDENTITIES_NOT_PROVISIONED' }
        catch { $identities = 'UNKNOWN' }
    }
    $directories = 'EXISTING_ROOTS_OBSERVED'
    foreach ($root in $p.roots) {
        try {
            # Inspect components in order, reject a junction before visiting a child.
            $parts = ([string]$root).Split('\')
            $current = $parts[0] + '\'
            foreach ($part in $parts[1..($parts.Length - 1)]) {
                $current = [IO.Path]::Combine($current, $part)
                $attributes = [IO.File]::GetAttributes($current)
                if (($attributes -band [IO.FileAttributes]::ReparsePoint) -or
                    -not ($attributes -band [IO.FileAttributes]::Directory)) { throw 'UNSAFE_ROOT' }
            }
        } catch [IO.DirectoryNotFoundException] { if ($directories -ne 'ACCESS_DENIED') { $directories = 'NOT_PROVISIONED' } }
          catch [IO.FileNotFoundException] { if ($directories -ne 'ACCESS_DENIED') { $directories = 'NOT_PROVISIONED' } }
          catch [UnauthorizedAccessException] { $directories = 'ACCESS_DENIED' }
          catch { $directories = 'UNKNOWN' }
    }
    @{observer_standard=$standard; identities=$identities; directories=$directories} | ConvertTo-Json -Compress
} catch { [Console]::Out.Write('{}'); exit 1 }
