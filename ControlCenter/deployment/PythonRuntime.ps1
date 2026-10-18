# Validation only. Never stage Python, repair ACLs, use a launcher or registry.
# Included by Common.ps1; executing this file alone is a no-op preview.
. "$PSScriptRoot\PythonCoreArchive.ps1"
function Get-PlainTree([string]$Root) {
    Assert-PlainPath $Root
    foreach ($item in @(Get-ChildItem -Force -LiteralPath $Root)) {
        if ($item.Attributes -band [IO.FileAttributes]::ReparsePoint) { throw 'RUNTIME_REPARSE_FORBIDDEN' }
        $item
        if ($item.PSIsContainer) { Get-PlainTree $item.FullName }
    }
}

function Assert-TreeACL([string]$Path, [string]$PanelSid) {
    $acl = Get-Acl -LiteralPath $Path
    if ($acl.GetOwner([Security.Principal.SecurityIdentifier]).Value -notin @('S-1-5-18','S-1-5-32-544')) { throw 'RUNTIME_TRUSTED_OWNER_REQUIRED' }
    $read = $false
    $max = [int64]([Security.AccessControl.FileSystemRights]::ReadAndExecute -bor [Security.AccessControl.FileSystemRights]::Synchronize)
    foreach ($rule in $acl.GetAccessRules($true,$true,[Security.Principal.SecurityIdentifier])) {
        $sid = $rule.IdentityReference.Value
        if ($sid -notin @('S-1-5-18','S-1-5-32-544',$PanelSid) -or $rule.AccessControlType -ne 'Allow') { throw 'RUNTIME_UNTRUSTED_ACL' }
        if ($sid -eq $PanelSid) {
            if ([int64]$rule.FileSystemRights -band (-bnot $max)) { throw 'RUNTIME_PANEL_WRITE_FORBIDDEN' }
            if (($rule.FileSystemRights -band [Security.AccessControl.FileSystemRights]::ReadAndExecute) -eq [Security.AccessControl.FileSystemRights]::ReadAndExecute) { $read = $true }
        }
    }
    if (-not $read) { throw 'RUNTIME_PANEL_READ_REQUIRED' }
}

function Invoke-PythonProbe([string]$Python, [switch]$Venv) {
    # -I excludes user site, PYTHONHOME/PYTHONPATH and current directory. -B
    # prevents validation writing bytecode into the immutable base or venv.
    $probe = @'
import importlib, json, pathlib, struct, sys
base, expected, mode = map(str, sys.argv[1:])
norm = lambda x: str(pathlib.Path(x).resolve()).casefold()
assert sys.version_info[:3] == (3,12,10) and struct.calcsize('P') == 8, 'PYTHON_31210_X64_REQUIRED'
assert norm(sys.executable) == norm(expected), 'EXACT_EXECUTABLE_REQUIRED'
assert norm(sys.base_prefix) == norm(base), 'BASE_PREFIX_MISMATCH'
assert norm(sys._base_executable) == norm(pathlib.Path(base)/'python.exe'), 'BASE_EXECUTABLE_MISMATCH'
assert norm(sys.prefix) == norm(pathlib.Path(expected).parents[1] if mode == 'venv' else base), 'PREFIX_MISMATCH'
origins = {}
for name in ('encodings','ssl','venv','ensurepip') + (('streamlit','plotly','pip') if mode == 'venv' else ('pip',)):
    module = importlib.import_module(name)
    origin = norm(module.__file__)
    roots = (norm(base) + '\\', norm(sys.prefix) + '\\')
    assert origin.startswith(roots), 'MODULE_OUTSIDE_MANAGED_RUNTIME'
    origins[name] = origin
import ensurepip
bundled = list((pathlib.Path(base)/'Lib/ensurepip/_bundled').glob('pip-*.whl'))
assert len(bundled) == 1 and bundled[0].is_file(), 'BUNDLED_PIP_WHEEL_REQUIRED'
assert not any('\\users\\' in norm(p) for p in sys.path if p), 'PROFILE_DEPENDENCY_FORBIDDEN'
print(json.dumps(dict(executable=sys.executable,base_executable=sys._base_executable,
    base_prefix=sys.base_prefix,prefix=sys.prefix,version=list(sys.version_info[:3]),mode=mode,
    origins=origins,bundled_pip=str(bundled[0]),ensurepip_version=ensurepip.version())))
'@
    $mode = $(if ($Venv) { 'venv' } else { 'base' })
    & $Python -I -B -c $probe $script:BaseRoot $Python $mode
    if ($LASTEXITCODE -ne 0) { throw 'TRUSTED_PYTHON_PROBE_FAILED' }
}

