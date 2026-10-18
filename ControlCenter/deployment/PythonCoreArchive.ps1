# Pure offline archive inspection. No extraction, Python execution or ACL writes.
$script:PythonCoreUri = 'https://www.python.org/ftp/python/3.12.10/python-3.12.10-amd64.zip'
$script:PythonCoreHash = '8649692de846c56a7189d6dae5c322ab20deb1b5908b6f39426b62a36f39415d'
$script:PythonCoreSize = 32399361
$script:PythonCoreInventory = $null

function Assert-PythonCoreName([string]$Name) {
    if ([string]::IsNullOrWhiteSpace($Name) -or $Name.Length -gt 220 -or
        $Name -cnotmatch '^[A-Za-z0-9_./+ -]+$' -or $Name.StartsWith('/')) { throw 'ZIP_UNSAFE_NAME' }
    foreach ($part in $Name.Split('/')) {
        if ($part -in @('','.','..') -or $part.EndsWith('.') -or $part.EndsWith(' ') -or
            $part -match '^(CON|PRN|AUX|NUL|COM[0-9]|LPT[0-9])(?:\.|$)') { throw 'ZIP_NTFS_NAME_FORBIDDEN' }
    }
}

function Get-StreamSHA256([IO.Stream]$Stream) {
    $hash = [Security.Cryptography.SHA256]::Create()
    try { return ([BitConverter]::ToString($hash.ComputeHash($Stream))).Replace('-','').ToLowerInvariant() }
    finally { $hash.Dispose() }
}

function Get-PythonCoreEntries($Archive) {
    # Also used directly by native malicious-ZIP tests, without weakening pins.
    $seen = @{}; $nodes = @{}; $records = @()
    foreach ($entry in $Archive.Entries) {
        $directory = $entry.FullName.EndsWith('/')
        $name = $entry.FullName.TrimEnd('/')
        Assert-PythonCoreName $name
        if ($seen.ContainsKey($name)) { throw 'ZIP_DUPLICATE_OR_CASE_COLLISION' }
        $seen[$name] = $true
        $unixType = ($entry.ExternalAttributes -shr 16) -band 0xF000
        if ($unixType -notin @(0,0x8000,0x4000) -or
            ($entry.ExternalAttributes -band 0x400) -or
            ($unixType -eq 0x4000 -and -not $directory)) { throw 'ZIP_LINK_OR_SPECIAL_FORBIDDEN' }
        $parts = $name.Split('/')
        for ($i=0; $i -lt $parts.Count; $i++) {
            $node = ($parts[0..$i] -join '/')
            $kind = $(if ($i -lt $parts.Count-1 -or $directory) { 'directory' } else { 'file' })
            if ($nodes.ContainsKey($node)) {
                if ($nodes[$node].name -cne $node -or $nodes[$node].kind -ne $kind -or $kind -eq 'file') { throw 'ZIP_PATH_COLLISION' }
            } else { $nodes[$node] = @{name=$node;kind=$kind} }
        }
        if ($directory) {
            if ($entry.Length -ne 0) { throw 'ZIP_DIRECTORY_WITH_DATA' }
            continue
        }
        if ($entry.Length -lt 0 -or $entry.Length -gt 100MB) { throw 'ZIP_ENTRY_SIZE_FORBIDDEN' }
        $stream = $entry.Open()
        try { $digest = Get-StreamSHA256 $stream } finally { $stream.Dispose() }
        $records += @{path=$name;sha256=$digest;size=[int64]$entry.Length}
    }
    return @($records | Sort-Object -Property path -CaseSensitive)
}

function Get-PythonCoreInventory([IO.Stream]$Stream) {
    if ($Stream.Length -ne $script:PythonCoreSize) { throw 'ZIP_SIZE_MISMATCH' }
    $Stream.Position = 0
    if ((Get-StreamSHA256 $Stream) -cne $script:PythonCoreHash) { throw 'ZIP_HASH_MISMATCH' }
    # Exact SHA-256 determines every entry byte. Rehash the held archive on EVERY
    # call; only avoid decompressing identical pinned bytes repeatedly within
    # this script invocation. No disk cache, no skipped source/tree validation.
    if ($null -ne $script:PythonCoreInventory) {
        return @($script:PythonCoreInventory | ForEach-Object { $_.Clone() })
    }
    $Stream.Position = 0
    Add-Type -AssemblyName System.IO.Compression
    $archive = [IO.Compression.ZipArchive]::new($Stream,[IO.Compression.ZipArchiveMode]::Read,$true)
    try { $records = @(Get-PythonCoreEntries $archive) } finally { $archive.Dispose() }
    if ($records.Count -ne 3845) { throw 'FULL_PYTHONCORE_FILE_COUNT_REQUIRED' }
    $names = @($records | ForEach-Object { $_.path })
    foreach ($name in @('python.exe','python312.dll','Lib/encodings/__init__.py',
                       'Lib/venv/__init__.py','Lib/ensurepip/__init__.py','Lib/site-packages/pip/__init__.py','Lib/ssl.py')) {
        if ($name -cnotin $names) { throw 'FULL_PYTHONCORE_REQUIRED' }
    }
    if (@($names | Where-Object { $_ -like 'Lib/ensurepip/_bundled/pip-*.whl' }).Count -ne 1 -or
        @($names | Where-Object { $_ -like '*._pth' -or $_ -eq 'pyvenv.cfg' }).Count) { throw 'FULL_PYTHONCORE_REQUIRED' }
    $script:PythonCoreInventory = @($records | ForEach-Object { $_.Clone() })
    return $records
}

function Assert-PythonCoreManifest($Expected, $Actual) {
    if (@($Expected).Count -ne @($Actual).Count) { throw 'RUNTIME_ARCHIVE_MANIFEST_MISMATCH' }
    $seen = @{}
    foreach ($entry in $Expected) {
        Assert-PythonCoreName $entry.path
        if ($seen.ContainsKey($entry.path) -or $entry.sha256 -cnotmatch '^[a-f0-9]{64}$') { throw 'RUNTIME_MANIFEST_INVALID' }
        $seen[$entry.path] = $entry
    }
    foreach ($entry in $Actual) {
        if (-not $seen.ContainsKey($entry.path) -or $seen[$entry.path].path -cne $entry.path -or
            $seen[$entry.path].sha256 -cne $entry.sha256 -or $seen[$entry.path].size -ne $entry.size) { throw 'RUNTIME_ARCHIVE_MANIFEST_MISMATCH' }
    }
}
