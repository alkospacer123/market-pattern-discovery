"""CC-05 historical broker acceptance and redaction, independent of FINAM."""
from datetime import datetime, timedelta, timezone
from hashlib import sha256
import json
from pathlib import Path
import pytest
from cc import v20_finam as panel
from deployment.export_v20_finam import sanitize

NOW = datetime(2026, 10, 24, 13, 0, tzinfo=timezone.utc)
AT = "2026-10-24T06:07:32.065908+00:00"
IDS = ("v20-shallow", "v20-obv", "v20-inside")


def original():
    return {
        "schema": "v20.finam.broker_readonly_report.v1",
        "status": "PASS_READONLY_3_OF_3", "stage_06_status": "PASS",
        "entry_authorized": False, "real_orders_sent_by_diagnostics": 0,
        "actual_sltp_execution_verified": False,
        "live_equity_ledger_reconciled": False,
        "source_observed_at_utc": AT,
        "accounts": [
            {"robot": robot, "account_sha256": f"{i + 1:064x}",
             "readonly_result": "PASS_READONLY", "money_status": "PASS",
             "positions_nonzero": 0, "active_orders": 0,
             "sensitive_account_id": f"secret-account-{i}", "money_details": "secret"}
            for i, robot in enumerate(IDS)],
        "token": "secret-token",
    }


def wire(value):
    return json.dumps(value, ensure_ascii=True).encode("utf-8")


def test_export_allowlist_never_contains_secrets_or_accounts():
    original_bytes = wire(original())
    exported = sanitize(original_bytes, NOW)
    raw = wire(exported)
    assert exported["overall"] == "PASS_READONLY_3_OF_3"
    assert exported["source_sha256"] == sha256(original_bytes).hexdigest()
    assert set(exported) == panel.EXPECTED
    assert b"secret" not in raw and b"account_sha256" not in raw
    assert len(exported["accounts"]) == 3
    result = panel.parse(raw, NOW)
    assert result["kind"] == "HISTORICAL_ONLY"
    assert result["observed_at"].isoformat() == AT
    assert set(result["accounts"]) == set(IDS)
    assert all(row["positions"] == 0 and row["orders"] == 0
               for row in result["accounts"].values())


@pytest.mark.parametrize("mutation", [
    lambda x: x.update(status="PARTIAL_READONLY"),
    lambda x: x.update(entry_authorized=True),
    lambda x: x["accounts"][0].update(money_status="BLOCKED"),
    lambda x: x["accounts"][0].update(active_orders=1),
    lambda x: x["accounts"][0].update(positions_nonzero=1),
    lambda x: x["accounts"][0].update(robot="v20-inside"),
    lambda x: x["accounts"][1].update(account_sha256=f"{1:064x}"),
    lambda x: x.update(source_observed_at_utc="2030-01-01T00:00:00Z"),
])
def test_export_refuses_partial_wrong_accounts_trading_or_future(mutation):
    source = original()
    mutation(source)
    with pytest.raises(ValueError):
        sanitize(wire(source), NOW)


def test_export_refuses_duplicate_json_keys():
    raw = wire(original()).replace(b'"status": "PASS_READONLY_3_OF_3"',
                                   b'"status": "PASS_READONLY_3_OF_3", "status": "PASS_READONLY_3_OF_3"')
    with pytest.raises(ValueError, match="DUPLICATE"):
        sanitize(raw, NOW)


@pytest.mark.parametrize("change", [
    lambda x: x.update(overall="PARTIAL_READONLY"),
    lambda x: x["accounts"][0].update(active_orders=1),
    lambda x: x["accounts"][0].update(robot="v20-inside"),
    lambda x: x.update(source_observed_at_utc="2030-01-01T00:00:00Z"),
    lambda x: x.update(token="SECRET_TOKEN"),
])
def test_reader_never_accepts_forged_or_extended_evidence(change):
    exported = sanitize(wire(original()), NOW)
    change(exported)
    with pytest.raises(ValueError):
        panel.parse(wire(exported), NOW)


def test_reader_is_manual_secure_local_only_and_fails_closed(monkeypatch):
    exported = sanitize(wire(original()), NOW)
    calls = []
    def read(root, name, limit, expected_root=None, admin_policy=False):
        calls.append((root, name, limit, expected_root, admin_policy))
        return wire(exported)
    monkeypatch.setattr(panel, "read_windows", read)
    assert panel.acquire(NOW)["kind"] == "HISTORICAL_ONLY"
    assert calls == [(str(panel.ROOT), panel.NAME, 4096, None, True)]
    monkeypatch.setattr(panel, "read_windows", lambda *args, **kwargs: (_ for _ in ()).throw(ValueError("DENIED")))
    assert panel.acquire(NOW) is None


def test_historical_does_not_become_current_by_refresh():
    raw = wire(sanitize(wire(original()), NOW))
    year_later = NOW + timedelta(days=365)
    accepted = panel.parse(raw, year_later)
    assert accepted["kind"] == "HISTORICAL_ONLY"
    assert accepted["observed_at"].year == 2026
