[CmdletBinding()]
param([switch]$Execute, [string]$PanelSid, [string]$Wheelhouse)
. "$PSScriptRoot\Common.ps1"
if (-not $Execute) { Write-Output 'PREVIEW: copy manifest files into empty C:\Control Center\app; create C:\Control Center\venv; install offline wheels. No ACL/Task/H1 changes.'; return }
if (-not ([Security.Principal.WindowsPrincipal][Security.Principal.WindowsIdentity]::GetCurrent()).IsInRole([Security.Principal.SecurityIdentifier]::new('S-1-5-32-544'))) { throw 'B_ADMIN_INSTALL_TOKEN_REQUIRED' }
& "$PSScriptRoot\Preflight.ps1" -Execute -PanelSid $PanelSid -Wheelhouse $Wheelhouse
foreach ($root in @($script:AppRoot,$script:VenvRoot)) {
    if (@(Get-ChildItem -Force -LiteralPath $root).Count -ne 0) { throw 'EMPTY_CC_TARGET_REQUIRED' }
}
$manifest = Get-Manifest $script:PackageRoot
# Everything above is read-only. Rollback owns only initially empty app/venv.
$pipEnvironment = @{}
foreach ($item in @(Get-ChildItem Env:PIP_*)) { $pipEnvironment[$item.Name] = $item.Value; Remove-Item -LiteralPath ('Env:'+$item.Name) }
$env:PIP_CONFIG_FILE = 'NUL'
try {
    foreach ($entry in $manifest.files) {
        $target = Join-Path $script:AppRoot $entry.path
        $null = New-Item -ItemType Directory -Force -Path (Split-Path $target -Parent)
        Copy-Item -LiteralPath (Join-Path $script:PackageRoot $entry.path) -Destination $target
    }
    Copy-Item -LiteralPath (Join-Path $script:PackageRoot 'deployment\manifest.json') -Destination "$script:AppRoot\deployment\manifest.json"
    Set-Content -LiteralPath "$script:VenvRoot\CC03-owned.txt" -Value 'CC03 independent venv only' -Encoding ASCII
    & $script:BasePython -I -B -m venv $script:VenvRoot
    if ($LASTEXITCODE -ne 0) { throw 'VENV_CREATION_FAILED' }
    & "$script:VenvRoot\Scripts\python.exe" -I -B -m pip --isolated install --no-index --no-cache-dir --only-binary=:all: --require-hashes --find-links $Wheelhouse -r "$script:AppRoot\requirements-windows.lock"
    if ($LASTEXITCODE -ne 0) { throw 'OFFLINE_DEPENDENCY_INSTALL_FAILED' }
    & "$script:VenvRoot\Scripts\python.exe" -I -B -m pip check
    if ($LASTEXITCODE -ne 0) { throw 'DEPENDENCY_CHECK_FAILED' }
    $null = Get-Manifest $script:AppRoot
    Assert-PanelVenv $PanelSid
} catch {
    $failure = $_
    # Reject links before recursive traversal/deletion; retain roots and ACLs.
    $owned = @()
    foreach ($root in @($script:AppRoot,$script:VenvRoot)) { $owned += @(Get-PlainTree $root) }
    foreach ($item in ($owned | Sort-Object { $_.FullName.Length } -Descending)) { Remove-Item -LiteralPath $item.FullName }
    throw $failure
} finally {
    foreach ($item in @(Get-ChildItem Env:PIP_*)) { Remove-Item -LiteralPath ('Env:'+$item.Name) }
    foreach ($key in $pipEnvironment.Keys) { [Environment]::SetEnvironmentVariable($key,$pipEnvironment[$key],'Process') }
}
Write-Output 'CC03_INSTALLED_SOURCE_POLICY_UNAPPROVED'
