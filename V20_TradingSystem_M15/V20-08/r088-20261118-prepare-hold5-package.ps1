# R088 / 18 Nov 2026: prepare HOLD5 + account source binding on seven pinned R070 patches
# WITHOUT FINAM access, Task modification, live code changes or re-ARM.
# Source SHA-pinned via GitHub blob API, all nine patches applied together.
[CmdletBinding()]
param([ValidateSet('prepare','verify')][string]$mode='prepare')
$ErrorActionPreference='Stop'
Set-StrictMode -Version Latest
$root='c:\v20lab'
$branchCommit='2d46e5b99f6ce302c20b46783c80989b3ac1d642'
$package=Join-Path $root 'r088-candidate\release-20261118-hold5-all3-src4'
$stage=Join-Path $package 'staged'
$liveDir=Join-Path $root 'pretrade-08\live-runtime-08\V20_TradingSystem_M15\v20_runtime'
$origLive='b80fb9eb135f7cdcb4c78337e2b808c4d7135195'
$origExecution='6b600451178b42bd4f8b2037995e7db3a9ad27c8'
$expectedLive='e5e5fc765a6d846c914bb4f43af5df4ba7064abb'
$expectedExecution='0fc4c454d55f37e4e87fd74e3370cbc1ad83b53f'
$base='V20_TradingSystem_M15/v20_runtime/'
$patchBase='V20_TradingSystem_M15/V20-08/'
$files=[ordered]@{
  'V20_TradingSystem_M15/v20_runtime/finam_live.py'=$origLive
  'V20_TradingSystem_M15/v20_runtime/finam_execution.py'=$origExecution
  'V20_TradingSystem_M15/v20_runtime/tp6_protect3.py'='a578cac629350f2c9fe3409121ac085c8a41eb63'
  'V20_TradingSystem_M15/v20_runtime/ext2_r060.py'='60ab3e16cda819d785e7763ca17a8e74a8a30e04'
  'V20_TradingSystem_M15/v20_runtime/ext2_history_bridge.py'='1045555cb423542dec2568496c7366b1749a9761'
  'V20_TradingSystem_M15/v20_runtime/r070_candidate_entry.py'='b1a695f04b953299aba3134dfa31ff25e75236fa'
  'V20_TradingSystem_M15/v20_runtime/r070_m15_checkpoint.py'='8923b1614c00f9c84b9f5e62c728b1447778c146'
  'V20_TradingSystem_M15/v20_runtime/r070_m15_candidate_state.py'='81f25481b46753c7c54f138df8617a51f06f9a40'
  'V20_TradingSystem_M15/v20_runtime/r070_linked_sltp.py'='864d03d8fe467138adf73c6e6216a88fc81e8c21'
  'V20_TradingSystem_M15/v20_runtime/r088_hold5.py'='f0b9058707230299464f1f6fb5245653a022ec31'
  'V20_TradingSystem_M15/v20_runtime/r088_cny_verified_bootstrap.py'='0042f844bcd3ed37c5fc3499e6a634ccf21640fd'
  'V20_TradingSystem_M15/v20_runtime/r088_ext2_live_source.py'='888e30bfc94406ea8a6bb41439f2d5e7c5c595ec'
  'V20_TradingSystem_M15/V20-08/r070-tp6-one-shot-candidate.patch'='c1947f59ab68884fd6543c40d64892d6a899f225'
  'V20_TradingSystem_M15/V20-08/r070-protect3-flat-cleanup-candidate.patch'='b7d3eb587e97d4012cc21a593f2d8b605e431611'
  'V20_TradingSystem_M15/V20-08/r070-protect3-broker-id-readonly-candidate.patch'='4d975f8d2d4b701b48205f9ad24c0d49e45c9c4e'
  'V20_TradingSystem_M15/V20-08/r070-protect3-live-trigger-candidate.patch'='0e378d0197815556cdd99ac8e1d6c20d1c05a056'
  'V20_TradingSystem_M15/V20-08/r070-protect3-night-monitor-candidate.patch'='05dffdaaaed6359b0a78116adac9364dd2bdcc34'
  'V20_TradingSystem_M15/V20-08/r070-ext2-pre-intent-candidate.patch'='53a07245857b79c53e1710eeca37b70f768d903d'
  'V20_TradingSystem_M15/V20-08/r070-finam-get-incomplete-read-candidate.patch'='fabfa58e9d84553fe0c51833530cb90d89412e85'
  'V20_TradingSystem_M15/V20-08/r088-hold5-after-r070-combined-candidate.patch'='0c73f8265a1c7f75a1bc8f4b849e5970fe274bc4'
  'V20_TradingSystem_M15/V20-08/r088-ext2-live-source-after-combined-candidate.patch'='50f7ed23a8bee1d760c090113e12c68916cfa0d4'
}
$patchNames=@(
 'r070-tp6-one-shot-candidate.patch',
 'r070-protect3-flat-cleanup-candidate.patch',
 'r070-protect3-broker-id-readonly-candidate.patch',
 'r070-protect3-live-trigger-candidate.patch',
 'r070-protect3-night-monitor-candidate.patch',
 'r070-ext2-pre-intent-candidate.patch',
 'r070-finam-get-incomplete-read-candidate.patch',
 'r088-hold5-after-r070-combined-candidate.patch',
 'r088-ext2-live-source-after-combined-candidate.patch'
)
function need([bool]$valid,[string]$code){if(-not $valid){throw $code}}
function git-hash([string]$file) {
    need (Test-Path -LiteralPath $file -PathType Leaf) 'R088_PKG_FILE_MISSING'
    need (-not ((Get-Item -LiteralPath $file -Force).Attributes -band [io.fileattributes]::ReparsePoint)) 'R088_PKG_FILE_LINK'
    $hash=(& git.exe hash-object -- $file).Trim().ToLowerInvariant()
    need ($LASTEXITCODE -eq 0 -and $hash -match '^[0-9a-f]{40}$') 'R088_PKG_GIT_HASH_FAILED'
    return $hash
}
function exact([string]$path,[string]$sha) {
    need ((git-hash $path) -ceq $sha) 'R088_PKG_SHA_MISMATCH'
}
function get-pin([string]$rel,[string]$sha,[string]$dest) {
    if(Test-Path -LiteralPath $dest){exact $dest $sha;return}
    $uri='https://api.github.com/repos/alkospacer123/market-pattern-discovery/git/blobs/'+$sha
    $x=Invoke-RestMethod -Uri $uri -Headers @{'user-agent'='v20lab-r070'} -TimeoutSec 30
    need ($x.sha -ceq $sha -and $x.encoding -eq 'base64') 'R088_PKG_BLOB_IDENTITY_FAILED'
    $bytes=[convert]::frombase64string([string]$x.content)
    $parent=Split-Path -Path $dest -Parent
    [io.directory]::CreateDirectory($parent)|Out-Null
    [io.file]::WriteAllBytes($dest,$bytes)
    exact $dest $sha
}
need ($env:OS -eq 'Windows_NT' -and $env:COMPUTERNAME -eq 'URIU-PC') 'R088_PKG_INTEL_ONLY'
need (Test-Path -LiteralPath $liveDir -PathType Container) 'R088_PKG_LIVE_RUNTIME_NOT_FOUND'
exact (Join-Path $liveDir 'finam_live.py') $origLive
exact (Join-Path $liveDir 'finam_execution.py') $origExecution
# Offline staging only. The 17-Nov broker snapshot is historical evidence,
# not permission to install, update SLTP, or ARM without fresh broker proof.
if($mode -eq 'verify') {
    Write-Output 'R088_PKG_INSTALLED_ORIGINAL_LIVE_PINS=PASS'
    if(Test-Path -LiteralPath $package){Write-Output 'R088_PKG_STAGING_DIR_EXISTS=YES'}
    Write-Output 'R088_PKG_NO_FINAM_NO_TASK_MUTATION_NO_ORDER_NO_REARM=YES'
    return
}
if(Test-Path -LiteralPath $package){
    need (Test-Path -LiteralPath $stage -PathType Container) 'R088_PKG_EXISTING_DIRECTORY_UNTRUSTED'
    need (-not (Test-Path -LiteralPath ($package+'.zip'))) 'R088_PKG_ALREADY_PREPARED_NO_REPEAT'
    need (-not (Test-Path -LiteralPath (Join-Path $package 'manifest.json'))) 'R088_PKG_MANIFEST_ALREADY_EXISTS'
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
            need ($LASTEXITCODE -eq 0) ('R088_PKG_PATCH_CONFLICT_'+$name)
            & git.exe apply -- $p
            need ($LASTEXITCODE -eq 0) ('R088_PKG_PATCH_APPLY_FAILED_'+$name)
        }
    } finally {Pop-Location}
    $finalLive=git-hash (Join-Path $stage (($base+'finam_live.py').Replace('/','\')))
    $finalExecution=git-hash (Join-Path $stage (($base+'finam_execution.py').Replace('/','\')))
    need ($finalLive -ceq $expectedLive -and $finalExecution -ceq $expectedExecution) 'R088_PKG_FINAL_COMBINED_SHA_INVALID'
    $manifest=[ordered]@{
       schema='v20.r088.20261118.hold5_ext2_account_source_staged.v2'
       status='STAGED_NOT_INSTALLED_NO_LIVE_APPROVAL'
       source_commit=$branchCommit
       package_files_git_sha=$files
       patched_live_git_sha=$finalLive
       patched_execution_git_sha=$finalExecution
       windows_test='44347998417'
       physical_cny_finam_m15='PASS_2_OF_2_20261118_READONLY_OPERATOR_REPORTED'
       ext2_rolling_refresh='STAGED_FAIL_CLOSED_ACCOUNT_SOURCE_HOOK_REQUIRES_ALL3_CHECKPOINTS_AND_CALENDAR'
       installation='NOT_EXECUTED'
       auto_arm=$false
       finam_requests=0
       orders_sent=0
       original_live_pins_verified=$true
       post_install_observation='FIRST_NATURAL_HOLD5_SIXTH_OPEN_BROKER_RECONCILIATION'
       unresolved_physical_gates=@(
         'R088_EXT2_ALL3_ACCOUNT_CHECKPOINT_BOOTSTRAP_AND_VERIFIED_MOEX_CALENDAR'
         'R070_USDRUBF_GLDRUBF_M15_GAPS'
         'R070_PROTECT3_RELEASE_AUTHORIZATION_AND_BROKER_REPLACEMENT'
         'R070_LIVE_LAUNCHER_NEW_SOURCE_AND_SHA_CUTOVER'
       )
    }
    $manifestPath=Join-Path $package 'manifest.json'
    [io.file]::WriteAllText($manifestPath,($manifest|ConvertTo-Json -Depth 8),[text.utf8encoding]::new($false))
    $targetZip=$package+'.zip'
    need (-not (Test-Path -LiteralPath $targetZip)) 'R088_PKG_ZIP_EXISTS'
    Copy-Item -LiteralPath $PSCommandPath -Destination (Join-Path $package 'r088-20261118-prepare-hold5-package.ps1') -ErrorAction Stop
    Compress-Archive -Path (Join-Path $package '*') -DestinationPath $targetZip -CompressionLevel Optimal
    need (Test-Path -LiteralPath $targetZip -PathType Leaf) 'R088_PKG_ZIP_MISSING'
    $digest=(Get-FileHash -LiteralPath $targetZip -Algorithm SHA256).Hash.ToLowerInvariant()
    Write-Output ('R088_PKG_FULL_STAGED=PASS_9_PATCHES '+$targetZip)
    Write-Output ('R088_PKG_ZIP_SHA256='+$digest)
    Write-Output ('R088_PKG_DERIVED_LIVE_SHA='+$finalLive)
    Write-Output ('R088_PKG_DERIVED_EXEC_SHA='+$finalExecution)
    Write-Output 'R088_PKG_NOT_INSTALLED_NOT_REARMED_NO_FINAM=YES'
    $success=$true
} finally {
    if(-not $success) {Write-Output 'R088_PKG_PREPARATION_HOLD_NO_LIVE_CHANGES'}
}
