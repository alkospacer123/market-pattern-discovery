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
                data = path.read_bytes().replace(b"\r\n", b"\n")
                derived["V20_TradingSystem_M15/v20_runtime/" + name] = data
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
