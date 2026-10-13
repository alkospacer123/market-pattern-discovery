"""Synthetic external snapshots only; no LIVE file, credentials or broker order."""
import copy
from datetime import datetime,timezone
from decimal import Decimal as D
import json
from pathlib import Path
import sqlite3

import pandas as pd
import pytest

from TradingSystemLab.stage8_robot import release_preparation as release
from TradingSystemLab.stage8_robot import release_candidate_runner as preview
from TradingSystemLab.stage8_robot.production_history import continuation_payload_from_frame
from TradingSystemLab.stage8_robot.production_service import ProductionService, run_from_environment
from TradingSystemLab.stage8_robot.production_runtime import ProductionRuntime
from TradingSystemLab.stage8_robot.execution_grid import EXECUTION_REVISION
from TradingSystemLab.stage8_robot.tests.test_stop_tick_grid_amendment import signal
from TradingSystemLab.stage8_robot.tests.test_stage8_12_production_runtime import authority

ACCOUNT='synthetic-release-account';COMMIT='a'*40;SOURCE='184e8c2b8fa092a606249ff293a4f507160bff29'
NOW=datetime(2026,9,16,1,tzinfo=timezone.utc)


def broker():
    return {'observed_at':NOW.isoformat(),'account':{'account_id':ACCOUNT,'status':'ACCOUNT_ACTIVE','positions':[],
      'equity':{'value':'100000'},'unrealized_profit':{'value':'0'},'type':'FORTS',
      'portfolio_forts':{'available_cash':{'value':'1000000'},'money_reserved':{'value':'0'}}},'orders':{'orders':[]}}


def seed():
    return pd.DataFrame([[D('100'),D('101'),D('99'),D('100')]],
        index=pd.DatetimeIndex([pd.Timestamp('2026-09-15T23:00:00',tz='Europe/Moscow')],name='OpenTime'),
        columns=['Open','High','Low','Close'])


@pytest.fixture
def external_snapshot(tmp_path,monkeypatch):
    # Exercise the actual legacy service/StateStore schema, then online-backup
    # that synthetic database into a separate closed external snapshot file.
    svc=ProductionService(tmp_path/'legacy-fixture',tmp_path/'data',object(),ACCOUNT,SOURCE)
    rt=svc.runtime
    rt.set_realized_equity(D('100000'));rt.store.put('starting_realized_equity','100000')
    rt.store.put('production_positions',{});rt.store.put('production_service_cycle_count',9258)
    sig=signal(ticks='5')
    action=rt.plan_entry(sig,authority(),realized_equity=D('100000'),
        budget=rt.begin_batch(realized_equity=D('100000'),available_cash=D('1000000')))
    rt.store.transition_intent(action.idempotency_key,'CLOSED','historical-synthetic-order')
    rt.store.persist_fill({'fill_id':'historical-fill','broker_order_id':'historical-synthetic-order','trade_id':sig.trade_id,
                          'quantity':action.quantity,'price':'100','timestamp':sig.timestamp.isoformat()})
    empty=seed().iloc[0:0]
    for symbol in release.INSTRUMENTS:
        rt.store.put(f'production_h1_continuation:{symbol}',continuation_payload_from_frame(empty,symbol))
        rt.store.put(f'last_evaluated_h1:{symbol}','2026-09-16T00:00:00+03:00')
        rt.store.put(f'last_managed_h1:{symbol}','2026-09-16T00:00:00+03:00')
        rt.store.put(f'production_expected_h1:{symbol}','2026-09-15T23:00:00+03:00')
        rt.store.put(f'signal_sequence:{symbol}',42);rt.store.put(f'pending_signal:{symbol}',None)
    snapshot=tmp_path/'external-snapshot.sqlite3'
    destination=sqlite3.connect(snapshot);rt.store.db.backup(destination);destination.close();svc.close()
    monkeypatch.setattr(release,'load_stage5_seed_open_h1',lambda *args:seed())
    monkeypatch.setattr(release,'checkout_commit',lambda:COMMIT)
    monkeypatch.setattr(release,'committed_code_binding',lambda commit:release.code_binding())
    return snapshot,tmp_path


def prepare(fixture,broker_snapshot=None,name='prepared'):
    snapshot,root=fixture
    return release.dry_run(snapshot,release.sha(snapshot),root/name,account_hash=release.digest(ACCOUNT),
                           source_commit=SOURCE,candidate_commit=COMMIT,data_root=root/'data',broker=broker_snapshot or broker())


