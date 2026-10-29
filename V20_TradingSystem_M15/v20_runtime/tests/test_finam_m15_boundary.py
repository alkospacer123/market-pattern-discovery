"""Focused V20-08.1 FINAM M15 GET boundary tests, synthetic responses only."""
from __future__ import annotations

from datetime import datetime, timedelta, timezone
from decimal import Decimal
import hashlib
import unittest
import pandas as pd
from urllib.parse import parse_qs, urlsplit

from TradingSystemLab.stage8_robot.finam_api import FinamAPI, Response
from TradingSystemLab.stage8_robot.production_runtime import _load_registry

from V20_TradingSystem_M15.v20_runtime.finam_execution import (
    V20FinamBlocked, V20FinamReadAdapter, read_finam_m15_boundary,
    V20M15Boundary, frozen_observed_session_exit,
)

ACCOUNT = "no-network-m15-boundary-a"
ACCOUNT_HASH = hashlib.sha256(ACCOUNT.encode()).hexdigest()
SYMBOL = _load_registry()["USDRUBF"]["finam_symbol"]
UTC = timezone.utc


def bar(stamp, *, current=False):
    item = {"timestamp": stamp.isoformat(), "open": {"value": "85.00"}}
    if not current:
        item.update(high={"value": "85.10"}, low={"value": "84.90"},
                    close={"value": "85.02"}, volume={"value": "100"})
    return item


AT = datetime(2026, 10, 24, 7, 30, 5, tzinfo=UTC)
START = datetime(2026, 10, 24, 6, 30, tzinfo=UTC)
COMPLETED_1 = datetime(2026, 10, 24, 7, 0, tzinfo=UTC)
COMPLETED_2 = datetime(2026, 10, 24, 7, 15, tzinfo=UTC)
CURRENT = datetime(2026, 10, 24, 7, 30, tzinfo=UTC)


class FakeFinam(FinamAPI):
    def __init__(self):
        self.rows = [bar(COMPLETED_1), bar(COMPLETED_2), bar(CURRENT, current=True)]
        self.calls = []

    def create_session(self):
        return None

    def session_details(self):
        return {"readonly": False, "account_ids": [ACCOUNT]}

    def _request(self, method, path, *args, **kwargs):
        self.calls.append((method, path))
        return Response(200, {"symbol": SYMBOL, "bars": self.rows}, None)

    def place_order(self, *_args, **_kwargs):
        raise AssertionError("M15_BARS_MUST_NOT_PLACE_ORDER")

    def place_sltp_order(self, *_args, **_kwargs):
        raise AssertionError("M15_BARS_MUST_NOT_PLACE_SLTP")


