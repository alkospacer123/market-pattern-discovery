"""Offline static regression for Windows PowerShell 5.1 financial READONLY wrapper.

These tests do not replace a physical Intel PowerShell run and never call FINAM.
"""
from pathlib import Path

SOURCE = Path(__file__).resolve().parents[1] / "diagnostics/stage8-493-n4-financial-readonly.ps1"


def test_explicit_independent_hash_guards_without_nested_array_iteration():
    value = SOURCE.read_text(encoding="utf-8")
    assert "foreach ($row in @(@(" not in value
    assert "-LiteralPath $row[0]" not in value
    assert "-cne $row[1]" not in value
    assert value.count("-LiteralPath $source -PathType Leaf") == 1
    assert value.count("-LiteralPath $probe -PathType Leaf") == 1
    assert value.count("-LiteralPath $source -Algorithm SHA256") == 1
    assert value.count("-LiteralPath $probe -Algorithm SHA256") == 1
    assert "-cne $source_sha256" in value
    assert "-cne $probe_sha256" in value
    assert "throw 'EXACT_FINANCIAL_PYTHON_SOURCE_HASH_MISMATCH'" in value
    assert "throw 'EXACT_POST_ISOLATION_SOURCE_HASH_MISMATCH'" in value
    assert "Write-Output 'EXACT_READONLY_SOURCE_HASHES=PASS'" in value


def test_exact_existing_pins_and_fail_closed_gate_preserved():
    value = SOURCE.read_text(encoding="utf-8")
    assert "CF366762E7CB4B75EB25317E890FD59D6F5F4FB88299B85FBE1904FEB3D16F2B" in value
    assert "37DF9E1A8F4B0B18EE37D1ACC8757AD674160E878264B2746ED0E1BB3E66C201" in value
    assert "FRESH_POST_ISOLATION_READONLY_GATE_FAILED" in value
    assert "Get-ReadonlyCredential" in value
    assert "CLASSIFICATION=STAGE8_493_N4_FINANCIAL_READONLY_REPORT_CREATED_NOT_TRADE_AUTHORITY" in value
    assert "NO_REAL_ORDER_AUTHORIZATION=YES" in value
    assert "PINNED_LIVE_CHECKOUT_CHANGED" in value


def test_no_mutating_production_or_trade_endpoint_commands():
    value = SOURCE.read_text(encoding="utf-8").lower()
    for forbidden in (
        "enable-scheduledtask", "disable-scheduledtask", "start-scheduledtask",
        "stop-scheduledtask", "set-content", "invoke-restmethod", "invoke-webrequest",
        "get-tradingcredential", "set-itemproperty", "new-itemproperty", "remove-scheduledtask",
        "/orders'", "/sltp-orders'", "/cancel", "place_order(",
    ):
        assert forbidden not in value
