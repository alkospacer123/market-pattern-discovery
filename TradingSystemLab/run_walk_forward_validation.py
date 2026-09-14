"""CLI for Phase 4 frozen walk-forward validation."""
from argparse import ArgumentParser
from pathlib import Path
from .walk_forward.phase4 import run

if __name__ == "__main__":
    parser=ArgumentParser()
    parser.add_argument("--data-root",type=Path,default=Path("/workspace/market-pattern-data"))
    parser.add_argument("--output",type=Path,default=Path("TradingSystemLab/results/walk_forward_validation"))
    args=parser.parse_args(); run(args.data_root,args.output)
