"""Command-line runner for frozen M15 robustness validation."""
from .timeframe_analysis.m15_robustness import run

if __name__ == "__main__":
    result = run()
    print(result["status"])
