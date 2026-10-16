# Disposable GitHub-hosted VM only. Never invoked by deployment entrypoints.
[CmdletBinding()]
param()
Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'
if ($env:GITHUB_ACTIONS -cne 'true' -or $env:RUNNER_ENVIRONMENT -cne 'github-hosted') { throw 'GITHUB_HOSTED_VM_REQUIRED' }
$package = Split-Path $PSScriptRoot -Parent
$sandbox = Join-Path $env:RUNNER_TEMP ('CC03-' + [guid]::NewGuid().ToString('N'))
$env:CC03_CI_DISPOSABLE_ROOT = $sandbox
$env:STREAMLIT_SERVER_HEADLESS = 'true'
$env:STREAMLIT_BROWSER_GATHER_USAGE_STATS = 'false'
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

function Start-IdentityScript($Identity, [string]$Entry, [string]$Output, [string]$ErrorLog) {
    function Literal([string]$Value) { return "'" + $Value.Replace("'", "''") + "'" }
    $lines = @(
        '$ErrorActionPreference = ''Stop''',
        'Write-Output (''STARTUP_SID='' + [Security.Principal.WindowsIdentity]::GetCurrent().User.Value)',
        'Write-Output (''STARTUP_CWD='' + (Get-Location).Path)',
        'Write-Output (''STARTUP_PID='' + $PID)',
        'Write-Output (''STARTUP_TEMP='' + $env:TEMP)'
    )
    foreach ($name in @('GITHUB_ACTIONS','RUNNER_ENVIRONMENT','RUNNER_TEMP','CC03_CI_DISPOSABLE_ROOT',
                        'PSMODULEPATH','STREAMLIT_SERVER_HEADLESS','STREAMLIT_BROWSER_GATHER_USAGE_STATS')) {
        $lines += '$env:' + $name + ' = ' + (Literal ([Environment]::GetEnvironmentVariable($name)))
    }
    $lines += 'if ([Security.Principal.WindowsIdentity]::GetCurrent().User.Value -ne ' + (Literal $Identity.Sid) + ') { throw ''WRONG_STARTUP_TOKEN'' }'
    $lines += '& ' + (Literal "$script:VenvRoot\Scripts\python.exe") + ' -m ci.identity_probe ' + (Literal $Identity.Sid) + ' ' + (Literal $Identity.Name.Substring(4,1))
    $lines += 'if ($LASTEXITCODE -ne 0) { throw ''IDENTITY_PYTHON_PROBE_FAILED'' }'
    $lines += 'Get-ExecutionPolicy -List | Format-Table | Out-String | Write-Output'
    $lines += '& ' + (Literal $Entry) + ' -Execute -PanelSid ' + (Literal $panelSid) + ' -ExporterSid ' + (Literal $exporterSid)
    $command = '& {' + "`n" + ($lines -join "`n") + "`n" + '}'
    $bootstrap = Join-Path $sandbox ('identity-' + $Identity.Name + '.ps1')
    Set-Content -LiteralPath $bootstrap -Value $command -Encoding UTF8
    $nativeLog = $ErrorLog + '.native'
    $native = [CC03Access]::StartAs($Identity.Name, $Identity.Password, (Join-Path $env:SYSTEMROOT 'System32\cmd.exe'), $bootstrap, $script:AppRoot, $nativeLog, $Identity.Sid)
    try {
        if (-not $native.WaitForExit(10000) -or $native.ExitCode -ne 0) {
            Write-Host ('NATIVE_CMD_STARTUP_STATE=' + $(if ($native.HasExited) { '0x{0:X8}' -f $native.ExitCode } else { 'RUNNING_BEFORE_COMMAND' }))
            throw 'NATIVE_CMD_STARTUP_FAILED'
        }
        Write-Host ('NATIVE_CMD_STARTUP_PASS sid=' + $Identity.Sid)
    } finally { if (-not $native.HasExited) { & taskkill.exe /PID $native.Id /T /F | Out-Host }; $native.Dispose() }
    $executable = Join-Path $env:SYSTEMROOT 'System32\WindowsPowerShell\v1.0\powershell.exe'
    return [CC03Access]::StartAs($Identity.Name, $Identity.Password, $executable, $bootstrap, $script:AppRoot, $ErrorLog, $Identity.Sid)
}

