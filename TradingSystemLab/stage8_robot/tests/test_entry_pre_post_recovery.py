"""Offline ENTRY recovery at the actual transport preflight/endpoint boundary.

All authorization/session checks are in-memory test doubles. The API spy has no
network implementation. Candidate entry guards are patched only in this test
process to reach the otherwise closed, proposed submission path.
"""
from dataclasses import replace
from datetime import datetime, timedelta, timezone
from decimal import Decimal as D

import pytest

from TradingSystemLab.stage8_robot.execution_grid import EXECUTION_REVISION
from TradingSystemLab.stage8_robot.live_execution import AuthorizedFinamProductionTransport, LiveExecutionError
from TradingSystemLab.stage8_robot.production_service import ProductionService, Snapshot
from TradingSystemLab.stage8_robot.tests.test_stop_tick_grid_amendment import plan

ACCOUNT='synthetic-pre-post-account'
NOW=datetime(2026,1,2,7,1,tzinfo=timezone.utc)


class OfflineEntryAPI:
    """No HTTP client: records simulated endpoint invocation, never a real POST."""
    def __init__(self):
        self.calls=[]
        self.error=None
        self.response={'order_id':'synthetic-entry-ack'}
        self.before_call=None
    def place_order(self,account_id,payload):
        if self.before_call:self.before_call()
        self.calls.append((account_id,payload))
        if self.error:raise self.error
        return self.response


@pytest.fixture
def candidate(tmp_path,monkeypatch):
    import TradingSystemLab.stage8_robot.production_service as service_module
    import TradingSystemLab.stage8_robot.live_execution as transport_module
    monkeypatch.setattr(service_module,'FINAM_FILL_AUTHORITY_VERIFIED',True)
    monkeypatch.setattr(transport_module,'FINAM_FILL_AUTHORITY_VERIFIED',True)
    clock=[NOW]
    api=OfflineEntryAPI()
    services=[]
    def opened():
        svc=ProductionService(tmp_path,tmp_path/'data',api,ACCOUNT,'a'*40,
                              execution_revision=EXECUTION_REVISION,clock=lambda:clock[0])
        svc._require_entry_submission_session=lambda *args:None
        adapter=AuthorizedFinamProductionTransport.__new__(AuthorizedFinamProductionTransport)
        adapter.api=api;adapter.account_id=ACCOUNT
        adapter._require_entry_gate=lambda now:None
        svc.transport=adapter
        services.append(svc)
        return svc
    svc=opened();entry=plan(svc.runtime,cash=D('300'))
    snap=Snapshot({'account_id':ACCOUNT},{},[],D('100000'),D('1000000'),NOW)
    yield svc,api,clock,entry,snap,opened
    for service in services:service.close()


def refuse_before_endpoint(adapter):
    def closed(now):raise LiveExecutionError('SYNTHETIC_ENTRY_GATE_BLOCKED')
    adapter._require_entry_gate=closed


def test_proven_pre_post_refusal_consistent_then_restart_new_timestamp_one_post(candidate):
    svc,api,clock,entry,snap,opened=candidate
    refuse_before_endpoint(svc.transport)
    with pytest.raises(LiveExecutionError):svc._submit(entry,snap)
    assert api.calls==[]
    assert svc.runtime.store.intent(entry.idempotency_key)['status']=='INTENT_PERSISTED'
    assert svc.runtime.store.get(f'entry_submission:{entry.idempotency_key}') is None
    svc.close();svc=opened();clock[0]+=timedelta(seconds=3)
    svc._submit(entry,replace(snap,observed_at=clock[0]))
    assert len(api.calls)==1
    assert svc.runtime.store.intent(entry.idempotency_key)['status']=='ACK'
    assert svc.runtime.store.get(f'entry_submission:{entry.idempotency_key}')['submitted_at']==clock[0].isoformat()
    svc._submit(entry,snap)
    assert len(api.calls)==1
    svc.close()


