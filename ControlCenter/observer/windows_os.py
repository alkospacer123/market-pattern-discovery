"""One-shot independent observer; --execute requires protected local OS policy.

No live JSON, production DB, trading import, broker API or arbitrary UI command.
Default invocation is preview. All positive facts have WINDOWS_OS_ONLY authority.
"""
import argparse
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import re
import subprocess
from cc.deployment_paths import data_root
from cc.providers.h1_contract import MAX_BYTES, timestamp, validate
from cc.providers.h1_readonly import canonical_digest, _pairs, _reject_constant
from cc.providers.os_contract import SCHEMA, SCHEMA_ID, GROUPS, check_semantics
from cc.providers.windows_file import read_windows
from exporter.snapshot import publish
from .metadata import probe

TASK = 'TradingSystemLab-Stage8-Production'
SCRIPT = Path(__file__).with_name('Read-OsFacts.ps1')
POLICY_ROOT = data_root() / 'private'
MAX_OPERATION_SECONDS = 6


def policy_check(p):
    required = {'schema_id', 'os_policy_approved', 'source_id', 'account_alias', 'binding_id',
                'observer_sid', 'task_name', 'task_xml_sha256', 'task_principal_sid',
                'process_enabled', 'process_pid', 'process_creation_sha256', 'process_image_sha256', 'process_command_sha256', 'process_principal_sid',
                'metadata_enabled', 'heartbeat_root', 'heartbeat_root_id', 'kill_switch_root', 'kill_switch_root_id',
                'export_root_id'}
    if (type(p) is not dict or set(p) != required or p['schema_id'] != 'cc03.os-policy.v1'
            or p['os_policy_approved'] is not True or p['task_name'] != TASK
            or type(p['process_enabled']) is not bool or type(p['metadata_enabled']) is not bool):
        raise ValueError('OS_POLICY_UNAPPROVED')
    patterns = {'source_id': r'CC03-H1-[A-Z0-9]{8,32}', 'account_alias': r'H1-[A-Z0-9]{4,24}',
                'binding_id': r'[a-f0-9]{64}', 'task_xml_sha256': r'[a-f0-9]{64}',
                'process_creation_sha256': r'[a-f0-9]{64}', 'process_image_sha256': r'[a-f0-9]{64}', 'process_command_sha256': r'[a-f0-9]{64}',
                'observer_sid': r'S-1-5-21-[0-9-]{5,100}', 'task_principal_sid': r'S-1-[0-9-]{3,100}',
                'process_principal_sid': r'S-1-[0-9-]{3,100}'}
    for key, pattern in patterns.items():
        if type(p[key]) is not str or not re.fullmatch(pattern, p[key]):
            raise ValueError('OS_IDENTITY_REQUIRED')
    if type(p['process_pid']) is not int or not 1 <= p['process_pid'] <= 2**32-1:
        raise ValueError('PINNED_PROCESS_REQUIRED')
    if p['observer_sid'] in (p['task_principal_sid'], p['process_principal_sid']):
        raise ValueError('SEPARATE_IDENTITY_REQUIRED')
    for key in ('export_root_id', 'heartbeat_root_id', 'kill_switch_root_id'):
        if type(p[key]) is not list or len(p[key]) != 3 or any(type(x) is not int or x < 0 for x in p[key]):
            raise ValueError('OS_ROOT_PIN_REQUIRED')
    return p


def row(source, state='UNKNOWN', reason='UNAVAILABLE', value=None, at=None):
    return dict(source=source, state=state, reason=reason,
                observed_at=(at or datetime.now(timezone.utc)).isoformat(),
                confidence='UNKNOWN' if state == 'UNKNOWN' else 'OS_OBSERVED', value=value)


