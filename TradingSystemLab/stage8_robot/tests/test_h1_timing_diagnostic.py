import json
from datetime import datetime, timezone
import pytest

from TradingSystemLab.stage8_robot import h1_timing_diagnostic as diagnostic
from TradingSystemLab.stage8_robot.h1_timing_diagnostic import (
    REPOSITORY_OUTPUT_FORBIDDEN,
    REPOSITORY_ROOT,
    collect,
    validated_external_output,
)


class EvidenceAPI:
    def __init__(self):
        self.calls=[]
        self.last_server_timestamp=None
    def create_session(self):
        self.calls.append(("create_session",))
    def schedule(self, symbol):
        self.calls.append(("schedule", symbol)); self.last_server_timestamp="Thu, 01 Oct 2026 10:00:00 GMT"
        return {"sessions":[{"type":"SESSION_TYPE_MAIN", "interval":{
            "start_time":"2026-10-01T06:50:00+00:00", "end_time":"2026-10-01T20:50:00Z"},
            "account_id":"must disappear"}]}
    def bars(self, symbol, start, end):
        self.calls.append(("bars", symbol, start, end)); self.last_server_timestamp="Thu, 01 Oct 2026 10:00:01 GMT"
        return {"bars":[{"timestamp":"2026-10-01T07:00:00Z", "close":"secret-price"}]}
    def place_order(self, *_a, **_k): raise AssertionError("order call")
    submit_order=cancel_order=modify_order=place_order


def test_collector_projects_only_public_market_time_and_has_no_order_calls():
    api=EvidenceAPI()
    now=lambda: datetime(2026,10,1,10,0,2,tzinfo=timezone.utc)
    evidence=collect(api, clock=now)
    encoded=json.dumps(evidence)
    assert len(evidence["instruments"]) == 4
    assert all(set(row)=={"symbol","sessions","h1_timestamps","schedule_observed_at",
                              "schedule_server_timestamp","bars_observed_at","bars_server_timestamp"}
               for row in evidence["instruments"])
    assert "secret-price" not in encoded and "account_id" not in encoded
    assert not ({name for name,*_ in api.calls} & {"place_order","submit_order","cancel_order","modify_order"})
    assert evidence["order_capable_calls"] is False


@pytest.mark.parametrize(
    "output",
    [
        REPOSITORY_ROOT,
        REPOSITORY_ROOT / "nested" / "evidence.json",
        REPOSITORY_ROOT.parent / REPOSITORY_ROOT.name / ".." / REPOSITORY_ROOT.name / "evidence.json",
    ],
    ids=["repository-root", "nested-repository-path", "canonical-dot-dot"],
)
def test_repository_output_is_rejected_before_collection_or_write(monkeypatch, output):
    collected = False

    def forbidden_collect(*_args, **_kwargs):
        nonlocal collected
        collected = True
        raise AssertionError("collection must not start for a forbidden destination")

    monkeypatch.setattr(diagnostic, "collect", forbidden_collect)
    with pytest.raises(SystemExit, match=f"^{REPOSITORY_OUTPUT_FORBIDDEN}$"):
        diagnostic.main(["--output", str(output)])
    assert collected is False
    if output != REPOSITORY_ROOT:
        assert not output.resolve().exists()


def test_external_runtime_output_is_accepted_and_written(monkeypatch, tmp_path):
    output = tmp_path / "runtime" / "evidence.json"
    assert validated_external_output(output) == output.resolve()
    monkeypatch.setenv("FINAM_MODE", "REAL_READONLY")
    monkeypatch.setenv("NEW_ENTRIES_DISABLED", "true")
    monkeypatch.setenv("FINAM_API_SECRET", "test-placeholder")
    monkeypatch.setattr(diagnostic, "FinamAPI", lambda _secret: object())
    monkeypatch.setattr(diagnostic, "collect", lambda _api, **_kwargs: {"schema": "test"})
    assert diagnostic.main(["--output", str(output)]) == 0
    assert json.loads(output.read_text(encoding="utf-8")) == {"schema": "test"}


def test_existing_symlink_into_repository_is_rejected(tmp_path):
    link = tmp_path / "checkout"
    try:
        link.symlink_to(REPOSITORY_ROOT, target_is_directory=True)
    except OSError as exc:
        pytest.skip(f"symlinks unavailable: {exc}")
    with pytest.raises(diagnostic.DiagnosticSafetyFault, match=f"^{REPOSITORY_OUTPUT_FORBIDDEN}$"):
        validated_external_output(link / "evidence.json")
