"""MOEX futures ISS calendar contract and pinned initial M15 source (OFFLINE)."""
from __future__ import annotations

from datetime import date, datetime, timedelta
from hashlib import sha256
from unittest import TestCase, main
from unittest.mock import patch
from urllib.parse import parse_qs, urlsplit
import json

from V20_TradingSystem_M15.v20_runtime.ext2_history_bridge import (
    EXT2HistoryBlocked, m15_history_sha256,
)
from V20_TradingSystem_M15.v20_runtime.r070_moex_calendar import (
    MOEX_FUTURES_PATH, fetch_moex_futures_calendar,
    parse_moex_futures_calendar,
)
from V20_TradingSystem_M15.v20_runtime.r070_initial_bootstrap import (
    prepare_r070_initial_m15,
)
from V20_TradingSystem_M15.v20_runtime.tests.test_ext2_history_bridge import (
    make_bars,
)


def fixture(days: list[tuple[str, int, str | None, str | None]]) -> bytes:
    # Schema is the futures-specific one, NOT generic futures_workday.
    data = [[d, traded, session, reason, "2026-11-16 10:00:00"]
            for d, traded, session, reason in days]
    return json.dumps({"off_days": {
        "columns": ["tradedate", "is_traded", "trade_session_date",
                    "reason", "updatetime"],
        "data": data,
    }}, separators=(",", ":")).encode()


class MoexFuturesCalendarTests(TestCase):
    def test_weekend_session_and_off_day_are_not_inferred_weekdays(self):
        raw = fixture([
            ("2026-11-02", 1, None, "N"),
            ("2026-11-03", 1, None, "N"),
            ("2026-11-04", 1, "2026-11-05", "W"),
            ("2026-11-05", 1, None, "N"),
            ("2026-11-06", 0, None, "H"),
            ("2026-11-07", 1, "2026-11-09", "W"),
            ("2026-11-08", 1, "2026-11-09", "W"),
        ])
        open_days, digest = parse_moex_futures_calendar(
            raw, date_from=date(2026, 11, 2), date_till=date(2026, 11, 8))
        self.assertEqual(open_days, tuple(
            date(2026, 11, n) for n in (2, 3, 4, 5, 7, 8)))
        self.assertEqual(digest, sha256(raw).hexdigest())

    def test_missing_duplicate_unknown_or_inconsistent_row_blocks(self):
        start, end = date(2026, 11, 7), date(2026, 11, 8)
        cases = [
            [("2026-11-07", 1, "2026-11-09", "W")],
            [("2026-11-07", 1, "2026-11-09", "W")] * 2,
            [("2026-11-07", None, None, None),
             ("2026-11-08", 1, "2026-11-09", "W")],
            [("2026-11-07", 0, "2026-11-09", "W"),
             ("2026-11-08", 1, "2026-11-09", "W")],
            [("2026-11-07", 1, None, "W"),
             ("2026-11-08", 1, "2026-11-09", "W")],
            [("2026-11-07", 1, "2026-11-07", "W"),
             ("2026-11-08", 1, "2026-11-09", "W")],
        ]
        for rows in cases:
            with self.subTest(rows=rows), self.assertRaisesRegex(
                    EXT2HistoryBlocked, "R070_MOEX_CALENDAR_INVALID"):
                parse_moex_futures_calendar(
                    fixture(rows), date_from=start, date_till=end)

    def test_https_get_only_source_and_missing_payload_fails(self):
        raw = fixture([
            ("2026-11-07", 1, "2026-11-09", "W"),
            ("2026-11-08", 1, "2026-11-09", "W"),
        ])
        observed = []
        class Response:
            def __enter__(self): return self
            def __exit__(self, *_): return False
            def geturl(self):
                return "https://iss.moex.com/iss/calendars/futures.json"
            def getcode(self): return 200
            def read(self, size): return raw
        class Opener:
            def open(self, request, timeout):
                observed.append((request.full_url, request.get_method(), timeout))
                return Response()
        with patch(
            "V20_TradingSystem_M15.v20_runtime.r070_moex_calendar.build_opener",
            return_value=Opener()):
            days = fetch_moex_futures_calendar(
                date_from=date(2026, 11, 7), date_till=date(2026, 11, 8))
        self.assertEqual(days, (date(2026, 11, 7), date(2026, 11, 8)))
        self.assertEqual(len(observed), 1)
        url, method, timeout = observed[0]
        self.assertEqual(method, "GET")
        self.assertEqual(urlsplit(url).netloc, "iss.moex.com")
        self.assertEqual(urlsplit(url).path, MOEX_FUTURES_PATH)
        self.assertEqual(parse_qs(urlsplit(url).query)["show_all_days"], ["1"])
        self.assertEqual(timeout, 10)
        with patch(
            "V20_TradingSystem_M15.v20_runtime.r070_moex_calendar.build_opener",
            side_effect=OSError("MOEX_OFFLINE")):
            with self.assertRaisesRegex(EXT2HistoryBlocked, "R070_MOEX_CALENDAR_READ_UNVERIFIED"):
                fetch_moex_futures_calendar(
                    date_from=date(2026, 11, 7),
                    date_till=date(2026, 11, 8))


