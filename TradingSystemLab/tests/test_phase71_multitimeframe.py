from __future__ import annotations

from dataclasses import asdict
import hashlib
from pathlib import Path

import pandas as pd
import pytest

from TradingSystemLab.core.instrument_specs import get_instrument_spec
from TradingSystemLab.multitimeframe.phase71 import (TimeframeAdapter, _aggregate,
    frozen_candidates, reject_true_oos, run, verify_frozen_strategies)
from TradingSystemLab.optimization.experiment import stable_hash


def _bars(periods: int = 8) -> pd.DataFrame:
    index = pd.date_range("2024-01-03 10:00", periods=periods, freq="h", tz="Europe/Moscow", name="CloseTime")
    return pd.DataFrame({"Open": range(periods), "High": [x + 2 for x in range(periods)],
                         "Low": [x - 1 for x in range(periods)], "Close": [x + 1 for x in range(periods)]}, index=index)


def _hash_tree(path: Path) -> dict[str, str]:
    return {str(p.relative_to(path)): hashlib.sha256(p.read_bytes()).hexdigest()
            for p in sorted(path.rglob("*")) if p.is_file()}


def test_timeframe_adapter_is_causal_and_complete() -> None:
    source = _bars()
    h4 = TimeframeAdapter("H4").execution(source)
    assert list(h4.index) == [source.index[3], source.index[7]]
    assert h4.iloc[0].to_dict() == {"Open": 0, "High": 5, "Low": -1, "Close": 4}
    assert TimeframeAdapter("H1").execution(source).equals(source)


def test_intraday_aggregation_resets_at_day_boundary() -> None:
    first = _bars(3)
    second = first.copy(); second.index = second.index + pd.Timedelta(days=1)
    assert _aggregate(pd.concat([first, second]), 4).empty


def test_research_instrument_registry_units() -> None:
    for symbol in ("USDRUBF", "CNYRUBF", "EURRUBF", "HKDRUBF"):
        spec = get_instrument_spec(symbol)
        assert (spec.tick_size, spec.price_precision, spec.lot_size) == (0.01, 0.001, 1000)


def test_true_oos_is_rejected_at_boundary() -> None:
    with pytest.raises(ValueError, match="TRUE_OOS_BARRIER_VIOLATION"):
        reject_true_oos(pd.DatetimeIndex(["2025-01-01T00:00:00Z"]))


def test_frozen_strategy_and_parameter_integrity() -> None:
    verify_frozen_strategies()
    candidates = frozen_candidates()
    assert stable_hash(candidates["T2"]["parameters"]) == "2b0494cdd24bfbfa8ce7d657d6f83d1408f07b9f565d38d093dec5b4856e3c00"
    assert stable_hash(candidates["T3"]["parameters"]) == "938b6b3b78f680010115a204b9a49e7eef962db119f4ea121e388c00741920ba"


def test_unavailable_instruments_do_not_fail_and_outputs_are_deterministic(tmp_path: Path) -> None:
    output = tmp_path / "one"
    protected = [Path("TradingSystemLab/results/true_oos_validation"),
                 Path("TradingSystemLab/results/portfolio_construction")]
    before = [_hash_tree(path) for path in protected]
    run(output=output); first = _hash_tree(output)
    run(output=output); second = _hash_tree(output)
    assert first == second
    manifest = (output / "manifest.json").read_text(encoding="utf-8")
    assert '"instrument": "EURRUBF"' in manifest and '"status": "DATA_UNAVAILABLE"' in manifest
    assert before == [_hash_tree(path) for path in protected]