def test_refusal_proof_is_retained_idempotently_and_cannot_release_later_attempt(candidate):
    svc,api,clock,entry,snap,opened=candidate
    refuse_before_endpoint(svc.transport)
    with pytest.raises(LiveExecutionError) as refusal:svc._submit(entry,snap)
    history_key=f'entry_pre_post_refusals:{entry.idempotency_key}'
    proof=svc.runtime.store.get(history_key)
    assert proof==[{'submission':{'account_sha256':svc.account_hash,'submitted_at':NOW.isoformat(),
                                'execution_revision':EXECUTION_REVISION},
                   'outcome':'ENTRY_POST_NOT_CALLED','reason':str(refusal.value)}]
    svc.runtime.restore_entry_pre_post(entry.idempotency_key,ACCOUNT,NOW.isoformat(),str(refusal.value))
    assert svc.runtime.store.get(history_key)==proof
    svc.close();svc=opened();clock[0]+=timedelta(seconds=3)
    svc.runtime.record_entry_submission(entry.idempotency_key,ACCOUNT,clock[0].isoformat())
    before=svc.runtime.store.get(f'entry_submission:{entry.idempotency_key}')
    with pytest.raises(RuntimeError,match='RECOVERY_AUTHORITY_MISMATCH'):
        svc.runtime.restore_entry_pre_post(entry.idempotency_key,ACCOUNT,NOW.isoformat(),str(refusal.value))
    assert svc.runtime.store.get(f'entry_submission:{entry.idempotency_key}')==before
    assert svc.runtime.store.intent(entry.idempotency_key)['status']=='SUBMITTED'
    assert svc.runtime.store.get(history_key)==proof and api.calls==[]
    svc.close()


def test_same_or_regressed_time_cannot_reuse_refusal_authority(candidate):
    svc,api,clock,entry,snap,opened=candidate
    refuse_before_endpoint(svc.transport)
    with pytest.raises(LiveExecutionError):svc._submit(entry,snap)
    for stamp in (NOW,NOW-timedelta(seconds=1)):
        with pytest.raises(RuntimeError,match='TIME_REUSED_OR_REGRESSED'):
            svc.runtime.record_entry_submission(entry.idempotency_key,ACCOUNT,stamp.isoformat())
    assert svc.runtime.store.intent(entry.idempotency_key)['status']=='INTENT_PERSISTED'
    assert svc.runtime.store.get(f'entry_submission:{entry.idempotency_key}') is None
    assert len(svc.runtime.store.get(f'entry_pre_post_refusals:{entry.idempotency_key}'))==1
    assert api.calls==[]


def test_repeated_reconcile_refusals_and_restarts_then_exactly_one_simulated_entry(candidate):
    svc,api,clock,entry,snap,opened=candidate
    for _ in range(3):
        refuse_before_endpoint(svc.transport)
        svc._reconcile_intents(replace(snap,observed_at=clock[0]))
        assert svc.runtime.store.intent(entry.idempotency_key)['status']=='INTENT_PERSISTED'
        assert svc.runtime.store.get(f'entry_submission:{entry.idempotency_key}') is None
        assert svc.runtime.store.get('execution_halt') is None
        svc.close();svc=opened();clock[0]+=timedelta(seconds=3)
    assert len(svc.runtime.store.get(f'entry_pre_post_refusals:{entry.idempotency_key}'))==3
    svc._reconcile_intents(replace(snap,observed_at=clock[0]))
    assert len(api.calls)==1
    for _ in range(2):
        svc.close();svc=opened();clock[0]+=timedelta(seconds=3)
        with pytest.raises(RuntimeError,match='HALTED'):svc._reconcile_intents(snap)
        svc._submit(entry,snap)
        assert len(api.calls)==1
    assert svc.runtime.store.intent(entry.idempotency_key)['status']=='ACK'
    svc.close()


