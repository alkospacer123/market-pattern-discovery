# V20 all three / 2026-11-19: one shared, scoped pre-POST order-intent fix.
# Source is pinned R088 + 1 patch; the CNY 100% SLTP is broker-verified
# BEFORE pausing 3 V20 workers. No order POST/DELETE or auto-ARM.
[CmdletBinding()]
param([ValidateSet('install')][string]$mode='install')
$ErrorActionPreference='Stop'
Set-StrictMode -Version Latest
$root='c:\v20lab'
$robot='v20-inside'
$robots=@('v20-shallow','v20-obv','v20-inside')
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
$newSha='NEW_SHA_TBD'
$execSha='0fc4c454d55f37e4e87fd74e3370cbc1ad83b53f'
$patchSha='34fba96898bf4a707a45be5401270f5e7bbbc47f'
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
function switch-state([string]$name){
 $path=Join-Path $root ('robots\'+$name.Substring(4)+'\safety\stage8-trading-kill-switch.json')
 need (Test-Path -LiteralPath $path -PathType Leaf) 'V20_SWITCH_FILE_MISSING'
 return (Get-Content -LiteralPath $path -Raw -Encoding UTF8 | ConvertFrom-Json).state
}
function all-halted(){
 foreach($n in $robots){need ((switch-state $n) -eq 'HALTED') ('V20_SWITCH_NOT_HALTED_'+$n)}
}
function task([string]$name){
 $t=Get-ScheduledTask -TaskName $name -TaskPath '\' -ErrorAction Stop
 $expected='-noprofile -noninteractive -executionpolicy bypass -file "'+$launcher+'" -mode run -robot '+$name
 $dir=Join-Path $root ('robots\'+$name.Substring(4))
 need (@($t.Actions).Count -eq 1 -and $t.Actions[0].Execute -ieq 'powershell.exe' -and
       $t.Actions[0].Arguments -ieq $expected -and
       $t.Actions[0].WorkingDirectory -ieq $dir) ('V20_TASK_ACTION_CHANGED_'+$name)
 return $t
}
function readonly-flat([string]$name){
 $o=@(& powershell.exe -noprofile -noninteractive -executionpolicy bypass -file $launcher -mode readonly -robot $name 2>&1)
 need ($LASTEXITCODE -eq 0 -and ($o -join '|') -match 'v20_08_4_positions=0' -and
       ($o -join '|') -match 'v20_08_4_active_orders=0' -and
       ($o -join '|') -match 'v20_08_4_order_posts=zero') ('V20_BROKER_FLAT_NOT_PROVEN_'+$name)
 Write-Output ('V20_BROKER_FLAT_'+$name+'=PASS_GET_ONLY')
}
function no-workers(){
 $processes=@(Get-CimInstance Win32_Process -Filter "Name='python.exe'" | Where-Object {
   $_.CommandLine -match 'V20_TradingSystem_M15.v20_runtime.finam_live' -and
   $_.CommandLine -match '--robot\s+v20-(shallow|obv|inside)'
 })
 need ($processes.Count -eq 0) 'V20_OLD_PYTHON_WORKERS_STILL_RUNNING'
}
function stop-all(){
 foreach($n in $robots){
  if((task $n).State -eq 'Running'){Stop-ScheduledTask -TaskName $n -TaskPath '\' -ErrorAction Stop}
 }
 for($i=0;$i -lt 30;$i++){
  if(@($robots | Where-Object {(task $_).State -eq 'Running'}).Count -eq 0){break}
  Start-Sleep -Seconds 1
 }
 need (@($robots | Where-Object {(task $_).State -eq 'Running'}).Count -eq 0) 'V20_WORKERS_NOT_QUIESCENT'
 no-workers
}
function start-all(){
 foreach($n in $robots){
  if((task $n).State -ne 'Running'){Start-ScheduledTask -TaskName $n -TaskPath '\' -ErrorAction Stop}
 }
 for($i=0;$i -lt 35;$i++){
  if(@($robots | Where-Object {(task $_).State -ne 'Running'}).Count -eq 0){break}
  Start-Sleep -Seconds 1
 }
 need (@($robots | Where-Object {(task $_).State -ne 'Running'}).Count -eq 0) 'V20_WORKER_RESTART_FAILED'
}
function fresh-halted-cycles([datetimeoffset]$started){
 for($i=0;$i -lt 55;$i++){
  $valid=0
  foreach($n in $robots){
   $p=Join-Path $root ('robots\'+$n.Substring(4)+'\logs\live-m15.jsonl')
   try {
    $entry=Get-Content -LiteralPath $p -Tail 1 -Encoding UTF8 | ConvertFrom-Json -ErrorAction Stop
    $at=[datetimeoffset]::Parse([string]$entry.utc,[globalization.cultureinfo]::InvariantCulture)
    if($entry.robot -eq $n -and $at -ge $started.AddSeconds(-5) -and
       $entry.state -eq 'HALTED_NO_NEW_ENTRIES'){$valid++}
   }catch{}
  }
  if($valid -eq 3){return}
  Start-Sleep -Seconds 1
 }
 throw 'V20_FRESH_3_HALTED_CYCLES_NOT_PROVEN'
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
need ($env:OS -eq 'Windows_NT' -and $env:COMPUTERNAME -eq 'URIU-PC') 'V20_EXPECTED_INTEL_ONLY'
foreach($n in $robots){need ((task $n).State -eq 'Running') ('V20_TASK_NOT_RUNNING_'+$n)}
need ((switch-state 'v20-inside') -eq 'HALTED') 'INSIDE_INCIDENT_SWITCH_NOT_HALTED'
foreach($n in @('v20-shallow','v20-obv')){
 need ((switch-state $n) -in @('ARMED','HALTED')) ('V20_SWITCH_INVALID_'+$n)
}
pin $live $oldSha
$exec=Join-Path (Split-Path $live -Parent) 'finam_execution.py'
pin $exec $execSha
foreach($file in @($operator,$launcher,$secret,$receipt,$db,$python,$h1,$log)){
 need (Test-Path -LiteralPath $file) ('V20_REQUIRED_FILE_MISSING_'+$file)
}
$text=[io.file]::ReadAllText($launcher)
need (([regex]::Matches($text,[regex]::Escape("'$oldSha'"))).Count -eq 1 -and
      ([regex]::Matches($text,[regex]::Escape("'$execSha'"))).Count -eq 1) 'V20_LAUNCHER_PIN_NOT_R088'
# Do not interrupt another protected live trade or uncertain broker request.
foreach($n in @('v20-shallow','v20-obv')){readonly-flat $n}
$stamp=([datetimeoffset]::UtcNow).ToString('yyyyMMddTHHmmssZ')
$working=Join-Path $root ('r088-candidate\prepost-all3-20261119-'+$stamp)
$stage=Join-Path $working 'V20_TradingSystem_M15\v20_runtime'
$backup=Join-Path $root ('backup-08\prepost-all3-20261119-'+$stamp)
need (-not (Test-Path -LiteralPath $working) -and -not (Test-Path -LiteralPath $backup)) 'V20_TARGET_COLLISION'
[io.directory]::CreateDirectory($stage)|Out-Null
[io.directory]::CreateDirectory($backup)|Out-Null
$patch=Join-Path $working 'v20-prepost.patch'
$helper=Join-Path $working 'inside-incident-readonly.py'
get-pin $patchSha $patch
get-pin $helperSha $helper
Copy-Item -LiteralPath $live -Destination (Join-Path $stage 'finam_live.py')
Push-Location $working
try {
 & git.exe apply --check -- $patch
 need ($LASTEXITCODE -eq 0) 'V20_PATCH_CONFLICT'
 & git.exe apply -- $patch
 need ($LASTEXITCODE -eq 0) 'V20_PATCH_APPLY_FAILED'
} finally {Pop-Location}
$patched=Join-Path $stage 'finam_live.py'
pin $patched $newSha
& $python -B -m py_compile $patched $helper
need ($LASTEXITCODE -eq 0) 'V20_PYTHON_SYNTAX_INVALID'
# Fresh FINAM proof BEFORE changing any task or account switch.
python-pre $helper
# Stop NEW entries on all accounts before stopping workers.
$o=@(& powershell.exe -noprofile -noninteractive -executionpolicy bypass -file $operator -mode stop -robot all 2>&1)
need ($LASTEXITCODE -eq 0) 'V20_OPERATOR_HALT_ALL_FAILED'
all-halted
# Second GET-only guard closes the gap between preflight and Kill Switch HALT.
foreach($n in @('v20-shallow','v20-obv')){readonly-flat $n}
python-pre $helper
$bo=@(& powershell.exe -noprofile -noninteractive -executionpolicy bypass -file $operator -mode backup -robot all 2>&1)
need ($LASTEXITCODE -eq 0 -and ($bo -join '|') -match 'v20_08_5_backup=PASS') 'V20_SQLITE_BACKUP_3_FAILED'
$bo | Write-Output
Copy-Item -LiteralPath $live -Destination (Join-Path $backup 'finam_live.py')
Copy-Item -LiteralPath $launcher -Destination (Join-Path $backup 'v20-08-live-launch.ps1')
[io.file]::WriteAllText((Join-Path $backup 'fix-info.txt'),
 ('r088-all3-prepost-20261119 base='+$oldSha+' target='+$newSha+' patch='+$patchSha),
 [text.utf8encoding]::new($false))
Write-Output ('V20_ALL3_ROLLBACK_DIR='+$backup)
# No active Shallow/OBV position; Inside CNY stop identity was broker-proven.
try {
 stop-all
 Copy-Item -LiteralPath $patched -Destination $live -Force
 pin $live $newSha
 $nextText=$text.Replace("'$oldSha'","'$newSha'")
 [io.file]::WriteAllText($launcher,$nextText,[text.utf8encoding]::new($false))
 foreach($n in $robots){
  & powershell.exe -noprofile -noninteractive -executionpolicy bypass -file $launcher -mode verify -robot $n
  need ($LASTEXITCODE -eq 0) ('V20_NEW_LAUNCHER_VERIFY_FAILED_'+$n)
 }
 $started=[datetimeoffset]::UtcNow
 start-all
 fresh-halted-cycles $started
 & $python -B $helper post $db
 need ($LASTEXITCODE -eq 0) 'V20_INSIDE_SQLITE_ORPHAN_NOT_RESOLVED'
 all-halted
 Write-Output 'V20_ALL3_PREPOST_FIX=PASS_3_RUNNING_HALTED_FRESH_CYCLES'
 Write-Output 'V20_INSIDE_USD_ORPHAN=CANCELLED_NO_BROKER_POST'
 Write-Output 'V20_CNY_EXISTING_SLTP=UNCHANGED'
 Write-Output 'V20_ALL3_NO_NEW_ORDERS_NO_AUTO_ARM=YES'
} catch {
 Write-Output ('V20_INSTALL_HOLD='+$_.Exception.Message)
 try {
  stop-all
  Copy-Item -LiteralPath (Join-Path $backup 'finam_live.py') -Destination $live -Force
  Copy-Item -LiteralPath (Join-Path $backup 'v20-08-live-launch.ps1') -Destination $launcher -Force
  pin $live $oldSha
  foreach($n in $robots){
   & powershell.exe -noprofile -noninteractive -executionpolicy bypass -file $launcher -mode verify -robot $n
   need ($LASTEXITCODE -eq 0) ('V20_ROLLBACK_VERIFY_FAILED_'+$n)
  }
  start-all
  all-halted
  Write-Output 'V20_AUTO_ROLLBACK=PASS_ORIGINAL_3_RUNNING_HALTED'
 } catch {
  Write-Output ('V20_ROLLBACK_NEEDS_OPERATOR='+$_.Exception.Message)
 }
 Write-Output ('V20_ALL3_ROLLBACK_DIR='+$backup)
 throw
}
