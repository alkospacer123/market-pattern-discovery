"""Run the deterministic M5 main-session candidate comparison."""
from __future__ import annotations

import argparse
import json
from pathlib import Path

from .timeframe_analysis.m5_session_candidate import OPTIMIZATION, OUTPUT, VALIDATION, run


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--validation", type=Path, default=VALIDATION)
    parser.add_argument("--optimization", type=Path, default=OPTIMIZATION)
    parser.add_argument("--output", type=Path, default=OUTPUT)
    args = parser.parse_args()
    print(json.dumps(run(args.validation, args.optimization, args.output), indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
