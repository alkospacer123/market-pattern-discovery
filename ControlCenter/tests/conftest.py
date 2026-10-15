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


@pytest.fixture
def h1_export():
    import json
    from pathlib import Path
    return json.loads((Path(__file__).parents[1] / 'fixtures/h1/h1.snapshot.json').read_text())


@pytest.fixture
def publish(tmp_path, monkeypatch):
    import json
    import cc.providers.h1_readonly as adapter
    monkeypatch.setattr(adapter, 'FIXTURE_ROOT', tmp_path)

    def write(value, *, seal=True):
        if seal:
            value['payload_sha256'] = adapter.canonical_digest(value)
        path = tmp_path / 'h1.snapshot.json'
        path.write_text(json.dumps(value, allow_nan=True))
        return path
    return write
