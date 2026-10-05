import hashlib
import json

import pytest

from TradingSystemLab.stage8_robot.broker import OrderRequest
from TradingSystemLab.stage8_robot.controlled_real_acceptance import ControlledAcceptanceBroker
from TradingSystemLab.stage8_robot.specification import ACTIVE_IDENTITY, PRODUCTION_SPECIFICATION_ID
from TradingSystemLab.stage8_robot.stage8_11_attempt2_manual_recovery import (
    ATTEMPT2_EVIDENCE_NAME,
    ATTEMPT2_INTENT_KEY,
    FINAM_SYMBOL,
    RECOVERY_EVIDENCE_NAME,
    Attempt2RecoveryBlocked,
    recover_attempt2_manual_close,
)
from TradingSystemLab.stage8_robot.state import StateStore, initialize_stage8_11_acceptance_ledger
from TradingSystemLab.stage8_robot.tests.test_controlled_real_acceptance import ACCOUNT, NOW
from TradingSystemLab.stage8_robot.trading_safety_gate import write_kill_switch


class ReadonlyAttempt2API:
    def __init__(self, *, client_id, positions=None, orders=None):
        self.positions = positions if positions is not None else [
            {"symbol": FINAM_SYMBOL, "quantity": {"value": "0.0"}}
        ]
        self.orders_rows = orders if orders is not None else [
            {"order_id": "old-order", "status": "ORDER_STATUS_EXECUTED",
             "order": {"client_order_id": client_id, "symbol": FINAM_SYMBOL,
                       "side": "SIDE_BUY", "quantity": {"value": "1"}}}
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


def setup_attempt2(tmp_path, monkeypatch):
    from TradingSystemLab.stage8_robot import stage8_11_attempt2_manual_recovery as recovery

    root = tmp_path / "runtime"
    write_kill_switch(root, "HALTED", now=NOW)

    evidence = root / "diagnostics" / ATTEMPT2_EVIDENCE_NAME
    evidence.parent.mkdir(parents=True, exist_ok=True)
    evidence.write_bytes(b"synthetic immutable attempt2 evidence\n")
    digest = hashlib.sha256(evidence.read_bytes()).hexdigest().upper()
    monkeypatch.setattr(recovery, "ATTEMPT2_EVIDENCE_SHA256", digest)

    ledger = initialize_stage8_11_acceptance_ledger(root, ACCOUNT)
    store = StateStore(ledger)
    payload = ControlledAcceptanceBroker._payload(
        OrderRequest(ATTEMPT2_INTENT_KEY, FINAM_SYMBOL, "LONG", 1)
    )
    assert store.persist_intent(ATTEMPT2_INTENT_KEY, payload)
    store.transition_intent(ATTEMPT2_INTENT_KEY, "ACK", "old-order")
    client_id = store.intent(ATTEMPT2_INTENT_KEY)["payload"]["client_order_id"]
    store.close()
    return root, digest, client_id


def test_attempt2_manual_recovery_closes_only_exact_stale_local_intent(tmp_path, monkeypatch):
    root, digest, client_id = setup_attempt2(tmp_path, monkeypatch)
    api = ReadonlyAttempt2API(client_id=client_id)

    result = recover_attempt2_manual_close(
        runtime_root=root, account_id=ACCOUNT, readonly_api=api,
        recovery_code_commit="a" * 40, now=NOW)

    store = StateStore(root / "state" / "stage8-11-acceptance.sqlite3")
    try:
        assert store.intent(ATTEMPT2_INTENT_KEY)["status"] == "CLOSED"
        assert store.unresolved_intent_count() == 0
    finally:
        store.close()

    assert result["recovery_status"] == "COMMITTED"
    assert result["attempt2_evidence_sha256"] == digest
    assert result["attempt2_reclassified_as_pass"] is False
    assert result["manual_close_history_preserved"] is True
    assert result["all_positions_zero"] is True
    assert result["active_broker_order_count"] == 0
    assert result["broker_order_terminal_status"] == "EXECUTED"
    assert (root / "diagnostics" / RECOVERY_EVIDENCE_NAME).is_file()
    assert list((root / "backups" / "stage8-11-acceptance").glob("*.sqlite3"))
    assert api.calls == ["session_details", "account", "orders"]


def test_attempt2_manual_recovery_is_idempotent_after_commit(tmp_path, monkeypatch):
    root, _, client_id = setup_attempt2(tmp_path, monkeypatch)
    api = ReadonlyAttempt2API(client_id=client_id)
    first = recover_attempt2_manual_close(
        runtime_root=root, account_id=ACCOUNT, readonly_api=api,
        recovery_code_commit="a" * 40, now=NOW)
    second = recover_attempt2_manual_close(
        runtime_root=root, account_id=ACCOUNT, readonly_api=api,
        recovery_code_commit="a" * 40, now=NOW)
    assert second == first


@pytest.mark.parametrize("case", ["nonflat", "active", "missing", "identity", "quantity", "nofill"])
def test_attempt2_manual_recovery_fails_closed_on_unclean_or_unproven_broker_state(
        tmp_path, monkeypatch, case):
    root, _, client_id = setup_attempt2(tmp_path, monkeypatch)
    if case == "nonflat":
        api = ReadonlyAttempt2API(
            client_id=client_id,
            positions=[{"symbol": FINAM_SYMBOL, "quantity": {"value": "1"}}])
    elif case == "active":
        api = ReadonlyAttempt2API(
            client_id=client_id,
            orders=[{"order_id": "old-order", "status": "ORDER_STATUS_PENDING_NEW",
                     "order": {"client_order_id": client_id, "symbol": FINAM_SYMBOL,
                               "side": "SIDE_BUY", "quantity": {"value": "1"}}}])
    elif case == "missing":
        api = ReadonlyAttempt2API(client_id=client_id, orders=[])
    elif case == "identity":
        api = ReadonlyAttempt2API(
            client_id=client_id,
            orders=[{"order_id": "old-order", "status": "ORDER_STATUS_EXECUTED",
                     "order": {"client_order_id": "wrong", "symbol": FINAM_SYMBOL,
                               "side": "SIDE_BUY", "quantity": {"value": "1"}}}])
    elif case == "quantity":
        api = ReadonlyAttempt2API(
            client_id=client_id,
            orders=[{"order_id": "old-order", "status": "ORDER_STATUS_EXECUTED",
                     "order": {"client_order_id": client_id, "symbol": FINAM_SYMBOL,
                               "side": "SIDE_BUY", "quantity": {"value": "2"}}}])
    else:
        api = ReadonlyAttempt2API(
            client_id=client_id,
            orders=[{"order_id": "old-order", "status": "ORDER_STATUS_REJECTED",
                     "order": {"client_order_id": client_id, "symbol": FINAM_SYMBOL,
                               "side": "SIDE_BUY", "quantity": {"value": "1"}}}])

    with pytest.raises(Attempt2RecoveryBlocked):
        recover_attempt2_manual_close(
            runtime_root=root, account_id=ACCOUNT, readonly_api=api,
            recovery_code_commit="a" * 40, now=NOW)

    store = StateStore(root / "state" / "stage8-11-acceptance.sqlite3")
    try:
        assert store.intent(ATTEMPT2_INTENT_KEY)["status"] == "ACK"
    finally:
        store.close()


def test_attempt2_manual_recovery_source_is_order_incapable():
    import pathlib
    import TradingSystemLab.stage8_robot.stage8_11_attempt2_manual_recovery as recovery

    source = pathlib.Path(recovery.__file__).read_text(encoding="utf-8")
    assert ".place_order(" not in source
    assert ".cancel_order(" not in source
    assert ".trades(" not in source
    assert "write_kill_switch" not in source


def test_attempt3_windows_wrapper_recovers_before_trading_secret_environment():
    import pathlib
    import TradingSystemLab.stage8_robot.stage8_11_attempt2_manual_recovery as recovery

    wrapper = pathlib.Path(recovery.__file__).parent / "deploy" / "windows" / "run-stage8-11-physical-acceptance-attempt3.ps1"
    source = wrapper.read_text(encoding="utf-8")
    recovery_call = source.index("stage8_11_attempt2_manual_recovery")
    trading_secret = source.index("$env:STAGE8_11_TRADING_SECRET")
    assert recovery_call < trading_secret
    assert "STAGE8_11_RECOVERY_READONLY_SECRET" in source
    assert "STAGE8_11_RECOVERY_ACCOUNT_ID" in source
    assert "STAGE8_11_ATTEMPT2_MANUAL_RECOVERY_FAILED" in source
