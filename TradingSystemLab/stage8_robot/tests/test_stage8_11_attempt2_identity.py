"""Attempt-2 provenance and immutable-evidence regression tests."""
import hashlib
import json

import pytest

from TradingSystemLab.stage8_robot.controlled_real_acceptance import (
    AcceptanceBlocked, ControlledAcceptanceBroker, STAGE8_11_ATTEMPT2_ID,
    run_controlled_lifecycle,
)
from TradingSystemLab.stage8_robot.stage8_11_failed_attempt_recovery import (
    FAILED_PHYSICAL_EVIDENCE_SHA256, HISTORICAL_INTENT_KEY,
)
from TradingSystemLab.stage8_robot.stage8_11_physical_acceptance import (
    ATTEMPT_ID, AUTHORIZATION_VALUE, HISTORICAL_REPORT_NAME, REPORT_NAME,
    PhysicalAcceptanceBlocked, _write_new, execute_boundary,
)
from TradingSystemLab.stage8_robot.state import (
    StateStore, initialize_stage8_11_acceptance_ledger,
)
from TradingSystemLab.stage8_robot.tests.test_controlled_real_acceptance import (
    ACCOUNT, API, HASH, NOW, armed_runtime, authority, fill,
)


def _historical_rejected(store: StateStore) -> tuple:
    payload = {"symbol": "CNYRUBF@RTSX", "side": "SIDE_BUY", "quantity": {"value": "1"}}
    assert store.persist_intent(HISTORICAL_INTENT_KEY, payload)
    store.transition_intent(HISTORICAL_INTENT_KEY, "REJECTED")
    return store.db.execute("SELECT * FROM intents WHERE idempotency_key=?",
                            (HISTORICAL_INTENT_KEY,)).fetchone()


def test_attempt2_keys_coexist_with_immutable_historical_rejection(tmp_path):
    root = armed_runtime(tmp_path)
    store = StateStore(tmp_path / "state.db")
    before = _historical_rejected(store)
    api = API(store, [fill("o1", 1), fill("o2", 0)])
    broker = ControlledAcceptanceBroker(api, ACCOUNT, HASH, store)

    result = run_controlled_lifecycle(
        authority=authority(), runtime_root=root, execution_authorized=True,
        instrument="CNYRUBF", finam_symbol="CNYRUBF@RTSX", direction="LONG",
        broker=broker, now=NOW, attempt_id=STAGE8_11_ATTEMPT2_ID)

    assert result["classification"] == "SYNTHETIC_PASS"
    assert store.db.execute("SELECT * FROM intents WHERE idempotency_key=?",
                            (HISTORICAL_INTENT_KEY,)).fetchone() == before
    assert store.intent("stage8.11.attempt2:CNYRUBF:entry")["status"] == "RECONCILED"
    assert store.intent("stage8.11.attempt2:CNYRUBF:flatten")["status"] == "RECONCILED"
    assert store.unresolved_intent_count() == 0


def test_global_unresolved_count_includes_historical_and_attempt2_rows(tmp_path):
    store = StateStore(tmp_path / "state.db")
    _historical_rejected(store)
    assert store.persist_intent("stage8.11.attempt2:CNYRUBF:entry", {"fixed": True})
    assert store.unresolved_intent_count() == 1
    assert store.persist_intent("historical:unresolved", {"fixed": True})
    assert store.unresolved_intent_count() == 2
    store.close()


