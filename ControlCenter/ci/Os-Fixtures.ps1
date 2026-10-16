# MUTATING TEST HARNESS: disposable GitHub VM objects only. Never installed/run by UI.
[CmdletBinding()]
param([ValidateSet('Create','Inspect','Remove','Process')][string]$Operation,
      [string]$Folder, [uint32]$ProcessId)
Set-StrictMode -Version Latest
$ErrorActionPreference='Stop'
if ($env:GITHUB_ACTIONS -cne 'true' -or $env:RUNNER_ENVIRONMENT -cne 'github-hosted') { throw 'DISPOSABLE_HOST_REQUIRED' }
function Digest([string]$Text) {
    $sha=[Security.Cryptography.SHA256]::Create()
    try { ([BitConverter]::ToString($sha.ComputeHash([Text.Encoding]::UTF8.GetBytes($Text)))).Replace('-','').ToLowerInvariant() }
    finally { $sha.Dispose() }
}
if ($Operation -eq 'Process') {
    $p=Get-CimInstance Win32_Process -Filter "ProcessId=$ProcessId"
    $owner=Invoke-CimMethod -InputObject $p -MethodName GetOwnerSid
    if ($owner.ReturnValue -ne 0) { throw 'OWNER_UNAVAILABLE' }
    @{process_pid=$ProcessId;process_image_sha256=(Digest (([string]$p.ExecutablePath).ToLowerInvariant()));
      process_command_sha256=(Digest ([string]$p.CommandLine));process_principal_sid=$owner.Sid;
      process_creation_sha256=(Digest ($p.CreationDate.ToUniversalTime().ToString('o')))} | ConvertTo-Json -Compress
    return
}
if ($Folder -cnotmatch '^CC03-CI-[a-f0-9]{32}$') { throw 'DISPOSABLE_TASK_SCOPE_REQUIRED' }
$service=New-Object -ComObject Schedule.Service
$service.Connect()
$root=$service.GetFolder('\')
if ($Operation -eq 'Create') {
    $folderObject=$root.CreateFolder($Folder,'O:BAG:BAD:P(A;;GA;;;SY)(A;;GA;;;BA)(A;;GR;;;BU)')
    foreach ($name in @('Disabled','Ready','Running','Denied')) {
        $definition=$service.NewTask(0)
        $definition.RegistrationInfo.Description='CC03 disposable OS observation fixture'
        $definition.Principal.UserId=[Security.Principal.WindowsIdentity]::GetCurrent().User.Value
        $definition.Principal.LogonType=3
        $definition.Settings.Enabled=($name -ne 'Disabled')
        $definition.Settings.ExecutionTimeLimit='PT2M'
        $action=$definition.Actions.Create(0)
        $action.Path=Join-Path $env:SYSTEMROOT 'System32\WindowsPowerShell\v1.0\powershell.exe'
        $action.Arguments='-NoProfile -NonInteractive -Command Start-Sleep -Seconds 90'
        $registered=$folderObject.RegisterTaskDefinition($name,$definition,2,$null,$null,3,$null)
        $registered.SetSecurityDescriptor('O:BAG:BAD:P(A;;GA;;;SY)(A;;GA;;;BA)(A;;GR;;;BU)',0)
        if ($name -eq 'Running') { $null=$registered.Run($null) }
        if ($name -eq 'Denied') { $registered.SetSecurityDescriptor('O:BAG:BAD:P(A;;GA;;;SY)(A;;GA;;;BA)',0) }
    }
    for ($i=0;$i -lt 40 -and $folderObject.GetTask('Running').State -ne 4;$i++) { Start-Sleep -Milliseconds 100 }
}
if ($Operation -eq 'Remove') {
    $folderObject=$root.GetFolder($Folder)
    foreach ($name in @('Disabled','Ready','Running','Denied')) {
        $task=$folderObject.GetTask($name)
        if ($task.State -in @(2,4)) { $task.Stop(0) }
        $folderObject.DeleteTask($name,0)
    }
    $root.DeleteFolder($Folder,0)
    return
}
$folderObject=$root.GetFolder($Folder)
$result=@{}
foreach ($name in @('Disabled','Ready','Running','Denied')) {
    $task=$folderObject.GetTask($name)
    $principal=[string]$task.Definition.Principal.UserId
    if ($principal -notmatch '^S-1-') { $principal=([Security.Principal.NTAccount]::new($principal)).Translate([Security.Principal.SecurityIdentifier]).Value }
    $result[$name]=@{task_name="\$Folder\$name";task_xml_sha256=(Digest ([string]$task.Xml));
        task_principal_sid=$principal;state=[int]$task.State}
}
$result | ConvertTo-Json -Compress -Depth 5
