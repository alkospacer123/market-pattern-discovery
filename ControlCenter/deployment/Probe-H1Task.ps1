[CmdletBinding()]
param([switch]$Execute)
Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'
if (-not $Execute) { Write-Output 'PREVIEW: unbound legacy Task probe retired; use separately bound Start-Exporter -OsObserver. No Task query/change.'; return }
# A name-only manual probe cannot establish the approved Task identity.
Write-Output 'CC03_TASK_UNAVAILABLE_USE_BOUND_OS_OBSERVER'
exit 1