def test_dry_run_preserves_all_causal_values_archives_ledger_and_rolls_back(external_snapshot):
    snapshot,root=external_snapshot;before=release.sha(snapshot)
    _,raw,old_intents,old_fills=release.snapshot_rows(snapshot,before)
    manifest,result=prepare(external_snapshot)
    assert release.sha(snapshot)==before==release.sha(result['archive'])
    assert result['rollback_exact'] and result['archived_terminal_intents']==1 and result['archived_fills']==1
    rt=ProductionRuntime(Path(result['database']),execution_revision=EXECUTION_REVISION)
    actual=dict(rt.store.db.execute('SELECT key,value FROM state'))
    assert all(actual[k]==value for k,value in raw.items() if k!='database_identity')
    assert rt.store.all_intents()==[] and rt.store.all_fills()==[] and rt.open_positions()=={}
    assert rt.store.get('execution_halt')['status']=='HALTED'
    for symbol in release.INSTRUMENTS:
        assert rt.store.get(f'signal_sequence:{symbol}')==42
        assert rt.store.get(f'last_evaluated_h1:{symbol}')=='2026-09-16T00:00:00+03:00'
    rt.close()
    for _ in range(2):
        rt=ProductionRuntime(Path(result['database']),execution_revision=EXECUTION_REVISION);rt.close()
    _,restored,intents,fills=release.snapshot_rows(root/'prepared/rollback-restored.sqlite3',before)
    assert (restored,intents,fills)==(raw,old_intents,old_fills)
    assert result['entry_authorized'] is False


@pytest.mark.parametrize('change',['nonflat','unresolved','pending','unknown','sequence','watermark','continuation','identity','account','source','schema','fill'])
def test_contradictory_or_incompatible_state_never_creates_candidate(external_snapshot,change):
    snapshot,root=external_snapshot
    db=sqlite3.connect(snapshot)
    def alter(key,func):
        old=json.loads(db.execute('SELECT value FROM state WHERE key=?',(key,)).fetchone()[0])
        db.execute('UPDATE state SET value=? WHERE key=?',(json.dumps(func(old)),key))
    if change=='nonflat':alter('production_positions',lambda _: {'CNYRUBF':{'quantity':1}})
    elif change=='unresolved':db.execute("UPDATE intents SET status='ACK'")
    elif change=='pending':alter('pending_signal:CNYRUBF',lambda _: {'old_signal':'do not replay'})
    elif change=='unknown':db.execute('INSERT INTO state VALUES(?,?)',('unknown_authority','true'))
    elif change=='sequence':alter('signal_sequence:CNYRUBF',lambda _: -1)
    elif change=='watermark':alter('last_evaluated_h1:CNYRUBF',lambda _: '2026-10-12T12:00:00+03:00')
    elif change=='continuation':alter('production_h1_continuation:CNYRUBF',lambda v:v|{'bars_sha256':'0'*64})
    elif change=='identity':alter('database_identity',lambda v:v|{'execution_revision':'STOP_TICK_GRID_V1_PROPOSED'})
    elif change=='account':alter('production_service_identity',lambda v:v|{'account_hash':'0'*64})
    elif change=='source':alter('production_service_identity',lambda v:v|{'stage5_data_commit':'0'*40})
    elif change=='schema':db.execute('CREATE TABLE unknown(x)')
    else:db.execute("UPDATE fills SET price='999'")
    db.commit();db.close()
    with pytest.raises((RuntimeError,ValueError,sqlite3.DatabaseError)):prepare(external_snapshot)
    assert not (root/'prepared').exists()


@pytest.mark.parametrize('case',['position','active_order','wrong_account','duplicate_positions','wrong_time'])
def test_broker_contradiction_fails_closed_before_outputs(external_snapshot,case):
    snap=broker()
    if case=='position':snap['account']['positions']=[{'symbol':'CNYRUBF@RTSX','quantity':{'value':'1'}}]
    elif case=='active_order':snap['orders']={'orders':[{'order_id':'foreign','status':'NEW','order':{'symbol':'CNYRUBF@RTSX',
        'client_order_id':'foreign','side':'SIDE_BUY','quantity':{'value':'1'}}}]}
    elif case=='wrong_account':snap['account']['account_id']='wrong'
    elif case=='duplicate_positions':snap['account']['positions']=[{'symbol':'CNYRUBF@RTSX','quantity':{'value':'0'}}]*2
    else:snap['observed_at']='2026-09-01T00:00:00Z'
    with pytest.raises((RuntimeError,ValueError)):prepare(external_snapshot,snap)
    assert not (external_snapshot[1]/'prepared').exists()


