"""Isolated, order-incapable legacy -> V2 preparation. Never opens LIVE state."""
from __future__ import annotations
import hashlib
import json
import os
import re
import shutil
import sqlite3
import stat
import subprocess
from datetime import datetime, timezone
from decimal import Decimal
from pathlib import Path, PureWindowsPath

import pandas as pd

from .execution_grid import EXECUTION_REVISION
from .production_broker_state import position_quantities, order_views
from .margin import parse_rest_decimal_value_object, portfolio_authority
from .production_history import STAGE5_DATA_COMMIT, load_stage5_seed_open_h1, load_continuation_open_h1
from .production_runtime import ProductionRuntime, RUNTIME_SCHEMA, AMENDED_RUNTIME_SCHEMA, MODE
from .specification import PRODUCTION_SPECIFICATION_ID, ACTIVE_IDENTITY, INSTRUMENTS
from .state import _validate_acceptance_schema, _SCHEMA, TERMINAL_INTENT_STATUSES

SCHEMA='stop_tick_grid_v2_release_preparation.v1'
CODE_ROOT=Path(__file__).resolve().parents[2]
CODE_FILES=('release_preparation.py','release_candidate_runner.py','production_service.py','production_runtime.py',
            'execution_grid.py','production_history.py','specification.py','strategy_core.py','trail1_state.py',
            'risk.py','margin.py','production_instrument_registry.csv','state.py','finam_api.py',
            'production_broker_state.py','production_authorization.py','production_safety_gate.py','operations.py',
            'context_builder.py','live_execution.py','broker.py','finam_fill_price_readonly.py')
FIXED_KEYS={'database_identity','production_service_identity','realized_equity','starting_realized_equity',
            'explained_external_cash_flows','production_positions','production_service_cycle_count'}
PREFIXES=('production_h1_continuation','production_expected_h1','last_evaluated_h1','last_managed_h1',
          'signal_sequence','pending_signal')


class ReleaseBlocked(RuntimeError):
    pass


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def digest(value):
    return hashlib.sha256(value.encode()).hexdigest()


def _commit(value):
    if not isinstance(value,str) or not re.fullmatch('[0-9a-f]{40}',value):
        raise ReleaseBlocked('EXACT_COMMIT_REQUIRED')
    return value


def code_binding():
    root=Path(__file__).parent
    return {name:sha(root/name) for name in CODE_FILES}


def committed_code_binding(commit):
    try:
        return {name:hashlib.sha256(subprocess.check_output(['git','show',
            f'{commit}:TradingSystemLab/stage8_robot/{name}'],cwd=CODE_ROOT,stderr=subprocess.DEVNULL)).hexdigest()
                for name in CODE_FILES}
    except subprocess.CalledProcessError:
        raise ReleaseBlocked('COMMITTED_RELEASE_CODE_REQUIRED') from None


def checkout_commit():
    return subprocess.check_output(['git','rev-parse','HEAD'],cwd=CODE_ROOT,text=True).strip()


def _check_external_path(path):
    """Check the absolute path and every ancestor without following aliases."""
    if not path.is_absolute():raise ReleaseBlocked('ABSOLUTE_EXTERNAL_PATH_REQUIRED')
    raw_parts={part.casefold() for part in PureWindowsPath(str(path)).parts} | {part.casefold() for part in path.parts}
    if raw_parts & {'live','runtime','state','tradingsystemlab'} or path.name.casefold() in {
            'stage8-12-production.sqlite3','stage8-11-acceptance.sqlite3','readonly-supervisor.sqlite3'}:
        raise ReleaseBlocked('LIVE_PATH_FORBIDDEN')
    for item in (path,*path.parents):
        try:
            if item.is_symlink():raise ReleaseBlocked('SYMLINK_PATH_FORBIDDEN')
            metadata=item.lstat()
        except FileNotFoundError:continue  # A new output may have missing components.
        except OSError as exc:raise ReleaseBlocked('PATH_METADATA_UNVERIFIED') from exc
        attributes=getattr(metadata,'st_file_attributes',None)
        if attributes is None and os.name=='nt':
            raise ReleaseBlocked('WINDOWS_REPARSE_AUTHORITY_UNAVAILABLE')
        if attributes is not None and attributes & stat.FILE_ATTRIBUTE_REPARSE_POINT:
            raise ReleaseBlocked('REPARSE_PATH_FORBIDDEN')
    if path==CODE_ROOT or CODE_ROOT in path.parents:
        raise ReleaseBlocked('REPOSITORY_OUTPUT_OR_SNAPSHOT_FORBIDDEN')


