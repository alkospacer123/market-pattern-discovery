"""Regression tests for position-authoritative Stage 8.11 attempt7."""
import hashlib
import json

import pytest

from TradingSystemLab.stage8_robot.broker import OrderRequest
from TradingSystemLab.stage8_robot.controlled_real_acceptance import (
    ControlledAcceptanceBroker, STAGE8_11_ATTEMPT7_ID, run_controlled_lifecycle,
)
from TradingSystemLab.stage8_robot.specification import ACTIVE_IDENTITY, PRODUCTION_SPECIFICATION_ID
from TradingSystemLab.stage8_robot.stage8_11_physical_acceptance_attempt7 import (
    ATTEMPT_ID, ATTEMPT6_RECOVERY_CODE_COMMIT, ATTEMPT6_RECOVERY_EVIDENCE_NAME,
    ATTEMPT6_RECOVERY_SCHEMA, PREVIOUS_ENTRY_KEY, REPORT_NAME, _reconcile_previous_attempt,
)
from TradingSystemLab.stage8_robot.state import StateStore
from TradingSystemLab.stage8_robot.tests.test_controlled_real_acceptance import (
    ACCOUNT, API, HASH, NOW, armed_runtime, authority,
)


class CleanRecoveredAccountAPI:
    def account(self, account_id):
        return {"positions": [{"symbol": "CNYRUBF@RTSX", "quantity": {"value": "0"}}]}

    def orders(self, account_id):
        return {"orders": []}


def prepare_recovered_attempt6(root, store, monkeypatch):
    from TradingSystemLab.stage8_robot import stage8_11_physical_acceptance_attempt7 as physical

    evidence = root / "diagnostics" / physical.PREVIOUS_REPORT_NAME
    evidence.parent.mkdir(parents=True, exist_ok=True)
    evidence.write_bytes(b"synthetic immutable attempt6 evidence\n")
    physical_digest = hashlib.sha256(evidence.read_bytes()).hexdigest().upper()
    monkeypatch.setattr(physical, "PREVIOUS_EVIDENCE_SHA256", physical_digest)

    payload = ControlledAcceptanceBroker._payload(
        OrderRequest(PREVIOUS_ENTRY_KEY, "CNYRUBF@RTSX", "LONG", 1))
    assert store.persist_intent(PREVIOUS_ENTRY_KEY, payload)
    store.transition_intent(PREVIOUS_ENTRY_KEY, "ACK", "attempt6-order")
    store.transition_intent(PREVIOUS_ENTRY_KEY, "CLOSED", "attempt6-order")

    recovery = root / "diagnostics" / ATTEMPT6_RECOVERY_EVIDENCE_NAME
    recovery.write_text(json.dumps({
        "schema_id": ATTEMPT6_RECOVERY_SCHEMA,
        "recovery_status": "COMMITTED",
        "attempt6_evidence_sha256": physical_digest,
        "intent_key": PREVIOUS_ENTRY_KEY,
        "account_identity_sha256": HASH,
        "production_specification_id": PRODUCTION_SPECIFICATION_ID,
        "active_identity": ACTIVE_IDENTITY,
        "final_local_intent_status": "CLOSED",
        "attempt6_reclassified_as_pass": False,
        "manual_close_history_preserved": True,
        "physical_result_preserved": "OPERATOR_INTERVENTION_REQUIRED",
        "recovery_code_commit": ATTEMPT6_RECOVERY_CODE_COMMIT,
    }, sort_keys=True) + "\n")
    recovery_digest = hashlib.sha256(recovery.read_bytes()).hexdigest().upper()
    monkeypatch.setattr(physical, "ATTEMPT6_RECOVERY_EVIDENCE_SHA256", recovery_digest)
    return physical_digest, recovery_digest


def test_attempt7_identity_and_evidence_path_are_fixed():
    assert ATTEMPT_ID == STAGE8_11_ATTEMPT7_ID == "stage8.11.attempt7"
    assert REPORT_NAME == "stage8_11_physical_acceptance_attempt7.json"


def test_attempt7_requires_exact_committed_attempt6_manual_recovery(tmp_path, monkeypatch):
    root = tmp_path / "runtime"
    store = StateStore(tmp_path / "state.db")
    prepare_recovered_attempt6(root, store, monkeypatch)

    broker = ControlledAcceptanceBroker(CleanRecoveredAccountAPI(), ACCOUNT, HASH, store)
    _reconcile_previous_attempt(
        runtime_root=root, broker=broker, store=store, accepted_commit="a" * 40)

    assert store.intent(PREVIOUS_ENTRY_KEY)["status"] == "CLOSED"
    assert store.unresolved_intent_count() == 0


def test_attempt7_blocks_tampered_attempt6_recovery_evidence(tmp_path, monkeypatch):
    from TradingSystemLab.stage8_robot import stage8_11_physical_acceptance_attempt7 as physical

    root = tmp_path / "runtime"
    store = StateStore(tmp_path / "state.db")
    prepare_recovered_attempt6(root, store, monkeypatch)
    recovery = root / "diagnostics" / ATTEMPT6_RECOVERY_EVIDENCE_NAME
    recovery.write_text(recovery.read_text() + "tamper\n")

    broker = ControlledAcceptanceBroker(CleanRecoveredAccountAPI(), ACCOUNT, HASH, store)
    with pytest.raises(Exception, match="RECOVERY_EVIDENCE_HASH_MISMATCH"):
        _reconcile_previous_attempt(
            runtime_root=root, broker=broker, store=store, accepted_commit="a" * 40)


def test_attempt7_full_position_authoritative_lifecycle_after_attempt6_recovery(tmp_path, monkeypatch):
    root = armed_runtime(tmp_path)
    store = StateStore(tmp_path / "state.db")
    prepare_recovered_attempt6(root, store, monkeypatch)

    clean_broker = ControlledAcceptanceBroker(CleanRecoveredAccountAPI(), ACCOUNT, HASH, store)
    _reconcile_previous_attempt(
        runtime_root=root, broker=clean_broker, store=store, accepted_commit="a" * 40)

    api = API(store, [{"position_quantity": 1}, {"position_quantity": 0}])
    broker = ControlledAcceptanceBroker(api, ACCOUNT, HASH, store)
    result = run_controlled_lifecycle(
        authority=authority(), runtime_root=root,
        execution_authorized=True, instrument="CNYRUBF", finam_symbol="CNYRUBF@RTSX",
        direction="LONG", broker=broker, now=NOW, sleeper=lambda _: None,
        attempt_id=STAGE8_11_ATTEMPT7_ID)

    assert result["classification"] == "SYNTHETIC_PASS"
    assert api.posts == 2
    assert not any(call[0] == "cancel" for call in api.calls)
    assert store.intent("stage8.11.attempt7:CNYRUBF:entry")["status"] == "RECONCILED"
    assert store.intent("stage8.11.attempt7:CNYRUBF:flatten")["status"] == "RECONCILED"
    assert store.unresolved_intent_count() == 0
