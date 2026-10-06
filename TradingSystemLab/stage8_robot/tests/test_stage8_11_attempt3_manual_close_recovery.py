import hashlib
import json

import pytest

from TradingSystemLab.stage8_robot.broker import OrderRequest
from TradingSystemLab.stage8_robot.controlled_real_acceptance import ControlledAcceptanceBroker
from TradingSystemLab.stage8_robot.specification import ACTIVE_IDENTITY, PRODUCTION_SPECIFICATION_ID
from TradingSystemLab.stage8_robot.stage8_11_attempt3_manual_close_recovery import (
    ATTEMPT3_ACCEPTED_CODE_COMMIT,
    ATTEMPT3_EVIDENCE_NAME,
    ATTEMPT3_INTENT_KEY,
    FINAM_SYMBOL,
    RECOVERY_EVIDENCE_NAME,
    Attempt3ManualCloseRecoveryBlocked,
    recover_attempt3_manual_close,
)
from TradingSystemLab.stage8_robot.state import StateStore, initialize_stage8_11_acceptance_ledger
from TradingSystemLab.stage8_robot.tests.test_controlled_real_acceptance import ACCOUNT, NOW
from TradingSystemLab.stage8_robot.trading_safety_gate import write_kill_switch


class ReadonlyAttempt3API:
    def __init__(self, *, client_id, positions=None, orders=None):
        self.positions = positions if positions is not None else [
            {"symbol": FINAM_SYMBOL, "quantity": {"value": "0.0"}}
        ]
        self.client_id = client_id
        self.orders_rows = orders if orders is not None else [
            {"order_id": "attempt3-order", "status": "ORDER_STATUS_EXECUTED",
             "order": {"client_order_id": client_id}}
        ]
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

    def order(self, account_id, order_id):
        self.calls.append("order")
        return {
            "order_id": order_id,
            "status": "ORDER_STATUS_EXECUTED",
            "order": {
                "account_id": account_id,
                "client_order_id": self.client_id,
                "symbol": FINAM_SYMBOL,
                "side": "SIDE_BUY",
                "quantity": {"value": "1"},
            },
            "initial_quantity": {"value": "1"},
            "executed_quantity": {"value": "1"},
            "remaining_quantity": {"value": "0"},
        }


def setup_attempt3(tmp_path, monkeypatch):
    from TradingSystemLab.stage8_robot import stage8_11_attempt3_manual_close_recovery as recovery

    root = tmp_path / "runtime"
    write_kill_switch(root, "HALTED", now=NOW)

    evidence = root / "diagnostics" / ATTEMPT3_EVIDENCE_NAME
    evidence.parent.mkdir(parents=True, exist_ok=True)
    evidence.write_text(json.dumps({
        "schema_id": "stage8_11_physical_acceptance.v1",
        "production_specification_id": PRODUCTION_SPECIFICATION_ID,
        "stage8_11_status": "PHYSICAL_RESULT_REQUIRES_INDEPENDENT_AUDIT",
        "accepted_code_commit": ATTEMPT3_ACCEPTED_CODE_COMMIT,
        "attempt_id": "stage8.11.attempt3",
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
    }, sort_keys=True) + "\n")
    digest = hashlib.sha256(evidence.read_bytes()).hexdigest().upper()
    monkeypatch.setattr(recovery, "ATTEMPT3_EVIDENCE_SHA256", digest)

    ledger = initialize_stage8_11_acceptance_ledger(root, ACCOUNT)
    store = StateStore(ledger)
    payload = ControlledAcceptanceBroker._payload(
        OrderRequest(ATTEMPT3_INTENT_KEY, FINAM_SYMBOL, "LONG", 1)
    )
    assert store.persist_intent(ATTEMPT3_INTENT_KEY, payload)
    store.transition_intent(ATTEMPT3_INTENT_KEY, "ACK", "attempt3-order")
    client_id = store.intent(ATTEMPT3_INTENT_KEY)["payload"]["client_order_id"]
    store.close()
    return root, digest, client_id


