"""CLI for the isolated BBW CORE v1 execution replay."""
from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys

from .core_execution import CoreExecutionError
from .core_execution.replay import run_execution_replay


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Run TRAIN-only BBW CORE v1 execution replay")
    parser.add_argument("--symbol", required=True)
    parser.add_argument("--feature-root", required=True, type=Path)
    parser.add_argument("--normalized-root", required=True, type=Path)
    parser.add_argument("--candidate-root", required=True, type=Path)
    parser.add_argument("--baseline-root", required=True, type=Path)
    parser.add_argument("--output-root", required=True, type=Path)
    args = parser.parse_args(argv)
    try:
        result = run_execution_replay(**vars(args))
        print(json.dumps(result, sort_keys=True))
        return 0
    except (CoreExecutionError, OSError, ValueError, KeyError, json.JSONDecodeError) as exc:
        print(f"CORE_EXECUTION_FAILED: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
