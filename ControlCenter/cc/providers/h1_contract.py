"""CC-02 receiving contract. No trading imports; all names/strings are allowlisted.

SCHEMA is also published as docs/H1_READONLY_SNAPSHOT_SCHEMA.json. This small
validator implements only the keywords used here; changes require contract tests.
"""
from datetime import datetime, timezone
from math import isfinite
import re

SCHEMA_ID = "controlcenter.h1.readonly.v1"
SPEC = "PROD_STAGE7_46DB784378797C7FB04636892350AFF21006D71A31F2CED9D4B974EDA2DC36B8"
ACTIVE = "TRAIL1__N4_01__FULL__R15"
ACCEPTED_COMMIT = "3a18c8c24301c866a60f5d725de227288d48f7ec"
# Public test binding, deliberately unrelated to any real broker account.
FIXTURE_BINDING = "f" * 64
N4 = ("USDRUBF", "CNYRUBF", "GLDRUBF", "IMOEXF")
MAX_BYTES = 131072
SNAPSHOT_TTL = 180
HEARTBEAT_TTL = 90
RECONCILIATION_TTL = 90
FINANCIAL_TTL = 300
MAX_SKEW = 0  # receiving timestamps must never be in the future


def obj(**properties):
    return dict(type="object", properties=properties, required=list(properties), additionalProperties=False)


def enum(*values):
    return dict(enum=list(values))


def nullable(schema):
    return {"anyOf": [schema, {"type": "null"}]}


def array(items, limit):
    return dict(type="array", items=items, maxItems=limit)


TIME = dict(type="string", format="date-time", maxLength=32)
HASH = dict(type="string", pattern="[a-f0-9]{64}", maxLength=64)
SYMBOL = enum(*N4)
COUNT = dict(type="integer", minimum=0, maximum=1000000)
NUMBER = dict(type="number", minimum=-1e12, maximum=1e12)
PRICE = dict(type="number", minimum=0.00000001, maximum=1e12)
SIDE = enum("LONG", "SHORT")
EVIDENCE = obj(kind=enum("FIXTURE_TRADE_HISTORY", "FIXTURE_BROKER_SLTP", "FIXTURE_ACCOUNT"),
               reference=HASH, observed_at=TIME, complete=enum(True))
OHLC = obj(open=PRICE, high=PRICE, low=PRICE, close=PRICE)
BAR = obj(instrument=SYMBOL, observed_at=TIME, open_at=nullable(TIME), close_at=nullable(TIME),
          time_label=enum("CLOSE"), time_source=enum("RUNTIME_HISTORY_OPEN_PLUS_1H", "UNKNOWN"),
          completed=dict(type="boolean"), gaps=nullable(dict(type="boolean")),
          quality=enum("CONFIRMED", "GAP", "UNKNOWN"), calendar=enum("UNAPPROVED"), ohlc=nullable(OHLC))
SIGNAL = obj(instrument=SYMBOL, bar_close_at=TIME, emitted=enum(True),
             direction=enum("LONG", "SHORT", "NO_SIGNAL"),
             rejection_reason=nullable(enum("HALTED", "RISK_REJECTED", "SESSION_CLOSED", "CONDITION_FALSE")),
             risk_result=enum("PASS", "FAIL", "UNKNOWN"))
ORDER = obj(instrument=SYMBOL, occurred_at=TIME, reference=HASH,
            state=enum("INTENT", "REQUESTED", "ACK", "POSITION_OBSERVED", "FILL_CONFIRMED", "UNRESOLVED"),
            quantity=nullable(COUNT), filled_quantity=nullable(COUNT), fill_price=nullable(PRICE),
            evidence=nullable(EVIDENCE))
POSITION = obj(instrument=SYMBOL, side=SIDE, quantity=COUNT, entry_price=nullable(PRICE),
               price_evidence=nullable(EVIDENCE))
STOP = obj(instrument=SYMBOL, side=SIDE, quantity=COUNT, expected_quantity=COUNT,
           observed_quantity=nullable(COUNT), broker_status=enum("ACTIVE", "INACTIVE", "UNKNOWN"),
           checked_at=nullable(TIME), planned_price=nullable(PRICE), evidence=nullable(EVIDENCE))