@pytest.mark.parametrize('name',['stage8-12-production.sqlite3','stage8-11-acceptance.sqlite3','state/snapshot.sqlite3','LIVE/snapshot.sqlite3'])
def test_accidental_live_file_rejected_before_sqlite_open(external_snapshot,monkeypatch,name):
    _,root=external_snapshot;path=root/name;calls=[]
    monkeypatch.setattr(release.sqlite3,'connect',lambda *a,**k:(calls.append(a) or (_ for _ in ()).throw(AssertionError('SQLite opened'))))
    with pytest.raises(release.ReleaseBlocked,match='LIVE_PATH_FORBIDDEN'):release.snapshot_rows(path,'0'*64)
    assert calls==[]


@pytest.mark.parametrize('case',['hash','wal','symlink','existing_out'])
def test_source_or_destination_guard_is_create_only(external_snapshot,case):
    source,root=external_snapshot
    if case=='hash':
        with pytest.raises(release.ReleaseBlocked,match='SHA256'):release.snapshot_rows(source,'0'*64)
    elif case=='wal':
        Path(str(source)+'-wal').write_bytes(b'not a checkpointed snapshot')
        with pytest.raises(release.ReleaseBlocked,match='STANDALONE'):prepare(external_snapshot)
    elif case=='symlink':
        alias=root/'alias.sqlite3';alias.symlink_to(source)
        with pytest.raises(release.ReleaseBlocked,match='SYMLINK'):release.snapshot_rows(alias,release.sha(source))
    else:
        (root/'prepared').mkdir()
        with pytest.raises(release.ReleaseBlocked,match='NEW_ISOLATED'):prepare(external_snapshot)


class FakeReadonly:
    def __init__(self,*args):self.calls=[]
    def connect_readonly(self):self.calls.append('READONLY_SESSION')
    def account(self,account):self.calls.append('GET_ACCOUNT');return broker()['account']
    def orders(self,account):self.calls.append('GET_ORDERS');return broker()['orders']
    def place_order(self,*a):raise AssertionError('REAL_OR_FAKE_ORDER_ENDPOINT_FORBIDDEN')
    place_sltp_order=place_order;cancel_order=place_order


def test_actual_release_cli_dispatch_selects_v2_service_but_cannot_trade(external_snapshot,monkeypatch,capsys):
    manifest,result=prepare(external_snapshot);api=FakeReadonly()
    monkeypatch.setattr(preview,'CandidateReadonlyAPI',lambda *a:api)
    env={'FINAM_MODE':'STAGE8_12_PRODUCTION','FINAM_API_SECRET':'synthetic-readonly-only','FINAM_REAL_ACCOUNT_ID':ACCOUNT,
         'FINAM_EXECUTION_REVISION':EXECUTION_REVISION,'FINAM_FILL_AUTHORITY_VERIFIED':'true'}
    assert run_from_environment(Path(result['runtime_root']),external_snapshot[1]/'data',accepted_commit=COMMIT,
        environment=env,once=True,release_manifest=manifest,release_manifest_sha256=release.sha(manifest),clock=lambda:NOW)==0
    report=json.loads(capsys.readouterr().out)
    assert report['execution_revision']==EXECUTION_REVISION and report['selected_service']=='ProductionService'
    assert report['entry_authorized'] is False and report['real_order_endpoint_calls']==0
    assert api.calls==['READONLY_SESSION','GET_ACCOUNT','GET_ORDERS']
    assert not (Path(result['runtime_root'])/'safety/stage8-12-4-production-authorization.json').exists()


@pytest.mark.parametrize('field',['commit','account','revision','state','archive','code','root','auth','manifest_hash'])
def test_invalid_optin_fails_before_api_or_live_state_access(external_snapshot,field):
    manifest,result=prepare(external_snapshot);root=Path(result['runtime_root']);account=ACCOUNT;commit=COMMIT
    if field=='commit':commit='b'*40
    elif field=='account':account='other'
    elif field=='revision':result['execution_revision']='unknown'
    elif field=='state':Path(result['database']).write_bytes(b'different DB')
    elif field=='archive':Path(result['archive']).write_bytes(b'different archive')
    elif field=='code':result['code_sha256']['production_service.py']='0'*64
    elif field=='root':root=external_snapshot[1]/'LIVE'
    elif field=='auth':
        (root/'safety').mkdir();(root/'safety/stage8-12-4-production-authorization.json').write_text('{}')
    manifest.write_text(json.dumps(result))
    calls=[]
    def forbidden(*args):calls.append(args);raise AssertionError('API created before binding')
    with pytest.raises((RuntimeError,ValueError)):
        preview.run_preview(root,external_snapshot[1]/'data',manifest=manifest,
            manifest_sha='0'*64 if field=='manifest_hash' else release.sha(manifest),accepted_commit=commit,
            secret='synthetic',account_id=account,api_factory=forbidden)
    assert calls==[]


