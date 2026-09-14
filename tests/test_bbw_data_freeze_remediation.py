import json
from pathlib import Path

import pandas as pd
import pytest

from bbw_system.data_freeze import (FINAM_TIMEFRAMES, IdentityError, classify,
    load_passports, raw_audit, resolve_identity, run_freeze)
from bbw_system.data_pipeline import read_source


HEADER = "<TICKER>;<PER>;<DATE>;<TIME>;<OPEN>;<HIGH>;<LOW>;<CLOSE>;<VOL>\n"


def passports(root: Path, *, metadata: bool = False) -> Path:
    root.mkdir()
    data = {"symbol": "CNYRUBF", "aliases": ["CNY"],
        "source_timezone": {"value": "UTC" if metadata else None},
        "exchange_timezone": {"value": "UTC" if metadata else None},
        "session": {"value": {"start": "00:00", "end": "23:59"} if metadata else None},
        "breaks": {"value": []}, "series_type": {"value": "unknown", "verified": False}}
    (root / "cnyrubf.yaml").write_text(json.dumps(data))
    return root


def finam(path: Path, ticker="CNYRUBF", per="60", dates=("20230103", "20230103"),
          times=("100000", "110000")) -> Path:
    rows = [f"{ticker};{per};{d};{t};10;11;9;10.5;5" for d, t in zip(dates, times)]
    path.write_text(HEADER + "\n".join(rows) + "\n")
    return path


def test_cny_filename_alias_and_finam_identity(tmp_path):
    docs = load_passports(passports(tmp_path / "passports"))
    path = finam(tmp_path / "CNY_H1_2023_Q1.csv")
    raw, info = read_source(path)
    identity = resolve_identity(path, raw, info, docs)
    assert classify(path, docs) == ("CNYRUBF", "H1")
    assert identity["detected_symbol"] == "CNYRUBF"
    assert identity["detected_timeframe"] == "H1"
    assert identity["symbol_evidence"] == "finam_ticker_column"
    assert identity["timeframe_evidence"] == "finam_per_column"


@pytest.mark.parametrize(("per", "timeframe"), FINAM_TIMEFRAMES.items())
def test_all_finam_per_mappings(tmp_path, per, timeframe):
    docs = load_passports(passports(tmp_path / "passports"))
    path = finam(tmp_path / "source.csv", per=per, dates=("20230103",), times=("100000",))
    raw, info = read_source(path)
    assert resolve_identity(path, raw, info, docs)["detected_timeframe"] == timeframe


def test_content_identity_supplies_identity_for_weak_filename(tmp_path):
    docs = load_passports(passports(tmp_path / "passports"))
    path = finam(tmp_path / "quarter_one.csv")
    raw, info = read_source(path)
    assert resolve_identity(path, raw, info, docs)["detected_symbol"] == "CNYRUBF"


@pytest.mark.parametrize(("name", "ticker", "per", "reason"), [
    ("CNY_H1.csv", "USDRUBF", "60", "IDENTITY_MISMATCH"),
    ("CNY_H1.csv", "CNYRUBF", "5", "IDENTITY_MISMATCH"),
])
def test_filename_source_contradiction_is_explicit(tmp_path, name, ticker, per, reason):
    docs = load_passports(passports(tmp_path / "passports"))
    raw, info = read_source(finam(tmp_path / name, ticker=ticker, per=per))
    with pytest.raises(IdentityError, match=reason):
        resolve_identity(tmp_path / name, raw, info, docs)


def test_multiple_tickers_and_periods_fail_explicitly(tmp_path):
    docs = load_passports(passports(tmp_path / "passports"))
    path = tmp_path / "source.csv"
    path.write_text(HEADER + "CNYRUBF;60;20230103;100000;10;11;9;10;1\nBR;5;20230103;110000;10;11;9;10;1\n")
    raw, info = read_source(path)
    with pytest.raises(IdentityError, match="MULTIPLE_SOURCE_TICKERS"):
        resolve_identity(path, raw, info, docs)
    raw["<TICKER>"] = "CNYRUBF"
    with pytest.raises(IdentityError, match="MULTIPLE_SOURCE_PERIODS"):
        resolve_identity(path, raw, info, docs)


def test_raw_audit_and_readiness_do_not_require_metadata(tmp_path):
    data = tmp_path / "raw"; data.mkdir(); docs = passports(tmp_path / "passports")
    finam(data / "CNY_H1_2023_Q1.csv")
    out = tmp_path / "outside_git"; assert run_freeze(data, out, docs, ["CNYRUBF"]) == 0
    manifest = json.loads((out / "evidence" / "FREEZE_MANIFEST.json").read_text())
    item = manifest["instruments"]["CNYRUBF"]["H1"][0]
    assert item["raw_parse_status"] == "PASS"
    assert item["normalization_status"] == "PENDING_METADATA"
    assert item["normalization_block_reason"] == ["source_timezone", "exchange_timezone", "session_start", "session_end"]
    assert item["synthetic_h4_status"] == "PENDING_METADATA"
    readiness = (out / "evidence" / "DATA_READINESS.md").read_text()
    assert "READY_FOR_METADATA_FREEZE" in readiness and "PENDING_METADATA" in readiness
    assert all("<OPEN>;<HIGH>;<LOW>;<CLOSE>" not in path.read_text()
               for path in (out / "evidence").iterdir())
    assert not list((out / "large_local_output" / "normalized").iterdir())


def test_scope_excludes_other_instruments_from_gate(tmp_path):
    data = tmp_path / "raw"; data.mkdir(); docs = passports(tmp_path / "passports")
    finam(data / "CNY_H1.csv")
    finam(data / "Si_H1.csv", ticker="Si")
    out = tmp_path / "out"; run_freeze(data, out, docs, ["CNYRUBF"])
    readiness = (out / "evidence" / "DATA_READINESS.md").read_text()
    assert "CNYRUBF" in readiness and "IMOEXF" not in readiness
    inventory = (out / "evidence" / "DATA_INVENTORY.md").read_text()
    assert "Si_H1.csv" in inventory and "NOT_TARGET" in inventory


def test_multifile_aggregate_coverage_is_deterministic(tmp_path):
    data = tmp_path / "raw"; data.mkdir(); docs = passports(tmp_path / "passports")
    finam(data / "CNY_H1_2023_Q1.csv", dates=("20230103", "20230103"), times=("100000", "110000"))
    finam(data / "CNY_H1_2023_Q2.csv", dates=("20230403", "20230403"), times=("100000", "110000"))
    out = tmp_path / "out"; run_freeze(data, out, docs, ["CNYRUBF"])
    first = (out / "evidence" / "FREEZE_MANIFEST.json").read_bytes()
    run_freeze(data, out, docs, ["CNYRUBF"])
    assert first == (out / "evidence" / "FREEZE_MANIFEST.json").read_bytes()
    row = pd.read_csv(out / "evidence" / "DATA_COVERAGE.csv").iloc[0]
    assert (row.source_files, row.total_rows, row.overlapping_file_ranges, row.gaps_between_file_ranges) == (2, 4, 0, 1)


def test_no_strategy_or_performance_module_is_imported():
    source = Path("src/bbw_system/data_freeze.py").read_text()
    assert all(token not in source for token in (".strategy import", ".engine import", ".metrics import", "BBW", "WinRate", "profit_factor"))
