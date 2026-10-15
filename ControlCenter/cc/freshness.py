"""Display-only freshness. Thresholds here grant no operational authority."""
from datetime import datetime, timedelta, timezone
from .models import DataProvenance, RobotStatus, State, aware

MSK = timezone(timedelta(hours=3), name="MSK")
MAX_SNAPSHOT_AGE = 10  # synthetic snapshots refresh every 2s
MAX_CLOCK_SKEW = 2


def freshness(provenance: DataProvenance, now: datetime) -> State:
    aware(now)
    if provenance.observed_at is None:
        return State.UNKNOWN
    age = (now - provenance.observed_at).total_seconds()
    if age < -MAX_CLOCK_SKEW:
        return State.UNKNOWN
    return State.STALE if age > MAX_SNAPSHOT_AGE else State.HEALTHY


def display_state(status: RobotStatus, now: datetime) -> State:
    quality = freshness(status.provenance, now)
    if quality != State.HEALTHY:
        return quality
    if status.state == State.HEALTHY:
        if status.heartbeat_at is None:
            return State.UNKNOWN
        age = (now - status.heartbeat_at).total_seconds()
        if age < -MAX_CLOCK_SKEW:
            return State.UNKNOWN
        if age > MAX_SNAPSHOT_AGE:
            return State.STALE
    return status.state


def stamp(value: datetime | None) -> str:
    if value is None:
        return "UNKNOWN"
    aware(value)
    return f"{value.astimezone(timezone.utc):%d.%m.%Y %H:%M:%S} UTC · {value.astimezone(MSK):%H:%M:%S} MSK"


def metric(value: float | int | None, suffix: str = "") -> str:
    if value is None:
        return "UNKNOWN"
    return f"{value:,.2f}{suffix}".replace(',', ' ')