def test_attempt3_manual_close_recovery_closes_only_stale_entry(tmp_path, monkeypatch):
    root, digest, client_id = setup_attempt3(tmp_path, monkeypatch)
    api = ReadonlyAttempt3API(client_id=client_id)

    result = recover_attempt3_manual_close(
        runtime_root=root, account_id=ACCOUNT, readonly_api=api,
        recovery_code_commit="a" * 40, now=NOW)

    store = StateStore(root / "state" / "stage8-11-acceptance.sqlite3")
    try:
        assert store.intent(ATTEMPT3_INTENT_KEY)["status"] == "CLOSED"
        assert store.unresolved_intent_count() == 0
    finally:
        store.close()

    assert result["recovery_status"] == "COMMITTED"
    assert result["attempt3_evidence_sha256"] == digest
    assert result["attempt3_reclassified_as_pass"] is False
    assert result["physical_result_preserved"] == "OPERATOR_INTERVENTION_REQUIRED"
    assert result["manual_close_history_preserved"] is True
    assert result["all_positions_zero"] is True
    assert result["active_broker_order_count"] == 0
    assert result["broker_order_terminal_status"] == "EXECUTED"
    assert (root / "diagnostics" / RECOVERY_EVIDENCE_NAME).is_file()
    assert list((root / "backups" / "stage8-11-acceptance").glob("*.sqlite3"))
    assert api.calls == ["session_details", "account", "orders", "order"]


def test_attempt3_manual_close_recovery_is_idempotent(tmp_path, monkeypatch):
    root, _, client_id = setup_attempt3(tmp_path, monkeypatch)
    api = ReadonlyAttempt3API(client_id=client_id)
    first = recover_attempt3_manual_close(
        runtime_root=root, account_id=ACCOUNT, readonly_api=api,
        recovery_code_commit="a" * 40, now=NOW)
    second = recover_attempt3_manual_close(
        runtime_root=root, account_id=ACCOUNT, readonly_api=api,
        recovery_code_commit="a" * 40, now=NOW)
    assert second == first


def test_attempt3_manual_close_recovery_blocks_while_position_still_open(tmp_path, monkeypatch):
    root, _, client_id = setup_attempt3(tmp_path, monkeypatch)
    api = ReadonlyAttempt3API(
        client_id=client_id,
        positions=[{"symbol": FINAM_SYMBOL, "quantity": {"value": "1"}}],
    )
    with pytest.raises(Attempt3ManualCloseRecoveryBlocked, match="ACCOUNT_NOT_FLAT"):
        recover_attempt3_manual_close(
            runtime_root=root, account_id=ACCOUNT, readonly_api=api,
            recovery_code_commit="a" * 40, now=NOW)


def test_attempt3_manual_close_recovery_blocks_wrong_broker_identity(tmp_path, monkeypatch):
    root, _, client_id = setup_attempt3(tmp_path, monkeypatch)
    api = ReadonlyAttempt3API(client_id=client_id)
    original = api.order

    def wrong_order(account_id, order_id):
        detail = original(account_id, order_id)
        detail["order"]["client_order_id"] = "wrong"
        return detail

    api.order = wrong_order
    with pytest.raises(Attempt3ManualCloseRecoveryBlocked, match="IDENTITY_MISMATCH"):
        recover_attempt3_manual_close(
            runtime_root=root, account_id=ACCOUNT, readonly_api=api,
            recovery_code_commit="a" * 40, now=NOW)


def test_attempt3_manual_close_recovery_requires_exact_executed_quantity(tmp_path, monkeypatch):
    root, _, client_id = setup_attempt3(tmp_path, monkeypatch)
    api = ReadonlyAttempt3API(client_id=client_id)
    original = api.order

    def not_executed(account_id, order_id):
        detail = original(account_id, order_id)
        detail["executed_quantity"] = {"value": "0"}
        detail["remaining_quantity"] = {"value": "1"}
        return detail

    api.order = not_executed
    with pytest.raises(Attempt3ManualCloseRecoveryBlocked, match="EXECUTION_NOT_PROVEN"):
        recover_attempt3_manual_close(
            runtime_root=root, account_id=ACCOUNT, readonly_api=api,
            recovery_code_commit="a" * 40, now=NOW)


def test_attempt3_manual_close_recovery_source_is_order_incapable():
    import pathlib
    import TradingSystemLab.stage8_robot.stage8_11_attempt3_manual_close_recovery as recovery

    source = pathlib.Path(recovery.__file__).read_text(encoding="utf-8")
    for forbidden in (".place_order(", ".cancel_order(", ".modify_order(", ".trades("):
        assert forbidden not in source


def test_attempt3_manual_close_windows_wrapper_uses_only_readonly_store():
    import pathlib
    import TradingSystemLab.stage8_robot.stage8_11_attempt3_manual_close_recovery as recovery

    wrapper = pathlib.Path(recovery.__file__).parent / "deploy" / "windows" / "run-stage8-11-attempt3-manual-close-recovery.ps1"
    source = wrapper.read_text(encoding="utf-8")
    assert "credential-store.ps1" in source
    assert "Get-ReadonlyCredential" in source
    assert "trading-credential-store.ps1" not in source
    assert "FINAM_TRADING" not in source
    assert "place_order" not in source
    assert "cancel_order" not in source
