[CmdletBinding()]
param([switch]$Execute, [string]$PanelSid, [string]$Wheelhouse)
. "$PSScriptRoot\Common.ps1"
if (-not $Execute) { Write-Output 'PREVIEW: verify package hashes, local NTFS, single pre-provisioned ccpanel ACL roots, Python 3.12 x64. No writes.'; return }
$null = Get-Manifest $script:PackageRoot
Assert-LayoutACL $PanelSid
Assert-TrustedBase $PanelSid
Assert-OfflineWheels $Wheelhouse $PanelSid
Write-Output 'CC03_PREFLIGHT_PASS_NO_H1_ACCESS'
