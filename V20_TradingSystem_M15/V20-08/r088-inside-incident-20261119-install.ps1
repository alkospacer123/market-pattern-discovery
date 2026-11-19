# V20 Inside / 2026-11-19: one scoped LIVE fix of never-POSTed 13:45 USD entry.
# Source is pinned R088 + 1 patch; the CNY 100% SLTP is broker-verified
# BEFORE pausing ONLY Inside. No new entry, order POST/DELETE, or auto-ARM.
[CmdletBinding()]
param([ValidateSet('install')][string]$mode='install')
$ErrorActionPreference='Stop'
Set-StrictMode -Version Latest
$root='c:\v20lab'
$robot='v20-inside'
$live=Join-Path $root 'pretrade-08\live-runtime-08\V20_TradingSystem_M15\v20_runtime\finam_live.py'
$launcher=Join-Path $root 'pretrade-08\live-08\v20-08-live-launch.ps1'
$operator=Join-Path $root 'pretrade-08\live-08\v20-08-live-operator.ps1'
$switch=Join-Path $root 'robots\inside\safety\stage8-trading-kill-switch.json'
$secret=Join-Path $root 'robots\inside\secrets\finam.dpapi.json'
$receipt=Join-Path $root 'pretrade-08\DPAPI_TRADING_BINDINGS_REPORT.json'
$db=Join-Path $root 'robots\inside\state\v20-real-intents.sqlite3'
$python=Join-Path $root '.venv-raw\scripts\python.exe'
$h1=Join-Path $root 'source-raw'
$log=Join-Path $root 'robots\inside\logs\live-m15.jsonl'
$oldSha='54ae8e1262482f4ecc80d202c6e9063cf0d6e402'
$newSha='9ce789ead74dabed156ccc93d284cb79486ed2bc'
$execSha='0fc4c454d55f37e4e87fd74e3370cbc1ad83b53f'
$patchSha='ac37ab66c4496871219d8f106561fdabc6abe4a5'
$helperSha='c92c8dac3876f1d402e08f4891f3da2c8d66a6fe'
function need([bool]$ok,[string]$reason){if(-not $ok){throw $reason}}
function pin([string]$p,[string]$sha){
 need (Test-Path -LiteralPath $p -PathType Leaf) 'INSIDE_MISSING_FILE'
 need (-not ((Get-Item -LiteralPath $p -Force).Attributes -band [io.fileattributes]::ReparsePoint)) 'INSIDE_REPARSE_FORBIDDEN'
 $got=(& git.exe hash-object -- $p).Trim().ToLowerInvariant()
 need ($LASTEXITCODE -eq 0 -and $got -ceq $sha) ('INSIDE_SHA_MISMATCH_'+$p)
}
function get-pin([string]$sha,[string]$path){
 $uri='https://api.github.com/repos/alkospacer123/market-pattern-discovery/git/blobs/'+$sha
 $response=Invoke-RestMethod -Uri $uri -Headers @{'user-agent'='v20-inside-20261119'} -TimeoutSec 30
 need ($response.sha -ceq $sha -and $response.encoding -eq 'base64') 'INSIDE_GITHUB_PIN_INVALID'
 [io.file]::WriteAllBytes($path,[convert]::FromBase64String([string]$response.content))
 pin $path $sha
}
function halted(){
 $obj=Get-Content -LiteralPath $switch -Raw -Encoding UTF8 | ConvertFrom-Json
 need ($obj.state -eq 'HALTED') 'INSIDE_KILL_SWITCH_NOT_HALTED'
}
function task(){
 $t=Get-ScheduledTask -TaskName $robot -TaskPath '\' -ErrorAction Stop
 $expected='-noprofile -noninteractive -executionpolicy bypass -file "'+$launcher+'" -mode run -robot v20-inside'
 $dir=Join-Path $root 'robots\inside'
 need (@($t.Actions).Count -eq 1 -and $t.Actions[0].Execute -ieq 'powershell.exe' -and
       $t.Actions[0].Arguments -ieq $expected -and
       $t.Actions[0].WorkingDirectory -ieq $dir) 'INSIDE_SCHEDULED_TASK_ACTION_CHANGED'
 return $t
}
function no-worker(){
 $processes=@(Get-CimInstance Win32_Process -Filter "Name='python.exe'" | Where-Object {
  $_.CommandLine -match 'V20_TradingSystem_M15.v20_runtime.finam_live' -and
  $_.CommandLine -match '--robot\s+v20-inside'
 })
 need ($processes.Count -eq 0) 'INSIDE_OLD_PYTHON_WORKER_STILL_RUNNING'
}
function stop-inside(){
 if((task).State -eq 'Running'){Stop-ScheduledTask -TaskName $robot -TaskPath '\' -ErrorAction Stop}
 for($i=0;$i -lt 25 -and (task).State -eq 'Running';$i++){Start-Sleep -Seconds 1}
 need ((task).State -ne 'Running') 'INSIDE_TASK_STOP_UNCONFIRMED'
 no-worker
}
function start-inside(){
 if((task).State -ne 'Running'){Start-ScheduledTask -TaskName $robot -TaskPath '\' -ErrorAction Stop}
 for($i=0;$i -lt 30 -and (task).State -ne 'Running';$i++){Start-Sleep -Seconds 1}
 need ((task).State -eq 'Running') 'INSIDE_TASK_RESTART_FAILED'
}
function python-pre([string]$helper){
 $scope=Get-Content -LiteralPath $receipt -Raw -Encoding UTF8 | ConvertFrom-Json
 $data=Get-Content -LiteralPath $secret -Raw -Encoding UTF8 | ConvertFrom-Json
 $sid=[security.principal.windowsidentity]::GetCurrent().User.Value
 $match=@($scope.robots | Where-Object {$_.robot -eq $robot})
 need ($scope.principal_sid -eq $sid -and $match.Count -eq 1 -and
       $match[0].account_sha256 -eq $data.account_sha256 -and
       $data.robot_id -eq $robot -and $data.principal_sid -eq $sid) 'INSIDE_DPAPI_BINDINGS_INVALID'
 $priorPath=$env:PYTHONPATH
 $priorNoBytes=$env:PYTHONDONTWRITEBYTECODE
 $priorAccount=$env:V20_FINAM_ACCOUNT
 $priorToken=$env:V20_FINAM_TOKEN
 $priorScope=$env:V20_FINAM_ACCOUNT_SHA256
 try {
  $acc=ConvertTo-SecureString -String ([string]$data.account_dpapi)
  $tok=ConvertTo-SecureString -String ([string]$data.token_dpapi)
  $env:V20_FINAM_ACCOUNT=[net.networkcredential]::new('',$acc).Password
  $env:V20_FINAM_TOKEN=[net.networkcredential]::new('',$tok).Password
  $env:V20_FINAM_ACCOUNT_SHA256=[string]$data.account_sha256
  $env:PYTHONPATH=(Join-Path $root 'pretrade-08\live-runtime-08')+[io.path]::PathSeparator+$h1
  $env:PYTHONDONTWRITEBYTECODE='1'
  & $python -B $helper pre $db
  need ($LASTEXITCODE -eq 0) 'INSIDE_BROKER_SLTP_OR_USD_PREPOST_PROOF_FAILED'
 } finally {
  $env:PYTHONPATH=$priorPath
  $env:PYTHONDONTWRITEBYTECODE=$priorNoBytes
  $env:V20_FINAM_ACCOUNT=$priorAccount
  $env:V20_FINAM_TOKEN=$priorToken
  $env:V20_FINAM_ACCOUNT_SHA256=$priorScope
 }
}
need ($env:OS -eq 'Windows_NT' -and $env:COMPUTERNAME -eq 'URIU-PC') 'INSIDE_ONLY_INTEL'
halted
need ((task).State -eq 'Running') 'INSIDE_WORKER_TASK_NOT_RUNNING'
pin $live $oldSha
$exec=Join-Path (Split-Path $live -Parent) 'finam_execution.py'
pin $exec $execSha
foreach($file in @($operator,$launcher,$secret,$receipt,$db,$python,$h1,$log)){
 need (Test-Path -LiteralPath $file) ('INSIDE_REQUIRED_FILE_MISSING_'+$file)
}
$text=[io.file]::ReadAllText($launcher)
need (([regex]::Matches($text,[regex]::Escape("'$oldSha'"))).Count -eq 1 -and
      ([regex]::Matches($text,[regex]::Escape("'$execSha'"))).Count -eq 1) 'INSIDE_LAUNCHER_PIN_NOT_R088'
$stamp=([datetimeoffset]::UtcNow).ToString('yyyyMMddTHHmmssZ')
$working=Join-Path $root ('r088-candidate\inside-prepost-20261119-'+$stamp)
$stage=Join-Path $working 'V20_TradingSystem_M15\v20_runtime'
$backup=Join-Path $root ('backup-08\inside-20261119-'+$stamp)
need (-not (Test-Path -LiteralPath $working) -and -not (Test-Path -LiteralPath $backup)) 'INSIDE_TARGET_COLLISION'
[io.directory]::CreateDirectory($stage)|Out-Null
[io.directory]::CreateDirectory($backup)|Out-Null
$patch=Join-Path $working 'inside-prepost.patch'
$helper=Join-Path $working 'inside-incident-readonly.py'
get-pin $patchSha $patch
get-pin $helperSha $helper
Copy-Item -LiteralPath $live -Destination (Join-Path $stage 'finam_live.py')
Push-Location $working
try {
 & git.exe apply --check -- $patch
 need ($LASTEXITCODE -eq 0) 'INSIDE_PATCH_CONFLICT'
 & git.exe apply -- $patch
 need ($LASTEXITCODE -eq 0) 'INSIDE_PATCH_APPLY_FAILED'
} finally {Pop-Location}
$patched=Join-Path $stage 'finam_live.py'
pin $patched $newSha
& $python -B -m py_compile $patched $helper
need ($LASTEXITCODE -eq 0) 'INSIDE_PYTHON_SYNTAX_INVALID'
# The only FINAM access is this GET-only proof of existing CNY SLTP, and
# proof that USD has neither a position nor an order/post checkpoint.
python-pre $helper
halted
need ((task).State -eq 'Running') 'INSIDE_TASK_CHANGED_AFTER_READONLY'
$bo=@(& powershell.exe -noprofile -noninteractive -executionpolicy bypass -file $operator -mode backup -robot $robot 2>&1)
need ($LASTEXITCODE -eq 0 -and ($bo -join '|') -match 'v20_08_5_backup=PASS') 'INSIDE_LIVE_SQLITE_BACKUP_FAILED'
$bo | Write-Output
Copy-Item -LiteralPath $live -Destination (Join-Path $backup 'finam_live.py')
Copy-Item -LiteralPath $launcher -Destination (Join-Path $backup 'v20-08-live-launch.ps1')
[io.file]::WriteAllText((Join-Path $backup 'fix-info.txt'),
 ('r088-inside-20261119 base='+$oldSha+' target='+$newSha+' patch='+$patchSha+' test_run=44517858788'),[text.utf8encoding]::new($false))
Write-Output ('INSIDE_FIX_ROLLBACK_DIR='+$backup)
# Broker protection was proved BEFORE stopping the Inside worker.
# Neither Shallow nor OBV is stopped/armed/changed in memory.
try {
 stop-inside
 Copy-Item -LiteralPath $patched -Destination $live -Force
 pin $live $newSha
 $nextText=$text.Replace("'$oldSha'","'$newSha'")
 [io.file]::WriteAllText($launcher,$nextText,[text.utf8encoding]::new($false))
 foreach($n in @('v20-inside','v20-shallow','v20-obv')){
  & powershell.exe -noprofile -noninteractive -executionpolicy bypass -file $launcher -mode verify -robot $n
  need ($LASTEXITCODE -eq 0) ('INSIDE_R088_LAUNCHER_VERIFY_FAILED_'+$n)
 }
 $started=[datetimeoffset]::UtcNow
 start-inside
 $fresh=$false
 for($i=0;$i -lt 45;$i++){
  try {
   $row=Get-Content -LiteralPath $log -Tail 1 -Encoding UTF8 | ConvertFrom-Json
   $at=[datetimeoffset]::Parse([string]$row.utc,[globalization.cultureinfo]::InvariantCulture)
   if($at -ge $started.AddSeconds(-5) -and $row.robot -eq 'v20-inside' -and
      $row.state -eq 'HALTED_NO_NEW_ENTRIES'){$fresh=$true;break}
  }catch{}
  Start-Sleep -Seconds 1
 }
 need $fresh 'INSIDE_NEW_WORKER_FRESH_SAFE_CYCLE_MISSING'
 & $python -B $helper post $db
 need ($LASTEXITCODE -eq 0) 'INSIDE_SQLITE_PREPOST_RECOVERY_NOT_PROVEN'
 halted
 Write-Output 'INSIDE_PREPOST_FIX=PASS_INSTALLED_WORKER_RUNNING_HALTED'
 Write-Output 'INSIDE_CNY_EXISTING_SLTP=UNCHANGED_NEW_ENTRIES_OFF'
 Write-Output 'INSIDE_NO_TRADING_POST_DELETE_NO_ARM=YES'
} catch {
 $why=$_.Exception.Message
 Write-Output ('INSIDE_INSTALL_HOLD='+$why)
 try {
  stop-inside
  Copy-Item -LiteralPath (Join-Path $backup 'finam_live.py') -Destination $live -Force
  Copy-Item -LiteralPath (Join-Path $backup 'v20-08-live-launch.ps1') -Destination $launcher -Force
  pin $live $oldSha
  start-inside
  halted
  Write-Output 'INSIDE_AUTO_ROLLBACK=PASS_ORIGINAL_RUNNING_HALTED'
 } catch {
  Write-Output ('INSIDE_ROLLBACK_NEEDS_OPERATOR='+$_.Exception.Message)
 }
 Write-Output ('INSIDE_FIX_ROLLBACK_DIR='+$backup)
 throw
}
