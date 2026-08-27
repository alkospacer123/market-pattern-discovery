"""Phase 3B neutral future-path representation.

All calculations in this module are target-side and forward looking.  They
must never be imported by the feature package or presented as observations at
decision time.  Offset one is the first candle after the decision candle.
"""
from __future__ import annotations

import hashlib
import json
from pathlib import Path

import numpy as np
import pandas as pd

from .outcomes import HORIZONS, build_outcomes

TARGET_DEFINITION_VERSION = "1.0"
ATR_REFERENCE = "atr_20"
FIRST_PASSAGE_BARRIERS = (0.5, 1.0)
MANIFEST_PATH = Path(__file__).resolve().parents[3] / "config" / "target_definitions_v1.json"
_IDENTITY = ("instrument", "timeframe", "open_time", "close_time", "decision_time")
_PER_HORIZON = (
    "behavior_signed_displacement_atr", "behavior_abs_displacement_atr",
    "behavior_up_excursion_atr", "behavior_down_excursion_atr",
    "behavior_excursion_balance_atr", "behavior_path_length_atr",
    "behavior_path_efficiency", "behavior_direction_changes",
    "behavior_direction_persistence", "behavior_future_range_atr",
    "behavior_high_time_fraction", "behavior_low_time_fraction",
    "label_direction", "label_dominant_side", "label_extreme_order",
    "label_first_passage_0p5", "label_first_passage_1p0",
    "label_large_future_movement", "label_future_efficient_direction",
    "label_future_active_nondirectional", "label_future_quiet",
    "label_future_trend_like", "label_future_range_like",
    "label_continuation_close_delta_1",
)
_SHAPE = (
    "behavior_early_displacement_atr", "behavior_mid_displacement_atr",
    "behavior_late_displacement_atr", "behavior_early_to_mid_increment_atr",
    "behavior_mid_to_late_increment_atr", "behavior_peak_abs_displacement_hindex",
    "behavior_final_vs_peak_abs_ratio", "behavior_sign_persistence_across_horizons",
    "behavior_horizon_sign_changes", "behavior_early_speed_atr_per_min",
    "behavior_mid_increment_speed_atr_per_min", "behavior_late_increment_speed_atr_per_min",
)


def load_target_manifest(path: Path = MANIFEST_PATH) -> dict:
    return json.loads(path.read_text())


def signature_payload(manifest: dict) -> bytes:
    payload = {k: v for k, v in manifest.items() if k != "signature_sha256"}
    return json.dumps(payload, sort_keys=True, separators=(",", ":"), ensure_ascii=True).encode()


def target_definition_signature(manifest: dict) -> str:
    return hashlib.sha256(signature_payload(manifest)).hexdigest()


def behavior_columns(timeframe: str) -> list[str]:
    if timeframe not in HORIZONS:
        raise ValueError(f"unsupported timeframe {timeframe!r}")
    return [*(f"{stem}_{h}" for h in HORIZONS[timeframe] for stem in _PER_HORIZON), *_SHAPE]


def generic_columns(timeframe: str) -> list[str]:
    return [c for c in behavior_columns(timeframe) if not c.startswith("label_future_trend_like")
            and not c.startswith("label_future_range_like")
            and not c.startswith("label_continuation_")]


def known_hypothesis_columns(timeframe: str) -> list[str]:
    generic = set(generic_columns(timeframe))
    return [c for c in behavior_columns(timeframe) if c not in generic]


def _first_passage(high: np.ndarray, low: np.ndarray, reference: np.ndarray,
                   atr: np.ndarray, horizon: int, barrier: float) -> np.ndarray:
    n = len(reference)
    result = np.full(n, np.nan)
    for i in range(n - horizon):
        if not np.isfinite(atr[i]) or atr[i] <= 0:
            continue
        upper, lower = reference[i] + barrier * atr[i], reference[i] - barrier * atr[i]
        up = np.flatnonzero(high[i + 1:i + horizon + 1] >= upper)
        down = np.flatnonzero(low[i + 1:i + horizon + 1] <= lower)
        if not len(up) and not len(down): result[i] = 0
        elif not len(down): result[i] = 1
        elif not len(up): result[i] = -1
        elif up[0] < down[0]: result[i] = 1
        elif down[0] < up[0]: result[i] = -1
        # same first candle deliberately remains NaN: OHLC has no sequence.
    return result


