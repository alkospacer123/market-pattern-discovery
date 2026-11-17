# R070 / Intel physical CNY acceptance. GET /bars only; NO orders/SLTP/Tasks/LIVE SQLite.
# Exact source files from the current Draft PR; all downloads hash-pinned.
[CmdletBinding()]
param()
$ErrorActionPreference='Stop'
Set-StrictMode -Version Latest

$root='c:\v20lab'
$candidate=Join-Path $root 'r070-candidate'
$sources=Join-Path $candidate 'sources'
$tools=Join-Path $candidate 'tooling'
$python=Join-Path $root '.venv-raw\scripts\python.exe'
$h1=Join-Path $root 'source-raw'
$receipt=Join-Path $root 'pretrade-08\DPAPI_TRADING_BINDINGS_REPORT.json'
$commit='07ada1eb37d8acbf31244a4dbd6cd02234c490ef'
$expectedR060='80291246ba4692485545f58fd28c7563199bf7be28033fc16eb296efee377e31'
$expectedCNY='f6ae045a074fea9be3f7c9b5ca47dfc7dedae4481f61e8a71fc60d16b502d4f2'
$names=@('v20-shallow','v20-obv')

function require([bool]$yes,[string]$reason) { if(-not $yes){throw $reason} }
function sha-text([string]$value) {
    $sha=[security.cryptography.sha256]::Create()
    try {return ([bitconverter]::ToString($sha.ComputeHash([text.encoding]::UTF8.GetBytes($value)))).Replace('-','').ToLowerInvariant()}
    finally {$sha.Dispose()}
}
function no-junction([string]$path) {
    if(Test-Path -LiteralPath $path) {
        require (-not ((Get-Item -LiteralPath $path -Force).Attributes -band [io.fileattributes]::ReparsePoint)) 'R070_PHYSICAL_REPARSE_FORBIDDEN'
    }
}
function pinned([string]$file,[string]$blob,[string]$previous='') {
    $target=Join-Path $tools $file
    no-junction $target
    $present=(Test-Path -LiteralPath $target -PathType Leaf)
    $current=if($present){(& git.exe hash-object -- $target).Trim().ToLowerInvariant()}else{''}
    if($present){require ($LASTEXITCODE -eq 0) 'R070_PHYSICAL_LOCAL_BLOB_CHECK_FAILED'}
    if(-not $present -or $current -ne $blob) {
        require (-not $present -or ($previous -ne '' -and $current -eq $previous)) 'R070_PHYSICAL_UNEXPECTED_LOCAL_SCRIPT_CHANGED'
        # Keep existing pinned Git blob; fetch through GitHub API because
        # raw.githubusercontent.com may time out on the Intel workstation.
        $uri='https://api.github.com/repos/alkospacer123/market-pattern-discovery/git/blobs/'+$blob
        $tmp=$target+'.download'
        require (-not (Test-Path -LiteralPath $tmp)) 'R070_PHYSICAL_PARTIAL_DOWNLOAD'
        try {
            $response=Invoke-RestMethod -Uri $uri -Headers @{'user-agent'='v20lab'} -TimeoutSec 30
            require ($response.sha -eq $blob -and $response.encoding -eq 'base64') 'R070_PHYSICAL_GITHUB_BLOB_INVALID'
            [io.file]::writeallbytes($tmp,[convert]::frombase64string($response.content))
            $hash=(& git.exe hash-object -- $tmp).Trim().ToLowerInvariant()
            require ($LASTEXITCODE -eq 0 -and $hash -eq $blob) 'R070_PHYSICAL_DOWNLOADED_BLOB_INVALID'
            Move-Item -LiteralPath $tmp -Destination $target -Force -ErrorAction Stop
        } finally {
            if(Test-Path -LiteralPath $tmp){Remove-Item -LiteralPath $tmp -Force}
        }
    }
    $final=(& git.exe hash-object -- $target).Trim().ToLowerInvariant()
    require ($LASTEXITCODE -eq 0 -and $final -eq $blob) 'R070_PHYSICAL_PINNED_SOURCE_CHANGED'
    return $target
}
require ($env:OS -eq 'Windows_NT' -and $env:COMPUTERNAME -eq 'URIU-PC') 'R070_PHYSICAL_EXPECTED_INTEL_ONLY'
foreach($path in @($root,$candidate,$sources,$python,$h1,$receipt)) {
    require (Test-Path -LiteralPath $path) 'R070_PHYSICAL_REQUIRED_SOURCE_MISSING'
    no-junction $path
}
require ((Get-FileHash -LiteralPath (Join-Path $sources 'TRL-R060-V20-Cash-Parity-2023-2026-Reproducible.zip') -Algorithm SHA256).Hash.ToLowerInvariant() -eq $expectedR060) 'R070_PHYSICAL_ORIGINAL_R060_SHA_INVALID'
require ((Get-FileHash -LiteralPath (Join-Path $sources 'CNYRUBF_260830_261116.csv') -Algorithm SHA256).Hash.ToLowerInvariant() -eq $expectedCNY) 'R070_PHYSICAL_CNY_TERMINAL_SHA_INVALID'
$report=Get-Content -LiteralPath $receipt -Raw -Encoding UTF8 | ConvertFrom-Json
$sid=[security.principal.windowsidentity]::GetCurrent().User.Value
require ($report.schema -eq 'v20.08.1.dpapi_trading_bindings.v1' -and $report.status -eq 'PASS_3_OF_3_DPAPI_LIVE_OFF' -and $report.principal_sid -eq $sid) 'R070_PHYSICAL_DPAPI_BINDING_RECEIPT_INVALID'
New-Item -ItemType Directory -Path $tools -Force | Out-Null
no-junction $tools
$builder=pinned 'r070-build-verified-cny-checkpoint.py' 'd2ab63b5519ddcd4049b9240b1249dc4047c78d0'
$reader=pinned 'r070-cny-intel-readonly.py' 'ce988769658eeab2d8c9869da283e25104f52355' 'ad4e3432eb244ed71ad4cd6229ecae59568a08a7'
$oldPath=$env:PYTHONPATH
$oldAccount=$env:V20_FINAM_ACCOUNT
$oldToken=$env:V20_FINAM_TOKEN
$oldHash=$env:V20_FINAM_ACCOUNT_SHA256
$oldNoBytecode=$env:PYTHONDONTWRITEBYTECODE
try {
    $env:PYTHONPATH=$h1
    $env:PYTHONDONTWRITEBYTECODE='1'
    foreach($name in $names) {
        $match=@($report.robots | Where-Object { $_.robot -eq $name })
        require ($match.Count -eq 1 -and $match[0].account_sha256 -match '^[0-9a-f]{64}$') 'R070_PHYSICAL_ROBOT_IDENTITY_NOT_PROVED'
        $secretPath=Join-Path $root ('robots\'+$name.Substring(4)+'\secrets\finam.dpapi.json')
        no-junction $secretPath
        require (Test-Path -LiteralPath $secretPath -PathType Leaf) 'R070_PHYSICAL_DPAPI_SECRET_MISSING'
        $secret=Get-Content -LiteralPath $secretPath -Raw -Encoding UTF8 | ConvertFrom-Json
        require ($secret.schema -eq 'v20.08.1.dpapi_finam_pair.v1' -and $secret.robot_id -eq $name -and $secret.account_sha256 -eq $match[0].account_sha256 -and $secret.principal_sid -eq $sid) 'R070_PHYSICAL_ROBOT_ACCOUNT_SCOPE_INVALID'
        $completed=Join-Path $candidate ('m15\r070-cny-physical-'+$name+'-'+([datetimeoffset]::Now).ToString('yyyyMMdd')+'.json')
        if(Test-Path -LiteralPath $completed) {
            no-junction $completed
            $prior=Get-Content -LiteralPath $completed -Raw -Encoding UTF8 | ConvertFrom-Json
            require ($prior.status -eq 'PASS_CNYRUBF_FRESH_M15_READONLY_NO_LIVE' -and $prior.account_sha256 -eq $match[0].account_sha256 -and $prior.robot -eq $name) 'R070_PHYSICAL_PREVIOUS_REPORT_INVALID'
            Write-Output ('R070_'+$name+'_ALREADY_PASS_NO_REPEAT=YES')
            continue
        }
        $secureAccount=$null
        $secureToken=$null
        try {
            $secureAccount=ConvertTo-SecureString -String ([string]$secret.account_dpapi)
            $secureToken=ConvertTo-SecureString -String ([string]$secret.token_dpapi)
            $env:V20_FINAM_ACCOUNT=[net.networkcredential]::new('',$secureAccount).Password
            $env:V20_FINAM_TOKEN=[net.networkcredential]::new('',$secureToken).Password
            $env:V20_FINAM_ACCOUNT_SHA256=[string]$secret.account_sha256
            require ((sha-text $env:V20_FINAM_ACCOUNT) -ceq $env:V20_FINAM_ACCOUNT_SHA256) 'R070_PHYSICAL_DECRYPTED_ACCOUNT_MISMATCH'
            & $python -B $reader --root $root --robot $name --builder $builder
            require ($LASTEXITCODE -eq 0) ('R070_PHYSICAL_'+$name+'_FINAM_READONLY_HOLD')
        } finally {
            Remove-Item Env:\V20_FINAM_ACCOUNT -ErrorAction SilentlyContinue
            Remove-Item Env:\V20_FINAM_TOKEN -ErrorAction SilentlyContinue
            Remove-Item Env:\V20_FINAM_ACCOUNT_SHA256 -ErrorAction SilentlyContinue
            if($secureAccount){$secureAccount.Dispose()}
            if($secureToken){$secureToken.Dispose()}
        }
    }
    Write-Output 'R070_CNY_PHYSICAL_READONLY=PASS_2_OF_2_NO_LIVE_CHANGE'
    Write-Output ('R070_CNY_REPORT_DIR='+(Join-Path $candidate 'm15'))
} finally {
    $env:PYTHONPATH=$oldPath
    $env:PYTHONDONTWRITEBYTECODE=$oldNoBytecode
    $env:V20_FINAM_ACCOUNT=$oldAccount
    $env:V20_FINAM_TOKEN=$oldToken
    $env:V20_FINAM_ACCOUNT_SHA256=$oldHash
}
