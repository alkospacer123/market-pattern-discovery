"""CLI for all six Phase 3.2 bounded robustness experiments."""
from __future__ import annotations
import argparse, json
from pathlib import Path
from .optimization.phase32 import run_all

if __name__ == "__main__":
    parser=argparse.ArgumentParser(); parser.add_argument("--data-root",required=True,type=Path)
    parser.add_argument("--output",type=Path,default=Path("TradingSystemLab/results/optimization"))
    args=parser.parse_args(); print(json.dumps(run_all(args.data_root,args.output),indent=2))
