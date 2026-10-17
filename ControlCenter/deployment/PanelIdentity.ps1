# Read existing local ccpanel only. Never provision, enable, or change membership.
$script:CCPrivilegedGroups = @('S-1-5-32-544','S-1-5-32-547','S-1-5-32-548',
    'S-1-5-32-549','S-1-5-32-550','S-1-5-32-551','S-1-5-32-556',
    'S-1-5-32-578','S-1-5-32-580')
function Get-CCPanelState($PanelSid) {
    if ($null -eq $PanelSid) { return 'CCPANEL_NOT_PROVISIONED' }
    if ([string]$PanelSid -notmatch '^S-1-5-21-[0-9]+-[0-9]+-[0-9]+-[0-9]+$') { return 'CCPANEL_SID_MISMATCH' }
    try {
        $account = Get-LocalUser -Name 'ccpanel' -ErrorAction SilentlyContinue
        if ($null -eq $account) { return 'CCPANEL_NOT_PROVISIONED' }
        if ($account.SID.Value -ne $PanelSid) { return 'CCPANEL_SID_MISMATCH' }
        if (-not $account.Enabled) { return 'CCPANEL_DISABLED' }
        $groups = @(Get-LocalGroup -ErrorAction Stop)
        foreach ($groupSid in $script:CCPrivilegedGroups) {
            $group = $groups | Where-Object { $_.SID.Value -eq $groupSid }
            if ($null -ne $group) {
                $members = @(Get-LocalGroupMember -SID $groupSid -ErrorAction Stop)
                if (@($members | Where-Object { $_.SID.Value -eq $PanelSid }).Count) { return 'CCPANEL_PRIVILEGED' }
            }
        }
        return 'CCPANEL_ENABLED'
    } catch { return 'UNKNOWN' }
}

function Test-CCStandardIdentity($Identity) {
    return ($Identity.User.Value -match '^S-1-5-21-') -and
        (-not (@($Identity.Groups | ForEach-Object { $_.Value } |
            Where-Object { $_ -in $script:CCPrivilegedGroups }).Count)) -and
        ($Identity.ImpersonationLevel -eq [Security.Principal.TokenImpersonationLevel]::None)
}
