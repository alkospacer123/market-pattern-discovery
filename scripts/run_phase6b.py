#!/usr/bin/env python3
import argparse
from market_pattern_discovery.backtest.phase6b import run,smoke
p=argparse.ArgumentParser();p.add_argument('--data-root',default='/workspace/market-pattern-data');p.add_argument('--output',default='results/phase6b');p.add_argument('--smoke',action='store_true')
a=p.parse_args();print(smoke(a.data_root) if a.smoke else run(a.data_root,a.output))
