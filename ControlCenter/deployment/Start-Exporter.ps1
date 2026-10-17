# Compatibility entrypoint: exporter is prohibited without a separate
# approved source and security review. No H1, broker or task access.
[CmdletBinding()]
param([switch]$Execute, [string]$PanelSid, [switch]$OsObserver)
if (-not $Execute) { Write-Output 'PREVIEW: exporter disabled in single ccpanel model; All live broker observations remain UNKNOWN.'; return }
throw 'CC03_SINGLE_CCPANEL_EXPORTER_DISABLED'
