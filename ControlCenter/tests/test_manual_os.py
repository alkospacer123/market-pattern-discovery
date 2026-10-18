"""Manual C boundary, independent of producer/publisher and physical A approval."""
from copy import deepcopy
from datetime import datetime, timedelta, timezone
import json
from pathlib import Path
import subprocess
import sys
import pytest
from cc.models import RobotId, SourceKind, State
from cc.providers import h1_windows_os as manual
from cc.providers import h1_export as receiver
from observer import windows_os as observer
from test_os_observer import os_policy


@pytest.fixture
def manual_policy(os_policy):
    return dict(schema_id='cc03.manual-os-policy.v1', manual_source_approved=True,
        **{k: os_policy[k] for k in ('source_id','account_alias','binding_id','observer_sid',
                                  'task_name','task_xml_sha256','task_principal_sid')},
        process_binding=None, snapshot_ttl_seconds=30, os_ttl_seconds=15)


def facts(p):
    return dict(task=observer.row('WINDOWS_TASK_READONLY','TASK_RUNNING','OK',p['task_xml_sha256']),
                process=observer.row('WINDOWS_PROCESS_READONLY',reason='DISABLED'))


def wire(monkeypatch, p, probe=facts):
    monkeypatch.setattr(manual, 'installed_policy', lambda: manual.policy_check(deepcopy(p)))
    monkeypatch.setattr(manual, 'current_identity', lambda: (p['observer_sid'],False))
    monkeypatch.setattr(manual, 'os_facts', probe)


def click():
    return manual.manual_os_refresh(datetime.now(timezone.utc))


def test_one_click_one_diagnostic_no_publication_and_unknown_authorities(manual_policy, monkeypatch):
    calls=[]
    def probe(p):
        calls.append(p)
        return facts(p)
    wire(monkeypatch,manual_policy,probe)
    monkeypatch.setattr(receiver,'read_latest_windows',lambda *a:pytest.fail('export read'))
    monkeypatch.setattr(subprocess,'Popen',lambda *a,**k:pytest.fail('unexpected child'))
    result,accepted=click()
    assert accepted and len(calls)==1
    assert calls[0]['require_ccpanel'] is True and not calls[0]['process_enabled']
    assert result.status.provenance.source_kind==SourceKind.WINDOWS_OS_ONLY
    assert result.status.task_state=='TASK_RUNNING' and result.status.state==State.UNKNOWN
    assert result.status.heartbeat_at is None and result.status.trading_allowed is None
    assert result.positions is None and result.trades is None and result.portfolio.equity is None
    assert not result.candles and not result.orders and not result.signals
    assert 'source/account UNVERIFIED' in result.readonly_identity
    assert result.windows_observations[1].state=='UNKNOWN'
    assert result.readonly_expires_at==result.windows_observations[0].observed_at+timedelta(seconds=15)


@pytest.mark.parametrize('key,bad', [('schema_id','cc03.intel-preflight-policy.v2'),
    ('schema_id','cc03.os-policy.v1'),('manual_source_approved',False),('task_name','arbitrary'),
    ('observer_sid','S-1-5-18'),('task_xml_sha256','bad'),('binding_id',None),('source_id','OTHER'),
    ('account_alias','DEMO-H1'),('os_ttl_seconds',None),('os_ttl_seconds',True),
    ('snapshot_ttl_seconds',0),('snapshot_ttl_seconds',86401),('process_binding',{}),
    ('task_principal_sid','S-1-5-21-1-2-3-1001')])
def test_bad_policy_before_identity_or_probe(manual_policy,monkeypatch,key,bad):
    manual_policy[key]=bad
    wire(monkeypatch,manual_policy,lambda p:pytest.fail('probe on bad policy'))
    monkeypatch.setattr(manual,'current_identity',lambda:pytest.fail('identity on bad policy'))
    s,accepted=click()
    assert not accepted and s.status.task_state is None and not s.windows_observations


@pytest.mark.parametrize('raw', ['{}','{"schema_id":"a","schema_id":"b"}', 'NaN', '[]'])
def test_policy_parse_failure_before_probe(monkeypatch,raw):
    seen=[]
    def read(*a,**k): seen.append((a,k));return raw.encode()
    monkeypatch.setattr(manual,'read_windows',read)
    monkeypatch.setattr(manual,'os_facts',lambda p:pytest.fail('probe on invalid JSON'))
    assert not click()[1]
    assert seen==[((str(manual.POLICY_ROOT),'manual-os-policy.json',16384),{'admin_policy':True})]
    assert 'private' not in str(manual.POLICY_ROOT)