@pytest.mark.parametrize('method,path',[('POST','/v1/accounts/synthetic/orders'),('POST','/v1/accounts/synthetic/sltp-orders'),
    ('DELETE','/v1/accounts/synthetic/orders/order'),('GET','/v1/accounts/foreign/orders')])
def test_http_request_allowlist_blocks_order_mutations_even_with_gate_or_write_token(method,path):
    api=preview.CandidateReadonlyAPI('synthetic','synthetic');api.bound=True
    with pytest.raises(release.ReleaseBlocked,match='READONLY_REQUEST_FORBIDDEN'):api._request(method,path)


def test_write_capable_token_cannot_pass_preview_readonly_contract(monkeypatch):
    api=preview.CandidateReadonlyAPI('synthetic',ACCOUNT)
    api.create_session=lambda:None
    api.session_details=lambda:{'readonly':False,'account_ids':[ACCOUNT]}
    with pytest.raises(release.ReleaseBlocked,match='EXACT_READONLY'):api.connect_readonly()
    assert api.bound is False


def test_env_flag_alone_does_not_select_v2_or_construct_readonly_release_path(tmp_path,monkeypatch):
    observed=[]
    class Legacy:
        def __init__(self,*a,**k):observed.append(k)
        def authenticate(self):pass
        def run(self,**kwargs):return 0
        def close(self):pass
    import TradingSystemLab.stage8_robot.production_service as module
    monkeypatch.setattr(module,'ProductionService',Legacy)
    assert run_from_environment(tmp_path/'unchanged-legacy',tmp_path/'data',accepted_commit=COMMIT,once=True,
       environment={'FINAM_MODE':module.MODE,'FINAM_API_SECRET':'synthetic','FINAM_REAL_ACCOUNT_ID':ACCOUNT,
                    'FINAM_EXECUTION_REVISION':EXECUTION_REVISION,'FINAM_FILL_AUTHORITY_VERIFIED':'true'},api_factory=lambda _:object())==0
    assert all('execution_revision' not in kwargs for kwargs in observed)


def test_hardlink_alias_cannot_open_live_inode(external_snapshot):
    source,root=external_snapshot;alias=root/'hardlink-copy.sqlite3'
    import os
    os.link(source,alias)
    with pytest.raises(release.ReleaseBlocked,match='HARDLINK'):release.snapshot_rows(alias,release.sha(source))


def test_mutated_archive_binding_cannot_hash_a_live_path(external_snapshot):
    manifest,result=prepare(external_snapshot)
    result['archive']=str(external_snapshot[1]/'state/stage8-12-production.sqlite3')
    manifest.write_text(json.dumps(result))
    with pytest.raises(release.ReleaseBlocked,match='LIVE_PATH_FORBIDDEN'):
        release.validate_manifest(manifest,release.sha(manifest),runtime_root=result['runtime_root'],
            data_root=external_snapshot[1]/'data',account_hash=release.digest(ACCOUNT),accepted_commit=COMMIT)


def test_shadow_nonflat_broker_does_not_trigger_any_protection_order(external_snapshot):
    manifest,result=prepare(external_snapshot)
    class Contradictory(FakeReadonly):
        def account(self,account):
            value=super().account(account)
            value['positions']=[{'symbol':'CNYRUBF@RTSX','quantity':{'value':'1'}}]
            return value
    api=Contradictory()
    with pytest.raises(release.ReleaseBlocked,match='BROKER_NOT_FLAT'):
        preview.run_preview(result['runtime_root'],external_snapshot[1]/'data',manifest=manifest,
            manifest_sha=release.sha(manifest),accepted_commit=COMMIT,secret='synthetic',account_id=ACCOUNT,
            api_factory=lambda *a:api,clock=lambda:NOW)
    assert api.calls==['READONLY_SESSION','GET_ACCOUNT','GET_ORDERS']