function Set-DisposableACL([string]$Path, [string]$Kind) {
    if ($Path -ne $sandbox -and -not $Path.StartsWith($sandbox + '\', [StringComparison]::OrdinalIgnoreCase)) { throw 'ACL_SCOPE_VIOLATION' }
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
using System.Text;
public sealed class CC03Child : IDisposable {
    IntPtr handle;
    public int Id { get; private set; }
    [DllImport("kernel32.dll", SetLastError=true)] static extern uint WaitForSingleObject(IntPtr handle, uint milliseconds);
    [DllImport("kernel32.dll", SetLastError=true)] static extern bool GetExitCodeProcess(IntPtr handle, out uint code);
    [DllImport("kernel32.dll")] static extern bool CloseHandle(IntPtr handle);
    public CC03Child(IntPtr handle, int id) { this.handle=handle; Id=id; }
    public bool WaitForExit(int milliseconds) {
        uint result=WaitForSingleObject(handle, (uint)milliseconds);
        if (result==0) return true;
        if (result==258) return false;
        throw new Exception("CHILD_WAIT_FAILED win32="+Marshal.GetLastWin32Error());
    }
    public bool HasExited { get { return WaitForExit(0); } }
    public int ExitCode { get { uint code; if (!GetExitCodeProcess(handle,out code)) throw new Exception("CHILD_EXIT_UNAVAILABLE"); return unchecked((int)code); } }
    public void Dispose() { if (handle!=IntPtr.Zero) { CloseHandle(handle); handle=IntPtr.Zero; } }
}
public static class CC03Access {
    [DllImport("advapi32.dll", CharSet=CharSet.Unicode, SetLastError=true)]
    static extern bool LogonUser(string user, string domain, string password, int type, int provider, out IntPtr token);
    [DllImport("kernel32.dll")] static extern bool CloseHandle(IntPtr token);
    [StructLayout(LayoutKind.Sequential)] struct StartupInfo {
        public int cb; public IntPtr reserved,desktop,title;
        public int x,y,xsize,ysize,xchars,ychars,fill,flags;
        public short show,reservedSize; public IntPtr reserved2,input,output,error;
    }
    [StructLayout(LayoutKind.Sequential)] struct ProcessInfo {
        public IntPtr process,thread; public int processId,threadId;
    }
    [DllImport("advapi32.dll", CharSet=CharSet.Unicode, SetLastError=true)]
    static extern bool CreateProcessWithTokenW(IntPtr token,int logonFlags,string application,StringBuilder command,int flags,IntPtr environment,string directory,ref StartupInfo startup,out ProcessInfo process);
    [DllImport("userenv.dll", SetLastError=true)] static extern bool CreateEnvironmentBlock(out IntPtr environment,IntPtr token,bool inherit);
    [DllImport("userenv.dll")] static extern bool DestroyEnvironmentBlock(IntPtr environment);
    public static CC03Child StartAs(string user,string password,string executable,string script,string directory,string log,string expectedSid) {
        IntPtr token;
        if (!LogonUser(user,".",password,2,0,out token)) throw new Exception("LOGON_USER_UNAVAILABLE win32="+Marshal.GetLastWin32Error());
        try {
            // Build the target identity environment BEFORE starting its runtime.
            // A null block inherits runneradmin TEMP/USERPROFILE and is invalid
            // for a separate low-privilege SID. Never copy runner secrets.
            IntPtr original;
            if (!CreateEnvironmentBlock(out original,token,false)) throw new Exception("USER_ENVIRONMENT_FAILED win32="+Marshal.GetLastWin32Error());
            var env=new System.Collections.Generic.SortedDictionary<string,string>(StringComparer.OrdinalIgnoreCase);
            try {
                int offset=0;
                while (true) {
                    string item=Marshal.PtrToStringUni(IntPtr.Add(original,offset));
                    if (String.IsNullOrEmpty(item)) break;
                    offset+=(item.Length+1)*2;
                    int split=item.IndexOf('=',1);
                    if (split>0) env[item.Substring(0,split)]=item.Substring(split+1);
                }
            } finally { DestroyEnvironmentBlock(original); }
            string temporary=Path.Combine(Path.GetDirectoryName(log),"runtime-"+user);
            using (var identity=new WindowsIdentity(token))
            using (var context=identity.Impersonate()) {
                if (WindowsIdentity.GetCurrent().User.Value!=expectedSid) throw new Exception("WRONG_CHILD_SID");
                Directory.CreateDirectory(temporary);
                Directory.CreateDirectory(Path.Combine(temporary,"AppData","Roaming"));
                Directory.CreateDirectory(Path.Combine(temporary,"AppData","Local"));
                File.WriteAllText(log,"NATIVE_LAUNCH_SID="+expectedSid+Environment.NewLine);
            }
            env["TEMP"]=temporary; env["TMP"]=temporary;
            env["USERPROFILE"]=temporary;
            env["APPDATA"]=Path.Combine(temporary,"AppData","Roaming");
            env["LOCALAPPDATA"]=Path.Combine(temporary,"AppData","Local");
            env["HOMEDRIVE"]=Path.GetPathRoot(temporary).TrimEnd('\\');
            env["HOMEPATH"]=temporary.Substring(2);
            env["PYTHONNOUSERSITE"]="1"; env["PYTHONDONTWRITEBYTECODE"]="1";
            var block=new StringBuilder();
            foreach (var pair in env) block.Append(pair.Key).Append('=').Append(pair.Value).Append('\0');
            block.Append('\0');
            IntPtr environment=Marshal.StringToHGlobalUni(block.ToString());
            var startup=new StartupInfo(); startup.cb=Marshal.SizeOf(typeof(StartupInfo));
            // NULL inherits the caller desktop, which belongs to runneradmin's
            // logon session. Empty string asks Windows for the target logon's
            // noninteractive station/desktop. Never alter an existing desktop
            // DACL or grant this user interactive runner desktop access.
            startup.desktop=Marshal.StringToHGlobalUni("");
            ProcessInfo process;
            string action="& '"+script.Replace("'","''")+"' *> '"+log.Replace("'","''")+"'";
            var command=new StringBuilder(executable.EndsWith("cmd.exe",StringComparison.OrdinalIgnoreCase)
                ? "\""+executable+"\" /d /c exit 0"
                : "\""+executable+"\" -NoProfile -NonInteractive -NoLogo -Command \""+action+"\"");
            if (command.Length>=1024) throw new Exception("LOGON_COMMAND_LINE_TOO_LONG");
            try {
                if (!CreateProcessWithTokenW(token,1,executable,command,0x08000400,environment,directory,ref startup,out process))
                    throw new Exception("CREATE_PROCESS_WITH_TOKEN_UNAVAILABLE win32="+Marshal.GetLastWin32Error());
            } finally { Marshal.FreeHGlobal(environment); Marshal.FreeHGlobal(startup.desktop); }
            CloseHandle(process.thread);
            return new CC03Child(process.process,process.processId);
        } finally { CloseHandle(token); }
    }
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
    Set-DisposableACL $sandbox 'parent'
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
    $wheelRecords = @(Get-ChildItem $wheelhouse -Filter '*.whl' | ForEach-Object {
        @{name=$_.Name; sha256=(Get-FileHash -LiteralPath $_.FullName -Algorithm SHA256).Hash.ToLowerInvariant()}
    })
    $validDigest = $wheelRecords[0].sha256
    $wheelRecords[0].sha256 = '0' * 64
    $wheelRecords | ConvertTo-Json | Set-Content -LiteralPath "$wheelhouse\wheels.sha256.json" -Encoding ASCII
    Expect-Failure { & "$package\deployment\Install.ps1" -Execute -PanelSid $panelSid -ExporterSid $exporterSid -Wheelhouse $wheelhouse } 'WHEEL_HASH_MISMATCH'
    if (@(Get-ChildItem -Force $script:AppRoot).Count -or @(Get-ChildItem -Force $script:VenvRoot).Count) { throw 'INVALID_WHEEL_WROTE_INSTALL_TARGET' }
    $results['invalid_wheel_regression'] = 'PASS: bad hash rejected before any target write'
    $wheelRecords[0].sha256 = $validDigest
    $wheelRecords | ConvertTo-Json | Set-Content -LiteralPath "$wheelhouse\wheels.sha256.json" -Encoding ASCII
    & "$package\deployment\Install.ps1" -Execute -PanelSid $panelSid -ExporterSid $exporterSid -Wheelhouse $wheelhouse
    if ($LASTEXITCODE -ne 0) { throw 'INSTALL_FAILED' }
    & "$script:VenvRoot\Scripts\python.exe" -c "import sys,struct; print('REHEARSAL_PYTHON='+sys.version); assert sys.version_info[:3]==(3,12,10) and struct.calcsize('P')==8"
    if ($LASTEXITCODE -ne 0) { throw 'REHEARSAL_PYTHON_VERSION_MISMATCH' }
    $results['install'] = 'PASS: real offline install into disposable ACL-provisioned roots'
    # Verify a loopback-only panel under the actual low-privilege panel SID.
    try {
        $panelProcess = Start-IdentityScript $panel "$script:AppRoot\deployment\Start-Panel.ps1" "$script:DataRoot\logs\panel-stdout.txt" "$script:DataRoot\logs\panel-stderr.txt"
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
    if (-not $ready) {
        $results['panel_child_exit'] = $(if ($panelProcess.HasExited) { '0x{0:X8}' -f $panelProcess.ExitCode } else { 'RUNNING_WITHOUT_LISTENER' })
        Get-CimInstance Win32_Process | Where-Object { $_.ProcessId -eq $panelProcess.Id -or $_.ParentProcessId -eq $panelProcess.Id } | ForEach-Object {
            $owner = Invoke-CimMethod -InputObject $_ -MethodName GetOwnerSid
            Write-Output ("CHILD_STATE pid=" + $_.ProcessId + " parent=" + $_.ParentProcessId + " name=" + $_.Name + " sid=" + $owner.Sid + " threads=" + $_.ThreadCount)
        }
        if (-not $panelProcess.HasExited) {
            $process = Get-Process -Id $panelProcess.Id
            Write-Output ('CHILD_SESSION=' + $process.SessionId)
            $process.Threads | ForEach-Object { Write-Output ('CHILD_THREAD id=' + $_.Id + ' state=' + $_.ThreadState + $(if ($_.ThreadState -eq 'Wait') { ' wait=' + $_.WaitReason } else { '' })) }
            Write-Output ('CHILD_MODULES=' + (($process.Modules | Select-Object -ExpandProperty ModuleName) -join ','))
        }
        $results['panel_log_present'] = Test-Path "$script:DataRoot\logs\panel-stderr.txt"
        throw 'DISPOSABLE_PANEL_DID_NOT_BIND_LOOPBACK'
    }
    $listenerProcess = Get-CimInstance Win32_Process -Filter ("ProcessId=" + $listener[0].OwningProcess)
    $listenerOwner = Invoke-CimMethod -InputObject $listenerProcess -MethodName GetOwnerSid
    if ($listenerOwner.Sid -ne $panelSid) { throw 'LISTENER_WRONG_SID' }
    $health = Invoke-WebRequest -Uri 'http://127.0.0.1:8501/_stcore/health' -UseBasicParsing
    if ($health.StatusCode -ne 200 -or $health.Content -ne 'ok') { throw 'PANEL_HEALTH_FAILED' }
    $results['panel_listener'] = 'PASS: HTTP health 200, 127.0.0.1:8501 owned by CCPanel SID ' + $listenerOwner.Sid
    & "$package\deployment\Verify.ps1" -Execute -PanelSid $panelSid -ExporterSid $exporterSid
    if ($LASTEXITCODE -ne 0) { throw 'VERIFY_FAILED' }
    $results['panel_verify'] = 'PASS: low-privilege panel and real loopback-only listener; receiver remains UNKNOWN without approved source'
    # A real low-privilege one-shot exporter must reject the unapproved empty
    # policy before any source reads. No physical H1 authority is synthesized.
    Assert-ACL $private $panelSid $exporterSid 'private'
    $exporterLog = "$script:DataRoot\export\exporter-process.txt"
    $exporterProcess = Start-IdentityScript $exporter "$script:AppRoot\deployment\Start-Exporter.ps1" $exporterLog $exporterLog
    if (-not $exporterProcess.WaitForExit(30000)) { throw 'EXPORTER_TIMEOUT' }
    if ($exporterProcess.ExitCode -eq 0 -or (Get-Content -Raw $exporterLog) -notlike '*CC03_EXPORT_UNAVAILABLE*') { throw 'UNAPPROVED_EXPORTER_DID_NOT_FAIL_CLOSED' }
    $exporterProcess.Dispose()
    $exporterProcess = $null
    # The CI identity probe deliberately publishes one synthetic UNKNOWN export;
    # the production entrypoint with an unapproved policy must add none.
    $probeSnapshots = @(Get-ChildItem "$script:DataRoot\export" -Filter 'h1-*.json')
    if ($probeSnapshots.Count -ne 1) { throw 'UNAPPROVED_EXPORTER_PUBLISHED_DATA' }
    $results['exporter_fail_closed'] = 'PASS: separate-SID one-shot rejected unapproved policy, published nothing beyond the explicitly synthetic CI probe'
    $results['physical_source'] = 'OUT_OF_SCOPE: physical H1 source/account/TTL authority remains a separate Intel gate'
    # Stop only the process tree launched above, before uninstalling own package.
    & taskkill.exe /PID $panelProcess.Id /T /F
    if (-not $panelProcess.WaitForExit(10000)) { throw 'PANEL_CLEANUP_TIMEOUT' }
    if (@(Get-NetTCPConnection -LocalPort 8501 -State Listen -ErrorAction SilentlyContinue).Count) { throw 'PANEL_LISTENER_NOT_CLEANED' }
    $results['process_cleanup'] = 'PASS: own panel process tree exited and listener removed; exporter already exited'
    $panelProcess.Dispose()
    $panelProcess = $null
    & "$package\deployment\Uninstall.ps1" -Execute -PanelSid $panelSid -ExporterSid $exporterSid
    if ($LASTEXITCODE -ne 0) { throw 'UNINSTALL_FAILED' }
    if (Test-Path "$script:AppRoot\app.py") { throw 'OWN_APP_NOT_REMOVED' }
    if (@(Get-ChildItem -Force -LiteralPath $script:VenvRoot).Count -ne 0) { throw 'OWN_VENV_NOT_REMOVED' }
    if (-not (Test-Path $private) -or -not (Test-Path $exportFile) -or (Get-Content -Raw $private).Trim() -ne '{}' -or (Get-Content -Raw $exportFile) -ne 'DISPOSABLE_CC03_PROBE') { throw 'DATA_NOT_RETAINED' }
    $results['uninstall'] = 'PASS: own package/venv removed, disposable private/export/log data retained'
    $results['status'] = 'PASS'
} catch {
    $results['status'] = $(if ($_.Exception.Message -match 'SID_REHEARSAL_NOT_VERIFIED|LOGON_USER_UNAVAILABLE') { 'NOT_VERIFIED' } else { 'FAIL' })
    $results['error'] = $_.Exception.Message
    $results['position'] = $_.InvocationInfo.PositionMessage
    $results['stack'] = $_.ScriptStackTrace
} finally {
    if ($null -ne $panelProcess -and -not $panelProcess.HasExited) { & taskkill.exe /PID $panelProcess.Id /T /F }
    if ($null -ne $exporterProcess -and -not $exporterProcess.HasExited) { & taskkill.exe /PID $exporterProcess.Id /T /F }
    if ($null -ne $panelProcess) { $panelProcess.Dispose() }
    if ($null -ne $exporterProcess) { $exporterProcess.Dispose() }
    if (Test-Path "$script:DataRoot\export\exporter-process.txt") {
        Copy-Item "$script:DataRoot\export\exporter-process.txt" -Destination $evidence
        Write-Output 'REHEARSAL_LOG exporter-process.txt'
        Get-Content "$script:DataRoot\export\exporter-process.txt"
    }
    if ($results.Contains('install') -and -not $results.Contains('uninstall')) {
        try {
            & "$package\deployment\Uninstall.ps1" -Execute -PanelSid $panelSid -ExporterSid $exporterSid
            if ($LASTEXITCODE -ne 0 -or (Test-Path "$script:AppRoot\app.py") -or @(Get-ChildItem -Force -LiteralPath $script:VenvRoot).Count -ne 0) { throw 'FALLBACK_UNINSTALL_FAILED' }
            if (-not (Test-Path $private) -or -not (Test-Path $exportFile)) { throw 'DATA_NOT_RETAINED' }
            $results['uninstall'] = 'PASS: own package/venv removed after failed launch; data retained'
        } catch { $results['uninstall'] = 'FAIL: ' + $_.Exception.Message }
    }
    if (Test-Path "$script:DataRoot\logs") {
        Get-ChildItem "$script:DataRoot\logs" -Filter '*.txt' | ForEach-Object {
            Copy-Item -LiteralPath $_.FullName -Destination $evidence
            Write-Output ('REHEARSAL_LOG ' + $_.Name)
            Get-Content -LiteralPath $_.FullName
        }
    }
    foreach ($name in $users) { Remove-LocalUser -Name $name }
    Remove-Item Env:CC03_CI_DISPOSABLE_ROOT
    $results | ConvertTo-Json -Depth 6 | Set-Content -LiteralPath "$evidence\powershell-rehearsal.json" -Encoding UTF8
    $results | ConvertTo-Json -Depth 6 | Write-Output
}
if ($results['status'] -eq 'NOT_VERIFIED') { exit 2 }
if ($results['status'] -ne 'PASS') { exit 1 }
