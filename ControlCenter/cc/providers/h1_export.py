"""Receiver for the external partial CC-03 export. No broker/financial authority."""
from dataclasses import dataclass
from datetime import datetime
import json
from pathlib import Path
from threading import Lock
from ..models import (DataProvenance, FieldObservation, InstrumentStatus, PortfolioSnapshot,
                      RiskSnapshot, RobotId, RobotSnapshot, RobotStatus, SourceKind, State, SystemAlert, WindowsObservation)
from .h1_contract import ACTIVE, SPEC, ACCEPTED_COMMIT, MAX_BYTES, timestamp, validate
from .h1_readonly import canonical_digest, _pairs, _reject_constant
from .source_contract import SCHEMA, GROUPS
from .os_contract import SCHEMA as OS_SCHEMA, SCHEMA_ID as OS_SCHEMA_ID, GROUPS as OS_GROUPS, check_semantics
from .windows_file import read_windows, read_latest_windows
from ..deployment_paths import data_root

EXPORT_ROOT = data_root() / 'export'
POLICY_ROOT = Path(__file__).absolute().parents[2] / 'deployment'
SAFE_ERROR = 'CC03_SOURCE_UNKNOWN_OR_UNAVAILABLE'
# One Streamlit server process, shared by all UI sessions. Not an interprocess lock.
# No polling, retries, background threads, or H1/FINAM access here.
_MANUAL_EXPORT_GATE = Lock()

def unchecked_export_snapshot(now: datetime):
    """Unobserved H1: render UNKNOWN without opening any file or invoking a provider."""
    p = DataProvenance(RobotId.H1, 'UNBOUND-H1', 'READONLY_EXPORT/H1', None, now,
                       synthetic=False, source_kind=SourceKind.READONLY_EXPORT)
    return RobotSnapshot(
        RobotStatus(p, State.UNKNOWN, 'TradingSystemLab', 'T3/H1/TRAIL1', ACTIVE,
                    None, None, None, False, None, None, None),
        tuple(InstrumentStatus(p, name, State.UNKNOWN, None, 'NOT_CHECKED', None, None)
              for name in ('USDRUBF', 'CNYRUBF', 'GLDRUBF', 'IMOEXF')),
        (), (), (), None, RiskSnapshot(p, None, None, None, None, 'NOT_CHECKED'),
        PortfolioSnapshot(p, None, None, None, None, None, None), None,
        (SystemAlert(p, None, now, 'SOURCE', 'WARNING', 'MANUAL_REFRESH_REQUIRED'),),
    )



def manual_export_refresh(now: datetime):
    """At most one local CC-export read across all sessions in this panel process.

    Concurrent clicks fail closed and never invoke the provider. A different panel
    process is outside this gate; physical CC-03 acceptance must prove a single
    loopback Streamlit listener before extending this path to an H1 diagnostic.
    """
    if not _MANUAL_EXPORT_GATE.acquire(blocking=False):
        return unchecked_export_snapshot(now), False
    try:
        return H1ExportProvider().snapshot(RobotId.H1, 'READONLY_EXPORT', now), True
    except Exception:
        return unchecked_export_snapshot(now), False
    finally:
        _MANUAL_EXPORT_GATE.release()


@dataclass(frozen=True)
class ReceiverPolicy:
    # Trusted, administrator-owned application policy; never taken from an export.
    export_root_id: tuple[int, int, int] | None = None
    source_id: str | None = None
    account_alias: str | None = None
    binding_id: str | None = None
    snapshot: int | None = None
    heartbeat: int | None = None
    task: int | None = None
    kill_switch: int | None = None
    reconciliation: int | None = None
    candles: int | None = None
    finances: int | None = None
    os_observations: int | None = None

    def __post_init__(self):
        for key in ('snapshot','heartbeat','task','kill_switch','reconciliation','candles','finances','os_observations'):
            value = getattr(self, key)
            if value is not None and (type(value) is not int or not 1 <= value <= 86400):
                raise ValueError('APPROVED_TTL_REQUIRED')


def installed_policy():
    try:
        value = json.loads(read_windows(str(POLICY_ROOT), 'receiver-policy.json', MAX_BYTES, admin_policy=True).decode('utf-8'),
                           object_pairs_hook=_pairs, parse_constant=_reject_constant)
        if set(value) != {'schema_id','physical_source_approved','policy'} or value['schema_id'] != 'cc03.receiver-policy.v1':
            raise ValueError('POLICY_INVALID')
        if value['physical_source_approved'] is not True:
            return ReceiverPolicy()
        return ReceiverPolicy(**value['policy'])
    except Exception:
        return ReceiverPolicy()


