"""Reproducible V20-05 acceptance using existing tests and a FakeBroker only.

Native Windows evidence requires --windows on an actual Windows interpreter.
No installer, scheduler, broker transport, credentials or historical replay.
"""
import argparse
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import platform
import subprocess
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[2]
PREFIX = "V20_TradingSystem_M15.v20_runtime.tests."
TESTS = [
    PREFIX+"test_h1_execution",
    PREFIX+"test_m15_runner.M15LoopTests",
    PREFIX+"test_system_acceptance",
    # Only card causality/independence, no renewed indicator research.
    *[PREFIX+"test_market_suitability.SuitabilityCardTests."+name for name in (
        "test_three_readonly_robot_cards_never_filter",
        "test_future_session_and_premature_bar_blocked",
        "test_last20_rolls_and_older_session_disappears",
        "test_bidirectional_metric_changes_not_verdicts")],
]


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def git(*args):
    return subprocess.check_output(["git", *args], cwd=ROOT, text=True).strip()


class RecordedResult(unittest.TextTestResult):
    def __init__(self, *a, **kw):
        super().__init__(*a, **kw)
        self.passed = []

    def addSuccess(self, test):
        super().addSuccess(test)
        self.passed.append(test.id())


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--offline", required=True, action="store_true")
    p.add_argument("--windows", action="store_true")
    p.add_argument("--scratch-base", type=Path, required=True)
    p.add_argument("--report", type=Path, required=True)
    args = p.parse_args()
    if args.windows and os.name != "nt":
        p.error("WINDOWS_NOT_AVAILABLE: Linux tests cannot establish Windows PASS")
    report_path = args.report.resolve()
    if any(part.casefold() in {"tradingsystemlab", "intradaylab", ".git"} for part in report_path.parts):
        p.error("Protected report path forbidden")
    v20 = ROOT/"V20_TradingSystem_M15"
    if ROOT in report_path.parents and v20 not in report_path.parents:
        p.error("Only V20 files may be written inside checkout")
    scratch = args.scratch_base.resolve()
    if ROOT == scratch or ROOT in scratch.parents or scratch.is_symlink():
        p.error("Acceptance scratch must be outside checkout")
    if any(part.casefold() in {"tradingsystemlab", "intradaylab", ".git"} for part in scratch.parts):
        p.error("Protected project path forbidden")
    scratch.mkdir(parents=True, exist_ok=True)
    # Same fixture layout on Linux and Windows, including spaces in the path.
    with tempfile.TemporaryDirectory(prefix="v20 acceptance ", dir=scratch) as temporary:
        previous = tempfile.tempdir
        tempfile.tempdir = temporary
        try:
            proof_file = ROOT/"V20_TradingSystem_M15/V20-04/OFFLINE_FRAMEWORK_ACCEPTANCE.json"
            proof = json.loads(proof_file.read_text())
            prior_sources = proof["source_sha256"]
            before = {f: sha(ROOT/f) for f in prior_sources}
            before["TradingSystemLab/stage8_robot/trading_safety_gate.py"] = sha(
                ROOT/"TradingSystemLab/stage8_robot/trading_safety_gate.py")
            source_mismatch = [f for f, record in prior_sources.items() if before[f] != record["sha256"]]
            if source_mismatch:
                raise RuntimeError("Prior evidence changed: "+str(source_mismatch))
            from .tests.test_system_acceptance import EVIDENCE
            EVIDENCE.clear()
            suite = unittest.defaultTestLoader.loadTestsFromNames(TESTS)
            result = unittest.TextTestRunner(verbosity=2, resultclass=RecordedResult).run(suite)
            after = {f: sha(ROOT/f) for f in before}
            integrity = before == after
            passed = result.wasSuccessful() and not result.skipped and integrity
            code = {str(f.relative_to(ROOT)): sha(f) for f in sorted(
                (ROOT/"V20_TradingSystem_M15/v20_runtime").glob("*.py"))
                if f.name in {"offline_acceptance.py", "m15_runner.py", "h1_execution.py",
                              "account_risk.py", "frozen_adapter.py", "h1_state_journal.py", "offline_planner.py",
                              "market_suitability.py"}}
            code[str((v20/"v20_runtime/robots.json").relative_to(ROOT))] = sha(v20/"v20_runtime/robots.json")
            test_hashes = {str(f.relative_to(ROOT)): sha(f) for f in sorted(
                (ROOT/"V20_TradingSystem_M15/v20_runtime/tests").glob("*.py"))
                if f.name in {"test_h1_execution.py", "test_m15_runner.py", "test_system_acceptance.py",
                              "acceptance_child.py", "test_market_suitability.py"}}
            report = dict(
                schema="v20.offline_acceptance.v1", generated_utc=datetime.now(timezone.utc).isoformat(),
                main_sha=git("rev-parse", "origin/main"), input_pr_head=git("rev-parse", "HEAD"),
                branch=git("branch", "--show-current"), pr=567, draft=True,
                mode="OFFLINE_EXACT_FAKE_ONLY", platform=platform.platform(), python=sys.version,
                overall="PASS_OFFLINE_AND_WINDOWS" if passed and args.windows else
                        "PARTIAL_WINDOWS_BLOCKED" if passed else "FAIL",
                stages={**{f"V20-05.{i}": "PASS_OFFLINE" if passed else "FAIL" for i in range(1, 5)},
                        "V20-05.5": "PASS_NATIVE_WINDOWS" if passed and args.windows else
                                       "FAIL" if args.windows else "BLOCKED_NOT_RUN"},
                tests=dict(run=result.testsRun, passed=len(result.passed), failed=len(result.failures),
                           errors=len(result.errors), skipped=len(result.skipped),
                           successful_ids=result.passed,
                           failures=[dict(test=t.id(), detail=detail) for t, detail in result.failures+result.errors]),
                processes=EVIDENCE,
                reused=dict(receipt=str(proof_file.relative_to(ROOT)), receipt_sha256=sha(proof_file),
                            base_commit="d8eaef215efdd05cc8ace7e664d51b791e2da976",
                            tests=99, source_mismatches=source_mismatch,
                            frozen_parity="18 CNY/GLD/IMOEX signals + prior 6 USD; original proof reused",
                            three_real_frozen_process_signals=proof["processes"]["signals"],
                            rerun_changed_modules=["h1_execution", "m15_runner"],
                            no_heavy_replay=True),
                source_integrity=dict(status="PASS" if integrity else "FAIL", sha256=after),
                code_sha256=code, test_sha256=test_hashes,
                fixed_defects=[dict(id="V20_EXIT_WITH_UNCONFIRMED_STOP", reproduced=True,
                                    before="FAIL: protection error also prohibited verified-position exit",
                                    after="PASS: halt entries, no stop retry, preserve verified-quantity exit")],
                windows=dict(status="RUN" if args.windows else "NOT_RUN_BLOCKED", native=os.name == "nt",
                             reason=None if args.windows else "No Windows executor/VPN/private TCP grants or configured capability",
                             script="V20_TradingSystem_M15/V20-05/Invoke-OfflineAcceptance.ps1"),
                limitations=[
                    "Synthetic process signal and adverse/fault fixtures are plumbing acceptance, not historical PnL.",
                    "Protection rejected/missing is an explicitly injected fault: halt entries; never claim that position protected.",
                    "Unknown ENTRY/EXIT POST or conflicting broker/SQLite position remains blocked; no fabricated safe quantity.",
                    "Crash after decision claim can skip one NEXT_OPEN; no delayed replay entry.",
                    "Partial-fill VWAP stop replacement is unverified: keep installed 100% stop and halt entries.",
                    "Fake account GO/cash are synthetic. Real FINAM transport, freshness and bounded history remain unverified.",
                    "H1 kill-switch file format reused only inside V20 instance; ARMED authorizes fake fixtures only.",
                    "No FINAM auth/orders, Windows Tasks, Intel deployment or Merge performed.",
                ],
                not_run=["Native Windows (unless --windows)", "FINAM physical accounts/transport",
                         "1589-trade replay and historical market research (reused unchanged evidence)"],
                next="Complete native Windows 05.5; then V20-06.1 account binding READONLY with owner-provided accounts",
                reproduce="python -m V20_TradingSystem_M15.v20_runtime.offline_acceptance --offline "
                          "--scratch-base <external-directory> --report <report.json>")
            args.report.parent.mkdir(parents=True, exist_ok=True)
            args.report.write_text(json.dumps(report, ensure_ascii=False, indent=2)+"\n", encoding="utf-8")
            print(json.dumps(dict(overall=report["overall"], tests=report["tests"]["run"], report=str(args.report))))
            return 0 if passed else 1
        finally:
            tempfile.tempdir = previous


if __name__ == "__main__":
    raise SystemExit(main())
