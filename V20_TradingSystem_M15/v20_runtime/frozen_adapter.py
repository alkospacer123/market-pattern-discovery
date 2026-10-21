"""Offline invocation of the exact frozen V20/V4 signal functions.

No duplicated strategy conditions, no broker, no external source modification.
This reuses the already-verified V20-03 frozen AST adapter as-is. V20-04/05
must replace its temporary CSV transport with a non-mutating in-memory
production adapter only after signal-by-signal parity is demonstrated.
"""
from __future__ import annotations

import importlib.util
from datetime import datetime, timedelta
from decimal import Decimal
from pathlib import Path
import pandas as pd

from .offline_planner import FrozenSignal, N4, STRATEGIES

_ROOT = Path(__file__).resolve().parents[1]
_FROZEN_REPLAY_ADAPTER = _ROOT / "V20-03" / "offline" / "stress_v20_03.py"
_REQUIRED = ("Datetime", "Open", "High", "Low", "Close", "Volume")
_STEP = timedelta(minutes=15)


def _frozen_immutable_features(source: pd.DataFrame) -> pd.DataFrame:
    spec = importlib.util.spec_from_file_location("v20_03_readonly_frozen_adapter", _FROZEN_REPLAY_ADAPTER)
    if spec is None or spec.loader is None:
        raise RuntimeError("PINNED_FROZEN_ADAPTER_UNAVAILABLE")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module.frozen_signals(source)


def completed_signal(symbol: str, strategy: str, bars: pd.DataFrame,
                     *, observed_at: datetime) -> FrozenSignal | None:
    """Evaluate only the most recently completed M15 bar at its NEXT_OPEN.

    The input is an isolated OHLCV snapshot for one N4 symbol, with Moscow-naive
    Open-labelled times. No interaction with FINAM or a running robot occurs.
    """
    if symbol not in N4 or strategy not in STRATEGIES:
        raise ValueError("UNKNOWN_SYMBOL_OR_STRATEGY")
    if not isinstance(bars, pd.DataFrame) or bars.empty:
        raise ValueError("EMPTY_M15_INPUT")
    if any(c not in bars.columns for c in _REQUIRED):
        raise ValueError("M15_FIELDS_INCOMPLETE")
    if not isinstance(observed_at, datetime) or observed_at.tzinfo is not None:
        raise ValueError("MOSCOW_NAIVE_OBSERVATION_REQUIRED")
    timestamps = pd.to_datetime(bars["Datetime"], errors="raise")
    if timestamps.dt.tz is not None or not timestamps.is_monotonic_increasing or timestamps.duplicated().any():
        raise ValueError("M15_TIMESTAMP_ORDER_OR_TIMEZONE")
    if (timestamps.dt.minute % 15).any() or timestamps.dt.second.any():
        raise ValueError("M15_GRID_INVALID")
    last_open = timestamps.iloc[-1].to_pydatetime()
    if observed_at != last_open + _STEP:
        raise ValueError("ONLY_COMPLETED_SIGNAL_AT_IMMEDIATE_NEXT_OPEN")
    frame = bars[list(_REQUIRED)].copy()
    frame["Datetime"] = timestamps
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
