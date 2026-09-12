from __future__ import annotations
import argparse
from pathlib import Path
import pandas as pd

from .config import load_config
from .data import reject_true_oos, validate_ohlcv
from .reports import DiagnosticWriter
from .timeframes import synthetic_bars


def main() -> None:
    parser = argparse.ArgumentParser(description="BBW Core v1.0 causal baseline data preparation")
    parser.add_argument("--config", default="bbw_system/config/base.yaml")
    parser.add_argument("--h1", required=True, help="Read-only source CSV; timestamp denotes bar open")
    parser.add_argument("--output", default="results/bbw_baseline")
    args = parser.parse_args()
    strategy, instrument = load_config(args.config)
    raw = pd.read_csv(args.h1, parse_dates=["datetime"])
    clean, diagnostics = validate_ohlcv(raw, "1h")
    reject_true_oos(clean)
    h4 = synthetic_bars(clean, strategy.setup_hours, instrument.session)
    output = Path(args.output); output.mkdir(parents=True, exist_ok=True)
    h4.to_csv(output / "synthetic_setup_bars.csv")
    pd.DataFrame([diagnostics.__dict__]).to_json(output / "data_diagnostics.json", orient="records", indent=2)
    DiagnosticWriter().write(output)
