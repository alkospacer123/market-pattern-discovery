"""Static guarantee: the Intel SLTP preflight is local READONLY only."""
from pathlib import Path
import re

SCRIPT = Path(__file__).resolve().parents[1] / "diagnostics" / "run-stage8-493-sltp-local-readonly-precheck.ps1"


def test_local_sltp_preflight_cannot_mutate_live_or_submit_orders():
    text = SCRIPT.read_text(encoding="utf-8")
    assert "Get-ScheduledTask" in text and "Get-Content" in text
    assert "BLOCKED_LIVE_PRODUCTION_NOT_ISOLATED" in text
    assert "THIS_IS_NOT_PHYSICAL_BROKER_ACCEPTANCE" in text
    assert "REAL_ORDER_AUTHORIZATION=NOT_GRANTED_BY_THIS_SCRIPT" in text
    assert "184e8c2b8fa092a606249ff293a4f507160bff29" in text
    assert "FRESH_FINAM_POSITION_ORDER_AND_MARGIN_AUTHORITY=NOT_COLLECTED" in text
    forbidden_verbs = re.compile(r"(?im)^\\s*(?:start|stop|restart|enable|disable|register|unregister|remove|new|set|invoke)\\-[a-z]+")
    assert not forbidden_verbs.search(text)
    for forbidden in (
        "Get-TradingCredential", "Get-ReadonlyCredential", "FINAM_API_SECRET",
        "FinamAPI", "place_order", "place_sltp_order", "cancel_order",
        "Invoke-WebRequest", "Invoke-RestMethod", "curl.exe",
        "sqlite3", "Set-Content", "New-Item", "Out-File",
        "emergency_halt", "write_kill_switch", "kill_switch_state=ARMED",
    ):
        assert forbidden not in text
