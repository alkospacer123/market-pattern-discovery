"""CLI for the frozen experimental M5 EMA50 NORMAL TRUE-OOS replay."""
from argparse import ArgumentParser
from pathlib import Path

from .true_oos.m5_experimental_ema50 import OUTPUT, run

if __name__ == "__main__":
    parser = ArgumentParser()
    parser.add_argument("--data-root", type=Path, default=Path("/workspace/market-pattern-data"))
    parser.add_argument("--output", type=Path, default=OUTPUT)
    args = parser.parse_args()
    print(run(args.data_root, args.output)["status"])
