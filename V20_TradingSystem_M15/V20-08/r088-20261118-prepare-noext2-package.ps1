# R088 / 18 Nov 2026: STAGE ONLY the already tested TP6 + Protect3 + HOLD5
# candidate, explicitly WITHOUT EXT2/history/calendar/live account hooks.
# Never installs/rearms robots, alters stop/orders/tasks or calls FINAM.
[CmdletBinding()]
param([ValidateSet('prepare','verify')][string]$mode='prepare')
$ErrorActionPreference='Stop'
Set-StrictMode -Version Latest
$root='c:\v20lab'
$base='V20_TradingSystem_M15/v20_runtime/'
$patchBase='V20_TradingSystem_M15/V20-08/'
$oldStage=Join-Path $root 'r088-candidate\release-20261118-hold5-all3-src5\staged'
$package=Join-Path $root 'r088-candidate\release-20261118-tp6-protect3-hold5-noext2'
$stage=Join-Path $package 'staged'
$liveDir=Join-Path $root 'pretrade-08\live-runtime-08\V20_TradingSystem_M15\v20_runtime'
$oldLive='b80fb9eb135f7cdcb4c78337e2b808c4d7135195'
$oldExec='6b600451178b42bd4f8b2037995e7db3a9ad27c8'
$newLive='54ae8e1262482f4ecc80d202c6e9063cf0d6e402'
$newExec='0fc4c454d55f37e4e87fd74e3370cbc1ad83b53f'
$files=[ordered]@{
  'V20_TradingSystem_M15/v20_runtime/finam_live.py'=$oldLive
  'V20_TradingSystem_M15/v20_runtime/finam_execution.py'=$oldExec
  'V20_TradingSystem_M15/v20_runtime/tp6_protect3.py'='a578cac629350f2c9fe3409121ac085c8a41eb63'
  'V20_TradingSystem_M15/v20_runtime/r070_linked_sltp.py'='864d03d8fe467138adf73c6e6216a88fc81e8c21'
  'V20_TradingSystem_M15/v20_runtime/r088_hold5.py'='f0b9058707230299464f1f6fb5245653a022ec31'
  'V20_TradingSystem_M15/V20-08/r070-tp6-one-shot-candidate.patch'='c1947f59ab68884fd6543c40d64892d6a899f225'
  'V20_TradingSystem_M15/V20-08/r070-protect3-flat-cleanup-candidate.patch'='b7d3eb587e97d4012cc21a593f2d8b605e431611'
  'V20_TradingSystem_M15/V20-08/r070-protect3-broker-id-readonly-candidate.patch'='4d975f8d2d4b701b48205f9ad24c0d49e45c9c4e'
  'V20_TradingSystem_M15/V20-08/r070-protect3-live-trigger-candidate.patch'='0e378d0197815556cdd99ac8e1d6c20d1c05a056'
  'V20_TradingSystem_M15/V20-08/r070-protect3-night-monitor-candidate.patch'='05dffdaaaed6359b0a78116adac9364dd2bdcc34'
  'V20_TradingSystem_M15/V20-08/r070-finam-get-incomplete-read-candidate.patch'='fabfa58e9d84553fe0c51833530cb90d89412e85'
  'V20_TradingSystem_M15/V20-08/r088-hold5-after-r070-combined-candidate.patch'='0c73f8265a1c7f75a1bc8f4b849e5970fe274bc4'
}
$patches=@(
 'r070-tp6-one-shot-candidate.patch',
 'r070-protect3-flat-cleanup-candidate.patch',
 'r070-protect3-broker-id-readonly-candidate.patch',
 'r070-protect3-live-trigger-candidate.patch',
 'r070-protect3-night-monitor-candidate.patch',
 'r070-finam-get-incomplete-read-candidate.patch',
 'r088-hold5-after-r070-combined-candidate.patch'
)
function need([bool]$ok,[string]$code){if(-not $ok){throw $code}}
function sha([string]$path){
    need (Test-Path -LiteralPath $path -PathType Leaf) 'R088_NOEXT2_FILE_MISSING'
    need (-not ((Get-Item -LiteralPath $path -Force).Attributes -band [io.fileattributes]::ReparsePoint)) 'R088_NOEXT2_SOURCE_LINK'
    $hash=(& git.exe hash-object -- $path).Trim().ToLowerInvariant()
    need ($LASTEXITCODE -eq 0 -and $hash -match '^[0-9a-f]{40}$') 'R088_NOEXT2_HASH_FAILED'
    return $hash
}
function pinned([string]$path,[string]$expected){
    need ((sha $path) -ceq $expected) 'R088_NOEXT2_SHA_MISMATCH'
}
function get-source([string]$rel,[string]$expected,[string]$target) {
    $parent=Split-Path $target -Parent
    [io.directory]::CreateDirectory($parent)|Out-Null
    $local=Join-Path $oldStage ($rel.Replace('/','\'))
    if((Test-Path -LiteralPath $local -PathType Leaf) -and (sha $local) -ceq $expected) {
        Copy-Item -LiteralPath $local -Destination $target -ErrorAction Stop
    } else {
        $u='https://api.github.com/repos/alkospacer123/market-pattern-discovery/git/blobs/'+$expected
        $r=Invoke-RestMethod -Uri $u -Headers @{'user-agent'='v20lab-r088-noext2'} -TimeoutSec 30
        need ($r.sha -ceq $expected -and $r.encoding -eq 'base64') 'R088_NOEXT2_BLOB_UNVERIFIED'
        [io.file]::WriteAllBytes($target,[convert]::FromBase64String([string]$r.content))
    }
    pinned $target $expected
}
need ($env:OS -eq 'Windows_NT' -and $env:COMPUTERNAME -eq 'URIU-PC') 'R088_NOEXT2_INTEL_ONLY'
pinned (Join-Path $liveDir 'finam_live.py') $oldLive
pinned (Join-Path $liveDir 'finam_execution.py') $oldExec
if($mode -eq 'verify'){
    Write-Output 'R088_NOEXT2_ORIGINAL_LIVE_PINS=PASS'
    Write-Output 'R088_NOEXT2_NO_FINAM_NO_ORDER_NO_REARM=YES'
    return
}
need (-not (Test-Path -LiteralPath $package)) 'R088_NOEXT2_PACKAGE_EXISTS_NO_OVERWRITE'
need (-not (Test-Path -LiteralPath ($package+'.zip'))) 'R088_NOEXT2_ZIP_EXISTS'
[io.directory]::CreateDirectory($stage)|Out-Null
$ok=$false
try {
    foreach($item in $files.GetEnumerator()){
        get-source $item.Key $item.Value (Join-Path $stage ($item.Key.Replace('/','\')))
    }
    Push-Location $stage
    try {
        foreach($name in $patches){
            $patch=Join-Path $stage (($patchBase+$name).Replace('/','\'))
            & git.exe apply --check -- $patch
            need ($LASTEXITCODE -eq 0) ('R088_NOEXT2_PATCH_CONFLICT_'+$name)
            & git.exe apply -- $patch
            need ($LASTEXITCODE -eq 0) ('R088_NOEXT2_PATCH_FAILED_'+$name)
        }
    } finally { Pop-Location }
    $live=Join-Path $stage (($base+'finam_live.py').Replace('/','\'))
    $exec=Join-Path $stage (($base+'finam_execution.py').Replace('/','\'))
    pinned $live $newLive
    pinned $exec $newExec
    $liveText=[io.file]::ReadAllText($live)
    foreach($needle in @(
      'admit_r070_frozen_draft_pre_intent',
      'configure_r088_ext2_live_source',
      'r070_verified_history_refresh',
      'r088-moex-calendar.json')) {
        need (-not $liveText.Contains($needle)) ('R088_NOEXT2_HAS_EXT2_HOOK_'+$needle)
    }
    $manifest=[ordered]@{
        schema='v20.r088.20261118.noext2_staged.v1'
        status='STAGED_NOT_INSTALLED'
        configuration='TP6_PROTECT3_HOLD5_WITHOUT_EXT2'
        windows_ci='44363714666'
        ci_commit='9d9c797af2db9ee78ba73e2d55840f21c6aaf854'
        base_live_sha=$oldLive
        base_execution_sha=$oldExec
        patched_live_sha=$newLive
        patched_execution_sha=$newExec
        source_git_sha=$files
        patch_order=$patches
        order_posts=0
        finam_requests=0
        installed=$false
        armed=$false
        rollback='ORIGINAL_SHA_PINNED_LIVE_AND_EXECUTION_UNCHANGED'
    }
    [io.file]::WriteAllText((Join-Path $package 'manifest.json'),
        ($manifest|ConvertTo-Json -Depth 6),[text.utf8encoding]::new($false))
    Copy-Item -LiteralPath $PSCommandPath -Destination (Join-Path $package 'r088-20261118-prepare-noext2-package.ps1')
    Compress-Archive -Path (Join-Path $package '*') -DestinationPath ($package+'.zip') -CompressionLevel Optimal
    need (Test-Path -LiteralPath ($package+'.zip') -PathType Leaf) 'R088_NOEXT2_ZIP_MISSING'
    Write-Output ('R088_NOEXT2_STAGED=PASS_7_PATCHES '+$package+'.zip')
    Write-Output ('R088_NOEXT2_ZIP_SHA256='+(Get-FileHash -LiteralPath ($package+'.zip') -Algorithm SHA256).Hash.ToLowerInvariant())
    Write-Output ('R088_NOEXT2_LIVE_SHA='+$newLive)
    Write-Output ('R088_NOEXT2_EXEC_SHA='+$newExec)
    Write-Output 'R088_NOEXT2_NO_EXT2_NO_FINAM_NO_INSTALL_NO_REARM=YES'
    $ok=$true
} finally {
    if(-not $ok){Write-Output 'R088_NOEXT2_STAGE_HOLD_NO_LIVE_CHANGE'}
}
