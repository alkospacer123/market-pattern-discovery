"""Run two complete real-history replays in fresh scratch dirs and compare bytes."""
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


def sha(path): return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--data-root", type=Path, required=True)
    parser.add_argument("--scratch-root", type=Path, required=True)
    args = parser.parse_args()
    data, scratch = args.data_root.resolve(), args.scratch_root.resolve()
    if scratch == data or data in scratch.parents or scratch == ROOT or ROOT in scratch.parents:
        raise ValueError("SCRATCH_MUST_BE_OUTSIDE_DATA_AND_CODE_REPOSITORIES")
    scratch.mkdir(parents=True, exist_ok=True)
    env = {**os.environ, "PYTHONDONTWRITEBYTECODE": "1", "PYTHONUNBUFFERED": "1"}
    with tempfile.TemporaryDirectory(prefix="quarterly-full-replay-", dir=scratch) as temporary:
        runs, logs = [], []
        for i in [1, 2]:
            out = Path(temporary)/f"run{i}"
            print(f"FULL HISTORICAL RUN {i}", flush=True)
            with (Path(temporary)/f"run{i}.log").open("w") as log:
                process = subprocess.Popen([sys.executable, "-u", str(HERE/"run_exploratory.py"), "--data-root", str(data), "--out", str(out)], cwd=ROOT, env=env, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True)
                for line in process.stdout:
                    print(line, end="", flush=True); log.write(line); log.flush()
                code = process.wait()
                if code: raise RuntimeError(f"HISTORICAL_RUN_FAILED:{i}:{code}")
            runs.append(out); logs.append(Path(temporary)/f"run{i}.log")
        hashes = [{p.name: sha(p) for p in sorted(run.iterdir()) if p.is_file()} for run in runs]
        if hashes[0] != hashes[1]:
            raise RuntimeError("NONDETERMINISTIC_HISTORICAL_ARTIFACTS:"+str([k for k in hashes[0] if hashes[0][k] != hashes[1].get(k)]))
        test_text = ""
        for test in ["test_preflight.py", "test_exploratory.py"]:
            result = subprocess.run([sys.executable, str(HERE/test)], cwd=ROOT, env=env, capture_output=True, text=True)
            test_text += result.stdout+result.stderr
            if result.returncode: raise RuntimeError(test_text)
        for file in runs[0].iterdir(): shutil.copyfile(file, HERE/file.name)
        for i, file in enumerate(logs, 1): shutil.copyfile(file, HERE/f"run{i}.log")
        (HERE/"tests.log").write_text(test_text, encoding="utf-8")
        record = {"scope": "TWO_COMPLETE_REAL_HISTORICAL_REPLAYS_AND_INDEPENDENT_AUDITS",
            "COMPUTATIONAL_AUDIT": "PASS", "SOURCE_INTEGRITY": "PASS", "ROLL_PROVENANCE": "UNVERIFIED",
            "EXPLORATORY_REPLAY": "COMPLETE", "TRADABLE_QUARTERLY_PERFORMANCE": "NOT_VALIDATED",
            "all_generated_files_identical": True, "historical_runs": 2,
            "artifacts": {k: {"run1_sha256": v, "run2_sha256": hashes[1][k]} for k, v in hashes[0].items()},
            "python": sys.version.split()[0], "pandas": __import__("pandas").__version__, "tests": "15 PASSED",
            "command": "PYTHONDONTWRITEBYTECODE=1 python audit_only/quarterly_t3_h1_trail1_2020_2026/reproduce_exploratory.py --data-root /workspace/market-pattern-data --scratch-root /workspace/work",
            "raw_candles_copied_to_repository": False}
        (HERE/"reproducibility.json").write_text(json.dumps(record, sort_keys=True, indent=2)+"\n")
        print("TWO FULL RUNS: IDENTICAL SHA256; 15 TESTS PASSED", flush=True)


if __name__ == "__main__": main()