def quality(at, now, ttl):
    if at is None or ttl is None or (now-at).total_seconds() < 0:
        return State.UNKNOWN
    return State.STALE if (now-at).total_seconds() > ttl else State.HEALTHY


class H1ExportProvider:
    def __init__(self, policy=None):
        self.policy = installed_policy() if policy is None else policy

    def snapshot(self, robot_id, scenario, now: datetime):
        policy = self.policy
        p = DataProvenance(RobotId.H1, 'UNBOUND-H1', 'READONLY_EXPORT/H1', None, now,
                           synthetic=False, source_kind=SourceKind.READONLY_EXPORT,
                           snapshot_ttl_seconds=policy.snapshot, heartbeat_ttl_seconds=policy.heartbeat)
        observations, state, heartbeat, task, identity = (), State.UNKNOWN, None, None, None
        try:
            if robot_id != RobotId.H1:
                raise ValueError('H1_ONLY')
            raw = read_latest_windows(EXPORT_ROOT, MAX_BYTES, policy.export_root_id)
            value = json.loads(raw.decode('utf-8'), object_pairs_hook=_pairs, parse_constant=_reject_constant)
            if value.get('schema_id') == OS_SCHEMA_ID:
                return os_snapshot(value, policy, now)
            validate(value, SCHEMA)
            if canonical_digest(value) != value['payload_sha256']:
                raise ValueError('INTEGRITY_INVALID')
            generated = timestamp(value['generated_at'])
            if generated > now:
                raise ValueError('FUTURE_EXPORT')
            bound = (value['identity']['source_id'] == policy.source_id
                     and value['identity']['account_alias'] == policy.account_alias
                     and value['identity']['binding_id'] == policy.binding_id
                     and value['identity']['account_binding'] == 'MATCHED_LOCAL_POLICY')
            # A mismatched or unapproved producer cannot assert current HALTED either.
            if not bound:
                raise ValueError('SOURCE_BINDING_UNAPPROVED')
            p = DataProvenance(RobotId.H1, policy.account_alias, 'READONLY_EXPORT/H1', generated, now,
                               synthetic=False, source_kind=SourceKind.READONLY_EXPORT,
                               snapshot_ttl_seconds=policy.snapshot, heartbeat_ttl_seconds=policy.heartbeat)
            snapshot_quality = quality(generated, now, policy.snapshot)
            observed, qs = [], {}
            for name in GROUPS:
                group = value[name]
                at = timestamp(group['observed_at'])
                if ((group['status'] == 'AVAILABLE') != (at is not None and group['value'] is not None)
                        or at is not None and at > generated):
                    raise ValueError('OBSERVATION_INVALID')
                q = quality(at, now, getattr(policy, name, None)) if group['status'] == 'AVAILABLE' else State.UNKNOWN
                if snapshot_quality != State.HEALTHY:
                    q = snapshot_quality
                qs[name] = q
                observed.append(FieldObservation(name + '/' + group['status'], at, q))
            observations = tuple(observed)
            state = snapshot_quality if snapshot_quality != State.HEALTHY else State.UNKNOWN
            kill = value['kill_switch']
            if kill['value'] is not None and timestamp(kill['value']['updated_at']) > timestamp(kill['observed_at']):
                raise ValueError('KILL_TIME_INVALID')
            hb = value['heartbeat']
            if hb['value'] is not None:
                heartbeat = timestamp(hb['observed_at'])
                if timestamp(hb['value']['last_api_contact_at']) > heartbeat:
                    raise ValueError('CONTACT_TIME_INVALID')
            if snapshot_quality == State.HEALTHY:
                if qs['kill_switch'] == State.HEALTHY and kill['value']['state'] == 'HALTED':
                    state = State.HALTED
                elif qs['heartbeat'] == State.STALE or qs['kill_switch'] == State.STALE:
                    state = State.STALE
                elif qs['heartbeat'] == State.HEALTHY and hb['value']['state'] == 'UNHEALTHY':
                    state = State.UNHEALTHY
                rec = value['reconciliation']
                if qs['reconciliation'] == State.HEALTHY and rec['value']['unresolved_intents'] > 0:
                    state = State.UNRESOLVED
                # Current exporter deliberately has no approved Task/process source:
                # HEALTHY is unreachable without all independent fresh observations.
                elif all(qs[n] == State.HEALTHY for n in ('heartbeat','kill_switch','task','reconciliation')):
                    contact_quality = quality(timestamp(hb['value']['last_api_contact_at']), now, policy.heartbeat)
                    if (kill['value']['state'] == 'ARMED' and value['task']['value'] == 'Running'
                            and hb['value']['state'] == 'HEALTHY' and rec['value']['state'] == 'PASS'
                            and contact_quality == State.HEALTHY):
                        state = State.HEALTHY
                if qs['task'] == State.HEALTHY:
                    task = value['task']['value']
            identity = f'{SPEC} · installed code {ACCEPTED_COMMIT} · {policy.source_id} · local binding matched; broker authority UNKNOWN'
        except Exception:
            # Clear every partially converted value; no last-good state and no path/error leakage.
            p = DataProvenance(RobotId.H1, 'UNBOUND-H1', 'READONLY_EXPORT/H1', None, now,
                               synthetic=False, source_kind=SourceKind.READONLY_EXPORT,
                               snapshot_ttl_seconds=policy.snapshot, heartbeat_ttl_seconds=policy.heartbeat)
            observations, state, heartbeat, task, identity = (), State.UNKNOWN, None, None, None
        return RobotSnapshot(
            RobotStatus(p, state, 'TradingSystemLab', 'T3/H1/TRAIL1', ACTIVE, heartbeat,
                        None, None, False, None, task, None),
            tuple(InstrumentStatus(p, name, State.UNKNOWN, None, 'NEEDS_SOURCE_APPROVAL', None, None)
                  for name in ('USDRUBF','CNYRUBF','GLDRUBF','IMOEXF')),
            (), (), (), None, RiskSnapshot(p, None, None, None, None, 'ACCOUNT_AUTHORITY_UNKNOWN'),
            PortfolioSnapshot(p, None, None, None, None, None, None), None,
            (SystemAlert(p, None, now, 'SOURCE', 'WARNING', SAFE_ERROR if identity is None else 'CC03_PARTIAL_READONLY_NO_BROKER_AUTHORITY'),),
            readonly_observations=observations, readonly_identity=identity)


