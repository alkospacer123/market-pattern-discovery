"""Command-line runner for M30 frozen-candidate robustness validation."""
from .timeframe_analysis.m30_robustness import run

if __name__ == "__main__":
    print(run()["status"])