def safe_external(path, *, snapshot=False, must_exist=True):
    """Reject LIVE roots and symlink/junction/reparse aliases before content IO."""
    path=Path(path).absolute()
    _check_external_path(path)
    path=path.resolve()
    _check_external_path(path)
    if must_exist and not path.is_file():raise ReleaseBlocked('EXTERNAL_FILE_REQUIRED')
    if snapshot and path.exists() and path.stat().st_nlink!=1:
        raise ReleaseBlocked('HARDLINK_SNAPSHOT_FORBIDDEN')
    if snapshot and any(Path(str(path)+suffix).exists() for suffix in ('-wal','-shm','-journal')):
        raise ReleaseBlocked('STANDALONE_CONSISTENT_SNAPSHOT_REQUIRED')
    return path


def flat_broker(snapshot, account_hash):
    if not isinstance(snapshot,dict) or set(snapshot)!={'observed_at','account','orders'}:
        raise ReleaseBlocked('BROKER_SNAPSHOT_SCHEMA_INVALID')
    stamp=pd.Timestamp(snapshot['observed_at'])
    if stamp.tzinfo is None:raise ReleaseBlocked('BROKER_OBSERVATION_TIME_INVALID')
    account=snapshot['account']
    if not isinstance(account,dict) or not isinstance(account.get('account_id'),str) or digest(account['account_id'])!=account_hash:
        raise ReleaseBlocked('BROKER_ACCOUNT_IDENTITY_MISMATCH')
    if account.get('status') not in {'ACCOUNT_ACTIVE','ACCOUNT_STATUS_ACTIVE'}:
        raise ReleaseBlocked('BROKER_ACCOUNT_NOT_ACTIVE')
    positions=account.get('positions')
    if isinstance(positions,list):
        symbols=[row.get('symbol') for row in positions if isinstance(row,dict)]
        if len(symbols)!=len(set(symbols)):raise ReleaseBlocked('DUPLICATE_BROKER_POSITION_ROWS')
    if position_quantities(account) or any(order.active for order in order_views(snapshot['orders'])):
        raise ReleaseBlocked('BROKER_NOT_FLAT_OR_HAS_ACTIVE_ORDERS')
    return stamp


def snapshot_rows(path, expected_sha):
    path=safe_external(path,snapshot=True)
    if not re.fullmatch('[0-9a-f]{64}',expected_sha) or sha(path)!=expected_sha:
        raise ReleaseBlocked('SNAPSHOT_SHA256_MISMATCH')
    db=sqlite3.connect(path.as_uri()+'?mode=ro&immutable=1',uri=True)
    try:
        _validate_acceptance_schema(db)
        expected=sqlite3.connect(':memory:')
        try:
            expected.executescript(_SCHEMA)
            query='SELECT type,name,tbl_name,sql FROM sqlite_master ORDER BY type,name'
            if db.execute(query).fetchall()!=expected.execute(query).fetchall():
                raise ReleaseBlocked('CHANGED_SQLITE_SCHEMA_OBJECTS')
        finally:expected.close()
        if db.execute('PRAGMA integrity_check').fetchone()!=('ok',):raise ReleaseBlocked('SNAPSHOT_INTEGRITY_INVALID')
        state=dict(db.execute('SELECT key,value FROM state ORDER BY key'))
        intents=db.execute('SELECT * FROM intents ORDER BY idempotency_key').fetchall()
        fills=db.execute('SELECT * FROM fills ORDER BY fill_id').fetchall()
    finally:db.close()
    if sha(path)!=expected_sha:raise ReleaseBlocked('SNAPSHOT_CHANGED')
    return path,state,intents,fills


