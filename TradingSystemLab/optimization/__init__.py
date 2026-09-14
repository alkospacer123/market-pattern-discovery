"""Safety-first foundation for bounded, reproducible experiments.

This package deliberately provides no objective, ranking, or parameter-selection
facility.  Phase 3.1 can execute frozen baselines only.
"""

from .experiment import Experiment, deterministic_experiment_id, stable_hash
from .parameter_space import ParameterSpace, SearchSpaceError
from .runner import ExperimentRunner, SearchSpaceTooLarge

__all__ = [
    "Experiment",
    "ExperimentRunner",
    "ParameterSpace",
    "SearchSpaceError",
    "SearchSpaceTooLarge",
    "deterministic_experiment_id",
    "stable_hash",
]
