[CmdletBinding()]
param([switch]$Execute, [string]$PanelSid, [string]$ExporterSid)
. "$PSScriptRoot\Common.ps1"
if (-not $Execute) { Write-Output 'PREVIEW: verify package hashes, local NTFS, separate pre-provisioned ACL roots, Python 3.12 x64. No writes.'; return }
$null = Get-Manifest $script:PackageRoot
Assert-LayoutACL $PanelSid $ExporterSid
& py -3.12 -c "import sys,struct; assert sys.version_info[:2]==(3,12) and struct.calcsize('P')==8"
if ($LASTEXITCODE -ne 0) { throw 'PYTHON_312_X64_REQUIRED' }
Write-Output 'CC03_PREFLIGHT_PASS_NO_H1_ACCESS'