def test_closed_guard_cannot_be_overridden_even_by_valid_manifest(external_snapshot,monkeypatch):
    manifest,result=prepare(external_snapshot);calls=[]
    monkeypatch.setattr(preview,'FINAM_FILL_AUTHORITY_VERIFIED',True)
    with pytest.raises(release.ReleaseBlocked,match='CLOSED_CANDIDATE_ENTRY_GUARD_REQUIRED'):
        preview.run_preview(result['runtime_root'],external_snapshot[1]/'data',manifest=manifest,
            manifest_sha=release.sha(manifest),accepted_commit=COMMIT,secret='synthetic',account_id=ACCOUNT,
            api_factory=lambda *a:calls.append(a))
    assert calls==[]


def test_unexplained_broker_financial_change_does_not_create_new_equity_authority(external_snapshot):
    snap=broker();snap['account']['equity']={'value':'200000'}
    with pytest.raises(release.ReleaseBlocked,match='UNEXPLAINED_REALIZED_EQUITY'):prepare(external_snapshot,snap)
    assert not (external_snapshot[1]/'prepared').exists()


def test_causal_watermark_must_belong_to_preserved_h1_not_merely_be_older(external_snapshot):
    source,_=external_snapshot
    db=sqlite3.connect(source)
    db.execute('UPDATE state SET value=? WHERE key=?',(json.dumps('2026-09-15T23:34:00+03:00'),'last_evaluated_h1:CNYRUBF'))
    db.commit();db.close()
    with pytest.raises(release.ReleaseBlocked,match='WATERMARK_NOT_IN_IMMUTABLE'):prepare(external_snapshot)

@pytest.mark.parametrize('runner',['service','release'])
def test_cli_arguments_reach_manifest_bound_readonly_service(external_snapshot,monkeypatch,capsys,runner):
    from TradingSystemLab.stage8_robot import production_service
    manifest,result=prepare(external_snapshot);api=FakeReadonly()
    monkeypatch.setattr(preview,'CandidateReadonlyAPI',lambda *a:api)
    monkeypatch.setenv('FINAM_MODE','STAGE8_12_PRODUCTION')
    monkeypatch.setenv('FINAM_API_SECRET','synthetic-readonly-only')
    monkeypatch.setenv('FINAM_REAL_ACCOUNT_ID',ACCOUNT)
    args=['--runtime-root',result['runtime_root'],'--stage5-data-root',str(external_snapshot[1]/'data'),
          '--accepted-commit',COMMIT,'--release-manifest',str(manifest),'--release-manifest-sha256',release.sha(manifest)]
    if runner=='service':args.append('--once')
    assert (production_service.main if runner=='service' else preview.main)(args)==0
    assert json.loads(capsys.readouterr().out)['execution_revision']==EXECUTION_REVISION
    assert api.calls==['READONLY_SESSION','GET_ACCOUNT','GET_ORDERS']


def test_signal_diagnostic_rejects_uncovered_live_week_without_output(external_snapshot,monkeypatch):
    from TradingSystemLab.stage8_robot import signal_execution_diagnostic as diagnostic
    monkeypatch.setattr(diagnostic,'load_stage5_seed_open_h1',lambda *a:seed())
    root=external_snapshot[1]
    with pytest.raises(release.ReleaseBlocked,match='INTERVAL_NOT_COVERED'):
        diagnostic.diagnose(root/'data',root/'uncovered-diagnostic',start='2026-10-01T00:00:00+03:00',end='2026-10-12T00:00:00+03:00')
    assert not (root/'uncovered-diagnostic').exists()


def test_signal_diagnostic_requires_explicit_causal_interval(tmp_path):
    from TradingSystemLab.stage8_robot.signal_execution_diagnostic import diagnose
    with pytest.raises(release.ReleaseBlocked,match='EXPLICIT_INTERVAL'):
        diagnose(tmp_path/'data',tmp_path/'bad-interval',start='2026-09-01',end='2026-09-02')
    assert not (tmp_path/'bad-interval').exists()

@pytest.mark.parametrize('case',['hardlink','wal'])
def test_candidate_database_alias_or_unclosed_wal_rejected_before_service(external_snapshot,case):
    import os
    manifest,result=prepare(external_snapshot);database=Path(result['database'])
    if case=='hardlink':os.link(database,external_snapshot[1]/'database-alias.sqlite3')
    else:Path(str(database)+'-wal').write_bytes(b'not a consistent standalone database')
    with pytest.raises(release.ReleaseBlocked,match='ISOLATED_RELEASE_ROOT'):
        release.validate_manifest(manifest,release.sha(manifest),runtime_root=Path(result['runtime_root']),
            data_root=external_snapshot[1]/'data',account_hash=release.digest(ACCOUNT),accepted_commit=COMMIT)

