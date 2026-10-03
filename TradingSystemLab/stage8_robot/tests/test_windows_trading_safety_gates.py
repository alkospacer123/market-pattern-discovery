from pathlib import Path
import hashlib

EXPECTED = {
    "trading_safety_gate.py": "64c781579e630836cfde7a0b772df1e2707caf35decafb9acdc75d7d2e3df6e4",
    "safety_gate_validation.py": "c8b13bc0938a0b8362c5c75db46d75bff17dd04bede769bb323f99b443bd26ff",
    "deploy/windows/validate-trading-safety-gates.ps1": "2c10fbfcfdf5e79bf8d224dc05f50d9e536b89b8623cef7526329a7e252ab9eb",
}

def canonical(raw):
    return hashlib.sha256(raw.replace(b"\r\n", b"\n")).hexdigest()

def test_lf_crlf_canonical_hashes_and_content_mutation():
    root=Path(__file__).parents[1]
    for relative, expected in EXPECTED.items():
        raw=(root/relative).read_bytes().replace(b"\r\n",b"\n")
        assert canonical(raw)==canonical(raw.replace(b"\n",b"\r\n"))==expected
        assert canonical(raw+b"# semantic mutation\n")!=expected

def test_wrapper_is_offline_halt_only():
    text=(Path(__file__).parents[1]/"deploy/windows/validate-trading-safety-gates.ps1").read_text()
    assert "Get-ScheduledTask" in text and "Push-Location" in text and "Pop-Location" in text
    assert "emergency_halt" in text and "allow_arm" not in text.lower()
    for forbidden in ("Enable-ScheduledTask","Start-ScheduledTask","Invoke-WebRequest","Invoke-RestMethod"):
        assert forbidden not in text
