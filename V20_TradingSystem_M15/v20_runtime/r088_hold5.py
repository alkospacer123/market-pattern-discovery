"""TRL-R088 / HOLD5 candidate: observed-session deadline, no broker actions.

TIME3 frozen implementation in finam_execution.py is deliberately untouched.
The caller must independently prove the entry and M15 observations.  We
do not infer exchange sessions from weekdays or elapsed calendar days.
All timestamps are Moscow wall-clock M15 opens, without timezone.
"""
from __future__ import annotations

from datetime import datetime, timedelta
from typing import Iterable

HOLD = "HOLD_UNTIL_SIXTH_OBSERVED_SESSION"
EXIT = "EXIT_AT_SIXTH_OBSERVED_SESSION_OPEN"
MISSED = "MISSED_OR_PASSED_SIXTH_SESSION_OPEN_HALT"
_SESSIONS_HELD = 5

class HOLD5Unverified(ValueError):
    """A missing/open-time/incomplete witness cannot authorize an exit."""


def _grid_msk(t: datetime) -> None:
    if (not isinstance(t, datetime) or t.tzinfo is not None
            or t.second or t.microsecond or t.minute % 15):
        raise HOLD5Unverified("R088_M15_MSK_GRID_INVALID")


def hold5_observed_session_exit(
    *, entry_open_msk: datetime, observed_open_msk: datetime,
    completed_m15_opens: Iterable[datetime],
) -> str:
    """Keep five OBSERVED trading sessions incl. entry; first sixth Open exits.

    `completed_m15_opens` are FINAM-confirmed M15 opens, not future bars
    or a weekday calendar. Exactly as frozen TIME3, session_key=(MSK-9h).date().
    First observed Open can therefore be 09:00 MSK (research TIME3 exit),
    while 07:00 next calendar morning still belongs to the PRIOR session.
    Weekend dates count only when FINAM M15 witnesses a bar for that session.
    If a sixth-session bar has already completed, first Open was missed:
    return MISSED (HALT), never a fictitious past-price market order.

    This candidate has no SQLite, FINAM or order side effects. Safe restart
    requires the same entry + all M15 history to be independently recovered;
    incomplete/corrupt input fails closed.
    """
    _grid_msk(entry_open_msk)
    _grid_msk(observed_open_msk)
    if observed_open_msk < entry_open_msk:
        raise HOLD5Unverified("R088_HOLD5_ENTRY_OR_CLOCK_INVALID")
    try:
        rows = tuple(completed_m15_opens)
    except (TypeError, ValueError) as exc:
        raise HOLD5Unverified("R088_COMPLETED_M15_REQUIRED") from exc
    prev = None
    for stamp in rows:
        _grid_msk(stamp)
        if (prev is not None and stamp <= prev
                or stamp >= observed_open_msk):
            raise HOLD5Unverified("R088_M15_HISTORY_DUPLICATE_FUTURE_OR_UNSORTED")
        prev = stamp
    if entry_open_msk != observed_open_msk and entry_open_msk not in rows:
        raise HOLD5Unverified("R088_ENTRY_OPEN_WITNESS_MISSING")

    # Reuse EXACT frozen V20 session key to keep TIME3 replay parity.
    from .offline_planner import OfflinePlanner
    key = OfflinePlanner._session_key
    entry_session = key(entry_open_msk)
    current_session = key(observed_open_msk)
    observed = sorted({key(stamp) for stamp in rows if stamp >= entry_open_msk}
                      | {current_session, entry_session})
    if len(observed) <= _SESSIONS_HELD:
        return HOLD
    sixth = observed[_SESSIONS_HELD]
    if (len(observed) == _SESSIONS_HELD + 1
            and current_session == sixth
            and not any(key(t) == sixth for t in rows)):
        return EXIT
    return MISSED


def hold5_from_broker_boundary(boundary, *, entry_open_msk: datetime) -> str:
    """Adapter for a REAL V20M15Boundary; no order or persistence methods."""
    from .finam_execution import V20FinamBlocked, V20M15Boundary
    if (not isinstance(boundary, V20M15Boundary)
            or boundary.completed is None
            or "Datetime" not in boundary.completed
            or boundary.completed.empty):
        raise V20FinamBlocked("R088_HOLD5_BOUNDARY_NOT_BROKER_PROVEN")
    try:
        return hold5_observed_session_exit(
            entry_open_msk=entry_open_msk,
            observed_open_msk=boundary.at_msk,
            completed_m15_opens=(
                stamp.to_pydatetime() if hasattr(stamp, "to_pydatetime")
                else stamp for stamp in boundary.completed["Datetime"]
            ),
        )
    except (HOLD5Unverified, TypeError) as exc:
        raise V20FinamBlocked("R088_HOLD5_OBSERVATION_UNVERIFIED") from exc
