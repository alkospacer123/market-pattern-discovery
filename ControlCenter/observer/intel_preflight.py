"""Operator-only, one-shot CC-03 physical READONLY preflight. Default: PREVIEW.

Separate permission A; never installs CC, publishes an export, or approves source C.
Only a protected private preflight policy can enable the fixed production Task.
"""
import argparse
from datetime import datetime, timezone
import json
import os
from pathlib import Path
import re
import subprocess
from cc.deployment_paths import data_root
from cc.providers.h1_readonly import _pairs, _reject_constant
from cc.providers.windows_file import read_windows
from .identity import current_identity
from .windows_os import TASK, os_facts

# Reviewed standalone package; does not require provisioned CC roots.
POLICY_ROOT = Path(__file__).absolute().parents[1] / 'deployment'
READINESS_SCRIPT = Path(__file__).with_name('Read-PreflightReadiness.ps1')
PROCESS_KEYS = {'process_pid', 'process_creation_sha256', 'process_image_sha256',
                'process_command_sha256', 'process_principal_sid'}
UNKNOWN_FACTS = ('ROBOT_HEALTHY', 'BROKER_CONNECTED', 'TRADING_AUTHORIZED', 'POSITION_FLAT',
                 'STOP_PROTECTED', 'POSITIONS', 'ORDERS', 'FILLS', 'SLTP', 'CAPITAL', 'PNL')
PREVIEW = dict(mode='PREVIEW', outcome='NOT_VERIFIED', intel_execution='NOT_EXECUTED',
    checks=['own non-elevated standard SID', 'one exact approved Task XML/principal/state before and after',
            'optional already-approved PID/creation/image/command/owner binding; no discovery',
            'one existing enabled ccpanel SID and fixed own roots only; no provisioning'],
    permissions=['A: explicit limited READONLY preflight permission + protected private preflight-policy.json',
                 'existing Task Scheduler read and optional exact-PID CIM read under current token',
                 'existing own CC directory/SID read; never production ACL changes',
                 'B: installation and C: OS source/export require separate later decisions'],
    possible_results=['TASK_IDENTITY_MATCHED', 'TASK_RUNNING_OBSERVED', 'PROCESS_IDENTITY_MATCHED',
                      'PROCESS_UNKNOWN', 'ACCESS_DENIED', 'CCPANEL_NOT_PROVISIONED', 'CCPANEL_DISABLED',
                      'OS_SOURCE_APPROVAL_REQUIRED', 'UNKNOWN'],
    forbidden=['H1 file content/metadata', 'broker/token/SQLite/WAL access', 'Task/process mutation',
               'installation, users, ACL changes, OS export'],
    trading={key: 'UNKNOWN' for key in UNKNOWN_FACTS})


def valid_sid(value):
    return type(value) is str and re.fullmatch(r'S-1-5-21-(?:[0-9]+-){3}[0-9]+', value) is not None


def policy_check(p):
    # Only the unused-null v1 exporter field can migrate without a new decision.
    # Never silently discard a configured exporter identity or infer observer_sid.
    if type(p) is dict and p.get('schema_id') == 'cc03.intel-preflight-policy.v1':
        if 'cc_exporter_sid' not in p or p['cc_exporter_sid'] is not None:
            raise ValueError('EXPLICIT_SINGLE_CCPANEL_MIGRATION_REQUIRED')
        p = dict(p)
        del p['cc_exporter_sid']
        p['schema_id'] = 'cc03.intel-preflight-policy.v2'
    keys = {'schema_id', 'readonly_preflight_approved', 'observer_sid', 'task_name',
            'task_xml_sha256', 'task_principal_sid', 'process_binding', 'cc_panel_sid'}
    if (type(p) is not dict or set(p) != keys or p['schema_id'] != 'cc03.intel-preflight-policy.v2'
            or p['readonly_preflight_approved'] is not True or p['task_name'] != TASK
            or not valid_sid(p['observer_sid']) or not valid_sid(p['task_principal_sid'])
            or type(p['task_xml_sha256']) is not str
            or not re.fullmatch('[a-f0-9]{64}', p['task_xml_sha256'])):
        raise ValueError('PREFLIGHT_APPROVAL_REQUIRED')
    binding = p['process_binding']
    production_sids = {p['task_principal_sid']}
    if binding is not None:
        if (type(binding) is not dict or set(binding) != PROCESS_KEYS
                or type(binding['process_pid']) is not int or not 1 <= binding['process_pid'] <= 2**32-1
                or not valid_sid(binding['process_principal_sid'])
                or any(type(binding[k]) is not str or not re.fullmatch('[a-f0-9]{64}', binding[k])
                       for k in PROCESS_KEYS if k.endswith('sha256'))):
            raise ValueError('PINNED_PROCESS_INVALID')
        production_sids.add(binding['process_principal_sid'])
    cc = [p['cc_panel_sid']]
    if (p['observer_sid'] in production_sids
            or any(s is not None and (not valid_sid(s) or s in production_sids) for s in cc)):
        raise ValueError('SEPARATE_STANDARD_IDENTITIES_REQUIRED')
    return p


