"""Only the 14 exact FINAM historical missing M15 labels may be tolerated.

No artificial OHLCV, no new live permissions, no broker access.
"""
from datetime import date, datetime, timedelta
from unittest import TestCase, main
import pandas as pd

from V20_TradingSystem_M15.v20_runtime.ext2_history_bridge import (
    EXT2HistoryBlocked, _require_continuous_trading_sessions,
)
from V20_TradingSystem_M15.v20_runtime.r088_finam_historical_gaps import (
    accepted_historical_missing_m15, OFFICIAL_FINAM_REEXPORT_SHA256,
)


def rows(*days):
    stamps = [datetime.combine(day, datetime.min.time()) +
              timedelta(hours=10, minutes=15*i)
              for day in days for i in range(32)]
    return pd.DataFrame({"Datetime": pd.to_datetime(stamps)})


class R088HistoricalGapsTests(TestCase):
    def test_exact_usd_nov1_gap_only(self):
        days = (date(2026, 11, 1), date(2026, 11, 2))
        original = rows(*days)
        observed = original.loc[
            original.Datetime != pd.Timestamp("2026-11-01 10:45:00")].reset_index(drop=True)
        args = dict(bars=observed, from_msk=datetime(2026, 11, 1, 10),
                    signal_open_msk=datetime(2026, 11, 2, 17, 45),
                    verified_open_days=days, symbol="USDRUBF")
        with self.assertRaisesRegex(EXT2HistoryBlocked, "EXT2_RECENT_SESSION_M15_MISSING"):
            _require_continuous_trading_sessions(**args)
        _require_continuous_trading_sessions(
            **args, accepted_historical_gaps=accepted_historical_missing_m15("USDRUBF"))
        with self.assertRaisesRegex(EXT2HistoryBlocked, "R088_HISTORICAL_GAP_SCOPE_NOT_PINNED"):
            _require_continuous_trading_sessions(
                **args, accepted_historical_gaps=accepted_historical_missing_m15("GLDRUBF"))
        # A fresh missing bar is never forgiven just because *some* historical
        # absence was accepted.
        lost = observed.loc[
            observed.Datetime != pd.Timestamp("2026-11-02 11:30:00")].reset_index(drop=True)
        with self.assertRaisesRegex(EXT2HistoryBlocked, "EXT2_RECENT_SESSION_M15_MISSING"):
            _require_continuous_trading_sessions(
                **{**args, "bars": lost},
                accepted_historical_gaps=accepted_historical_missing_m15("USDRUBF"))
    
    def test_exact_gld_earliest_gap_preserves_no_synthetic_m15(self):
        days = (date(2026, 9, 27), date(2026, 9, 28))
        original = rows(*days)
        removed = {pd.Timestamp("2026-09-27 10:00:00"),
                   pd.Timestamp("2026-09-27 10:30:00")}
        observed = original.loc[~original.Datetime.isin(removed)].reset_index(drop=True)
        _require_continuous_trading_sessions(
            bars=observed, from_msk=datetime(2026, 9, 27, 10),
            signal_open_msk=datetime(2026, 9, 28, 17, 45),
            verified_open_days=days, symbol="GLDRUBF",
            accepted_historical_gaps=accepted_historical_missing_m15("GLDRUBF"))
        self.assertEqual(len(observed), len(original)-2)
        self.assertTrue(not observed.Datetime.isin(removed).any())

    def test_no_future_approval_and_pinned_shas(self):
        self.assertEqual(len(accepted_historical_missing_m15("USDRUBF")), 10)
        self.assertEqual(len(accepted_historical_missing_m15("GLDRUBF")), 4)
        self.assertFalse(accepted_historical_missing_m15("CNYRUBF"))
        self.assertEqual(set(OFFICIAL_FINAM_REEXPORT_SHA256),
                         {"USDRUBF","GLDRUBF","CNYRUBF","IMOEXF"})
        self.assertTrue(all(len(value)==64 for value in
                            OFFICIAL_FINAM_REEXPORT_SHA256.values()))


if __name__ == "__main__":
    main()