function Assert-RuntimeBoundary([string]$PanelSid) {
    Assert-CCPanelSid $PanelSid
    foreach ($path in @($script:ControlCenterRoot,$script:RuntimeRoot)) { Assert-ACL $path $PanelSid 'app' }
    # Every intermediate ancestor must have the same protected owner/SID grants.
    $ancestor = [IO.DirectoryInfo]::new($script:ControlCenterRoot).Parent
    while ($null -ne $ancestor -and $null -ne $ancestor.Parent) {
        Assert-PlainPath $ancestor.FullName
        if (-not (Get-Acl -LiteralPath $ancestor.FullName).AreAccessRulesProtected) { throw 'UNPROTECTED_RUNTIME_ANCESTOR' }
        Assert-TreeACL $ancestor.FullName $PanelSid
        $ancestor = $ancestor.Parent
    }
    # Drive roots may grant Users CreateDirectories but never DeleteChild or
    # modification of existing protected children. Do not change system ACLs.
    $driveACL = Get-Acl -LiteralPath ([IO.Path]::GetPathRoot($script:ControlCenterRoot))
    if ($driveACL.GetOwner([Security.Principal.SecurityIdentifier]).Value -notin @('S-1-5-18','S-1-5-32-544','S-1-5-80-956008885-3418522649-1831038044-1853292631-2271478464')) { throw 'UNTRUSTED_DRIVE_OWNER' }
    foreach ($rule in $driveACL.GetAccessRules($true,$true,[Security.Principal.SecurityIdentifier])) {
        if (($rule.PropagationFlags -band [Security.AccessControl.PropagationFlags]::InheritOnly) -or $rule.AccessControlType -ne 'Allow') { continue }
        if ($rule.IdentityReference.Value -notin @('S-1-5-18','S-1-5-32-544') -and
            ($rule.FileSystemRights -band ([Security.AccessControl.FileSystemRights]::DeleteSubdirectoriesAndFiles -bor [Security.AccessControl.FileSystemRights]::ChangePermissions -bor [Security.AccessControl.FileSystemRights]::TakeOwnership))) { throw 'UNTRUSTED_DRIVE_MUTATION' }
    }
}

function Assert-SupportingPythonMedia([string]$Media, [string]$Digest) {
    Assert-PlainPath $Media
    if ($Digest -cnotmatch '^[a-f0-9]{64}$' -or
        (Get-FileHash -LiteralPath $Media -Algorithm SHA256).Hash.ToLowerInvariant() -cne $Digest) { throw 'RUNTIME_MEDIA_HASH_MISMATCH' }
    $signature = Get-AuthenticodeSignature -LiteralPath $Media
    if ($signature.Status -ne 'Valid' -or $signature.SignerCertificate.Subject -notmatch '(?:^|,\s*)O=Python Software Foundation(?:,|$)') { throw 'RUNTIME_MEDIA_SIGNATURE_INVALID' }
}

