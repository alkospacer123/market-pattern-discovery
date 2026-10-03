"""Trading System Lab research engine.

Research dependencies are imported lazily so safety-only tooling remains
usable in a deliberately minimal offline operator environment.
"""

__all__ = ["Backtester", "BacktestResult"]


def __getattr__(name):
    if name in __all__:
        from .core.backtester import Backtester, BacktestResult
        return {"Backtester": Backtester, "BacktestResult": BacktestResult}[name]
    raise AttributeError(name)
