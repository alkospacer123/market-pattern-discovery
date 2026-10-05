"""Regression tests for Stage 8.11 attempt4 retry after attempt3 manual close."""
import hashlib
import json

from TradingSystemLab.stage8_robot.broker import OrderRequest
from TradingSystemLab.stage8_robot.controlled_real_acceptance import (
    ControlledAcceptanceBroker, STAGE8_11_ATTEMPT4_ID, run_controlled_lifecycle,
)
from TradingSystemLab.stage8_robot.specification import ACTIVE_IDENTITY, PRODUCTION_SPECIFICATION_ID
from TradingSystemLab.stage8_robot.stage8_11_physical_acceptance_attempt4 import (
    ATTEMPT_ID, ATTEMPT3_RECOVERY_EVIDENCE_NAME, ATTEMPT3_RECOVERY_SCHEMA,
    PREVIOUS_ENTRY_KEY, REPORT_NAME, _reconcile_previous_attempt,
)
from TradingSystemLab.stage8_robot.state import StateStore
from TradingSystemLab.stage8_robot.tests.test_controlled_real_acceptance import (
    ACCOUNT, API, HASH, NOW, armed_runtime, authority, fill,
)


class CleanRecoveredAccountAPI:
    def account(self, account_id):
        return {"positions": [{"symbol": "CNYRUBF@RTSX", "quantity": {"value": "0.0"}}]}

    def orders(self, account_id):
        return {"orders": [{"order_id": "attempt3-order", "status": "ORDER_STATUS_EXECUTED"}]}


def prepare_recovered_attempt3(root, store, monkeypatch, recovery_commit):
    from TradingSystemLab.stage8_robot import stage8_11_physical_acceptance_attempt4 as physical

    evidence = root / "diagnostics" / physical.PREVIOUS_REPORT_NAME
    evidence.parent.mkdir(parents=True, exist_ok=True)
    evidence.write_bytes(b"synthetic immutable attempt3 evidence\n")
    digest = hashlib.sha256(evidence.read_bytes()).hexdigest().upper()
    monkeypatch.setattr(physical, "PREVIOUS_EVIDENCE_SHA256", digest)

    payload = ControlledAcceptanceBroker._payload(
        OrderRequest(PREVIOUS_ENTRY_KEY, "CNYRUBF@RTSX", "LONG", 1))
    assert store.persist_intent(PREVIOUS_ENTRY_KEY, payload)
    store.transition_intent(PREVIOUS_ENTRY_KEY, "ACK", "attempt3-order")
    store.transition_intent(PREVIOUS_ENTRY_KEY, "CLOSED", "attempt3-order")

    recovery = root / "diagnostics" / ATTEMPT3_RECOVERY_EVIDENCE_NAME
    recovery.write_text(json.dumps({
        "schema_id": ATTEMPT3_RECOVERY_SCHEMA,
        "recovery_status": "COMMITTED",
        "attempt3_evidence_sha256": digest,
        "intent_key": PREVIOUS_ENTRY_KEY,
        "account_identity_sha256": HASH,
        "production_specification_id": PRODUCTION_SPECIFICATION_ID,
        "active_identity": ACTIVE_IDENTITY,
        "final_local_intent_status": "CLOSED",
        "attempt3_reclassified_as_pass": False,
        "manual_close_history_preserved": True,
        "physical_result_preserved": "OPERATOR_INTERVENTION_REQUIRED",
        "recovery_code_commit": recovery_commit,
    }))
    return digest


def test_attempt4_identity_and_evidence_path_are_fixed():
    assert ATTEMPT_ID == STAGE8_11_ATTEMPT4_ID == "stage8.11.attempt4"
    assert REPORT_NAME == "stage8_11_physical_acceptance_attempt4.json"


def test_attempt4_requires_committed_attempt3_manual_recovery(tmp_path, monkeypatch):
    root = tmp_path / "runtime"
    store = StateStore(tmp_path / "state.db")
    commit = "a" * 40
    prepare_recovered_attempt3(root, store, monkeypatch, commit)

    broker = ControlledAcceptanceBroker(CleanRecoveredAccountAPI(), ACCOUNT, HASH, store)
    _reconcile_previous_attempt(
        runtime_root=root, broker=broker, store=store, accepted_commit=commit)

    assert store.intent(PREVIOUS_ENTRY_KEY)["status"] == "CLOSED"
    assert store.unresolved_intent_count() == 0


def test_attempt4_full_retry_after_attempt3_manual_recovery(tmp_path, monkeypatch):
    root = armed_runtime(tmp_path)
    store = StateStore(tmp_path / "state.db")
    commit = "a" * 40
    prepare_recovered_attempt3(root, store, monkeypatch, commit)

    clean_broker = ControlledAcceptanceBroker(CleanRecoveredAccountAPI(), ACCOUNT, HASH, store)
    _reconcile_previous_attempt(
        runtime_root=root, broker=clean_broker, store=store, accepted_commit=commit)

    api = API(store, [fill("o1", 1), fill("o2", 0)])
    broker = ControlledAcceptanceBroker(api, ACCOUNT, HASH, store)
    result = run_controlled_lifecycle(
        authority=authority(), runtime_root=root,
        execution_authorized=True, instrument="CNYRUBF", finam_symbol="CNYRUBF@RTSX",
        direction="LONG", broker=broker, now=NOW, attempt_id=STAGE8_11_ATTEMPT4_ID)

    assert result["classification"] == "SYNTHETIC_PASS"
    assert api.posts == 2
    assert store.intent("stage8.11.attempt4:CNYRUBF:entry")["status"] == "RECONCILED"
    assert store.intent("stage8.11.attempt4:CNYRUBF:flatten")["status"] == "RECONCILED"
    assert store.unresolved_intent_count() == 0


def test_attempt4_wrapper_recovers_attempt3_before_trading_secret():
    import pathlib
    import TradingSystemLab.stage8_robot.stage8_11_physical_acceptance_attempt4 as physical

    wrapper = pathlib.Path(physical.__file__).parent / "deploy" / "windows" / "run-stage8-11-physical-acceptance-attempt4.ps1"
    source = wrapper.read_text(encoding="utf-8")
    recovery = source.index("stage8_11_attempt3_manual_close_recovery")
    trading_secret = source.index("$env:STAGE8_11_TRADING_SECRET")
    child = source.index("stage8_11_physical_acceptance_attempt4")
    assert recovery < trading_secret < child
    assert "--accepted-recovery-commit $AcceptedCommit" in source
