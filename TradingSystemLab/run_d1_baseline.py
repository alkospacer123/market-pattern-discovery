"""Run the standalone frozen-H1-candidate D1 baseline."""
from __future__ import annotations
import argparse
import json
from pathlib import Path
from .timeframe_validation.d1_baseline import APPROVED_DATA_ROOT, OUTPUT, run


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--data-root", type=Path, default=APPROVED_DATA_ROOT)
    parser.add_argument("--output", type=Path, default=OUTPUT)
    args = parser.parse_args()
    print(json.dumps(run(args.data_root, args.output), indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
