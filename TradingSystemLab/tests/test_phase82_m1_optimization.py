from __future__ import annotations

from pathlib import Path

import pandas as pd
import pytest

from TradingSystemLab.multitimeframe.phase73 import hash_tree
from TradingSystemLab.optimization.phase82 import BASELINES, MAX_CONFIGURATIONS, RANGES, bounded_design, run, validate_bounds
from TradingSystemLab.timeframe_validation.phase81 import validate_candle_order


def _trades(key: str, config: dict, alias: str, frame: pd.DataFrame) -> pd.DataFrame:
    # Stable synthetic executions keep regression tests independent of private market data.
    offset = sum(RANGES[key][name].index(config[name]) for name in RANGES[key]) * .001
    times = pd.date_range("2024-01-02 10:00", periods=12, freq="10min", tz="Europe/Moscow")
    net = [1.0 + offset, -.45, .4, -.2] * 3
    return pd.DataFrame({"trade_id": [f"{key}-{alias}-{n}" for n in range(12)],
        "entry_time": times, "exit_time": times + pd.Timedelta("5min"), "net_R": net})


def test_bounds_include_phase81_baseline() -> None:
    for key in ("T2", "T3"):
        design = bounded_design(key, BASELINES[key]["parameters"])
        assert BASELINES[key]["parameters"] in design
        assert len(design) <= MAX_CONFIGURATIONS
        validate_bounds(key, design)


def test_development_barrier_rejects_2025() -> None:
    frame = pd.DataFrame(index=pd.DatetimeIndex(["2025-01-01T00:00:00Z"]))
    with pytest.raises(ValueError, match="TRUE_OOS_BARRIER_VIOLATION"):
        validate_candle_order(frame)


def test_determinism_provenance_and_baseline_protection(tmp_path: Path,
                                                        monkeypatch: pytest.MonkeyPatch) -> None:
    import TradingSystemLab.optimization.phase82 as phase82
    monkeypatch.setattr(phase82, "load_m1_development", lambda *args: (pd.DataFrame({"Close": [1]}), []))
    monkeypatch.setattr(phase82, "_execute", _trades)
    baseline_hash = hash_tree(phase82.BASELINE_ROOT)
    output = tmp_path / "M1"
    first = run(output=output)
    first_hash = hash_tree(output)
    second = run(output=output)
    assert first == second
    assert first_hash == hash_tree(output)
    assert baseline_hash == hash_tree(phase82.BASELINE_ROOT)
    for key in ("T2", "T3"):
        registry = (output / key / "candidate_registry.json").read_text()
        assert f'"candidate_id": "{key}_M1_candidate_v1"' in registry
        assert '"configuration_id"' in registry and '"parameter_hash"' in registry
        assert '"source_hashes"' in registry


def test_no_forbidden_phase_interfaces() -> None:
    source = Path("TradingSystemLab/optimization/phase82.py").read_text(encoding="utf-8")
    assert "true_oos import" not in source
    assert "walk_forward import" not in source
    assert "portfolio import" not in source
