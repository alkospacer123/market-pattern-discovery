from __future__ import annotations

import hashlib
import json
from pathlib import Path

import pandas as pd
import pytest

from TradingSystemLab.multitimeframe.phase73 import hash_tree
from TradingSystemLab.timeframe_analysis.m5_candidates import CANDIDATES, DEVELOPMENT, run


def _sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _inputs(root: Path) -> tuple[Path, Path]:
    diagnostics, validation = root / "diagnostics", root / "validation"
    diagnostics.mkdir(parents=True)
    rows = [
        {"trade_id": "a", "instrument": "USDRUBF", "direction": "LONG",
         "entry_time": "2023-01-02T09:00:00+03:00", "exit_time": "2023-01-02T09:10:00+03:00", "net_R": -1.0},
        {"trade_id": "b", "instrument": "CNYRUBF", "direction": "SHORT",
         "entry_time": "2024-07-01T10:00:00+03:00", "exit_time": "2024-07-01T10:30:00+03:00", "net_R": 2.0},
        {"trade_id": "c", "instrument": "CNYRUBF", "direction": "LONG",
         "entry_time": "2024-07-01T17:00:00+03:00", "exit_time": "2024-07-01T19:01:00+03:00", "net_R": .5},
    ]
    hashes = {}
    for strategy in CANDIDATES:
        target = validation / strategy / "trades.csv"
        target.parent.mkdir(parents=True)
        pd.DataFrame(rows).to_csv(target, index=False)
        hashes[str(target)] = _sha(target)
    manifest = {"phase": "M5_FULL_DIAGNOSTIC", "candidate_identities": CANDIDATES,
                "development_period": DEVELOPMENT, "true_oos_cutoff": "2025-01-01",
                "true_oos_access": False, "source_artifact_hashes": hashes}
    (diagnostics / "manifest.json").write_text(json.dumps(manifest), encoding="utf-8")
    return diagnostics, validation


def test_candidate_analysis_is_complete_read_only_and_deterministic(tmp_path: Path) -> None:
    diagnostics, validation = _inputs(tmp_path)
    source_before = (hash_tree(diagnostics), hash_tree(validation))
    output = tmp_path / "output"
    manifest = run(diagnostics, validation, output)
    first = hash_tree(output)
    run(diagnostics, validation, output)
    assert first == hash_tree(output)
    assert source_before == (hash_tree(diagnostics), hash_tree(validation))
    assert manifest["status"] == "PHASE_M5_CANDIDATE_ANALYSIS_COMPLETE"
    assert manifest["diagnostic_only"] and manifest["true_oos_blocked"] and manifest["deterministic"]
    assert not manifest["optimization"] and not manifest["strategy_changes"] and not manifest["parameter_changes"]
    required = {"session_filter_analysis.csv", "holding_time_analysis.csv",
                "instrument_session_analysis.csv", "time_analysis.csv"}
    for strategy in CANDIDATES:
        assert {p.name for p in (output / strategy).iterdir()} == required
        assert len(pd.read_csv(output / strategy / "session_filter_analysis.csv")) == 3
        assert len(pd.read_csv(output / strategy / "holding_time_analysis.csv")) == 5
        assert len(pd.read_csv(output / strategy / "instrument_session_analysis.csv")) == 6
    comparison = pd.read_csv(output / "comparison.csv")
    assert set(comparison.scope) == {"T2", "T3", "portfolio"}


def test_tampering_identity_and_true_oos_are_rejected_before_output(tmp_path: Path) -> None:
    diagnostics, validation = _inputs(tmp_path)
    output = tmp_path / "output"
    ledger = validation / "T2" / "trades.csv"
    ledger.write_text(ledger.read_text(encoding="utf-8") + "\n", encoding="utf-8")
    with pytest.raises(ValueError, match="SOURCE_HASH_MISMATCH"):
        run(diagnostics, validation, output)
    assert not output.exists()

    diagnostics, validation = _inputs(tmp_path / "second")
    path = validation / "T3" / "trades.csv"
    frame = pd.read_csv(path)
    frame.loc[0, "exit_time"] = "2025-01-01T00:00:00+03:00"
    frame.to_csv(path, index=False)
    diagnostic_manifest = json.loads((diagnostics / "manifest.json").read_text())
    diagnostic_manifest["source_artifact_hashes"][str(path)] = _sha(path)
    (diagnostics / "manifest.json").write_text(json.dumps(diagnostic_manifest), encoding="utf-8")
    with pytest.raises(ValueError, match="TRUE_OOS_TRADE_REJECTED"):
        run(diagnostics, validation, tmp_path / "second_output")
