"""CLI for the indicator-only BBW Engine stage."""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from .bbw_engine import BBWEngineError, run_bbw_engine


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Build causal CNYRUBF H1 BBW features")
    parser.add_argument("--input-root", required=True, type=Path)
    parser.add_argument("--output-root", required=True, type=Path)
    parser.add_argument("--symbol", required=True)
    args = parser.parse_args(argv)
    try:
        result = run_bbw_engine(args.input_root, args.output_root, args.symbol.upper())
        print(json.dumps(result, sort_keys=True))
        return 0
    except (BBWEngineError, OSError, ValueError, KeyError, json.JSONDecodeError) as exc:
        print(f"BBW Engine failed closed: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
