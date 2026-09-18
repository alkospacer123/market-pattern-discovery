from __future__ import annotations

import copy
import inspect
import json
from pathlib import Path

import pandas as pd
import pytest

from TradingSystemLab.optimization.experiment import stable_hash
from TradingSystemLab.true_oos import m15


def _candles(start: str = "2025-01-01 10:00", periods: int = 220) -> pd.DataFrame:
    index = pd.date_range(start, periods=periods, freq="15min", tz="Europe/Moscow")
    values = pd.Series(range(periods), index=index, dtype=float) / 100 + 10
    return pd.DataFrame({"Open": values, "High": values + .1, "Low": values - .1,
                         "Close": values + .02, "Volume": 1.0}, index=index)


def test_frozen_registry_ids_and_parameter_hashes_are_exact():
    registries = m15.load_frozen_registry()
    assert {key: row["baseline_candidate_id"] for key, row in registries.items()} == m15.ALLOWED_CANDIDATES
    assert all(stable_hash(row["parameters"]) == row["parameter_hash"] for row in registries.values())
    with pytest.raises(TypeError, match="frozen"):
        registries["T2"]["parameters"]["ema_fast"] = 1
    assert "parameters" not in inspect.signature(m15.run).parameters
    assert not hasattr(m15, "optimize") and not hasattr(m15, "rank")


def test_true_oos_rejects_any_pre_2025_close():
    frame = _candles("2024-12-31 23:45", 2)
    with pytest.raises(RuntimeError, match="PRE_BOUNDARY"):
        m15.validate_true_oos_candles(frame)


def test_parameter_or_candidate_mutation_hard_fails():
    registry = m15.load_frozen_registry()["T2"]
    changed = copy.deepcopy(registry); changed["parameters"] = dict(registry["parameters"])
    changed["parameters"]["ema_fast"] += 1
    with pytest.raises(RuntimeError, match="PARAMETER_HASH"):
        m15.execute_candidate("T2", changed, {"Si": _candles(), "CNY": _candles()})
    changed = copy.deepcopy(registry); changed["baseline_candidate_id"] = "other"
    with pytest.raises(RuntimeError, match="CANDIDATE_ID"):
        m15.execute_candidate("T2", changed, {"Si": _candles(), "CNY": _candles()})


def test_period_is_continuous_flat_and_has_no_reset(monkeypatch, tmp_path):
    seen = []
    monkeypatch.setattr(m15, "execute_candidate", lambda key, registry, loaded:
                        (seen.append((key, loaded)) or pd.DataFrame(columns=m15.TRADE_COLUMNS)))
    monkeypatch.setattr(m15, "load_true_oos", lambda root, alias: (_candles(), [tmp_path / f"{alias}.csv"]))
    monkeypatch.setattr(m15, "_sha", lambda path: "0" * 64 if not path.exists() else __import__("hashlib").sha256(path.read_bytes()).hexdigest())
    first, second = tmp_path / "one", tmp_path / "two"
    a = m15.run(output=first); b = m15.run(output=second)
    assert a["initial_state"] == "FLAT" and a["internal_resets"] == 0 and a["continuous_period"]
    assert a["artifact_sha256"] == b["artifact_sha256"]
    assert [item[0] for item in seen] == ["T2", "T3", "T2", "T3"]


def test_causal_h1_context_never_uses_a_future_close():
    candles = _candles(periods=16)
    context = m15.causal_h1_context(candles)
    assert list(context.index) == [candles.index[i] for i in (3, 7, 11, 15)]
    for close in context.index:
        assert close in candles.index and candles.index[candles.index <= close].max() == close


def test_execution_only_source_guard_and_declared_flags():
    m15._assert_execution_only()
    source = inspect.getsource(m15.run)
    assert "optimization" not in inspect.signature(m15.run).parameters
    assert "ranking" not in inspect.signature(m15.run).parameters
    assert '"optimization": False' in source and '"ranking": False' in source
