# Fixed local READONLY API calls. Input is administrator-owned policy, never UI data.
Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'
$ProgressPreference = 'SilentlyContinue'
function Digest([string]$Text) {
    $sha = [Security.Cryptography.SHA256]::Create()
    try { return ([BitConverter]::ToString($sha.ComputeHash([Text.Encoding]::UTF8.GetBytes($Text)))).Replace('-','').ToLowerInvariant() }
    finally { $sha.Dispose() }
}
function Row([string]$State, [string]$Reason, $Value) {
    return @{state=$State; reason=$Reason; observed_at=[DateTime]::UtcNow.ToString('yyyy-MM-ddTHH:mm:ss.ffffffK');
        confidence=$(if ($State -eq 'UNKNOWN') {'UNKNOWN'} else {'OS_OBSERVED'}); value=$Value}
}
function Sid([string]$Name) {
    if ($Name -match '^S-1-') { return $Name }
    return ([Security.Principal.NTAccount]::new($Name)).Translate([Security.Principal.SecurityIdentifier]).Value
}
try {
    $p = [Console]::In.ReadToEnd() | ConvertFrom-Json
    $task = Row 'UNKNOWN' 'UNAVAILABLE' $null
    $process = Row 'UNKNOWN' 'DISABLED' $null
    # Manual C uses the same standard primary ccpanel as the panel. Fail before
    # any Task/PID query; this is a read-only account/token check, no ACL repair.
    if ($p.PSObject.Properties.Name -contains 'require_ccpanel') {
        if ($p.require_ccpanel -cne $true) { throw 'CCPANEL_REQUIRED' }
        . "$PSScriptRoot\..\deployment\PanelIdentity.ps1"
        $identity = [Security.Principal.WindowsIdentity]::GetCurrent()
        if ($identity.User.Value -ne $p.observer_sid -or
            $identity.ImpersonationLevel -ne [Security.Principal.TokenImpersonationLevel]::None -or
            (Get-CCPanelState $p.observer_sid) -ne 'CCPANEL_ENABLED') {
            @{task=(Row 'UNKNOWN' 'ACCESS_DENIED' $null);process=(Row 'UNKNOWN' 'ACCESS_DENIED' $null)} |
                ConvertTo-Json -Compress -Depth 5
            exit 0
        }
    }
    try {
        $service = New-Object -ComObject 'Schedule.Service'
        $service.Connect() # local host, current low-privilege identity only
        $registered = $service.GetFolder('\').GetTask([string]$p.task_name)
        $fingerprint = Digest ([string]$registered.Xml)
        $principal = Sid ([string]$registered.Definition.Principal.UserId)
        $state = [int]$registered.State
        if ($fingerprint -ne $p.task_xml_sha256 -or $principal -ne $p.task_principal_sid) {
            $task = Row 'UNKNOWN' 'IDENTITY_MISMATCH' $null
        } elseif ((Digest ([string]$registered.Xml)) -ne $fingerprint -or [int]$registered.State -ne $state) {
            $task = Row 'UNKNOWN' 'CHANGED' $null
        } elseif ($state -in @(1,3,4)) {
            $states = @{1='TASK_DISABLED';3='TASK_READY';4='TASK_RUNNING'}
            $task = Row $states[$state] 'OK' $fingerprint
        }
    } catch {
        $code = $_.Exception.HResult -band 0xffff
        # COM errors can be wrapped by PowerShell's MethodInvocationException.
        if ($null -ne $_.Exception.InnerException) { $code = $_.Exception.InnerException.HResult -band 0xffff }
        $reason = if ($code -eq 2 -or $code -eq 3) {'NOT_FOUND'} elseif ($code -eq 5) {'ACCESS_DENIED'} else {'UNAVAILABLE'}
        $task = Row 'UNKNOWN' $reason $null
    }
    if ($p.process_enabled -and $task.state -eq 'UNKNOWN') { $process=Row 'UNKNOWN' 'UNAPPROVED' $null }
    if ($p.process_enabled -and $task.state -ne 'UNKNOWN') {
        try {
            # Exact approved PID + creation epoch; PID reuse cannot satisfy identity.
            # No wildcard/name discovery, command invocation or environment read.
            $expectedPid = [uint32]$p.process_pid
            $candidates = @(Get-CimInstance -ClassName Win32_Process -Filter "ProcessId=$expectedPid" -OperationTimeoutSec 2 -ErrorAction Stop)
            if ($candidates.Count -gt 1) { throw 'BOUND' }
            $matches = 0; $uncertain = $false; $denied = $false
            foreach ($candidate in $candidates) {
                if (-not $candidate.ExecutablePath -or -not $candidate.CommandLine) { $uncertain=$true; $denied=$true; continue }
                $image = Digest (([string]$candidate.ExecutablePath).ToLowerInvariant())
                $command = Digest ([string]$candidate.CommandLine)
                $created = Digest ($candidate.CreationDate.ToUniversalTime().ToString('o'))
                if ($image -ne $p.process_image_sha256 -or $command -ne $p.process_command_sha256 -or
                    $created -ne $p.process_creation_sha256) { $uncertain=$true; continue }
                $owner = Invoke-CimMethod -InputObject $candidate -MethodName GetOwnerSid -OperationTimeoutSec 2 -ErrorAction Stop
                if ($owner.ReturnValue -ne 0) { $uncertain=$true; $denied=$true; continue }
                if ($owner.Sid -ne $p.process_principal_sid) { $uncertain=$true; continue }
                $pidValue = [uint32]$candidate.ProcessId
                $again = @(Get-CimInstance Win32_Process -Filter "ProcessId=$pidValue" -OperationTimeoutSec 2 -ErrorAction Stop)
                if ($again.Count -eq 0) { continue } # disappeared is not access denied
                if ($again.Count -ne 1 -or $again[0].CreationDate -ne $candidate.CreationDate -or
                    $again[0].ExecutablePath -cne $candidate.ExecutablePath -or $again[0].CommandLine -cne $candidate.CommandLine) {
                    $uncertain=$true; continue
                }
                $matches++
            }
            if ($matches -eq 1) { $process=Row 'PROCESS_OBSERVED' 'OK' $p.process_command_sha256 }
            elseif ($matches -gt 1) { $process=Row 'UNKNOWN' 'IDENTITY_MISMATCH' $null }
            elseif ($uncertain) { $process=Row 'UNKNOWN' $(if ($denied) {'ACCESS_DENIED'} else {'IDENTITY_MISMATCH'}) $null }
            else { $process=Row 'PROCESS_ABSENT' 'NOT_FOUND' $p.process_command_sha256 }
        } catch { $process=Row 'UNKNOWN' 'UNAVAILABLE' $null }
    }
    # One helper invocation brackets the optional PID read with the same exact
    # Task. State/XML/principal drift clears BOTH positive facts, never retries.
    if ($task.state -ne 'UNKNOWN') {
        try {
            $final = $service.GetFolder('\').GetTask([string]$p.task_name)
            if ((Digest ([string]$final.Xml)) -ne $fingerprint -or
                (Sid ([string]$final.Definition.Principal.UserId)) -ne $principal -or
                [int]$final.State -ne $state) {
                $task=Row 'UNKNOWN' 'CHANGED' $null
                $process=Row 'UNKNOWN' 'CHANGED' $null
            }
        } catch {
            $task=Row 'UNKNOWN' 'UNAVAILABLE' $null
            $process=Row 'UNKNOWN' 'UNAVAILABLE' $null
        }
    }
    @{task=$task;process=$process} | ConvertTo-Json -Compress -Depth 5
} catch { [Console]::Out.Write('{}'); exit 1 }
