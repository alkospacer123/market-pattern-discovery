"""Offline invocation of the exact frozen V20/V4 signal functions.

No duplicated strategy conditions, no broker, no external source modification.
This reuses the already-verified V20-03 frozen AST adapter as-is. V20-04/05
must replace its temporary CSV transport with a non-mutating in-memory
production adapter only after signal-by-signal parity is demonstrated.
"""
from __future__ import annotations

import importlib.util
import tempfile
from datetime import datetime, timedelta
from decimal import Decimal
from pathlib import Path
import pandas as pd
import numpy as np

from .offline_planner import FrozenSignal, N4, STRATEGIES

_ROOT = Path(__file__).resolve().parents[1]
_FROZEN_REPLAY_ADAPTER = _ROOT / "V20-03" / "offline" / "stress_v20_03.py"
_REQUIRED = ("Datetime", "Open", "High", "Low", "Close", "Volume")
_STEP = timedelta(minutes=15)


def _locked_adapter():
    spec = importlib.util.spec_from_file_location("v20_03_readonly_frozen_adapter", _FROZEN_REPLAY_ADAPTER)
    if spec is None or spec.loader is None:
        raise RuntimeError("PINNED_FROZEN_ADAPTER_UNAVAILABLE")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def known_m15_gap(previous, current):
    """Reuse locked observed-hole/declared-break semantics; no inferred bars."""
    return _locked_adapter().broken(previous, current)


def _frozen_immutable_features(source: pd.DataFrame) -> pd.DataFrame:
    module = _locked_adapter()
    # The locked helper needs a temporary CSV. Bind only its scratch parent to
    # an external OS workspace; BASE and every frozen AST/formula stay intact.
    # Source candles must never be copied into the repository checkout.
    with tempfile.TemporaryDirectory(prefix="v20_frozen_adapter_") as workspace:
        module.ROOT = Path(workspace) / "runtime_root"
        return module.frozen_signals(source)


def validate_completed_history(symbol: str, bars: pd.DataFrame, *, observed_at: datetime):
    """Shared immutable M15 input boundary, including stale warmup histories."""
    if symbol not in N4:
        raise ValueError("UNKNOWN_SYMBOL_OR_STRATEGY")
    if not isinstance(bars, pd.DataFrame) or bars.empty:
        raise ValueError("EMPTY_M15_INPUT")
    if any(c not in bars.columns for c in _REQUIRED):
        raise ValueError("M15_FIELDS_INCOMPLETE")
    if "Ticker" in bars and not bars["Ticker"].eq(symbol).all():
        raise ValueError("M15_MIXED_CONTRACT_OR_SYMBOL")
    if not isinstance(observed_at, datetime) or observed_at.tzinfo is not None:
        raise ValueError("MOSCOW_NAIVE_OBSERVATION_REQUIRED")
    timestamps = pd.to_datetime(bars["Datetime"], errors="raise")
    if timestamps.dt.tz is not None or not timestamps.is_monotonic_increasing or timestamps.duplicated().any():
        raise ValueError("M15_TIMESTAMP_ORDER_OR_TIMEZONE")
    if ((timestamps.dt.minute % 15).any() or timestamps.dt.second.any()
            or timestamps.dt.microsecond.any() or timestamps.dt.nanosecond.any()):
        raise ValueError("M15_GRID_INVALID")
    last_open = timestamps.iloc[-1].to_pydatetime()
    if observed_at < last_open + _STEP:
        raise ValueError("ONLY_COMPLETED_SIGNAL_AT_IMMEDIATE_NEXT_OPEN")
    frame = bars[list(_REQUIRED)].copy()
    frame["Datetime"] = timestamps
    values = frame[list(_REQUIRED[1:])].to_numpy(dtype=float)
    frame[list(_REQUIRED[1:])] = values
    if (not np.isfinite(values).all() or (values[:, :4] <= 0).any()
            or (values[:, 4] < 0).any()
            or not (frame.High >= frame[["Open", "Low", "Close"]].max(axis=1)).all()
            or not (frame.Low <= frame[["Open", "High", "Close"]].min(axis=1)).all()):
        raise ValueError("M15_OHLCV_INVALID")
    return frame


def completed_signal(symbol: str, strategy: str, bars: pd.DataFrame,
                     *, observed_at: datetime) -> FrozenSignal | None:
    """Exact frozen rule at immediate NEXT_OPEN, Moscow-naive Open labels."""
    if strategy not in STRATEGIES:
        raise ValueError("UNKNOWN_SYMBOL_OR_STRATEGY")
    frame = validate_completed_history(symbol, bars, observed_at=observed_at)
    last_open = frame.Datetime.iloc[-1].to_pydatetime()
    if observed_at != last_open + _STEP:
        raise ValueError("ONLY_COMPLETED_SIGNAL_AT_IMMEDIATE_NEXT_OPEN")
    features = _frozen_immutable_features(frame)
    side = int(features[strategy].iloc[-1])
    if side not in (-1, 0, 1):
        raise ValueError("FROZEN_SIGNAL_INVALID")
    if not side:
        return None
    atr = Decimal(str(features["atr"].iloc[-1]))
    if not atr.is_finite() or atr <= 0:
        raise ValueError("FROZEN_ATR_INVALID")
    return FrozenSignal(strategy, symbol, side, last_open, atr)
