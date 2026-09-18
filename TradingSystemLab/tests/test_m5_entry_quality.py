from __future__ import annotations

import hashlib
import json
from pathlib import Path

import pandas as pd
import pytest

from TradingSystemLab.multitimeframe.phase73 import hash_tree
from TradingSystemLab.timeframe_analysis.m5_entry_quality import CANDIDATES, REPORTS, run


def _fixture(root: Path):
    validation, optimization = root / "validation", root / "optimization"
    raw_index = pd.date_range("2023-01-02 00:00", periods=260, freq="5min", tz="UTC")
    close = pd.Series([100 + n * .01 for n in range(260)], index=raw_index)
    bars = pd.DataFrame({"Open": close - .02, "High": close + .08,
                         "Low": close - .08, "Close": close}, index=raw_index)
    entry = raw_index[220] + pd.Timedelta(minutes=5)
    rows = [{"trade_id": "a", "instrument": "USDRUBF", "direction": "LONG",
             "entry_time": entry.isoformat(), "entry_price": float(close.iloc[220]),
             "initial_stop": float(close.iloc[220] - 1), "initial_risk_points": 1,
             "exit_time": (entry + pd.Timedelta(minutes=20)).isoformat(),
             "exit_price": float(close.iloc[224]), "exit_reason": "TIME", "net_R": -.25},
            {"trade_id": "b", "instrument": "CNYRUBF", "direction": "LONG",
             "entry_time": entry.isoformat(), "entry_price": float(close.iloc[220]),
             "initial_stop": float(close.iloc[220] - 1), "initial_risk_points": 1,
             "exit_time": (entry + pd.Timedelta(minutes=130)).isoformat(),
             "exit_price": float(close.iloc[246]), "exit_reason": "TIME", "net_R": 1.25}]
    for scope, identity in CANDIDATES.items():
        ledger = validation / scope / "trades.csv"
        ledger.parent.mkdir(parents=True)
        pd.DataFrame(rows).assign(trade_id=lambda x: scope + "-" + x.trade_id).to_csv(ledger, index=False)
        registry = optimization / scope / "candidate_registry.json"
        registry.parent.mkdir(parents=True)
        registry.write_text(json.dumps({"candidate_id": identity}), encoding="utf-8")
    return validation, optimization, {"USDRUBF": bars.copy(), "CNYRUBF": bars.copy()}


def _file_hashes(path: Path) -> dict[str, str]:
    return {str(p.relative_to(path)): hashlib.sha256(p.read_bytes()).hexdigest()
            for p in sorted(path.rglob("*")) if p.is_file()}


def test_deterministic_repeated_execution_and_identical_artifact_hashes(tmp_path: Path) -> None:
    validation, optimization, market = _fixture(tmp_path)
    output = tmp_path / "output"
    first_manifest = run(validation, optimization, output=output, market_data=market)
    first = _file_hashes(output)
    second_manifest = run(validation, optimization, output=output, market_data=market)
    assert first == _file_hashes(output)
    assert first_manifest == second_manifest
    assert first_manifest["status"] == "PHASE_M5_ENTRY_QUALITY_DIAGNOSTIC_COMPLETE"


def test_source_immutability_and_required_artifacts(tmp_path: Path) -> None:
    validation, optimization, market = _fixture(tmp_path)
    before_validation, before_optimization = hash_tree(validation), hash_tree(optimization)
    output = tmp_path / "output"
    run(validation, optimization, output=output, market_data=market)
    assert before_validation == hash_tree(validation)
    assert before_optimization == hash_tree(optimization)
    for scope in ("T2", "T3", "COMBINED"):
        assert {path.name for path in (output / scope).iterdir()} == set(REPORTS)
    assert {"comparison.csv", "entry_quality_report.md", "manifest.json"}.issubset(
        {path.name for path in output.iterdir()})


def test_true_oos_rejection_before_output(tmp_path: Path) -> None:
    validation, optimization, market = _fixture(tmp_path)
    market["USDRUBF"] = market["USDRUBF"].set_axis(
        pd.date_range("2025-01-01", periods=len(market["USDRUBF"]), freq="5min", tz="UTC"))
    output = tmp_path / "output"
    with pytest.raises(ValueError, match="TRUE_OOS"):
        run(validation, optimization, output=output, market_data=market)
    assert not output.exists()


def test_no_lookahead_entry_features(tmp_path: Path) -> None:
    validation, optimization, market = _fixture(tmp_path)
    first = tmp_path / "first"
    run(validation, optimization, output=first, market_data=market)
    baseline = pd.read_csv(first / "T2/trend_context.csv")
    # Change only candles after all entries. Entry context must remain identical.
    changed = {key: value.copy() for key, value in market.items()}
    for frame in changed.values():
        frame.loc[frame.index[-20]:, ["Open", "High", "Low", "Close"]] *= 100
    second = tmp_path / "second"
    run(validation, optimization, output=second, market_data=changed)
    pd.testing.assert_frame_equal(baseline, pd.read_csv(second / "T2/trend_context.csv"))


def test_frozen_candidate_identity_validation(tmp_path: Path) -> None:
    validation, optimization, market = _fixture(tmp_path)
    (optimization / "T2/candidate_registry.json").write_text(
        json.dumps({"candidate_id": "not-frozen"}), encoding="utf-8")
    output = tmp_path / "output"
    with pytest.raises(ValueError, match="CANDIDATE_IDENTITY_MISMATCH"):
        run(validation, optimization, output=output, market_data=market)
    assert not output.exists()
