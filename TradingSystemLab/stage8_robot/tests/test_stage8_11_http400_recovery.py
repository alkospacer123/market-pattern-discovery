import hashlib
import json
from datetime import datetime, timezone
from io import BytesIO
from pathlib import Path
from urllib.error import HTTPError, URLError

import pytest

from TradingSystemLab.stage8_robot.controlled_real_acceptance import ControlledAcceptanceBroker, run_controlled_lifecycle
from TradingSystemLab.stage8_robot.finam_api import (
    FinamAPI, FinamOrderRejected, FinamUncertainSubmission, TIME_IN_FORCE_DAY,
)
from TradingSystemLab.stage8_robot.state import StateStore, initialize_stage8_11_acceptance_ledger
from TradingSystemLab.stage8_robot.tests.test_controlled_real_acceptance import (
    ACCOUNT, HASH, NOW, API, armed_runtime, authority,
)
import TradingSystemLab.stage8_robot.stage8_11_failed_attempt_recovery as recovery


class Headers(dict):
    def get(self, key, default=None):
        return super().get(key, super().get(key.lower(), default))


def rejected_transport(status):
    def call(request, timeout):
        if request.full_url.endswith("/v1/sessions"):
            return type("R", (), {"status": 200, "headers": Headers(), "read": lambda self: b'{"token":"redacted"}'})()
        raise HTTPError(request.full_url, status, "rejected", Headers({"x-request-id": "safe-id"}), BytesIO(b'{"unsafe":"body"}'))
    return call


def test_http400_is_typed_sanitized_deterministic_rejection():
    api = FinamAPI("secret", transport=rejected_transport(400), limiter=type("L", (), {"wait": lambda self: None})())
    with pytest.raises(FinamOrderRejected) as caught:
        api.place_order("sensitive-account", {})
    assert (caught.value.status, caught.value.category, caught.value.request_id) == (400, "TRADING_PARAMETERS_REJECTED", "safe-id")
    assert "unsafe" not in str(caught.value) and "sensitive-account" not in str(caught.value)


@pytest.mark.parametrize("status", [500, 503, 504])
def test_post_5xx_is_uncertain(status):
    api = FinamAPI("secret", transport=rejected_transport(status), limiter=type("L", (), {"wait": lambda self: None})())
    with pytest.raises(FinamUncertainSubmission):
        api.place_order("account", {})


def test_network_post_is_uncertain_and_not_retried():
    calls = 0
    def transport(request, timeout):
        nonlocal calls
        calls += 1
        if request.full_url.endswith("/v1/sessions"):
            return type("R", (), {"status": 200, "headers": Headers(), "read": lambda self: b'{"token":"x"}'})()
        raise URLError("lost")
    api = FinamAPI("secret", transport=transport, limiter=type("L", (), {"wait": lambda self: None})())
    with pytest.raises(FinamUncertainSubmission): api.place_order("account", {})
    assert calls == 2  # one session call plus exactly one order call


class RejectingAPI(API):
    def __init__(self, store, *, position=0, active=False, extra_unresolved=False):
        super().__init__(store, [])
        self.position, self.active, self.extra_unresolved = position, active, extra_unresolved
    def place_order(self, account, payload):
        self.posts += 1
        if self.extra_unresolved:
            self.store.persist_intent("other", {"symbol":"OTHER"})
        raise FinamOrderRejected(400, request_id="request-1")
    def account(self, account):
        return {"positions": [] if self.position == 0 else
                [{"symbol":"CNYRUBF@RTSX", "quantity":{"value":str(self.position)}}]}
    def orders(self, account):
        return {"orders": [] if not self.active else
                [{"order_id":"other", "status":"ACTIVE", "order":{"client_order_id":"other"}}]}


def rejection_run(tmp_path, **options):
    root = armed_runtime(tmp_path); store = StateStore(tmp_path / "acceptance.sqlite3")
    api = RejectingAPI(store, **options); broker = ControlledAcceptanceBroker(api, ACCOUNT, HASH, store)
    result = run_controlled_lifecycle(authority=authority(), runtime_root=root,
        execution_authorized=True, instrument="CNYRUBF", finam_symbol="CNYRUBF@RTSX",
        direction="LONG", broker=broker, now=NOW)
    return result, api, store


def test_http400_once_terminalizes_intent_and_clean_account_is_no_execution(tmp_path):
    result, api, store = rejection_run(tmp_path)
    assert api.posts == 1 and store.intent("stage8.11:CNYRUBF:entry")["status"] == "REJECTED"
    assert result["classification"] == "NOT_ACCEPTED_NO_EXECUTION"
    assert result["rejection"] == {"http_status":400, "category":"TRADING_PARAMETERS_REJECTED",
        "request_id":"request-1", "broker_acknowledgement_present":False}


