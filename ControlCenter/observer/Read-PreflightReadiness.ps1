# Only own CC directory attributes and exact existing SID translation. No H1 paths.
Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'
$ProgressPreference = 'SilentlyContinue'
$stage = 'INPUT'
try {
    $p = [Console]::In.ReadToEnd() | ConvertFrom-Json
    . (Join-Path $PSScriptRoot '..\deployment\PanelIdentity.ps1')
    $stage = 'TOKEN'
    $identity = [Security.Principal.WindowsIdentity]::GetCurrent()
    # Deny even a filtered administrator token, including deny-only Administrators SID.
    $standard = Test-CCStandardIdentity $identity
    $stage = 'SIDS'
    $identities = Get-CCPanelState $p.cc_panel_sid
    $stage = 'ROOTS'
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
    $stage = 'SERIALIZE'
    @{observer_standard=$standard; identities=$identities; directories=$directories} | ConvertTo-Json -Compress
} catch { [Console]::Error.Write('READINESS_' + $stage + '_' + $_.Exception.GetType().Name); [Console]::Out.Write('{}'); exit 1 }
