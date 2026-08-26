"""Feature Builder v1.1 public orchestration API."""
from __future__ import annotations

import numpy as np
import pandas as pd

from .core import FeatureBuildResult, build_core_features
from .levels import add_round_level_features
from .multitimeframe import attach_m5_context
from .schema import FEATURE_BUILDER_VERSION, RoundLevelConfig
from .structure import add_structure_features


def build_features(frame: pd.DataFrame, *, timeframe: str, round_levels: RoundLevelConfig,
                   native_m5: pd.DataFrame | None = None) -> FeatureBuildResult:
    """Build Phase 2A+2B, optionally attaching fully closed native M5 to M1."""
    core = build_core_features(frame, timeframe=timeframe)
    out, structure = add_structure_features(core.frame)
    out, levels = add_round_level_features(out, round_levels)
    context: list[str] = []; cross: list[str] = []
    if native_m5 is not None:
        if timeframe != "M1":
            raise ValueError("native_m5 context is valid only for M1")
        if "instrument" not in native_m5 or native_m5.instrument.nunique(dropna=False) != 1:
            raise ValueError("native M5 input must contain exactly one instrument")
        if str(frame.instrument.iloc[0]) != str(native_m5.instrument.iloc[0]):
            raise ValueError("M1 and native M5 instruments must match")
        m5_built = build_features(native_m5, timeframe="M5", round_levels=round_levels).frame
        out, attached = attach_m5_context(out, m5_built)
        context, cross = attached[:-6], attached[-6:]
    numeric = out.select_dtypes(include=[np.number]).to_numpy(dtype=float)
    if np.isinf(numeric).any() or len(out) != len(frame):
        raise ArithmeticError("Phase 2B output must preserve rows and contain no infinity")
    metadata = dict(core.metadata)
    metadata.update({"feature_builder_version": FEATURE_BUILDER_VERSION,
                     "phase2a_feature_names": core.metadata["feature_names"],
                     "structure_feature_names": structure, "round_level_feature_names": levels,
                     "m5_context_feature_names": context, "cross_timeframe_feature_names": cross,
                     "feature_names": core.metadata["feature_names"] + structure + levels + context + cross})
    return FeatureBuildResult(out, metadata)
