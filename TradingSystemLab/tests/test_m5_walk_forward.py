from __future__ import annotations

import hashlib
import json
from pathlib import Path

import pandas as pd
import pytest

from TradingSystemLab.multitimeframe.phase73 import hash_tree
from TradingSystemLab.walk_forward.m5 import FOLDS, STATUS, reject_true_oos, run, validate_fold_schedule


def _fixture(root: Path):
    validation, optimization = root / "validation", root / "optimization"
    index = pd.date_range("2022-01-01 10:00", "2024-12-30 10:00", freq="1D", tz="UTC")
    values = pd.Series(100 + pd.RangeIndex(len(index)) * .01, index=index)
    bars = pd.DataFrame({"Open": values - .02, "High": values + .08,
                         "Low": values - .08, "Close": values}, index=index)
    dates = pd.to_datetime(["2023-03-01 10:05Z", "2023-08-01 10:05Z",
                            "2024-02-01 10:05Z", "2024-08-01 10:05Z"])
    rows = []
    for number, entry in enumerate(dates):
        price = float(bars.loc[entry - pd.Timedelta(minutes=5), "Close"])
        result = (1.0, -0.5, 1.5, -0.25)[number]
        rows.append({"trade_id": str(number), "instrument": "USDRUBF" if number % 2 == 0 else "CNYRUBF",
                     "direction": "LONG" if number % 2 == 0 else "SHORT", "entry_time": entry.isoformat(),
                     "entry_price": price, "initial_stop": price - 1, "initial_risk_points": 1,
                     "exit_time": (entry + pd.Timedelta(minutes=30)).isoformat(), "exit_price": price + result,
                     "exit_reason": "TIME", "net_R": result})
    for key in ("T2", "T3"):
        (validation / key).mkdir(parents=True)
        (optimization / key).mkdir(parents=True)
        pd.DataFrame(rows).assign(trade_id=lambda frame: key + "-" + frame.trade_id).to_csv(
            validation / key / "trades.csv", index=False)
        (optimization / key / "candidate_registry.json").write_text(json.dumps({
            "candidate_id": f"{key}_M5_candidate_v1", "parameters": {"frozen": True}}) + "\n")
    (validation / "manifest.json").write_text(json.dumps({
        "cost_model": {"cost_ticks_per_side": 1.0, "slippage_ticks_per_side": 0.0}}) + "\n")
    return validation, optimization, {"USDRUBF": bars.copy(), "CNYRUBF": bars.copy()}


def _hashes(path: Path) -> dict[str, str]:
    return {str(item.relative_to(path)): hashlib.sha256(item.read_bytes()).hexdigest()
            for item in sorted(path.rglob("*")) if item.is_file()}


def test_repeated_execution_has_identical_artifacts_and_immutable_sources(tmp_path: Path) -> None:
    validation, optimization, market = _fixture(tmp_path)
    before = hash_tree(validation), hash_tree(optimization)
    output = tmp_path / "walk_forward"
    first = run(validation, optimization, output=output, market_data=market)
    first_hashes = _hashes(output)
    second = run(validation, optimization, output=output, market_data=market)
    assert first == second
    assert first_hashes == _hashes(output)
    assert before == (hash_tree(validation), hash_tree(optimization))
    assert first["status"] == STATUS
    assert first["deterministic"] is True
    assert first["optimization"] is first["ranking"] is False
    assert first["parameter_change"] is first["strategy_change"] is first["true_oos_access"] is False
    for candidate in ("baseline", "session_candidate", "session_ema50_normal_candidate"):
        assert (output / candidate / "summary.csv").is_file()
        assert {item.name for item in (output / candidate).iterdir() if item.is_dir()} == {"WF01", "WF02", "WF03"}


def test_fold_schedule_and_breakdowns_are_exact(tmp_path: Path) -> None:
    validate_fold_schedule()
    assert FOLDS == (
        ("WF01", "2023-01-01", "2023-07-01", "2023-07-01", "2024-01-01"),
        ("WF02", "2023-01-01", "2024-01-01", "2024-01-01", "2024-07-01"),
        ("WF03", "2023-01-01", "2024-07-01", "2024-07-01", "2025-01-01"),
    )
    validation, optimization, market = _fixture(tmp_path)
    output = tmp_path / "walk_forward"
    manifest = run(validation, optimization, output=output, market_data=market)
    assert manifest["development_period"] == "2023-01-01 to 2024-12-31"
    assert manifest["true_oos_boundary"] == "2025-01-01"
    metrics = pd.read_csv(output / "baseline/WF01/metrics.csv")
    assert set(metrics.dimension) == {"portfolio", "strategy", "instrument", "direction"}
    assert set(metrics.category) == {"COMBINED", "T2", "T3", "USDRUBF", "CNYRUBF", "LONG", "SHORT"}
    assert set(metrics.split) == {"train", "test"}


def test_true_oos_and_candidate_identity_fail_closed_before_output(tmp_path: Path) -> None:
    with pytest.raises(ValueError, match="TRUE_OOS"):
        reject_true_oos(pd.DataFrame({"entry_time": ["2025-01-01T00:00:00Z"]}))
    validation, optimization, market = _fixture(tmp_path)
    market["USDRUBF"] = market["USDRUBF"].set_axis(
        pd.date_range("2025-01-01", periods=len(market["USDRUBF"]), freq="1D", tz="UTC"))
    output = tmp_path / "walk_forward"
    with pytest.raises(ValueError, match="TRUE_OOS"):
        run(validation, optimization, output=output, market_data=market)
    assert not output.exists()
    validation, optimization, market = _fixture(tmp_path / "identity")
    (optimization / "T2/candidate_registry.json").write_text(json.dumps({"candidate_id": "changed"}))
    with pytest.raises(ValueError, match="CANDIDATE_IDENTITY_MISMATCH:T2"):
        run(validation, optimization, output=tmp_path / "other", market_data=market)
