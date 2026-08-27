"""Reserved for future pattern discovery (not implemented)."""
"""Governed market-effect discovery (never strategy profitability)."""

from .protocol import (authorize_experiment, benjamini_hochberg, binary_effect,
    categorical_states, continuous_effect, day_block_bootstrap, load_discovery_protocol,
    quantile_states)
from .target_mapping import (hypothesis_units, load_discovery_target_mapping,
    mapped_targets, mapping_signature, primary_contrasts,
    validate_mapping_against_behavior_set, verify_phase5b_contracts)

__all__ = ["authorize_experiment", "benjamini_hochberg", "binary_effect", "categorical_states",
           "continuous_effect", "day_block_bootstrap", "load_discovery_protocol", "quantile_states"]
__all__ += ["hypothesis_units", "load_discovery_target_mapping", "mapped_targets",
            "mapping_signature", "primary_contrasts", "validate_mapping_against_behavior_set",
            "verify_phase5b_contracts"]
