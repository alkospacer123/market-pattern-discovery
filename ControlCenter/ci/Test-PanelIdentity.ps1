# Test fixtures only; never called by a deployment or observer entrypoint.
Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'
if ($env:GITHUB_ACTIONS -cne 'true' -or $env:RUNNER_ENVIRONMENT -cne 'github-hosted' -or
    [string]::IsNullOrWhiteSpace($env:CC03_CI_DISPOSABLE_ROOT)) { throw 'HOSTED_DISPOSABLE_REQUIRED' }
. "$PSScriptRoot\..\deployment\Common.ps1"
if (Get-LocalUser -Name 'ccpanel' -ErrorAction SilentlyContinue) { throw 'FIXTURE_ACCOUNT_ALREADY_EXISTS' }
$created = $false
$checks = @()
function Check-State([string]$Sid, [string]$Expected) {
    $actual = Get-CCPanelState $Sid
    if ($actual -ne $Expected) { throw "PANEL_STATE expected=$Expected actual=$actual" }
    if ($Expected -ne 'CCPANEL_ENABLED') {
        $rejected = $false
        try { Assert-CCPanelSid $Sid } catch { $rejected = $true }
        if (-not $rejected) { throw 'INSTALL_ACCOUNT_NOT_REJECTED' }
    } else { Assert-CCPanelSid $Sid }
    $script:checks += $Expected
}
try {
    Check-State 'S-1-5-21-1-2-3-1234' 'CCPANEL_NOT_PROVISIONED'
    $password = ConvertTo-SecureString ('Cc03!aA9' + [guid]::NewGuid().ToString('N')) -AsPlainText -Force
    $user = New-LocalUser -Name 'ccpanel' -Password $password -AccountNeverExpires
    $created = $true
    Add-LocalGroupMember -SID 'S-1-5-32-545' -Member 'ccpanel'
    $sid = $user.SID.Value
    Check-State $sid 'CCPANEL_ENABLED'
    Check-State 'S-1-5-21-1-2-3-1234' 'CCPANEL_SID_MISMATCH'
    Disable-LocalUser -Name 'ccpanel'
    Check-State $sid 'CCPANEL_DISABLED'
    Enable-LocalUser -Name 'ccpanel'
    Add-LocalGroupMember -SID 'S-1-5-32-544' -Member 'ccpanel'
    Check-State $sid 'CCPANEL_PRIVILEGED'
    Remove-LocalGroupMember -SID 'S-1-5-32-544' -Member 'ccpanel'
    Check-State $sid 'CCPANEL_ENABLED'
    # A real restricted runner token retains Administrators as deny-only.
    # This exercises the filtered-admin rejection without changing any account.
    Add-Type -TypeDefinition @'
using System;
using System.Runtime.InteropServices;
using System.Security.Principal;
public static class CC03RestrictedToken {
    [StructLayout(LayoutKind.Sequential)] public struct SidAndAttributes { public IntPtr Sid; public uint Attributes; }
    [DllImport("advapi32.dll",SetLastError=true)] static extern bool CreateRestrictedToken(IntPtr source,uint flags,uint disableCount,[In] SidAndAttributes[] disable,uint deleteCount,IntPtr delete,uint restrictCount,IntPtr restrict,out IntPtr token);
    [DllImport("kernel32.dll")] public static extern bool CloseHandle(IntPtr handle);
    public static IntPtr Create() {
        var sid=new SecurityIdentifier("S-1-5-32-544"); var bytes=new byte[sid.BinaryLength]; sid.GetBinaryForm(bytes,0);
        var pointer=Marshal.AllocHGlobal(bytes.Length);
        try {
            Marshal.Copy(bytes,0,pointer,bytes.Length); IntPtr token;
            var disabled=new[]{new SidAndAttributes{Sid=pointer,Attributes=0}};
            if(!CreateRestrictedToken(WindowsIdentity.GetCurrent().Token,1,1,disabled,0,IntPtr.Zero,0,IntPtr.Zero,out token)) throw new Exception("RESTRICTED_TOKEN_CREATE_FAILED");
            return token;
        } finally { Marshal.FreeHGlobal(pointer); }
    }
}
'@
    $restricted = [CC03RestrictedToken]::Create()
    try {
        $filtered = [Security.Principal.WindowsIdentity]::new($restricted)
        try {
            if (-not (@($filtered.Groups | ForEach-Object { $_.Value }) -contains 'S-1-5-32-544')) { throw 'FILTERED_ADMIN_GROUP_MISSING' }
            if (Test-CCStandardIdentity $filtered) { throw 'FILTERED_ADMIN_ACCEPTED' }
            $checks += 'FILTERED_ADMIN_REJECTED'
        } finally { $filtered.Dispose() }
    } finally { [void][CC03RestrictedToken]::CloseHandle($restricted) }
    $checks | ConvertTo-Json -Compress
} finally { if ($created) { Remove-LocalUser -Name 'ccpanel' } }
