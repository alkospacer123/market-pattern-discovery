"""Temporal and causal validation contracts (loaded lazily to avoid data-layer cycles)."""

__all__ = ["DataPartition", "DataSplit", "Period", "ValidationEngine", "ValidationReport",
           "ValidationStatus", "ValidationThresholds", "WalkForwardWindow"]


def __getattr__(name):
    if name not in __all__:
        raise AttributeError(name)
    from . import engine
    return getattr(engine, name)
