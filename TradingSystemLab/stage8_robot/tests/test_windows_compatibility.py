import csv
import hashlib
import json
import subprocess
import sys
from pathlib import Path

import pytest

from TradingSystemLab.authority_hashing import canonical_authority_sha256


ROOT = Path(__file__).resolve().parents[3]
STAGE7 = ROOT / "TradingSystemLab/results/post_v3_analysis/stage7_production_specification_freeze"
STAGE8 = ROOT / "TradingSystemLab/stage8_robot"


def _simulate_windows_checkout(raw):
    canonical_lf = raw.replace(b"\r\n", b"\n")
    if b"\r" in canonical_lf:
        raise AssertionError("TEST_SOURCE_CONTAINS_LONE_CR")
    return canonical_lf.replace(b"\n", b"\r\n")


@pytest.mark.parametrize("suffix,payload", [
    (".py", b"value = 1\nprint(value)\n"),
    (".json", b'{\n  "value": 1\n}\n'),
    (".csv", b"name,value\nexample,1\n"),
])
def test_authority_hash_accepts_only_lf_crlf_equivalence(tmp_path, suffix, payload):
    expected = hashlib.sha256(payload).hexdigest()
    lf = tmp_path / f"lf{suffix}"; lf.write_bytes(payload)
    crlf = tmp_path / f"crlf{suffix}"; crlf.write_bytes(payload.replace(b"\n", b"\r\n"))
    changed = tmp_path / f"changed{suffix}"; changed.write_bytes(payload.replace(b"1", b"2", 1))
    whitespace = tmp_path / f"space{suffix}"; whitespace.write_bytes(payload.replace(b"\n", b" \n", 1))
    assert canonical_authority_sha256(lf) == canonical_authority_sha256(crlf) == expected
    assert canonical_authority_sha256(changed) != expected
    assert canonical_authority_sha256(whitespace) != expected
    crlf.write_bytes(payload.replace(b"\n", b"\r", 1))
    with pytest.raises(ValueError, match="AUTHORITY_TEXT_LONE_CR"):
        canonical_authority_sha256(crlf)


@pytest.mark.parametrize("source_newline", [b"\n", b"\r\n"])
def test_simulated_windows_checkout_is_independent_of_source_newlines(tmp_path, source_newline):
    canonical_lf = b"value = 1\nprint(value)\n"
    expected = hashlib.sha256(canonical_lf).hexdigest()
    source = tmp_path / "source.py"
    source.write_bytes(canonical_lf.replace(b"\n", source_newline))

    assert canonical_authority_sha256(source) == expected
    windows_checkout = tmp_path / "windows.py"
    windows_checkout.write_bytes(_simulate_windows_checkout(source.read_bytes()))
    assert b"\r\r\n" not in windows_checkout.read_bytes()
    assert canonical_authority_sha256(windows_checkout) == expected


def test_simulated_windows_checkout_rejects_lone_cr():
    with pytest.raises(AssertionError, match="TEST_SOURCE_CONTAINS_LONE_CR"):
        _simulate_windows_checkout(b"value = 1\rprint(value)\n")


@pytest.mark.parametrize("relative,expected", [
    ("TradingSystemLab/strategies/trend/T3_MTF_Trend.py", "840dd3b2cda43fa00259445cd0a22ace6d82e677f4c793028ccc8126f9ad9a8c"),
    ("TradingSystemLab/results/post_v3_analysis/stage5_structural_validation/stage5_trail1_execution.py", "d1d8ac2eeea9095becd6f74295e4a540d02ee0494237af5f16f6d66a487f221b"),
    ("TradingSystemLab/results/post_v3_analysis/stage6_7_n4_full_four_case_test/four_case_registry.csv", "e1f5edbff005ce17fcaa73c71837db1b3906bdd3d92d1f249788e80c725c34a2"),
    ("TradingSystemLab/results/post_v3_analysis/stage6_7_n4_full_four_case_test/independent_audit_result.json", "706e7198ef39788bc3a3d33474583411d76d4d14480fad67357557feea33a684"),
])
def test_current_frozen_authorities_keep_literal_lf_hashes(relative, expected, tmp_path):
    source = ROOT / relative
    assert canonical_authority_sha256(source) == expected
    windows_checkout = tmp_path / source.name
    raw = source.read_bytes()
    windows_checkout.write_bytes(_simulate_windows_checkout(raw))
    assert canonical_authority_sha256(windows_checkout) == expected