def os_snapshot(value, policy, now):
    validate(value, OS_SCHEMA)
    check_semantics(value, timestamp)
    generated = timestamp(value['generated_at'])
    identity = value['identity']
    if (canonical_digest(value) != value['payload_sha256'] or generated > now or
            identity['source_id'] != policy.source_id or identity['account_alias'] != policy.account_alias or
            identity['binding_id'] != policy.binding_id):
        raise ValueError('OS_SOURCE_UNAPPROVED')
    p = DataProvenance(RobotId.H1, policy.account_alias, 'READONLY_EXPORT/H1', generated, now,
                       synthetic=False, source_kind=SourceKind.READONLY_EXPORT,
                       snapshot_ttl_seconds=policy.snapshot, heartbeat_ttl_seconds=None)
    rows = []
    for name in OS_GROUPS:
        row = value[name]
        at = timestamp(row['observed_at'])
        q = quality(at, now, policy.os_observations)
        outer = quality(generated, now, policy.snapshot)
        if outer != State.HEALTHY:
            q = outer
        current = q == State.HEALTHY and row['state'] != 'UNKNOWN'
        rows.append(WindowsObservation(name, row['source'], row['state'] if current else 'UNKNOWN', at,
                    'CURRENT' if q == State.HEALTHY else q.value,
                    'WINDOWS_OS_ONLY' if current else 'UNKNOWN', row['reason'],
                    json.dumps(row['value'], sort_keys=True) if current and row['value'] is not None else None))
    task = next(r.state for r in rows if r.name == 'task')
    return RobotSnapshot(
        RobotStatus(p, State.UNKNOWN, 'TradingSystemLab', 'T3/H1/TRAIL1', ACTIVE,
                    None, None, None, None, None, None if task == 'UNKNOWN' else task, None),
        tuple(InstrumentStatus(p, name, State.UNKNOWN, None, 'SOURCE_BLOCKED', None, None)
              for name in ('USDRUBF', 'CNYRUBF', 'GLDRUBF', 'IMOEXF')),
        (), (), (), None, RiskSnapshot(p, None, None, None, None, 'ACCOUNT_AUTHORITY_UNKNOWN'),
        PortfolioSnapshot(p, None, None, None, None, None, None), None,
        (SystemAlert(p, None, now, 'SOURCE', 'WARNING', 'WINDOWS_OS_ONLY_NO_ROBOT_OR_BROKER_AUTHORITY'),),
        readonly_identity=identity['source_id'] + ' · source binding matched local receiver policy · account UNVERIFIED',
        windows_observations=tuple(rows))
