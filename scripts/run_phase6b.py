#!/usr/bin/env python3
import argparse
from market_pattern_discovery.backtest.phase6b import run

p=argparse.ArgumentParser(); p.add_argument("--data-root",default="/workspace/market-pattern-data"); p.add_argument("--output",default="results/phase6b")
args=p.parse_args(); print(run(args.data_root,args.output))
