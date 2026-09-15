"""Command-line entry point for Phase 7.1 descriptive research."""
from __future__ import annotations

import argparse
import json
from pathlib import Path

from .multitimeframe.phase71 import APPROVED_DATA_ROOT, run


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--data-root", type=Path, default=APPROVED_DATA_ROOT)
    parser.add_argument("--output", type=Path, default=Path("TradingSystemLab/results/multitimeframe_research"))
    args = parser.parse_args()
    print(json.dumps(run(args.data_root, args.output), indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
