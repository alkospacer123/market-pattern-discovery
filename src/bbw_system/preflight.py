"""Fail-closed baseline readiness validation."""
from __future__ import annotations
import json
from pathlib import Path
from typing import Any

CRITICAL_METADATA = ("source_timezone", "exchange_timezone", "session", "tick_size", "tick_value_per_contract", "go_per_contract", "commission_value", "rollover_policy")
REQUIRED_STRATEGY = ("bbw_period", "bbw_std", "threshold_trading_days", "threshold_minima", "ema", "ema_slope", "atr", "range_bars", "atr_range_bounds", "max_width_pct", "retest_min_bars", "retest_max_bars", "penetration", "stop_offset", "stop_min_max", "entry_extension", "confirmation_candle_limit", "risk_pct", "margin_limit", "commissions", "slippage", "tp_allocations")


def load_document(path: str | Path) -> dict[str, Any]:
    """Passports use the JSON subset of YAML, avoiding an optional dependency."""
    return json.loads(Path(path).read_text(encoding="utf-8"))


def _verified(value: Any) -> bool:
    return isinstance(value, dict) and value.get("value") is not None and value.get("verified") is True


def baseline_preflight(passport: dict[str, Any], strategy: dict[str, Any]) -> list[str]:
    errors = []
    for key in CRITICAL_METADATA:
        if not _verified(passport.get(key)):
            errors.append(f"metadata.{key}: missing or unverified")
    for key in REQUIRED_STRATEGY:
        entry = strategy.get(key)
        if not isinstance(entry, dict) or entry.get("status") != "FIXED" or entry.get("value") is None:
            errors.append(f"strategy.{key}: not FIXED")
    return errors


def assert_baseline_ready(passport: dict[str, Any], strategy: dict[str, Any]) -> None:
    errors = baseline_preflight(passport, strategy)
    if errors:
        raise ValueError("Baseline blocked:\n" + "\n".join(errors))
