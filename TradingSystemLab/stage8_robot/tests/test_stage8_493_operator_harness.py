"""Offline tests of an injected fake port, NEVER FINAM or LIVE runtime."""
from __future__ import annotations
import importlib.util
from pathlib import Path
import pytest

p=Path(__file__).resolve().parents[1] / 'diagnostics' / 'stage8_493_operator_harness.py'
spec=importlib.util.spec_from_file_location('harness', p)
h=importlib.util.module_from_spec(spec)
import sys
sys.modules[spec.name]=h
spec.loader.exec_module(h)

HASH='a'*64


def plan():
    return h.Plan(HASH,'CNYRUBF','CNYRUBF@RTSX','LONG','entry-1','stop-1','12.740')


class Fake:
    def __init__(self, positions=(0,1,1,2)):
        self.positions=list(positions)
        self.actual=0
        self.entry_posts=0
        self.stop_posts=0
        self.entry_exception=None
        self.stop_exception=None
        self.stop_active=True
        self.remaining=0
        self.fills_valid=True
        self.stop_side='SIDE_SELL'
        self.stop_percent=100
        self.stop_price='12.740'
        self.auth_hash=HASH
        self.calls=[]

    def observe(self):
        if self.positions:
            self.actual=self.positions.pop(0)
        orders=[]
        if self.entry_posts:
            orders.append(dict(id='entry-id',kind='regular',active=False,remaining=self.remaining))
        if self.stop_posts:
            orders.append(dict(id='stop-id',kind='sltp',active=self.stop_active,remaining=0,
                side=self.stop_side, percent=self.stop_percent,price=self.stop_price,symbol='CNYRUBF@RTSX'))
        return {'account_hash':self.auth_hash, 'symbol':'CNYRUBF@RTSX',
                'position':self.actual,'other_positions':0,'orders':orders}

    def entry(self, *, key, symbol, side, quantity):
        self.calls.append(('entry',key,quantity))
        self.entry_posts+=1
        if self.entry_exception:
            raise RuntimeError('synthetic-transport')
        assert quantity==2 and side=='SIDE_BUY'
        return 'entry-id'

    def install_stop(self, *, key, symbol, side, price, percent):
        self.calls.append(('stop',key,percent))
        self.stop_posts+=1
        if self.stop_exception:
            raise RuntimeError('synthetic-transport')
        return 'stop-id'

    def fills(self, order_id):
        if not self.fills_valid:
            return []
        return [dict(order_id=order_id,account_hash=self.auth_hash,symbol='CNYRUBF@RTSX',
                     side='SIDE_BUY',trade_id=f'trade-{i}',quantity=1)
                for i in range(max(self.actual,0))]

    def cancel(self,order_id):
        self.calls.append(('cancel',order_id))
        raise AssertionError('cannot cancel')

    def exit(self,*,key,symbol,side,quantity):
        self.calls.append(('exit',key,quantity))
        raise AssertionError('cannot exit')


def new(tmp_path, broker=None):
    broker=broker or Fake()
    journal=h.Journal(tmp_path/'standalone-audit', fresh=True)
    return h.OperatorHarness(plan(),broker,journal),broker


def test_partial_growth_never_claims_live_proof(tmp_path):
    op,broker=new(tmp_path)
    assert op.entry_and_growth()=='STOP_AT_ONE_OBSERVED_GROWTH_PENDING'
    assert op.observe_growth()=='INCONCLUSIVE_REAL_STOP_TRIGGER_NOT_PROVEN'
    assert broker.entry_posts==1 and broker.stop_posts==1
    assert op.journal.count('growth_observed')==1
    assert op.journal.count('entry_intent')==1 and op.journal.count('stop_intent')==1
    assert op.recovery_precheck()['status']=='MANUAL_BROKER_TERMINAL_RECOVERY_REQUIRED'
    assert not any(c[0] in ('cancel','exit') for c in broker.calls)


def test_crash_restart_blocks_duplicate_post(tmp_path):
    op,b=new(tmp_path)
    op.entry_and_growth()
    recovered=h.Journal(op.journal.root, fresh=False)
    restarted=h.OperatorHarness(plan(),b,recovered)
    with pytest.raises(h.Hold,match='JOURNAL_ALREADY_USED_NO_REPLAY'):
        restarted.entry_and_growth()
    assert b.entry_posts==1