SCHEMA = obj(
    schema_id=enum(SCHEMA_ID), source_kind=enum("OFFLINE_FIXTURE"), complete=enum(True),
    payload_sha256=HASH, generated_at=TIME, observed_at=TIME,
    identity=obj(robot_id=enum("H1"), strategy_id=enum("T3/H1/TRAIL1"),
                 active_identity=enum(ACTIVE), production_specification_id=enum(SPEC),
                 accepted_code_commit=enum(ACCEPTED_COMMIT), account_alias=enum("FIXTURE-H1"),
                 account_scope=enum("FIXTURE-H1"), account_binding=enum(FIXTURE_BINDING)),
    runtime=obj(observed_at=TIME, state=enum("HALTED", "HEALTHY", "UNHEALTHY", "UNKNOWN"),
                trading_permission=nullable(enum(False)), heartbeat_at=nullable(TIME),
                last_successful_cycle_at=nullable(TIME), source_status=enum("AVAILABLE", "UNAVAILABLE", "UNKNOWN")),
    reconciliation=obj(observed_at=nullable(TIME), last_success_at=nullable(TIME),
                       status=enum("PASS", "FAULT", "UNKNOWN"), unresolved_intents=nullable(COUNT)),
    bars=array(BAR, 4),
    signals=obj(observed_at=nullable(TIME), complete=dict(type="boolean"), items=array(SIGNAL, 32)),
    orders=obj(observed_at=nullable(TIME), complete=dict(type="boolean"), items=array(ORDER, 64)),
    positions=obj(observed_at=nullable(TIME), complete=dict(type="boolean"), items=array(POSITION, 4)),
    stops=obj(observed_at=nullable(TIME), complete=dict(type="boolean"), items=array(STOP, 4)),
    finances=obj(observed_at=nullable(TIME), complete=dict(type="boolean"), evidence=nullable(EVIDENCE),
                 equity=nullable(NUMBER), realized_pnl=nullable(NUMBER), unrealized_pnl=nullable(NUMBER),
                 commissions=nullable(NUMBER), deposits=nullable(NUMBER), withdrawals=nullable(NUMBER),
                 available_margin=nullable(NUMBER), used_risk_pct=nullable(dict(type="number", minimum=0, maximum=100)),
                 contracts=nullable(COUNT)),
)
SCHEMA["$schema"] = "https://json-schema.org/draft/2020-12/schema"
SCHEMA["title"] = SCHEMA_ID


def timestamp(value):
    """Wire contract is strict UTC RFC3339; no naive, implicit zone or offset conversion."""
    if value is None:
        return None
    if type(value) is not str or not re.fullmatch(r"\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}(?:\.\d{1,6})?(?:Z|\+00:00)", value):
        raise ValueError("TIME_INVALID")
    result = datetime.fromisoformat(value.replace("Z", "+00:00"))
    if result.utcoffset() != timezone.utc.utcoffset(result):
        raise ValueError("TIME_INVALID")
    return result


def validate(value, schema=SCHEMA):
    if "anyOf" in schema:
        for option in schema["anyOf"]:
            try:
                validate(value, option)
                return
            except ValueError:
                pass
        raise ValueError("TYPE_INVALID")
    if "enum" in schema and not any(type(value) is type(v) and value == v for v in schema["enum"]):
        raise ValueError("ENUM_INVALID")
    kind = schema.get("type")
    types = {"object": dict, "array": list, "string": str, "integer": int, "boolean": bool, "null": type(None)}
    if kind == "number":
        if type(value) not in (int, float) or not isfinite(value):
            raise ValueError("NUMBER_INVALID")
    elif kind is not None and type(value) is not types[kind]:
        raise ValueError("TYPE_INVALID")
    if kind == "object":
        if set(value) != set(schema["properties"]):
            raise ValueError("FIELDS_INVALID")
        for key, child in schema["properties"].items():
            validate(value[key], child)
    elif kind == "array":
        if len(value) > schema["maxItems"]:
            raise ValueError("ARRAY_TOO_LARGE")
        for child in value:
            validate(child, schema["items"])
    elif kind == "string":
        if len(value) > schema.get("maxLength", 128):
            raise ValueError("STRING_TOO_LARGE")
        if "pattern" in schema and not re.fullmatch(schema["pattern"], value):
            raise ValueError("STRING_INVALID")
        if schema.get("format") == "date-time":
            timestamp(value)
    elif kind in ("integer", "number"):
        if not schema["minimum"] <= value <= schema["maximum"]:
            raise ValueError("NUMBER_RANGE_INVALID")
