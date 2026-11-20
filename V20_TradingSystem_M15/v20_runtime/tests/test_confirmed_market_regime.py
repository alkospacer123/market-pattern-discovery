"""Focused as-of historical regime confirmation tests; no FINAM."""
import unittest
from datetime import datetime, timedelta

from V20_TradingSystem_M15.v20_runtime.confirmed_market_regime import (
    cohorts, confirmed_card, load_published, SOURCE_PATH,
)


def make_events(kinds, *, instrument="USDRUBF", start=None):
    """20 complete distinct raw events per proposed block; 3 days apart."""
    base = start or datetime(2025, 1, 1, 9)
    events = []
    for i, kind in enumerate(kinds):
        for j in range(20):
            ts = base + timedelta(days=(i * 20 + j) * 3)
            fp2 = "1" if kind == "STRONG" and j < 12 else "0"
            stop_aware = "1.0" if kind == "STRONG" else "-1.0" if kind == "WEAK" else "0.5"
            events.append(dict(instrument=instrument, contract=instrument,
                               signal=ts.isoformat(sep=" "),
                               available=(ts + timedelta(days=2)).isoformat(sep=" "),
                               fp2=fp2, stop_aware=stop_aware))
    return events


class ConfirmedMarketRegimeTests(unittest.TestCase):
    def test_two_weak_only(self):
        rows = make_events(["STRONG", "WEAK", "WEAK"])
        at = rows[-1]["available"]
        early = confirmed_card(rows, "USDRUBF", as_of=rows[39]["available"])
        self.assertEqual(early["historical_observation"], "UNCONFIRMED_OR_TRANSITION")
        confirmed = confirmed_card(rows, "USDRUBF", as_of=at)
        self.assertEqual(confirmed["historical_observation"], "CONFIRMED_OBSERVED_WEAK")
        self.assertEqual(confirmed["live_current_status"], "LIVE_FEED_NOT_CONNECTED")
        self.assertFalse(confirmed["trading_gate"])

    def test_two_strong_required_to_recover(self):
        rows = make_events(["WEAK", "WEAK", "STRONG", "STRONG"])
        early = confirmed_card(rows, "USDRUBF", as_of=rows[59]["available"])
        self.assertEqual(early["historical_observation"], "UNCONFIRMED_OR_TRANSITION")
        later = confirmed_card(rows, "USDRUBF", as_of=rows[79]["available"])
        self.assertEqual(later["historical_observation"], "CONFIRMED_OBSERVED_FAVORABLE")
        self.assertFalse(later["prediction_validated"])

    def test_horizon_availability_is_atomic(self):
        rows = make_events(["WEAK", "WEAK"])
        cutoff = datetime.fromisoformat(rows[-1]["available"])
        at = confirmed_card(rows, "USDRUBF", as_of=cutoff)
        before = confirmed_card(rows, "USDRUBF", as_of=cutoff - timedelta(seconds=1))
        self.assertEqual(at["complete_blocks"], 2)
        self.assertEqual(before["complete_blocks"], 1)
        self.assertEqual(before["pending_block_n"], 19)

    def test_future_poison_cannot_be_parsed(self):
        rows = make_events(["WEAK", "WEAK"])
        cutoff = datetime.fromisoformat(rows[-1]["available"])
        poison = dict(rows[-1], signal=(cutoff + timedelta(days=1)).isoformat(),
                      available=(cutoff + timedelta(days=2)).isoformat(),
                      fp2=object(), stop_aware=object())
        one = confirmed_card(rows, "USDRUBF", as_of=cutoff)
        two = confirmed_card(rows + [poison], "USDRUBF", as_of=cutoff)
        self.assertEqual(one, two)

    def test_stale_outcomes_and_offline_feed(self):
        rows = make_events(["WEAK", "WEAK"])
        last = datetime.fromisoformat(rows[-1]["available"])
        old = confirmed_card(rows, "USDRUBF", as_of=last + timedelta(days=91))
        self.assertEqual(old["historical_observation"], "STALE_OR_MISSING_COMPLETED_OUTCOMES")
        self.assertEqual(old["live_current_status"], "LIVE_FEED_NOT_CONNECTED")
        recent = confirmed_card(rows, "USDRUBF", as_of=last,
                                latest_completed_m15=last, feed_connected=True)
        self.assertEqual(recent["live_current_status"], "CONFIRMED_OBSERVED_WEAK")
        not_fresh = confirmed_card(rows, "USDRUBF", as_of=last + timedelta(days=5),
                                   latest_completed_m15=last, feed_connected=True)
        self.assertEqual(not_fresh["live_current_status"], "LIVE_FEED_STALE")

    def test_conflicting_or_duplicate_unique_event_fails(self):
        rows = make_events(["WEAK"])
        with self.assertRaisesRegex(ValueError, "DUPLICATE_UNIQUE"):
            cohorts(rows + [dict(rows[0])], "USDRUBF", as_of=rows[-1]["available"])
        with self.assertRaisesRegex(ValueError, "M15_FUTURE"):
            confirmed_card(rows, "USDRUBF", as_of=rows[-1]["available"],
                           latest_completed_m15=datetime(2028, 1, 1))

    def test_mixed_breaks_confirmation(self):
        rows = make_events(["WEAK", "WEAK", "MIXED"])
        card = confirmed_card(rows, "USDRUBF", as_of=rows[-1]["available"])
        self.assertEqual(card["historical_observation"], "UNCONFIRMED_OR_TRANSITION")

    def test_published_real_2018_2026_counts(self):
        rows = load_published()
        names = ("MIX", "Si", "CNY", "CNYRUBF", "GLDRUBF", "IMOEXF", "USDRUBF")
        block_count = 0
        weak_runs = 0
        isolated = 0
        for name in names:
            blocks, pending, events = cohorts(rows, name, as_of=datetime(2026, 10, 22))
            block_count += len(blocks)
            seq = []
            for b in blocks:
                if b["kind"] != "WEAK":
                    if seq:
                        weak_runs += len(seq) >= 2
                        isolated += len(seq) == 1
                        seq = []
                else:
                    seq.append(b)
            if seq:
                weak_runs += len(seq) >= 2
                isolated += len(seq) == 1
        self.assertEqual((block_count, weak_runs, isolated), (197, 5, 33))

    def test_sha_tampering_fails_closed(self):
        self.assertTrue(SOURCE_PATH.exists())
        with self.assertRaisesRegex(ValueError, "SHA_MISMATCH"):
            load_published(expected_sha="0" * 64)


if __name__ == "__main__":
    unittest.main()
