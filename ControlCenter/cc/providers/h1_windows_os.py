"""Manual, session-local H1 OS source. No publication or legacy file capability.

Only the click wrapper acquires policy/identity/facts, under the shared manual gate.
The separate C policy lives with protected application code, never data/private.
"""
from datetime import datetime, timezone
import json
from pathlib import Path
import re
from observer.identity import current_identity
from observer.windows_os import TASK, os_facts, envelope
from .h1_contract import timestamp
from .h1_readonly import _pairs, _reject_constant
from .windows_file import read_windows
from .h1_export import ReceiverPolicy, manual_export_refresh, os_snapshot

POLICY_ROOT = Path(__file__).absolute().parents[2] / 'deployment'
POLICY_NAME = 'manual-os-policy.json'
PROCESS_KEYS = {'process_pid', 'process_creation_sha256', 'process_image_sha256',
                'process_command_sha256', 'process_principal_sid'}


def policy_check(p):
    keys = {'schema_id', 'manual_source_approved', 'observer_sid', 'task_name',
            'task_xml_sha256', 'task_principal_sid', 'process_binding',
            'source_id', 'account_alias', 'binding_id', 'snapshot_ttl_seconds', 'os_ttl_seconds'}
    if (type(p) is not dict or set(p) != keys or p['schema_id'] != 'cc03.manual-os-policy.v1'
            or p['manual_source_approved'] is not True or p['task_name'] != TASK):
        raise ValueError('MANUAL_C_SOURCE_APPROVAL_REQUIRED')
    patterns = {'source_id': r'CC03-H1-[A-Z0-9]{8,32}', 'account_alias': r'H1-[A-Z0-9]{4,24}',
                'binding_id': r'[a-f0-9]{64}', 'task_xml_sha256': r'[a-f0-9]{64}',
                'observer_sid': r'S-1-5-21-(?:[0-9]+-){3}[0-9]+',
                'task_principal_sid': r'S-1-5-21-(?:[0-9]+-){3}[0-9]+'}
    for name, pattern in patterns.items():
        if type(p[name]) is not str or not re.fullmatch(pattern, p[name]):
            raise ValueError('MANUAL_OS_IDENTITY_REQUIRED')
    for key in ('snapshot_ttl_seconds', 'os_ttl_seconds'):
        if type(p[key]) is not int or not 1 <= p[key] <= 86400:
            raise ValueError('EXPLICIT_TTL_REQUIRED')
    principals = {p['task_principal_sid']}
    binding = p['process_binding']
    if binding is not None:
        if (type(binding) is not dict or set(binding) != PROCESS_KEYS
                or type(binding['process_pid']) is not int or not 1 <= binding['process_pid'] <= 2**32-1
                or type(binding['process_principal_sid']) is not str
                or not re.fullmatch(patterns['task_principal_sid'], binding['process_principal_sid'])
                or any(type(binding[k]) is not str or not re.fullmatch('[a-f0-9]{64}', binding[k])
                       for k in PROCESS_KEYS if k.endswith('sha256'))):
            raise ValueError('INDEPENDENT_PROCESS_PINS_REQUIRED')
        principals.add(binding['process_principal_sid'])
    if p['observer_sid'] in principals:
        raise ValueError('SEPARATE_STANDARD_CCPANEL_REQUIRED')
    return p


def installed_policy():
    # The existing native reader bounds the operation and authenticates every
    # ancestor/leaf owner, DACL, local NTFS identity and no-reparse boundary.
    raw = read_windows(str(POLICY_ROOT), POLICY_NAME, 16384, admin_policy=True)
    return policy_check(json.loads(raw, object_pairs_hook=_pairs, parse_constant=_reject_constant))


def snapshot():
    p = installed_policy()  # Invalid/duplicate/missing policy -> zero diagnostic calls.
    sid, unsafe = current_identity()
    if unsafe or sid != p['observer_sid']:
        raise ValueError('STANDARD_CCPANEL_PRIMARY_TOKEN_REQUIRED')
    query = dict(task_name=p['task_name'], task_xml_sha256=p['task_xml_sha256'],
                 task_principal_sid=p['task_principal_sid'], process_enabled=p['process_binding'] is not None,
                 require_ccpanel=True, observer_sid=p['observer_sid'])
    if p['process_binding'] is not None:
        query.update(p['process_binding'])
    started = datetime.now(timezone.utc)
    facts = os_facts(query)  # Exactly ONE fixed helper, total timeout <=6s. No retry.
    value = envelope(p, facts)  # Strict OS schema, timestamps, reasons, no extra fields.
    for name, row in facts.items():
        if timestamp(row['observed_at']) < started:
            raise ValueError('OLD_DIAGNOSTIC_RESULT')
        expected = p['task_xml_sha256'] if name == 'task' else query.get('process_command_sha256')
        if row['state'] != 'UNKNOWN' and row['value'] != expected:
            raise ValueError('OS_RESULT_IDENTITY_MISMATCH')
    if not query['process_enabled'] and facts['process']['state'] != 'UNKNOWN':
        raise ValueError('UNAPPROVED_PROCESS_RESULT')
    if facts['task']['state'] == 'UNKNOWN' and facts['process']['state'] != 'UNKNOWN':
        raise ValueError('TASK_BRACKET_REQUIRED')
    receiver = ReceiverPolicy(source_id=p['source_id'], account_alias=p['account_alias'],
        binding_id=p['binding_id'], snapshot=p['snapshot_ttl_seconds'], os_observations=p['os_ttl_seconds'])
    # Receipt occurs AFTER acquisition. UI startup time cannot make new facts future-dated.
    return os_snapshot(value, receiver, datetime.now(timezone.utc), manual=True)


def manual_os_refresh(now):
    return manual_export_refresh(now, reader=snapshot, windows_os=True)
