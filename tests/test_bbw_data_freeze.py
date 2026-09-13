import json
from pathlib import Path

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
