"""Phase 0: frozen T2/Si/M30 development-only pipeline smoke test."""
from __future__ import annotations

import hashlib
import json
from pathlib import Path
import shutil
from typing import Any

import pandas as pd

from .core.data_loader import DataLoader
from .core.instrument_specs import get_instrument_spec
from .core.unified_metrics import finite, stats
from .multitimeframe.phase71 import APPROVED_DATA_ROOT, STRATEGY_SHA256
from .strategies.trend.T2_Trend_Pullback import STRATEGY_ID, T2TrendPullback

SOURCE_RELATIVE = Path("futures_quarterly/Si/Si_M30.csv")
OUTPUT = Path("TradingSystemLab/results/phase0_smoke/T2_Si_M30")
START = pd.Timestamp("2020-01-01", tz="Europe/Moscow")
END_EXCLUSIVE = pd.Timestamp("2025-01-01", tz="Europe/Moscow")


def _sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _json(path: Path, value: Any) -> None:
    path.write_text(json.dumps(value, indent=2, sort_keys=True, allow_nan=False) + "\n", encoding="utf-8")


def load_development(data_root: Path) -> tuple[pd.DataFrame, Path, dict[str, Any]]:
    root = Path(data_root).resolve()
    if root != APPROVED_DATA_ROOT.resolve():
        raise ValueError("UNAPPROVED_MARKET_DATA_ROOT")
    source = root / SOURCE_RELATIVE
    opened = DataLoader(timezone="Europe/Moscow").load_csv_prefix(
        source, start=START, end_exclusive=END_EXCLUSIVE)
    closed = DataLoader.close_index(opened, "30min")
    if closed.empty or closed.index.min() < START or (closed.index >= END_EXCLUSIVE).any():
        raise ValueError("DEVELOPMENT_WINDOW_VIOLATION")
    if not ((closed.index.minute % 30 == 0) & (closed.index.second == 0)).all():
        raise ValueError("M30_TIMEFRAME_VIOLATION")
    quality = {
        "status": "PASS", "rows": len(closed), "timezone": str(closed.index.tz),
        "first_close": closed.index.min().isoformat(), "last_close": closed.index.max().isoformat(),
        "sorted": bool(closed.index.is_monotonic_increasing),
        "duplicate_timestamps": int(closed.index.duplicated().sum()),
        "ohlc_valid": True,
    }
    return closed, source, quality


def run(data_root: Path = APPROVED_DATA_ROOT, output: Path = OUTPUT) -> dict[str, Any]:
    strategy_file = Path("TradingSystemLab/strategies/trend/T2_Trend_Pullback.py")
    if _sha(strategy_file) != STRATEGY_SHA256["T2"]:
        raise RuntimeError("T2_FROZEN_STRATEGY_HASH_MISMATCH")
    bars, source, quality = load_development(data_root)
    spec = get_instrument_spec("Si")
    strategy = T2TrendPullback()
    trades = strategy.run(bars, "Si", tick_size=spec.price_step)
    trades = trades.sort_values(["exit_time", "trade_id"], kind="mergesort").reset_index(drop=True)
    if len(trades) and ((pd.to_datetime(trades.entry_time, utc=True) >= END_EXCLUSIVE.tz_convert("UTC")).any() or
                        (pd.to_datetime(trades.exit_time, utc=True) >= END_EXCLUSIVE.tz_convert("UTC")).any()):
        raise RuntimeError("TRUE_OOS_BARRIER_VIOLATION")
    metric = stats(trades.net_R_C1 if len(trades) else pd.Series(dtype=float))
    metrics = {"trades": metric["trades"], "PF_C1": metric["PF_R"],
               "expectancy_C1": metric["expectancy"], "net_R_C1": metric["net_R"],
               "max_DD_R_C1": metric["max_DD_R"], "win_rate_C1": metric["winrate"]}
    metrics = {key: finite(value) for key, value in metrics.items()}

    output = Path(output)
    if output.exists():
        shutil.rmtree(output)
    output.mkdir(parents=True)
    trades.to_csv(output / "trades.csv", index=False, date_format="%Y-%m-%dT%H:%M:%S%z",
                  lineterminator="\n", float_format="%.12g")
    _json(output / "data_quality.json", quality)
    _json(output / "metrics.json", metrics)
    manifest = {
        "phase": "PHASE_0_SMOKE_TEST", "status": "PASS", "strategy": "T2",
        "strategy_id": STRATEGY_ID, "frozen_parameters": strategy.frozen_parameters(),
        "instrument": "Si", "timeframe": "M30",
        "development_period": ["2020-01-01", "2024-12-31"],
        "source": str(SOURCE_RELATIVE), "source_sha256": _sha(source),
        "timezone": "Europe/Moscow",
        "instrument_spec": {"lot_size": spec.lot_size, "price_step": spec.price_step,
                            "tick_value_rub": spec.tick_value_rub, "currency": spec.currency},
        "cost_model": {"scenario": "C1", "ticks_per_side": 1.0,
                       "round_trip_ticks": 2.0, "additional_slippage_ticks": 0.0},
        "cost_scenarios_run": ["C1"], "true_oos_blocked": True,
        "optimization": False, "ranking": False, "walk_forward": False, "mtf": False,
    }
    _json(output / "manifest.json", manifest)
    (output / "report.md").write_text(
        "# TradingSystemLab v2 — Phase 0 Smoke Test\n\n"
        "**PASS** — Data → Loader → frozen T2 → Backtester → Metrics → Artifacts completed.\n\n"
        f"Si M30 development data: {quality['rows']} closed candles, {quality['first_close']} through "
        f"{quality['last_close']}. Timezone, ordering, duplicates, and OHLC checks passed.\n\n"
        f"C1 only: {metrics['trades']} trades; net R {metrics['net_R_C1']}. "
        "No optimization, ranking, walk-forward, MTF, or TRUE OOS access was performed.\n",
        encoding="utf-8")
    return {"status": "PASS", "bars": len(bars), "trades": len(trades), "output": str(output)}
