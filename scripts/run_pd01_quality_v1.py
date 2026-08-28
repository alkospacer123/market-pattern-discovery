#!/usr/bin/env python3
import argparse
from market_pattern_discovery.discovery.pd01_quality import run
p=argparse.ArgumentParser();p.add_argument("--data-root",default="/workspace/market-pattern-data");p.add_argument("--output",default="results/pd01_quality_v1");p.add_argument("--smoke",action="store_true")
a=p.parse_args();run(a.data_root,a.output,a.smoke)
