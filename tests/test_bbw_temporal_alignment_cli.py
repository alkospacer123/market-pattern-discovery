import json
from pathlib import Path

import pandas as pd

from bbw_system.data_pipeline import file_sha256
from bbw_system.temporal_alignment import aggregate_m1
from bbw_system.temporal_alignment_cli import main


def _freeze(tmp_path: Path, *, empty: bool = False) -> Path:
    root = tmp_path / "freeze"
    evidence = root / "evidence"
    raw_root = tmp_path / "raw"
    evidence.mkdir(parents=True)
    raw_root.mkdir()
    minute = pd.DataFrame({
        "timestamp": pd.date_range("2024-01-03 09:00", periods=0 if empty else 60, freq="min"),
        "open": range(0 if empty else 60), "high": range(0 if empty else 60),
        "low": range(0 if empty else 60), "close": range(0 if empty else 60),
        "volume": [1] * (0 if empty else 60),
    })
    frames = {"M1": minute}
    for timeframe in ("M5", "M15", "M30", "H1"):
        frames[timeframe] = aggregate_m1(minute, timeframe, "START").drop(columns="source_bar_count") if not empty else minute
    frames["D1"] = (minute.assign(timestamp=minute.timestamp.dt.normalize()).groupby("timestamp").agg(
        open=("open", "first"), high=("high", "max"), low=("low", "min"),
        close=("close", "last"), volume=("volume", "sum")).reset_index() if not empty else minute)
    instruments = {"CNYRUBF": {}}
    for timeframe, frame in frames.items():
        path = raw_root / f"CNYRUBF_{timeframe}.csv"
        frame.to_csv(path, index=False, lineterminator="\n")
        instruments["CNYRUBF"][timeframe] = [{"source_path": str(path.resolve()),
            "source_sha256": file_sha256(path)}]
    (evidence / "FREEZE_MANIFEST.json").write_text(
        json.dumps({"instruments": instruments}), encoding="utf-8")
    return root


def _args(freeze: Path, output: Path) -> list[str]:
    return ["--freeze-root", str(freeze), "--output-root", str(output), "--symbol", "CNYRUBF"]


def test_cli_execution_and_deterministic_evidence(tmp_path):
    freeze, output = _freeze(tmp_path), tmp_path / "output"
    assert main(_args(freeze, output)) == 0
    expected = {"TEMPORAL_ALIGNMENT.json", "TEMPORAL_ALIGNMENT_REPORT.md", "MTF_ALIGNMENT.csv",
                "SESSION_ALIGNMENT.csv", "READINESS.md"}
    first = {name: (output / name).read_bytes() for name in expected}
    assert main(_args(freeze, output)) == 0
    assert first == {name: (output / name).read_bytes() for name in expected}
    assert json.loads(first["TEMPORAL_ALIGNMENT.json"])["timestamp_alignment"]["timestamp_semantics"] == "START"


def test_cli_missing_freeze_bundle_fails_closed(tmp_path, capsys):
    assert main(_args(tmp_path / "missing", tmp_path / "output")) == 2
    assert "failed closed" in capsys.readouterr().err


def test_cli_hash_mismatch_fails_before_output(tmp_path):
    freeze, output = _freeze(tmp_path), tmp_path / "output"
    manifest = json.loads((freeze / "evidence" / "FREEZE_MANIFEST.json").read_text())
    manifest["instruments"]["CNYRUBF"]["M1"][0]["source_sha256"] = "0" * 64
    (freeze / "evidence" / "FREEZE_MANIFEST.json").write_text(json.dumps(manifest))
    assert main(_args(freeze, output)) == 2
    assert not output.exists()


def test_cli_empty_data_fails_closed(tmp_path):
    freeze, output = _freeze(tmp_path, empty=True), tmp_path / "output"
    assert main(_args(freeze, output)) == 2
    assert not output.exists()
