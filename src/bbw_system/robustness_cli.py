"""Command line entry point for Candidate Baseline v1 robustness research."""
from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys

from .robustness import RobustnessError, run_candidate_robustness


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Run deterministic TRAIN-only BBW robustness research")
    parser.add_argument("--symbol", required=True)
    parser.add_argument("--candidate-root", required=True, type=Path)
    parser.add_argument("--feature-root", required=True, type=Path)
    parser.add_argument("--normalized-root", required=True, type=Path)
    parser.add_argument("--output-root", required=True, type=Path)
    args = parser.parse_args(argv)
    try:
        result = run_candidate_robustness(args.feature_root, args.normalized_root,
                                          args.candidate_root, args.output_root,
                                          args.symbol.upper())
        print(json.dumps(result, sort_keys=True))
        return 0
    except (RobustnessError, OSError, ValueError, KeyError, json.JSONDecodeError) as exc:
        print(f"Robustness failed closed: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
