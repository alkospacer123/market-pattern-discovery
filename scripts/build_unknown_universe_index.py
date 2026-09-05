#!/usr/bin/env python3
"""Explicit slow audit/build command for the immutable UNKNOWN rank index."""
from __future__ import annotations

import argparse
import json
from pathlib import Path

from market_pattern_discovery.discovery.unknown import load_discovery_matrix
from market_pattern_discovery.orchestration import (
    PatternSearchSpace, UnknownUniverseIndex, build_unknown_universe_index,
)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--data-root", required=True, type=Path)
    parser.add_argument("--output", required=True, type=Path)
    parser.add_argument("--seed", type=int, default=20260401)
    parser.add_argument("--validate-only", action="store_true")
    args = parser.parse_args()
    space = PatternSearchSpace(
        load_discovery_matrix(args.data_root, instrument, timeframe)
        for instrument in ("CNYRUBF", "USDRUBF")
        for timeframe in ("M1", "M5"))
    if args.validate_only:
        index = UnknownUniverseIndex(args.output, space, args.seed)
        print(json.dumps(index.manifest, sort_keys=True))
    else:
        print(json.dumps(build_unknown_universe_index(
            space, args.output, seed=args.seed), sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
