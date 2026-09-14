"""Safety-first foundation for bounded, reproducible experiments.

Phase 3.1 baseline reproduction and Phase 3.2 finite, plateau-oriented research
share these deterministic safety primitives.
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
