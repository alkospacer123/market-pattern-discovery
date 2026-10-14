"""Synthetic approval and physical callbacks. NEVER FINAM or real operator authority."""
from datetime import datetime, timezone, timedelta
from hashlib import sha256
import pytest

from TradingSystemLab.stage8_robot.diagnostics.stage8_493_operator_harness import Journal, Hold, Plan
from TradingSystemLab.stage8_robot.diagnostics.stage8_493_operator_write_gate import (
    OperatorOneAttemptWriteGate, SPEC, IDENTITY,
)

NOW=datetime(2026,10,14,8,0,tzinfo=timezone.utc)
ACCOUNT="synthetic-approved-account"
HASH=sha256(ACCOUNT.encode()).hexdigest()


def plan():
    return Plan(HASH,'CNYRUBF','CNYRUBF@RTSX','LONG','entry-A','stop-A','12.740')


def receipt():
    return {
        'schema':'stage8_493_operator_one_attempt_approval.v1',
        'production_specification_id':SPEC, 'active_identity':IDENTITY,
        'account_hash':HASH, 'instrument':'CNYRUBF', 'symbol':'CNYRUBF@RTSX',
        'direction':'LONG', 'quantity':2,
        'entry_key':'entry-A','stop_key':'stop-A','exit_key':'exit-A',
        'stop_price':'12.740','entry_reference':'12.990',
        'fees_rub':'10','slippage_ticks':3,'risk_budget_rub':'600',
        'approved_operations':['ENTRY','SLTP','CANCEL','EXIT'],
        'approved_from':(NOW-timedelta(minutes=2)).isoformat(),
        'approved_until':(NOW+timedelta(minutes=2)).isoformat(),
    }


def physical():
    return {
        'account_hash':HASH, 'task_disabled':True, 'switch_halted':True,
        'production_process_count':0, 'production_lock_free':True,
        'write_session_exact_account':True, 'broker_snapshot_age_seconds':0,
        'risk_and_margin_exact_two_current':True,
        'operator_budget_current_verified':True,
        'unresolved_intents_zero':True, 'recovery_approved':True,
    }


def gate(tmp_path, *, approval=None, phys=None, now=NOW, authorizer=True, physical_callback=True, existing=None):
    root=tmp_path/'one-operator-attempt'
    journal=Journal(root, fresh=existing is None) if existing is None else Journal(root,fresh=False)
    checker=(lambda _: approval if approval is not None else True) if authorizer else None
    checkphysical=(lambda: phys if phys is not None else physical()) if physical_callback else None
    g=OperatorOneAttemptWriteGate(plan=plan(),journal=journal,receipt=receipt(),
                                   verify_operator_approval=checker,
                                   verify_physical_authority=checkphysical,
                                   now=lambda:now)
    return g,journal


def test_strict_one_shot_with_durable_restart(tmp_path):
    g,j=gate(tmp_path)
    g('ENTRY',plan(),'entry-A')
    g('SLTP',plan(),'stop-A')
    assert j.count('operator_write_intent')==2
    with pytest.raises(Hold, match='ALREADY_CONSUMED'):
        g('ENTRY',plan(),'entry-A')
    fresh,_=gate(tmp_path,existing=True)
    with pytest.raises(Hold, match='ALREADY_CONSUMED'):
        fresh('ENTRY',plan(),'entry-A')
    assert j.count('operator_write_intent')==2
    assert all('account_id' not in str(v) and 'api_secret' not in str(v) for v in j.records)


def test_missing_authority_denies_without_journal(tmp_path):
    g,j=gate(tmp_path,authorizer=False)
    with pytest.raises(Hold,match='INDEPENDENT_APPROVAL'):
        g('ENTRY',plan(),'entry-A')
    assert not j.records


def test_missing_broker_and_host_callback_denies(tmp_path):
    g,j=gate(tmp_path,physical_callback=False)
    with pytest.raises(Hold,match='INDEPENDENT_APPROVAL'):
        g('ENTRY',plan(),'entry-A')
    assert not j.records


def test_rejected_operator_approval_denies(tmp_path):
    g,j=gate(tmp_path,approval=False)
    with pytest.raises(Hold,match='NOT_INDEPENDENTLY_VERIFIED'):
        g('ENTRY',plan(),'entry-A')
    assert not j.records


@pytest.mark.parametrize('key,value',[
    ('task_disabled',False),('switch_halted',False),
    ('production_process_count',1),('production_lock_free',False),
    ('write_session_exact_account',False),('broker_snapshot_age_seconds',20),
    ('risk_and_margin_exact_two_current',False),
    ('operator_budget_current_verified',False),('unresolved_intents_zero',False),
    ('recovery_approved',False),('account_hash','0'*64),
])
def test_bad_physical_gate_fails_closed(tmp_path,key,value):
    p=physical();p[key]=value
    g,j=gate(tmp_path,phys=p)
    with pytest.raises(Hold,match='PRECHECK_NOT_PASS'):
        g('ENTRY',plan(),'entry-A')
    assert not j.records


def test_expired_approval_denies(tmp_path):
    g,j=gate(tmp_path,now=NOW+timedelta(hours=1))
    with pytest.raises(Hold,match='EXPIRED'):
        g('ENTRY',plan(),'entry-A')
    assert not j.records


def test_only_exact_approved_entry_stop_exit_keys(tmp_path):
    g,j=gate(tmp_path)
    for action,key in [('ENTRY','evil'),('SLTP','evil'),('EXIT','evil')]:
        with pytest.raises(Hold,match='KEY_INVALID'):
            g(action,plan(),key)
    with pytest.raises(Hold,match='ENTRY_INTENT_NOT_PRESENT'):
        g('SLTP',plan(),'stop-A')
    g('ENTRY',plan(),'entry-A')
    with pytest.raises(Hold,match='PROTECTIVE_INTENT_NOT_PRESENT'):
        g('EXIT',plan(),'exit-A')
    g('SLTP',plan(),'stop-A')
    g('EXIT',plan(),'exit-A')
    assert [x['action'] for x in j.records]==['ENTRY','SLTP','EXIT']


def test_approval_binding_rejects_other_instrument(tmp_path):
    bad=receipt();bad['instrument']='USDRUBF'
    with pytest.raises(Hold,match='BINDING_INVALID'):
        OperatorOneAttemptWriteGate(plan=plan(), journal=Journal(tmp_path/'rejected',fresh=True),
                                    receipt=bad)


def test_stop_after_cancel_denied(tmp_path):
    g,j=gate(tmp_path)
    g('ENTRY',plan(),'entry-A')
    g('CANCEL',plan(),'entry-order-id')
    with pytest.raises(Hold,match='STOP_AFTER_RECOVERY'):
        g('SLTP',plan(),'stop-A')
    assert j.count('operator_write_intent')==2
