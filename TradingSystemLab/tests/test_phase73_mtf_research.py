from __future__ import annotations

import hashlib
from pathlib import Path

import pandas as pd
import pytest

from TradingSystemLab.core.mtf import align_closed_context
from TradingSystemLab.multitimeframe.phase71 import reject_true_oos, verify_frozen_strategies
from TradingSystemLab.multitimeframe.phase73 import causal_aggregate, hash_tree, run


def _bars(periods: int = 8, freq: str = "30min") -> pd.DataFrame:
    index = pd.date_range("2024-01-03 10:00", periods=periods, freq=freq,
                          tz="Europe/Moscow", name="CloseTime")
    return pd.DataFrame({"Open": range(periods), "High": [x + 2 for x in range(periods)],
                         "Low": [x - 1 for x in range(periods)], "Close": [x + 1 for x in range(periods)]}, index=index)


def test_causal_context_is_unavailable_on_simultaneous_execution_close() -> None:
    execution = _bars(8)
    context = causal_aggregate(execution, "M30", "H1")
    aligned = align_closed_context(execution, context.assign(marker=[1, 2, 3, 4]), "30min")
    assert pd.isna(aligned.loc[context.index[0], "marker"])
    assert aligned.loc[context.index[0] + pd.Timedelta("30min"), "marker"] == 1


def test_aggregation_drops_gaps_and_resets_days() -> None:
    bars = _bars(4).drop(_bars(4).index[1])
    assert len(causal_aggregate(bars, "M30", "H1")) == 0


def test_true_oos_and_frozen_provenance() -> None:
    verify_frozen_strategies()
    with pytest.raises(ValueError, match="TRUE_OOS_BARRIER_VIOLATION"):
        reject_true_oos(pd.DatetimeIndex(["2025-01-01T00:00:00Z"]))


def test_deterministic_artifacts_and_protected_results(tmp_path: Path,
                                                       monkeypatch: pytest.MonkeyPatch) -> None:
    import TradingSystemLab.multitimeframe.phase73 as phase73
    # Determinism of the artifact writer does not require replaying the full
    # market history in a unit test; integration execution covers that path.
    monkeypatch.setattr(phase73, "load_development", lambda *_: (None, []))
    protected = [Path("TradingSystemLab/results/true_oos_validation"),
                 Path("TradingSystemLab/results/portfolio_construction")]
    before = [hash_tree(p) for p in protected]
    output = tmp_path / "mtf"
    run(output=output)
    first = hash_tree(output)
    run(output=output)
    assert first == hash_tree(output)
    assert before == [hash_tree(p) for p in protected]
    assert (output / "H4_H1/T2/trades.csv").exists()
    assert '"optimization": false' in (output / "manifest.json").read_text()


def test_missing_data_returns_data_unavailable(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    import TradingSystemLab.multitimeframe.phase73 as phase73
    monkeypatch.setattr(phase73, "load_development", lambda *_: (None, []))
    output = tmp_path / "missing"
    run(output=output)
    assert "DATA_UNAVAILABLE" in (output / "H1_M15/T3/metrics.json").read_text()
