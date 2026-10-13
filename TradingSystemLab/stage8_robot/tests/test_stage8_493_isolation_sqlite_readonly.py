"""Independent SQLite-only tests: never touch production or credentials."""
import importlib.util
import json
import sqlite3
from pathlib import Path
import pytest

FILE = Path(__file__).resolve().parents[1] / 'diagnostics' / 'stage8_493_isolation_sqlite_readonly.py'
spec = importlib.util.spec_from_file_location('isolation_audit', FILE)
audit = importlib.util.module_from_spec(spec)
spec.loader.exec_module(audit)


def state(tmp_path):
    directory = tmp_path / 'state'
    directory.mkdir()
    path = directory / audit.DB_NAME
    con = sqlite3.connect(path)
    con.executescript('create table state(key text primary key,value text not null);'
                      'create table intents(idempotency_key text primary key,status text);'
                      'create table fills(fill_id text primary key);')
    identity = {'production_specification_id': audit.SPEC, 'active_identity': audit.IDENTITY}
    con.execute('insert into state values(?,?)', ('database_identity', json.dumps(identity)))
    con.commit(); con.close()
    return path


def put(path, key, val):
    with sqlite3.connect(path) as c:
        c.execute('insert or replace into state values(?,?)', (key,json.dumps(val)))


def test_flat_and_absent_position_key_are_accepted(tmp_path):
    db = state(tmp_path)
    assert audit.inspect(tmp_path)['unresolved_intents'] == 0
    put(db,'production_positions',{})
    put(db,'pending_signal:USDRUBF',None)
    assert audit.inspect(tmp_path)['positions'] == 0


@pytest.mark.parametrize('value', [{'USDRUBF': {'quantity': 1}}, None, [], 'zero'])
def test_nonempty_or_malformed_positions_block(tmp_path,value):
    db=state(tmp_path)
    put(db,'production_positions',value)
    with pytest.raises(audit.Blocked,match='SQLITE_POSITIONS_NOT_EMPTY'):
        audit.inspect(tmp_path)


def test_intents_block_except_terminal(tmp_path):
    db=state(tmp_path)
    with sqlite3.connect(db) as c:
        c.execute("insert into intents values('one','ACK')")
    with pytest.raises(audit.Blocked,match='SQLITE_UNRESOLVED_INTENTS_PRESENT'):
        audit.inspect(tmp_path)
    with sqlite3.connect(db) as c:
        c.execute("update intents set status='RECONCILED'")
    assert audit.inspect(tmp_path)['unresolved_intents']==0


def test_pending_signal_and_identity_mismatch_block(tmp_path):
    db=state(tmp_path)
    put(db,'pending_signal:CNYRUBF',{'intent':'exists'})
    with pytest.raises(audit.Blocked,match='SQLITE_PENDING_SIGNALS_PRESENT'):
        audit.inspect(tmp_path)
    put(db,'pending_signal:CNYRUBF',None)
    put(db,'database_identity',{'active_identity':'wrong'})
    with pytest.raises(audit.Blocked,match='SQLITE_FROZEN_IDENTITY_MISMATCH'):
        audit.inspect(tmp_path)


def test_symlinks_and_wal_without_shm_block(tmp_path):
    db=state(tmp_path)
    (tmp_path/'state'/('stage8-12-production.sqlite3-wal')).write_bytes(b'x')
    with pytest.raises(audit.Blocked,match='SQLITE_WAL_REQUIRES_PREEXISTING_SHM'):
        audit.inspect(tmp_path)
    (tmp_path/'state'/('stage8-12-production.sqlite3-wal')).unlink()
    shortcut = tmp_path/'shortcut'
    try: shortcut.symlink_to(tmp_path/'state',target_is_directory=True)
    except OSError: pytest.skip('symlinks unavailable')
    with pytest.raises(audit.Blocked):
        audit.inspect(shortcut.parent/'shortcut')


def test_db_byte_identical_and_no_network_no_order_imports(tmp_path):
    import hashlib
    db=state(tmp_path)
    before=hashlib.sha256(db.read_bytes()).hexdigest()
    audit.inspect(tmp_path)
    assert hashlib.sha256(db.read_bytes()).hexdigest()==before
    src=FILE.read_text()
    assert 'place_order' not in src and 'cancel_order' not in src
    assert 'mode=ro' in src and 'pragma query_only=on' in src
