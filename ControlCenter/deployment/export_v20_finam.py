"""CC-05 operator-only one-shot sanitizer; never invoked by Streamlit.

Reads the pre-existing V20-06 funded READONLY receipt and writes ONLY a bounded
allowlisted historical result under Control Center. No broker network or tokens.
Output cannot be silently overwritten; admin-owned NTFS ACL acceptance is separate.
"""
from datetime import datetime, timedelta, timezone
from hashlib import sha256
import json
import os
from pathlib import Path
import re
import sys

SOURCE = Path(r"C:\V20Lab\readonly-06\BROKER_READONLY_REPORT_FUNDED.json")
DEST = Path(r"C:\Control Center\data\v20-finam\finam-funded-readonly.json")
ROBOTS = ("v20-shallow", "v20-obv", "v20-inside")


def _pairs(items):
    result = {}
    for key, value in items:
        if key in result:
            raise ValueError("CC05_DUPLICATE_FIELD")
        result[key] = value
    return result


def _clock(value):
    if type(value) is not str or not 0 < len(value) <= 48:
        raise ValueError("CC05_SOURCE_TIME_INVALID")
    try:
        t = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError:
        raise ValueError("CC05_SOURCE_TIME_INVALID") from None
    if t.tzinfo is None:
        raise ValueError("CC05_SOURCE_TIME_INVALID")
    return t.astimezone(timezone.utc)


def sanitize(raw, now):
    if type(raw) is not bytes or not 0 < len(raw) <= 65536 or now.tzinfo is None:
        raise ValueError("CC05_SOURCE_SIZE_INVALID")
    doc = json.loads(raw.decode("utf-8-sig"), object_pairs_hook=_pairs,
                     parse_constant=lambda x: (_ for _ in ()).throw(ValueError("CC05_NONFINITE")))
    if (type(doc) is not dict
            or doc.get("schema") != "v20.finam.broker_readonly_report.v1"
            or doc.get("status") != "PASS_READONLY_3_OF_3"
            or doc.get("stage_06_status") != "PASS"
            or doc.get("entry_authorized") is not False
            or doc.get("real_orders_sent_by_diagnostics") != 0
            or doc.get("actual_sltp_execution_verified") is not False
            or doc.get("live_equity_ledger_reconciled") is not False):
        raise ValueError("CC05_SOURCE_NOT_ACCEPTED")
    observed = _clock(doc.get("source_observed_at_utc"))
    now = now.astimezone(timezone.utc)
    if observed > now + timedelta(seconds=30):
        raise ValueError("CC05_SOURCE_FUTURE")
    rows = doc.get("accounts")
    if type(rows) is not list or len(rows) != 3:
        raise ValueError("CC05_SOURCE_ACCOUNTS")
    found, hashes = {}, set()
    for item in rows:
        if (type(item) is not dict or type(item.get("robot")) is not str
                or item["robot"] not in ROBOTS or item["robot"] in found
                or item.get("readonly_result") != "PASS_READONLY"
                or item.get("money_status") != "PASS"
                or type(item.get("positions_nonzero")) is not int or item["positions_nonzero"] != 0
                or type(item.get("active_orders")) is not int or item["active_orders"] != 0
                or type(item.get("account_sha256")) is not str
                or not re.fullmatch("[0-9a-f]{64}", item["account_sha256"])
                or item["account_sha256"] in hashes):
            raise ValueError("CC05_SOURCE_ACCOUNT_INVALID")
        hashes.add(item["account_sha256"])
        found[item["robot"]] = {
            "robot": item["robot"], "readonly_result": "PASS_READONLY",
            "money_status": "PASS", "positions_nonzero": 0, "active_orders": 0}
    if set(found) != set(ROBOTS):
        raise ValueError("CC05_SOURCE_ROBOTS_INVALID")
    return {
        "schema_id": "cc.v20.finam-historical.v1",
        "source_observed_at_utc": observed.isoformat(),
        "exported_at_utc": now.isoformat(),
        "source_sha256": sha256(raw).hexdigest(),
        "overall": "PASS_READONLY_3_OF_3",
        "accounts": [found[n] for n in ROBOTS],
    }


def publish(source=SOURCE, dest=DEST, now=None):
    if os.name != "nt":
        raise ValueError("CC05_WINDOWS_ONLY")
    if not dest.parent.is_dir() or dest.exists() or dest.is_symlink():
        raise ValueError("CC05_DESTINATION_NOT_PREPARED_OR_EXISTS")
    source_bytes = source.read_bytes()
    payload = sanitize(source_bytes, now or datetime.now(timezone.utc))
    wire = (json.dumps(payload, ensure_ascii=True, separators=(",", ":")) + "\n").encode("ascii")
    if len(wire) > 4096:
        raise ValueError("CC05_OUTPUT_OVERSIZE")
    # Operator-provisioned destination; its owner and ACL are verified by
    # the panel's existing native Windows boundary on every manual read.
    with dest.open("xb") as stream:
        stream.write(wire)
    return payload


if __name__ == "__main__":
    try:
        if len(sys.argv) != 1:
            raise ValueError("CC05_UNEXPECTED_ARGUMENTS")
        report = publish()
        print("cc05_export=pass")
        print("cc05_source=historical_v20_06")
        print("cc05_observed_at=" + report["source_observed_at_utc"])
        print("cc05_accounts=3_of_3")
        print("cc05_no_finam_no_tokens_no_task_mutation=yes")
    except Exception as error:
        print("cc05_export=fail " + (
            str(error) if str(error).startswith("CC05_") else "CC05_SOURCE_UNAVAILABLE"))
        sys.exit(1)