function Assert-TrustedBase([string]$PanelSid) {
    Assert-RuntimeBoundary $PanelSid
    if ($script:BasePython -ne (Join-Path $script:ControlCenterRoot 'runtime\python312\python.exe')) { throw 'BASE_PATH_NOT_ALLOWLISTED' }
    foreach ($path in @($script:BaseRoot,$script:RuntimeProvenance)) { Assert-ACL $path $PanelSid 'app' }
    $p = Get-Content -Raw -LiteralPath $script:RuntimeProvenance | ConvertFrom-Json
    if ($p.schema_id -cne 'cc03.python-base.v2' -or $p.b_only_approved -ne $true -or
        $p.release -cne 'CPython-3.12.10-amd64-full' -or $p.distribution_id -cne 'pythoncore-3.12-64' -or
        $p.source_uri -cne $script:PythonCoreUri -or $p.archive_sha256 -cne $script:PythonCoreHash -or
        $p.archive_size -ne $script:PythonCoreSize -or
        $p.supporting_media.source_uri -cne 'https://www.python.org/ftp/python/3.12.10/python-3.12.10-amd64.exe') { throw 'RUNTIME_PROVENANCE_REQUIRED' }
    # Supporting signed EXE is never represented as the source of extracted bytes.
    $media = Join-Path $script:RuntimeRoot 'python-3.12.10-amd64.exe'
    Assert-PlainPath $media
    Assert-TreeACL $media $PanelSid
    Assert-SupportingPythonMedia $media $p.supporting_media.sha256
    $zip = Join-Path $script:RuntimeRoot 'python-3.12.10-amd64.zip'
    Assert-PlainPath $zip
    Assert-TreeACL $zip $PanelSid
    $stream = [IO.File]::Open($zip,[IO.FileMode]::Open,[IO.FileAccess]::Read,[IO.FileShare]::Read)
    try { $inventory = @(Get-PythonCoreInventory $stream) } finally { $stream.Dispose() }
    Assert-PythonCoreManifest $p.files $inventory
    $tree = @(Get-PlainTree $script:BaseRoot)
    $files = @($tree | Where-Object { -not $_.PSIsContainer })
    $seen = @{}
    foreach ($entry in $p.files) {
        if ($entry.path -notmatch '^[A-Za-z0-9_./+ -]+$' -or $entry.path.Contains('..') -or
            $entry.path.StartsWith('/') -or $seen.ContainsKey($entry.path) -or $entry.sha256 -cnotmatch '^[a-f0-9]{64}$') { throw 'RUNTIME_MANIFEST_INVALID' }
        $seen[$entry.path] = $entry.sha256
    }
    foreach ($required in @('python.exe','python312.dll','Lib/encodings/__init__.py','Lib/venv/__init__.py','Lib/ensurepip/__init__.py')) {
        if (-not $seen.ContainsKey($required)) { throw 'FULL_CPYTHON_REQUIRED' }
    }
    if ($files.Count -ne $seen.Count) { throw 'RUNTIME_FILE_SET_MISMATCH' }
    foreach ($item in $tree) {
        Assert-TreeACL $item.FullName $PanelSid
        if (-not $item.PSIsContainer) {
            $relative = $item.FullName.Substring($script:BaseRoot.Length+1).Replace('\','/')
            if (-not $seen.ContainsKey($relative) -or (Get-FileHash -LiteralPath $item.FullName -Algorithm SHA256).Hash.ToLowerInvariant() -cne $seen[$relative]) { throw 'RUNTIME_HASH_MISMATCH' }
        }
    }
    if (Test-Path -LiteralPath "$script:BaseRoot\pyvenv.cfg") { throw 'FULL_BASE_NOT_VENV_REQUIRED' }
    if (@($files | Where-Object { $_.Name -like '*._pth' }).Count) { throw 'EMBEDDABLE_BASE_FORBIDDEN' }
    Invoke-PythonProbe $script:BasePython
}

function Assert-PanelVenv([string]$PanelSid) {
    Assert-TrustedBase $PanelSid
    Assert-ACL $script:VenvRoot $PanelSid 'venv'
    $tree = @(Get-PlainTree $script:VenvRoot)
    foreach ($item in $tree) { Assert-TreeACL $item.FullName $PanelSid }
    $cfg = @{}
    foreach ($line in (Get-Content -LiteralPath "$script:VenvRoot\pyvenv.cfg")) {
        if ($line -notmatch '^([^=]+?)\s*=\s*(.+)$' -or $cfg.ContainsKey($Matches[1].Trim())) { throw 'VENV_CONFIG_INVALID' }
        $cfg[$Matches[1].Trim()] = $Matches[2].Trim()
    }
    if ($cfg['home'] -ne $script:BaseRoot -or $cfg['executable'] -ne $script:BasePython -or
        $cfg['version'] -ne '3.12.10' -or $cfg['include-system-site-packages'] -ne 'false') { throw 'VENV_BASE_BINDING_INVALID' }
    Invoke-PythonProbe "$script:VenvRoot\Scripts\python.exe" -Venv
}

function Assert-OfflineWheels([string]$Wheelhouse, [string]$PanelSid) {
    if ([string]::IsNullOrWhiteSpace($Wheelhouse)) { throw 'OFFLINE_WHEELHOUSE_REQUIRED' }
    Assert-PlainPath $Wheelhouse
    $tree = @(Get-PlainTree $Wheelhouse)
    foreach ($item in $tree) { Assert-PlainPath $item.FullName }
    $manifestPath = Join-Path $Wheelhouse 'wheels.sha256.json'
    Assert-PlainPath $manifestPath
    $records = Get-Content -Raw -LiteralPath $manifestPath | ConvertFrom-Json
    $seen = @{}
    foreach ($wheel in $records) {
        if ($wheel.name -notmatch '^[A-Za-z0-9_.+-]+\.whl$' -or $seen.ContainsKey($wheel.name)) { throw 'WHEEL_NAME_INVALID' }
        $seen[$wheel.name] = $true
        if ((Get-FileHash -LiteralPath (Join-Path $Wheelhouse $wheel.name) -Algorithm SHA256).Hash.ToLowerInvariant() -cne $wheel.sha256) { throw 'WHEEL_HASH_MISMATCH' }
    }
    if ($seen.Count -eq 0 -or @($tree | Where-Object { $_.Extension -eq '.whl' }).Count -ne $seen.Count) { throw 'UNLISTED_OR_MISSING_WHEEL' }
    # The reviewed lock authenticates bytes and complete dependency closure.
    # This fixed helper reads ZIP metadata only; it makes zero install/temp writes.
    & $script:BasePython -I -B "$script:PackageRoot\deployment\check_wheels.py" $Wheelhouse "$script:PackageRoot\requirements-windows.lock" "$script:PackageRoot\requirements.txt"
    if ($LASTEXITCODE -ne 0) { throw 'OFFLINE_PINNED_WHEELS_REQUIRED' }
}
