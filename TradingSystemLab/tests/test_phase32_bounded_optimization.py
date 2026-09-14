from __future__ import annotations

import hashlib
from pathlib import Path

import pytest

from TradingSystemLab.optimization.phase32 import (PARAMETERS, SPACES, analyze,
    bounded_design, experiment_definition, parameter_space)
from TradingSystemLab.optimization.runner import SearchSpaceTooLarge


def test_all_six_spaces_are_finite_bounded_and_include_frozen_baseline():
    assert set(SPACES) == {"T1", "T2", "T3", "R1", "R2", "R3"}
    for key in SPACES:
        rows = bounded_design(key)
        baseline = {name: getattr(PARAMETERS[key], name) for name in SPACES[key]}
        assert baseline in rows
        assert 1 < len(rows) <= 5000
        assert all(parameter_space(key).contains(name, row[name]) for row in rows for name in SPACES[key])


def test_design_and_experiment_ids_are_deterministic():
    for key in SPACES:
        assert bounded_design(key) == bounded_design(key)
        assert experiment_definition(key) == experiment_definition(key)


def test_design_limit_fails_closed(monkeypatch):
    monkeypatch.setattr("TradingSystemLab.optimization.phase32.DEFAULT_SEARCH_SPACE_LIMIT", 1)
    with pytest.raises(SearchSpaceTooLarge, match="SEARCH_SPACE_TOO_LARGE"):
        bounded_design("R3")


def test_plateau_requires_multiple_stable_positive_neighbors():
    configs=[{"x":1},{"x":2},{"x":3}]
    results=[{"configuration_id":str(i),"expectancy_C1":v,"PF_C1":1.2} for i,v in enumerate((.1,.11,.09))]
    old=SPACES["X"] if "X" in SPACES else None
    SPACES["X"]={"x":("int",[1,2,3])}
    try:
        plateau,_,overall=analyze(configs,results,"X")
        assert plateau[1]["classification"] == "ROBUST_PLATEAU"
        assert overall == "ROBUST_PLATEAU"
    finally:
        if old is None: del SPACES["X"]


def test_frozen_strategy_and_config_hashes_are_unchanged():
    expected = {
        "configs/T1_BBW_Donchian.yaml": "bfd95f92a3db9fba874756a0d3accfd836b7ed453dc46e473b290a423bcf99ae",
        "configs/T2_Trend_Pullback.yaml": "d3614150fc50b056cbfdb6ca7f011adf7581577b43bdc67ea82028c6c7ad67fb",
        "configs/R1_Bollinger_False_Breakout.yaml": "231ae54161cce9dfb062cbf968fe693d2e63f1d06249412ff0d2b184e11077f3",
        "configs/R2_Liquidity_Sweep.yaml": "f1265ba2b6f0836b0d6440836ba3624711c2d3f71691de85ef74560253b2f6e6",
        "configs/R3_Round_Level_Rejection.yaml": "560fe46ae1eb86d6f5f3b3cd8572aa43977869ee8dc530990568bcd258fecaf0",
        "results/T3_parameter_robustness/frozen_baseline.json": "90dd22c5e91c1b0245c168de73c9634a4387aa7dbe051662716726eb4940ddfb",
    }
    root=Path(__file__).resolve().parents[1]
    # This check records inputs without writing them; repository-level diff tests
    # additionally ensure frozen files are absent from the Phase 3.2 patch.
    for relative, digest in expected.items():
        assert hashlib.sha256((root/relative).read_bytes()).hexdigest() == digest
