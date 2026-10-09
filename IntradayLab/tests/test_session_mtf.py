"""Synthetic causality and physical TRUE OOS read-boundary tests. No real CSVs."""
import io
from dataclasses import replace
from datetime import date, datetime, timedelta
from decimal import Decimal
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "tools"))
from session_mtf import (Bar, BlockedInterval, SessionWindow, TimestampEvidence,
                         aggregate, align_contexts, bounded_lines)
from audit_session_mtf import (IMOEXF_QUARANTINE, candidate_segments,
                               compare_labels, is_trading_date, read_prefix)

START = datetime(2024, 4, 26, 10)
PROOF = TimestampEvidence("Europe/Moscow", "start", ("synthetic contract",))
SESSION = SessionWindow(START, START + timedelta(hours=8), "synthetic-day",
                        START.date(), True, ("synthetic calendar",))


def data(minutes=15, count=36, start=START):
    m5 = [Bar(start + timedelta(minutes=5 * i), Decimal(100 + i),
              Decimal(110 + i), Decimal(90 + i), Decimal(101 + i), Decimal(i + 1))
          for i in range(count)]
    n = minutes // 5
    parents = [aggregate(m5[i:i + n], m5[i].timestamp) for i in range(0, count - n + 1, n)]
    return m5, parents


def aligned(m5, parents, minutes=15, **kwargs):
    return align_contexts(m5, parents, minutes, kwargs.pop("evidence", PROOF),
                          kwargs.pop("sessions", (SESSION,)), **kwargs)