@pytest.mark.parametrize('kind',['finam_uncertain','live_error','unknown_error','invalid_ack','forged_pre_post_marker'])
def test_possible_post_never_releases_authority_or_reposts_after_repeat_restart(candidate,kind):
    from TradingSystemLab.stage8_robot.finam_api import FinamUncertainSubmission
    from TradingSystemLab.stage8_robot.live_execution import EntryPrePostRefused
    svc,api,clock,entry,snap,opened=candidate
    if kind=='finam_uncertain':api.error=FinamUncertainSubmission('SYNTHETIC_UNKNOWN_POST')
    elif kind=='live_error':api.error=LiveExecutionError('SYNTHETIC_ERROR_AFTER_ENDPOINT_INVOCATION')
    elif kind=='unknown_error':api.error=ValueError('SYNTHETIC_BODY_DECODE_FAILURE')
    elif kind=='forged_pre_post_marker':api.error=EntryPrePostRefused('SYNTHETIC_MARKER_FROM_ENDPOINT')
    else:api.response={}
    with pytest.raises((RuntimeError,ValueError)):svc._submit(entry,snap)
    assert len(api.calls)==1
    original=svc.runtime.store.get(f'entry_submission:{entry.idempotency_key}')
    assert original['submitted_at']==NOW.isoformat()
    assert svc.runtime.store.get(f'entry_pre_post_refusals:{entry.idempotency_key}') is None
    assert svc.runtime.store.intent(entry.idempotency_key)['status']=='UNCERTAIN'
    assert svc.runtime.store.get('execution_halt')['operator_intervention_required'] is True
    for _ in range(3):
        svc.close();svc=opened();clock[0]+=timedelta(seconds=3)
        svc._submit(entry,snap)
        with pytest.raises(RuntimeError,match='HALTED'):svc._reconcile_intents(snap)
        assert len(api.calls)==1
        assert svc.runtime.store.get(f'entry_submission:{entry.idempotency_key}')==original
        assert svc.runtime.store.intent(entry.idempotency_key)['status']=='UNCERTAIN'
    svc.close()


def test_error_without_explicit_pre_post_contract_halts_even_if_spy_saw_zero_posts(candidate):
    svc,api,clock,entry,snap,opened=candidate
    def unclassified(now):raise RuntimeError('SYNTHETIC_UNCLASSIFIED_TRANSPORT_FAILURE')
    svc.transport._require_entry_gate=unclassified
    with pytest.raises(RuntimeError):svc._submit(entry,snap)
    assert api.calls==[]  # Observer knowledge must not be invented as runtime proof.
    assert svc.runtime.store.intent(entry.idempotency_key)['status']=='UNCERTAIN'
    assert svc.runtime.store.get(f'entry_submission:{entry.idempotency_key}') is not None
    assert svc.runtime.store.get(f'entry_pre_post_refusals:{entry.idempotency_key}') is None
    assert svc.runtime.store.get('execution_halt')['status']=='HALTED'


@pytest.mark.parametrize('boundary',['archive','active_release','intent_restore'])
def test_crash_during_refusal_recovery_rolls_back_and_restart_never_reposts(candidate,monkeypatch,boundary):
    svc,api,clock,entry,snap,opened=candidate
    refuse_before_endpoint(svc.transport)
    original_put=svc.runtime.store.put;original_transition=svc.runtime.store.transition_intent
    def crash_put(key,value):
        original_put(key,value)
        if boundary=='archive' and key.startswith('entry_pre_post_refusals:') or boundary=='active_release' and key.startswith('entry_submission:') and value is None:
            raise RuntimeError('SYNTHETIC_RECOVERY_CRASH')
    def crash_transition(key,status,*args):
        original_transition(key,status,*args)
        if status=='INTENT_PERSISTED':raise RuntimeError('SYNTHETIC_RECOVERY_CRASH')
    with monkeypatch.context() as patch:
        if boundary=='intent_restore':patch.setattr(svc.runtime.store,'transition_intent',crash_transition)
        else:patch.setattr(svc.runtime.store,'put',crash_put)
        with pytest.raises(RuntimeError,match='RECOVERY_CRASH'):svc._submit(entry,snap)
    assert api.calls==[]
    active=svc.runtime.store.get(f'entry_submission:{entry.idempotency_key}')
    assert active['submitted_at']==NOW.isoformat()
    assert svc.runtime.store.intent(entry.idempotency_key)['status']=='SUBMITTED'
    assert svc.runtime.store.get(f'entry_pre_post_refusals:{entry.idempotency_key}') is None
    assert svc.runtime.store.get('execution_halt')['status']=='HALTED'
    svc.close();svc=opened();clock[0]+=timedelta(seconds=3)
    svc._submit(entry,snap)
    with pytest.raises(RuntimeError,match='HALTED'):svc._reconcile_intents(snap)
    assert api.calls==[] and svc.runtime.store.get(f'entry_submission:{entry.idempotency_key}')==active
    svc.close()


