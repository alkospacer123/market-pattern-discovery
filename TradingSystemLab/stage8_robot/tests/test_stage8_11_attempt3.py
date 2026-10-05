"""Regression tests for the fixed Stage 8.11 attempt-3 boundary."""
import hashlib

from TradingSystemLab.stage8_robot.broker import OrderRequest
from TradingSystemLab.stage8_robot.controlled_real_acceptance import (
    ControlledAcceptanceBroker, STAGE8_11_ATTEMPT3_ID, run_controlled_lifecycle,
)
from TradingSystemLab.stage8_robot.stage8_11_physical_acceptance_attempt3 import (
    ATTEMPT_ID, PREVIOUS_ENTRY_KEY, REPORT_NAME, _reconcile_previous_attempt,
)
from TradingSystemLab.stage8_robot.state import StateStore
from TradingSystemLab.stage8_robot.tests.test_controlled_real_acceptance import (
    ACCOUNT, API, HASH, NOW, armed_runtime, authority, fill,
)


def test_attempt3_identity_and_evidence_path_are_repository_fixed():
    assert ATTEMPT_ID == STAGE8_11_ATTEMPT3_ID == "stage8.11.attempt3"
    assert REPORT_NAME == "stage8_11_physical_acceptance_attempt3.json"


def test_attempt3_reconciles_attempt2_ack_without_resubmitting_entry(tmp_path, monkeypatch):
    from TradingSystemLab.stage8_robot import stage8_11_physical_acceptance_attempt3 as physical

    root = tmp_path / "runtime"
    evidence = root / "diagnostics" / physical.PREVIOUS_REPORT_NAME
    evidence.parent.mkdir(parents=True)
    evidence.write_bytes(b"synthetic immutable attempt2 evidence\n")
    monkeypatch.setattr(
        physical, "PREVIOUS_EVIDENCE_SHA256",
        hashlib.sha256(evidence.read_bytes()).hexdigest().upper())

    store = StateStore(tmp_path / "state.db")
    payload = ControlledAcceptanceBroker._payload(
        OrderRequest(PREVIOUS_ENTRY_KEY, "CNYRUBF@RTSX", "LONG", 1))
    assert store.persist_intent(PREVIOUS_ENTRY_KEY, payload)
    store.transition_intent(PREVIOUS_ENTRY_KEY, "ACK", "o1")

    # Broker order is filled and the account is already flat because the
    # operator manually closed the position outside Stage 8.11.
    api = API(store, [fill("o1", 0)])
    broker = ControlledAcceptanceBroker(api, ACCOUNT, HASH, store)

    _reconcile_previous_attempt(runtime_root=root, broker=broker, store=store)

    assert api.posts == 0
    assert store.intent(PREVIOUS_ENTRY_KEY)["status"] == "RECONCILED"
    assert store.unresolved_intent_count() == 0
    assert store.db.execute("SELECT COUNT(*) FROM fills").fetchone()[0] == 1

def test_attempt3_full_repeat_after_manual_flat_and_attempt2_reconciliation(tmp_path, monkeypatch):
    from TradingSystemLab.stage8_robot import stage8_11_physical_acceptance_attempt3 as physical

    root = tmp_path / "runtime"
    evidence = root / "diagnostics" / physical.PREVIOUS_REPORT_NAME
    evidence.parent.mkdir(parents=True)
    evidence.write_bytes(b"synthetic immutable attempt2 evidence\n")
    monkeypatch.setattr(
        physical, "PREVIOUS_EVIDENCE_SHA256",
        hashlib.sha256(evidence.read_bytes()).hexdigest().upper())

    store = StateStore(tmp_path / "state.db")
    previous_payload = ControlledAcceptanceBroker._payload(
        OrderRequest(PREVIOUS_ENTRY_KEY, "CNYRUBF@RTSX", "LONG", 1))
    assert store.persist_intent(PREVIOUS_ENTRY_KEY, previous_payload)
    store.transition_intent(PREVIOUS_ENTRY_KEY, "ACK", "old-order")

    api = API(store, [
        fill("old-order", 0),
        fill("o1", 1),
        fill("o2", 0),
    ])
    broker = ControlledAcceptanceBroker(api, ACCOUNT, HASH, store)

    _reconcile_previous_attempt(runtime_root=root, broker=broker, store=store)
    assert api.posts == 0
    assert store.intent(PREVIOUS_ENTRY_KEY)["status"] == "RECONCILED"

    result = run_controlled_lifecycle(
        authority=authority(), runtime_root=armed_runtime(tmp_path),
        execution_authorized=True, instrument="CNYRUBF", finam_symbol="CNYRUBF@RTSX",
        direction="LONG", broker=broker, now=NOW, attempt_id=STAGE8_11_ATTEMPT3_ID)

    assert result["classification"] == "SYNTHETIC_PASS"
    assert api.posts == 2
    assert store.intent("stage8.11.attempt3:CNYRUBF:entry")["status"] == "RECONCILED"
    assert store.intent("stage8.11.attempt3:CNYRUBF:flatten")["status"] == "RECONCILED"
    assert store.unresolved_intent_count() == 0

