[CmdletBinding()]
param([switch]$Execute, [string]$PanelSid, [string]$ExporterSid)
. "$PSScriptRoot\Common.ps1"
if (-not $Execute) { Write-Output 'PREVIEW: foreground Streamlit on 127.0.0.1:8501, CORS/XSRF enabled; only panel process.'; return }
Assert-CurrentIdentity $PanelSid
Assert-ACL $script:DataRoot $PanelSid $ExporterSid 'parent'
if (Test-Path -LiteralPath "$script:AppRoot\deployment\receiver-policy.json") {
    Assert-ACL "$script:AppRoot\deployment\receiver-policy.json" $PanelSid $ExporterSid 'app'
}
Assert-ACL $script:AppRoot $PanelSid $ExporterSid 'app'
Assert-ACL $script:VenvRoot $PanelSid $ExporterSid 'venv'
Assert-ACL "$script:DataRoot\export" $PanelSid $ExporterSid 'export'
$null = Get-Manifest $script:AppRoot
Assert-PlainPath $script:VenvRoot
Push-Location $script:AppRoot
try {
    & "$script:VenvRoot\Scripts\python.exe" -m streamlit run app.py --server.address=127.0.0.1 --server.port=8501 --server.enableCORS=true --server.enableXsrfProtection=true
    if ($LASTEXITCODE -ne 0) { throw 'PANEL_EXITED_WITH_ERROR' }
} finally { Pop-Location }
