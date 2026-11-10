"""CC-05: strictly historical FINAM READONLY evidence from CC-owned NTFS, manual only.

This is not a live broker connection or authority to enable trading.
"""
from datetime import datetime, timedelta, timezone
import json
import re
from .deployment_paths import data_root
from .providers.windows_file import read_windows
from .v20_contract import ROBOTS, _pairs, _bad_constant

ROOT = data_root() / "v20-finam"
NAME = "finam-funded-readonly.json"
SCHEMA = "cc.v20.finam-historical.v1"
EXPECTED = {"schema_id", "source_observed_at_utc", "exported_at_utc",
            "source_sha256", "overall", "accounts"}
ROW_FIELDS = {"robot", "readonly_result", "money_status", "positions_nonzero",
              "active_orders"}
ALIASES = {"v20-shallow": "V20_SHALLOW", "v20-obv": "V20_OBV",
           "v20-inside": "V20_INSIDE"}


def _clock(value):
    if type(value) is not str or not 0 < len(value) <= 48:
        raise ValueError("CC05_TIME_INVALID")
    try:
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError:
        raise ValueError("CC05_TIME_INVALID") from None
    if parsed.tzinfo is None:
        raise ValueError("CC05_TIME_INVALID")
    return parsed.astimezone(timezone.utc)


def parse(raw, now):
    if (type(raw) is not bytes or not 0 < len(raw) <= 4096
            or now.tzinfo is None):
        raise ValueError("CC05_INPUT_INVALID")
    value = json.loads(raw.decode("utf-8"), object_pairs_hook=_pairs,
                       parse_constant=_bad_constant)
    if (type(value) is not dict or set(value) != EXPECTED
            or value["schema_id"] != SCHEMA
            or value["overall"] != "PASS_READONLY_3_OF_3"
            or type(value["source_sha256"]) is not str
            or not re.fullmatch("[a-f0-9]{64}", value["source_sha256"])):
        raise ValueError("CC05_REPORT_INVALID")
    observed = _clock(value["source_observed_at_utc"])
    exported = _clock(value["exported_at_utc"])
    if (observed > exported + timedelta(seconds=30)
            or exported > now.astimezone(timezone.utc) + timedelta(seconds=30)):
        raise ValueError("CC05_FUTURE_REPORT")
    rows = value["accounts"]
    if type(rows) is not list or len(rows) != 3:
        raise ValueError("CC05_ACCOUNTS_INVALID")
    accounts = {}
    for row in rows:
        if (type(row) is not dict or set(row) != ROW_FIELDS
                or type(row["robot"]) is not str or row["robot"] not in ALIASES
                or row["robot"] in accounts or row["readonly_result"] != "PASS_READONLY"
                or row["money_status"] != "PASS"
                or type(row["positions_nonzero"]) is not int or row["positions_nonzero"] != 0
                or type(row["active_orders"]) is not int or row["active_orders"] != 0):
            raise ValueError("CC05_ACCOUNT_MISMATCH")
        accounts[row["robot"]] = {
            "robot": ALIASES[row["robot"]], "readonly": "PASS_READONLY",
            "money": "PASS", "positions": 0, "orders": 0}
    if set(accounts) != set(ALIASES) or {a["robot"] for a in accounts.values()} != set(ROBOTS):
        raise ValueError("CC05_IDENTITIES_INVALID")
    return {"kind": "HISTORICAL_ONLY", "observed_at": observed,
            "exported_at": exported, "accounts": accounts}


def acquire(now):
    """Exactly one CC-owned secure local read. Fail closed, no FINAM or V20 access."""
    try:
        return parse(read_windows(str(ROOT), NAME, 4096, admin_policy=True), now)
    except Exception:
        return None
