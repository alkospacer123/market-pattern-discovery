[CmdletBinding()]
param([switch]$Execute, [string]$PanelSid, [string]$ExporterSid)
. "$PSScriptRoot\Common.ps1"
if (-not $Execute) { Write-Output 'PREVIEW: independent one-shot exporter; legacy live source BLOCKED, own immutable export only. No H1 process or API.'; return }
Assert-CurrentIdentity $ExporterSid
Assert-ACL $script:DataRoot $PanelSid $ExporterSid 'parent'
Assert-ACL "$script:DataRoot\private" $PanelSid $ExporterSid 'private'
Assert-ACL "$script:DataRoot\private\source-policy.json" $PanelSid $ExporterSid 'private'
Assert-ACL $script:AppRoot $PanelSid $ExporterSid 'app'
Assert-ACL $script:VenvRoot $PanelSid $ExporterSid 'venv'
Assert-ACL "$script:DataRoot\export" $PanelSid $ExporterSid 'export'
$null = Get-Manifest $script:AppRoot
Assert-PlainPath $script:VenvRoot
Push-Location $script:AppRoot
try {
    & "$script:VenvRoot\Scripts\python.exe" -m exporter.snapshot --execute
    if ($LASTEXITCODE -ne 0) { throw 'CC03_EXPORT_UNAVAILABLE' }
} finally { Pop-Location }
