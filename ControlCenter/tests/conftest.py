from datetime import datetime, timezone
import pytest
from cc.models import RobotId
from cc.providers.synthetic import SyntheticProvider


@pytest.fixture
def now():
    return datetime(2026, 10, 15, 18, 20, 0, tzinfo=timezone.utc)


@pytest.fixture
def h1(now):
    return SyntheticProvider().snapshot(RobotId.H1, "BASELINE", now)


@pytest.fixture
def m15(now):
    return SyntheticProvider().snapshot(RobotId.M15, "BASELINE", now)
