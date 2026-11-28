"""PG10.2 F4: reproducible all-three/CC package and paired rollback contract."""
from hashlib import sha1, sha256
import io
import json
import os
from pathlib import Path
import subprocess
import tempfile
import unittest
import zipfile


ROOT = Path(__file__).resolve().parents[3]
RELEASE = ROOT / "V20_TradingSystem_M15" / "V20-08"
MANIFEST_PATH = RELEASE / "pg10-2-release-manifest.json"


def canonical(path):
    return Path(path).read_bytes().replace(b"\r\n", b"\n")


def identities(data):
    return (sha256(data).hexdigest(),
            sha1(b"blob " + str(len(data)).encode() + b"\0" + data).hexdigest())


def build_derived(manifest, work):
    work = Path(work)
    for name in ("finam_live.py", "finam_execution.py"):
        source = ROOT / "V20_TradingSystem_M15" / "v20_runtime" / name
        target = work / "V20_TradingSystem_M15" / "v20_runtime" / name
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(canonical(source).replace(b"\n", b"\r\n"))
    for patch in manifest["ordered_patches"]:
        source = ROOT / patch["source_path"]
        local = work / patch["source_path"]
        local.parent.mkdir(parents=True, exist_ok=True)
        local.write_bytes(canonical(source).replace(b"\n", b"\r\n"))
        subprocess.run(["git", "apply", "--check", "--", str(local)],
                       cwd=work, check=True, capture_output=True)
        subprocess.run(["git", "apply", "--", str(local)],
                       cwd=work, check=True, capture_output=True)
    derived = {}
    for name in ("finam_live.py", "finam_execution.py"):
        path = work / "V20_TradingSystem_M15" / "v20_runtime" / name
        derived["V20_TradingSystem_M15/v20_runtime/" + name] = path.read_bytes().replace(b"\r\n", b"\n")
    return derived


