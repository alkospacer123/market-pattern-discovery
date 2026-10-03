from pathlib import Path
import hashlib

EXPECTED = {
    "trading_safety_gate.py": "64c781579e630836cfde7a0b772df1e2707caf35decafb9acdc75d7d2e3df6e4",
    "safety_gate_validation.py": "baf9f85f8fa3c6c789db7ce40d9d23fb13d7854c11820986f33c1c5436716b9f",
    "deploy/windows/validate-trading-safety-gates.ps1": "7da9ff0a252008f41c771866d528cbaf4ce2fc97221b87a1b933d50acb75c4d5",
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
    halt = text.index("emergency_halt")
    validation = text.index("TradingSystemLab.stage8_robot.safety_gate_validation")
    final_halt = text.rindex("load_kill_switch")
    assert halt < validation < final_halt
    assert "--production-runtime-root $runtime" in text
    assert "emergency_halt" in text and "allow_arm" not in text.lower()
    assert "Get-ScheduledTask" in text
    for forbidden in ("Enable-ScheduledTask","Start-ScheduledTask","Register-ScheduledTask","Invoke-WebRequest","Invoke-RestMethod",
                      "credential-store.ps1","trading-credential-store.ps1","Get-ReadonlyCredential","Get-TradingCredential",
                      "execution_authorized=true"):
        assert forbidden not in text