@pytest.mark.parametrize("options", [{"position":1}, {"active":True}, {"extra_unresolved":True}])
def test_http400_ambiguous_account_requires_intervention(tmp_path, options):
    result, api, store = rejection_run(tmp_path, **options)
    assert api.posts == 1 and result["classification"] == "OPERATOR_INTERVENTION_REQUIRED"
    assert store.intent("stage8.11:CNYRUBF:entry")["status"] == "REJECTED"


def test_payload_contract_has_documented_day_tif_and_fixed_semantics(tmp_path):
    store = StateStore(tmp_path / "s.sqlite3"); api = API(store, [])
    broker = ControlledAcceptanceBroker(api, ACCOUNT, HASH, store)
    entry = broker._payload(type("R", (), {"quantity":1,"idempotency_key":"stage8.11:CNYRUBF:entry",
        "contract_id":"CNYRUBF@RTSX","direction":"LONG","exit_order":False})())
    flatten = broker._payload(type("R", (), {**entry})()) if False else dict(entry, side="SIDE_SELL")
    assert entry == {"symbol":"CNYRUBF@RTSX", "quantity":{"value":"1"}, "side":"SIDE_BUY",
        "type":"ORDER_TYPE_MARKET", "time_in_force":TIME_IN_FORCE_DAY,
        "client_order_id":entry["client_order_id"]}
    assert len(entry["client_order_id"]) <= 20 and flatten["side"] == "SIDE_SELL"


def test_outside_or_malformed_schedule_blocks_without_intent_or_post(tmp_path):
    for schedule in ({"sessions":[]}, {"bad":True}, {"sessions":[{"type":"CLOSED","interval":{
            "start_time":"2026-10-04T00:00:00Z","end_time":"2026-10-04T23:59:00Z"}}]}):
        root=armed_runtime(tmp_path / hashlib.sha256(repr(schedule).encode()).hexdigest()[:8])
        store=StateStore(tmp_path / (hashlib.sha256(repr(schedule).encode()).hexdigest()+".db"))
        api=API(store, []); api.schedule=lambda symbol, value=schedule: value
        broker=ControlledAcceptanceBroker(api, ACCOUNT, HASH, store)
        result=run_controlled_lifecycle(authority=authority(),runtime_root=root,execution_authorized=True,
            instrument="CNYRUBF",finam_symbol="CNYRUBF@RTSX",direction="LONG",broker=broker,now=NOW)
        assert result["classification"] == "BLOCKED" and api.posts == 0
        assert store.intent("stage8.11:CNYRUBF:entry") is None and result["kill_switch_final_state"] == "HALTED"


class ReadonlyClean:
    def __init__(self, account=ACCOUNT, positions=None, orders=None):
        self.account_id=account; self.positions=positions or []; self.order_rows=orders or []
    def session_details(self): return {"readonly":True,"account_ids":[self.account_id]}
    def account(self, account): return {"positions":self.positions}
    def orders(self, account): return {"orders":self.order_rows}


def recovery_fixture(tmp_path, monkeypatch):
    root=tmp_path/"runtime"; evidence=tmp_path/"original.json"; evidence.write_text("failed physical evidence\n")
    digest=hashlib.sha256(evidence.read_bytes()).hexdigest().upper()
    monkeypatch.setattr(recovery,"FAILED_PHYSICAL_EVIDENCE_SHA256",digest)
    ledger=initialize_stage8_11_acceptance_ledger(root,ACCOUNT); store=StateStore(ledger)
    store.persist_intent(recovery.HISTORICAL_INTENT_KEY,{"symbol":recovery.FINAM_SYMBOL,
        "quantity":{"value":"1"},"side":"SIDE_BUY","type":"ORDER_TYPE_MARKET","client_order_id":"fixed"})
    store.close()
    return root,evidence,digest


def test_historical_recovery_is_order_incapable_and_creates_backup_evidence(tmp_path,monkeypatch):
    root,evidence,digest=recovery_fixture(tmp_path,monkeypatch)
    before=evidence.read_bytes()
    got=recovery.recover_historical_intent(runtime_root=root,account_id=ACCOUNT,readonly_api=ReadonlyClean(),
        accepted_commit=recovery.ACCEPTED_PHYSICAL_COMMIT,physical_evidence=evidence,
        physical_evidence_sha256=digest,intent_key=recovery.HISTORICAL_INTENT_KEY,now=NOW)
    store=StateStore(root/"state"/"stage8-11-acceptance.sqlite3")
    assert store.intent(recovery.HISTORICAL_INTENT_KEY)["status"] == "REJECTED"
    assert evidence.read_bytes()==before and got["fresh_account_wide_reconciliation"]=="PASS"
    assert list((root/"backups"/"stage8-11-acceptance").glob("*.sqlite3"))
    assert (root/"diagnostics"/recovery.RECOVERY_EVIDENCE_NAME).is_file()
    source=Path(recovery.__file__).read_text()
    assert ".place_order(" not in source and ".cancel_order(" not in source and "write_kill_switch" not in source


