"""Offline checks of the read-only diagnostic, never FINAM price acceptance."""
from dataclasses import replace
from decimal import Decimal, localcontext
import json
from pathlib import Path
from urllib.parse import parse_qs, urlsplit
from urllib.error import HTTPError

import pytest

from TradingSystemLab.stage8_robot.broker import compact_client_order_id
from TradingSystemLab.stage8_robot.finam_api import FinamError
from TradingSystemLab.stage8_robot.finam_fill_price_readonly import (
    FillDiagnosticBlocked, Target, ReadonlyFillAPI, analyze_history, collect,
    file_digest, load_ack_copy,
)
from TradingSystemLab.stage8_robot.state import StateStore, stage8_11_identity
from TradingSystemLab.stage8_robot.tests.test_stop_tick_grid_amendment import runtime, signal, plan, confirm, bar
from TradingSystemLab.stage8_robot.production_runtime import ProductionRuntimeError

D=Decimal
ACCOUNT='synthetic-account'
KEY='stage8.11.attempt7:CNYRUBF:entry'
START='2026-10-05T09:00:00Z'
END='2026-10-05T10:00:00Z'


def target(quantity=3):
    return Target(ACCOUNT,KEY,'known-ack-order','CNYRUBF@RTSX','SIDE_BUY',quantity,D('.001'))


def fill(trade='fill-1', quantity='1',price='10.001',**changes):
    result={'trade_id':trade,'order_id':'known-ack-order','account_id':ACCOUNT,'symbol':'CNYRUBF@RTSX',
            'side':'SIDE_BUY','size':{'value':quantity},'price':{'value':price},'currency':'RUB',
            'timestamp':'2026-10-05T09:01:00.000000001Z'}
    result.update(changes)
    return result


class Raw:
    status=200
    headers={}
    def __init__(self,body): self.body=body
    def read(self): return json.dumps(self.body).encode()


class NoDelay:
    def wait(self): pass


class ReadTransport:
    def __init__(self,rows=None,readonly=True,error=None):
        self.rows=rows if rows is not None else [fill()]
        self.readonly=readonly; self.error=error; self.requests=[]
    def __call__(self,request,timeout):
        url=urlsplit(request.full_url); method=request.get_method()
        self.requests.append((method,url.path,url.query))
        if url.path=='/v1/sessions': return Raw({'token':'synthetic-jwt'})
        if url.path=='/v1/sessions/details': return Raw({'readonly':self.readonly,'account_ids':[ACCOUNT]})
        if url.path==f'/v1/accounts/{ACCOUNT}':
            return Raw({'account_id':ACCOUNT,'positions':[],'type':'FORTS'})
        if url.path==f'/v1/accounts/{ACCOUNT}/trades':
            if self.error: raise HTTPError(request.full_url,self.error,'synthetic',{},None)
            query=parse_qs(url.query)
            assert query=={'limit':['50'],'interval.start_time':[START],'interval.end_time':[END]}
            return Raw({'trades':self.rows})
        raise AssertionError('NON_READONLY_ENDPOINT')


def api(transport): return ReadonlyFillAPI('synthetic-secret',ACCOUNT,transport=transport,limiter=NoDelay())


def ledger(path,**changes):
    store=StateStore(path,stage8_11_identity(ACCOUNT))
    payload={'client_order_id':compact_client_order_id(KEY),'symbol':'CNYRUBF@RTSX','side':'SIDE_BUY',
             'quantity':{'value':'1'},'type':'ORDER_TYPE_MARKET'}
    payload.update(changes)
    store.persist_intent(KEY,payload); store.transition_intent(KEY,'ACK','known-ack-order'); store.close()
    return file_digest(path)


def test_immutable_copied_ack_identity_no_sqlite_changes(tmp_path):
    path=tmp_path/'standalone-copy.sqlite3'; sha=ledger(path)
    value=load_ack_copy(path,sha,ACCOUNT,KEY)
    assert value.order_id=='known-ack-order' and value.quantity==1
    assert file_digest(path)==sha and sorted(p.name for p in tmp_path.iterdir())==[path.name]
    with pytest.raises(FillDiagnosticBlocked,match='ACCOUNT_IDENTITY'): load_ack_copy(path,sha,'other-account',KEY)
    with pytest.raises(FillDiagnosticBlocked,match='IMMUTABLE_LEDGER'): load_ack_copy(path,'f'*64,ACCOUNT,KEY)


