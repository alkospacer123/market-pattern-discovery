"""Mutation tests for perpetual-v3 Phase 3's fail-closed contract."""
from copy import deepcopy
import json
from pathlib import Path

import pytest

from TradingSystemLab.optimization.experiment import stable_hash
from TradingSystemLab.robustness import perpetual_v3_phase3 as phase3

REGISTRY = Path("TradingSystemLab/results/perpetual_v3/phase3_candidate_freeze/candidate_registry.json")


def payload():
    return json.loads(REGISTRY.read_text())


def write(tmp_path, value):
    path = tmp_path / "registry.json"
    path.write_text(json.dumps(value))
    return path


def test_exact_registry_consumption():
    candidates, digest = phase3.load_frozen_registry()
    assert [(x["strategy"], x["timeframe"]) for x in candidates] == list(phase3.STUDIES)
    assert len(digest) == 64

@pytest.mark.parametrize("mutation", ["hash", "substitute", "parameter", "provenance"])
def test_registry_mutations_fail_closed(tmp_path, mutation):
    value = payload()
    item = value["candidates"][0]
    if mutation == "hash": item["parameter_hash"] = "0" * 64
    elif mutation == "substitute": item["candidate_id"] = "replacement"
    elif mutation == "parameter": item["parameters"]["ema_fast"] = 21
    else: item["selection_locked_before_validation"] = False
    with pytest.raises(RuntimeError): phase3.load_frozen_registry(write(tmp_path, value))


def test_strategy_source_hash_mismatch(monkeypatch):
    monkeypatch.setitem(phase3.__dict__, "verify_strategy_identity", lambda: (_ for _ in ()).throw(RuntimeError("hash")))
    with pytest.raises(RuntimeError, match="hash"):
        phase3.run(output=Path("unused"))

@pytest.mark.parametrize("expectancy,instruments,years,severe,probability,expected", [
    (.1, True, True, False, .9, "ROBUST_READY"),
    (.1, True, True, True, .9, "BORDERLINE"),
    (-.1, True, True, False, .9, "REJECTED"),
])
def test_canonical_classification(expectancy, instruments, years, severe, probability, expected):
    assert phase3.classify(expectancy, instruments, years, severe, probability) == expected


def test_non_c1_and_tick_are_frozen():
    assert phase3.COST_MODELS == ("C1",)
    assert phase3.FROZEN_TICK_SIZE == .001


def test_true_oos_trade_rejected(monkeypatch):
    import pandas as pd
    bad = pd.DataFrame({"entry_time": ["2025-01-01T00:00:00Z"], "exit_time": ["2025-01-01T01:00:00Z"]})
    monkeypatch.setattr(phase3, "execute_t2", lambda parameters, frames: bad)
    with pytest.raises(RuntimeError, match="TRUE_OOS"):
        phase3._execute("T2", {}, {})


def test_outputs_are_byte_deterministic():
    first = sorted((p.relative_to(phase3.OUTPUT_ROOT), p.read_bytes()) for p in phase3.OUTPUT_ROOT.rglob("*") if p.is_file())
    second = sorted((p.relative_to(phase3.OUTPUT_ROOT), p.read_bytes()) for p in phase3.OUTPUT_ROOT.rglob("*") if p.is_file())
    assert first == second