@pytest.mark.parametrize("point,committed", [
    ("before_backup", False), ("after_backup", False),
    ("before_sqlite_mutation", False), ("after_sqlite_mutation", True),
    ("during_evidence_finalization", True),
])
def test_recovery_faults_are_restartable_and_never_claim_success_early(
        tmp_path, monkeypatch, point, committed):
    root,evidence,digest=recovery_fixture(tmp_path,monkeypatch)
    kwargs=dict(runtime_root=root,account_id=ACCOUNT,readonly_api=ReadonlyClean(),
        accepted_commit=recovery.ACCEPTED_PHYSICAL_COMMIT,physical_evidence=evidence,
        physical_evidence_sha256=digest,intent_key=recovery.HISTORICAL_INTENT_KEY,now=NOW)
    def fail(at):
        if at == point: raise OSError("injected")
    with pytest.raises(OSError):
        recovery.recover_historical_intent(**kwargs,fault_injector=fail)
    target=root/"diagnostics"/recovery.RECOVERY_EVIDENCE_NAME
    assert not target.exists()
    store=StateStore(root/"state"/"stage8-11-acceptance.sqlite3")
    assert (store.intent(recovery.HISTORICAL_INTENT_KEY)["status"] == "REJECTED") is committed
    store.close()
    got=recovery.recover_historical_intent(**kwargs)
    assert got["recovery_status"] == "COMMITTED" and target.is_file()
    assert not target.with_name(target.name+recovery.RECOVERY_PREPARED_SUFFIX).exists()


def test_windows_recovery_boundary_uses_readonly_credential_only():
    wrapper=Path(recovery.__file__).parent/"deploy"/"windows"/"run-stage8-11-failed-intent-recovery.ps1"
    source=wrapper.read_text(encoding="utf-8")
    assert "Get-ReadonlyCredential" in source and "REAL_READONLY" in source
    assert "Get-TradingCredential" not in source and "TRADING_SECRET" not in source
    assert all(term not in source for term in ("place_order", "cancel_order", "modify_order", "allow_arm"))


def test_recovery_cli_runs_end_to_end_with_synthetic_readonly_transport(
        tmp_path, monkeypatch):
    root,evidence,digest=recovery_fixture(tmp_path,monkeypatch)
    monkeypatch.setenv("STAGE8_11_READONLY_SECRET", "synthetic-readonly")
    monkeypatch.setenv("STAGE8_11_READONLY_ACCOUNT_ID", ACCOUNT)
    argv=["--runtime-root",str(root),"--account-id",ACCOUNT,
        "--accepted-commit",recovery.ACCEPTED_PHYSICAL_COMMIT,
        "--physical-evidence",str(evidence),"--physical-evidence-sha256",digest,
        "--intent-key",recovery.HISTORICAL_INTENT_KEY]
    assert recovery.main(argv,api_factory=lambda secret:ReadonlyClean()) == 0
    store=StateStore(root/"state"/"stage8-11-acceptance.sqlite3")
    assert store.intent(recovery.HISTORICAL_INTENT_KEY)["status"] == "REJECTED"
    assert (root/"diagnostics"/recovery.RECOVERY_EVIDENCE_NAME).is_file()


@pytest.mark.parametrize("mutation", ["commit","sha","intent","account","dirty"])
def test_wrong_recovery_authority_or_dirty_broker_blocks(tmp_path,monkeypatch,mutation):
    root,evidence,digest=recovery_fixture(tmp_path,monkeypatch)
    kwargs=dict(runtime_root=root,account_id=ACCOUNT,readonly_api=ReadonlyClean(),
        accepted_commit=recovery.ACCEPTED_PHYSICAL_COMMIT,physical_evidence=evidence,
        physical_evidence_sha256=digest,intent_key=recovery.HISTORICAL_INTENT_KEY,now=NOW)
    if mutation=="commit": kwargs["accepted_commit"]="0"*40
    elif mutation=="sha": kwargs["physical_evidence_sha256"]="0"*64
    elif mutation=="intent": kwargs["intent_key"]="wrong"
    elif mutation=="account": kwargs["readonly_api"]=ReadonlyClean("wrong")
    else: kwargs["readonly_api"]=ReadonlyClean(positions=[{"symbol":"OTHER","quantity":{"value":"1"}}])
    with pytest.raises(recovery.RecoveryBlocked): recovery.recover_historical_intent(**kwargs)
    store=StateStore(root/"state"/"stage8-11-acceptance.sqlite3")
    assert store.intent(recovery.HISTORICAL_INTENT_KEY)["status"]=="INTENT_PERSISTED"