def test_immediate_fill_two_is_inconclusive_with_no_duplicate_order(tmp_path):
    op,b=new(tmp_path, Fake(positions=(0,2)))
    with pytest.raises(h.Hold,match='DIRECT_0_TO_2_INCONCLUSIVE'):
        op.entry_and_growth()
    assert b.entry_posts==1 and b.stop_posts==1
    assert op.journal.count('stop_intent')==1
    assert op.journal.value('stop_intent','after_quantity')==2
    assert op.journal.count('operator_hold')==1


@pytest.mark.parametrize('field', ['entry_exception','stop_exception'])
def test_unknown_post_response_is_sticky(tmp_path,field):
    b=Fake()
    setattr(b,field,True)
    op,b=new(tmp_path,b)
    with pytest.raises(h.Hold,match='UNKNOWN'):
        op.entry_and_growth()
    assert b.entry_posts==1 and b.stop_posts in (0,1)
    assert op.journal.count('operator_hold')==1
    with pytest.raises(h.Hold,match='NO_REPLAY'):
        op.entry_and_growth()
    assert b.entry_posts==1


@pytest.mark.parametrize('field,value', [('stop_percent',50),('stop_side','SIDE_BUY'),
                                         ('stop_active',False),('stop_price','12.700')])
def test_wrong_stop_cannot_pass_one_to_two(tmp_path,field,value):
    b=Fake()
    setattr(b,field,value)
    op,b=new(tmp_path,b)
    with pytest.raises(h.Hold,match='ACTIVE_SAME_SLTP'):
        op.entry_and_growth()
    assert b.stop_posts==1 and op.journal.count('operator_hold')==1


def test_broker_history_missing_prevents_stop(tmp_path):
    b=Fake();b.fills_valid=False
    op,b=new(tmp_path,b)
    with pytest.raises(h.Hold,match='FILL_HISTORY_MISSING'):
        op.entry_and_growth()
    assert b.stop_posts==0 and op.journal.count('operator_hold')==1


def test_account_identity_mismatch_blocks_entry(tmp_path):
    b=Fake();b.auth_hash='b'*64
    op,b=new(tmp_path,b)
    with pytest.raises(h.Hold,match='BROKER_OBSERVATION_INVALID'):
        op.entry_and_growth()
    assert b.entry_posts==0


def test_remaining_entry_blocks_manual_recovery(tmp_path):
    op,b=new(tmp_path)
    op.entry_and_growth()
    b.remaining=1
    with pytest.raises(h.Hold,match='ENTRY_REMAINDER'):
        op.recovery_precheck()
    assert not any(c[0]=='exit' for c in b.calls)


def test_double_final_flat_requires_no_live_stop(tmp_path):
    op,b=new(tmp_path)
    op.entry_and_growth()
    b.positions=[0,0]
    with pytest.raises(h.Hold,match='FINAL_FLAT_OR_ORDERS_NOT_PROVEN'):
        op.final_flat()
    b.stop_active=False
    b.positions=[0,0]
    assert op.final_flat()=='FLAT_AFTER_MANUAL_RECOVERY_NOT_PHYSICAL_SLTP_ACCEPTANCE'


def test_no_live_credential_or_order_endpoint_wiring():
    content=p.read_text('utf-8')
    for forbidden in ('import FinamAPI','from .finam_api','--execute','create_session(', 
                      'sqlite3.connect(', 'powershell.exe', 'write_kill_switch('):
        assert forbidden not in content
    assert 'NOT LIVE wired' in content


def test_invalid_plan_and_unsafe_journal(tmp_path):
    for item in [h.Plan(HASH,'NG','NG@RTSX','LONG','a','b','1'),
                 h.Plan(HASH,'CNYRUBF','CNYRUBF@RTSX','LONG','a','a','1'),
                 h.Plan(HASH,'CNYRUBF','CNYRUBF@RTSX','LONG','a','b','1',True)]:
        with pytest.raises(h.Hold): item.check()
    with pytest.raises(h.Hold,match='UNSAFE_JOURNAL_DIRECTORY'):
        h.Journal(tmp_path/'runtime'/'scratch',fresh=True)
