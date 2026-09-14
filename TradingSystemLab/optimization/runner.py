"""Baseline-only experiment orchestration."""
from __future__ import annotations

from pathlib import Path
from typing import Any, Callable, Mapping

from .artifacts import write_artifacts
from .constraints import validate_configuration
from .experiment import Experiment
from .validation import validate_data_period

DEFAULT_SEARCH_SPACE_LIMIT = 5000


class SearchSpaceTooLarge(RuntimeError):
    pass


class ExperimentRunner:
    def __init__(self, search_space_limit: int = DEFAULT_SEARCH_SPACE_LIMIT):
        if search_space_limit < 1:
            raise ValueError("search_space_limit must be positive")
        self.search_space_limit = search_space_limit

    def run(self, experiment: Experiment,
            baseline_executor: Callable[[Experiment], Mapping[str, Any]],
            output: Path) -> dict[str, Any]:
        validate_data_period(experiment.data_period)
        size = experiment.parameter_space.size
        if size > self.search_space_limit:
            raise SearchSpaceTooLarge(f"SEARCH_SPACE_TOO_LARGE: {size} > {self.search_space_limit}")
        # Baselines may contain frozen values outside the candidate space; only
        # candidate parameters are checked, and never generated in Phase 3.1.
        bounded_baseline = {name: experiment.baseline_config[name]
                            for name in experiment.parameter_space.definition}
        validate_configuration(bounded_baseline, experiment.parameter_space, experiment.constraints)
        result = dict(baseline_executor(experiment))
        missing = set(experiment.metrics_required) - set(result.get("metrics", {}))
        if missing:
            raise ValueError("MISSING_UNIFIED_METRICS: " + ",".join(sorted(missing)))
        write_artifacts(Path(output), experiment.as_dict(), result, size)
        return result
