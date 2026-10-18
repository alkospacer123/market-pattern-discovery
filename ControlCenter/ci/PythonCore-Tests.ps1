# Dot-sourced by Windows-Rehearsal only, using its disposable ccpanel and roots.
if ($env:GITHUB_ACTIONS -cne 'true' -or $env:RUNNER_ENVIRONMENT -cne 'github-hosted') { throw 'GITHUB_HOSTED_VM_REQUIRED' }
$inputRoot = Join-Path $sandbox 'pythoncore-input'
$null = New-Item -ItemType Directory -Path $inputRoot,$script:RuntimeRoot
Set-DisposableACL $inputRoot 'app'
Set-DisposableACL $script:RuntimeRoot 'app'
$sourceZip = Join-Path $inputRoot 'python-3.12.10-amd64.zip'
$sourceMedia = Join-Path $inputRoot 'python-3.12.10-amd64.exe'
$indexUri = 'https://www.python.org/ftp/python/3.12.10/windows-3.12.10.json'
$indexPath = Join-Path $inputRoot 'windows-3.12.10.json'
Invoke-WebRequest -UseBasicParsing -Uri $indexUri -OutFile $indexPath
$index = Get-Content -Raw -LiteralPath $indexPath | ConvertFrom-Json
$distribution = @($index.versions | Where-Object { $_.id -ceq 'pythoncore-3.12-64' })
if ($distribution.Count -ne 1 -or $distribution[0].url -cne $script:PythonCoreUri -or
    $distribution[0].hash.sha256 -cne $script:PythonCoreHash -or $distribution[0].'sort-version' -cne '3.12.10') { throw 'OFFICIAL_PSF_INDEX_MISMATCH' }
Invoke-WebRequest -UseBasicParsing -Uri $script:PythonCoreUri -OutFile $sourceZip
Invoke-WebRequest -UseBasicParsing -Uri 'https://www.python.org/ftp/python/3.12.10/python-3.12.10-amd64.exe' -OutFile $sourceMedia
foreach ($path in @($sourceZip,$sourceMedia,$indexPath)) { Set-DisposableACL $path 'app' }
Copy-Item -LiteralPath $indexPath -Destination "$evidence\official-windows-3.12.10.json"
$approvalPath = Join-Path $script:DataRoot 'private\pythoncore-b-approval.json'
$approval = @{schema_id='cc03.pythoncore-b-approval.v1';b_execution_approved=$true;
    seal_fresh_cc_files_approved=$true;panel_sid=$panelSid;archive_sha256=$script:PythonCoreHash;
    package_manifest_sha256=(Get-FileHash -LiteralPath "$package\deployment\manifest.json" -Algorithm SHA256).Hash.ToLowerInvariant();
    supporting_media_sha256=(Get-FileHash -LiteralPath $sourceMedia -Algorithm SHA256).Hash.ToLowerInvariant();
    review_reference='DISPOSABLE HOSTED CI ONLY - NOT INTEL APPROVAL'}
