import json
from datetime import datetime, timezone

from TradingSystemLab.stage8_robot.h1_timing_diagnostic import collect


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
