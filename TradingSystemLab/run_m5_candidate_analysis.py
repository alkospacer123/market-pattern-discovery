"""Run deterministic read-only M5 candidate hypothesis analysis."""
from __future__ import annotations

import argparse
import json
from pathlib import Path

from .timeframe_analysis.m5_candidates import DIAGNOSTICS, OUTPUT, VALIDATION, run


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--diagnostics", type=Path, default=DIAGNOSTICS)
    parser.add_argument("--validation", type=Path, default=VALIDATION)
    parser.add_argument("--output", type=Path, default=OUTPUT)
    args = parser.parse_args()
    print(json.dumps(run(args.diagnostics, args.validation, args.output), indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