def readiness(policy):
    """Fixed own roots only. No H1 path is accepted, resolved or enumerated."""
    executable = Path(os.environ.get('SYSTEMROOT', r'C:\Windows')) / 'System32/WindowsPowerShell/v1.0/powershell.exe'
    # Resolve all six CC-only paths from the exact deployment path contract.
    # This preserves the disposable CI sandbox and the approved Intel root,
    # without probing legacy installation paths or any production H1 files.
    data = data_root()
    roots = [str(data.parent / 'app'), str(data.parent / 'venv'), str(data)]
    roots += [str(data / part) for part in ('export', 'logs', 'private')]
    environment = {k: os.environ[k] for k in ('SYSTEMROOT', 'SYSTEMDRIVE', 'WINDIR', 'TEMP', 'TMP',
                    'USERPROFILE', 'APPDATA', 'LOCALAPPDATA', 'PROGRAMFILES',
                    'PROGRAMFILES(X86)', 'COMSPEC', 'COMPUTERNAME') if k in os.environ}
    environment['PSModulePath'] = os.pathsep.join((str(executable.parent / 'Modules'),
        str(Path(os.environ.get('PROGRAMFILES', r'C:\Program Files')) / 'WindowsPowerShell/Modules')))
    environment['PATH'] = str(executable.parent) + os.pathsep + str(executable.parents[2])
    payload = dict(cc_panel_sid=policy['cc_panel_sid'], roots=roots)
    try:
        result = subprocess.run([str(executable), '-NoLogo', '-NoProfile', '-NonInteractive',
                                 '-ExecutionPolicy', 'Bypass', '-File', str(READINESS_SCRIPT)], input=json.dumps(payload),
                                capture_output=True, text=True, timeout=6, env=environment,
                                creationflags=subprocess.CREATE_NO_WINDOW)
        value = json.loads(result.stdout, object_pairs_hook=_pairs, parse_constant=_reject_constant)
        if result.returncode or set(value) != {'observer_standard', 'identities', 'directories'}:
            raise ValueError('READINESS_UNAVAILABLE')
        if (type(value['observer_standard']) is not bool
                or value['identities'] not in {'CCPANEL_ENABLED', 'CCPANEL_NOT_PROVISIONED', 'CCPANEL_DISABLED',
                                                'CCPANEL_SID_MISMATCH', 'CCPANEL_PRIVILEGED', 'UNKNOWN'}
                or value['directories'] not in {'EXISTING_ROOTS_OBSERVED', 'NOT_PROVISIONED', 'ACCESS_DENIED', 'UNKNOWN'}):
            raise ValueError('READINESS_UNAVAILABLE')
        return value
    except Exception:
        return dict(observer_standard=False, identities='UNKNOWN', directories='UNKNOWN')


def empty_report(reason='UNAVAILABLE'):
    return dict(schema_id='cc03.intel-preflight-report.v2', mode='EXECUTE', outcome='NOT_VERIFIED',
        observed_at=datetime.now(timezone.utc).isoformat(), own_identity='UNKNOWN',
        task_identity='UNKNOWN', task_state='UNKNOWN', task_before_after='UNKNOWN',
        process='PROCESS_UNKNOWN', task_access='UNKNOWN', process_access='UNKNOWN',
        cc_identities='UNKNOWN', cc_installation='NOT_VERIFIED', cc_directories='UNKNOWN', cc_acl='NOT_VERIFIED',
        os_source='OS_SOURCE_APPROVAL_REQUIRED', reason=reason,
        trading={key: 'UNKNOWN' for key in UNKNOWN_FACTS})


