"""Phase 4B neutral marginal summaries.

Feature and behavior matrices are deliberately summarized in separate calls.
There is no API accepting both matrices, preventing conditioned summaries.
"""
from __future__ import annotations

import json
import math
import time
from pathlib import Path
from typing import Any

try:
    import resource as _resource
except ImportError:  # pragma: no cover - exercised by the Windows compatibility test
    _resource = None

import numpy as np
import pandas as pd

QUANTILES = (.01, .05, .25, .5, .75, .95, .99)
REPORT_NAMES = ("coverage", "feature_inventory", "feature_temporal_stability",
                "target_inventory", "target_temporal_stability", "intraday_descriptives")


def finite_summary(series: pd.Series) -> dict[str, Any]:
    """Deterministic robust numeric inventory; infinities are excluded and counted."""
    values = pd.to_numeric(series, errors="coerce").to_numpy(float)
    finite = values[np.isfinite(values)]
    q = np.quantile(finite, QUANTILES) if len(finite) else [None] * len(QUANTILES)
    result: dict[str, Any] = {"count": int(len(values)), "finite_count": int(len(finite)),
        "nan_count": int(np.isnan(values).sum()), "infinite_count": int(np.isinf(values).sum()),
        "mean": float(np.mean(finite)) if len(finite) else None,
        "std": float(np.std(finite, ddof=1)) if len(finite) > 1 else None,
        "min": float(np.min(finite)) if len(finite) else None,
        "max": float(np.max(finite)) if len(finite) else None}
    result.update({name: (float(value) if value is not None else None) for name, value in
                   zip(("p01", "p05", "p25", "median", "p75", "p95", "p99"), q)})
    return result


def quality_summary(series: pd.Series) -> dict[str, Any]:
    result = finite_summary(series)
    numeric = pd.to_numeric(series, errors="coerce").to_numpy(float)
    finite = numeric[np.isfinite(numeric)]
    _, counts = np.unique(finite, return_counts=True)
    unique = int(len(counts)); dominant = float(counts.max() / len(finite)) if len(finite) else None
    result.update({"nan_fraction": float(np.isnan(numeric).mean()) if len(numeric) else 0.0,
        "unique_finite_count": unique, "dominant_finite_value_fraction": dominant,
        "flags": {"very_sparse": bool(result["finite_count"] < .1 * len(numeric)),
                  "near_constant": bool(dominant is not None and dominant >= .999),
                  "binary_or_categorical_like": bool(0 < unique <= 10),
                  "bounded": bool(len(finite) and np.min(finite) >= 0 and np.max(finite) <= 1),
                  "heavy_tailed": bool(len(finite) > 3 and result["p99"] is not None and
                                       result["p75"] is not None and result["median"] is not None and
                                       abs(result["p99"] - result["median"]) >
                                       10 * max(abs(result["p75"] - result["median"]), 1e-15))}})
    return result


def coverage_summary(frame: pd.DataFrame) -> dict[str, Any]:
    trading_dates = frame["trading_date"] if "trading_date" in frame else frame.open_time.dt.date
    dates = trading_dates.astype(str)
    per_day = dates.value_counts()
    month = frame["open_time"].dt.strftime("%Y-%m")
    monthly = {}
    for key, part in frame.groupby(month, sort=True):
        part_dates = part["trading_date"] if "trading_date" in part else part.open_time.dt.date
        monthly[key] = {"rows": int(len(part)), "trading_dates": int(part_dates.nunique()),
            "first_timestamp": part.open_time.min().isoformat(), "last_timestamp": part.close_time.max().isoformat()}
    return {"rows": int(len(frame)), "first_open_time": frame.open_time.min().isoformat(),
        "last_close_time": frame.close_time.max().isoformat(), "trading_dates": int(dates.nunique()),
        "median_rows_per_day": float(per_day.median()), "min_rows_per_day": int(per_day.min()),
        "max_rows_per_day": int(per_day.max()), "rows_per_trading_date": {str(k): int(v) for k, v in per_day.sort_index().items()},
        "months": monthly}


def activity_summary(frame: pd.DataFrame) -> dict[str, Any]:
    trading_dates = frame["trading_date"] if "trading_date" in frame else frame.open_time.dt.date
    def grouped(keys: pd.Series) -> dict[str, Any]:
        answer = {}
        for key, part in frame.groupby(keys, sort=True):
            counts = part.groupby(trading_dates.loc[part.index], sort=False).size()
            answer[str(key)] = {"rows": int(len(part)), "contributing_dates": int(len(counts)),
                                "median_rows_per_contributing_date": float(counts.median())}
        return answer
    return {"hour": grouped(frame.open_time.dt.hour), "weekday": grouped(frame.open_time.dt.weekday),
            "month": grouped(frame.open_time.dt.strftime("%Y-%m"))}


def marginal_drift(frame: pd.DataFrame, columns: list[str]) -> dict[str, Any]:
    """Compare each column's own monthly marginals; no other matrix is accepted."""
    months = frame.open_time.dt.strftime("%Y-%m")
    output = {}
    for column in columns:
        entries = []
        for month, series in frame[column].groupby(months, sort=True):
            summary = quality_summary(series)
            entries.append({"month": month, "median": summary["median"],
                "iqr": None if summary["p25"] is None else summary["p75"] - summary["p25"],
                "nan_fraction": summary["nan_fraction"]})
        medians = [x["median"] for x in entries if x["median"] is not None]
        iqrs = [x["iqr"] for x in entries if x["iqr"] is not None]
        output[column] = {"months": entries, "median_shift": max(medians)-min(medians) if medians else None,
            "iqr_shift": max(iqrs)-min(iqrs) if iqrs else None,
            "missingness_shift": max(x["nan_fraction"] for x in entries)-min(x["nan_fraction"] for x in entries)}
    return output


def target_validity(frame: pd.DataFrame, columns: list[str]) -> dict[str, Any]:
    output = {}
    for name in [c for c in columns if c.startswith("target_future_valid_")]:
        horizon = name.rsplit("_", 1)[-1]; values = frame[name].fillna(False).astype(bool)
        reason = f"target_future_invalid_reason_{horizon}"
        output[horizon] = {"rows": int(len(frame)), "valid_count": int(values.sum()),
            "invalid_count": int((~values).sum()), "valid_fraction": float(values.mean()),
            "invalid_reasons": ({str(k): int(v) for k, v in frame.loc[~values, reason].value_counts(dropna=False).items()}
                                if reason in frame else {})}
    return output


def categorical_summary(series: pd.Series) -> dict[str, Any]:
    counts = series.value_counts(dropna=False)
    return {"count": int(len(series)), "undefined_count": int(series.isna().sum()),
            "class_counts": {str(k): int(v) for k, v in counts.items()},
            "class_fractions": {str(k): float(v / len(series)) for k, v in counts.items()}}


def write_reports(reports: dict[str, Any], output: Path) -> dict[str, int]:
    output.mkdir(parents=True, exist_ok=True)
    sizes = {}
    for name in REPORT_NAMES:
        path = output / f"{name}.json"; path.write_text(json.dumps(reports[name], indent=2, sort_keys=True)+"\n")
        sizes[path.name] = path.stat().st_size
    summary = output / "summary.json"; summary.write_text(json.dumps(reports["summary"], indent=2, sort_keys=True)+"\n")
    sizes[summary.name] = summary.stat().st_size
    return sizes


def memory_mb() -> float:
    if _resource is None:
        return 0.0
    return _resource.getrusage(_resource.RUSAGE_SELF).ru_maxrss / 1024
