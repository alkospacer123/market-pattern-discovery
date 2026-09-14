from __future__ import annotations

import hashlib
from pathlib import Path

import pytest

from TradingSystemLab.optimization.constraints import ConstraintViolation, validate_configuration
from TradingSystemLab.optimization.experiment import Experiment, REQUIRED_METRICS, stable_hash
from TradingSystemLab.optimization.parameter_space import ParameterSpace, SearchSpaceError
from TradingSystemLab.optimization.runner import ExperimentRunner, SearchSpaceTooLarge
from TradingSystemLab.optimization.validation import (artifact_hashes, reject_true_oos,
    validate_determinism, validate_tick_sizes)
from TradingSystemLab.run_optimization_baseline_test import baseline_executor, build_experiment


def test_parameter_space_generation_and_types():
    space = ParameterSpace({"ema": {"type": "integer", "values": [50, 100]},
                            "threshold": {"type": "float", "values": [1, 1.5]},
                            "mode": {"type": "categorical", "values": ["a", "b"]}})
    assert space.size == 8
    assert list(space.generate())[0] == {"ema": 50, "mode": "a", "threshold": 1.0}
    with pytest.raises(SearchSpaceError):
        ParameterSpace({"x": {"type": "int", "min": 1}})


def test_explicit_constraints_and_forbidden_combinations():
    space = ParameterSpace({"fast": {"type": "int", "values": [10, 20]},
                            "slow": {"type": "int", "values": [20, 30]}})
    validate_configuration({"fast": 10, "slow": 20}, space,
                           ({"left": "fast", "operator": "<", "right": "slow"},))
    with pytest.raises(ConstraintViolation):
        validate_configuration({"fast": 20, "slow": 20}, space,
                               ({"left": "fast", "operator": "<", "right": "slow"},))
    with pytest.raises(ConstraintViolation, match="forbidden"):
        validate_configuration({"fast": 10, "slow": 20}, space,
                               ({"forbidden": {"fast": 10, "slow": 20}},))
    with pytest.raises(ConstraintViolation, match="unknown parameter"):
        validate_configuration({"fast": 10, "slow": 20, "extra": 1}, space)


def test_search_size_limit_stops_before_execution(tmp_path):
    values = list(range(71))
    experiment = Experiment("x", {"a": 0, "b": 0},
        {"a": {"type": "int", "values": values}, "b": {"type": "int", "values": values}})
    called = False
    def executor(_):
        nonlocal called; called = True
        return {}
    with pytest.raises(SearchSpaceTooLarge, match="SEARCH_SPACE_TOO_LARGE"):
        ExperimentRunner().run(experiment, executor, tmp_path)
    assert not called


def test_deterministic_experiment_id_and_config_hash_stability():
    left, right = build_experiment(), build_experiment()
    assert left.experiment_id == right.experiment_id
    assert Experiment.from_dict(left.as_dict()).experiment_id == left.experiment_id
    assert stable_hash({"b": 2, "a": 1}) == stable_hash({"a": 1, "b": 2})


def test_baseline_only_and_no_selection_outputs(tmp_path):
    experiment = build_experiment()
    ExperimentRunner().run(experiment, baseline_executor, tmp_path)
    manifest = (tmp_path / "manifest.json").read_text()
    all_text = "\n".join(path.read_text() for path in tmp_path.iterdir())
    assert '"parameter_search_performed": false' in manifest
    assert '"baseline_only": true' in manifest
    for forbidden in ("best_config", "ranking_score", "leaderboard", "winner"):
        assert forbidden not in all_text.lower()
    with pytest.raises(ValueError, match="BASELINE_ONLY"):
        Experiment("x", {}, {}, optimization_enabled=True)


def test_true_oos_rejection_and_tick_validation():
    with pytest.raises(ValueError, match="TRUE_OOS_BLOCKED"):
        reject_true_oos(["2025-01-01T00:00:00Z"])
    validate_tick_sizes({"Si": .001, "CNY": .001})
    with pytest.raises(ValueError, match="TICK_MODEL_MISMATCH"):
        validate_tick_sizes({"Si": .01, "CNY": .001})


def test_artifacts_are_deterministic(tmp_path):
    experiment = build_experiment()
    a, b = tmp_path / "a", tmp_path / "b"
    runner = ExperimentRunner()
    runner.run(experiment, baseline_executor, a)
    runner.run(experiment, baseline_executor, b)
    validate_determinism(artifact_hashes(a), artifact_hashes(b))
    assert artifact_hashes(a) == artifact_hashes(b)
    assert all(path.suffix in {".json", ".csv", ".md"} for path in a.iterdir())
