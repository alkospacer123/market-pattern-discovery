import hashlib
import json
from pathlib import Path

import pytest

from TradingSystemLab.stage8_robot.broker import OrderRequest
from TradingSystemLab.stage8_robot.controlled_real_acceptance import ControlledAcceptanceBroker
from TradingSystemLab.stage8_robot.specification import PRODUCTION_SPECIFICATION_ID
from TradingSystemLab.stage8_robot.stage8_11_attempt6_manual_close_recovery import (
    ATTEMPT6_ACCEPTED_CODE_COMMIT,
    ATTEMPT6_EVIDENCE_NAME,
    ATTEMPT6_INTENT_KEY,
    FINAM_SYMBOL,
    RECOVERY_EVIDENCE_NAME,
    Attempt6ManualCloseRecoveryBlocked,
    recover_attempt6_manual_close,
)
from TradingSystemLab.stage8_robot.state import StateStore, initialize_stage8_11_acceptance_ledger
from TradingSystemLab.stage8_robot.tests.test_controlled_real_acceptance import ACCOUNT, NOW
from TradingSystemLab.stage8_robot.trading_safety_gate import write_kill_switch


class ReadonlyAttempt6API:
    def __init__(self, *, positions=None, orders=None):
        self.positions = positions if positions is not None else [
            {"symbol": FINAM_SYMBOL, "quantity": {"value": "0"}}
        ]
        self.orders_rows = orders if orders is not None else []
        self.calls = []

    def session_details(self):
        self.calls.append("session_details")
        return {"readonly": True, "account_ids": [ACCOUNT]}

    def account(self, account_id):
        self.calls.append("account")
        return {"positions": self.positions}

    def orders(self, account_id):
        self.calls.append("orders")
        return {"orders": self.orders_rows}


def setup_attempt6(tmp_path, monkeypatch):
    from TradingSystemLab.stage8_robot import stage8_11_attempt6_manual_close_recovery as recovery

    root = tmp_path / "runtime"
    write_kill_switch(root, "HALTED", now=NOW)

    evidence = root / "diagnostics" / ATTEMPT6_EVIDENCE_NAME
    evidence.parent.mkdir(parents=True, exist_ok=True)
    payload = {
        "schema_id": "stage8_11_physical_acceptance.v1",
        "production_specification_id": PRODUCTION_SPECIFICATION_ID,
        "stage8_11_status": "PHYSICAL_RESULT_REQUIRES_INDEPENDENT_AUDIT",
        "accepted_code_commit": ATTEMPT6_ACCEPTED_CODE_COMMIT,
        "attempt_id": "stage8.11.attempt6",
        "sanitized_account_identity_hash": hashlib.sha256(ACCOUNT.encode()).hexdigest(),
        "instrument": "CNYRUBF",
        "direction": "LONG",
        "quantity": 1,
        "kill_switch_final_state": "HALTED",
        "execution_authorization_observed": True,
        "order_endpoint_call_count": 1,
        "broker_order_present": True,
        "broker_fill_count": 0,
        "entry_fill_proven": False,
        "one_contract_position_observed": False,
        "controlled_flatten_proven": False,
        "final_position_quantity": 1,
        "final_active_order_count": 0,
        "unresolved_intent_count": 1,
        "reconciliation_result": "UNRESOLVED",
        "physical_result_classification": "OPERATOR_INTERVENTION_REQUIRED",
        "preflight_gate_outcomes": {
            "account_binding": True, "credential_scope": True,
            "h1_data_safety": True, "initial_reconciliation": True,
            "instrument_binding": True, "instrument_tradable": True,
            "margin_capacity": True, "r15_capacity": True,
            "session_write_capable": True,
        },
    }
    evidence.write_text(json.dumps(payload, sort_keys=True) + "\n")
    digest = hashlib.sha256(evidence.read_bytes()).hexdigest().upper()
    monkeypatch.setattr(recovery, "ATTEMPT6_EVIDENCE_SHA256", digest)

    ledger = initialize_stage8_11_acceptance_ledger(root, ACCOUNT)
    store = StateStore(ledger)
    request = ControlledAcceptanceBroker._payload(
        OrderRequest(ATTEMPT6_INTENT_KEY, FINAM_SYMBOL, "LONG", 1)
    )
    assert store.persist_intent(ATTEMPT6_INTENT_KEY, request)
    store.transition_intent(ATTEMPT6_INTENT_KEY, "ACK", "attempt6-order")
    store.close()
    return root, digest