@pytest.mark.parametrize('sql',["CREATE VIEW hidden_authority AS SELECT * FROM intents", "CREATE TRIGGER hidden_trigger AFTER INSERT ON state BEGIN SELECT 1; END"])
def test_changed_schema_objects_block_even_if_table_columns_are_canonical(external_snapshot,sql):
    snapshot,root=external_snapshot
    db=sqlite3.connect(snapshot);db.execute(sql);db.commit();db.close()
    with pytest.raises(release.ReleaseBlocked,match='CHANGED_SQLITE_SCHEMA'):
        prepare(external_snapshot)
    assert not (root/'prepared').exists()


def test_corrupt_terminal_fill_not_silently_archived_as_valid_ledger(external_snapshot):
    snapshot,root=external_snapshot
    db=sqlite3.connect(snapshot);payload=json.loads(db.execute('SELECT payload FROM fills').fetchone()[0])
    payload['quantity']='-1';db.execute('UPDATE fills SET quantity=?,payload=?',('-1',json.dumps(payload)));db.commit();db.close()
    with pytest.raises(release.ReleaseBlocked,match='FILL_LEDGER_VALUE'):
        prepare(external_snapshot)
    assert not (root/'prepared').exists()


def path_guard_boundary(role,path,tmp_path):
    if role=='snapshot':
        return release.snapshot_rows(path,'0'*64)
    if role=='output':
        return release.safe_external(path,must_exist=False)
    return release.validate_manifest(path,'0'*64,runtime_root=tmp_path/'candidate-root',
        data_root=tmp_path/'data',account_hash='0'*64,accepted_commit='0'*40)


def forbid_path_content_io(monkeypatch):
    def forbidden(*a,**k):raise AssertionError('PATH_GUARD_MUST_REFUSE_BEFORE_CONTENT_IO')
    monkeypatch.setattr(release,'sha',forbidden)
    monkeypatch.setattr(release.sqlite3,'connect',forbidden)


@pytest.mark.parametrize('role',['snapshot','output','manifest'])
@pytest.mark.parametrize('location',['leaf','parent','ancestor'])
def test_path_guard_windows_reparse_attributes_before_resolve(tmp_path,monkeypatch,role,location):
    from types import SimpleNamespace
    parent=tmp_path/'external-alias'/'nested';parent.mkdir(parents=True)
    path=parent/('new-directory' if role=='output' else role+'.bin')
    if role=='output':path.mkdir()
    else:path.write_bytes(b'synthetic, never opened')
    flagged={'leaf':path,'parent':parent,'ancestor':parent.parent}[location]
    original=Path.lstat
    def metadata(item,*a,**k):
        if item==flagged:
            return SimpleNamespace(st_file_attributes=0x400,st_reparse_tag=0xA0000003)
        return original(item,*a,**k)
    monkeypatch.setattr(Path,'lstat',metadata)
    monkeypatch.setattr(Path,'is_symlink',lambda p:False)  # Windows mount-point junction is not a symlink.
    original_resolve=Path.resolve
    def resolve(item,*a,**k):
        if item==path:raise AssertionError('REPARSE_MUST_BE_REJECTED_BEFORE_RESOLVE')
        return original_resolve(item,*a,**k)
    monkeypatch.setattr(Path,'resolve',resolve)
    forbid_path_content_io(monkeypatch)
    with pytest.raises(release.ReleaseBlocked,match='REPARSE'):
        path_guard_boundary(role,path,tmp_path)


@pytest.mark.parametrize('role',['snapshot','output','manifest'])
@pytest.mark.parametrize('destination',['LIVE','runtime','repository'])
def test_path_guard_rechecks_resolved_absolute_target(tmp_path,monkeypatch,role,destination):
    alias=tmp_path/('new-output' if role=='output' else role+'.bin')
    if role!='output':alias.write_bytes(b'synthetic')
    resolved=(release.CODE_ROOT/'elsewhere.bin') if destination=='repository' else tmp_path/destination/'nested'/'target.bin'
    original=Path.resolve
    def resolve(item,*a,**k):return resolved if item==alias else original(item,*a,**k)
    monkeypatch.setattr(Path,'resolve',resolve)
    forbid_path_content_io(monkeypatch)
    with pytest.raises(release.ReleaseBlocked,match='LIVE_PATH|REPOSITORY'):
        path_guard_boundary(role,alias,tmp_path)