function Save-TestApproval {
    $approval | ConvertTo-Json | Set-Content -LiteralPath $approvalPath -Encoding ASCII
    Set-DisposableACL $approvalPath 'private'
}
Save-TestApproval
function Invoke-TestProvision([string]$ZipPath = $sourceZip, [string]$MediaPath = $sourceMedia) {
    & "$package\deployment\Provision-PythonCore.ps1" -Execute -SealFreshCCFiles -PanelSid $panelSid -Archive $ZipPath -SupportingMedia $MediaPath
}
function Assert-EmptyPythonTargets {
    foreach ($root in @($script:RuntimeRoot,$script:AppRoot,$script:VenvRoot)) {
        if (@(Get-ChildItem -Force -LiteralPath $root).Count) { throw 'PROVISION_NEGATIVE_WROTE_TARGET' }
    }
}
& "$package\deployment\Provision-PythonCore.ps1"
Assert-EmptyPythonTargets
$identityScript = Join-Path $sandbox 'provision-standard-token.ps1'
$entryLiteral = (Join-Path $package 'deployment\Provision-PythonCore.ps1').Replace("'","''")
@"
`$ErrorActionPreference='Stop'
try { & '$entryLiteral' -Execute -SealFreshCCFiles -PanelSid '$panelSid' }
catch { if (`$_.Exception.Message -like '*B_ADMIN_INSTALL_TOKEN_REQUIRED*') { Write-Output 'STANDARD_CCPANEL_PROVISION_REJECTED'; exit 0 }; throw }
throw 'STANDARD_TOKEN_PROVISION_NOT_REJECTED'
"@ | Set-Content -LiteralPath $identityScript -Encoding UTF8
Set-DisposableACL $identityScript 'app'
$identityLog = Join-Path $script:DataRoot 'logs\provision-standard-token.txt'
$identityProcess = [CC03Access]::StartAs($panel.Name,$panel.Password,(Join-Path $env:SYSTEMROOT 'System32\WindowsPowerShell\v1.0\powershell.exe'),$identityScript,$sandbox,$identityLog,$panelSid)
try {
    if (-not $identityProcess.WaitForExit(30000) -or $identityProcess.ExitCode -ne 0) { throw 'STANDARD_TOKEN_NEGATIVE_FAILED' }
} finally { if (-not $identityProcess.HasExited) { & taskkill.exe /PID $identityProcess.Id /T /F }; $identityProcess.Dispose() }
$results['pythoncore_standard_token'] = 'PASS: real standard ccpanel process cannot execute B provisioning; administrator token required'
Expect-Failure { & "$package\deployment\Provision-PythonCore.ps1" -Execute -PanelSid $panelSid } 'DISTINCT_FRESH_CC_SEAL_APPROVAL_REQUIRED'
$approval.b_execution_approved = $false; Save-TestApproval
Expect-Failure { Invoke-TestProvision } 'INDEPENDENT_B_APPROVAL_REQUIRED'
$approval.b_execution_approved = $true; Save-TestApproval
$broken = Join-Path $inputRoot 'corrupt.zip'
Copy-Item -LiteralPath $sourceZip -Destination $broken
$stream = [IO.File]::OpenWrite($broken)
try { $stream.Position=0; $stream.WriteByte(0) } finally { $stream.Dispose() }
Expect-Failure { Invoke-TestProvision $broken } 'ZIP_HASH_MISMATCH'
Remove-Item -LiteralPath $broken
$savedRuntimeACL = Get-Acl -LiteralPath $script:RuntimeRoot
Set-DisposableACL $script:RuntimeRoot 'private'
Expect-Failure { Invoke-TestProvision } 'CCPANEL_READ_RULE_REQUIRED'
Set-Acl -LiteralPath $script:RuntimeRoot -AclObject $savedRuntimeACL
$actualMediaHash = $approval.supporting_media_sha256
$approval.supporting_media_sha256 = '1'*64; Save-TestApproval
Expect-Failure { Invoke-TestProvision } 'RUNTIME_MEDIA_HASH_MISMATCH'
$badMedia = Join-Path $inputRoot 'unsigned.exe'
Set-Content -LiteralPath $badMedia -Value 'NOT AN EXE' -Encoding ASCII
$approval.supporting_media_sha256 = (Get-FileHash -LiteralPath $badMedia -Algorithm SHA256).Hash.ToLowerInvariant(); Save-TestApproval
Expect-Failure { Invoke-TestProvision $sourceZip $badMedia } 'RUNTIME_MEDIA_SIGNATURE_INVALID'
Remove-Item -LiteralPath $badMedia
$approval.supporting_media_sha256 = $actualMediaHash; Save-TestApproval
Assert-EmptyPythonTargets

