"""One offline regression for Protect3's python -m __main__ class identity."""
import subprocess
import sys
import textwrap
import unittest


class Protect3ModuleIdentityTests(unittest.TestCase):
    def test_python_dash_m_module_alias_protect3_sender(self):
        script = textwrap.dedent(
            """
            import runpy, sys
            sys.argv = ["v20-finam-live", "--help"]
            try:
                runpy.run_module(
                    "V20_TradingSystem_M15.v20_runtime.finam_live",
                    run_name="__main__", alter_sys=True)
            except SystemExit as exc:
                assert exc.code == 0, exc.code
            else:
                raise AssertionError("argparse --help must exit before broker initialization")
            key = "V20_TradingSystem_M15.v20_runtime.finam_live"
            module = sys.modules.get(key)
            assert module is not None, "python -m class identity alias absent"
            assert module.V20LiveTransport.__module__ == "__main__"
            from V20_TradingSystem_M15.v20_runtime.finam_live import (
                V20LiveTransport, V20LiveJournal)
            assert V20LiveTransport is module.V20LiveTransport
            assert V20LiveJournal is module.V20LiveJournal
            print("R088_PROTECT3_LIVE_MODULE_IDENTITY=PASS_ONE_CLASS_NO_SECOND_IMPORT")
            """
        )
        result = subprocess.run(
            [sys.executable, "-B", "-c", script],
            capture_output=True, text=True, check=False, timeout=20,
        )
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertIn("R088_PROTECT3_LIVE_MODULE_IDENTITY=PASS", result.stdout)


if __name__ == "__main__":
    unittest.main()
