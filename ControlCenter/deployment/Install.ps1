[CmdletBinding()]
param([switch]$Execute, [string]$PanelSid, [string]$ExporterSid, [string]$Wheelhouse)
. "$PSScriptRoot\Common.ps1"
if (-not $Execute) { Write-Output 'PREVIEW: copy manifest files into empty C:\TSLControlCenterApp; create independent venv; install offline wheels. No ACL/Task/H1 changes.'; return }
& "$PSScriptRoot\Preflight.ps1" -Execute -PanelSid $PanelSid -ExporterSid $ExporterSid
if ([string]::IsNullOrWhiteSpace($Wheelhouse)) { throw 'OFFLINE_WHEELHOUSE_REQUIRED' }
Assert-PlainPath $Wheelhouse
foreach ($root in @($script:AppRoot,$script:VenvRoot)) {
    if (@(Get-ChildItem -Force -LiteralPath $root).Count -ne 0) { throw 'EMPTY_CC_TARGET_REQUIRED' }
}
$manifest = Get-Manifest $script:PackageRoot
# No dependency execution occurs until operator-approved wheelhouse hashes match.
$wheelManifest = Join-Path $Wheelhouse 'wheels.sha256.json'
Assert-PlainPath $wheelManifest
# Windows PowerShell 5.1 emits a JSON array as one pipeline object. Materialize
# it before @() enumerates it, so each validated record remains a single wheel.
$wheelRecords = Get-Content -Raw -LiteralPath $wheelManifest | ConvertFrom-Json
$wheels = @($wheelRecords)
if ($wheels.Count -eq 0) { throw 'WHEEL_MANIFEST_EMPTY' }
foreach ($wheel in $wheels) {
    if ($wheel.name -notmatch '^[A-Za-z0-9_.+-]+\.whl$') { throw 'WHEEL_NAME_INVALID' }
    $file = Join-Path $Wheelhouse $wheel.name
    Assert-PlainPath $file
    if ((Get-FileHash -LiteralPath $file -Algorithm SHA256).Hash.ToLowerInvariant() -ne $wheel.sha256) { throw 'WHEEL_HASH_MISMATCH' }
}
if (@(Get-ChildItem -LiteralPath $Wheelhouse -Filter '*.whl').Count -ne $wheels.Count) { throw 'UNLISTED_WHEEL' }
$null = New-Item -ItemType Directory -Force -Path "$script:AppRoot\deployment"
Copy-Item -LiteralPath (Join-Path $script:PackageRoot 'deployment\manifest.json') -Destination "$script:AppRoot\deployment\manifest.json"
Set-Content -LiteralPath "$script:VenvRoot\CC03-owned.txt" -Value 'CC03 independent venv only' -Encoding ASCII
foreach ($entry in $manifest.files) {
    $target = Join-Path $script:AppRoot $entry.path
    $null = New-Item -ItemType Directory -Force -Path (Split-Path $target -Parent)
    Copy-Item -LiteralPath (Join-Path $script:PackageRoot $entry.path) -Destination $target
}
Copy-Item -LiteralPath (Join-Path $script:PackageRoot 'deployment\manifest.json') -Destination "$script:AppRoot\deployment\manifest.json"
& py -3.12 -m venv $script:VenvRoot
if ($LASTEXITCODE -ne 0) { throw 'VENV_CREATION_FAILED' }
& "$script:VenvRoot\Scripts\python.exe" -m pip install --no-index --find-links $Wheelhouse -r "$script:AppRoot\requirements.txt"
if ($LASTEXITCODE -ne 0) { throw 'OFFLINE_DEPENDENCY_INSTALL_FAILED' }
& "$script:VenvRoot\Scripts\python.exe" -m pip check
if ($LASTEXITCODE -ne 0) { throw 'DEPENDENCY_CHECK_FAILED' }
$null = Get-Manifest $script:AppRoot
Write-Output 'CC03_INSTALLED_SOURCE_POLICY_UNAPPROVED'