@pytest.mark.parametrize('change',[{'client_order_id':'other-client'},{'symbol':'USDRUBF@RTSX'},
                                   {'side':'SIDE_UNKNOWN'},{'quantity':{'value':'2'}},{'type':'ORDER_TYPE_LIMIT'}])
def test_ack_request_identity_invalid(tmp_path,change):
    path=tmp_path/'copy.sqlite3'; sha=ledger(path,**change)
    with pytest.raises(FillDiagnosticBlocked,match='ACK_REQUEST_IDENTITY'): load_ack_copy(path,sha,ACCOUNT,KEY)


def test_reject_live_filename_sidecars_and_absent_ack(tmp_path):
    live=tmp_path/'stage8-11-acceptance.sqlite3'; sha=ledger(live)
    with pytest.raises(FillDiagnosticBlocked,match='IMMUTABLE_LEDGER'): load_ack_copy(live,sha,ACCOUNT,KEY)
    path=tmp_path/'copy.sqlite3'; sha=ledger(path)
    Path(str(path)+'-wal').touch()
    with pytest.raises(FillDiagnosticBlocked,match='IMMUTABLE_LEDGER'): load_ack_copy(path,sha,ACCOUNT,KEY)
    Path(str(path)+'-wal').unlink()
    with pytest.raises(FillDiagnosticBlocked,match='DURABLE_ACK'): load_ack_copy(path,sha,ACCOUNT,'stage8.11.attempt6:CNYRUBF:entry')


def test_correct_history_request_and_no_account_price_fallback():
    transport=ReadTransport()
    report=collect(api(transport),target(1),START,END,50,ledger_sha='a'*64)
    assert report['history']['weighted_price_exact']=={'numerator':'10001','denominator':'1000'}
    assert report['current_position_quantity']==0  # historical fill remains valid after manual close
    assert report['history']['quantity_observation']=='FULL_REQUEST_MATCHED'
    assert report['acceptance_status']=='DIAGNOSTIC_OBSERVATION_ONLY_NOT_LIVE_ACCEPTANCE'
    assert report['real_order_endpoint_calls']==0
    assert transport.requests==[
        ('POST','/v1/sessions',''),('POST','/v1/sessions/details',''),
        ('GET',f'/v1/accounts/{ACCOUNT}',''),
        ('GET',f'/v1/accounts/{ACCOUNT}/trades',transport.requests[-1][2]),
    ]
    assert ACCOUNT not in json.dumps(report)
    assert 'synthetic-secret' not in json.dumps(report) and 'synthetic-jwt' not in json.dumps(report)


@pytest.mark.parametrize('method,path',[
    ('POST',f'/v1/accounts/{ACCOUNT}/orders'),('DELETE',f'/v1/accounts/{ACCOUNT}/orders/id'),
    ('GET',f'/v1/accounts/{ACCOUNT}/orders'),('GET',f'/v1/accounts/{ACCOUNT}/orders/id'),
    ('POST',f'/v1/accounts/{ACCOUNT}/sltp-orders'),('GET',f'/v1/accounts/{ACCOUNT}/trades'),
    ('GET','/v1/accounts/other/trades'),('GET','/v1/assets/all'),
])
def test_request_allowlist_rejects_orders_and_unbounded_history(method,path):
    transport=ReadTransport(); client=api(transport); client.connect_readonly()
    before=list(transport.requests)
    with pytest.raises(FillDiagnosticBlocked,match='READONLY_REQUEST_FORBIDDEN'): client._request(method,path)
    assert transport.requests==before


def test_inherited_order_methods_cannot_reach_transport():
    transport=ReadTransport(); client=api(transport)
    for call in (lambda:client.place_order(ACCOUNT,{}),lambda:client.place_sltp_order(ACCOUNT,{}),
                 lambda:client.cancel_order(ACCOUNT,'id'),lambda:client.order(ACCOUNT,'id')):
        with pytest.raises(FillDiagnosticBlocked,match='READONLY_REQUEST_FORBIDDEN'): call()
    assert transport.requests==[]


