#!/usr/bin/env python3
"""Run a finite number of production multi-horizon research cycles."""
from __future__ import annotations
import argparse
import json
from dataclasses import asdict
from pathlib import Path
from market_pattern_discovery.orchestration.multihorizon import MultiHorizonResearchRunner


def main(argv=None):
    parser = argparse.ArgumentParser()
    parser.add_argument("--data-root", required=True, type=Path)
    parser.add_argument("--memory-root", required=True, type=Path)
    parser.add_argument("--cycles", required=True, type=int)
    parser.add_argument("--budget", type=int, default=1)
    args = parser.parse_args(argv)
    if args.cycles <= 0 or args.budget <= 0:
        parser.error("--cycles and --budget must be positive")
    results = MultiHorizonResearchRunner(args.data_root, args.memory_root).run(
        args.cycles, budget=args.budget)
    print(json.dumps([asdict(result) for result in results], sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
