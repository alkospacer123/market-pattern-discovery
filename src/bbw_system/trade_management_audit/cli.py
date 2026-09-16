"""Command line interface for the isolated BBW trade-management audit."""
from __future__ import annotations

import argparse
import json
from pathlib import Path

from .audit import run_trade_management_audit


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--feature-root", type=Path, required=True)
    parser.add_argument("--normalized-root", type=Path, required=True)
    parser.add_argument("--output-root", type=Path, required=True)
    parser.add_argument("--symbol", default="CNYRUBF")
    parser.add_argument("--config", type=Path)
    args = parser.parse_args(argv)
    result = run_trade_management_audit(args.feature_root, args.normalized_root, args.output_root,
                                        args.symbol, args.config)
    print(json.dumps(result, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
