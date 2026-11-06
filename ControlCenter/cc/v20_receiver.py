"""Manual V20 receiver. Only CC-owned, admin-protected files; no robot/broker access."""
import json
from pathlib import Path
from .deployment_paths import data_root
from .providers.windows_file import read_windows
from .v20_contract import ROBOTS, NAMES, parse, unconnected, _pairs, _bad_constant

POLICY_ROOT = Path(__file__).absolute().parents[1] / "deployment"
POLICY_NAME = "v20-readonly-policy.json"  # intentionally NOT shipped/approved
SNAPSHOT_ROOT = data_root() / "v20-readonly"
POLICY_KEYS = {"schema_id", "approved", "root_id", "account_aliases"}


def policy_check(value):
    if (type(value) is not dict or set(value) != POLICY_KEYS
            or value["schema_id"] != "cc.v20.source-policy.v1"
            or value["approved"] is not True
            or type(value["root_id"]) is not list or len(value["root_id"]) != 3
            or any(type(x) is not int or x < 0 for x in value["root_id"])
            or type(value["account_aliases"]) is not dict
            or set(value["account_aliases"]) != set(ROBOTS)):
        raise ValueError("V20_SOURCE_NOT_APPROVED")
    from .v20_contract import ALIAS
    if any(type(v) is not str or not ALIAS.fullmatch(v)
           for v in value["account_aliases"].values()):
        raise ValueError("V20_ACCOUNT_BINDING_INVALID")
    if len(set(value["account_aliases"].values())) != len(ROBOTS):
        raise ValueError("V20_ACCOUNTS_NOT_ISOLATED")
    return value


def acquire(now):
    """Exactly one manual one-shot per robot; per-robot failure cannot mask others.

    The caller must hold the existing cross-process manual gate. No retry or
    periodic acquisition. Installed policy does not exist during V20-04.
    """
    try:
        raw_policy = read_windows(str(POLICY_ROOT), POLICY_NAME, 4096, admin_policy=True)
        policy = policy_check(json.loads(raw_policy.decode("utf-8"),
                                         object_pairs_hook=_pairs,
                                         parse_constant=_bad_constant))
    except Exception:
        return {robot: unconnected(robot, "SOURCE_NOT_APPROVED") for robot in ROBOTS}
    result = {}
    for robot in ROBOTS:
        try:
            raw = read_windows(str(SNAPSHOT_ROOT), NAMES[robot], 32768,
                               expected_root=policy["root_id"], admin_policy=True)
            result[robot] = parse(raw, robot, now, policy["account_aliases"][robot])
        except Exception:
            result[robot] = unconnected(robot, "SOURCE_UNAVAILABLE")
    return result