@pytest.mark.parametrize("key", ["historical:unresolved", "stage8.11.attempt2:CNYRUBF:entry"])
def test_physical_precheck_blocks_any_global_unresolved_intent(tmp_path, monkeypatch, key):
    from TradingSystemLab.stage8_robot import stage8_11_physical_acceptance as physical
    root = tmp_path / "runtime"
    from TradingSystemLab.stage8_robot.trading_safety_gate import write_kill_switch
    write_kill_switch(root, "HALTED", now=NOW)
    report = root / "diagnostics" / physical.PRECHECK_REPORT_NAME
    report.parent.mkdir(parents=True)
    report.write_bytes(b"fixed-precheck")
    digest = hashlib.sha256(report.read_bytes()).hexdigest().upper()
    monkeypatch.setattr(physical, "PRECHECK_EVIDENCE_SHA256", digest)
    monkeypatch.setattr(physical, "stage8_10_authority_complete", lambda: True)
    store = StateStore(initialize_stage8_11_acceptance_ledger(root, ACCOUNT))
    store.persist_intent(key, {"fixed": True})
    store.close()
    api = type("NoPost", (), {"posts": 0, "place_order": lambda self, *a, **k: None})()
    with pytest.raises(PhysicalAcceptanceBlocked, match="UNRESOLVED_INTENTS_PRESENT"):
        execute_boundary(accepted_commit="a" * 40, authorization=AUTHORIZATION_VALUE,
            account_id=ACCOUNT, api=api, runtime_root=root,
            external_evidence_sha256=digest, now=NOW)
    assert api.posts == 0


def test_attempt_identity_is_repository_fixed(tmp_path):
    store = StateStore(tmp_path / "state.db")
    broker = ControlledAcceptanceBroker(API(store, []), ACCOUNT, HASH, store)
    with pytest.raises(AcceptanceBlocked, match="ATTEMPT_ID_INVALID"):
        run_controlled_lifecycle(authority=authority(), runtime_root=armed_runtime(tmp_path),
            execution_authorized=True, instrument="CNYRUBF", finam_symbol="CNYRUBF@RTSX",
            direction="LONG", broker=broker, now=NOW, attempt_id="operator-choice")
    assert ATTEMPT_ID == "stage8.11.attempt2"


def test_attempt2_evidence_is_separate_create_only_file(tmp_path):
    diagnostics = tmp_path / "diagnostics"
    diagnostics.mkdir()
    historical = diagnostics / HISTORICAL_REPORT_NAME
    historical.write_bytes(b"immutable-attempt-one\n")
    before = hashlib.sha256(historical.read_bytes()).hexdigest()
    attempt2 = diagnostics / REPORT_NAME
    payload = {"attempt_id": ATTEMPT_ID, "marker": 2}
    _write_new(payload, attempt2)
    first = attempt2.read_bytes()
    with pytest.raises(PhysicalAcceptanceBlocked, match="EVIDENCE_ALREADY_EXISTS"):
        _write_new({"attempt_id": ATTEMPT_ID, "marker": 3}, attempt2)
    assert attempt2.read_bytes() == first
    assert hashlib.sha256(historical.read_bytes()).hexdigest() == before
    assert REPORT_NAME == "stage8_11_physical_acceptance_attempt2.json"
    assert FAILED_PHYSICAL_EVIDENCE_SHA256 == (
        "9FEFC5469F2C97F1EB36A5B5C99D323FA37BB948CF53C8A8745A27A06AB3B324")


def test_attempt2_pass_evidence_requires_global_unresolved_zero():
    from TradingSystemLab.stage8_robot.controlled_real_acceptance import sanitized_evidence
    facts = dict(attempt_id=ATTEMPT_ID, accepted_code_commit="a" * 40,
        sanitized_account_identity_hash="b" * 64, instrument="CNYRUBF", direction="LONG",
        quantity=1, preflight_gate_outcomes={}, kill_switch_pre_state="ARMED",
        kill_switch_final_state="HALTED", execution_authorization_observed=True,
        order_endpoint_call_count=2, broker_order_present=True, broker_fill_count=2,
        entry_fill_proven=True, one_contract_position_observed=True,
        controlled_flatten_proven=True, final_position_quantity=0,
        final_active_order_count=0, unresolved_intent_count=1,
        reconciliation_result="PASS", physical_result_classification="PASS",
        external_raw_evidence_sha256="c" * 64)
    with pytest.raises(ValueError, match="PASS_EVIDENCE_INVARIANTS_INVALID"):
        sanitized_evidence(**facts)