@pytest.mark.parametrize('same_timestamp',[True,False])
def test_previous_inconsistent_persisted_intent_is_not_silently_repaired_or_posted(candidate,same_timestamp):
    svc,api,clock,entry,snap,opened=candidate
    svc.runtime.record_entry_submission(entry.idempotency_key,ACCOUNT,NOW.isoformat())
    svc.runtime.store.transition_intent(entry.idempotency_key,'INTENT_PERSISTED') # Previous audited defect.
    active=svc.runtime.store.get(f'entry_submission:{entry.idempotency_key}')
    svc.close();svc=opened()
    if not same_timestamp:clock[0]+=timedelta(seconds=3)
    with pytest.raises(RuntimeError,match='SUBMISSION_(STATUS_MISMATCH|ALREADY_COMMITTED)'):svc._submit(entry,snap)
    assert api.calls==[] and svc.runtime.store.get(f'entry_submission:{entry.idempotency_key}')==active
    assert svc.runtime.store.intent(entry.idempotency_key)['status']=='UNCERTAIN'
    assert svc.runtime.store.get('execution_halt')['status']=='HALTED'
    svc.close();svc=opened();svc._submit(entry,snap)
    assert api.calls==[]
    svc.close()


def test_submitted_before_transport_crash_retains_authority_after_restart(candidate):
    svc,api,clock,entry,snap,opened=candidate
    # Simulates process loss after durable SUBMITTED, before returning any proof.
    def process_loss(now):raise SystemExit('SYNTHETIC_PROCESS_LOSS')
    svc.transport._require_entry_gate=process_loss
    with pytest.raises(SystemExit):svc._submit(entry,snap)
    assert api.calls==[]
    active=svc.runtime.store.get(f'entry_submission:{entry.idempotency_key}')
    svc.close();svc=opened();clock[0]+=timedelta(seconds=3)
    with pytest.raises(RuntimeError,match='HALTED'):svc._reconcile_intents(snap)
    svc._submit(entry,snap)
    assert api.calls==[] and svc.runtime.store.get(f'entry_submission:{entry.idempotency_key}')==active
    assert svc.runtime.store.intent(entry.idempotency_key)['status']=='SUBMITTED'
    svc.close()


def test_submission_evidence_committed_before_simulated_endpoint_invocation(candidate):
    svc,api,clock,entry,snap,opened=candidate
    def durable_witness():
        import json,sqlite3
        # A separate connection cannot see uncommitted writes from StateStore.
        db=sqlite3.connect((svc.root/'state/stage8-12-production.sqlite3').as_uri()+'?mode=ro',uri=True)
        try:
            assert db.execute('SELECT status FROM intents WHERE idempotency_key=?',(entry.idempotency_key,)).fetchone()==('SUBMITTED',)
            raw=db.execute('SELECT value FROM state WHERE key=?',(f'entry_submission:{entry.idempotency_key}',)).fetchone()
            assert json.loads(raw[0])['submitted_at']==NOW.isoformat()
        finally:db.close()
    api.before_call=durable_witness
    svc._submit(entry,snap)
    assert len(api.calls)==1 and svc.runtime.store.intent(entry.idempotency_key)['status']=='ACK'


def test_repeated_reconcile_at_same_attempt_time_is_idempotent_across_restart(candidate):
    svc,api,clock,entry,snap,opened=candidate
    refuse_before_endpoint(svc.transport)
    svc._reconcile_intents(snap)
    original=svc.runtime.store.get(f'entry_pre_post_refusals:{entry.idempotency_key}')
    for _ in range(3):
        svc._reconcile_intents(snap)
        svc.close();svc=opened()
        svc._reconcile_intents(snap)
        assert svc.runtime.store.get('execution_halt') is None
        assert svc.runtime.store.intent(entry.idempotency_key)['status']=='INTENT_PERSISTED'
        assert svc.runtime.store.get(f'entry_submission:{entry.idempotency_key}') is None
        assert svc.runtime.store.get(f'entry_pre_post_refusals:{entry.idempotency_key}')==original
        assert api.calls==[]
    clock[0]+=timedelta(seconds=3)
    svc._submit(entry,replace(snap,observed_at=clock[0]))
    assert len(api.calls)==1
    svc.close()
