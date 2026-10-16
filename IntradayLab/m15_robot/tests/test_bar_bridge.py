"""Synthetic FINAM M15 candle publication contract — no network or real fills."""
import unittest
from datetime import datetime, timedelta, timezone

from IntradayLab.m15_robot.bar_bridge import (
    M15BarAuthorityError, completed_close_labeled_m15, trading_windows,
)

UTC = timezone.utc
AT = datetime(2026, 10, 16, 7, 0, tzinfo=UTC)


def iso(t):
    return t.isoformat()


def sessions(*windows):
    return {"sessions": [
        {"type": "CORE_TRADING", "interval": {"start_time": iso(a), "end_time": iso(b)}}
        for a, b in windows
    ]}


def bars(*opens):
    return {"bars": [
        {"timestamp": iso(t), "open": {"value": "100"}, "high": {"value": "102"},
         "low": {"value": "99"}, "close": {"value": "101"}, "volume": {"value": "10"}}
        for t in opens
    ]}


def bridge(response, schedule=None, now=None, *, verified=True):
    return completed_close_labeled_m15(
        response, schedule or sessions((AT, AT + timedelta(hours=2))),
        observed_at=now or AT + timedelta(minutes=30),
        verified_open_labels=verified,
    )


class M15Publication(unittest.TestCase):
    def test_unverified_open_labels_always_stop(self):
        with self.assertRaisesRegex(M15BarAuthorityError, "NOT_VERIFIED"):
            bridge(bars(AT, AT + timedelta(minutes=15)), verified=False)

    def test_next_open_at_now_proves_previous_complete(self):
        df = bridge(bars(AT, AT + timedelta(minutes=15)),
                    now=AT + timedelta(minutes=15))
        self.assertEqual(len(df), 1)
        self.assertEqual(df.index[0].hour, 10)  # UTC 07:15 = MSK 10:15
        self.assertEqual(df.index[0].minute, 15)
        self.assertEqual(df.iloc[0]["Close"], 101)

    def test_no_adjacent_next_open_never_assumes_completion(self):
        df = bridge(bars(AT), now=AT + timedelta(minutes=45))
        self.assertEqual(len(df), 0)

    def test_next_not_published_yet_blocks_last(self):
        df = bridge(bars(AT, AT + timedelta(minutes=15)),
                    now=AT + timedelta(minutes=16))
        self.assertEqual(len(df), 1)

    def test_two_witnessed_adjacent_candles(self):
        df = bridge(bars(AT, AT + timedelta(minutes=15), AT + timedelta(minutes=30)),
                    now=AT + timedelta(minutes=30))
        self.assertEqual(len(df), 2)
        self.assertEqual(df.index[1].minute, 30)

    def test_gap_has_no_fabricated_ohlc(self):
        df = bridge(bars(AT, AT + timedelta(minutes=15), AT + timedelta(minutes=45)),
                    now=AT + timedelta(minutes=45))
        self.assertEqual(len(df), 1)

    def test_duplicate_open_fails_closed(self):
        with self.assertRaisesRegex(M15BarAuthorityError, "DUPLICATE"):
            bridge(bars(AT, AT))

    def test_reverse_unsorted_fails_closed(self):
        with self.assertRaisesRegex(M15BarAuthorityError, "DUPLICATE"):
            bridge(bars(AT + timedelta(minutes=15), AT))

    def test_future_broker_open_rejected(self):
        with self.assertRaisesRegex(M15BarAuthorityError, "FUTURE"):
            bridge(bars(AT + timedelta(hours=1)), now=AT)

    def test_bad_grid_rejected(self):
        with self.assertRaisesRegex(M15BarAuthorityError, "OPEN_GRID"):
            bridge(bars(AT + timedelta(minutes=2)),
                   now=AT + timedelta(minutes=15))

    def test_gap_over_clearing_boundary_does_not_count_as_adjacent(self):
        schedule = sessions((AT, AT + timedelta(minutes=30)),
                            (AT + timedelta(hours=1), AT + timedelta(hours=2)))
        df = bridge(bars(AT + timedelta(minutes=15),
                         AT + timedelta(hours=1), AT + timedelta(hours=1, minutes=15)),
                    schedule=schedule, now=AT + timedelta(hours=1, minutes=15))
        self.assertEqual(len(df), 1)
        self.assertEqual(df.index[0].minute, 15)

    def test_touching_trading_windows_are_merged(self):
        ws = trading_windows(sessions(
            (AT, AT + timedelta(minutes=30)),
            (AT + timedelta(minutes=30), AT + timedelta(hours=1)),
        ))
        self.assertEqual(ws, ((AT, AT + timedelta(hours=1)),))

    def test_overlapping_trading_windows_rejected(self):
        with self.assertRaisesRegex(M15BarAuthorityError, "OVERLAP"):
            trading_windows(sessions(
                (AT, AT + timedelta(hours=1)),
                (AT + timedelta(minutes=45), AT + timedelta(hours=2)),
            ))

    def test_session_end_without_next_open_not_fabricated(self):
        schedule = sessions((AT, AT + timedelta(minutes=30)))
        df = bridge(bars(AT + timedelta(minutes=15)), schedule,
                    now=AT + timedelta(hours=2))
        self.assertEqual(len(df), 0)

    def test_unknown_session_type_fails(self):
        with self.assertRaisesRegex(M15BarAuthorityError, "SESSION_INVALID"):
            trading_windows({"sessions": [{
                "type": "UNKNOWN",
                "interval": {"start_time": iso(AT), "end_time": iso(AT + timedelta(hours=1))}
            }]})

    def test_negative_and_nonfinite_ohlc_rejected(self):
        for wrong in ("-1", "NaN", "Infinity"):
            with self.subTest(wrong=wrong):
                b = bars(AT, AT + timedelta(minutes=15))
                b["bars"][0]["close"]["value"] = wrong
                with self.assertRaises(M15BarAuthorityError):
                    bridge(b, now=AT + timedelta(minutes=15))

    def test_reject_malformed_rest_timestamp(self):
        b = bars(AT, AT + timedelta(minutes=15))
        b["bars"][0]["timestamp"] = "2026-10-16T07:00:00"
        with self.assertRaisesRegex(M15BarAuthorityError, "TZ_REQUIRED"):
            bridge(b)


if __name__ == "__main__":
    unittest.main()
