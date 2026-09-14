from dataclasses import asdict
from pathlib import Path

import pandas as pd
import pytest

from TradingSystemLab.optimization.experiment import stable_hash
from TradingSystemLab.optimization.phase32 import PARAMETERS
from TradingSystemLab.optimization.validation import reject_true_oos
from TradingSystemLab.robustness.phase33 import ITERATIONS, _bootstrap, select_candidate


OPT = Path("TradingSystemLab/results/optimization")


def test_candidate_selection_is_deterministic_and_has_provenance():
    first = select_candidate("T2", OPT)
    assert first == select_candidate("T2", OPT)
    assert first["candidate_id"] == "T2_candidate_v1"
    assert first["phase32_configuration_id"] == "T2-0007-608dc87d09f1"
    assert first["selection_locked_before_validation"] is True


def test_both_candidates_are_from_robust_plateau():
    for key in ("T2", "T3"):
        candidate = select_candidate(key, OPT)
        plateau = pd.read_csv(OPT / key / "plateau_report.csv")
        row = plateau.loc[plateau.configuration_id.eq(candidate["phase32_configuration_id"])]
        assert row.iloc[0].classification == "ROBUST_PLATEAU"


def test_selection_does_not_modify_frozen_baseline():
    before = {key: stable_hash(asdict(PARAMETERS[key])) for key in ("T2", "T3")}
    select_candidate("T2", OPT); select_candidate("T3", OPT)
    assert before == {key: stable_hash(asdict(PARAMETERS[key])) for key in ("T2", "T3")}


def test_true_oos_is_rejected():
    with pytest.raises(ValueError, match="TRUE_OOS_BLOCKED"):
        reject_true_oos(pd.to_datetime(["2025-01-01T00:00:00Z"]))


def test_bootstrap_is_deterministic_and_minimum_size():
    values = pd.Series([-1.0, .5, 1.5, 2.0])
    assert _bootstrap(values) == _bootstrap(values)
    assert _bootstrap(values)["iterations"] == ITERATIONS == 10_000
    assert _bootstrap(values)["interpretation"] == "DIAGNOSTIC_ONLY_IID_TRADE_BOOTSTRAP"
