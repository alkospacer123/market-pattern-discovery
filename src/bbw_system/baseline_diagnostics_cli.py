"""CLI for the read-only BBW Baseline diagnostic report."""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from .baseline import BaselineError
from .baseline_diagnostics import run_baseline_diagnostics


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Generate deterministic BBW Baseline diagnostics")
    parser.add_argument("--feature-root", required=True, type=Path)
    parser.add_argument("--normalized-root", required=True, type=Path)
    parser.add_argument("--baseline-root", required=True, type=Path)
    parser.add_argument("--output-root", required=True, type=Path)
    parser.add_argument("--symbol", required=True)
    args = parser.parse_args(argv)
    try:
        print(json.dumps(run_baseline_diagnostics(args.feature_root, args.normalized_root,
              args.baseline_root, args.output_root, args.symbol.upper()), sort_keys=True))
        return 0
    except (BaselineError, OSError, ValueError, KeyError, json.JSONDecodeError) as exc:
        print(f"Baseline diagnostics failed closed: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
