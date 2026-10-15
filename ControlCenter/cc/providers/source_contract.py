"""CC-03 deliberately partial, sanitized envelope. No financial/execution claims."""
from .h1_contract import obj, enum, nullable, array, TIME, COUNT, HASH, SPEC, ACTIVE, ACCEPTED_COMMIT

SCHEMA_ID = 'cc03.h1.readonly-observations.v1'
STATUS = enum('AVAILABLE', 'UNAVAILABLE', 'NEEDS_SOURCE_APPROVAL', 'INVALID')


def observation(source, value):
    return obj(source=enum(source), status=STATUS, observed_at=nullable(TIME), value=nullable(value))


SCHEMA = obj(
    schema_id=enum(SCHEMA_ID), payload_sha256=HASH, generated_at=TIME,
    identity=obj(robot_id=enum('H1'), strategy_id=enum('T3/H1/TRAIL1'),
                 production_specification_id=enum(SPEC), active_identity=enum(ACTIVE),
                 installed_code_commit=enum(ACCEPTED_COMMIT),
                 source_id=dict(type='string', pattern=r'CC03-H1-[A-Z0-9]{8,32}', maxLength=40),
                 account_alias=dict(type='string', pattern=r'H1-[A-Z0-9]{4,24}', maxLength=27),
                 binding_id=HASH, account_binding=enum('UNVERIFIED', 'MATCHED_LOCAL_POLICY')),
    heartbeat=observation('H1_PRODUCTION_HEARTBEAT', obj(
        state=enum('HEALTHY', 'UNHEALTHY'), last_api_contact_at=TIME)),
    kill_switch=observation('H1_KILL_SWITCH_FILE', obj(state=enum('HALTED', 'ARMED'), updated_at=TIME)),
    reconciliation=observation('H1_PRODUCTION_HEARTBEAT', obj(
        state=enum('PASS', 'FAULT'), unresolved_intents=COUNT)),
    task=observation('WINDOWS_TASK_PROBE', enum('Disabled', 'Ready', 'Running')),
    candles=observation('APPROVED_H1_CALENDAR', enum('UNKNOWN')),
    finances=observation('APPROVED_ACCOUNT_FINANCE', enum('UNKNOWN')),
    execution=observation('APPROVED_EXECUTION_EVENTS', enum('UNKNOWN')),
)
GROUPS = ('heartbeat', 'kill_switch', 'reconciliation', 'task', 'candles', 'finances', 'execution')