class M15BoundaryTests(unittest.TestCase):
    def setUp(self):
        self.api = FakeFinam()
        self.reader = V20FinamReadAdapter(
            api=self.api, robot_id="v20-shallow", account_id=ACCOUNT,
            expected_account_hash=ACCOUNT_HASH,
        )
        self.reader.authenticate()

    def test_completed_history_and_new_open_are_separate_and_h1_unchanged(self):
        proof = read_finam_m15_boundary(
            self.reader, symbol="USDRUBF", from_utc=START, now=AT,
        )
        self.assertEqual(proof.witnessed_open, Decimal("85.00"))
        self.assertEqual(proof.at_msk, datetime(2026, 10, 24, 10, 30))
        self.assertEqual(len(proof.completed), 2)
        self.assertEqual(proof.completed.Datetime.iloc[-1].to_pydatetime(),
                         datetime(2026, 10, 24, 10, 15))
        self.assertNotIn(datetime(2026, 10, 24, 10, 30),
                         set(proof.completed.Datetime.dt.to_pydatetime()))
        method, route = self.api.calls[-1]
        self.assertEqual(method, "GET")
        path = urlsplit(route)
        self.assertEqual(path.path, "/v1/instruments/" + SYMBOL + "/bars")
        qs = parse_qs(path.query)
        self.assertEqual(qs["timeframe"], ["TIME_FRAME_M15"])
        self.assertNotIn("TIME_FRAME_H1", route)

    def test_1415_fractional_seconds_preserve_earliest_bar_and_exclude_future(self):
        # Exact incident class: clock 14:15:00.264, candles at xx:00.000.
        # FINAM REST: inclusive start, exclusive end; a future candle at
        # boundary+15m MUST NOT be returned by a conforming GET.
        from_utc = COMPLETED_1 + timedelta(microseconds=264000)
        observed = AT + timedelta(microseconds=263995)
        all_bars = [bar(COMPLETED_1), bar(COMPLETED_2),
                    bar(CURRENT, current=True),
                    bar(CURRENT + timedelta(minutes=15), current=True)]

        def filtered_get(method, path, *_args, **_kwargs):
            self.api.calls.append((method, path))
            query = parse_qs(urlsplit(path).query)
            low = datetime.fromisoformat(query["interval.start_time"][0])
            high = datetime.fromisoformat(query["interval.end_time"][0])
            rows = [v for v in all_bars
                    if low <= datetime.fromisoformat(v["timestamp"]) < high]
            return Response(200, {"symbol": SYMBOL, "bars": rows}, None)

        self.api._request = filtered_get
        proof = read_finam_m15_boundary(
            self.reader, symbol="USDRUBF", from_utc=from_utc, now=observed,
        )
        params = parse_qs(urlsplit(self.api.calls[-1][1]).query)
        self.assertEqual(params["interval.start_time"], ["2026-10-24T07:00:00+00:00"])
        self.assertEqual(params["interval.end_time"], ["2026-10-24T07:45:00+00:00"])
        self.assertEqual(len(proof.completed), 2)
        self.assertEqual(proof.witnessed_open, Decimal("85.00"))
        self.assertEqual(self.api.calls[-1][0], "GET")

    def test_missing_new_open_or_stale_boundary_blocks(self):
        self.api.rows = [bar(COMPLETED_1), bar(COMPLETED_2)]
        with self.assertRaisesRegex(V20FinamBlocked, "M15_NEXT_OPEN_WITNESS_MISSING"):
            read_finam_m15_boundary(self.reader, symbol="USDRUBF", from_utc=START, now=AT)
        self.api.rows.append(bar(CURRENT, current=True))
        with self.assertRaisesRegex(V20FinamBlocked, "M15_IMMEDIATE_NEXT_OPEN_MISSED"):
            read_finam_m15_boundary(
                self.reader, symbol="USDRUBF", from_utc=START,
                now=AT+timedelta(seconds=65),
            )

    def test_technical_uses_completed_close_without_open_or_wait(self):
        # At 10:33 no new-bar Open need exist: normal NEXT_OPEN still blocks.
        self.api.rows = [bar(COMPLETED_1), bar(COMPLETED_2)]
        observed = AT + timedelta(minutes=3)
        with self.assertRaisesRegex(V20FinamBlocked, "M15_IMMEDIATE_NEXT_OPEN_MISSED"):
            read_finam_m15_boundary(
                self.reader, symbol="USDRUBF", from_utc=START, now=observed,
            )
        technical = read_finam_m15_boundary(
            self.reader, symbol="USDRUBF", from_utc=START,
            now=observed, technical_reference=True,
        )
        self.assertEqual(technical.witnessed_open, Decimal("85.02"))
        self.assertEqual(len(technical.completed), 2)
        self.assertEqual(self.api.calls[-1][0], "GET")

    def test_technical_refuses_stale_completed_bar_without_order(self):
        self.api.rows = [bar(COMPLETED_1)]
        with self.assertRaisesRegex(V20FinamBlocked, "TECHNICAL_NO_FRESH_COMPLETED_M15"):
            read_finam_m15_boundary(
                self.reader, symbol="USDRUBF", from_utc=START,
                now=AT+timedelta(minutes=3), technical_reference=True,
            )
        self.assertTrue(all(method == "GET" for method, _ in self.api.calls))

    def test_wrong_grid_duplicate_or_future_bar_blocks(self):
        self.api.rows[-1] = bar(CURRENT+timedelta(minutes=5), current=True)
        with self.assertRaisesRegex(V20FinamBlocked, "M15_FINAM_TIMESTAMP_OUT_OF_RANGE"):
            read_finam_m15_boundary(self.reader, symbol="USDRUBF", from_utc=START, now=AT)
        self.assertEqual(self.reader._m15_timestamp_diagnostic["reason"], "AFTER_NOW")
        self.assertEqual(self.reader._m15_timestamp_diagnostic["symbol"], "USDRUBF")
        self.api.rows = [bar(COMPLETED_1), bar(COMPLETED_2), bar(COMPLETED_2),
                         bar(CURRENT, current=True)]
        with self.assertRaisesRegex(V20FinamBlocked, "M15_DUPLICATE_OR_UNSORTED_BARS"):
            read_finam_m15_boundary(self.reader, symbol="USDRUBF", from_utc=START, now=AT)

    def test_third_observed_session_exit_only_at_witnessed_open(self):
        entry = datetime(2026, 10, 20, 10, 15)
        completed_days = [entry, datetime(2026, 10, 21, 10, 0)]
        frame = pd.DataFrame({"Datetime": completed_days})
        due = V20M15Boundary("USDRUBF", datetime(2026, 10, 22, 10, 0),
                              frame, Decimal("85.00"), AT)
        self.assertEqual(frozen_observed_session_exit(due, entry_open_msk=entry),
                         "EXIT_AT_THIRD_OBSERVED_SESSION_OPEN")
        waiting = V20M15Boundary("USDRUBF", datetime(2026, 10, 21, 10, 15),
                                  frame, Decimal("85.00"), AT)
        self.assertEqual(frozen_observed_session_exit(waiting, entry_open_msk=entry),
                         "HOLD_UNTIL_THIRD_OBSERVED_SESSION")

    def test_missed_third_open_refuses_historical_exit_and_missing_entry(self):
        entry = datetime(2026, 10, 20, 10, 15)
        frame = pd.DataFrame({"Datetime": [
            entry, datetime(2026, 10, 21, 10, 0),
            datetime(2026, 10, 22, 10, 0),
        ]})
        late = V20M15Boundary("USDRUBF", datetime(2026, 10, 22, 10, 15),
                               frame, Decimal("85.00"), AT)
        self.assertEqual(frozen_observed_session_exit(late, entry_open_msk=entry),
                         "MISSED_OR_PASSED_THIRD_SESSION_OPEN_HALT")
        missing = V20M15Boundary("USDRUBF", datetime(2026, 10, 22, 10, 0),
                                  frame.iloc[1:], Decimal("85.00"), AT)
        with self.assertRaisesRegex(V20FinamBlocked, "ENTRY_SESSION_OBSERVATION_MISSING"):
            frozen_observed_session_exit(missing, entry_open_msk=entry)


if __name__ == "__main__":
    unittest.main()