@pytest.mark.parametrize('role',['snapshot','output','manifest'])
@pytest.mark.parametrize('kind',['reparse','symlink'])
def test_path_guard_rechecks_all_resolved_parent_aliases(tmp_path,monkeypatch,role,kind):
    from types import SimpleNamespace
    alias=tmp_path/('new-output' if role=='output' else role+'.bin')
    if role!='output':alias.write_bytes(b'synthetic')
    resolved=tmp_path/'resolved-alias'/'nested'/'target.bin';resolved.parent.mkdir(parents=True)
    flagged=resolved.parent.parent
    original_resolve=Path.resolve;original_stat=Path.lstat;original_symlink=Path.is_symlink
    monkeypatch.setattr(Path,'resolve',lambda p,*a,**k:resolved if p==alias else original_resolve(p,*a,**k))
    monkeypatch.setattr(Path,'lstat',lambda p,*a,**k:SimpleNamespace(st_file_attributes=0x400,st_mode=original_stat(p).st_mode) if p==flagged and kind=='reparse' else original_stat(p,*a,**k))
    monkeypatch.setattr(Path,'is_symlink',lambda p:p==flagged if kind=='symlink' else original_symlink(p))
    forbid_path_content_io(monkeypatch)
    with pytest.raises(release.ReleaseBlocked,match='REPARSE|SYMLINK'):
        path_guard_boundary(role,alias,tmp_path)


@pytest.mark.parametrize('role',['snapshot','output','manifest'])
@pytest.mark.parametrize('root_name',['LIVE','runtime'])
def test_path_guard_relative_path_in_forbidden_absolute_cwd(tmp_path,monkeypatch,role,root_name):
    cwd=tmp_path/root_name/'nested';cwd.mkdir(parents=True)
    monkeypatch.chdir(cwd)
    forbid_path_content_io(monkeypatch)
    with pytest.raises(release.ReleaseBlocked,match='LIVE_PATH'):
        path_guard_boundary(role,Path('external.bin'),tmp_path)


def test_path_guard_metadata_read_failure_is_fail_closed(tmp_path,monkeypatch):
    path=tmp_path/'new-output';original=Path.lstat
    def metadata(item,*a,**k):
        if item==tmp_path:raise PermissionError('synthetic inaccessible parent')
        return original(item,*a,**k)
    monkeypatch.setattr(Path,'lstat',metadata)
    with pytest.raises(release.ReleaseBlocked,match='PATH_METADATA_UNVERIFIED'):
        release.safe_external(path,must_exist=False)


def test_path_guard_windows_missing_reparse_authority_is_fail_closed(tmp_path,monkeypatch):
    from types import SimpleNamespace
    # Only the release module's platform observation is replaced; pathlib/pytest
    # retain the native platform. No Windows filesystem claim is made here.
    monkeypatch.setattr(release,'os',SimpleNamespace(name='nt'),raising=False)
    monkeypatch.setattr(Path,'lstat',lambda *a,**k:SimpleNamespace(st_mode=0))
    monkeypatch.setattr(Path,'is_symlink',lambda p:False)
    with pytest.raises(release.ReleaseBlocked,match='WINDOWS_REPARSE_AUTHORITY_UNAVAILABLE'):
        release.safe_external(tmp_path/'new-output',must_exist=False)


def test_path_guard_non_reparse_windows_attributes_do_not_reject_external_output(tmp_path,monkeypatch):
    from types import SimpleNamespace
    original=Path.lstat
    def metadata(item,*a,**k):
        value=original(item,*a,**k)
        return SimpleNamespace(st_file_attributes=0x20,st_mode=value.st_mode)
    monkeypatch.setattr(Path,'lstat',metadata)
    path=tmp_path/'new-output'
    assert release.safe_external(path,must_exist=False)==path.resolve()


@pytest.mark.skipif(__import__('os').name!='nt',reason='Native Windows junction integration only')
@pytest.mark.parametrize('role',['snapshot','output','manifest'])
@pytest.mark.parametrize('target_name',['LIVE','runtime'])
def test_path_guard_native_windows_junction_to_synthetic_live(tmp_path,monkeypatch,role,target_name):
    import os,subprocess
    # These are fresh test directories only, never an Intel/LIVE path.
    target=tmp_path/target_name/'fixture';target.mkdir(parents=True)
    leaf='future-output' if role=='output' else role+'.bin'
    if role!='output':(target/leaf).write_bytes(b'synthetic, never opened')
    junction=tmp_path/'external-junction'
    result=subprocess.run(['cmd','/c','mklink','/J',str(junction),str(target)],
        stdout=subprocess.PIPE,stderr=subprocess.STDOUT,text=True)
    assert result.returncode==0,result.stdout
    try:
        assert not junction.is_symlink()
        forbid_path_content_io(monkeypatch)
        with pytest.raises(release.ReleaseBlocked,match='REPARSE'):
            path_guard_boundary(role,junction/leaf,tmp_path)
        assert not (target/'future-output').exists()
    finally:
        os.rmdir(junction)  # Remove the junction itself, never traverse its target.