def validate_legacy(state_raw,intents,fills, *, account_hash, data_root, broker):
    state={key:json.loads(value) for key,value in state_raw.items()}
    identity={'schema_id':RUNTIME_SCHEMA,'production_specification_id':PRODUCTION_SPECIFICATION_ID,
              'active_identity':ACTIVE_IDENTITY,'mode':MODE}
    if state.get('database_identity')!=identity:raise ReleaseBlocked('IDENTIFIED_LEGACY_STATE_REQUIRED')
    service={'production_specification_id':PRODUCTION_SPECIFICATION_ID,'active_identity':ACTIVE_IDENTITY,
             'account_hash':account_hash,'stage5_data_commit':STAGE5_DATA_COMMIT}
    if state.get('production_service_identity')!=service:raise ReleaseBlocked('LEGACY_ACCOUNT_SOURCE_IDENTITY_MISMATCH')
    unknown=[key for key in state if key not in FIXED_KEYS and not any(key==f'{prefix}:{symbol}' for prefix in PREFIXES for symbol in INSTRUMENTS)]
    if unknown:raise ReleaseBlocked('UNKNOWN_STATE_KEYS_REQUIRE_REVIEW:'+','.join(sorted(unknown)))
    if state.get('production_positions')!={}:raise ReleaseBlocked('LOCAL_NONFLAT_POSITION_BLOCKS_CUTOVER')
    for key in ('realized_equity','starting_realized_equity'):
        number=Decimal(str(state.get(key)))
        if not number.is_finite() or number<=0:raise ReleaseBlocked('REALIZED_EQUITY_AUTHORITY_MISSING')
    flow=Decimal(str(state.get('explained_external_cash_flows')))
    if not flow.is_finite():raise ReleaseBlocked('CASH_FLOW_AUTHORITY_INVALID')
    cycles=state.get('production_service_cycle_count')
    if type(cycles) is not int or cycles<0:raise ReleaseBlocked('CYCLE_AUTHORITY_INVALID')
    observed=flat_broker(broker,account_hash)
    account=broker['account']
    realized=parse_rest_decimal_value_object(account.get('equity'))-parse_rest_decimal_value_object(account.get('unrealized_profit'))-flow
    if realized!=Decimal(str(state['realized_equity'])):raise ReleaseBlocked('UNEXPLAINED_REALIZED_EQUITY_DISCREPANCY')
    portfolio_authority(account)
    for row in intents:
        payload=json.loads(row[1])
        if row[2] not in TERMINAL_INTENT_STATUSES:raise ReleaseBlocked('UNRESOLVED_INTENT_BLOCKS_CUTOVER')
        if (payload.get('runtime_schema')!=RUNTIME_SCHEMA or payload.get('production_specification_id')!=PRODUCTION_SPECIFICATION_ID
                or payload.get('active_identity')!=ACTIVE_IDENTITY or payload.get('execution_revision') is not None):
            raise ReleaseBlocked('INCOMPATIBLE_OR_UNIDENTIFIED_INTENT')
    for row in fills:
        fill=json.loads(row[7])
        columns=(fill['fill_id'],fill['broker_order_id'],fill['trade_id'],str(fill['quantity']),str(fill['price']),str(fill.get('fee','')),fill['timestamp'])
        if tuple(row[:7])!=columns or not any(r[3]==fill['broker_order_id'] for r in intents):
            raise ReleaseBlocked('FILL_LEDGER_IDENTITY_INVALID')
        for key in ('quantity','price'):
            value=Decimal(str(fill[key]))
            if not value.is_finite() or value<=0:raise ReleaseBlocked('FILL_LEDGER_VALUE_INVALID')
        if pd.Timestamp(fill['timestamp']).tzinfo is None:raise ReleaseBlocked('FILL_LEDGER_TIME_INVALID')
    watermark_inventory={}
    for symbol in INSTRUMENTS:
        seed=load_stage5_seed_open_h1(data_root,symbol)
        continuation_key=f'production_h1_continuation:{symbol}'
        if continuation_key not in state:raise ReleaseBlocked('H1_CONTINUATION_AUTHORITY_MISSING')
        continuation=load_continuation_open_h1(state[continuation_key],symbol,seed)
        latest=seed.index.max() if continuation.empty else continuation.index.max()
        close=latest+pd.Timedelta('1h')
        authority=seed if continuation.empty else pd.concat([seed,continuation])
        if close>observed:raise ReleaseBlocked('H1_AUTHORITY_AFTER_BROKER_OBSERVATION')
        if state.get(f'pending_signal:{symbol}') is not None:raise ReleaseBlocked('PENDING_SIGNAL_BLOCKS_CUTOVER')
        sequence=state.get(f'signal_sequence:{symbol}',0)
        if type(sequence) is not int or sequence<0:raise ReleaseBlocked('SIGNAL_SEQUENCE_INVALID')
        evaluated=state.get(f'last_evaluated_h1:{symbol}')
        if evaluated is None:raise ReleaseBlocked('SIGNAL_WATERMARK_AUTHORITY_MISSING')
        for prefix in ('last_evaluated_h1','last_managed_h1','production_expected_h1'):
            value=state.get(f'{prefix}:{symbol}')
            if value is None:continue
            stamp=pd.Timestamp(value)
            ceiling=latest if prefix=='production_expected_h1' else close
            valid_stamps=authority.index if prefix=='production_expected_h1' else authority.index+pd.Timedelta('1h')
            if stamp.tzinfo is None or stamp>ceiling or stamp not in valid_stamps:
                raise ReleaseBlocked('WATERMARK_NOT_IN_IMMUTABLE_HISTORY_AUTHORITY')
        watermark_inventory[symbol]={'last_evaluated_h1':evaluated,'signal_sequence':sequence,
                                    'latest_immutable_open_h1':latest.isoformat(),'continuation_bars':len(continuation)}
    return state,watermark_inventory


