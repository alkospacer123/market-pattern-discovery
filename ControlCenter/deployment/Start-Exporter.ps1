# Compatibility entrypoint: exporter is prohibited without a separate
# approved source and security review. No H1/FINAM/Task access.
[CmdletBinding()]
param([switch]$Execute, [string]$PanelSid, [switch]$OsObserver)
if (-not $Execute) { Write-Output 'PREVIEW: exporter disabled in single ccpanel model; H1 and FINAM remain UNKNOWN.'; return }
throw 'CC03_SINGLE_CCPANEL_EXPORTER_DISABLED'
