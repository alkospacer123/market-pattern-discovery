[CmdletBinding()]
param([switch]$Execute)
Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'
if (-not $Execute) { Write-Output 'PREVIEW: Get-ScheduledTask exact H1 production task; state + UTC only; no Task changes, no process launch.'; return }
try {
    $task = Get-ScheduledTask -TaskName 'TradingSystemLab-Stage8-Production' -TaskPath '\' -ErrorAction Stop
    $state = [string]$task.State
    if ($state -notin @('Disabled','Ready','Running','Queued','Unknown')) { $state = 'Unknown' }
    [pscustomobject]@{ schema_id='cc03.manual-task-observation.v1'; source='WINDOWS_TASK_READONLY'; observed_at=[DateTime]::UtcNow.ToString('o'); state=$state } | ConvertTo-Json -Compress
} catch { Write-Output 'CC03_TASK_UNAVAILABLE'; exit 1 }
