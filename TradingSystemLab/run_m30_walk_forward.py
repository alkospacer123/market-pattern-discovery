"""Run causal frozen-candidate M30 walk-forward validation."""
from __future__ import annotations
import json
from .walk_forward.m30 import run

if __name__ == "__main__":
    print(json.dumps(run(), indent=2, sort_keys=True))
