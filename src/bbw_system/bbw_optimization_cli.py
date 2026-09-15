"""CLI for controlled BBW Baseline parameter sensitivity research."""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from .optimization import OptimizationError, run_optimization


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Run deterministic TRAIN-only BBW parameter sensitivity")
    parser.add_argument("--symbol", required=True)
    parser.add_argument("--feature-root", required=True, type=Path)
    parser.add_argument("--normalized-root", required=True, type=Path)
    parser.add_argument("--baseline-root", required=True, type=Path)
    parser.add_argument("--output-root", required=True, type=Path)
    parser.add_argument("--grid-limit", type=int, default=256,
                        help="deterministic bounded-grid size (default: 256)")
    parser.add_argument("--transaction-cost-r", type=float, default=0.0)
    parser.add_argument("--slippage-r", type=float, default=0.0)
    args = parser.parse_args(argv)
    try:
        result = run_optimization(args.feature_root, args.normalized_root, args.baseline_root,
            args.output_root, args.symbol.upper(), grid_limit=args.grid_limit,
            transaction_cost_r=args.transaction_cost_r, slippage_r=args.slippage_r)
        print(json.dumps(result, sort_keys=True))
        return 0
    except (OptimizationError, OSError, ValueError, KeyError, json.JSONDecodeError) as exc:
        print(f"Optimization failed closed: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
