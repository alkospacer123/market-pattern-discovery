from __future__ import annotations

import hashlib
import json
from pathlib import Path

import pandas as pd
import pytest

from TradingSystemLab.multitimeframe.phase73 import hash_tree
from TradingSystemLab.timeframe_analysis.m5_holding_time import CANDIDATES, DEVELOPMENT, run


def _sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _inputs(root: Path) -> tuple[Path, Path, Path]:
    diagnostics, validation, optimization = root / "diagnostics", root / "validation", root / "optimization"
    diagnostics.mkdir(parents=True)
    optimization.mkdir()
    rows = [
        {"trade_id": "a", "instrument": "USDRUBF", "direction": "LONG", "entry_time": "2023-01-02T09:00:00+03:00", "exit_time": "2023-01-02T09:05:00+03:00", "net_R": -1.0, "MAE_R": 1.0, "MFE_R": .1},
        {"trade_id": "b", "instrument": "CNYRUBF", "direction": "SHORT", "entry_time": "2024-07-01T10:00:00+03:00", "exit_time": "2024-07-01T10:30:00+03:00", "net_R": 2.0, "MAE_R": .2, "MFE_R": 2.4},
        {"trade_id": "c", "instrument": "CNYRUBF", "direction": "LONG", "entry_time": "2024-07-01T17:00:00+03:00", "exit_time": "2024-07-01T19:01:00+03:00", "net_R": .5, "MAE_R": .4, "MFE_R": 1.1},
    ]
    hashes = {}
    for strategy in CANDIDATES:
        ledger = validation / strategy / "trades.csv"
        ledger.parent.mkdir(parents=True)
        pd.DataFrame(rows).to_csv(ledger, index=False)
        hashes[str(ledger)] = _sha(ledger)
    manifest = {"phase": "M5_FULL_DIAGNOSTIC", "candidate_identities": CANDIDATES,
                "development_period": DEVELOPMENT, "true_oos_cutoff": "2025-01-01",
                "true_oos_access": False, "source_artifact_hashes": hashes}
    (diagnostics / "manifest.json").write_text(json.dumps(manifest), encoding="utf-8")
    return diagnostics, validation, optimization


def test_holding_analysis_is_complete_read_only_and_deterministic(tmp_path: Path) -> None:
    diagnostics, validation, optimization = _inputs(tmp_path)
    before = (hash_tree(diagnostics), hash_tree(validation), hash_tree(optimization))
    output = tmp_path / "output"
    manifest = run(diagnostics, validation, optimization, output)
    first = hash_tree(output)
    run(diagnostics, validation, optimization, output)
    assert first == hash_tree(output)
    assert before == (hash_tree(diagnostics), hash_tree(validation), hash_tree(optimization))
    assert manifest["status"] == "PHASE_M5_HOLDING_TIME_ANALYSIS_COMPLETE"
    assert manifest["diagnostic_only"] and manifest["deterministic"] and manifest["true_oos_blocked"]
    assert not manifest["optimization"] and not manifest["strategy_changes"]
    required = {"holding_distribution.csv", "winner_loser_duration.csv", "mae_mfe_by_duration.csv",
                "time_to_profit.csv", "time_to_mae.csv", "instrument_report.csv",
                "session_report.csv", "direction_report.csv"}
    for strategy in CANDIDATES:
        assert {path.name for path in (output / strategy).iterdir()} == required
        assert len(pd.read_csv(output / strategy / "holding_distribution.csv")) == 6
        assert set(pd.read_csv(output / strategy / "time_to_profit.csv").status) == {"DATA_UNAVAILABLE"}
    comparison = pd.read_csv(output / "comparison.csv")
    assert set(comparison.scope) == {"T2", "T3", "portfolio"}
    assert len(comparison) == 18


def test_true_oos_is_rejected_before_output(tmp_path: Path) -> None:
    diagnostics, validation, optimization = _inputs(tmp_path)
    ledger = validation / "T2" / "trades.csv"
    frame = pd.read_csv(ledger)
    frame.loc[0, "exit_time"] = "2025-01-01T00:00:00+03:00"
    frame.to_csv(ledger, index=False)
    manifest_path = diagnostics / "manifest.json"
    manifest = json.loads(manifest_path.read_text())
    manifest["source_artifact_hashes"][str(ledger)] = _sha(ledger)
    manifest_path.write_text(json.dumps(manifest), encoding="utf-8")
    output = tmp_path / "output"
    with pytest.raises(ValueError, match="TRUE_OOS_TRADE_REJECTED"):
        run(diagnostics, validation, optimization, output)
    assert not output.exists()
