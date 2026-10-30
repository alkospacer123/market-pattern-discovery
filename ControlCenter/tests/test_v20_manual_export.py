"""Manual V20 update only reads known CC-owned source; no broker/order/Task use."""
from hashlib import sha1
from pathlib import Path
from types import SimpleNamespace

from cc import v20_manual_export as source


def test_nonwindows_or_absent_installation_fails_closed(monkeypatch):
    monkeypatch.setattr(source, "os", SimpleNamespace(name="posix"))
    assert source.refresh_once() == "PUBLISHER_UNAVAILABLE"


def test_exact_pinned_exporter_and_expected_readonly_response(tmp_path, monkeypatch):
    exporter = tmp_path / "v20_live_export.py"
    exporter.write_text("print('mocked by subprocess; not executed')\n", encoding="utf-8")
    python = tmp_path / "python.exe"
    python.write_bytes(b"exe fixture, never executed")
    raw = exporter.read_bytes()
    sha = sha1(b"blob " + str(len(raw)).encode() + b"\0" + raw).hexdigest()
    monkeypatch.setattr(source, "PUBLISHER", exporter)
    monkeypatch.setattr(source, "PYTHON", python)
    monkeypatch.setattr(source, "BLOB", sha)
    monkeypatch.setattr(source, "os", SimpleNamespace(name="nt"))
    calls = []
    def runner(argv, **kwargs):
        calls.append(argv)
        return SimpleNamespace(returncode=0, stdout=(
            b"cc02_v20-shallow=HALTED\ncc02_v20-obv=HALTED\n"
            b"cc02_v20-inside=HALTED\ncc02_export=PUBLISHED_CC_OWNED\n"
            b"cc02_no_finam_no_task_mutation_no_arm=YES\n"))
    monkeypatch.setattr(source.subprocess, "run", runner)
    assert source.refresh_once() == "READONLY_EXPORT_PASS"
    assert len(calls) == 1
    assert calls[0] == [str(python), "-I", "-B", str(exporter), "--publish"]

    monkeypatch.setattr(source, "BLOB", "0" * 40)
    assert source.refresh_once() == "PUBLISHER_UNVERIFIED"
    assert len(calls) == 1


def test_execution_failure_never_turns_into_success(tmp_path, monkeypatch):
    exporter = tmp_path / "v20_live_export.py"
    exporter.write_bytes(b"safe")
    python = tmp_path / "python.exe"
    python.write_bytes(b"exe")
    raw = exporter.read_bytes()
    sha = sha1(b"blob " + str(len(raw)).encode() + b"\0" + raw).hexdigest()
    monkeypatch.setattr(source, "PUBLISHER", exporter)
    monkeypatch.setattr(source, "PYTHON", python)
    monkeypatch.setattr(source, "BLOB", sha)
    monkeypatch.setattr(source, "os", SimpleNamespace(name="nt"))
    monkeypatch.setattr(source.subprocess, "run",
                        lambda *a, **kw: SimpleNamespace(returncode=1, stdout=b""))
    assert source.refresh_once() == "READONLY_EXPORT_FAILED"


def test_source_has_no_live_controls():
    source_code = (Path(__file__).resolve().parents[1] /
                   "cc/v20_manual_export.py").read_text(encoding="utf-8")
    assert '"--publish"' in source_code
    for forbidden in ("Start-ScheduledTask", "Stop-ScheduledTask",
                      "FinamAPI", '"--arm"', '"--halt"', '"--restart"'):
        assert forbidden not in source_code
