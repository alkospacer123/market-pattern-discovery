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
# venv's ensurepip child does not inherit -I/-B. Scrub its Python inputs too.
$pythonEnvironment = @{}
foreach ($item in @(Get-ChildItem Env:PYTHON*)) { $pythonEnvironment[$item.Name] = $item.Value; Remove-Item -LiteralPath ('Env:'+$item.Name) }
$env:PYTHONDONTWRITEBYTECODE = '1'
$env:PYTHONNOUSERSITE = '1'
$venvLauncher = [Environment]::GetEnvironmentVariable('__PYVENV_LAUNCHER__')
[Environment]::SetEnvironmentVariable('__PYVENV_LAUNCHER__',$null,'Process')
$installLocationPushed = $false
$savedTemp = $env:TEMP
$savedTmp = $env:TMP
$savedTmpDir = [Environment]::GetEnvironmentVariable('TMPDIR')
$installTemp = Join-Path $script:VenvRoot '.install-temp'
try {
    # venv/ensurepip/pip scratch writes are confined to this own empty CC root.
    $null = New-Item -ItemType Directory -Path $installTemp
    $env:TEMP = $installTemp
    $env:TMP = $installTemp
    $env:TMPDIR = $installTemp
    foreach ($entry in $manifest.files) {
        $target = Join-Path $script:AppRoot $entry.path
        $null = New-Item -ItemType Directory -Force -Path (Split-Path $target -Parent)
        Copy-Item -LiteralPath (Join-Path $script:PackageRoot $entry.path) -Destination $target
    }
    Copy-Item -LiteralPath (Join-Path $script:PackageRoot 'deployment\manifest.json') -Destination "$script:AppRoot\deployment\manifest.json"
    Set-Content -LiteralPath "$script:VenvRoot\CC03-owned.txt" -Value 'CC03 independent venv only' -Encoding ASCII
    # A child launched with -m must never resolve ensurepip from caller CWD.
    Push-Location $script:AppRoot
    $installLocationPushed = $true
    & $script:BasePython -I -B -c "import os,sys,tempfile; actual=tempfile.gettempdir(); assert os.path.normcase(actual)==os.path.normcase(sys.argv[1]); print('CC03_INSTALL_SCRATCH='+actual)" $installTemp
    if ($LASTEXITCODE -ne 0) { throw 'INSTALL_SCRATCH_OUTSIDE_CC_ROOT' }
    & $script:BasePython -I -B -m venv $script:VenvRoot
    if ($LASTEXITCODE -ne 0) { throw 'VENV_CREATION_FAILED' }
    & "$script:VenvRoot\Scripts\python.exe" -I -B -m pip --isolated install --no-index --no-cache-dir --only-binary=:all: --require-hashes --find-links $Wheelhouse -r "$script:AppRoot\requirements-windows.lock"
    if ($LASTEXITCODE -ne 0) { throw 'OFFLINE_DEPENDENCY_INSTALL_FAILED' }
    & "$script:VenvRoot\Scripts\python.exe" -I -B -m pip check
    if ($LASTEXITCODE -ne 0) { throw 'DEPENDENCY_CHECK_FAILED' }
    $null = Get-Manifest $script:AppRoot
    Assert-PanelVenv $PanelSid
    foreach ($item in (@(Get-PlainTree $installTemp) | Sort-Object { $_.FullName.Length } -Descending)) { Remove-Item -LiteralPath $item.FullName }
    Remove-Item -LiteralPath $installTemp
} catch {
    $failure = $_
    # Reject links before recursive traversal/deletion; retain roots and ACLs.
    $owned = @()
    foreach ($root in @($script:AppRoot,$script:VenvRoot)) { $owned += @(Get-PlainTree $root) }
    foreach ($item in ($owned | Sort-Object { $_.FullName.Length } -Descending)) { Remove-Item -LiteralPath $item.FullName }
    throw $failure
} finally {
    if ($installLocationPushed) { Pop-Location }
    foreach ($item in @(Get-ChildItem Env:PYTHON*)) { Remove-Item -LiteralPath ('Env:'+$item.Name) }
    foreach ($key in $pythonEnvironment.Keys) { [Environment]::SetEnvironmentVariable($key,$pythonEnvironment[$key],'Process') }
    [Environment]::SetEnvironmentVariable('__PYVENV_LAUNCHER__',$venvLauncher,'Process')
    $env:TEMP = $savedTemp
    $env:TMP = $savedTmp
    [Environment]::SetEnvironmentVariable('TMPDIR',$savedTmpDir,'Process')
    foreach ($item in @(Get-ChildItem Env:PIP_*)) { Remove-Item -LiteralPath ('Env:'+$item.Name) }
    foreach ($key in $pipEnvironment.Keys) { [Environment]::SetEnvironmentVariable($key,$pipEnvironment[$key],'Process') }
}
Write-Output 'CC03_INSTALLED_SOURCE_POLICY_UNAPPROVED'
