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
    # WindowsIdentity.Groups omits deny-only groups; inspect full TOKEN_GROUPS.
    if (-not ('CC03TokenGroups' -as [type])) {
        Add-Type -TypeDefinition @'
using System;
using System.Runtime.InteropServices;
using System.Security.Principal;
public static class CC03TokenGroups {
    [StructLayout(LayoutKind.Sequential)] struct SidAndAttributes { public IntPtr Sid; public uint Attributes; }
    [DllImport("advapi32.dll",SetLastError=true)] static extern bool GetTokenInformation(IntPtr token,int kind,IntPtr data,int length,out int needed);
    public static string[] All(WindowsIdentity identity) {
        int needed;
        GetTokenInformation(identity.Token,2,IntPtr.Zero,0,out needed);
        if(needed<=0 || needed>1048576) throw new Exception("TOKEN_GROUPS_UNAVAILABLE");
        IntPtr data=Marshal.AllocHGlobal(needed);
        try {
            if(!GetTokenInformation(identity.Token,2,data,needed,out needed)) throw new Exception("TOKEN_GROUPS_UNAVAILABLE");
            int count=Marshal.ReadInt32(data), offset=IntPtr.Size==8 ? 8 : 4, size=Marshal.SizeOf(typeof(SidAndAttributes));
            if(count<0 || count>1024 || offset+count*size>needed) throw new Exception("TOKEN_GROUPS_INVALID");
            var result=new string[count];
            for(int i=0;i<count;i++) {
                var entry=(SidAndAttributes)Marshal.PtrToStructure(IntPtr.Add(data,offset+i*size),typeof(SidAndAttributes));
                result[i]=new SecurityIdentifier(entry.Sid).Value;
            }
            return result;
        } finally { Marshal.FreeHGlobal(data); }
    }
}
'@
    }
    return ($Identity.User.Value -match '^S-1-5-21-') -and
        (-not (@([CC03TokenGroups]::All($Identity) |
            Where-Object { $_ -in $script:CCPrivilegedGroups }).Count)) -and
        ($Identity.ImpersonationLevel -eq [Security.Principal.TokenImpersonationLevel]::None)
}
