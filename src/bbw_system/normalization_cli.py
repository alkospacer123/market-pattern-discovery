"""Command-line entry point for BBW 03B-3 normalization."""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from .normalization import run_normalization


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Normalize hash-verified frozen CNYRUBF bars")
    parser.add_argument("--freeze-root", required=True, type=Path)
    parser.add_argument("--output-root", type=Path, default=Path("data/normalized/CNYRUBF"))
    parser.add_argument("--metadata", type=Path, default=Path("bbw_system/config/instruments/cnyrubf.yaml"))
    args = parser.parse_args(argv)
    try:
        run_normalization(args.freeze_root, args.output_root, args.metadata)
        return 0
    except (OSError, ValueError, KeyError, json.JSONDecodeError) as exc:
        print(f"normalization failed closed: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