@pytest.mark.parametrize('component',['state','database'])
@pytest.mark.parametrize('alias_kind',['reparse','symlink'])
def test_manifest_candidate_internal_reparse_or_symlink_is_rejected(external_snapshot,monkeypatch,component,alias_kind):
    """Internal state/SQLite cannot use safe_external due to their reserved names."""
    from types import SimpleNamespace
    manifest,result=prepare(external_snapshot)
    database=Path(result['database'])
    flagged=database.parent if component=='state' else database
    original_lstat=Path.lstat
    original_is_symlink=Path.is_symlink
    original_sha=release.sha
    def metadata(item,*args,**kwargs):
        value=original_lstat(item,*args,**kwargs)
        if item==flagged and alias_kind=='reparse':
            return SimpleNamespace(st_file_attributes=0x400,st_mode=value.st_mode)
        return value
    def is_symlink(item):
        return True if item==flagged and alias_kind=='symlink' else original_is_symlink(item)
    def refuse_database_hash(path):
        if Path(path)==database:
            raise AssertionError('CANDIDATE_DATABASE_MUST_NOT_BE_READ_BEFORE_ALIAS_REJECTION')
        return original_sha(path)
    monkeypatch.setattr(Path,'lstat',metadata)
    monkeypatch.setattr(Path,'is_symlink',is_symlink)
    monkeypatch.setattr(release,'sha',refuse_database_hash)
    with pytest.raises(release.ReleaseBlocked,match='REPARSE_PATH_FORBIDDEN|SYMLINK_PATH_FORBIDDEN'):
        release.validate_manifest(manifest,release.sha(manifest),runtime_root=result['runtime_root'],
            data_root=external_snapshot[1]/'data',account_hash=release.digest(ACCOUNT),accepted_commit=COMMIT)


@pytest.mark.parametrize('component',['state','database'])
def test_manifest_candidate_internal_missing_windows_reparse_metadata_fails_closed(external_snapshot,monkeypatch,component):
    """A Windows filesystem without metadata must not silently become trusted."""
    from types import SimpleNamespace
    manifest,result=prepare(external_snapshot)
    database=Path(result['database'])
    flagged=database.parent if component=='state' else database
    original_lstat=Path.lstat
    def metadata(item,*args,**kwargs):
        value=original_lstat(item,*args,**kwargs)
        if item==flagged:
            return SimpleNamespace(st_mode=value.st_mode)
        return value
    monkeypatch.setattr(Path,'lstat',metadata)
    monkeypatch.setattr(release,'os',SimpleNamespace(name='nt'),raising=False)
    with pytest.raises(release.ReleaseBlocked,match='WINDOWS_REPARSE_AUTHORITY_UNAVAILABLE'):
        release._candidate_state_database(Path(result['runtime_root']))


@pytest.mark.skipif(__import__('os').name!='nt',reason='Native Windows junction integration only')
def test_native_windows_candidate_state_junction_refused_before_db_open(external_snapshot):
    """Only synthetic disposable directories; never a production SQLite path."""
    import os,shutil,subprocess
    manifest,result=prepare(external_snapshot)
    root=Path(result['runtime_root'])
    state=root/'state'
    saved=external_snapshot[1]/'saved-original-candidate-state'
    target=external_snapshot[1]/'external-junction-target'
    target.mkdir()
    shutil.copy2(result['database'],target/'stage8-12-production.sqlite3')
    state.rename(saved)
    linked=False
    try:
        command=subprocess.run(['cmd','/c','mklink','/J',str(state),str(target)],
            stdout=subprocess.PIPE,stderr=subprocess.STDOUT,text=True)
        assert command.returncode==0,command.stdout
        linked=True
        with pytest.raises(release.ReleaseBlocked,match='REPARSE_PATH_FORBIDDEN'):
            release.validate_manifest(manifest,release.sha(manifest),runtime_root=root,
                data_root=external_snapshot[1]/'data',account_hash=release.digest(ACCOUNT),accepted_commit=COMMIT)
    finally:
        if linked:os.rmdir(state)  # Only remove test-created junction, not its target.
        saved.rename(state)
