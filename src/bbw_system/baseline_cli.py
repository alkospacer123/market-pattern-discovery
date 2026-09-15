"""Command line entry point for the first BBW Baseline stage."""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from .baseline import BaselineError, default_baseline_config_path, load_baseline_config, run_baseline


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Run deterministic H1/M15 BBW Baseline")
    parser.add_argument("--feature-root", required=True, type=Path)
    parser.add_argument("--normalized-root", required=True, type=Path)
    parser.add_argument("--output-root", required=True, type=Path)
    parser.add_argument("--symbol", required=True)
    parser.add_argument("--config", type=Path, help="Baseline JSON (defaults to config/bbw_baseline.json)")
    args = parser.parse_args(argv)
    try:
        config_path = args.config or default_baseline_config_path()
        result = run_baseline(args.feature_root, args.normalized_root, args.output_root,
                              args.symbol.upper(), load_baseline_config(config_path), config_path)
        print(json.dumps(result, sort_keys=True))
        return 0
    except (BaselineError, OSError, ValueError, KeyError, json.JSONDecodeError) as exc:
        print(f"Baseline failed closed: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