def dry_run(snapshot, expected_sha, out, *, account_hash, source_commit, candidate_commit, data_root, broker):
    """A separately supplied, immutable external snapshot is the only source."""
    _commit(source_commit);_commit(candidate_commit)
    source,state_raw,intents,fills=snapshot_rows(snapshot,expected_sha)
    state,watermarks=validate_legacy(state_raw,intents,fills,account_hash=account_hash,data_root=data_root,broker=broker)
    out=safe_external(out,must_exist=False)
    data_root=Path(data_root).resolve()
    if out.exists() or out==data_root or data_root in out.parents or out==source.parent:
        raise ReleaseBlocked('NEW_ISOLATED_OUTPUT_REQUIRED')
    out.mkdir(parents=True)
    archive=out/'legacy-snapshot.archive.sqlite3'
    shutil.copyfile(source,archive)
    if sha(source)!=expected_sha or sha(archive)!=expected_sha:raise ReleaseBlocked('ARCHIVE_COPY_CHANGED')
    # The entire old ledger remains immutable history; no incompatible intent
    # or fill is upgraded or copied into executable V2 tables.
    root=out/'candidate-root';database=root/'state'/'stage8-12-production.sqlite3'
    runtime=ProductionRuntime(database,execution_revision=EXECUTION_REVISION)
    try:
        with runtime.store.transaction():
            for key,raw in state_raw.items():
                if key!='database_identity':runtime.store.db.execute('INSERT OR REPLACE INTO state VALUES(?,?)',(key,raw))
            runtime.store.put('legacy_ledger_archive',{'sha256':expected_sha,'source_commit':source_commit,
                             'intents':len(intents),'fills':len(fills),'archive':str(archive)})
            runtime.halt('RELEASE_PREPARATION_NOT_AUTHORIZED')
        assert runtime.store.unresolved_intent_count()==0 and runtime.open_positions()=={}
    finally:runtime.close()
    # Restart validates the actual runtime revision, with all causal keys intact.
    runtime=ProductionRuntime(database,execution_revision=EXECUTION_REVISION)
    runtime.close()
    db=sqlite3.connect(database.as_uri()+'?mode=ro&immutable=1',uri=True)
    try:
        preserved=dict(db.execute('SELECT key,value FROM state'))
        if any(preserved.get(k)!=raw for k,raw in state_raw.items() if k!='database_identity'):
            raise ReleaseBlocked('CAUSAL_STATE_NOT_PRESERVED')
    finally:db.close()
    rollback=out/'rollback-restored.sqlite3'
    shutil.copyfile(archive,rollback)
    _,restored_state,restored_intents,restored_fills=snapshot_rows(rollback,expected_sha)
    if (restored_state,restored_intents,restored_fills)!=(state_raw,intents,fills):raise ReleaseBlocked('ROLLBACK_NOT_EXACT')
    result={'schema':SCHEMA,'mode':'ISOLATED_HALTED_READONLY_PREVIEW','execution_revision':EXECUTION_REVISION,
            'runtime_schema':AMENDED_RUNTIME_SCHEMA,'production_specification_id':PRODUCTION_SPECIFICATION_ID,'active_identity':ACTIVE_IDENTITY,
            'source_commit':source_commit,'candidate_commit':candidate_commit,'account_hash':account_hash,'stage5_data_commit':STAGE5_DATA_COMMIT,
            'snapshot_sha256':expected_sha,'archive':str(archive),'archive_sha256':sha(archive),
            'database':str(database),'database_sha256':sha(database),'runtime_root':str(root),
            'data_root':str(data_root),'code_sha256':code_binding(),'state_inventory':sorted(state_raw),
            'watermarks':watermarks,'archived_terminal_intents':len(intents),'archived_fills':len(fills),
            'causal_state_preserved':True,'rollback_exact':True,'pending_signals_activated':0,
            'broker_snapshot_provenance':'CALLER_SUPPLIED_NOT_PHYSICAL_ACCEPTANCE','broker_snapshot_sha256':digest(json.dumps(broker,sort_keys=True)),
            'entry_authorized':False,'live_changes':'NONE','real_order_endpoint_calls':0,'live_production_ready':'NO'}
    manifest=out/'release-manifest.json'
    manifest.write_text(json.dumps(result,indent=2,sort_keys=True)+'\n')
    return manifest,result


