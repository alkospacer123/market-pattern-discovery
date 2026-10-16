"""CC-owned immutable publication. Legacy live collection is disabled, no engine/DB/API.

Publication destination is fixed under the independent Control Center data tree.
Private policy and output directory must be provisioned/ACL-audited separately.
"""
import argparse
from datetime import datetime, timezone
import json
import os
from pathlib import Path
import re
import tempfile
import hashlib
import time
import uuid
from cc.providers.h1_contract import ACTIVE, SPEC, ACCEPTED_COMMIT, MAX_BYTES, timestamp, validate
from cc.providers.h1_readonly import canonical_digest, _pairs, _reject_constant
from cc.providers.readonly_file import read_source
from cc.providers.windows_file import read_windows, components, WinAPI, MAX_ENTRIES
from cc.providers.source_contract import SCHEMA, SCHEMA_ID
from cc.deployment_paths import data_root

DATA_ROOT = data_root()
EXPORT_ROOT = DATA_ROOT / 'export'
POLICY_ROOT = DATA_ROOT / 'private'
HB = 'stage8-12-4-production-heartbeat.json'
KS = 'stage8-trading-kill-switch.json'


def decode(raw):
    if not 0 < len(raw) <= MAX_BYTES:
        raise ValueError('SIZE_INVALID')
    return json.loads(raw.decode('utf-8'), object_pairs_hook=_pairs, parse_constant=_reject_constant)


def policy_check(policy):
    required = {'schema_id', 'source_id', 'account_alias', 'binding_id', 'expected_account_hash',
                'installed_code_commit', 'installed_commit_verified', 'sources_acl_approved',
                'binding_approved', 'heartbeat_root', 'heartbeat_root_id', 'kill_switch_root', 'kill_switch_root_id'}
    if (type(policy) is not dict or set(policy) != required or policy['schema_id'] != 'cc03.private-source-policy.v1'
            or policy['installed_code_commit'] != ACCEPTED_COMMIT
            or policy['installed_commit_verified'] is not True or policy['sources_acl_approved'] is not True
            or type(policy['binding_approved']) is not bool):
        raise ValueError('SOURCE_APPROVAL_REQUIRED')
    for key, pattern in [('source_id', r'CC03-H1-[A-Z0-9]{8,32}'), ('account_alias', r'H1-[A-Z0-9]{4,24}'),
                         ('binding_id', r'[a-f0-9]{64}'), ('expected_account_hash', r'[a-f0-9]{64}')]:
        if type(policy[key]) is not str or not re.fullmatch(pattern, policy[key]):
            raise ValueError('BINDING_INVALID')
    for key in ('heartbeat_root_id', 'kill_switch_root_id'):
        if type(policy[key]) is not list or len(policy[key]) != 3 or any(type(x) is not int or x < 0 for x in policy[key]):
            raise ValueError('ROOT_PIN_REQUIRED')
    return policy


def stamp(at):
    return at.astimezone(timezone.utc).isoformat()


def collect(policy, now, reader=None):
    policy_check(policy)
    if reader is None:
        raise ValueError('CC03_LIVE_SOURCE_COMPATIBILITY_BLOCKED')
    identity = dict(robot_id='H1', strategy_id='T3/H1/TRAIL1', production_specification_id=SPEC,
                    active_identity=ACTIVE, installed_code_commit=ACCEPTED_COMMIT,
                    source_id=policy['source_id'], account_alias=policy['account_alias'],
                    binding_id=policy['binding_id'], account_binding='UNVERIFIED')
    def missing(source):
        return dict(source=source, status='NEEDS_SOURCE_APPROVAL', observed_at=None, value=None)
    result = dict(schema_id=SCHEMA_ID, payload_sha256='0'*64, generated_at=stamp(now), identity=identity,
                  heartbeat=missing('H1_PRODUCTION_HEARTBEAT'), reconciliation=missing('H1_PRODUCTION_HEARTBEAT'),
                  kill_switch=missing('H1_KILL_SWITCH_FILE'), task=missing('WINDOWS_TASK_PROBE'),
                  candles=missing('APPROVED_H1_CALENDAR'), finances=missing('APPROVED_ACCOUNT_FINANCE'),
                  execution=missing('APPROVED_EXECUTION_EVENTS'))
    try:
        value = decode(reader(policy['heartbeat_root'], HB, policy['heartbeat_root_id']))
        expected = {'schema_id','production_specification_id','active_identity','accepted_code_commit','account_hash',
                    'timestamp','last_successful_finam_api_contact','reconciliation_status','unresolved_intent_count',
                    'health_status','cycle_count','open_position_count','active_protective_stop_count','position_protection'}
        if (set(value) != expected or value['schema_id'] != 'stage8_12_4_production_heartbeat.v1'
                or value['production_specification_id'] != SPEC or value['active_identity'] != ACTIVE
                or value['accepted_code_commit'] != ACCEPTED_COMMIT
                or value['account_hash'] != policy['expected_account_hash']):
            raise ValueError('SOURCE_IDENTITY_INVALID')
        at, contact = timestamp(value['timestamp']), timestamp(value['last_successful_finam_api_contact'])
        if at is None or contact is None or not contact <= at <= now:
            raise ValueError('SOURCE_TIME_INVALID')
        for key in ('unresolved_intent_count','cycle_count','open_position_count','active_protective_stop_count'):
            if type(value[key]) is not int or not 0 <= value[key] <= 100000000:
                raise ValueError('COUNTER_INVALID')
        if value['health_status'] not in ('HEALTHY','UNHEALTHY') or value['reconciliation_status'] not in ('PASS','FAULT'):
            raise ValueError('STATUS_INVALID')
        result['heartbeat'].update(status='AVAILABLE', observed_at=stamp(at),
            value=dict(state=value['health_status'], last_api_contact_at=stamp(contact)))
        result['reconciliation'].update(status='AVAILABLE', observed_at=stamp(at),
            value=dict(state=value['reconciliation_status'], unresolved_intents=value['unresolved_intent_count']))
        if policy['binding_approved']:
            identity['account_binding'] = 'MATCHED_LOCAL_POLICY'
    except Exception:
        result['heartbeat']['status'] = result['reconciliation']['status'] = 'INVALID'
    try:
        value = decode(reader(policy['kill_switch_root'], KS, policy['kill_switch_root_id']))
        if (set(value) != {'schema_id','production_specification_id','state','generation','updated_utc'}
                or value['schema_id'] != 'stage8_trading_kill_switch.v1' or value['production_specification_id'] != SPEC
                or value['state'] not in ('HALTED','ARMED') or type(value['generation']) is not int or value['generation'] < 1
                or timestamp(value['updated_utc']) is None or timestamp(value['updated_utc']) > now):
            raise ValueError('KILL_SWITCH_INVALID')
        result['kill_switch'].update(status='AVAILABLE', observed_at=stamp(now),
            value=dict(state=value['state'], updated_at=value['updated_utc']))
    except Exception:
        result['kill_switch']['status'] = 'INVALID'
    result['payload_sha256'] = canonical_digest(result)
    validate(result, SCHEMA)
    return result


