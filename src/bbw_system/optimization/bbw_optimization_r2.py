"""Second, bounded BBW sensitivity experiment around the R1 region.

R2 deliberately reuses the R1 evaluator and frozen Baseline.  Only its
deterministic candidate grid and research report are experiment-specific.
"""
from __future__ import annotations

import itertools
from pathlib import Path
from typing import Any

import numpy as np

from .bbw_parameter_search import (
    OptimizationError, OptimizationParameters, run_optimization,
)
from .optimization_report_r2 import build_r2_report

R2_GRID_LIMIT = 1024
R2_SPACE = {
    "bbw_period": (10, 15, 20),
    "bbw_std": (1.5, 2.0),
    "squeeze_window": (5, 10),
    "range_min_bars": (3, 4, 5, 6),
    "range_max_bars": (20, 30, 40),
    "atr_min": (0.5, 0.75, 1.0),
    "atr_max": (2.0, 3.0),
    "ema_period": (20, 30, 50),
    "ema_slope_threshold": (0.0, 0.0005, 0.001),
    "retest_min_bars": (3, 5),
    "retest_max_bars": (30, 40, 50),
    "penetration": (0.1, 0.2),
}
R2_BASELINE = OptimizationParameters(10, 2.0, 10, 6, 30, 1.0, 2.0, 50, 0.001, 5, 30, 0.2)


def generate_r2_parameter_grid(limit: int = R2_GRID_LIMIT) -> list[OptimizationParameters]:
    """Return a reproducible R2 grid with intact local-neighbour blocks."""
    if not 500 <= limit <= 2000:
        raise OptimizationError("R2 grid limit must be between 500 and 2000")
    names = tuple(R2_SPACE)
    full = sorted(OptimizationParameters(**dict(zip(names, values, strict=True)))
                  for values in itertools.product(*(R2_SPACE[name] for name in names)))
    # Preserve complete local blocks for the five coordinates highlighted by
    # R1.  This makes neighbour-based stability observable rather than relying
    # on isolated points from a flat Cartesian sample.  Contexts broaden the
    # other coordinates while remaining within the approved space.
    contexts = (
        (10, 2.0, 10, 1.0, 30, 5, 0.2),
        (15, 1.5, 5, 0.75, 20, 3, 0.1),
        (20, 2.0, 10, 0.5, 40, 5, 0.1),
        (10, 1.5, 5, 1.0, 40, 3, 0.2),
    )
    selected: set[OptimizationParameters] = set()
    context_count = min(len(contexts), limit // 216)
    for bbw_period, bbw_std, squeeze_window, atr_min, range_max, retest_min, penetration in contexts[:context_count]:
        for ema_period, slope, range_min, atr_max, retest_max in itertools.product(
                R2_SPACE["ema_period"], R2_SPACE["ema_slope_threshold"],
                R2_SPACE["range_min_bars"], R2_SPACE["atr_max"],
                R2_SPACE["retest_max_bars"]):
            selected.add(OptimizationParameters(
                bbw_period, bbw_std, squeeze_window, range_min, range_max,
                atr_min, atr_max, ema_period, slope, retest_min, retest_max,
                penetration,
            ))
    remaining = [item for item in full if item not in selected]
    slots = limit - len(selected)
    indices = np.linspace(0, len(remaining) - 1, slots, dtype=int)
    selected.update(remaining[int(index)] for index in indices)
    selected.add(R2_BASELINE)
    ordered = sorted(selected)
    if len(ordered) > limit:
        ordered.remove(next(item for item in reversed(ordered) if item != R2_BASELINE))
    return ordered


def run_r2_optimization(feature_root: Path, normalized_root: Path, baseline_root: Path,
                        output_root: Path, symbol: str, *, grid_limit: int = R2_GRID_LIMIT,
                        transaction_cost_r: float = 0.0,
                        slippage_r: float = 0.0) -> dict[str, Any]:
    """Run research-only R2 without promoting any candidate configuration."""
    return run_optimization(
        feature_root, normalized_root, baseline_root, output_root, symbol,
        transaction_cost_r=transaction_cost_r, slippage_r=slippage_r,
        grid=generate_r2_parameter_grid(grid_limit), report_builder=build_r2_report,
    )