class ReleaseTests(unittest.TestCase):
    def test_manifest_base_plus_eleven_and_deterministic_package(self):
        manifest = json.loads(MANIFEST_PATH.read_text(encoding="utf-8"))
        self.assertEqual(manifest["baseline_commit"],
                         "568b339a1bb3ebc3f025d74762ae66c344278be9")
        self.assertEqual([row["order"] for row in manifest["ordered_patches"]],
                         list(range(1, 12)))
        for row in manifest["ordered_patches"]:
            data = canonical(ROOT / row["source_path"])
            raw, blob = identities(data)
            self.assertEqual((raw, blob),
                             (row["raw_sha256"], row["raw_git_blob"]))
        with tempfile.TemporaryDirectory(prefix="pg10-2-release-") as temporary:
            work = Path(temporary)
            derived = build_derived(manifest, work)
            package = {}
            for row in manifest["files"]:
                if row["role"] == "DERIVED_BASE_PLUS_11":
                    data = derived[row["package_path"]]
                else:
                    data = canonical(ROOT / row["package_path"])
                raw, blob = identities(data)
                self.assertEqual((raw, blob),
                                 (row["raw_sha256"], row["raw_git_blob"]), row)
                self.assertEqual(blob, row["filtered_git_blob"])
                package[row["package_path"]] = data
            for row in manifest["ordered_patches"]:
                package[row["package_path"]] = canonical(ROOT / row["source_path"])
            package[MANIFEST_PATH.name] = canonical(MANIFEST_PATH)
            self.assertIn("ControlCenter/cc/v20_contract.py", package)
            self.assertEqual(manifest["files"][0]["raw_git_blob"],
                             "98037310ee5238f035ae174285a2f244cc1aeffd")
            self.assertEqual(manifest["files"][1]["raw_git_blob"],
                             "7f963423aa0e957d4eb5408aa1b77143c270b688")

            def archive():
                output = io.BytesIO()
                with zipfile.ZipFile(output, "w", zipfile.ZIP_DEFLATED,
                                     compresslevel=9) as bundle:
                    for name, data in sorted(package.items()):
                        info = zipfile.ZipInfo(name, (2026, 11, 28, 0, 0, 0))
                        info.compress_type = zipfile.ZIP_DEFLATED
                        info.create_system = 3
                        info.external_attr = 0o100644 << 16
                        bundle.writestr(info, data)
                return output.getvalue()

            first, second = archive(), archive()
            self.assertEqual(first, second)
            with zipfile.ZipFile(io.BytesIO(first)) as bundle:
                self.assertIsNone(bundle.testzip())
                self.assertEqual(set(bundle.namelist()), set(package))
            print("PG10_2_PACKAGE_FILES=" + str(len(package)))
            print("PG10_2_PACKAGE_SHA256=" + sha256(first).hexdigest())
            if os.environ.get("PG10_2_PACKAGE_OUT"):
                Path(os.environ["PG10_2_PACKAGE_OUT"]).write_bytes(first)

    def test_launcher_pins_cc_compatibility_and_rollback_guards(self):
        manifest = json.loads(MANIFEST_PATH.read_text(encoding="utf-8"))
        by_role = {row["role"]: row for row in manifest["files"]}
        launcher = canonical(RELEASE / "pg10-2-v20-08-live-launch.ps1").decode()
        controller = canonical(ROOT / "ControlCenter/controller/cc07-v20-operator.ps1").decode()
        admin = canonical(ROOT / "ControlCenter/v20_admin_control.py").decode()
        manual = canonical(ROOT / "ControlCenter/cc/v20_manual_export.py").decode()
        installer = canonical(RELEASE / "pg10-2-all3-cc-install.ps1").decode()
        self.assertIn(by_role["DERIVED_BASE_PLUS_11"]["filtered_git_blob"], launcher)
        self.assertIn("98037310ee5238f035ae174285a2f244cc1aeffd", launcher)
        self.assertIn("7f963423aa0e957d4eb5408aa1b77143c270b688", launcher)
        self.assertIn("dd55f201b3e9a92ce5fa3f927289f5a5ef89366d", launcher)
        self.assertIn(by_role["LAUNCHER"]["filtered_git_blob"], controller)
        self.assertIn(by_role["CC_CONTROLLER"]["filtered_git_blob"], admin)
        self.assertIn(by_role["CC_EXPORTER"]["filtered_git_blob"], manual)
        self.assertIn(by_role["CC_HISTORY"]["filtered_git_blob"], manual)
        self.assertIn("EXT2 OFF", manifest["safety"]["strategy"])
        self.assertIn("state_restore='FORBIDDEN_AUTOMATICALLY'", installer)
        self.assertIn("PG10_2_DURABLE_STATE_AND_UNKNOWN_INTENTS=UNTOUCHED", installer)
        self.assertIn("PG10_2_REFUSE_DELETE_UNKNOWN_FILE", installer)
        self.assertNotIn("Invoke-RestMethod", installer)
        self.assertNotIn("pip install", installer)
        self.assertNotIn("-mode arm", installer)
        self.assertNotIn("Remove-Item", installer)
        check = installer.split("if($mode -eq 'check')", 1)[1].split(
            "need ($env:OS", 1)[0]
        self.assertIn("verify-installed $false", check)
        self.assertIn("KNOWN_OLD_OR_NEW", check)
        control = manifest["conversion_control"]
        self.assertNotEqual(control["crlf_raw_git_blob"], control["filtered_git_blob"])
        self.assertNotEqual(control["crlf_raw_sha256"],
                            identities(canonical(ROOT / control["path"]))[0])

    def test_windows_functional_install_recovery_and_cc_restart(self):
        if os.name != "nt":
            self.skipTest("native Windows synthetic installer functions")
        manifest = json.loads(MANIFEST_PATH.read_text(encoding="utf-8"))
        with tempfile.TemporaryDirectory(prefix="pg10-2-functional-") as temporary:
            root = Path(temporary)
            build = root / "build"
            package = root / "package"
            derived = build_derived(manifest, build)
            for row in manifest["files"]:
                data = derived[row["package_path"]] if row["role"] == "DERIVED_BASE_PLUS_11" else canonical(ROOT / row["package_path"])
                path = package / row["package_path"]
                path.parent.mkdir(parents=True, exist_ok=True)
                path.write_bytes(data)
            path = package / MANIFEST_PATH.name
            path.write_bytes(canonical(MANIFEST_PATH))
            harness = r'''
$ErrorActionPreference='Stop'
Set-StrictMode -Version Latest
$source=Get-Content -LiteralPath $env:PG_INSTALLER -Raw -Encoding UTF8
$cut=[regex]::Match($source,'(?m)^verify-package\r?$')
if(-not $cut.Success){throw 'FUNCTION_TOP_LEVEL_BOUNDARY_MISSING'}
$source=$source.Substring(0,$cut.Index)
$definitions=[regex]::Matches($source,'(?ms)^function\s+.*?(?=^function\s+|\z)')
foreach($definition in $definitions){Invoke-Expression $definition.Value}
$v20=Join-Path $env:PG_ROOT 'V20Lab'
$cc=Join-Path $env:PG_ROOT 'Control Center'
$panel=Join-Path $cc 'v20-preview-d80f2446'
$stage=Join-Path $v20 'pretrade-08\live-08'
$runtime=Join-Path $v20 'pretrade-08\live-runtime-08\V20_TradingSystem_M15\v20_runtime'
$pythonCC=Join-Path $cc 'runtime\python312\python.exe'
$robots=@('v20-shallow','v20-obv','v20-inside')
$PackageRoot=$env:PG_PACKAGE
$BackupRoot=$env:PG_BACKUP
$manifestPath=Join-Path $PackageRoot 'pg10-2-release-manifest.json'
$release=Get-Content -LiteralPath $manifestPath -Raw -Encoding UTF8|ConvertFrom-Json
$releaseSha=sha256 ([IO.File]::ReadAllBytes($manifestPath))
$RecoveryPhrase=''
$ccMutex=$null
$ccMutexHeld=$false
$items=@($release.files|Where-Object {$_.install -ne 'none'})
foreach($item in $items){
 $path=target ([string]$item.install) ([string]$item.source_path)
 [IO.Directory]::CreateDirectory((Split-Path $path -Parent))|Out-Null
 [IO.File]::WriteAllBytes($path,[Text.Encoding]::UTF8.GetBytes('old-known-byte-content '+$item.source_path))
}
[IO.Directory]::CreateDirectory((Split-Path $pythonCC -Parent))|Out-Null
[IO.File]::WriteAllBytes($pythonCC,[Text.Encoding]::ASCII.GetBytes('synthetic-python'))
backup-targets $BackupRoot $true
$backup=backup-verify $BackupRoot
$tx=[ordered]@{schema='pg10.2.install-transaction.v1';id='0123456789abcdef0123456789abcdef';release_sha256=$releaseSha;backup_sha256=sha256 ([IO.File]::ReadAllBytes((Join-Path $BackupRoot 'backup.json')));status='PREPARED';coherent_before=$true;cc_was_running=$true;last_write_id='';created_utc=[datetimeoffset]::UtcNow.ToString('o');updated_utc=[datetimeoffset]::UtcNow.ToString('o')}
write-json (transaction-path) $tx $false
$tx=transaction-read
$script:flatCalls=0
function broker-flat([string]$path){$script:flatCalls++}
broker-flat-for-state 'NEW' $tx.id
need ($script:flatCalls -eq 1) 'COHERENT_FLAT_PATH_NOT_USED'
$refused=$false
try{broker-flat-for-state 'MIXED' $tx.id}catch{$refused=$_.Exception.Message -ceq 'PG10_2_MIXED_RUNTIME_REQUIRES_EXTERNAL_FINAM_READONLY_FLAT'}
need ($refused -and $script:flatCalls -eq 1) 'MIXED_FLAT_GATE_BYPASSED'
$RecoveryPhrase='PG10_2_EXTERNAL_FINAM_READONLY_FLAT_CONFIRMED '+$tx.id
broker-flat-for-state 'MIXED' $tx.id
need ($script:flatCalls -eq 1) 'MIXED_EXTERNAL_FLAT_NOT_SEPARATE'
for($i=0;$i -lt 3;$i++){install-file $items[$i] $tx}
transaction-write $tx 'INTERRUPTED'
assert-targets-known $backup
$unknownItem=$items[4]
$unknownPath=target ([string]$unknownItem.install) ([string]$unknownItem.source_path)
$knownNew=[IO.File]::ReadAllBytes((Join-Path $PackageRoot ([string]$unknownItem.package_path).Replace('/','\')))
[IO.File]::WriteAllBytes($unknownPath,[Text.Encoding]::UTF8.GetBytes('unknown-not-old-or-new'))
$rejected=$false
try{assert-targets-known $backup}catch{$rejected=$_.Exception.Message -match 'PG10_2_UNKNOWN_TARGET_BYTES_'}
need ($rejected) 'UNKNOWN_BYTES_ACCEPTED'
need (([Text.Encoding]::UTF8.GetString([IO.File]::ReadAllBytes($unknownPath))) -ceq 'unknown-not-old-or-new') 'UNKNOWN_BYTES_OVERWRITTEN'
[IO.File]::WriteAllBytes($unknownPath,$knownNew)
restore-targets $BackupRoot $backup
verify-backup-installed $backup
transaction-write $tx 'RECOVERED'
need ((transaction-read).status -ceq 'RECOVERED') 'RECOVERY_STATE_NOT_DURABLE'
Write-Output 'PG10_2_FUNCTIONAL_INTERRUPTED_RECOVERY=PASS_ATOMIC_KNOWN_BYTES_ONLY'
assert-restore-compatible
foreach($name in @('cc07-requests','cc07-release-history')){
 $folder=Join-Path $cc ('data\private\'+$name)
 [IO.Directory]::CreateDirectory($folder)|Out-Null
 $marker=Join-Path $folder 'request-evidence.jsonl'
 [IO.File]::WriteAllText($marker,'request-id-preserved',[Text.UTF8Encoding]::new($false))
 $blocked=$false
 try{assert-restore-compatible}catch{$blocked=$_.Exception.Message -ceq 'PG10_2_ROLLBACK_NEW_RECOVERY_JOURNALS_FORWARD_RECOVERY_REQUIRED'}
 need ($blocked -and [IO.File]::ReadAllText($marker) -ceq 'request-id-preserved') 'RECOVERY_JOURNAL_ROLLBACK_NOT_BLOCKED'
 [IO.File]::Delete($marker)
}
foreach($folder in @((Join-Path $cc 'data\control-audit\archive'),(Join-Path $v20 'robots\shallow\logs\archive'))){
 [IO.Directory]::CreateDirectory($folder)|Out-Null
 $marker=Join-Path $folder 'rotated-evidence.jsonl'
 [IO.File]::WriteAllText($marker,'archive-preserved',[Text.UTF8Encoding]::new($false))
 $blocked=$false
 try{assert-restore-compatible}catch{$blocked=$_.Exception.Message -match 'PG10_2_ROLLBACK_ROTATED_.*_FORWARD_RECOVERY_REQUIRED'}
 need ($blocked -and [IO.File]::ReadAllText($marker) -ceq 'archive-preserved') 'ARCHIVE_ROLLBACK_NOT_BLOCKED'
 [IO.File]::Delete($marker)
}
Write-Output 'PG10_2_FUNCTIONAL_JOURNAL_ARCHIVE_ROLLBACK_GATE=PASS_FORWARD_REQUIRED'
$script:listenerUp=$true
$script:listenerPid=1001
$script:healthOk=$false
function cc-listener{
 if($script:listenerUp){return [pscustomobject]@{OwningProcess=$script:listenerPid}}
 return $null
}
function Get-CimInstance{
 param($ClassName,$Filter)
 return [pscustomobject]@{ProcessId=$script:listenerPid;ExecutablePath=$pythonCC;CommandLine='python -I -B -m streamlit run v20_app.py --server.port=8502'}
}
function Stop-Process{param($Id,$ErrorAction);need ($Id -eq $script:listenerPid) 'WRONG_CC_PID_STOPPED';$script:listenerUp=$false}
function Start-Process{
 param($FilePath,$ArgumentList,$WorkingDirectory,$WindowStyle,$RedirectStandardOutput,$RedirectStandardError,$PassThru)
 $script:listenerPid=2001;$script:listenerUp=$true
 return [pscustomobject]@{Id=2001;HasExited=$false}
}
function Invoke-WebRequest{
 param($Uri,$UseBasicParsing,$TimeoutSec)
 $content=if($script:healthOk){'ok'}else{'not-ready'}
 return [pscustomobject]@{StatusCode=200;Content=$content}
}
need ((cc-running) -eq 1001) 'CC_EXISTING_PROCESS_NOT_RECOGNIZED'
need (stop-cc) 'CC_WAS_RUNNING_NOT_RECORDED'
need ($null -eq (cc-listener)) 'CC_LISTENER_NOT_STOPPED'
$healthRefused=$false
try{start-cc $false $backup $tx}catch{$healthRefused=$_.Exception.Message -ceq 'PG10_2_CC_HEALTH_NOT_PROVEN'}
need ($healthRefused) 'CC_FALSE_RUNNING_PASS_ACCEPTED'
$script:listenerUp=$false
$script:healthOk=$true
$ccOutput=@(start-cc $false $backup $tx) -join '|'
need ($ccOutput -match 'PG10_2_CC_RUNNING=PASS_NEW_PROCESS_LOOPBACK_HEALTH_AND_BACKUP_SOURCE_IDS') 'CC_VERIFIED_RESTART_MISSING'
need ((cc-running) -eq 2001) 'CC_NEW_PROCESS_NOT_OBSERVED'
Write-Output 'PG10_2_FUNCTIONAL_CC_RESTART=PASS_PROCESS_LISTENER_HEALTH_IDS_NO_COMMANDS'
'''
            script = root / "functional-install.ps1"
            script.write_text(harness, encoding="utf-8-sig")
            environment = os.environ.copy()
            environment.update(PG_ROOT=str(root / "runtime"),
                               PG_INSTALLER=str(RELEASE / "pg10-2-all3-cc-install.ps1"),
                               PG_PACKAGE=str(package), PG_BACKUP=str(root / "recovery"))
            result = subprocess.run(
                ["powershell.exe", "-noprofile", "-noninteractive",
                 "-executionpolicy", "bypass", "-file", str(script)],
                cwd=root, env=environment, capture_output=True, text=True,
                timeout=45, check=False)
            self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
            for marker in ("PG10_2_FUNCTIONAL_INTERRUPTED_RECOVERY=PASS",
                           "PG10_2_FUNCTIONAL_JOURNAL_ARCHIVE_ROLLBACK_GATE=PASS",
                           "PG10_2_FUNCTIONAL_CC_RESTART=PASS"):
                self.assertIn(marker, result.stdout)

    def test_new_powershell_files_parse_without_execution(self):
        if os.name != "nt":
            self.skipTest("native Windows PowerShell parser")
        for path in (RELEASE / "pg10-2-v20-08-live-launch.ps1",
                     RELEASE / "pg10-2-all3-cc-install.ps1"):
            literal = str(path).replace("'", "''")
            command = ("$e=$null;$t=$null;[void][System.Management.Automation.Language.Parser]::"
                       "ParseFile('" + literal + "',[ref]$t,[ref]$e);"
                       "if($e.Count){$e|Out-String|Write-Output;exit 1}")
            result = subprocess.run(
                ["powershell.exe", "-noprofile", "-noninteractive", "-command", command],
                capture_output=True, text=True, timeout=20, check=False)
            self.assertEqual(result.returncode, 0, result.stdout + result.stderr)


if __name__ == "__main__":
    unittest.main()
