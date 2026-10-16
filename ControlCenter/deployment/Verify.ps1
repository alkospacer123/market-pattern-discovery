[CmdletBinding()]
param([switch]$Execute, [string]$PanelSid, [string]$ExporterSid)
. "$PSScriptRoot\Common.ps1"
if (-not $Execute) { Write-Output 'PREVIEW: READONLY package/ACL/dependency/listener/source checks; no H1 Task/state/database read or change.'; return }
$null = Get-Manifest $script:AppRoot
Assert-LayoutACL $PanelSid $ExporterSid
& "$script:VenvRoot\Scripts\python.exe" -m pip check
if ($LASTEXITCODE -ne 0) { throw 'DEPENDENCIES_INVALID' }
$listener = @(Get-NetTCPConnection -LocalPort 8501 -State Listen -ErrorAction SilentlyContinue)
if ($listener.Count -ne 1 -or $listener[0].LocalAddress -ne '127.0.0.1') { throw 'LOOPBACK_LISTENER_REQUIRED' }
$listenerProcess = Get-CimInstance Win32_Process -Filter ("ProcessId=" + $listener[0].OwningProcess)
$listenerOwner = Invoke-CimMethod -InputObject $listenerProcess -MethodName GetOwnerSid
if ($listenerOwner.Sid -ne $PanelSid) { throw 'PANEL_LISTENER_IDENTITY_REQUIRED' }
Push-Location $script:AppRoot
try {
    & "$script:VenvRoot\Scripts\python.exe" -c "from datetime import datetime,timezone; from cc.models import RobotId; from cc.providers.h1_export import H1ExportProvider; s=H1ExportProvider().snapshot(RobotId.H1,'',datetime.now(timezone.utc)); print('CC03_H1_STATE='+s.status.state.value); assert s.positions is None and s.status.trading_allowed in (False,None)"
    if ($LASTEXITCODE -ne 0) { throw 'READONLY_RECEIVER_FAILED' }
} finally { Pop-Location }
Write-Output 'CC03_INSTALL_VERIFY_PASS_PHYSICAL_H1_NOT_ACCEPTED'