def _candidate_state_database(root):
    """Reject internal V2 state/SQLite aliases, even though their names are reserved."""
    database=root/'state'/'stage8-12-production.sqlite3'
    # safe_external(root) has already validated the absolute root and ancestors.
    # The internal names 'state' and stage8-12-production.sqlite3 cannot pass
    # safe_external's ordinary external-file name restrictions.
    for item in (database.parent,database):
        try:
            if item.is_symlink():raise ReleaseBlocked('SYMLINK_PATH_FORBIDDEN')
            metadata=item.lstat()
        except FileNotFoundError:
            raise ReleaseBlocked('ISOLATED_RELEASE_ROOT_REQUIRED') from None
        except OSError as exc:
            raise ReleaseBlocked('PATH_METADATA_UNVERIFIED') from exc
        attributes=getattr(metadata,'st_file_attributes',None)
        if attributes is None and os.name=='nt':
            raise ReleaseBlocked('WINDOWS_REPARSE_AUTHORITY_UNAVAILABLE')
        if attributes is not None and attributes & stat.FILE_ATTRIBUTE_REPARSE_POINT:
            raise ReleaseBlocked('REPARSE_PATH_FORBIDDEN')
    # No symlink, junction or other reparse redirect may change the canonical
    # internal root/state/database identity.
    if database.parent.resolve()!=database.parent or database.resolve()!=database:
        raise ReleaseBlocked('ISOLATED_RELEASE_ROOT_REQUIRED')
    return database


