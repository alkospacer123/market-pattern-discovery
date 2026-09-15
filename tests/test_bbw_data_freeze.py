import json
from hashlib import sha256
from pathlib import Path

import pandas as pd
import pytest

from bbw_system.data_cli import main
from bbw_system.data_freeze import EVIDENCE_FILES, portable_identifier, run_freeze


def passport(root: Path):
    root.mkdir()
    (root / "br.yaml").write_text(json.dumps({"symbol":"BR", "aliases":["BRENT"],
        "source_timezone":{"value":"UTC"}, "exchange_timezone":{"value":"UTC"},
        "session":{"value":{"start":"00:00","end":"23:59"}}, "breaks":{"value":[]},
        "series_type":{"value":"unknown","verified":False}}))


def test_freeze_is_deterministic_and_does_not_copy_raw(tmp_path):
    data, passports = tmp_path/"source", tmp_path/"passports"; data.mkdir(); passport(passports)
    (data/"BRENT_H1.csv").write_text("timestamp,open,high,low,close,volume\n2024-01-08 00:00,10,11,9,10,1\n")
    out = tmp_path/"out"; run_freeze(data,out,passports)
    first = {p.name:p.read_bytes() for p in (out/"evidence").iterdir()}
    run_freeze(data,out,passports)
    assert first == {p.name:p.read_bytes() for p in (out/"evidence").iterdir()}
    assert set(first) == set(EVIDENCE_FILES)
    assert not any("open,high,low,close" in p.read_text() for p in (out/"evidence").iterdir())


def test_bad_file_does_not_abort_and_portable_id_is_stable(tmp_path):
    data, passports = tmp_path/"data", tmp_path/"passports"; (data/"nested").mkdir(parents=True); passport(passports)
    (data/"BR_H1.csv").write_text("not,a,market,file\n1,2,3,4\n")
    (data/"nested"/"notes.txt").write_text("unsupported")
    out=tmp_path/"out"; assert run_freeze(data,out,passports) == 0
    text=(out/"evidence"/"DATA_INVENTORY.md").read_text()
    assert "PARSE_FAILED" in text and "nested/notes.txt" in text
    assert portable_identifier(data/"nested"/"notes.txt",data)=="nested/notes.txt"


def test_freeze_date_window_is_inclusive_and_excludes_true_oos(tmp_path):
    data, passports = tmp_path/"source", tmp_path/"passports"; data.mkdir(); passport(passports)
    source = data/"BRENT_H1.csv"
    source.write_text("timestamp,open,high,low,close,volume\n"
        "2023-01-02 23:00,10,11,9,10,1\n2023-01-03 00:00,11,12,10,11,2\n"
        "2023-01-03 01:00,12,13,11,12,3\n2024-12-31 22:00,13,14,12,13,4\n"
        "2024-12-31 23:00,14,15,13,14,5\n2025-01-01 00:00,15,16,14,15,6\n")

    out = tmp_path/"train"
    assert run_freeze(data, out, passports, start_date="2023-01-03", end_date="2024-12-31") == 0

    normalized_path = next((out/"large_local_output"/"normalized").glob("*.csv"))
    normalized = pd.read_csv(normalized_path)
    assert list(normalized["source_timestamp"]) == ["2023-01-03 00:00:00", "2023-01-03 01:00:00",
        "2024-12-31 22:00:00", "2024-12-31 23:00:00"]
    assert not normalized["source_timestamp"].str.startswith("2025-").any()
    manifest = json.loads((out/"evidence"/"FREEZE_MANIFEST.json").read_text())
    assert manifest["scope"]["date_window"] == {"start_date":"2023-01-03", "end_date":"2024-12-31",
        "boundaries":"inclusive", "timestamp_basis":"raw_source_timestamp"}
    item = manifest["instruments"]["BR"]["H1"][0]
    assert item["raw_audit"]["row_count"] == 4
    assert item["source_sha256"] == sha256(source.read_bytes()).hexdigest()


def test_windowed_freeze_is_deterministic_and_source_is_immutable(tmp_path):
    data, passports = tmp_path/"source", tmp_path/"passports"; data.mkdir(); passport(passports)
    source = data/"BRENT_H1.csv"
    source.write_text("timestamp,open,high,low,close,volume\n2024-01-01 00:00,10,11,9,10,1\n2025-01-01 00:00,20,21,19,20,2\n")
    original = source.read_bytes()
    out = tmp_path/"out"
    run_freeze(data, out, passports, start_date="2024-01-01", end_date="2024-12-31")
    first = {p.relative_to(out): p.read_bytes() for p in out.rglob("*") if p.is_file()}
    run_freeze(data, out, passports, start_date="2024-01-01", end_date="2024-12-31")
    assert first == {p.relative_to(out): p.read_bytes() for p in out.rglob("*") if p.is_file()}
    assert source.read_bytes() == original


def test_omitted_date_arguments_preserve_existing_manifest_shape(tmp_path):
    data, passports = tmp_path/"source", tmp_path/"passports"; data.mkdir(); passport(passports)
    (data/"BRENT_H1.csv").write_text("timestamp,open,high,low,close,volume\n2025-01-01 00:00,10,11,9,10,1\n")
    out = tmp_path/"out"; run_freeze(data, out, passports)
    manifest = json.loads((out/"evidence"/"FREEZE_MANIFEST.json").read_text())
    assert manifest["scope"] == {"symbols": ["CNYRUBF", "IMOEXF", "GLDRUBF", "BR", "GOLD"]}
    assert manifest["instruments"]["BR"]["H1"][0]["raw_audit"]["row_count"] == 1


def test_freeze_cli_accepts_date_window_and_rejects_invalid_ranges(tmp_path):
    data, passports = tmp_path/"source", tmp_path/"passports"; data.mkdir(); passport(passports)
    (data/"BRENT_H1.csv").write_text("timestamp,open,high,low,close,volume\n2024-01-01,10,11,9,10,1\n")
    assert main(["freeze", "--data-root", str(data), "--output-root", str(tmp_path/"out"),
        "--passport-root", str(passports), "--start-date", "2024-01-01", "--end-date", "2024-12-31"]) == 0
    with pytest.raises(ValueError, match="on or before"):
        run_freeze(data, tmp_path/"bad", passports, start_date="2025-01-01", end_date="2024-12-31")