def test_check_only_audits_do_not_write_results():
    commands = [
        [sys.executable, str(STAGE7 / "audit_production_specification.py"), "--check-only"],
        [sys.executable, str(STAGE8 / "audit_stage8.py"), "--check-only"],
    ]
    artifacts = [STAGE7 / "independent_audit_result.json", STAGE8 / "independent_audit_result.json"]
    before = [path.read_bytes() for path in artifacts]
    for command in commands:
        completed = subprocess.run(command, cwd=ROOT, capture_output=True, text=True)
        assert completed.returncode == 0, completed.stdout + completed.stderr
        assert json.loads(completed.stdout)["status"] == "PASS"
    assert [path.read_bytes() for path in artifacts] == before


def test_stage7_failed_check_only_retains_exit_code_and_writes_nothing(tmp_path):
    completed = subprocess.run(
        [sys.executable, str(STAGE7 / "audit_production_specification.py"),
         "--check-only", "--target", str(tmp_path)],
        cwd=ROOT, capture_output=True, text=True,
    )
    assert completed.returncode != 0
    assert json.loads(completed.stdout)["status"] == "FAIL"
    assert list(tmp_path.iterdir()) == []


def test_preflight_is_read_only(tmp_path):
    artifacts = [STAGE7 / "independent_audit_result.json", STAGE8 / "independent_audit_result.json"]
    before = [path.read_bytes() for path in artifacts]
    completed = subprocess.run(
        [sys.executable, str(STAGE8 / "server_preflight.py"), "--offline",
         "--state-directory", str(tmp_path / "state")],
        cwd=ROOT, capture_output=True, text=True,
    )
    assert completed.returncode == 0, completed.stdout + completed.stderr
    assert json.loads(completed.stdout)["status"] == "PASS"
    assert [path.read_bytes() for path in artifacts] == before


def test_directory_fsync_is_skipped_on_windows_and_retained_on_posix(monkeypatch, tmp_path):
    import TradingSystemLab.stage8_robot.update_real_registry as updater
    calls = []
    monkeypatch.setattr(updater.os, "open", lambda *args: calls.append(("open", args)) or 17)
    monkeypatch.setattr(updater.os, "fsync", lambda fd: calls.append(("fsync", fd)))
    monkeypatch.setattr(updater.os, "close", lambda fd: calls.append(("close", fd)))
    updater._fsync_directory(tmp_path, platform="nt")
    assert calls == []
    updater._fsync_directory(tmp_path, platform="posix")
    assert [name for name, _ in calls] == ["open", "fsync", "close"]


def test_registry_promotion_succeeds_with_windows_directory_semantics(tmp_path, monkeypatch):
    import TradingSystemLab.stage8_robot.update_real_registry as updater
    from TradingSystemLab.stage8_robot.tests.test_real_readonly_margin import real_registry_report
    report = real_registry_report()
    evidence = tmp_path / "evidence.json"; evidence.write_text(json.dumps(report))
    registry = tmp_path / "registry.csv"
    registry.write_bytes((STAGE8 / "production_instrument_registry.csv").read_bytes())
    real_fsync_directory = updater._fsync_directory
    monkeypatch.setattr(updater, "_fsync_directory", lambda path: real_fsync_directory(path, platform="nt"))
    updater.update(evidence, registry)
    with registry.open(newline="", encoding="utf-8") as stream:
        rows = list(csv.DictReader(stream))
    assert len(rows) == 4
    assert all(row["binding_status"] == "AUTHENTICATED_REAL_READONLY" for row in rows)


@pytest.mark.parametrize("field", ["trading_status", "authority"])
def test_independent_temp_reload_rejects_missing_operational_field(tmp_path, monkeypatch, field):
    import TradingSystemLab.stage8_robot.update_real_registry as updater
    from TradingSystemLab.stage8_robot.tests.test_real_readonly_margin import real_registry_report
    report = real_registry_report()
    evidence = tmp_path / "evidence.json"; evidence.write_text(json.dumps(report))
    registry = tmp_path / "registry.csv"
    original = (STAGE8 / "production_instrument_registry.csv").read_bytes(); registry.write_bytes(original)
    real_reader = updater.csv.DictReader
    calls = 0
    def mutating_reader(*args, **kwargs):
        nonlocal calls
        calls += 1
        reader = real_reader(*args, **kwargs)
        if calls != 2: return reader
        rows = list(reader); rows[0][field] += "-MUTATED"
        return iter(rows)
    monkeypatch.setattr(updater.csv, "DictReader", mutating_reader)
    with pytest.raises(RuntimeError, match="TEMP_REGISTRY_VALIDATION_FAILED"):
        updater.update(evidence, registry)
    assert registry.read_bytes() == original