def test_attempt6_manual_close_recovery_closes_stale_entry_from_flat_account(tmp_path, monkeypatch):
    root, digest = setup_attempt6(tmp_path, monkeypatch)
    api = ReadonlyAttempt6API()

    result = recover_attempt6_manual_close(
        runtime_root=root, account_id=ACCOUNT, readonly_api=api,
        recovery_code_commit="a" * 40, now=NOW)

    store = StateStore(root / "state" / "stage8-11-acceptance.sqlite3")
    try:
        assert store.intent(ATTEMPT6_INTENT_KEY)["status"] == "CLOSED"
        assert store.unresolved_intent_count() == 0
    finally:
        store.close()

    assert result["recovery_status"] == "COMMITTED"
    assert result["attempt6_evidence_sha256"] == digest
    assert result["all_positions_zero"] is True
    assert result["active_broker_order_count"] == 0
    assert result["attempt6_reclassified_as_pass"] is False
    assert result["physical_result_preserved"] == "OPERATOR_INTERVENTION_REQUIRED"
    assert result["manual_close_history_preserved"] is True
    assert (root / "diagnostics" / RECOVERY_EVIDENCE_NAME).is_file()
    assert list((root / "backups" / "stage8-11-acceptance").glob("*.sqlite3"))
    assert api.calls == ["session_details", "account", "orders"]


def test_attempt6_manual_close_recovery_blocks_if_position_still_open(tmp_path, monkeypatch):
    root, _ = setup_attempt6(tmp_path, monkeypatch)
    api = ReadonlyAttempt6API(
        positions=[{"symbol": FINAM_SYMBOL, "quantity": {"value": "1"}}]
    )
    with pytest.raises(Attempt6ManualCloseRecoveryBlocked, match="ACCOUNT_NOT_FLAT"):
        recover_attempt6_manual_close(
            runtime_root=root, account_id=ACCOUNT, readonly_api=api,
            recovery_code_commit="a" * 40, now=NOW)


def test_attempt6_manual_close_recovery_blocks_if_active_orders_present(tmp_path, monkeypatch):
    root, _ = setup_attempt6(tmp_path, monkeypatch)
    api = ReadonlyAttempt6API(
        orders=[{"order_id": "x", "status": "ORDER_STATUS_NEW", "order": {}}]
    )
    with pytest.raises(Attempt6ManualCloseRecoveryBlocked, match="ACTIVE_ORDERS_PRESENT"):
        recover_attempt6_manual_close(
            runtime_root=root, account_id=ACCOUNT, readonly_api=api,
            recovery_code_commit="a" * 40, now=NOW)


def test_attempt6_manual_close_recovery_is_idempotent(tmp_path, monkeypatch):
    root, _ = setup_attempt6(tmp_path, monkeypatch)
    api = ReadonlyAttempt6API()
    first = recover_attempt6_manual_close(
        runtime_root=root, account_id=ACCOUNT, readonly_api=api,
        recovery_code_commit="a" * 40, now=NOW)
    second = recover_attempt6_manual_close(
        runtime_root=root, account_id=ACCOUNT, readonly_api=api,
        recovery_code_commit="a" * 40, now=NOW)
    assert second == first


def test_attempt6_manual_close_recovery_source_has_no_trade_or_order_detail_capability():
    import TradingSystemLab.stage8_robot.stage8_11_attempt6_manual_close_recovery as recovery

    source = Path(recovery.__file__).read_text(encoding="utf-8")
    for forbidden in (".place_order(", ".cancel_order(", ".modify_order(", ".trades(", ".order("):
        assert forbidden not in source
