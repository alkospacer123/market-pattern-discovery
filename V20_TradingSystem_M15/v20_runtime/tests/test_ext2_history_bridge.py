"""Offline-only historical prefix authority: R060 seed ↔ FINAM M15 overlap."""
from __future__ import annotations

from datetime import datetime, timedelta
from tempfile import TemporaryDirectory
from pathlib import Path
from hashlib import sha256
from unittest.mock import patch
import unittest
import pandas as pd

from V20_TradingSystem_M15.v20_runtime.ext2_history_bridge import (
    EXT2HistoryBlocked, load_r060_pinned_csv, load_finam_terminal_csv, stitch_verified_m15
)


def make_bars():
    rows = []
    for day in range(19):
        t = datetime(2026, 8, 3, 10) + timedelta(days=day)
        for i in range(32):
            now = t + timedelta(minutes=15*i)
            rows.append({
                "Datetime": now, "Open": 100 + day*.2,
                "High": 101 + day*.2, "Low": 99 + day*.2,
                "Close": 100 + day*.2, "Volume": 100+i,
            })
    return pd.DataFrame(rows)


class ReadonlyM15BridgeTests(unittest.TestCase):
    def test_overlap_matching_causal_join_and_wilder(self):
        full = make_bars()
        old = full.iloc[:18*32]
        new = full.iloc[17*32:]
        result = stitch_verified_m15(
            seed=old, finam_recent=new,
            signal_open_msk=full.Datetime.iloc[-1],
            observed_at_msk=full.Datetime.iloc[-1]+timedelta(minutes=15),
            verified_open_days=tuple(d.date() for d in full.Datetime.iloc[17*32::32]))
        self.assertEqual(len(result), len(full))
        self.assertTrue(result.Datetime.equals(full.Datetime))
        self.assertEqual(result.Close.iloc[-1], full.Close.iloc[-1])

    def test_gap_between_sources_blocks_without_invented_bars(self):
        full = make_bars()
        with self.assertRaisesRegex(EXT2HistoryBlocked,
                                    "EXT2_SEED_FINAM_OVERLAP_MISSING"):
            stitch_verified_m15(
                seed=full.iloc[:10*32], finam_recent=full.iloc[17*32:],
                signal_open_msk=full.Datetime.iloc[-1],
                observed_at_msk=full.Datetime.iloc[-1]+timedelta(minutes=15))

    def test_disagreeing_overlap_blocks_and_no_partial_m15(self):
        full = make_bars()
        old = full.iloc[:18*32]
        new = full.iloc[17*32:].copy()
        new.loc[new.index[0], "High"] += 1
        with self.assertRaisesRegex(EXT2HistoryBlocked,
                                    "EXT2_SEED_FINAM_OHLCV_DISAGREEMENT"):
            stitch_verified_m15(
                seed=old, finam_recent=new,
                signal_open_msk=full.Datetime.iloc[-1],
                observed_at_msk=full.Datetime.iloc[-1]+timedelta(minutes=15))
        with self.assertRaisesRegex(EXT2HistoryBlocked,
                                    "EXT2_SIGNAL_NOT_COMPLETED"):
            stitch_verified_m15(
                seed=old, finam_recent=full.iloc[17*32:],
                signal_open_msk=full.Datetime.iloc[-1],
                observed_at_msk=full.Datetime.iloc[-1]+timedelta(minutes=14))
        with self.assertRaisesRegex(EXT2HistoryBlocked,
                                    "EXT2_HISTORY_FUTURE_OR_SIGNAL_MISSING"):
            stitch_verified_m15(
                seed=old, finam_recent=full.iloc[17*32:-1],
                signal_open_msk=full.Datetime.iloc[-1],
                observed_at_msk=full.Datetime.iloc[-1]+timedelta(minutes=15))

    def test_previous_session_incomplete_blocks_candidate(self):
        full = make_bars()
        previous = full[full.Datetime.dt.normalize() ==
                        full.Datetime.iloc[-33].normalize()]
        broken = full.drop(previous.index[-5:]).reset_index(drop=True)
        old = broken.iloc[:17*32]
        new = broken.iloc[16*32:]
        with self.assertRaisesRegex(EXT2HistoryBlocked,
                                    "EXT2_PREVIOUS_D_SESSION_INCOMPLETE"):
            stitch_verified_m15(
                seed=old, finam_recent=new,
                signal_open_msk=broken.Datetime.iloc[-1],
                observed_at_msk=broken.Datetime.iloc[-1]+timedelta(minutes=15))


    def test_explicit_calendar_and_missing_recent_m15_fail_closed(self):
        full = make_bars()
        old = full.iloc[:18*32]
        new = full.iloc[17*32:]
        kwargs = dict(seed=old, finam_recent=new,
                      signal_open_msk=full.Datetime.iloc[-1],
                      observed_at_msk=full.Datetime.iloc[-1]+timedelta(minutes=15))
        with self.assertRaisesRegex(EXT2HistoryBlocked,
                                    "EXT2_VERIFIED_SESSION_CALENDAR_REQUIRED"):
            stitch_verified_m15(**kwargs)
        days = tuple(x.date() for x in full.Datetime.iloc[17*32::32])
        damaged = new.drop(new.index[-7])
        with self.assertRaisesRegex(EXT2HistoryBlocked,
                                    "EXT2_RECENT_SESSION_M15_MISSING"):
            stitch_verified_m15(**{**kwargs, "finam_recent": damaged},
                                verified_open_days=days)
        with self.assertRaisesRegex(EXT2HistoryBlocked,
                                    "EXT2_SIGNAL_SESSION_NOT_PROVEN"):
            stitch_verified_m15(**kwargs, verified_open_days=days[:1])

    def test_whole_missing_session_cannot_be_inferred_holiday(self):
        full = make_bars()
        seed = full.iloc[:17*32]
        new = full.iloc[16*32:]
        absent = full.Datetime.iloc[17*32].normalize()
        new = new.loc[~new.Datetime.dt.normalize().eq(absent)]
        days = tuple(x.date() for x in full.Datetime.iloc[16*32::32])
        with self.assertRaisesRegex(EXT2HistoryBlocked,
                                    "EXT2_RECENT_SESSION_M15_MISSING"):
            stitch_verified_m15(
                seed=seed, finam_recent=new,
                signal_open_msk=full.Datetime.iloc[-1],
                observed_at_msk=full.Datetime.iloc[-1]+timedelta(minutes=15),
                verified_open_days=days)

    def test_finam_terminal_msk_sha_and_schema_are_strict(self):
        with TemporaryDirectory() as tmp:
            p = Path(tmp) / "CNYRUBF.csv"
            p.write_text(
                "<DATE>;<TIME>;<OPEN>;<HIGH>;<LOW>;<CLOSE>;<VOL>\\n"
                "20260831;100000;12.895;12.897;12.891;12.895;1852\\n"
                "20260831;101500;12.896;12.898;12.892;12.895;1315\\n",
                encoding="utf-8"
            )
            digest = sha256(p.read_bytes()).hexdigest()
            d = load_finam_terminal_csv(p, expected_sha256=digest)
            self.assertEqual(list(d.columns), ["Datetime", "Open", "High", "Low", "Close", "Volume"])
            self.assertEqual(d.Datetime.iloc[0], datetime(2026, 8, 31, 10, 0))
            self.assertEqual(d.Datetime.iloc[1], datetime(2026, 8, 31, 10, 15))
            with self.assertRaisesRegex(EXT2HistoryBlocked, "EXT2_FINAM_SOURCE_SHA_MISMATCH"):
                load_finam_terminal_csv(p, expected_sha256="0" * 64)
            with self.assertRaisesRegex(EXT2HistoryBlocked, "EXT2_FINAM_SOURCE_SHA_REQUIRED"):
                load_finam_terminal_csv(p, expected_sha256="")
            p.write_text("<DATE>;<TIME>\\n20260831;100000\\n", encoding="utf-8")
            digest2 = sha256(p.read_bytes()).hexdigest()
            with self.assertRaisesRegex(EXT2HistoryBlocked, "EXT2_FINAM_SOURCE_INVALID"):
                load_finam_terminal_csv(p, expected_sha256=digest2)

    def test_seed_sha_and_symbol_are_mandatory(self):
        with TemporaryDirectory() as tmp:
            p = Path(tmp)/"USDRUBF_M15.csv"
            make_bars().assign(Ticker="USDRUBF").to_csv(p, sep=";", index=False)
            with self.assertRaisesRegex(EXT2HistoryBlocked, "EXT2_SEED_SHA_MISMATCH"):
                load_r060_pinned_csv(p, symbol="USDRUBF")
            with self.assertRaisesRegex(EXT2HistoryBlocked, "EXT2_SEED_SYMBOL_UNAPPROVED"):
                load_r060_pinned_csv(p, symbol="UNKNOWN")
            with self.assertRaisesRegex(EXT2HistoryBlocked, "EXT2_SEED_MISSING"):
                load_r060_pinned_csv(Path(tmp)/"absent.csv", symbol="USDRUBF")


if __name__ == "__main__":
    unittest.main()
