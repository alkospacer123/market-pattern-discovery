from __future__ import annotations
from copy import deepcopy
from pathlib import Path
import inspect
import json
import pandas as pd
import pytest

import TradingSystemLab.timeframe_validation.d1_baseline as baseline
from TradingSystemLab.optimization.experiment import stable_hash


def _bars(days: int = 5, hours: int = 3) -> pd.DataFrame:
    stamps, rows = [], []
    n = 0
    for day in pd.date_range("2024-01-03", periods=days, freq="D"):
        for hour in range(hours):
            stamps.append((day + pd.Timedelta(hours=10 + hour)).tz_localize("Europe/Moscow"))
            rows.append({"Open": n, "High": n + 2, "Low": n - 1, "Close": n + 1, "Volume": 10})
            n += 1
    return pd.DataFrame(rows, index=pd.DatetimeIndex(stamps, name="CloseTime"))


def test_standalone_frozen_contract() -> None:
    source = inspect.getsource(baseline)
    assert baseline.TIMEFRAME == "D1" and baseline.PHASE == "D1_BASELINE"
    for forbidden in ("h4_baseline", "m30_baseline", "m15_baseline", "m5_baseline", "phase81"):
        assert forbidden not in source
    baseline.verify_frozen_strategies()
    candidates = baseline.frozen_candidates()
    original = deepcopy(candidates)
    assert baseline.STRATEGY_SHA256 == {
        "T2": "376df085cfda85eefccb31343aad40ed4fbb1078f1314496472a3a4ac9507774",
        "T3": "840dd3b2cda43fa00259445cd0a22ace6d82e677f4c793028ccc8126f9ad9a8c"}
    for key in ("T2", "T3"):
        assert candidates[key]["candidate_id"] == baseline.EXPECTED[key]["candidate_id"]
        assert candidates[key]["phase32_configuration_id"] == baseline.EXPECTED[key]["phase32_configuration_id"]
        assert candidates[key]["parameters"] == baseline.EXPECTED[key]["parameters"]
        assert stable_hash(candidates[key]["parameters"]) == baseline.EXPECTED[key]["parameter_hash"]
    assert candidates == original and candidates["T3"]["parameters"]["ema_period"] == 75


def test_explicit_source_discovery_and_validation() -> None:
    paths = baseline.discover_h1_files(baseline.APPROVED_DATA_ROOT, "Si")
    assert paths and all("_H1_" in p.name and ("_2023_" in p.name or "_2024_" in p.name) for p in paths)
    assert not any("_2025_" in p.name for p in paths)
    with pytest.raises(ValueError, match="UNAPPROVED"):
        baseline.discover_h1_files(Path("/tmp"), "Si")
    future = _bars(1); future.index = future.index + pd.DateOffset(years=1)
    with pytest.raises(ValueError, match="TRUE_OOS"):
        baseline.validate_development(future)
    unordered = _bars(1).iloc[::-1]
    with pytest.raises(ValueError, match="TIMESTAMP"):
        baseline.validate_development(unordered)
    duplicate = pd.concat([_bars(1), _bars(1).iloc[:1]]).sort_index()
    with pytest.raises(ValueError, match="TIMESTAMP"):
        baseline.validate_development(duplicate)


def test_causal_d1_and_exact_4d_context() -> None:
    h1 = _bars()
    d1 = baseline.causal_d1(h1)
    assert len(d1) == 5 and d1.index.tolist() == [g.index[-1] for _, g in h1.groupby(h1.index.normalize())]
    assert d1.iloc[0].to_dict() == {"Open": 0, "High": 4, "Low": -1, "Close": 3, "Volume": 30}
    context = baseline.causal_4d(d1)
    assert len(context) == 1 and context.index[0] == d1.index[3]
    assert context.iloc[0].to_dict() == {"Open": 0, "High": 13, "Low": -1, "Close": 12, "Volume": 120}
    assert all(context.index <= d1.index.max())


def test_c1_metrics_and_identity() -> None:
    gross, risk = pd.Series([1., -1.]), pd.Series([10., 20.])
    assert (gross - 2 / risk).tolist() == pytest.approx([.8, -1.1])
    assert [f"T2-D1-Si-{n:06d}" for n in range(1, 3)] == ["T2-D1-Si-000001", "T2-D1-Si-000002"]
    source = inspect.getsource(baseline)
    assert '"t3_context": "D1_TO_4D"' in source
    assert "causal_4d(execution)" in source
    for name in ("optimize", "rank", "select", "walk_forward", "true_oos"):
        assert not hasattr(baseline, name)


def test_deterministic_regeneration_protection_and_manifest(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    synthetic = _bars(240, 1)
    monkeypatch.setattr(baseline, "load_h1_development", lambda *_: (synthetic, [Path(__file__)]))
    monkeypatch.setattr(baseline, "_execute", lambda *args: pd.DataFrame(columns=baseline.TRADE_COLUMNS))
    output = tmp_path / "D1"
    assert baseline.run(output=output)["status"] == "PHASE_D1_BASELINE_COMPLETE"
    first = baseline.hash_tree(output)
    baseline.run(output=output)
    assert first == baseline.hash_tree(output)
    manifest = json.loads((output / "manifest.json").read_text())
    assert manifest["methodological_source"] == "H1_BASELINE"
    assert manifest["t3_context"] == "D1_TO_4D"
    assert manifest["historical_phase_7_1_parity"]
    for flag in ("optimization", "ranking", "selection", "robustness", "walk_forward", "parameter_change", "strategy_change"):
        assert manifest[flag] is False
    assert manifest["true_oos_blocked"] and manifest["protected_research_unchanged"]
