"""CLI for the separate BBW Optimization R2 experiment."""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from .optimization import OptimizationError
from .optimization.bbw_optimization_r2 import R2_GRID_LIMIT, run_r2_optimization


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Run deterministic TRAIN-only BBW Optimization R2")
    parser.add_argument("--symbol", required=True)
    parser.add_argument("--feature-root", required=True, type=Path)
    parser.add_argument("--normalized-root", required=True, type=Path)
    parser.add_argument("--baseline-root", required=True, type=Path)
    parser.add_argument("--output-root", type=Path, default=Path(r"C:\BBW\results\optimization\R2"))
    parser.add_argument("--grid-limit", type=int, default=R2_GRID_LIMIT)
    parser.add_argument("--transaction-cost-r", type=float, default=0.0)
    parser.add_argument("--slippage-r", type=float, default=0.0)
    args = parser.parse_args(argv)
    try:
        result = run_r2_optimization(args.feature_root, args.normalized_root, args.baseline_root,
            args.output_root, args.symbol.upper(), grid_limit=args.grid_limit,
            transaction_cost_r=args.transaction_cost_r, slippage_r=args.slippage_r)
        print(json.dumps(result, sort_keys=True))
        return 0
    except (OptimizationError, OSError, ValueError, KeyError, json.JSONDecodeError) as exc:
        print(f"Optimization R2 failed closed: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