def os_facts(policy, script=SCRIPT, timeout=MAX_OPERATION_SECONDS):
    # Fixed Windows binary and reviewed script; no shell=True / -Command / UI input.
    executable = Path(os.environ.get('SYSTEMROOT', r'C:\Windows')) / 'System32/WindowsPowerShell/v1.0/powershell.exe'
    sources = dict(task='WINDOWS_TASK_READONLY', process='WINDOWS_PROCESS_READONLY')
    try:
        # Do not inherit broker credentials or arbitrary PowerShell module paths.
        environment = {name: os.environ[name] for name in (
            'SYSTEMROOT','SYSTEMDRIVE','WINDIR','TEMP','TMP','USERPROFILE','APPDATA','LOCALAPPDATA',
            'PROGRAMFILES','PROGRAMFILES(X86)','COMSPEC','COMPUTERNAME') if name in os.environ}
        environment['PSModulePath'] = os.pathsep.join((
            str(executable.parent / 'Modules'),
            str(Path(os.environ.get('PROGRAMFILES', r'C:\Program Files')) / 'WindowsPowerShell/Modules')))
        environment['PATH'] = str(executable.parent) + os.pathsep + str(executable.parents[2])
        completed = subprocess.run([str(executable), '-NoLogo', '-NoProfile', '-NonInteractive',
                                    '-File', str(script)], input=json.dumps(policy),
                                   capture_output=True, text=True, timeout=timeout,
                                   env=environment,
                                   creationflags=subprocess.CREATE_NO_WINDOW)
        if completed.returncode or len(completed.stdout) > 8192:
            raise ValueError('OS_PROBE_FAILED')
        value = json.loads(completed.stdout, object_pairs_hook=_pairs, parse_constant=_reject_constant)
        if set(value) != set(sources):
            raise ValueError('OS_PROBE_FAILED')
        return {name: dict(source=source, **value[name]) for name, source in sources.items()}
    except subprocess.TimeoutExpired:
        return {name: row(source, reason='TIMEOUT') for name, source in sources.items()}
    except Exception:
        return {name: row(source) for name, source in sources.items()}


def collect(policy, facts=None, metadata=None):
    policy_check(policy)
    facts = os_facts if facts is None else facts
    metadata = probe if metadata is None else metadata
    value = dict(schema_id=SCHEMA_ID, payload_sha256='0'*64, generated_at='',
                 identity=dict(robot_id='H1', source_id=policy['source_id'], account_alias=policy['account_alias'],
                               binding_id=policy['binding_id'], account_binding='UNVERIFIED', authority='WINDOWS_OS_ONLY'))
    value.update(facts(policy))
    for group, root_key, filename in (
        ('heartbeat_metadata', 'heartbeat_root', 'stage8-12-4-production-heartbeat.json'),
        ('kill_switch_metadata', 'kill_switch_root', 'stage8-trading-kill-switch.json')):
        state, reason, result = ('UNKNOWN', 'DISABLED', None)
        if policy['metadata_enabled']:
            state, reason, result = metadata(policy[root_key], filename, policy[root_key+'_id'])
        value[group] = row('WINDOWS_FILE_METADATA', state, reason, result)
    value['generated_at'] = datetime.now(timezone.utc).isoformat()
    value['payload_sha256'] = canonical_digest(value)
    validate(value, SCHEMA)
    check_semantics(value, timestamp)
    return value


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--execute', action='store_true')
    args = parser.parse_args()
    if not args.execute:
        print('PREVIEW: independent WINDOWS_OS_ONLY observer; no production content or trading action')
        return
    try:
        if os.name != 'nt':
            raise ValueError('WINDOWS_REQUIRED')
        from .identity import current_identity
        sid, elevated = current_identity()
        p = json.loads(read_windows(str(POLICY_ROOT), 'os-policy.json', MAX_BYTES, admin_policy=True),
                       object_pairs_hook=_pairs, parse_constant=_reject_constant)
        policy_check(p)
        if elevated or sid != p['observer_sid']:
            raise ValueError('OBSERVER_IDENTITY_INVALID')
        publish(collect(p), expected_root=p['export_root_id'])
        print('CC03_WINDOWS_OS_SNAPSHOT_PUBLISHED_NO_TRADING_AUTHORITY')
    except Exception:
        print('CC03_OS_OBSERVER_UNAVAILABLE')
        raise SystemExit(1)


if __name__ == '__main__':
    main()
