"""Shared deterministic primitives for the Top-5 V4 research engine.

The machine contract in ``config/top5_v4/strategy_contract.json`` is the sole
source of frozen periods, ticks, round grids, and friction scenarios.  Python
code consumes those values; it does not maintain an independent copy.
"""
from __future__ import annotations
from decimal import Decimal, ROUND_HALF_UP
from hashlib import sha256
from pathlib import Path
from typing import Any
import json
import numpy as np
import pandas as pd

TZ = "Europe/Moscow"
REPO_ROOT = Path(__file__).resolve().parents[4]
CONTRACT_PATH = REPO_ROOT / "config/top5_v4/strategy_contract.json"
REGISTRY_PATH = REPO_ROOT / "config/top5_v4/candidate_registry.json"

def canonical_json(value: Any) -> str:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False, allow_nan=False)

def _load_machine_contract() -> dict:
    try:
        return json.loads(CONTRACT_PATH.read_text(encoding="utf-8"))
    except FileNotFoundError as exc:
        raise RuntimeError(f"Top-5 V4 machine contract missing: {CONTRACT_PATH}") from exc

_MACHINE_CONTRACT = _load_machine_contract()
_p = _MACHINE_CONTRACT["periods"]
DEV_START = pd.Timestamp(_p["DEV"][0])
DEV_END = pd.Timestamp(_p["DEV"][1])
VAL_A_END = pd.Timestamp(_p["VALIDATION_A"][1])
VALIDATION_END = pd.Timestamp(_p["VALIDATION_B"][1])
TICKS = {k: float(v) for k, v in _MACHINE_CONTRACT["ticks"].items()}
ROUND_STEPS = {k: float(v) for k, v in _MACHINE_CONTRACT["round_steps"].items()}
FRICTION_TICKS = {k: int(_MACHINE_CONTRACT["friction"][k]) for k in ("GROSS", "BASE", "STRESS")}
SCENARIOS = tuple(FRICTION_TICKS)

def stable_id(prefix: str, value: Any, n: int = 20) -> str:
    return f"{prefix}-{sha256(canonical_json(value).encode('utf-8')).hexdigest()[:n]}"

def _decimal(value: Any) -> Decimal:
    d = Decimal(str(value))
    if not d.is_finite():
        raise ValueError("finite numeric value required")
    return d

def price_to_ticks(price: Any, tick: Any) -> int:
    p, t = _decimal(price), _decimal(tick)
    if t <= 0:
        raise ValueError("positive finite tick required")
    return int((p / t).quantize(Decimal("1"), rounding=ROUND_HALF_UP))

def ticks_to_price(ticks: int, tick: Any) -> float:
    return float(Decimal(int(ticks)) * _decimal(tick))

def round_to_tick(price: Any, tick: Any) -> float:
    return ticks_to_price(price_to_ticks(price, tick), tick)

def _half_up_int(value: Any) -> int:
    return int(_decimal(value).quantize(Decimal("1"), rounding=ROUND_HALF_UP))

def validate_tick_grid(frame: pd.DataFrame, instrument: str) -> None:
    tick = TICKS[instrument]
    for col in ("open", "high", "low", "close"):
        vals = frame[col].to_numpy(float)
        if not np.isfinite(vals).all():
            raise ValueError(f"non-finite {col}")
        back = np.array([ticks_to_price(price_to_ticks(v, tick), tick) for v in vals])
        if not np.array_equal(vals, back):
            bad = int(np.flatnonzero(vals != back)[0])
            raise ValueError(f"raw OHLC is off instrument tick grid: {col} row={bad}")
