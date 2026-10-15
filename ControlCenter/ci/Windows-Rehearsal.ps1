# Disposable GitHub-hosted VM only. Never invoked by deployment entrypoints.
[CmdletBinding()]
param()
Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'
if ($env:GITHUB_ACTIONS -cne 'true' -or $env:RUNNER_ENVIRONMENT -cne 'github-hosted') { throw 'GITHUB_HOSTED_VM_REQUIRED' }
$package = Split-Path $PSScriptRoot -Parent
$sandbox = Join-Path $env:RUNNER_TEMP ('CC03-' + [guid]::NewGuid().ToString('N'))
$env:CC03_CI_DISPOSABLE_ROOT = $sandbox
$null = New-Item -ItemType Directory -Path $sandbox
. "$package\deployment\Common.ps1"
$users = @()
$panelProcess = $null
$exporterProcess = $null
$results = [ordered]@{}
$evidence = Join-Path $env:RUNNER_TEMP 'cc03-evidence'

function Expect-Failure([scriptblock]$Operation, [string]$Expected) {
    try { & $Operation } catch {
        if ($_.Exception.Message -notlike "*$Expected*") { throw }
        Write-Output "EXPECTED_REJECTION $Expected"
        return
    }
    throw "EXPECTED_FAILURE_MISSING: $Expected"
}

