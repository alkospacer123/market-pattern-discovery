"""Two fresh blocked preflights, byte comparison, offline tests, isolated outputs.

Exit 2 is intentional: reproducible DATA_BLOCKED is not an AUDIT_PASS.
"""
import argparse
import hashlib
import json
import os
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--data-root", type=Path, required=True)
    parser.add_argument("--scratch-root", type=Path, required=True)
    args = parser.parse_args()
    data_root, scratch_root = args.data_root.resolve(), args.scratch_root.resolve()
    if data_root == scratch_root or data_root in scratch_root.parents or ROOT == scratch_root or ROOT in scratch_root.parents:
        raise ValueError("SCRATCH_MUST_BE_OUTSIDE_SOURCE_AND_CODE_REPOSITORIES")
    scratch_root.mkdir(parents=True, exist_ok=True)
    environment = {**os.environ, "PYTHONDONTWRITEBYTECODE": "1"}
    with tempfile.TemporaryDirectory(prefix="quarterly-preflight-", dir=scratch_root) as temporary:
        scratch = Path(temporary)
        runs, logs = [], []
        for i in [1, 2]:
            out = scratch/f"run{i}"
            result = subprocess.run([sys.executable, str(HERE/"preflight.py"), "--data-root", str(data_root), "--out", str(out)], cwd=ROOT, env=environment, capture_output=True, text=True)
            if result.returncode != 2:
                raise RuntimeError(f"PREFLIGHT_FAILED:{result.returncode}:{result.stderr}")
            runs.append(out)
            logs.append(f"expected_exit_code=2\nobserved_exit_code={result.returncode}\n{result.stdout}{result.stderr}")
        first = {p.name: digest(p) for p in sorted(runs[0].iterdir()) if p.is_file()}
        second = {p.name: digest(p) for p in sorted(runs[1].iterdir()) if p.is_file()}
        if first != second:
            raise RuntimeError("NONDETERMINISTIC_PREFLIGHT_ARTIFACTS")
        tests = subprocess.run([sys.executable, str(HERE/"test_preflight.py")], cwd=ROOT, env=environment, capture_output=True, text=True)
        if tests.returncode:
            raise RuntimeError(f"OFFLINE_TEST_FAILURE:{tests.stdout}{tests.stderr}")
        for path in sorted(runs[0].iterdir()):
            shutil.copyfile(path, HERE/path.name)
        for i, log in enumerate(logs, 1):
            (HERE/f"run{i}.log").write_text(log, encoding="utf-8")
        (HERE/"tests.log").write_text(tests.stdout+tests.stderr, encoding="utf-8")
        report = {"status": "BLOCKED_PREFLIGHT_REPRODUCIBLE", "technical_status": "DATA_BLOCKED",
                  "scope": "PREFLIGHT_AND_SYNTHETIC_FIXTURES_NOT_HISTORICAL_BACKTEST",
                  "two_fresh_runs": True, "all_generated_artifact_sha256_identical": True,
                  "artifacts": {name: {"run1_sha256": h, "run2_sha256": second[name]} for name, h in first.items()},
                  "historical_trade_reproducibility": "NOT_RUN_DATA_BLOCKED",
                  "offline_tests_exit_code": tests.returncode, "python_version": sys.version.split()[0],
                  "command": "PYTHONDONTWRITEBYTECODE=1 python audit_only/quarterly_t3_h1_trail1_2020_2026/reproduce.py --data-root /workspace/market-pattern-data --scratch-root /workspace/work",
                  "raw_quotes_copied": False}
        (HERE/"reproducibility.json").write_text(json.dumps(report, indent=2, sort_keys=True)+"\n", encoding="utf-8")
        print(json.dumps({k: v for k, v in report.items() if k != "artifacts"}, sort_keys=True))
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
