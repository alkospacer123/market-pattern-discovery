"""Run strict H4 bounded-OAT development optimization."""
from .timeframe_optimization.h4 import run


if __name__ == "__main__":
    print(run()["status"])