@pytest.mark.parametrize('unsafe,sid', [(True,None),(False,'S-1-5-21-9-9-9-1009')])
def test_wrong_or_elevated_primary_identity_before_probe(manual_policy,monkeypatch,unsafe,sid):
    wire(monkeypatch,manual_policy,lambda p:pytest.fail('probe on wrong identity'))
    monkeypatch.setattr(manual,'current_identity',lambda:(sid or manual_policy['observer_sid'],unsafe))
    assert not click()[1]


@pytest.mark.parametrize('kind', ['incomplete','forged_task','forged_process','future','old','extra','task_unknown','reason'])
def test_incomplete_or_forged_result_clears_values(manual_policy,monkeypatch,kind):
    def bad(p):
        rows=facts(p)
        if kind=='incomplete':del rows['process']
        elif kind=='forged_task':rows['task']['value']='0'*64
        elif kind=='forged_process':rows['process']=observer.row('WINDOWS_PROCESS_READONLY','PROCESS_OBSERVED','OK','0'*64)
        elif kind=='future':rows['task']['observed_at']=(datetime.now(timezone.utc)+timedelta(days=1)).isoformat()
        elif kind=='old':rows['task']['observed_at']=(datetime.now(timezone.utc)-timedelta(days=1)).isoformat()
        elif kind=='extra':rows['heartbeat']=rows['task']
        elif kind=='reason':rows['task']['reason']='NOT_FOUND'
        else:
            rows['task']=observer.row('WINDOWS_TASK_READONLY',reason='CHANGED')
            rows['process']=observer.row('WINDOWS_PROCESS_READONLY','PROCESS_OBSERVED','OK','0'*64)
        return rows
    wire(monkeypatch,manual_policy,bad)
    result,accepted=click()
    assert not accepted and result.status.state==State.UNKNOWN and not result.windows_observations


@pytest.mark.parametrize('reason',['NOT_FOUND','IDENTITY_MISMATCH','ACCESS_DENIED','TIMEOUT','CHANGED'])
def test_unknown_task_never_claims_absence_or_health(manual_policy,monkeypatch,reason):
    wire(monkeypatch,manual_policy,lambda p:dict(task=observer.row('WINDOWS_TASK_READONLY',reason=reason),
                                             process=observer.row('WINDOWS_PROCESS_READONLY',reason='DISABLED')))
    s,accepted=click()
    assert accepted and s.status.task_state is None and s.status.state==State.UNKNOWN
    assert s.windows_observations[0].reason==reason and s.status.heartbeat_at is None


def test_approved_pid_only_and_wrong_process_hash_rejected(manual_policy,os_policy,monkeypatch):
    manual_policy['process_binding']={k:os_policy[k] for k in manual.PROCESS_KEYS}
    def present(p):
        assert p['process_enabled'] and p['process_pid']==12345
        rows=facts(p)
        rows['process']=observer.row('WINDOWS_PROCESS_READONLY','PROCESS_OBSERVED','OK',p['process_command_sha256'])
        return rows
    wire(monkeypatch,manual_policy,present)
    assert click()[0].windows_observations[1].state=='PROCESS_OBSERVED'
    def wrong(p):
        rows=present(p);rows['process']['value']='0'*64;return rows
    monkeypatch.setattr(manual,'os_facts',wrong)
    assert not click()[1]


def test_ttl_and_clock_rollback_without_new_io(manual_policy,monkeypatch):
    wire(monkeypatch,manual_policy)
    s,_=click()
    monkeypatch.setattr(manual,'installed_policy',lambda:pytest.fail('TTL policy I/O'))
    monkeypatch.setattr(manual,'os_facts',lambda p:pytest.fail('TTL diagnostic'))
    for now,state in [(s.readonly_expires_at, 'CURRENT'),(s.readonly_expires_at+timedelta(microseconds=1),'STALE'),
                      (s.status.provenance.received_at-timedelta(seconds=1),'UNKNOWN')]:
        aged=receiver.age_export_snapshot(s,now)
        assert aged.windows_observations[0].freshness==state
        assert aged.status.provenance==s.status.provenance
        if state!='CURRENT':assert aged.status.task_state is None


