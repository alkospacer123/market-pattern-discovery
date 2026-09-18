from __future__ import annotations

import hashlib
import json
from pathlib import Path

import pandas as pd
import pytest

from TradingSystemLab.multitimeframe.phase73 import hash_tree
from TradingSystemLab.timeframe_analysis.m5_overextension_session_candidate import FILES, run


def _fixture(root: Path):
    validation, optimization = root / "validation", root / "optimization"
    index = pd.date_range("2023-01-02 00:00", periods=500, freq="5min", tz="UTC")
    close = pd.Series(100 + pd.RangeIndex(len(index)) * .01, index=index)
    bars = pd.DataFrame({"Open": close - .02, "High": close + .08,
                         "Low": close - .08, "Close": close}, index=index)
    # Raw bars are open-labelled, hence entries are five minutes after an index value.
    entries = [index[220] + pd.Timedelta(minutes=5), index[225] + pd.Timedelta(minutes=5),
               index[309] + pd.Timedelta(minutes=5), index[310] + pd.Timedelta(minutes=5)]
    rows = []
    for number, (entry, duration, result) in enumerate(zip(entries, (20, 130, 30, 25), (-1., 2., .5, -.5))):
        price = float(bars.loc[entry - pd.Timedelta(minutes=5), "Close"])
        rows.append({"trade_id": str(number), "instrument": "USDRUBF" if number % 2 == 0 else "CNYRUBF",
                     "direction": "LONG", "entry_time": entry.isoformat(), "entry_price": price,
                     "initial_stop": price - 1, "initial_risk_points": 1,
                     "exit_time": (entry + pd.Timedelta(minutes=duration)).isoformat(),
                     "exit_price": price + result, "exit_reason": "TIME", "net_R": result})
    for key in ("T2", "T3"):
        (validation / key).mkdir(parents=True)
        (optimization / key).mkdir(parents=True)
        pd.DataFrame(rows).assign(trade_id=lambda x: key + "-" + x.trade_id).to_csv(validation / key / "trades.csv", index=False)
        (optimization / key / "candidate_registry.json").write_text(json.dumps({
            "candidate_id": f"{key}_M5_candidate_v1", "parameters": {"frozen": True}}) + "\n")
    return validation, optimization, {"USDRUBF": bars.copy(), "CNYRUBF": bars.copy()}


def _hashes(path: Path) -> dict[str, str]:
    return {str(item.relative_to(path)): hashlib.sha256(item.read_bytes()).hexdigest()
            for item in sorted(path.rglob("*")) if item.is_file()}


def test_deterministic_identical_hashes_source_immutability_and_artifacts(tmp_path: Path) -> None:
    validation, optimization, market = _fixture(tmp_path)
    before = hash_tree(validation), hash_tree(optimization)
    output = tmp_path / "output"
    first_manifest = run(validation, optimization, output=output, market_data=market)
    first = _hashes(output)
    second_manifest = run(validation, optimization, output=output, market_data=market)
    assert first == _hashes(output)
    assert first_manifest == second_manifest
    assert before == (hash_tree(validation), hash_tree(optimization))
    assert first_manifest["status"] == "PHASE_M5_OVEREXTENSION_SESSION_CANDIDATE_COMPLETE"
    for scope in ("T2", "T3", "COMBINED"):
        assert {path.name for path in (output / scope).iterdir()} == set(FILES)


def test_true_oos_rejection_before_output(tmp_path: Path) -> None:
    validation, optimization, market = _fixture(tmp_path)
    market["USDRUBF"] = market["USDRUBF"].set_axis(
        pd.date_range("2025-01-01", periods=len(market["USDRUBF"]), freq="5min", tz="UTC"))
    output = tmp_path / "output"
    with pytest.raises(ValueError, match="TRUE_OOS"):
        run(validation, optimization, output=output, market_data=market)
    assert not output.exists()


def test_session_boundaries_no_parameter_mutation_and_frozen_identity(tmp_path: Path) -> None:
    validation, optimization, market = _fixture(tmp_path)
    output = tmp_path / "output"
    before = json.loads((optimization / "T2/candidate_registry.json").read_text())
    manifest = run(validation, optimization, output=output, market_data=market)
    comparison = pd.read_csv(output / "T2/baseline_vs_candidate.csv")
    # Fixture entries are 18:25, 18:50, 01:50 and 01:55 UTC: none are eligible.
    assert comparison.query("variant == 'SESSION_CANDIDATE'").trades.iloc[0] == 0
    assert json.loads((optimization / "T2/candidate_registry.json").read_text()) == before
    assert manifest["parameter_change"] is False
    registry = optimization / "T2/candidate_registry.json"
    registry.write_text(json.dumps({"candidate_id": "mutated"}))
    with pytest.raises(ValueError, match="CANDIDATE_IDENTITY_MISMATCH:T2"):
        run(validation, optimization, output=tmp_path / "other", market_data=market)


def test_session_exactly_includes_1000_and_excludes_1700(tmp_path: Path) -> None:
    validation, optimization, market = _fixture(tmp_path)
    ledger = validation / "T2/trades.csv"
    frame = pd.read_csv(ledger).iloc[:2].copy()
    # Existing UTC project offset is used without conversion.
    frame.loc[0, ["entry_time", "exit_time"]] = ["2023-01-03T10:00:00+00:00", "2023-01-03T10:20:00+00:00"]
    frame.loc[1, ["entry_time", "exit_time"]] = ["2023-01-03T17:00:00+00:00", "2023-01-03T17:20:00+00:00"]
    frame.loc[:, "entry_price"] = [float(market["USDRUBF"].iloc[407].Close), float(market["CNYRUBF"].iloc[491].Close)]
    frame.loc[:, "initial_stop"] = frame.entry_price - 1
    frame.to_csv(ledger, index=False)
    # Keep the second strategy valid and isolate this boundary assertion to T2 output.
    output = tmp_path / "output"
    run(validation, optimization, output=output, market_data=market)
    result = pd.read_csv(output / "T2/baseline_vs_candidate.csv")
    assert result.query("variant == 'SESSION_CANDIDATE'").trades.iloc[0] == 1
