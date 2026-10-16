"""OS facts only. This envelope has no robot, broker or trading authority."""
from .h1_contract import obj, enum, nullable, TIME, HASH

SCHEMA_ID = 'cc03.h1.windows-os.v1'
REASONS = ('OK', 'NOT_FOUND', 'IDENTITY_MISMATCH', 'ACCESS_DENIED', 'UNAVAILABLE',
           'TIMEOUT', 'DISABLED', 'CHANGED', 'UNAPPROVED')


def observation(source, states, value):
    return obj(source=enum(source), state=enum(*states, 'UNKNOWN'), reason=enum(*REASONS),
               observed_at=nullable(TIME), confidence=enum('OS_OBSERVED', 'UNKNOWN'),
               value=nullable(value))


SCHEMA = obj(
    schema_id=enum(SCHEMA_ID), payload_sha256=HASH, generated_at=TIME,
    identity=obj(robot_id=enum('H1'), source_id=dict(type='string', pattern=r'CC03-H1-[A-Z0-9]{8,32}', maxLength=40),
                 account_alias=dict(type='string', pattern=r'H1-[A-Z0-9]{4,24}', maxLength=27), binding_id=HASH,
                 account_binding=enum('UNVERIFIED'), authority=enum('WINDOWS_OS_ONLY')),
    task=observation('WINDOWS_TASK_READONLY', ('TASK_DISABLED', 'TASK_READY', 'TASK_RUNNING'), HASH),
    process=observation('WINDOWS_PROCESS_READONLY', ('PROCESS_OBSERVED', 'PROCESS_ABSENT'), HASH),
    # Native noninterference failed; these placeholders can never carry facts.
    heartbeat_metadata=observation('WINDOWS_FILE_METADATA', (), enum(None)),
    kill_switch_metadata=observation('WINDOWS_FILE_METADATA', (), enum(None)),
)
GROUPS = ('task', 'process', 'heartbeat_metadata', 'kill_switch_metadata')


def check_semantics(value, timestamp):
    generated = timestamp(value['generated_at'])
    for name in GROUPS:
        row = value[name]
        if name.endswith('_metadata') and (row['state'] != 'UNKNOWN' or row['reason'] != 'DISABLED'):
            raise ValueError('CC03_METADATA_COMPATIBILITY_BLOCKED')
        at = timestamp(row['observed_at'])
        known = row['state'] != 'UNKNOWN'
        if (at is None or at > generated or
                (known != (row['confidence'] == 'OS_OBSERVED')) or
                (known and row['reason'] not in ('OK', 'NOT_FOUND')) or
                (not known and (row['value'] is not None or row['reason'] == 'OK')) or
                (known and row['value'] is None and row['state'] != 'FILE_ABSENT')):
            raise ValueError('OS_OBSERVATION_INVALID')
        if name.endswith('_metadata') and row['state'] == 'FILE_PRESENT':
            if timestamp(row['value']['modified_at']) > at:
                raise ValueError('METADATA_TIME_INVALID')
