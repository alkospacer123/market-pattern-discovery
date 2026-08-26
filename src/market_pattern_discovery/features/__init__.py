"""Reserved for a future causality-safe feature builder (not implemented)."""
"""Causal, day-reset market-state features."""

from .core import FeatureBuildResult, FeatureInputError, build_core_features
from .schema import CoreFeatureConfig

__all__ = ["CoreFeatureConfig", "FeatureBuildResult", "FeatureInputError", "build_core_features"]