# Adversarial central-directory inputs exercise the actual parser; production
# still requires the immutable official ZIP size/hash before this parser runs.
function Test-ArchiveRejection([string[]]$Names, [int]$Attributes, [string]$Expected) {
    $memory = [IO.MemoryStream]::new()
    try {
        $writer = [IO.Compression.ZipArchive]::new($memory,[IO.Compression.ZipArchiveMode]::Create,$true)
        foreach ($name in $Names) {
            $entry = $writer.CreateEntry($name)
            $entry.ExternalAttributes = $Attributes
            $data = $entry.Open(); $data.WriteByte(65); $data.Dispose()
        }
        $writer.Dispose(); $memory.Position=0
        $reader = [IO.Compression.ZipArchive]::new($memory,[IO.Compression.ZipArchiveMode]::Read,$true)
        try { Expect-Failure { Get-PythonCoreEntries $reader } $Expected } finally { $reader.Dispose() }
    } finally { $memory.Dispose() }
}
Add-Type -AssemblyName System.IO.Compression
foreach ($name in @('../escape','C:/escape','/absolute','file:ads','dir\escape','bad?.txt')) {
    Test-ArchiveRejection @($name) 0 'ZIP_'
}
foreach ($name in @('NUL.txt','CON','aux/x','COM1','x.','x /y')) { Test-ArchiveRejection @($name) 0 'ZIP_NTFS_NAME_FORBIDDEN' }
Test-ArchiveRejection @('Lib/a','Lib/a') 0 'ZIP_DUPLICATE_OR_CASE_COLLISION'
Test-ArchiveRejection @('Lib/a','lib/B') 0 'ZIP_PATH_COLLISION'
Test-ArchiveRejection @('Lib','Lib/a') 0 'ZIP_PATH_COLLISION'
Test-ArchiveRejection @('link') ([int](0xA000 -shl 16)) 'ZIP_LINK_OR_SPECIAL_FORBIDDEN'
Test-ArchiveRejection @('link') 0x400 'ZIP_LINK_OR_SPECIAL_FORBIDDEN'
$results['pythoncore_archive_negatives'] = 'PASS: corrupt pinned ZIP, unsigned/wrong supporting media, no B/seal approval, incomplete ACL, zip slip/drive/ADS/NTFS/duplicate/case/file-directory/symlink/reparse inputs; no target writes'

# Two real transaction faults. No production test hooks or unpinned runtime mode.
$faultState = @{count=0}
$fault = {
    param($LiteralPath,$Algorithm)
    if ($LiteralPath -like '*\python312\*') {
        $faultState.count++
        if ($faultState.count -eq 2) { throw 'DISPOSABLE_EXTRACTION_FAULT' }
    }
    Microsoft.PowerShell.Utility\Get-FileHash -LiteralPath $LiteralPath -Algorithm $Algorithm
}.GetNewClosure()
Set-Item -LiteralPath Function:Get-FileHash -Value $fault
try { Expect-Failure { Invoke-TestProvision } 'DISPOSABLE_EXTRACTION_FAULT' }
finally { Remove-Item Function:Get-FileHash }
Assert-EmptyPythonTargets
$sealFault = { param($LiteralPath,$AclObject) throw 'DISPOSABLE_SEAL_FAULT' }
Set-Item -LiteralPath Function:Set-Acl -Value $sealFault
try { Expect-Failure { Invoke-TestProvision } 'DISPOSABLE_SEAL_FAULT' }
finally { Remove-Item Function:Set-Acl }
Assert-EmptyPythonTargets
$results['pythoncore_provision_rollback'] = 'PASS: extracted file 2 and sealing faults remove only fresh transaction paths; existing roots, inputs and private approval retained'
Invoke-TestProvision
$provenance = Get-Content -Raw -LiteralPath $script:RuntimeProvenance | ConvertFrom-Json
Copy-Item -LiteralPath $script:RuntimeProvenance -Destination "$evidence\python-base-provenance.json"
Assert-TrustedBase $panelSid
$results['pythoncore_runtime'] = 'PASS: official full ZIP 3845 exact files; archive/manifest/tree hash and PSF supporting signature; real -I -B CPython 3.12.10 x64 with executable/base_prefix/ssl/venv/ensurepip/pip origins'
# This runtime came from ZIP, not setup-python. All later install, ccpanel and
# transport/ETW/500-replace suites continue unchanged against these exact bytes.