def test_startup_reruns_switches_and_m15_zero_calls_click_failure_clears_cache(manual_policy,monkeypatch):
    from streamlit.testing.v1 import AppTest
    from cc.ui import PAGES
    calls=[]
    def probe(p): calls.append(p);return facts(p)
    wire(monkeypatch,manual_policy,probe)
    app=AppTest.from_file(str(Path(__file__).parents[1]/'app.py'),default_timeout=15).run()
    app.selectbox(key='h1-source').select('WINDOWS_OS_ONLY').run()
    for page in PAGES:app.radio[0].set_value(page).run()
    app.run()
    assert not app.exception and not calls
    app.radio[0].set_value('Монитор H1').run()
    app.button(key='cc03-manual-refresh').click().run()
    assert len(calls)==1 and not app.exception
    assert app.session_state['cc03-last-export'].status.task_state=='TASK_RUNNING'
    for page in PAGES:app.radio[0].set_value(page).run()
    assert len(calls)==1 and not app.exception
    controls=[b for b in app.button if b.key!='cc03-manual-refresh']
    # Check controls on the actual controls page, independent of current PAGES order.
    app.radio[0].set_value('Управление').run()
    assert len([b for b in app.button if b.key!='cc03-manual-refresh' and b.disabled])==10
    monkeypatch.setattr(manual,'installed_policy',lambda:(_ for _ in ()).throw(PermissionError('SECRET')))
    app.button(key='cc03-manual-refresh').click().run()
    assert app.session_state['cc03-last-export'].status.task_state is None and len(calls)==1
    app.radio[0].set_value('Монитор M15').run()
    assert any('NOT_DEPLOYED' in str(x.value) for x in app.info)
    app.selectbox(key='h1-source').select('READONLY_EXPORT').run()
    assert 'cc03-last-export' not in app.session_state
    assert not app.exception


@pytest.mark.parametrize('terminate',[False,True])
def test_manual_os_shares_gate_with_export_across_processes_and_recovers(manual_policy,monkeypatch,terminate):
    from test_manual_gate import CHILD
    wire(monkeypatch,manual_policy,lambda p:pytest.fail('contended probe'))
    child=subprocess.Popen([sys.executable,'-u','-c',CHILD],stdin=subprocess.PIPE,stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,text=True,cwd=Path(__file__).parents[1])
    try:
        assert child.stdout.readline().strip()=='ACQUIRED'
        monkeypatch.setattr(manual,'installed_policy',lambda:pytest.fail('policy read before gate'))
        assert not click()[1]
        if terminate:child.terminate()
        else:child.stdin.write('\n');child.stdin.flush()
        child.wait(10)
        wire(monkeypatch,manual_policy)
        assert click()[0].status.task_state=='TASK_RUNNING'
    finally:
        if child.poll() is None:child.kill();child.wait(10)
        child.stdin.close();child.stdout.close();child.stderr.close()


@pytest.mark.parametrize("invalid_offset, expected_freshness", [(31,"STALE"),(-1,"UNKNOWN")])
def test_expired_os_cache_never_revives_on_clock_rewind_without_manual_click(manual_policy,monkeypatch,invalid_offset,expected_freshness):
    from cc import freshness
    from streamlit.testing.v1 import AppTest
    clock=[None]
    calls=[]
    def probe(p):calls.append(p);return facts(p)
    wire(monkeypatch,manual_policy,probe)
    monkeypatch.setattr(freshness,'utc_now',lambda:datetime.now(timezone.utc) if clock[0] is None else clock[0])
    app=AppTest.from_file(str(Path(__file__).parents[1]/'app.py'),default_timeout=15).run()
    app.selectbox(key='h1-source').select('WINDOWS_OS_ONLY').run()
    app.radio[0].set_value('Монитор H1').run()
    app.button(key='cc03-manual-refresh').click().run()
    original=app.session_state['cc03-last-export']
    assert original.status.task_state=='TASK_RUNNING' and len(calls)==1
    clock[0]=original.status.provenance.received_at+timedelta(seconds=invalid_offset)
    app.run()
    assert app.session_state['cc03-last-export'].status.task_state is None
    clock[0]=original.status.provenance.received_at+timedelta(seconds=5)
    app.run()
    cached=app.session_state['cc03-last-export']
    assert cached.status.task_state is None and cached.status.provenance==original.status.provenance
    assert all(r.state=='UNKNOWN' and r.authority=='UNKNOWN' and r.value is None for r in cached.windows_observations)
    assert len(calls)==1 and not app.exception
    assert cached.windows_observations[0].freshness==expected_freshness
    if expected_freshness=='STALE':
        assert any('качество STALE' in str(c.value) for c in app.caption)
    clock[0]=None
    app.button(key='cc03-manual-refresh').click().run()
    assert app.session_state['cc03-last-export'].status.task_state=='TASK_RUNNING'
    assert len(calls)==2 and not app.exception
