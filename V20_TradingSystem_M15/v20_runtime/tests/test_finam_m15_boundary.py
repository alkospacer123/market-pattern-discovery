"""Focused V20-08.1 FINAM M15 GET boundary tests, synthetic responses only."""
from __future__ import annotations

from datetime import datetime, timedelta, timezone
from decimal import Decimal
import hashlib
import unittest
from urllib.parse import parse_qs, urlsplit

from TradingSystemLab.stage8_robot.finam_api import FinamAPI, Response
from TradingSystemLab.stage8_robot.production_runtime import _load_registry

from V20_TradingSystem_M15.v20_runtime.finam_execution import (
    V20FinamBlocked, V20FinamReadAdapter, read_finam_m15_boundary,
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

    def test_wrong_grid_duplicate_or_future_bar_blocks(self):
        self.api.rows[-1] = bar(CURRENT+timedelta(minutes=5), current=True)
        with self.assertRaisesRegex(V20FinamBlocked, "M15_FINAM_TIMESTAMP_OUT_OF_RANGE"):
            read_finam_m15_boundary(self.reader, symbol="USDRUBF", from_utc=START, now=AT)
        self.api.rows = [bar(COMPLETED_1), bar(COMPLETED_2), bar(COMPLETED_2),
                         bar(CURRENT, current=True)]
        with self.assertRaisesRegex(V20FinamBlocked, "M15_DUPLICATE_OR_UNSORTED_BARS"):
            read_finam_m15_boundary(self.reader, symbol="USDRUBF", from_utc=START, now=AT)


if __name__ == "__main__":
    unittest.main()