def execute(policy, *, identity=None, facts=None, cc_readiness=None):
    """Dependencies are injectable for disposable tests; CLI exposes no override."""
    report = empty_report()
    policy = policy_check(policy)  # reject before identity, Task/process or root probing
    identity = current_identity if identity is None else identity
    facts = os_facts if facts is None else facts
    cc_readiness = readiness if cc_readiness is None else cc_readiness
    sid, elevated = identity()
    if elevated or sid != policy['observer_sid']:
        report.update(outcome='BLOCKED', reason='OBSERVER_IDENTITY_INVALID')
        return report
    ready = cc_readiness(policy)
    report.update(cc_identities=ready['identities'], cc_directories=ready['directories'])
    if ready['identities'] == 'CCPANEL_NOT_PROVISIONED' or ready['directories'] == 'NOT_PROVISIONED':
        report['cc_installation'] = 'NOT_PROVISIONED'
    if ready['identities'] in {'CCPANEL_DISABLED', 'CCPANEL_SID_MISMATCH', 'CCPANEL_PRIVILEGED'}:
        report['cc_installation'] = 'BLOCKED'
    # An enabled panel account never establishes ACL acceptance or source authority.
    if ready['observer_standard'] is not True:
        report.update(outcome='BLOCKED', reason='STANDARD_TOKEN_NOT_VERIFIED')
        return report
    report['own_identity'] = 'STANDARD_IDENTITY_MATCHED'
    # First bracket has NO process query. Wrong Task identity cannot enable PID read.
    query = dict(task_name=TASK, task_xml_sha256=policy['task_xml_sha256'],
                 task_principal_sid=policy['task_principal_sid'], process_enabled=False)
    before = facts(query)['task']
    states = {'TASK_DISABLED', 'TASK_READY', 'TASK_RUNNING'}
    matched = lambda row: (row.get('state') in states and row.get('reason') == 'OK'
                            and row.get('value') == policy['task_xml_sha256'])
    if not matched(before):
        report.update(outcome='BLOCKED', reason='TASK_NOT_VERIFIED',
                      task_access='ACCESS_DENIED' if before.get('reason') == 'ACCESS_DENIED' else 'UNKNOWN')
        return report
    # Even this second call queries exactly the same Task. No name scan/rebinding.
    if policy['process_binding'] is not None:
        query.update(policy['process_binding'], process_enabled=True)
        middle = facts(query)
        proc = middle['process']
        report['process_access'] = 'ACCESS_DENIED' if proc.get('reason') == 'ACCESS_DENIED' else 'UNKNOWN'
        if (matched(middle['task']) and proc.get('state') == 'PROCESS_OBSERVED'
                and proc.get('reason') == 'OK' and proc.get('value') == policy['process_binding']['process_command_sha256']):
            report.update(process='PROCESS_IDENTITY_MATCHED', process_access='READ_OBSERVED')
        # Missing/restarted PID, wrong epoch, unreadable identity remain PROCESS_UNKNOWN.
        query['process_enabled'] = False
    else:
        middle = {'task': before}
    after = facts(query)['task']
    report['task_access'] = 'ACCESS_DENIED' if after.get('reason') == 'ACCESS_DENIED' else 'READ_OBSERVED'
    if not matched(after) or not matched(middle['task']):
        report.update(outcome='BLOCKED', reason='TASK_IDENTITY_NOT_STABLE', process='PROCESS_UNKNOWN')
        return report
    report['task_identity'] = 'TASK_IDENTITY_MATCHED'
    if after['state'] != before['state'] or middle['task']['state'] != before['state']:
        report.update(outcome='BLOCKED', task_before_after='UNKNOWN', reason='TASK_STATE_CHANGED')
        return report
    report.update(task_before_after='UNCHANGED_OBSERVED',
                  task_state='TASK_RUNNING_OBSERVED' if before['state'] == 'TASK_RUNNING' else before['state'],
                  outcome='PASS', reason='OS_BRACKET_ONLY_NO_TRADING_AUTHORITY')
    return report


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--execute', action='store_true', help='permission A required; never run as administrator')
    args = parser.parse_args(argv)
    if not args.execute:
        print(json.dumps(PREVIEW, ensure_ascii=True, sort_keys=True))
        return 0
    try:
        if os.name != 'nt':
            raise ValueError('WINDOWS_REQUIRED')
        # Only this fixed CC-private configuration is opened, using protected owner/ACL checks.
        policy = json.loads(read_windows(str(POLICY_ROOT), 'preflight-policy.json', 16384, admin_policy=True),
                            object_pairs_hook=_pairs, parse_constant=_reject_constant)
        report = execute(policy)
    except Exception:
        report = empty_report('PREFLIGHT_APPROVAL_OR_OBSERVATION_UNAVAILABLE')
    print(json.dumps(report, ensure_ascii=True, sort_keys=True))
    return 0 if report['outcome'] == 'PASS' else 1


if __name__ == '__main__':
    raise SystemExit(main())