def test_wrong_readonly_token_blocks_before_account_get():
    transport=ReadTransport(readonly=False)
    with pytest.raises(FillDiagnosticBlocked,match='READONLY_ACCOUNT_BINDING'): api(transport).connect_readonly()
    assert len(transport.requests)==2


@pytest.mark.parametrize('code',[400,404,503])
def test_unavailable_history_reports_blocked_never_imputes_price(code):
    report=collect(api(ReadTransport(error=code)),target(1),START,END,50,ledger_sha='a'*64)
    assert report['history_http_status']==code
    assert 'history' not in report and report['history_blocker']=='HISTORY_READ_UNAVAILABLE'
    assert report['live_production_ready']=='NO'


def test_partial_full_weighted_price_exact_duplicates_and_unrelated_rows():
    rows=[fill(),fill(),fill('fill-2','1','10.002'),fill(order_id='other-order',price='999')]
    partial=analyze_history({'trades':rows},target(),START,END,50)
    assert partial['matched_quantity']==2 and partial['quantity_observation']=='PARTIAL_REQUEST_MATCHED'
    assert partial['weighted_price_exact']=={'numerator':'20003','denominator':'2000'}
    full=analyze_history({'trades':rows+[fill('fill-3','1','10.003')]},target(),START,END,50)
    assert full['matched_quantity']==3 and full['weighted_price_exact']=={'numerator':'5001','denominator':'500'}
    # Non-terminating average retains an exact rational, never a fake Decimal fill.
    thirds=analyze_history({'trades':[fill(quantity='2'),fill('fill-2',price='10.002')]},target(),START,END,50)
    assert thirds['weighted_price_exact']=={'numerator':'7501','denominator':'750'}


@pytest.mark.parametrize('changes',[
    {'account_id':'other'},{'symbol':'USDRUBF@RTSX'},{'side':'SIDE_SELL'},{'currency':'USD'},
    {'size':{'value':'0.5'}},{'size':{'value':'0'}},{'price':{'value':'NaN'}},
    {'price':{'value':'10.0001'}},{'timestamp':END},{'timestamp':'2026-10-05T08:59:59Z'},
])
def test_matching_fill_identity_units_quantity_grid_and_interval_fail_closed(changes):
    with pytest.raises((FillDiagnosticBlocked,ValueError,RuntimeError)):
        analyze_history({'trades':[fill(**changes)]},target(),START,END,50)


def test_duplicate_conflict_overfill_and_limit_saturation():
    with pytest.raises(FillDiagnosticBlocked,match='CONFLICTING_DUPLICATE'):
        analyze_history({'trades':[fill(),fill(price='10.002')]},target(),START,END,50)
    with pytest.raises(FillDiagnosticBlocked,match='EXCEED_REQUEST'):
        analyze_history({'trades':[fill(quantity='4')]},target(),START,END,50)
    with pytest.raises(FillDiagnosticBlocked,match='COMPLETENESS'):
        analyze_history({'trades':[fill()]},target(),START,END,1)
    with pytest.raises(FillDiagnosticBlocked,match='COMPLETENESS'):
        analyze_history({'trades':[fill()],'next_cursor':'more'},target(),START,END,50)


def test_no_matching_fill_and_separate_process_retention_observation():
    empty=collect(api(ReadTransport(rows=[])),target(1),START,END,50,ledger_sha='a'*64)
    assert empty['history']['weighted_price_exact'] is None
    first=collect(api(ReadTransport()),target(1),START,END,50,ledger_sha='a'*64)
    restored=json.loads(json.dumps(first))
    second=collect(api(ReadTransport()),target(1),START,END,50,ledger_sha='a'*64,previous=restored)
    assert second['restart_observation']=='SAME_FULL_FILL_SET_OBSERVED'
    missing=collect(api(ReadTransport(rows=[])),target(1),START,END,50,ledger_sha='a'*64,previous=restored)
    assert missing['restart_observation']=='BLOCKED_CHANGED_OR_INCOMPLETE_HISTORY'
    with pytest.raises(FillDiagnosticBlocked,match='PREVIOUS_DIAGNOSTIC_IDENTITY'):
        collect(api(ReadTransport()),target(1),START,END,50,ledger_sha='b'*64,previous=restored)


