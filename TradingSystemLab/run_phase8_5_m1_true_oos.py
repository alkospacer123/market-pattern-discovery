"""Run Phase 8.5 M1 TRUE-OOS validation."""
from __future__ import annotations

import argparse
import json
from pathlib import Path

from .multitimeframe.phase71 import APPROVED_DATA_ROOT
from .optimization.phase82 import OUTPUT as PHASE82_ROOT
from .robustness.phase83 import OUTPUT as PHASE83_ROOT
from .true_oos.phase85 import OUTPUT, run
from .walk_forward.phase84 import OUTPUT as PHASE84_ROOT


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--data-root", type=Path, default=APPROVED_DATA_ROOT)
    parser.add_argument("--output", type=Path, default=OUTPUT)
    parser.add_argument("--phase82-root", type=Path, default=PHASE82_ROOT)
    parser.add_argument("--phase83-root", type=Path, default=PHASE83_ROOT)
    parser.add_argument("--phase84-root", type=Path, default=PHASE84_ROOT)
    args = parser.parse_args()
    print(json.dumps(run(args.data_root, args.output, args.phase83_root, args.phase84_root,
                         args.phase82_root), indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
