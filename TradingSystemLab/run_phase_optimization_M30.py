"""Run the strict M30 bounded-OAT development optimization."""
from .timeframe_optimization.m30 import run


if __name__ == "__main__":
    result = run()
    print(result["status"])