class CausalityTests(unittest.TestCase):
    def test_all_timeframes_are_unavailable_before_close(self):
        for minutes in (15, 30, 60):
            with self.subTest(minutes=minutes):
                m5, parents = data(minutes)
                for i, decision in enumerate(aligned(m5, parents, minutes)):
                    self.assertEqual(decision.asof, m5[i].timestamp + timedelta(minutes=5))
                    if decision.asof < START + timedelta(minutes=minutes):
                        self.assertIsNone(decision.parent)
                    if decision.parent:
                        self.assertLessEqual(decision.parent.timestamp + timedelta(minutes=minutes), decision.asof)
                self.assertEqual(aligned(m5, parents, minutes)[minutes // 5 - 1].parent, parents[0])

    def test_no_m5_observation_at_1014(self):
        m5, parents = data()
        early = aligned(m5, parents, observed_at=START + timedelta(minutes=14))
        self.assertEqual(len(early), 2)
        self.assertTrue(all(d.parent is None for d in early))
        closed = aligned(m5, parents, observed_at=START + timedelta(minutes=15))
        self.assertEqual(closed[-1].parent, parents[0])

    def test_prefix_invariance_when_future_prices_are_mutated(self):
        for minutes in (15, 30, 60):
            m5, parents = data(minutes, 48)
            cutoff = START + timedelta(minutes=minutes * 2)
            prefix = [b for b in m5 if b.timestamp + timedelta(minutes=5) <= cutoff]
            known = [p for p in parents if p.timestamp + timedelta(minutes=minutes) <= cutoff]
            expected = aligned(prefix, known, minutes)
            future_m5 = [replace(b, high=b.high + 10000) if b.timestamp >= cutoff else b for b in m5]
            future_parents = [replace(b, volume=b.volume + 777) if b.timestamp >= cutoff else b for b in parents]
            self.assertEqual(aligned(future_m5, future_parents, minutes, observed_at=cutoff), expected)

    def test_end_labels_have_same_observation_times_and_prices(self):
        for minutes in (15, 30, 60):
            m5, parents = data(minutes)
            base_end = [replace(b, timestamp=b.timestamp + timedelta(minutes=5)) for b in m5]
            parent_end = [replace(b, timestamp=b.timestamp + timedelta(minutes=minutes)) for b in parents]
            out = aligned(base_end, parent_end, minutes,
                          evidence=replace(PROOF, label="end"))
            expected = aligned(m5, parents, minutes)
            self.assertEqual([(d.asof, d.reason, d.parent.ohlcv if d.parent else None) for d in out],
                             [(d.asof, d.reason, d.parent.ohlcv if d.parent else None) for d in expected])

    def test_every_ohlcv_field_checked(self):
        m5, parents = data()
        for field, change in (("open", 1), ("high", 1), ("low", -1), ("close", 1), ("volume", 1)):
            bad = replace(parents[0], **{field: getattr(parents[0], field) + change})
            decisions = aligned(m5, [bad, *parents[1:]])
            self.assertEqual(decisions[2].reason, "ohlcv_mismatch", field)
            self.assertIsNone(decisions[2].parent)

    def test_each_missing_child_blocks_composition(self):
        for minutes in (15, 30, 60):
            m5, parents = data(minutes)
            for i in range(minutes // 5):
                with self.subTest(minutes=minutes, missing_slot=i):
                    remaining = [b for j, b in enumerate(m5) if i != j]
                    decisions = aligned(remaining, parents, minutes)
                    target = next(d for d in decisions if d.asof == START + timedelta(minutes=minutes + 5))
                    self.assertEqual(target.reason, "missing_m5_or_stale_context")

    def test_context_invalidated_by_gap_then_recovers_on_fresh_complete_parent(self):
        m5, parents = data()
        m5 = [b for b in m5 if b.timestamp != START + timedelta(minutes=20)]
        decisions = {d.asof: d for d in aligned(m5, parents)}
        self.assertIsNotNone(decisions[START + timedelta(minutes=20)].parent)
        for t in (30, 35, 40):
            self.assertEqual(decisions[START + timedelta(minutes=t)].reason, "missing_m5_or_stale_context")
        self.assertEqual(decisions[START + timedelta(minutes=45)].parent, parents[2])

    def test_missing_latest_parent_never_falls_back(self):
        m5, parents = data()
        decisions = aligned(m5, [parents[0], *parents[2:]])
        self.assertEqual(decisions[5].reason, "missing_parent")
        self.assertIsNone(decisions[5].parent)

    def test_delayed_parent_not_used_early(self):
        m5, parents = data()
        parents[0] = replace(parents[0], available_at=START + timedelta(minutes=20))
        out = aligned(m5, parents)
        self.assertEqual(out[2].reason, "parent_not_observable")
        self.assertEqual(out[3].parent, parents[0])

    def test_delayed_child_blocks_parent(self):
        m5, parents = data()
        m5[0] = replace(m5[0], available_at=START + timedelta(minutes=20))
        out = aligned(m5, parents)
        self.assertEqual(out[2].reason, "m5_not_observable")
        self.assertIsNotNone(out[3].parent)

    def test_unconfirmed_timestamp_never_admitted(self):
        m5, parents = data()
        for evidence in (TimestampEvidence(), replace(PROOF, sources=()),
                         replace(PROOF, timezone=None), replace(PROOF, label=None),
                         replace(PROOF, timezone="invalid/timezone")):
            out = aligned(m5, parents, evidence=evidence)
            self.assertTrue(all(d.parent is None and d.reason == "timestamp_unconfirmed" for d in out))

    def test_session_evidence_required(self):
        m5, parents = data()
        for sessions in ((), (replace(SESSION, confirmed=False),), (replace(SESSION, sources=()),)):
            out = aligned(m5, parents, sessions=sessions)
            self.assertTrue(all(d.parent is None and d.reason == "session_unconfirmed" for d in out))

    def test_clearing_boundary_resets_even_when_m5_is_contiguous(self):
        m5, parents = data()
        boundary = START + timedelta(minutes=20)
        windows = (replace(SESSION, end=boundary),
                   replace(SESSION, start=boundary, session_id="after-clearing"))
        out = aligned(m5, parents, sessions=windows)
        self.assertIsNotNone(out[3].parent)
        self.assertEqual(out[4].reason, "session_boundary")
        self.assertEqual(out[5].reason, "session_boundary")
        self.assertEqual(out[8].parent, parents[2])

    def test_parent_straddling_clearing_is_rejected(self):
        m5, parents = data()
        boundary = START + timedelta(minutes=10)
        windows = (replace(SESSION, end=boundary), replace(SESSION, start=boundary, session_id="second"))
        self.assertEqual(aligned(m5, parents, sessions=windows)[2].reason, "session_boundary")

    def test_next_calendar_day_cannot_carry_yesterday(self):
        m5, parents = data()
        tomorrow, _ = data(start=START + timedelta(days=1), count=1)
        new_session = replace(SESSION, start=SESSION.start + timedelta(days=1), end=SESSION.end + timedelta(days=1),
                              trading_day=START.date() + timedelta(days=1), session_id="next-day")
        self.assertIsNone(aligned([*m5, *tomorrow], parents, sessions=(SESSION, new_session))[-1].parent)

    def test_quarantine_blocks_overlap_and_carried_context(self):
        m5, parents = data()
        q = BlockedInterval(START + timedelta(minutes=16), START + timedelta(minutes=20), "synthetic")
        out = aligned(m5, parents, quarantine=(q,))
        self.assertEqual(out[3].reason, "quarantine")
        self.assertEqual(out[5].reason, "quarantine")
        self.assertIsNotNone(out[8].parent)

    def test_known_imoexf_quarantine_applies_to_all_timeframes(self):
        start = datetime(2024, 8, 16, 18)
        window = replace(SESSION, start=start, end=datetime(2024, 8, 17), trading_day=start.date())
        for minutes in (15, 30, 60):
            m5, parents = data(minutes, count=60, start=start)
            m5 = [replace(b, symbol="IMOEXF") for b in m5]
            parents = [replace(b, symbol="IMOEXF") for b in parents]
            out = aligned(m5, parents, minutes, sessions=(window,))
            self.assertTrue(all(d.parent is None for d in out if d.asof > IMOEXF_QUARANTINE.start))

    def test_midnight_resets_explicit_calendar_windows(self):
        start = datetime(2024, 4, 25, 23)
        m5, parents = data(15, 18, start)
        midnight = datetime(2024, 4, 26)
        windows = (replace(SESSION, start=start, end=midnight, trading_day=start.date()),
                   replace(SESSION, start=midnight, end=midnight + timedelta(hours=1), session_id="new-date"))
        out = aligned(m5, parents, sessions=windows)
        self.assertIsNotNone(next(d for d in out if d.asof == midnight).parent)
        self.assertEqual(next(d for d in out if d.asof == midnight + timedelta(minutes=5)).reason, "session_boundary")
        self.assertIsNotNone(next(d for d in out if d.asof == midnight + timedelta(minutes=15)).parent)
        with self.assertRaises(ValueError):
            aligned(m5, parents, sessions=(replace(windows[0], end=windows[1].end),))

    def test_parent_labels_shifted_against_children_are_blocked(self):
        m5, parents = data()
        shifted = [replace(b, timestamp=b.timestamp + timedelta(minutes=15)) for b in parents]
        out = aligned(m5, shifted)
        self.assertEqual(out[5].reason, "ohlcv_mismatch")

    def test_invalid_order_duplicates_grid_and_instrument_rejected(self):
        m5, parents = data()
        for bad in ([m5[1], m5[0]], [m5[0], m5[0]],
                    [replace(m5[0], timestamp=START + timedelta(minutes=1))],
                    [replace(m5[0], symbol="OTHER"), *m5[1:]]):
            with self.assertRaises(ValueError):
                aligned(bad, parents)
        with self.assertRaises(ValueError):
            aligned(m5, parents, minutes=10)
        with self.assertRaises(ValueError):
            aligned(m5, parents, sessions=(SESSION, SESSION))
        with self.assertRaises(ValueError):
            aligned(m5, parents, sessions=(replace(SESSION, trading_day=None),))
        with self.assertRaises(ValueError):
            aligned([replace(b, symbol=None) for b in m5], [replace(b, symbol=None) for b in parents])

    def test_label_diagnostic_does_not_attest_timezone(self):
        m5, parents = data()
        self.assertGreater(compare_labels(m5, parents, 15, "start")["complete_exact"], 0)
        self.assertFalse(TimestampEvidence().confirmed)


class HistoricalCalendarTests(unittest.TestCase):
    def test_exchange_holidays_and_holiday_trading(self):
        for day in (date(2023, 2, 23), date(2024, 5, 9), date(2024, 12, 31)):
            self.assertFalse(is_trading_date(day))
        for day in (date(2023, 1, 3), date(2023, 2, 24), date(2023, 11, 6),
                    date(2024, 1, 8), date(2024, 4, 29), date(2024, 12, 30)):
            self.assertTrue(is_trading_date(day))
        self.assertIsNone(is_trading_date(date(2022, 6, 1)))
        self.assertIsNone(is_trading_date(date(2025, 1, 3)))

    def test_working_saturdays_and_regular_weekends(self):
        for day in (date(2024, 4, 27), date(2024, 11, 2), date(2024, 12, 28)):
            self.assertTrue(is_trading_date(day))
        for day in (date(2024, 4, 28), date(2023, 4, 29)):
            self.assertFalse(is_trading_date(day))

    def test_dated_clearing_and_halt_candidate_boundaries(self):
        before = candidate_segments(date(2023, 3, 20))
        after = candidate_segments(date(2023, 3, 21))
        self.assertEqual(before[2][0].strftime("%H:%M"), "14:15")
        self.assertEqual(after[2][0].strftime("%H:%M"), "14:05")
        self.assertEqual(candidate_segments(date(2023, 9, 13))[0][0].strftime("%H:%M"), "13:30")
        self.assertEqual(candidate_segments(date(2024, 9, 19))[-1][0].strftime("%H:%M"), "19:50")
        nov = candidate_segments(date(2024, 11, 19))
        self.assertEqual(nov[2][1].strftime("%H:%M"), "16:18")
        self.assertEqual(nov[3][0].strftime("%H:%M"), "16:50")


class GuardRaw(io.RawIOBase):
    def __init__(self, content, limit):
        self.content, self.limit, self.position = content, limit, 0

    def read(self, size=-1):
        if size < 0 or self.position + size > self.limit:
            raise AssertionError("Attempted TRUE OOS read")
        chunk = self.content[self.position:self.position + size]
        self.position += len(chunk)
        return chunk


class GuardFile(io.FileIO):
    def __init__(self, path, limit):
        super().__init__(path, "r")
        self.limit = limit
        self.read_count = 0

    def read(self, size=-1):
        if size < 0 or self.tell() + size > self.limit:
            raise AssertionError("Attempted TRUE OOS read")
        self.read_count += 1
        return super().read(size)


class TrueOOSBoundaryTests(unittest.TestCase):
    def test_reader_never_requests_next_byte_including_blank_lines(self):
        for prefix in (b"a\n", b"\n\n\n", b"header\r\nrow\r\n", b"longline" * 400 + b"\n"):
            raw = GuardRaw(prefix + b"2025-01-01;SECRET_PRICE\n", len(prefix))
            self.assertEqual(b"".join(bounded_lines(raw, prefix.count(b"\n"))), prefix)
            self.assertEqual(raw.position, len(prefix))

    def test_large_prefix_chunk_boundary_never_reads_oos(self):
        prefix = b"row;2024-12-30;synthetic\n" * 70000
        raw = GuardRaw(prefix + b"2025-01-01;DO_NOT_READ\n", len(prefix))
        self.assertEqual(sum(len(line) for line in bounded_lines(raw, 70000)), len(prefix))
        self.assertEqual(raw.position, len(prefix))

    def test_zero_budget_does_not_read(self):
        raw = GuardRaw(b"2025;PROTECTED", 0)
        self.assertEqual(list(bounded_lines(raw, 0)), [])
        self.assertEqual(raw.position, 0)

    def test_buffered_stream_rejected(self):
        with self.assertRaises(TypeError):
            list(bounded_lines(io.BytesIO(b"row\n2025\n"), 1))

    def test_truncated_and_oversized_prefix_fail(self):
        with self.assertRaises(ValueError):
            list(bounded_lines(GuardRaw(b"row", 100), 1))
        with self.assertRaises(ValueError):
            list(bounded_lines(GuardRaw(b"x" * 100 + b"\n", 101), 1, max_line_bytes=10))

    def test_real_fileio_ingestion_stops_at_frozen_last_row(self):
        prefix = (b"Ticker;Datetime;Open;High;Low;Close;Volume\n"
                  b"USDRUBF;2024-12-30 23:40:00;100;110;90;101;1\n"
                  b"USDRUBF;2024-12-30 23:45:00;101;111;91;102;2\n")
        work = Path(__file__).resolve().parents[1] / "work"
        work.mkdir(exist_ok=True)
        with tempfile.TemporaryDirectory(dir=work) as folder:
            path = Path(folder) / "synthetic.csv"
            path.write_bytes(prefix + b"USDRUBF;2025-01-03 09:00:00;FORBIDDEN_PRICE;DO_NOT_PARSE\n")
            expected = {"rows": 2, "first": "2024-12-30 23:40:00", "last": "2024-12-30 23:45:00", "blob": "synthetic"}
            guard = GuardFile(path, len(prefix))
            with patch.object(Path, "open", return_value=guard):
                bars, stats = read_prefix(path, "USDRUBF", "M5", expected)
            self.assertEqual(len(bars), 2)
            self.assertEqual(stats["prefix_bytes_read"], len(prefix))
            self.assertEqual(stats["future_bytes_read"], 0)
            self.assertGreater(guard.read_count, 0)
            with self.assertRaises(ValueError):
                read_prefix(path, "USDRUBF", "M5", expected | {"last": "2025-01-03 09:00:00"})


if __name__ == "__main__":
    unittest.main()