def publish(value):
    # Fixed, separately provisioned local export directory. No source-derived paths.
    # Root must be protected against reparse/ACL substitution by installation policy.
    if os.name != 'nt' or not EXPORT_ROOT.is_dir() or EXPORT_ROOT.is_symlink() or getattr(EXPORT_ROOT, "is_junction", lambda: False)():
        raise ValueError('EXPORT_DIRECTORY_NOT_ACCEPTED')
    validate(value, SCHEMA)
    if value['payload_sha256'] != canonical_digest(value):
        raise ValueError('EXPORT_INTEGRITY_INVALID')
    raw = json.dumps(value, sort_keys=True, separators=(',', ':'), allow_nan=False).encode('ascii')
    if len(raw) > MAX_BYTES:
        raise ValueError('EXPORT_TOO_LARGE')
    name = f'h1-{time.time_ns():020d}-{uuid.uuid4().hex}-{hashlib.sha256(raw).hexdigest()}.json'
    api, held = WinAPI(), []
    try:
        directories, _ = components(str(EXPORT_ROOT), 'h1.snapshot.json')
        api.volume(directories[0])
        for path in directories:
            handle = api.open(path, True)
            held.append(handle)
            api.info(handle, path, True)
        with os.scandir(EXPORT_ROOT) as entries:
            for index, _ in enumerate(entries):
                if index >= MAX_ENTRIES - 1:
                    raise ValueError('EXPORT_DIRECTORY_FULL')
        fd, temporary = tempfile.mkstemp(prefix='.cc03-', suffix='.tmp', dir=EXPORT_ROOT)
        try:
            with os.fdopen(fd, 'wb') as stream:
                stream.write(raw)
                stream.flush()
                os.fsync(stream.fileno())
            # Windows rename fails if the unique destination already exists.
            # Never overwrite/delete an open published snapshot. Completed names
            # appear only after close+fsync; temp names are never consumed.
            os.rename(temporary, EXPORT_ROOT / name)
            return EXPORT_ROOT / name
        finally:
            if os.path.exists(temporary):
                os.unlink(temporary)
    finally:
        for handle in reversed(held):
            api.close(handle)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--execute', action='store_true', help='Read approved sources and publish once; default is preview')
    args = parser.parse_args()
    if not args.execute:
        print('PREVIEW: legacy live source BLOCKED; immutable Control Center transport only; no production action')
        return
    try:
        if os.name != 'nt':
            raise ValueError('WINDOWS_REQUIRED')
        policy = decode(read_windows(str(POLICY_ROOT).replace('/', '\\'), 'source-policy.json', MAX_BYTES, admin_policy=True))
        publish(collect(policy, datetime.now(timezone.utc)))
        print('CC03_EXPORT_PUBLISHED_AUTHORITY_LIMITED')
    except Exception as exc:
        print('CC03_EXPORT_UNAVAILABLE')
        if str(exc) == 'CC03_LIVE_SOURCE_COMPATIBILITY_BLOCKED':
            print('CC03_LIVE_SOURCE_COMPATIBILITY_BLOCKED')
        raise SystemExit(1)


if __name__ == '__main__':
    main()