function Set-DisposableACL([string]$Path, [string]$Kind) {
    if (-not $Path.StartsWith($sandbox + '\', [StringComparison]::OrdinalIgnoreCase)) { throw 'ACL_SCOPE_VIOLATION' }
    $directory = Test-Path -LiteralPath $Path -PathType Container
    $acl = $(if ($directory) { [Security.AccessControl.DirectorySecurity]::new() } else { [Security.AccessControl.FileSecurity]::new() })
    $acl.SetAccessRuleProtection($true, $false)
    $acl.SetOwner([Security.Principal.SecurityIdentifier]::new('S-1-5-32-544'))
    $rights = @{'S-1-5-18'='FullControl'; 'S-1-5-32-544'='FullControl'}
    if ($Kind -ne 'private') { $rights[$panelSid] = $(if ($Kind -eq 'logs') { 'Modify' } else { 'ReadAndExecute' }) }
    $rights[$exporterSid] = $(if ($Kind -eq 'export') { 'Modify' } else { 'ReadAndExecute' })
    foreach ($sid in $rights.Keys) {
        $inherit = $(if ($directory) { 'ContainerInherit,ObjectInherit' } else { 'None' })
        $rule = [Security.AccessControl.FileSystemAccessRule]::new(
            [Security.Principal.SecurityIdentifier]::new($sid), $rights[$sid], $inherit, 'None', 'Allow')
        $acl.AddAccessRule($rule)
    }
    Set-Acl -LiteralPath $Path -AclObject $acl
}

# Real LogonUser tokens for two local non-administrator identities. Passwords
# remain in memory and are never written to a file, process arguments, or logs.
Add-Type -TypeDefinition @'
using System;
using System.IO;
using System.Runtime.InteropServices;
using System.Security.Principal;
public static class CC03Access {
    [DllImport("advapi32.dll", CharSet=CharSet.Unicode, SetLastError=true)]
    static extern bool LogonUser(string user, string domain, string password, int type, int provider, out IntPtr token);
    [DllImport("kernel32.dll")] static extern bool CloseHandle(IntPtr token);
    public static string Probe(string user, string password, string expectedSid, string path, bool write) {
        IntPtr token;
        if (!LogonUser(user, ".", password, 2, 0, out token))
            throw new Exception("LOGON_USER_UNAVAILABLE win32="+Marshal.GetLastWin32Error());
        try {
            using (var identity = new WindowsIdentity(token))
            using (var context = identity.Impersonate()) {
                var current = WindowsIdentity.GetCurrent();
                if (current.User.Value != expectedSid) throw new Exception("WRONG_PROBE_SID");
                foreach (var group in current.Groups)
                    if (group.Value == "S-1-5-32-544") throw new Exception("PROBE_IDENTITY_IS_ADMIN");
                try {
                    if (write) File.WriteAllText(path, "DISPOSABLE_CC03_PROBE");
                    else File.ReadAllText(path);
                    return "ALLOWED";
                } catch (UnauthorizedAccessException) { return "ACCESS_DENIED"; }
            }
        } finally { CloseHandle(token); }
    }
}
'@

try {
    if (-not ([Security.Principal.WindowsPrincipal][Security.Principal.WindowsIdentity]::GetCurrent()).IsInRole('Administrators')) {
        $results['separate_sid_acl'] = 'NOT_VERIFIED: VM token lacks local administrator rights to provision disposable users/ACLs'
        throw 'SID_REHEARSAL_NOT_VERIFIED'
    }
    $credentials = @()
    foreach ($role in @('panel','exporter')) {
        $name = 'cc03' + $role.Substring(0,1) + [guid]::NewGuid().ToString('N').Substring(0,8)
        $password = 'Cc03!aA9' + [guid]::NewGuid().ToString('N')
        $secret = ConvertTo-SecureString $password -AsPlainText -Force
        try {
            $user = New-LocalUser -Name $name -Password $secret -AccountNeverExpires -Description 'Disposable CC03 hosted acceptance only'
            $users += $name
            Add-LocalGroupMember -SID 'S-1-5-32-545' -Member $name
        } catch {
            $results['separate_sid_acl'] = 'NOT_VERIFIED: local user/group provisioning unavailable: ' + $_.Exception.Message
            throw 'SID_REHEARSAL_NOT_VERIFIED'
        }
        $credentials += [pscustomobject]@{ Name=$name; Password=$password; Sid=$user.SID.Value; Credential=[pscredential]::new("$env:COMPUTERNAME\$name", $secret) }
    }
    $panel = $credentials[0]; $exporter = $credentials[1]
    $panelSid = $panel.Sid; $exporterSid = $exporter.Sid
    Write-Output "DISPOSABLE_PANEL_SID=$panelSid DISPOSABLE_EXPORTER_SID=$exporterSid"
    foreach ($pair in @(@($script:AppRoot,'app'), @($script:VenvRoot,'venv'), @($script:DataRoot,'parent'),
                        @("$script:DataRoot\export",'export'), @("$script:DataRoot\logs",'logs'), @("$script:DataRoot\private",'private'))) {
        $null = New-Item -ItemType Directory -Path $pair[0] -Force
        Set-DisposableACL $pair[0] $pair[1]
    }
    Assert-LayoutACL $panelSid $exporterSid
    Expect-Failure { Assert-LayoutACL $panelSid $panelSid } 'DISTINCT_LOW_PRIVILEGE_SIDS_REQUIRED'
    Expect-Failure { Assert-CurrentIdentity $panelSid } 'DEDICATED_IDENTITY_REQUIRED'
    # Only fixture directories receive ACLs. Probe real effective rights, not just ACE text.
    $private = "$script:DataRoot\private\source-policy.json"
    Set-Content -LiteralPath $private -Value '{}' -Encoding ASCII
    Set-DisposableACL $private 'private'
    $exportFile = "$script:DataRoot\export\fixture.json"
    Set-Content -LiteralPath $exportFile -Value '{}' -Encoding ASCII
    foreach ($case in @(
        @($panel,$private,$false,'ACCESS_DENIED'), @($exporter,$private,$false,'ALLOWED'),
        @($panel,$exportFile,$false,'ALLOWED'), @($panel,$exportFile,$true,'ACCESS_DENIED'),
        @($exporter,$exportFile,$true,'ALLOWED'),
        @($panel,"$script:AppRoot\forbidden.txt",$true,'ACCESS_DENIED'),
        @($exporter,"$script:VenvRoot\forbidden.txt",$true,'ACCESS_DENIED'),
        @($exporter,"$script:DataRoot\parent-forbidden.txt",$true,'ACCESS_DENIED'),
        @($panel,"$script:DataRoot\logs\allowed.txt",$true,'ALLOWED'),
        @($exporter,"$script:DataRoot\logs\forbidden.txt",$true,'ACCESS_DENIED'))) {
        $identity = $case[0]
        $actual = [CC03Access]::Probe($identity.Name,$identity.Password,$identity.Sid,$case[1],$case[2])
        if ($actual -ne $case[3]) { throw "EFFECTIVE_ACL_MISMATCH expected=$($case[3]) actual=$actual" }
        Write-Output "EFFECTIVE_ACL_PASS role=$($identity.Name.Substring(0,5)) write=$($case[2]) result=$actual"
    }
    $results['separate_sid_acl'] = 'PASS: 10 actual access probes under two distinct non-admin logon tokens'
    & "$package\deployment\Preflight.ps1" -Execute -PanelSid $panelSid -ExporterSid $exporterSid
    if ($LASTEXITCODE -ne 0) { throw 'PREFLIGHT_FAILED' }
    # Downloaded exact hashed wheels are CI-only, never production credentials.
    $wheelhouse = Join-Path $sandbox 'wheels'
    & python -m pip download --require-hashes --only-binary=:all: --no-deps -r "$package\requirements-windows-ci.lock" -d $wheelhouse
    if ($LASTEXITCODE -ne 0) { throw 'WHEEL_DOWNLOAD_FAILED' }
    @(Get-ChildItem $wheelhouse -Filter '*.whl' | ForEach-Object {
        @{name=$_.Name; sha256=(Get-FileHash -LiteralPath $_.FullName -Algorithm SHA256).Hash.ToLowerInvariant()}
    }) | ConvertTo-Json | Set-Content -LiteralPath "$wheelhouse\wheels.sha256.json" -Encoding ASCII
    & "$package\deployment\Install.ps1" -Execute -PanelSid $panelSid -ExporterSid $exporterSid -Wheelhouse $wheelhouse
    if ($LASTEXITCODE -ne 0) { throw 'INSTALL_FAILED' }
    $results['install'] = 'PASS: real offline install into disposable ACL-provisioned roots'
    # Verify a loopback-only panel under the actual low-privilege panel SID.
    $arguments = "-NoProfile -File `"$script:AppRoot\deployment\Start-Panel.ps1`" -Execute -PanelSid $panelSid -ExporterSid $exporterSid"
    try {
        $panelProcess = Start-Process powershell.exe -Credential $panel.Credential -LoadUserProfile -ArgumentList $arguments -WorkingDirectory $script:AppRoot -PassThru -RedirectStandardOutput "$script:DataRoot\logs\panel-stdout.txt" -RedirectStandardError "$script:DataRoot\logs\panel-stderr.txt"
    } catch {
        $results['panel_identity_launch'] = 'NOT_VERIFIED: separate-SID process creation unavailable: ' + $_.Exception.Message
        throw 'SID_REHEARSAL_NOT_VERIFIED'
    }
    $ready = $false
    for ($i=0; $i -lt 30; $i++) {
        Start-Sleep -Seconds 1
        $listener = @(Get-NetTCPConnection -LocalPort 8501 -State Listen -ErrorAction SilentlyContinue)
        if ($listener.Count -eq 1 -and $listener[0].LocalAddress -eq '127.0.0.1') { $ready=$true; break }
        if ($panelProcess.HasExited) { break }
    }
    if (-not $ready) { throw 'DISPOSABLE_PANEL_DID_NOT_BIND_LOOPBACK' }
    & "$package\deployment\Verify.ps1" -Execute -PanelSid $panelSid -ExporterSid $exporterSid
    if ($LASTEXITCODE -ne 0) { throw 'VERIFY_FAILED' }
    $results['panel_verify'] = 'PASS: low-privilege panel and real loopback-only listener; receiver remains UNKNOWN without approved source'
    # A real low-privilege one-shot exporter must reject the unapproved empty
    # policy before any source reads. No physical H1 authority is synthesized.
    Assert-ACL $private $panelSid $exporterSid 'private'
    $arguments = "-NoProfile -File `"$script:AppRoot\deployment\Start-Exporter.ps1`" -Execute -PanelSid $panelSid -ExporterSid $exporterSid"
    $exporterProcess = Start-Process powershell.exe -Credential $exporter.Credential -LoadUserProfile -ArgumentList $arguments -WorkingDirectory $script:AppRoot -PassThru -RedirectStandardOutput "$evidence\exporter-stdout.txt" -RedirectStandardError "$evidence\exporter-stderr.txt"
    if (-not $exporterProcess.WaitForExit(30000)) { throw 'EXPORTER_TIMEOUT' }
    if ($exporterProcess.ExitCode -eq 0 -or (Get-Content -Raw "$evidence\exporter-stderr.txt") -notlike '*CC03_EXPORT_UNAVAILABLE*') { throw 'UNAPPROVED_EXPORTER_DID_NOT_FAIL_CLOSED' }
    $exporterProcess = $null
    if (Test-Path "$script:DataRoot\export\h1.snapshot.json") { throw 'UNAPPROVED_EXPORTER_PUBLISHED_DATA' }
    $results['exporter_fail_closed'] = 'PASS: separate-SID one-shot rejected unapproved policy, published nothing'
    $results['physical_source'] = 'OUT_OF_SCOPE: physical H1 source/account/TTL authority remains a separate Intel gate'
    # Stop only the process tree launched above, before uninstalling own package.
    & taskkill.exe /PID $panelProcess.Id /T /F
    $panelProcess = $null
    & "$package\deployment\Uninstall.ps1" -Execute -PanelSid $panelSid -ExporterSid $exporterSid
    if ($LASTEXITCODE -ne 0) { throw 'UNINSTALL_FAILED' }
    if (Test-Path "$script:AppRoot\app.py") { throw 'OWN_APP_NOT_REMOVED' }
    if (@(Get-ChildItem -Force -LiteralPath $script:VenvRoot).Count -ne 0) { throw 'OWN_VENV_NOT_REMOVED' }
    if (-not (Test-Path $private) -or -not (Test-Path $exportFile)) { throw 'DATA_NOT_RETAINED' }
    $results['uninstall'] = 'PASS: own package/venv removed, disposable private/export/log data retained'
    $results['status'] = 'PASS'
} catch {
    $results['status'] = $(if ($_.Exception.Message -match 'SID_REHEARSAL_NOT_VERIFIED|LOGON_USER_UNAVAILABLE') { 'NOT_VERIFIED' } else { 'FAIL' })
    $results['error'] = $_.Exception.Message
} finally {
    if ($null -ne $panelProcess) { & taskkill.exe /PID $panelProcess.Id /T /F }
    if ($null -ne $exporterProcess -and -not $exporterProcess.HasExited) { & taskkill.exe /PID $exporterProcess.Id /T /F }
    if (Test-Path "$script:DataRoot\logs") {
        Get-ChildItem "$script:DataRoot\logs" -Filter '*.txt' | Copy-Item -Destination $evidence
    }
    foreach ($name in $users) { Remove-LocalUser -Name $name }
    Remove-Item Env:CC03_CI_DISPOSABLE_ROOT
    $results | ConvertTo-Json -Depth 6 | Set-Content -LiteralPath "$evidence\powershell-rehearsal.json" -Encoding UTF8
    $results | ConvertTo-Json -Depth 6 | Write-Output
}
if ($results['status'] -eq 'NOT_VERIFIED') { exit 2 }
if ($results['status'] -ne 'PASS') { exit 1 }
