"""TRL-R088 isolated offline regression; no FINAM, no real orders."""
from __future__ import annotations
import unittest
from datetime import datetime, timedelta, timezone
from decimal import Decimal
import pandas as pd

from V20_TradingSystem_M15.v20_runtime.r088_hold5 import (
    EXIT, HOLD, MISSED, HOLD5Unverified,
    hold5_observed_session_exit, hold5_from_broker_boundary,
)

def t(day, hm="10:00"):
    return datetime.fromisoformat(day + "T" + hm + ":00")

FRI = "2026-11-13"
MON = "2026-11-16"
TUE = "2026-11-17"
WED = "2026-11-18"
THU = "2026-11-19"
FRI2 = "2026-11-20"


class R088HOLD5ObservedSessions(unittest.TestCase):
    def setUp(self):
        self.entry = t(FRI, "14:00")

    def classify(self, current, dates, *, extras=()):
        complete = [self.entry] + [t(day) for day in dates] + list(extras)
        complete.sort()
        return hold5_observed_session_exit(
            entry_open_msk=self.entry,
            observed_open_msk=current,
            completed_m15_opens=complete,
        )

    def test_five_observed_sessions_including_entry_no_early_exit(self):
        self.assertEqual(self.classify(t(FRI, "14:15"), []), HOLD)
        self.assertEqual(self.classify(t(MON), []), HOLD)
        self.assertEqual(self.classify(t(TUE), [MON]), HOLD)
        self.assertEqual(self.classify(t(WED), [MON, TUE]), HOLD)
        self.assertEqual(self.classify(t(THU), [MON, TUE, WED]), HOLD)

    def test_first_broker_witnessed_open_of_sixth_session(self):
        dates = [MON, TUE, WED, THU]
        self.assertEqual(self.classify(t(FRI2), dates), EXIT)
        # Same restored broker history/entry after reboot means same result.
        rebuilt = tuple([self.entry, *[t(day) for day in dates]])
        self.assertEqual(
            hold5_observed_session_exit(
                entry_open_msk=self.entry,
                observed_open_msk=t(FRI2),
                completed_m15_opens=rebuilt,
            ), EXIT)

    def test_no_calendar_day_counting_during_weekend_and_holiday(self):
        # Fri 13, Tue 17, Wed 18, Thu 19, Fri 20, Mon 23 = 6.
        self.assertEqual(self.classify(t("2026-11-23"), [TUE, WED, THU, FRI2]), EXIT)
        self.assertEqual(self.classify(t(THU), [TUE, WED]), HOLD)

    def test_witnessed_weekend_trading_does_count_as_session(self):
        # Actual M15 bars, not a default weekday rule, authorize weekend count.
        self.assertEqual(
            self.classify(t(WED), ["2026-11-14", "2026-11-15", MON, TUE]),
            EXIT)

    def test_missed_open_or_late_sixth_is_not_retroactive_exit(self):
        five = [MON, TUE, WED, THU]
        self.assertEqual(
            self.classify(t(FRI2, "10:15"), five,
                          extras=[t(FRI2, "10:00")]), MISSED)
        self.assertEqual(
            self.classify(t("2026-11-23"), [*five, FRI2]),
            MISSED)

    def test_first_available_broker_open_can_be_after_10_when_unobserved(self):
        # 10:15 is permitted ONLY when there is no 10:00 completed bar from
        # this session in the fully witnessed FINAM M15 response.
        self.assertEqual(self.classify(t(FRI2, "10:15"),
                                       [MON, TUE, WED, THU]), EXIT)

    def test_early_and_late_bars_do_not_make_extra_session(self):
        self.assertEqual(
            self.classify(t(THU, "10:00"), [MON, TUE, WED],
                          extras=[t("2026-11-14", "07:00"),
                                  t("2026-11-15", "18:30")]), HOLD)

    def test_unverified_bar_or_entry_history_blocks(self):
        complete = [self.entry, t(MON)]
        def run(entry, current, rows):
            return hold5_observed_session_exit(
                entry_open_msk=entry, observed_open_msk=current,
                completed_m15_opens=rows)
        for a,b,c in (
            (self.entry, t(MON), [t(MON)]),
            (self.entry, t(MON), [self.entry,self.entry]),
            (self.entry, t(MON), [self.entry,t("2026-11-15", "10:05")]),
            (self.entry, t(MON), [self.entry,t(MON, "10:15")]),
            (self.entry, self.entry-timedelta(minutes=15), [self.entry]),
        ):
            with self.subTest(a=a,b=b,c=c):
                with self.assertRaises(HOLD5Unverified):
                    run(a,b,c)

    def test_original_time3_frozen_control_unchanged(self):
        from V20_TradingSystem_M15.v20_runtime.finam_execution import (
            V20M15Boundary, frozen_observed_session_exit,
        )
        bars = pd.DataFrame({"Datetime":[self.entry,t(MON)]})
        boundary = V20M15Boundary(
            "CNYRUBF", t(TUE), bars, Decimal("12.345"),
            datetime(2026,11,17,7,tzinfo=timezone.utc),
        )
        self.assertEqual(
            frozen_observed_session_exit(
                boundary, entry_open_msk=self.entry),
            "EXIT_AT_THIRD_OBSERVED_SESSION_OPEN")
        self.assertEqual(hold5_from_broker_boundary(
            boundary, entry_open_msk=self.entry), HOLD)

    def test_typed_finam_boundary_adapter_sixth(self):
        from V20_TradingSystem_M15.v20_runtime.finam_execution import V20M15Boundary
        bars = pd.DataFrame({"Datetime":[self.entry,*[
            t(x) for x in (MON,TUE,WED,THU)]]})
        observed = datetime(2026,11,20,7,tzinfo=timezone.utc)
        for symbol in ("USDRUBF","CNYRUBF","GLDRUBF","IMOEXF"):
            with self.subTest(symbol=symbol):
                boundary = V20M15Boundary(
                    symbol,t(FRI2),bars,Decimal("100"),observed)
                self.assertEqual(hold5_from_broker_boundary(
                    boundary, entry_open_msk=self.entry), EXIT)


if __name__ == "__main__":
    unittest.main()
