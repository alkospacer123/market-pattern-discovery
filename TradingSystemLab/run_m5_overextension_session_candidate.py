"""Run M5 overextension and session candidate validation."""
from __future__ import annotations

import argparse
import json
from pathlib import Path

from .timeframe_analysis.m5_overextension_session_candidate import DATA, OPTIMIZATION, OUTPUT, VALIDATION, run


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--validation", type=Path, default=VALIDATION)
    parser.add_argument("--optimization", type=Path, default=OPTIMIZATION)
    parser.add_argument("--data", type=Path, default=DATA)
    parser.add_argument("--output", type=Path, default=OUTPUT)
    parser.add_argument("--usd-data", type=Path, nargs="+")
    parser.add_argument("--cny-data", type=Path, nargs="+")
    args = parser.parse_args()
    supplied = args.usd_data is not None or args.cny_data is not None
    if supplied and (args.usd_data is None or args.cny_data is None):
        parser.error("--usd-data and --cny-data must be supplied together")
    market = {"USDRUBF": args.usd_data, "CNYRUBF": args.cny_data} if supplied else None
    print(json.dumps(run(args.validation, args.optimization, args.data, args.output, market), indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
