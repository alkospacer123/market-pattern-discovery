"""CC-06 independent controller contract — offline preview, no execution.

Not imported by Streamlit, and intentionally has no Task/FINAM/V20 access.
CC-07 live action dispatch requires separately approved controller revision.
"""
from __future__ import annotations

import argparse
import json
import re

ROBOTS = ("v20-shallow", "v20-obv", "v20-inside")
ACTIONS = ("start", "pause", "stop", "restart")
SCHEMA = "cc.v20.controller.preview.v1"
REQUEST_ID = re.compile(r"[a-z0-9][a-z0-9-]{0,47}\Z")


def preview(robot: str, action: str, request_id: str) -> dict:
    """Validate identities strictly and refuse all controls deterministically."""
    if type(robot) is not str or robot not in ROBOTS:
        raise ValueError("CC06_ROBOT_NOT_ALLOWED")
    if type(action) is not str or action not in ACTIONS:
        raise ValueError("CC06_ACTION_NOT_ALLOWED")
    if type(request_id) is not str or REQUEST_ID.fullmatch(request_id) is None:
        raise ValueError("CC06_REQUEST_ID_INVALID")
    return {
        "schema": SCHEMA, "robot": robot, "action": action,
        "request_id": request_id, "decision": "REFUSED_NOT_AUTHORIZED",
        "executed": False, "task_mutated": False,
        "finam_contacted": False, "live_authorized": False,
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="CC-06 offline control preview")
    parser.add_argument("--robot", choices=ROBOTS, required=True)
    parser.add_argument("--action", choices=ACTIONS, required=True)
    parser.add_argument("--request-id", required=True)
    args = parser.parse_args(argv)
    try:
        result = preview(args.robot, args.action, args.request_id)
    except ValueError as error:
        parser.error(str(error))
    print(json.dumps(result, sort_keys=True, separators=(",", ":")))
    return 3  # Refused, never a successful command execution.


if __name__ == "__main__":
    raise SystemExit(main())
