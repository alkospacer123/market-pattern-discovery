# R070 / 17 Nov 2026: assemble full EXT2 + TP6/Protect3 + FINAM-read fix
# WITHOUT FINAM access, Task modification, live code changes or re-ARM.
# Source SHA-pinned via GitHub blob API, all seven patches applied together.
[CmdletBinding()]
param([ValidateSet('prepare','verify')][string]$mode='prepare')
$ErrorActionPreference='Stop'
Set-StrictMode -Version Latest
$root='c:\v20lab'
$branchCommit='eb54e19e04f8c70165b2276e399d9c76c7dceaeb'
$package=Join-Path $root 'r070-candidate\release-20261117-all3'
$stage=Join-Path $package 'staged'
$liveDir=Join-Path $root 'pretrade-08\live-runtime-08\V20_TradingSystem_M15\v20_runtime'
$origLive='b80fb9eb135f7cdcb4c78337e2b808c4d7135195'
$origExecution='6b600451178b42bd4f8b2037995e7db3a9ad27c8'
$expectedLive='0c25db6d1223a39bcd0a5f28eccb738ef96931ab'
$expectedExecution='05dfd4d0fe5210fdd8cf7e933c556a3d439dbc6b'
$base='V20_TradingSystem_M15/v20_runtime/'
$patchBase='V20_TradingSystem_M15/V20-08/'
$files=[ordered]@{
  'V20_TradingSystem_M15/v20_runtime/finam_live.py'=$origLive
  'V20_TradingSystem_M15/v20_runtime/finam_execution.py'=$origExecution
  'V20_TradingSystem_M15/v20_runtime/tp6_protect3.py'='a578cac629350f2c9fe3409121ac085c8a41eb63'
  'V20_TradingSystem_M15/v20_runtime/ext2_r060.py'='60ab3e16cda819d785e7763ca17a8e74a8a30e04'
  'V20_TradingSystem_M15/v20_runtime/ext2_history_bridge.py'='1045555cb423542dec2568496c7366b1749a9761'
  'V20_TradingSystem_M15/v20_runtime/r070_candidate_entry.py'='59e9405d8fed88cc18be6676a298d1faaa27afc8'
  'V20_TradingSystem_M15/v20_runtime/r070_m15_checkpoint.py'='8923b1614c00f9c84b9f5e62c728b1447778c146'
  'V20_TradingSystem_M15/v20_runtime/r070_m15_candidate_state.py'='680fb9f1aad165b70f54c3cc3122a98fef0a753e'
  'V20_TradingSystem_M15/v20_runtime/r070_linked_sltp.py'='864d03d8fe467138adf73c6e6216a88fc81e8c21'
  'V20_TradingSystem_M15/V20-08/r070-tp6-one-shot-candidate.patch'='c1947f59ab68884fd6543c40d64892d6a899f225'
  'V20_TradingSystem_M15/V20-08/r070-protect3-flat-cleanup-candidate.patch'='b7d3eb587e97d4012cc21a593f2d8b605e431611'
  'V20_TradingSystem_M15/V20-08/r070-protect3-broker-id-readonly-candidate.patch'='4d975f8d2d4b701b48205f9ad24c0d49e45c9c4e'
  'V20_TradingSystem_M15/V20-08/r070-protect3-live-trigger-candidate.patch'='0e378d0197815556cdd99ac8e1d6c20d1c05a056'
  'V20_TradingSystem_M15/V20-08/r070-protect3-night-monitor-candidate.patch'='05dffdaaaed6359b0a78116adac9364dd2bdcc34'
  'V20_TradingSystem_M15/V20-08/r070-ext2-pre-intent-candidate.patch'='53a07245857b79c53e1710eeca37b70f768d903d'
  'V20_TradingSystem_M15/V20-08/r070-finam-get-incomplete-read-candidate.patch'='fabfa58e9d84553fe0c51833530cb90d89412e85'
}
$patchNames=@(
 'r070-tp6-one-shot-candidate.patch',
 'r070-protect3-flat-cleanup-candidate.patch',
 'r070-protect3-broker-id-readonly-candidate.patch',
 'r070-protect3-live-trigger-candidate.patch',
 'r070-protect3-night-monitor-candidate.patch',
 'r070-ext2-pre-intent-candidate.patch',
 'r070-finam-get-incomplete-read-candidate.patch'
)
function need([bool]$valid,[string]$code){if(-not $valid){throw $code}}
function git-hash([string]$file) {
    need (Test-Path -LiteralPath $file -PathType Leaf) 'R070_PKG_FILE_MISSING'
    need (-not ((Get-Item -LiteralPath $file -Force).Attributes -band [io.fileattributes]::ReparsePoint)) 'R070_PKG_FILE_LINK'
    $hash=(& git.exe hash-object -- $file).Trim().ToLowerInvariant()
    need ($LASTEXITCODE -eq 0 -and $hash -match '^[0-9a-f]{40}$') 'R070_PKG_GIT_HASH_FAILED'
    return $hash
}
function exact([string]$path,[string]$sha) {
    need ((git-hash $path) -ceq $sha) 'R070_PKG_SHA_MISMATCH'
}
function get-pin([string]$rel,[string]$sha,[string]$dest) {
    if(Test-Path -LiteralPath $dest){exact $dest $sha;return}
    $uri='https://api.github.com/repos/alkospacer123/market-pattern-discovery/git/blobs/'+$sha
    $x=Invoke-RestMethod -Uri $uri -Headers @{'user-agent'='v20lab-r070'} -TimeoutSec 30
    need ($x.sha -ceq $sha -and $x.encoding -eq 'base64') 'R070_PKG_BLOB_IDENTITY_FAILED'
    $bytes=[convert]::frombase64string([string]$x.content)
    $parent=Split-Path -Path $dest -Parent
    [io.directory]::CreateDirectory($parent)|Out-Null
    [io.file]::WriteAllBytes($dest,$bytes)
    exact $dest $sha
}
need ($env:OS -eq 'Windows_NT' -and $env:COMPUTERNAME -eq 'URIU-PC') 'R070_PKG_INTEL_ONLY'
need (Test-Path -LiteralPath $liveDir -PathType Container) 'R070_PKG_LIVE_RUNTIME_NOT_FOUND'
exact (Join-Path $liveDir 'finam_live.py') $origLive
exact (Join-Path $liveDir 'finam_execution.py') $origExecution
# Package staging does not demand a live broker query. The owner has already
# proved all three accounts flat on the separate 17-Nov GET-only incident ZIP.
if($mode -eq 'verify') {
    Write-Output 'R070_PKG_INSTALLED_ORIGINAL_LIVE_PINS=PASS'
    if(Test-Path -LiteralPath $package){Write-Output 'R070_PKG_STAGING_DIR_EXISTS=YES'}
    Write-Output 'R070_PKG_NO_FINAM_NO_TASK_MUTATION_NO_ORDER_NO_REARM=YES'
    return
}
if(Test-Path -LiteralPath $package){
    need (Test-Path -LiteralPath $stage -PathType Container) 'R070_PKG_EXISTING_DIRECTORY_UNTRUSTED'
    need (-not (Test-Path -LiteralPath ($package+'.zip'))) 'R070_PKG_ALREADY_PREPARED_NO_REPEAT'
    need (-not (Test-Path -LiteralPath (Join-Path $package 'manifest.json'))) 'R070_PKG_MANIFEST_ALREADY_EXISTS'
} else {
    [io.directory]::CreateDirectory($stage)|Out-Null
}
$success=$false
try {
    foreach($pair in $files.GetEnumerator()){
        $target=Join-Path $stage ($pair.Key.Replace('/','\'))
        get-pin $pair.Key $pair.Value $target
    }
    Push-Location $stage
    try {
        foreach($name in $patchNames){
            $p=Join-Path $stage (($patchBase+$name).Replace('/','\'))
            & git.exe apply --check -- $p
            need ($LASTEXITCODE -eq 0) ('R070_PKG_PATCH_CONFLICT_'+$name)
            & git.exe apply -- $p
            need ($LASTEXITCODE -eq 0) ('R070_PKG_PATCH_APPLY_FAILED_'+$name)
        }
    } finally {Pop-Location}
    $finalLive=git-hash (Join-Path $stage (($base+'finam_live.py').Replace('/','\')))
    $finalExecution=git-hash (Join-Path $stage (($base+'finam_execution.py').Replace('/','\')))
    need ($finalLive -ceq $expectedLive -and $finalExecution -ceq $expectedExecution) 'R070_PKG_FINAL_COMBINED_SHA_INVALID'
    $manifest=[ordered]@{
       schema='v20.r070.20261117.full_staged_bundle.v1'
       status='STAGED_NOT_INSTALLED_NO_LIVE_APPROVAL'
       source_commit=$branchCommit
       package_files_git_sha=$files
       patched_live_git_sha=$finalLive
       patched_execution_git_sha=$finalExecution
       windows_test='44092904281'
       installation='NOT_EXECUTED'
       auto_arm=$false
       finam_requests=0
       orders_sent=0
       original_live_pins_verified=$true
       unresolved_physical_gates=@(
         'R070_EXT2_ACCOUNT_BOUND_HISTORY_AND_FRESH_FINAM_M15'
         'R070_USDRUBF_GLDRUBF_M15_GAPS'
         'R070_PROTECT3_RELEASE_AUTHORIZATION_AND_BROKER_REPLACEMENT'
         'R070_LIVE_LAUNCHER_NEW_SOURCE_AND_SHA_CUTOVER'
       )
    }
    $manifestPath=Join-Path $package 'manifest.json'
    [io.file]::WriteAllText($manifestPath,($manifest|ConvertTo-Json -Depth 8),[text.utf8encoding]::new($false))
    $targetZip=$package+'.zip'
    need (-not (Test-Path -LiteralPath $targetZip)) 'R070_PKG_ZIP_EXISTS'
    Copy-Item -LiteralPath $PSCommandPath -Destination (Join-Path $package 'r070-20261117-prepare-full-package.ps1') -ErrorAction Stop
    Compress-Archive -Path (Join-Path $package '*') -DestinationPath $targetZip -CompressionLevel Optimal
    need (Test-Path -LiteralPath $targetZip -PathType Leaf) 'R070_PKG_ZIP_MISSING'
    $digest=(Get-FileHash -LiteralPath $targetZip -Algorithm SHA256).Hash.ToLowerInvariant()
    Write-Output ('R070_PKG_FULL_STAGED=PASS_7_PATCHES '+$targetZip)
    Write-Output ('R070_PKG_ZIP_SHA256='+$digest)
    Write-Output ('R070_PKG_DERIVED_LIVE_SHA='+$finalLive)
    Write-Output ('R070_PKG_DERIVED_EXEC_SHA='+$finalExecution)
    Write-Output 'R070_PKG_NOT_INSTALLED_NOT_REARMED_NO_FINAM=YES'
    $success=$true
} finally {
    if(-not $success) {Write-Output 'R070_PKG_PREPARATION_HOLD_NO_LIVE_CHANGES'}
}