def validate_manifest(path, expected_sha, *, runtime_root, data_root, account_hash, accepted_commit):
    path=safe_external(path)
    if sha(path)!=expected_sha:raise ReleaseBlocked('RELEASE_MANIFEST_SHA256_MISMATCH')
    value=json.loads(path.read_text())
    if (value.get('schema')!=SCHEMA or value.get('mode')!='ISOLATED_HALTED_READONLY_PREVIEW'
            or value.get('execution_revision')!=EXECUTION_REVISION or value.get('runtime_schema')!=AMENDED_RUNTIME_SCHEMA
            or value.get('production_specification_id')!=PRODUCTION_SPECIFICATION_ID or value.get('active_identity')!=ACTIVE_IDENTITY
            or value.get('entry_authorized') is not False or value.get('account_hash')!=account_hash
            or value.get('candidate_commit')!=_commit(accepted_commit) or checkout_commit()!=accepted_commit
            or value.get('code_sha256')!=code_binding() or value.get('code_sha256')!=committed_code_binding(accepted_commit)
            or value.get('stage5_data_commit')!=STAGE5_DATA_COMMIT):
        raise ReleaseBlocked('RELEASE_PROFILE_IDENTITY_OR_CODE_MISMATCH')
    root=safe_external(runtime_root,must_exist=False)
    database=_candidate_state_database(root)
    archive=safe_external(value['archive'],snapshot=True)
    if archive!=path.parent/'legacy-snapshot.archive.sqlite3':raise ReleaseBlocked('BOUND_ARCHIVE_REQUIRED')
    if (str(root)!=value['runtime_root'] or root.parent!=path.parent or str(database)!=value['database']
            or Path(data_root).resolve()!=Path(value['data_root']) or not database.is_file()
            or any(p.is_symlink() for p in (root,database,database.parent))
            or database.stat().st_nlink!=1
            or any(Path(str(database)+suffix).exists() for suffix in ('-wal','-shm','-journal'))
            or (root/'safety'/'stage8-12-4-production-authorization.json').exists()):
        raise ReleaseBlocked('ISOLATED_RELEASE_ROOT_REQUIRED')
    if sha(database)!=value['database_sha256'] or sha(archive)!=value['archive_sha256']:
        raise ReleaseBlocked('RELEASE_STATE_OR_ARCHIVE_CHANGED')
    db=sqlite3.connect(database.as_uri()+'?mode=ro&immutable=1',uri=True)
    try:
        _validate_acceptance_schema(db)
        values={k:json.loads(v) for k,v in db.execute('SELECT key,value FROM state')}
        identity={'schema_id':AMENDED_RUNTIME_SCHEMA,'production_specification_id':PRODUCTION_SPECIFICATION_ID,
                  'active_identity':ACTIVE_IDENTITY,'mode':MODE,'execution_revision':EXECUTION_REVISION}
        if (values.get('database_identity')!=identity or values.get('production_positions')!={}
                or not values.get('execution_halt') or values['execution_halt'].get('status')!='HALTED'
                or db.execute('SELECT COUNT(*) FROM intents').fetchone()!=(0,)
                or db.execute('SELECT COUNT(*) FROM fills').fetchone()!=(0,)):
            raise ReleaseBlocked('HALTED_FLAT_RELEASE_STATE_REQUIRED')
    finally:db.close()
    return value


def main(argv=None):
    import argparse
    parser=argparse.ArgumentParser(description='External immutable snapshot -> isolated HALTED V2 dry-run')
    for flag in ('snapshot','out','stage5-data-root','broker-snapshot'):
        parser.add_argument('--'+flag,type=Path,required=True)
    for flag in ('snapshot-sha256','broker-snapshot-sha256','account-hash','source-commit','candidate-commit'):
        parser.add_argument('--'+flag,required=True)
    args=parser.parse_args(argv)
    try:
        broker_path=safe_external(args.broker_snapshot)
        if sha(broker_path)!=args.broker_snapshot_sha256:raise ReleaseBlocked('BROKER_SNAPSHOT_SHA256_MISMATCH')
        manifest,result=dry_run(args.snapshot,args.snapshot_sha256,args.out,account_hash=args.account_hash,
            source_commit=args.source_commit,candidate_commit=args.candidate_commit,data_root=args.stage5_data_root,
            broker=json.loads(broker_path.read_text()))
        print(json.dumps({'status':'ISOLATED_DRY_RUN_PASS','manifest':str(manifest),'manifest_sha256':sha(manifest),
                          'causal_state_preserved':result['causal_state_preserved'],'rollback_exact':result['rollback_exact'],
                          'real_order_endpoint_calls':0,'live_changes':'NONE'},sort_keys=True));return 0
    except (RuntimeError,ValueError,sqlite3.DatabaseError) as exc:
        print(str(exc));return 1


if __name__=='__main__':raise SystemExit(main())
