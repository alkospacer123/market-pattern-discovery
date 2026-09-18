"""CLI for locked, execution-only M15 TRUE OOS validation."""
from __future__ import annotations

from argparse import ArgumentParser
from pathlib import Path

from .true_oos.m15 import run


if __name__ == "__main__":
    parser = ArgumentParser()
    parser.add_argument("--data-root", type=Path, default=Path("/workspace/market-pattern-data"))
    parser.add_argument("--output", type=Path, default=Path("TradingSystemLab/results/true_oos_validation/M15"))
    args = parser.parse_args()
    print(run(args.data_root, args.output)["status"])
