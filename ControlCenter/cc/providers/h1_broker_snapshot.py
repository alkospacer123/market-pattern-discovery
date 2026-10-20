"""Manual receiver for admin-owned CC-only FINAM read-only observations.

No broker API, credential, H1 filesystem, mutation, or background polling.
A received API-response clock is NOT an original broker snapshot timestamp.
"""
from datetime import datetime, timezone, timedelta
import json
from pathlib import Path
import re

from ..deployment_paths import data_root
from ..manual_gate import export_gate
from .h1_readonly import _pairs, _reject_constant
from .windows_file import read_windows, read_latest_windows

ROOT = data_root() / 'broker-readonly'
POLICY_ROOT = Path(__file__).absolute().parents[2] / 'deployment'
POLICY = 'broker-readonly-policy.json'
SPEC = 'PROD_STAGE7_46DB784378797C7FB04636892350AFF21006D71A31F2CED9D4B974EDA2DC36B8'
PROBE = '33668f23c7ffb774e198b4f7ef55c85d73a6d407cd84b2a3cb1ea5bd6a97fc7c'
SCHEMA = 'cc03.h1-broker-readonly.observation.v1'
SOURCE = 'CC03-H1-FINAMREADONLY'
N4 = ('USDRUBF', 'CNYRUBF', 'GLDRUBF', 'IMOEXF')
HEX = re.compile(r'[a-f0-9]{64}\Z')
STAMP = re.compile(r'\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}Z\Z')
POLICY_KEYS = {'schema_id', 'source_approved', 'export_root_id', 'principal_sid_sha256',
               'credential_blob_sha256', 'probe_sha256', 'received_ttl_seconds'}
DATA_KEYS = {'schema_id', 'robot_id', 'source_id', 'production_id', 'probe_sha256',
             'principal_sid_sha256', 'credential_blob_sha256', 'received_at_utc',
             'broker_original_snapshot_timestamp', 'readonly_session_verified',
             'account_response_identity_verified', 'position_contracts',
             'other_nonzero_position_symbols', 'order_rows', 'active_order_rows',
             'active_sltp_order_rows', 'positions_complete', 'orders_complete',
             'h1_account_ownership_verified', 'stop_coverage_verified'}


def _hex(value):
    return type(value) is str and HEX.fullmatch(value) is not None


def _limit(value, limit=1000000):
    return type(value) is int and 0 <= value <= limit


def _receipt(value):
    if type(value) is not str or STAMP.fullmatch(value) is None:
        raise ValueError('INVALID_RECEIPT')
    return datetime.strptime(value, '%Y-%m-%dT%H:%M:%SZ').replace(tzinfo=timezone.utc)


def _policy(value):
    if (type(value) is not dict or set(value) != POLICY_KEYS
            or value['schema_id'] != 'cc03.broker-readonly-policy.v1'
            or value['source_approved'] is not True or value['probe_sha256'] != PROBE
            or not _hex(value['principal_sid_sha256'])
            or not _hex(value['credential_blob_sha256'])
            or type(value['received_ttl_seconds']) is not int
            or not 30 <= value['received_ttl_seconds'] <= 600):
        raise ValueError('SOURCE_NOT_APPROVED')
    pin = value['export_root_id']
    if (type(pin) is not list or len(pin) != 3
            or any(type(v) is not int or not 0 <= v <= 2**32-1 for v in pin)):
        raise ValueError('ROOT_PIN_INVALID')
    return value


def validate(raw, policy, now):
    """Return display-only facts. A zero is an observed response row count, not verified flat."""
    if type(raw) is not bytes or not 0 < len(raw) <= 16384:
        raise ValueError('CAPTURE_SIZE_INVALID')
    value = json.loads(raw.decode('utf-8'), object_pairs_hook=_pairs, parse_constant=_reject_constant)
    if (type(value) is not dict or set(value) != DATA_KEYS
            or value['schema_id'] != SCHEMA or value['source_id'] != SOURCE
            or value['robot_id'] != 'H1' or value['production_id'] != SPEC
            or value['probe_sha256'] != PROBE
            or value['principal_sid_sha256'] != policy['principal_sid_sha256']
            or value['credential_blob_sha256'] != policy['credential_blob_sha256']):
        raise ValueError('CAPTURE_BINDING_INVALID')
    for key in ('readonly_session_verified', 'account_response_identity_verified'):
        if value[key] is not True:
            raise ValueError('BROKER_READONLY_NOT_VERIFIED')
    if (value['broker_original_snapshot_timestamp'] is not None
            or any(value[key] is not False for key in
                   ('positions_complete', 'orders_complete', 'h1_account_ownership_verified',
                    'stop_coverage_verified'))):
        raise ValueError('UNSUPPORTED_AUTHORITY')
    quantities = value['position_contracts']
    if (type(quantities) is not dict or set(quantities) != set(N4)
            or any(type(q) is not int or abs(q) > 10000000 for q in quantities.values())):
        raise ValueError('N4_INVALID')
    for name in ('other_nonzero_position_symbols', 'order_rows', 'active_order_rows',
                 'active_sltp_order_rows'):
        if not _limit(value[name]):
            raise ValueError('COUNTS_INVALID')
    if not (value['active_sltp_order_rows'] <= value['active_order_rows'] <= value['order_rows']):
        raise ValueError('ORDER_COUNTS_INVALID')
    received = _receipt(value['received_at_utc'])
    now = now.astimezone(timezone.utc)
    if received > now + timedelta(seconds=10):
        raise ValueError('FUTURE_RECEIPT')
    status = 'CURRENT' if now - received <= timedelta(seconds=policy['received_ttl_seconds']) else 'STALE'
    return dict(status=status, received_at=received, quantities={s: quantities[s] for s in N4},
                other_nonzero=value['other_nonzero_position_symbols'],
                order_rows=value['order_rows'], active_orders=value['active_order_rows'],
                active_sltp=value['active_sltp_order_rows'],
                account_identity='FINAM_REAL_READONLY_ACCOUNT_RESPONSE',
                original_source_timestamp=None,
                h1_account_ownership='UNVERIFIED', stop_coverage='UNVERIFIED',
                completeness='NOT_PROVEN_BY_API_RESPONSE')


def manual_broker_refresh(now):
    """At most one CC-owned file read, only on explicit UI click. No FINAM request."""
    unavailable = dict(status='UNKNOWN', reason='BROKER_SNAPSHOT_UNAVAILABLE')
    try:
        with export_gate() as acquired:
            if not acquired:
                return dict(status='UNKNOWN', reason='BROKER_SNAPSHOT_BUSY')
            policy_raw = read_windows(str(POLICY_ROOT), POLICY, 4096, admin_policy=True)
            policy = _policy(json.loads(policy_raw.decode('utf-8'),
                                        object_pairs_hook=_pairs, parse_constant=_reject_constant))
            raw = read_latest_windows(ROOT, 16384, policy['export_root_id'])
            return validate(raw, policy, now)
    except Exception:
        return unavailable


def age(observation, now, ttl=600):
    """Never let an earlier cache become CURRENT after expiry or clock rewind."""
    if observation is None:
        return dict(status='UNKNOWN', reason='MANUAL_REFRESH_REQUIRED')
    if observation.get('status') != 'CURRENT':
        return observation
    if now < observation['received_at'] or now - observation['received_at'] > timedelta(seconds=ttl):
        return dict(observation, status='STALE')
    return observation