def test_candidate_fill_math_and_partial_unknown_inhibition(tmp_path):
    rt=runtime(tmp_path/'state.db'); entry=plan(rt)
    partial_stop=rt.confirm_entry_position(entry.idempotency_key,entry.quantity-1)
    assert partial_stop.quantity==entry.quantity-1
    assert rt.open_positions()['USDRUBF']['quantity']==entry.quantity-1
    assert rt.store.intent(entry.idempotency_key)['status']=='PARTIAL_FILL'
    with pytest.raises(ProductionRuntimeError,match='ACTUAL_FILL_AUTHORITY'): plan(rt,signal('CNYRUBF'))
    stop=confirm(rt,entry,D('100.025'))
    position=rt.open_positions()['USDRUBF']
    expected=(D('100.025')-entry.stop_price)/D('.01')*D('10')*entry.quantity
    assert D(position['actual_initial_loss_cash'])==expected and expected>D('1500')
    assert position['reference_entry']!=position['verified_fill_entry']
    rt.confirm_protective_stop(stop.idempotency_key,'synthetic-backstop')
    assert rt.open_positions()['USDRUBF']['protective_stop_state']=='ACTIVE'
    rt.close()


def test_powershell_wrapper_has_no_live_controls_or_trading_credential_calls():
    source=Path('TradingSystemLab/stage8_robot/diagnostics/run-finam-fill-price-readonly.ps1').read_text()
    for forbidden in ('Disable-ScheduledTask','Enable-ScheduledTask','Stop-Process','Start-Process',
                      'Set-PrivateCredentialAcl','Set-TradingPrivateAcl','Get-TradingCredential',
                      'load_kill_switch','InstanceLock','ProductionService','git pull','git checkout'):
        assert forbidden not in source
    assert 'Get-ReadonlyCredential $runtime' in source
    assert 'Remove-Item Env:FINAM_FILL_READONLY_SECRET' in source


def test_cli_report_is_create_only_and_does_not_touch_ack_copy(tmp_path,monkeypatch,capsys):
    import TradingSystemLab.stage8_robot.finam_fill_price_readonly as diagnostic
    copied=tmp_path/'immutable-copy.sqlite3'; sha=ledger(copied)
    output=tmp_path/'report.json'; transport=ReadTransport()
    monkeypatch.setenv('FINAM_FILL_READONLY_SECRET','synthetic-secret')
    monkeypatch.setenv('FINAM_FILL_READONLY_ACCOUNT',ACCOUNT)
    monkeypatch.setattr(diagnostic,'ReadonlyFillAPI',lambda secret,account:api(transport))
    arguments=['--ledger-copy',str(copied),'--ledger-sha256',sha,'--intent-key',KEY,
               '--start-time',START,'--end-time',END,'--output',str(output)]
    assert diagnostic.main(arguments)==0
    report=json.loads(output.read_text())
    assert report['history']['quantity_observation']=='FULL_REQUEST_MATCHED' and file_digest(copied)==sha
    before=file_digest(output); calls=list(transport.requests)
    assert diagnostic.main(arguments)==1
    assert file_digest(output)==before and transport.requests==calls
    assert 'synthetic-secret' not in capsys.readouterr().out


def test_absolute_urls_fragments_and_foreign_account_never_reach_transport():
    transport=ReadTransport(); client=api(transport); client.connect_readonly()
    valid=f'/v1/accounts/{ACCOUNT}/trades?limit=50&interval.start_time={START}&interval.end_time={END}'
    before=list(transport.requests)
    for path in ('https://elsewhere.invalid'+valid,valid+'#fragment',valid.replace(ACCOUNT,'other-account')):
        with pytest.raises(FillDiagnosticBlocked,match='READONLY_REQUEST_FORBIDDEN'): client._request('GET',path)
    assert transport.requests==before