def build_behaviors(frame: pd.DataFrame, features: pd.DataFrame,
                    outcomes: pd.DataFrame | None = None) -> pd.DataFrame:
    """Return one deterministic Phase 3B row for each decision row."""
    if len(frame) != len(features):
        raise ValueError("raw and frozen-feature row counts differ")
    if ATR_REFERENCE not in features or "close_delta_1" not in features:
        raise ValueError("frozen features must contain atr_20 and close_delta_1")
    out = build_outcomes(frame) if outcomes is None else outcomes
    if len(out) != len(frame):
        raise ValueError("Phase 3A row count differs")
    timeframe = str(frame["timeframe"].iloc[0])
    if timeframe not in HORIZONS:
        raise ValueError("unsupported timeframe")
    source = frame.reset_index(drop=True)
    feat = features.reset_index(drop=True)
    identity = out[list(_IDENTITY)].copy()
    result_data: dict[str, np.ndarray | pd.Series] = {}
    reference = out["target_reference_close"].to_numpy(float)
    atr = pd.to_numeric(feat[ATR_REFERENCE], errors="coerce").to_numpy(float)
    highs, lows, closes = (source[x].to_numpy(float) for x in ("high", "low", "close"))
    signed_by_h: dict[int, np.ndarray] = {}
    minute = 1 if timeframe == "M1" else 5
    for h in HORIZONS[timeframe]:
        valid = out[f"target_future_valid_{h}"].to_numpy(bool)
        norm_valid = valid & np.isfinite(atr) & (atr > 0)
        delta = out[f"target_future_delta_{h}"].to_numpy(float)
        up = out[f"target_future_max_high_{h}"].to_numpy(float) - reference
        down = reference - out[f"target_future_min_low_{h}"].to_numpy(float)
        steps = np.full((len(source), h), np.nan)
        for offset in range(1, h + 1):
            if offset < len(source):
                if offset == 1: steps[:len(source)-1, 0] = closes[1:] - reference[:-1]
                else: steps[:len(source)-offset, offset-1] = closes[offset:len(source)] - closes[offset-1:len(source)-1]
        path = np.nansum(np.abs(steps), axis=1)
        efficiency = np.divide(np.abs(delta), path, out=np.full(len(source), np.nan), where=path != 0)
        changes = np.full(len(source), np.nan); persistence = np.full(len(source), np.nan)
        for i in np.flatnonzero(valid):
            signs = np.sign(steps[i]); signs = signs[signs != 0]
            if len(signs):
                changes[i] = np.count_nonzero(signs[1:] != signs[:-1])
                persistence[i] = max(np.count_nonzero(signs > 0), np.count_nonzero(signs < 0)) / len(signs)
        def normalized(value: np.ndarray) -> np.ndarray:
            return np.divide(value, atr, out=np.full(len(source), np.nan), where=norm_valid)
        signed = normalized(delta); signed_by_h[h] = signed
        values = {
            "behavior_signed_displacement_atr": signed,
            "behavior_abs_displacement_atr": normalized(np.abs(delta)),
            "behavior_up_excursion_atr": normalized(up),
            "behavior_down_excursion_atr": normalized(down),
            "behavior_excursion_balance_atr": normalized(up - down),
            "behavior_path_length_atr": normalized(path),
            "behavior_path_efficiency": np.where(norm_valid, efficiency, np.nan),
            "behavior_direction_changes": np.where(valid, changes, np.nan),
            "behavior_direction_persistence": np.where(valid, persistence, np.nan),
            "behavior_future_range_atr": normalized(out[f"target_future_range_{h}"].to_numpy(float)),
            "behavior_high_time_fraction": np.where(valid, out[f"target_bars_to_future_high_{h}"] / h, np.nan),
            "behavior_low_time_fraction": np.where(valid, out[f"target_bars_to_future_low_{h}"] / h, np.nan),
            "label_direction": np.where(valid, np.sign(delta), np.nan),
            "label_dominant_side": np.where(valid, np.sign(up - down), np.nan),
            "label_extreme_order": np.where(valid, np.where(out[f"target_bars_to_future_high_{h}"] < out[f"target_bars_to_future_low_{h}"], 1, np.where(out[f"target_bars_to_future_low_{h}"] < out[f"target_bars_to_future_high_{h}"], -1, np.nan)), np.nan),
        }
        for b, token in ((0.5, "0p5"), (1.0, "1p0")):
            fp = _first_passage(highs, lows, reference, atr, h, b)
            values[f"label_first_passage_{token}"] = np.where(norm_valid, fp, np.nan)
        absd, range_atr, path_atr = np.abs(signed), normalized(out[f"target_future_range_{h}"].to_numpy(float)), normalized(path)
        values.update({
            "label_large_future_movement": np.where(norm_valid, (range_atr >= 1.5).astype(float), np.nan),
            "label_future_efficient_direction": np.where(norm_valid, np.where((absd >= 1) & (efficiency >= .6), np.sign(delta), 0), np.nan),
            "label_future_active_nondirectional": np.where(norm_valid, ((range_atr >= 1.5) & (absd <= .5)).astype(float), np.nan),
            "label_future_quiet": np.where(norm_valid, ((range_atr <= .5) & (path_atr <= 1)).astype(float), np.nan),
            "label_future_trend_like": np.where(norm_valid, np.where((absd >= 1) & (efficiency >= .6), np.sign(delta), 0), np.nan),
            "label_future_range_like": np.where(norm_valid, ((absd <= .5) & (efficiency <= .35)).astype(float), np.nan),
        })
        causal = np.sign(pd.to_numeric(feat["close_delta_1"], errors="coerce").to_numpy(float))
        dominant = np.sign(up - down)
        values["label_continuation_close_delta_1"] = np.where(valid & np.isfinite(causal), np.where((causal == 0) | (dominant == 0), 0, np.where(causal == dominant, 1, -1)), np.nan)
        for stem in _PER_HORIZON: result_data[f"{stem}_{h}"] = values[stem]
    early, mid, late = ((5, 15, 60) if timeframe == "M1" else (1, 3, 12))
    e, m, l = signed_by_h[early], signed_by_h[mid], signed_by_h[late]
    curve = np.column_stack([signed_by_h[h] for h in HORIZONS[timeframe]])
    peak_idx = np.full(len(source), np.nan); ratio = np.full(len(source), np.nan)
    sign_persist = np.full(len(source), np.nan); horizon_changes = np.full(len(source), np.nan)
    for i in range(len(source)):
        values = curve[i]
        if not np.isfinite(values).all(): continue
        peak = np.max(np.abs(values)); peak_idx[i] = int(np.argmax(np.abs(values))) + 1
        if peak != 0: ratio[i] = abs(values[-1]) / peak
        signs = np.sign(values); nz = signs[signs != 0]
        if len(nz):
            sign_persist[i] = max(np.count_nonzero(nz > 0), np.count_nonzero(nz < 0)) / len(nz)
            horizon_changes[i] = np.count_nonzero(nz[1:] != nz[:-1])
    shape = (e, m, l, m-e, l-m, peak_idx, ratio, sign_persist, horizon_changes,
             e/(early*minute), (m-e)/((mid-early)*minute), (l-m)/((late-mid)*minute))
    for name, value in zip(_SHAPE, shape): result_data[name] = value
    result = pd.concat([identity, pd.DataFrame(result_data)], axis=1)
    numeric = result.select_dtypes(include=[np.number]).to_numpy(float)
    if np.isinf(numeric).any() or len(result) != len(frame):
        raise RuntimeError("Phase 3B produced infinity or row loss")
    return result[[*_IDENTITY, *behavior_columns(timeframe)]]
