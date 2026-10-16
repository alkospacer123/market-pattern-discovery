[CmdletBinding()]
param([switch]$Execute, [string]$PanelSid, [string]$ExporterSid, [switch]$OsObserver)
. "$PSScriptRoot\Common.ps1"
if (-not $Execute) { Write-Output 'PREVIEW: independent one-shot exporter; -OsObserver selects Windows OS READONLY facts; legacy live content BLOCKED. No H1 action or API.'; return }
Assert-CurrentIdentity $ExporterSid
Assert-ACL $script:DataRoot $PanelSid $ExporterSid 'parent'
Assert-ACL "$script:DataRoot\private" $PanelSid $ExporterSid 'private'
$policyName = if ($OsObserver) { 'os-policy.json' } else { 'source-policy.json' }
Assert-ACL "$script:DataRoot\private\$policyName" $PanelSid $ExporterSid 'private'
Assert-ACL $script:AppRoot $PanelSid $ExporterSid 'app'
Assert-ACL $script:VenvRoot $PanelSid $ExporterSid 'venv'
Assert-ACL "$script:DataRoot\export" $PanelSid $ExporterSid 'export'
$null = Get-Manifest $script:AppRoot
Assert-PlainPath $script:VenvRoot
Push-Location $script:AppRoot
try {
    if ($OsObserver) {
        & "$script:VenvRoot\Scripts\python.exe" -m observer.windows_os --execute
    } else {
        & "$script:VenvRoot\Scripts\python.exe" -m exporter.snapshot --execute
    }
    if ($LASTEXITCODE -ne 0) { throw 'CC03_EXPORT_UNAVAILABLE' }
} finally { Pop-Location }
