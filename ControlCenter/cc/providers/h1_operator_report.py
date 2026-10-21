"""Strict parser of the already-existing H1 operator's local read-only check.

Never opens H1 files or calls PowerShell. These are LOCAL operator-reported
observations, NOT independent FINAM / fill / stop coverage assertions.
"""
from datetime import datetime, timezone
import re

KEY = re.compile(r"^([A-Za-z][A-Za-z0-9_]*)=([^\r\n]{0,180})$")
CYCLE = re.compile(r"^status=(PASS|FAULT) cycle=(\d{1,20}|NOT_LOGGED) code=([A-Z0-9_]{1,80})$")
REQUIRED_PASS = (
    "PRODUCTION_TASK_ENABLED_RUNNING",
    "TASK_ACTION_EXACT_RELEASE",
    "HEARTBEAT_EXACT_FROZEN_IDENTITY",
    "HEARTBEAT_AUTHORIZATION_ACCOUNT_MATCH",
    "HEARTBEAT_HEALTHY_RECONCILIATION_PASS",
    "KILL_SWITCH_ARMED_EXACT_GENERATION_62",
    "HEARTBEAT_POSITION_STOP_COVERAGE_INTERNAL_CONSISTENCY",
    "LAST_10_PRODUCTION_CYCLE_ATTEMPTS_PRESENT",
    "LATEST_PRODUCTION_CYCLE_ATTEMPT_PASS",
)
EXPECTED_COMMIT = "3a18c8c24301c866a60f5d725de227288d48f7ec"
FIELDS = frozenset((
    "expected_production_commit", "production_task", "cycle_count", "health_status",
    "reconciliation_status", "reported_open_positions", "reported_active_stops",
    "reported_unresolved_intents", "heartbeat_utc", "last_finam_api_contact_utc",
    "kill_switch_state", "kill_switch_generation", "last_cycle_attempts_found",
    "TRADINGSYSTEMLAB_LIVE_LOCAL_READONLY_CHECK", "NO_CHANGES_MADE_BY_THIS_SCRIPT",
    *REQUIRED_PASS, *(f"cycle_{i:02}" for i in range(1, 11)),
))


def _timestamp(value):
    try:
        result = datetime.fromisoformat(value.replace("Z", "+00:00"))
        if result.tzinfo is None:
            raise ValueError("CLOCK_WITHOUT_TIMEZONE")
        return result.astimezone(timezone.utc)
    except (TypeError, ValueError) as exc:
        raise ValueError("OPERATOR_REPORT_CLOCK_INVALID") from exc


def parse_operator_report(raw, now):
    """Parse a CC-published operator report; fail closed on unverified checks."""
    if type(raw) is not str or not 0 < len(raw.encode("utf-8")) <= 65536:
        raise ValueError("OPERATOR_REPORT_SIZE_INVALID")
    if now.tzinfo is None:
        raise ValueError("OPERATOR_REPORT_NOW_INVALID")
    found = {}
    for line in raw.splitlines():
        if len(line) > 500:
            raise ValueError("OPERATOR_REPORT_LINE_OVERSIZE")
        m = KEY.fullmatch(line)
        if m and m[1] in FIELDS:
            if m[1] in found:
                raise ValueError("OPERATOR_REPORT_DUPLICATE")
            found[m[1]] = m[2]
    if (found.get("TRADINGSYSTEMLAB_LIVE_LOCAL_READONLY_CHECK") != "PASS"
            or found.get("NO_CHANGES_MADE_BY_THIS_SCRIPT") != "YES"
            or found.get("expected_production_commit") != EXPECTED_COMMIT
            or found.get("production_task") != "Running"
            or found.get("kill_switch_state") != "ARMED"
            or any(found.get(k) != "PASS" for k in REQUIRED_PASS)):
        raise ValueError("OPERATOR_REPORT_FAILED_OR_UNVERIFIED")
    numbers = {}
    for k in ("cycle_count", "reported_open_positions", "reported_active_stops",
              "reported_unresolved_intents", "last_cycle_attempts_found"):
        s = found.get(k, "")
        if not re.fullmatch(r"\d{1,20}", s) or int(s) > 10**12:
            raise ValueError("OPERATOR_REPORT_NUMBER_INVALID")
        numbers[k] = int(s)
    if (numbers["last_cycle_attempts_found"] != 10
            or numbers["reported_unresolved_intents"] != 0
            or found.get("health_status") != "HEALTHY"
            or found.get("reconciliation_status") != "PASS"):
        raise ValueError("OPERATOR_REPORT_INCONSISTENT")
    cycles = []
    for index in range(1, 11):
        match = CYCLE.fullmatch(found.get(f"cycle_{index:02}", ""))
        if not match:
            raise ValueError("OPERATOR_REPORT_CYCLE_INVALID")
        cycles.append({"Попытка": index, "Результат": match[1],
                       "Цикл": match[2], "Причина": match[3]})
    if cycles[-1]["Результат"] != "PASS":
        raise ValueError("OPERATOR_REPORT_LAST_CYCLE_FAILED")
    observed = _timestamp(found.get("heartbeat_utc"))
    contact = _timestamp(found.get("last_finam_api_contact_utc"))
    now_utc = now.astimezone(timezone.utc)
    age = (now_utc - observed).total_seconds()
    if age < -60 or contact > now_utc.replace(microsecond=999999):
        raise ValueError("OPERATOR_REPORT_FUTURE")
    return {"received_at": now_utc, "observed_at": observed, "contact_at": contact,
            "age_seconds": age, "status": "CURRENT" if 0 <= age <= 900 else "STALE",
            "cycle_count": numbers["cycle_count"], "positions": numbers["reported_open_positions"],
            "stops": numbers["reported_active_stops"],
            "unresolved": numbers["reported_unresolved_intents"],
            "health": found["health_status"], "reconciliation": found["reconciliation_status"],
            "task": found["production_task"], "kill_switch": found["kill_switch_state"],
            "generation": found.get("kill_switch_generation", "UNKNOWN"), "cycles": cycles}


def age_operator_report(report, now):
    if report is None:
        return None
    if report["status"] != "CURRENT":
        return report
    if (now.astimezone(timezone.utc) < report["received_at"]
            or (now.astimezone(timezone.utc) - report["observed_at"]).total_seconds() > 900):
        return dict(report, status="STALE")
    return report

def manual_published_report(now):
    """Read the separately published operator report from pinned admin-owned CC root.

    Never invoke the H1 script, FINAM, DPAPI, scheduler or production filesystem.
    Same previously accepted trusted directory as FINAM one-shot, different
    fixed filename that cannot be selected as a broker h1-<digest>.json.
    """
    import json
    from .h1_broker_snapshot import ROOT, POLICY_ROOT, POLICY, _policy
    from .h1_readonly import _pairs, _reject_constant
    from .windows_file import read_windows
    policy_bytes = read_windows(str(POLICY_ROOT), POLICY, 4096, admin_policy=True)
    policy = _policy(json.loads(policy_bytes.decode("utf-8"),
                                object_pairs_hook=_pairs, parse_constant=_reject_constant))
    raw = read_windows(str(ROOT), "h1-local-report.txt", 65536,
                       expected_root=policy["export_root_id"], admin_policy=True)
    return parse_operator_report(raw.decode("utf-8-sig"), now)
