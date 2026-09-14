"""Cross-cutting causal, execution-unit, parity, and reproducibility checks."""
from __future__ import annotations

import hashlib
from pathlib import Path
from typing import Any, Iterable, Mapping

import pandas as pd

TRUE_OOS_START = pd.Timestamp("2025-01-01", tz="UTC")
EXPECTED_TICKS = {"Si": 0.001, "CNY": 0.001}


def reject_true_oos(timestamps: Iterable[Any]) -> None:
    values = pd.to_datetime(list(timestamps), utc=True, format="mixed", errors="raise")
    if (values >= TRUE_OOS_START).any():
        raise ValueError("TRUE_OOS_BLOCKED: timestamp >= 2025-01-01")


def validate_data_period(period: Mapping[str, str]) -> None:
    if set(period) != {"start", "end"}:
        raise ValueError("data_period requires explicit start and end")
    start = pd.Timestamp(period["start"], tz="UTC")
    end = pd.Timestamp(period["end"], tz="UTC")
    if start > end or end >= TRUE_OOS_START:
        raise ValueError("TRUE_OOS_BLOCKED: development period must end before 2025")


def validate_tick_sizes(ticks: Mapping[str, float]) -> None:
    if dict(ticks) != EXPECTED_TICKS:
        raise ValueError(f"TICK_MODEL_MISMATCH: expected {EXPECTED_TICKS}")


def validate_trade_identity(rows: Iterable[Mapping[str, Any]]) -> None:
    failed = [row.get("strategy", "unknown") for row in rows
              if row.get("status") != "PASS" or not row.get("trade_identity_match")]
    if failed:
        raise ValueError("BASELINE_TRADE_IDENTITY_MISMATCH: " + ",".join(failed))


def artifact_hashes(directory: Path) -> dict[str, str]:
    allowed = {".json", ".csv", ".md"}
    return {path.relative_to(directory).as_posix(): hashlib.sha256(path.read_bytes()).hexdigest()
            for path in sorted(directory.rglob("*")) if path.is_file() and path.suffix in allowed}


def validate_determinism(first: Mapping[str, str], second: Mapping[str, str]) -> None:
    if dict(first) != dict(second):
        raise ValueError("NON_DETERMINISTIC_ARTIFACTS")
