"""Command line entry point for frozen Phase 3.3 robustness validation."""
from argparse import ArgumentParser
from pathlib import Path
from .robustness.phase33 import run

if __name__ == "__main__":
    parser=ArgumentParser(); parser.add_argument("--data-root",type=Path,required=True)
    parser.add_argument("--output",type=Path,default=Path("TradingSystemLab/results/robustness_validation"))
    parser.add_argument("--optimization-root",type=Path,default=Path("TradingSystemLab/results/optimization"))
    args=parser.parse_args(); run(args.data_root,args.output,args.optimization_root)