class R070PinnedBootstrapTests(TestCase):
    def test_pinned_sources_and_moex_calendar_combined_without_new_bars(self):
        full = make_bars()
        old = full.iloc[:18*32].copy()
        recent = full.iloc[17*32:].copy()
        signal = full.Datetime.iloc[-1].to_pydatetime()
        days = tuple(d.date() for d in full.Datetime.iloc[17*32::32])
        with patch(
            "V20_TradingSystem_M15.v20_runtime.r070_initial_bootstrap.load_r060_pinned_csv",
            return_value=old) as seed, patch(
            "V20_TradingSystem_M15.v20_runtime.r070_initial_bootstrap.load_finam_terminal_csv",
            return_value=recent) as terminal, patch(
            "V20_TradingSystem_M15.v20_runtime.r070_initial_bootstrap.fetch_moex_futures_calendar",
            return_value=days) as calendar:
            combined, digest = prepare_r070_initial_m15(
                symbol="CNYRUBF", r060_seed_csv="r060-seed.csv",
                finam_terminal_csv="finam-terminal.csv",
                signal_open_msk=signal,
                observed_at_msk=signal + timedelta(minutes=15))
        self.assertTrue(combined.Datetime.equals(full.Datetime))
        self.assertEqual(digest, m15_history_sha256(full))
        self.assertEqual(seed.call_args.kwargs["symbol"], "CNYRUBF")
        self.assertEqual(len(terminal.call_args.kwargs["expected_sha256"]), 64)
        self.assertEqual(calendar.call_args.kwargs["date_from"],
                         recent.Datetime.iloc[0].date())
        self.assertEqual(calendar.call_args.kwargs["date_till"], signal.date())

    def test_sparse_session_or_future_bar_never_bootstraps(self):
        full = make_bars()
        old = full.iloc[:18*32].copy()
        recent = full.iloc[17*32:].copy()
        signal = full.Datetime.iloc[-1].to_pydatetime()
        days = tuple(d.date() for d in full.Datetime.iloc[17*32::32])
        with patch(
            "V20_TradingSystem_M15.v20_runtime.r070_initial_bootstrap.load_r060_pinned_csv",
            return_value=old), patch(
            "V20_TradingSystem_M15.v20_runtime.r070_initial_bootstrap.load_finam_terminal_csv",
            return_value=recent), patch(
            "V20_TradingSystem_M15.v20_runtime.r070_initial_bootstrap.fetch_moex_futures_calendar",
            return_value=days):
            with self.assertRaisesRegex(
                    EXT2HistoryBlocked, "R070_BOOTSTRAP_SIGNAL_M15_NOT_IN_EXPORT"):
                prepare_r070_initial_m15(
                    symbol="CNYRUBF", r060_seed_csv="r060-seed.csv",
                    finam_terminal_csv="finam-terminal.csv",
                    signal_open_msk=signal + timedelta(minutes=15),
                    observed_at_msk=signal + timedelta(minutes=30))
        with patch(
            "V20_TradingSystem_M15.v20_runtime.r070_initial_bootstrap.load_r060_pinned_csv",
            return_value=old), patch(
            "V20_TradingSystem_M15.v20_runtime.r070_initial_bootstrap.load_finam_terminal_csv",
            return_value=recent.drop(recent.index[-5:])), patch(
            "V20_TradingSystem_M15.v20_runtime.r070_initial_bootstrap.fetch_moex_futures_calendar",
            return_value=days):
            with self.assertRaisesRegex(
                    EXT2HistoryBlocked, "R070_BOOTSTRAP_SIGNAL_M15_NOT_IN_EXPORT"):
                prepare_r070_initial_m15(
                    symbol="CNYRUBF", r060_seed_csv="r060-seed.csv",
                    finam_terminal_csv="finam-terminal.csv",
                    signal_open_msk=signal,
                    observed_at_msk=signal + timedelta(minutes=15))


if __name__ == "__main__":
    main()
