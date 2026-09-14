import json
from hashlib import sha256
from pathlib import Path

import pandas as pd

from bbw_system.data_pipeline import file_sha256
from bbw_system.normalization import TIMEFRAMES, normalize_frame, run_normalization
from bbw_system.normalization_cli import main
from bbw_system.temporal_alignment import aggregate_m1


METADATA = Path("bbw_system/config/instruments/cnyrubf.yaml")


def _freeze(tmp_path: Path) -> tuple[Path, list[Path]]:
    root, raw_root = tmp_path / "freeze", tmp_path / "raw"
    (root / "evidence").mkdir(parents=True)
    raw_root.mkdir()
    minute = pd.DataFrame({
        "timestamp": pd.date_range("2024-01-03 09:00", periods=60, freq="min"),
        "open": range(60), "high": range(60), "low": range(60),
        "close": range(60), "volume": [1] * 60,
    })
    frames = {"M1": minute}
    for timeframe in TIMEFRAMES[1:-1]:
        frames[timeframe] = aggregate_m1(minute, timeframe, "START").drop(columns="source_bar_count")
    frames["D1"] = minute.assign(timestamp=minute.timestamp.dt.normalize()).groupby("timestamp").agg(
        open=("open", "first"), high=("high", "max"), low=("low", "min"),
        close=("close", "last"), volume=("volume", "sum")).reset_index()
    records, paths = {"CNYRUBF": {}}, []
    for timeframe, frame in frames.items():
        path = raw_root / f"CNYRUBF_{timeframe}.csv"
        frame.to_csv(path, index=False, lineterminator="\n")
        paths.append(path)
        records["CNYRUBF"][timeframe] = [{"source_path": str(path.resolve()),
            "source_sha256": file_sha256(path)}]
    (root / "evidence" / "FREEZE_MANIFEST.json").write_text(
        json.dumps({"instruments": records}), encoding="utf-8")
    return root, paths


def _tree_hashes(root: Path) -> dict[str, str]:
    return {path.name: sha256(path.read_bytes()).hexdigest() for path in root.iterdir()}


def test_deterministic_output_hash_reproducibility_and_no_raw_mutation(tmp_path):
    freeze, sources = _freeze(tmp_path)
    before = {path: file_sha256(path) for path in sources}
    first, second = tmp_path / "first", tmp_path / "second"
    run_normalization(freeze, first, METADATA)
    run_normalization(freeze, second, METADATA)
    assert _tree_hashes(first) == _tree_hashes(second)
    assert before == {path: file_sha256(path) for path in sources}
    manifest = json.loads((first / "NORMALIZED_MANIFEST.json").read_text())
    for timeframe in TIMEFRAMES:
        assert manifest["timeframes"][timeframe]["sha256"] == file_sha256(first / f"{timeframe}.csv")


def test_timestamp_and_ohlcv_preservation(tmp_path):
    freeze, sources = _freeze(tmp_path)
    output = tmp_path / "normalized"
    run_normalization(freeze, output, METADATA)
    source = pd.read_csv(next(path for path in sources if path.name == "CNYRUBF_M1.csv"))
    normalized = pd.read_csv(output / "M1.csv")
    pd.testing.assert_frame_equal(normalized, source, check_dtype=False)


def test_gap_detection_does_not_fill():
    raw = pd.DataFrame({"timestamp": ["2024-01-03 09:00", "2024-01-03 09:02"],
        "open": [1, 2], "high": [1, 2], "low": [1, 2], "close": [1, 2], "volume": [1, 1]})
    normalized, report = normalize_frame(raw, "M1")
    assert len(normalized) == 2
    assert report["gap_count"] == 1
    assert report["gaps"][0]["elapsed_seconds"] == 120


def test_invalid_ohlc_and_duplicate_rows_are_rejected():
    raw = pd.DataFrame({"timestamp": ["2024-01-03 09:00", "2024-01-03 09:01", "2024-01-03 09:00"],
        "open": [1, 3, 1], "high": [1, 2, 1], "low": [1, 1, 1], "close": [1, 3, 1], "volume": [1, 1, 1]})
    normalized, report = normalize_frame(raw, "M1")
    assert len(normalized) == 1
    assert report["invalid_ohlc_rows"] == 1
    assert report["duplicate_rows"] == 1
    assert report["rejected_rows"] == 2


def test_cli_writes_required_dataset_and_reports(tmp_path):
    freeze, _ = _freeze(tmp_path)
    output = tmp_path / "data" / "normalized" / "CNYRUBF"
    assert main(["--freeze-root", str(freeze), "--output-root", str(output)]) == 0
    assert {path.name for path in output.iterdir()} == {
        *(f"{timeframe}.csv" for timeframe in TIMEFRAMES),
        "NORMALIZATION_REPORT.md", "NORMALIZED_MANIFEST.json"}
