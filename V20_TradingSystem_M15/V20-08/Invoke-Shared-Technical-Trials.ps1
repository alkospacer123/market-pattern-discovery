# V20-08.2: one supervised console command, two eligible accounts in sequence.
# Shallow previously had a REAL ACK and no broker SLTP proof: NEVER reuse its
# one-shot permit or reset its H1 SQLite just to repeat a technical test.
# This is only a PowerShell coordinator around the existing single-trial H1
# transport. No FINAM secret handling, no order APIs and no Windows Task mutation.
[CmdletBinding()]
param(
    [ValidateSet('verify','execute')][string]$Mode='verify',
    [switch]$AuthorizeRealTrials
)
$ErrorActionPreference='Stop'
Set-StrictMode -Version Latest
$one=Join-Path $PSScriptRoot 'v20-08-onetrial-technical.ps1'
$expected='f5fae8f01fa057f65226100953b1b50b8ad4c77d'
function need([bool]$ok,[string]$code) { if(-not $ok) { throw $code } }
need ($env:OS -eq 'Windows_NT' -and $env:COMPUTERNAME -eq 'URIU-PC') 'V20_08_2_WRONG_OPERATOR_HOST'
need (Test-Path -LiteralPath $one -PathType Leaf) 'V20_08_2_PINNED_LAUNCHER_MISSING'
need (-not ((Get-Item -LiteralPath $one -Force).Attributes -band [IO.FileAttributes]::ReparsePoint)) 'V20_08_2_LAUNCHER_IS_LINK'
$actual=(& git.exe hash-object -- $one).Trim().ToLowerInvariant()
need ($LASTEXITCODE -eq 0 -and $actual -ceq $expected) 'V20_08_2_LAUNCHER_SHA_INVALID'
$robots=@('v20-shallow','v20-obv','v20-inside')
# Exactly one already-accepted pinned launcher checks 3 account-scoped bindings,
# all 3 Disabled task stubs, unchanged H1 references and V20 source hashes.
foreach($robot in $robots) {
    & powershell.exe -noprofile -executionpolicy bypass -file $one -mode verify -robot $robot -symbol cnyrubf
    need ($LASTEXITCODE -eq 0) ('V20_08_2_PREVERIFY_FAILED_'+$robot)
}
Write-Output 'v20_08_2_shared_source=PASS_THREE_PINNED_OPERATOR_VERIFY'
Write-Output 'v20_08_2_shallow=HOLD_PREVIOUS_REAL_POST_STOP_NOT_PROVEN'
Write-Output 'v20_08_2_shallow_old_sqlite=UNTOUCHED'
if($Mode -eq 'verify') {
    Write-Output 'v20_08_2_shared_mode=VERIFY_NO_FINAM_NO_ORDER'
    return
}
need ($AuthorizeRealTrials.IsPresent) 'V20_08_2_SHARED_EXPLICIT_APPROVAL_REQUIRED'
# Only OBV/Inside remain unused and technically eligible. Existing per-account
# H1 StateStore/permit/InstanceLock refuse any repeat or foreign-account order.
# NEVER launch both orders concurrently. A broker-proven 100%-SLTP and owner's
# manual close/cancel must complete for robot 1 BEFORE robot 2 can be attempted.
foreach($robot in @('v20-obv','v20-inside')) {
    Write-Output ('v20_08_2_shared_now='+$robot)
    $seen=New-Object 'System.Collections.Generic.HashSet[string]'
    & powershell.exe -noprofile -executionpolicy bypass -file $one -mode technical -robot $robot -symbol cnyrubf -roundtripcostpercontract 2.02 -authorizerealtrial 2>&1 | ForEach-Object {
        $line=[string]$_
        Write-Output $line
        [void]$seen.Add($line.Trim())
    }
    $exit=$LASTEXITCODE
    need ($exit -eq 0) ('V20_08_2_SHARED_ABORT_CHILD_FAILED_'+$robot)
    $required=@(
        'v20_08_2_exact_permit=ONE_TECHNICAL_TRIAL_APPROVED',
        'v20_08_2_cycle=ENTRY_ACK_NEEDS_FILL_AND_STOP',
        'v20_08_2_cycle=STOP_ACK_NEEDS_BROKER_PROOF',
        'v20_08_2_cycle=STOP_NOW_BROKER_PROVEN',
        'v20_08_2_cycle=TECHNICAL_SLTP_CONFIRMED_AWAIT_MANUAL_CLOSE',
        'v20_08_2_cycle=MANUAL_EXIT_BROKER_FLAT_UNDER_ACCEPTANCE',
        'v20_08_2_operator=MANUAL_EXIT_BROKER_FLAT_UNDER_ACCEPTANCE'
    )
    foreach($marker in $required) {
        need ($seen.Contains($marker)) ('V20_08_2_SHARED_MISSING_BROKER_PROOF_'+$robot)
    }
    Write-Output ('v20_08_2_shared_'+$robot+'=PASS_SLTP_MANUAL_FLAT_FEES_PENDING')
}
Write-Output 'v20_08_2_shared_result=OBV_INSIDE_STOP_PROOF_DONE_SHALLOW_STILL_HOLD'
Write-Output 'v20_08_2_live=off'
