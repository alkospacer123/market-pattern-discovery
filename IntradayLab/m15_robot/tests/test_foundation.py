"""Offline parity boundaries: no H1 imports, no FINAM order path, no LIVE."""
import hashlib
import unittest
from datetime import datetime, timedelta
from decimal import Decimal
from pathlib import Path
from tempfile import gettempdir
from unittest.mock import patch
from zoneinfo import ZoneInfo

import pandas as pd

from IntradayLab.m15_robot import spec
from IntradayLab.m15_robot.feature_adapter import (
    M15Signal, consecutive_next_open_allowed, latest_completed_signal,
    latest_verified_finam_signal,
    validate_completed_history,
)
from IntradayLab.m15_robot.grid_risk import (
    ContractAuthority, TrailingState, initial_stop, project_stop,
    ratchet_after_survived_completed_bar, require_on_grid, size_r15,
)
from IntradayLab.m15_robot.account_boundary import (
    M15NotAuthorized, account_fingerprint, prohibit_real_order,
    validate_independent_binding,
)

MSK = ZoneInfo("Europe/Moscow")


def at(hour, minute=0):
    return datetime(2026, 10, 16, hour, minute, tzinfo=MSK)


def bar_frame(ts):
    return pd.DataFrame(
        {"Open": [100.0], "High": [102.0], "Low": [99.0], "Close": [101.0], "Volume": [200]},
        index=pd.DatetimeIndex([ts], name="close_at"),
    )


def sample_feature(t, side=1, published=None):
    return {
        "at": t, "Signal": side, "ATR": 1.25, "Close": 101.0,
        "H1AvailableAt": published or t,
        "PriorHigh": 100.0, "PriorLow": 102.0,
    }


def authority():
    return ContractAuthority(
        Decimal("1"), Decimal("10"), 1,
        Decimal("2000"), Decimal("2000"),
    )


class SelectionIdentity(unittest.TestCase):
    def test_selected_historical_build_and_r15(self):
        self.assertEqual(spec.RESEARCH_BUILD_ID, "T1_NEXT_OPEN_TRAIL_3p5")
        self.assertEqual(spec.ROBOT_ID, "T3_M15_T1_TRAIL35_N4_R15")
        self.assertEqual(spec.RISK_FRACTION, Decimal("0.015"))
        self.assertEqual(spec.MAX_NOMINAL_INITIAL_RISK, Decimal("0.06"))
        self.assertEqual(spec.INITIAL_STOP_ATR, Decimal("2"))
        self.assertEqual(spec.TRAILING_STOP_ATR, Decimal("3.5"))
        self.assertEqual(len(spec.INSTRUMENTS), 4)
        self.assertEqual(spec.EXECUTION_STATUS, "NOT_LIVE_AUTHORIZED")

    def test_next_open_adjacency_has_no_extra_bar_wait(self):
        self.assertTrue(consecutive_next_open_allowed(at(10, 15), at(10, 30)))
        self.assertFalse(consecutive_next_open_allowed(at(10, 15), at(10, 45)))
        self.assertFalse(consecutive_next_open_allowed(at(10, 15), at(10, 15)))


class SignalGate(unittest.TestCase):
    def test_rejects_future_candle(self):
        with self.assertRaisesRegex(ValueError, "INCOMPLETE"):
            validate_completed_history("USDRUBF", bar_frame(at(10, 30)), at(10, 15))

    def test_rejects_unobserved_account_or_non_n4(self):
        with self.assertRaisesRegex(ValueError, "NOT_N4"):
            validate_completed_history("BR", bar_frame(at(10, 15)), at(10, 15))

    def test_rejects_duplicated_close_labels(self):
        f = pd.concat([bar_frame(at(10, 15)), bar_frame(at(10, 15))])
        with self.assertRaisesRegex(ValueError, "NONMONOTONIC"):
            validate_completed_history("CNYRUBF", f, at(10, 15))

    def test_accepts_signal_at_first_t1_close(self):
        with patch("IntradayLab.t3_m15_t1_entry_retest_v1.primary.features",
                   return_value=[sample_feature(at(10, 0))]):
            s = latest_completed_signal("USDRUBF", bar_frame(at(10)), at(10))
        self.assertIsInstance(s, M15Signal)
        self.assertEqual(s.direction, "LONG")
        self.assertEqual(s.completed_at, at(10))
        self.assertEqual(s.signal_atr14, 1.25)

    def test_stale_completed_bar_does_not_repeat_signal(self):
        with patch("IntradayLab.t3_m15_t1_entry_retest_v1.primary.features",
                   return_value=[sample_feature(at(10, 0))]):
            self.assertIsNone(latest_completed_signal(
                "USDRUBF", bar_frame(at(10, 0)), at(10, 16)))

    def test_rejects_nonfinite_bar_volume(self):
        bad = bar_frame(at(10, 15))
        bad.loc[:, "Volume"] = float("inf")
        with self.assertRaisesRegex(ValueError, "NONFINITE"):
            validate_completed_history("USDRUBF", bad, at(10, 15))

    def test_rejects_entry_signal_at_1800(self):
        with patch("IntradayLab.t3_m15_t1_entry_retest_v1.primary.features",
                   return_value=[sample_feature(at(18))]):
            self.assertIsNone(latest_completed_signal("IMOEXF", bar_frame(at(18)), at(18)))

    def test_no_signal_inside_entry_window(self):
        with patch("IntradayLab.t3_m15_t1_entry_retest_v1.primary.features",
                   return_value=[sample_feature(at(11), side=0)]):
            self.assertIsNone(latest_completed_signal("USDRUBF", bar_frame(at(11)), at(11)))

    def test_missing_h1_publication_fails_closed(self):
        with patch("IntradayLab.t3_m15_t1_entry_retest_v1.primary.features",
                   return_value=[sample_feature(at(10), published=at(10, 15))]):
            with self.assertRaisesRegex(ValueError, "H1_LOOKAHEAD"):
                latest_completed_signal("GLDRUBF", bar_frame(at(10)), at(10))

    def test_same_completed_signal_has_deterministic_id(self):
        with patch("IntradayLab.t3_m15_t1_entry_retest_v1.primary.features",
                   return_value=[sample_feature(at(10, 15), side=-1)]):
            a = latest_completed_signal("CNYRUBF", bar_frame(at(10, 15)), at(10, 15))
            b = latest_completed_signal("CNYRUBF", bar_frame(at(10, 15)), at(10, 15))
        self.assertEqual(a.signal_id, b.signal_id)
        self.assertEqual(a.direction, "SHORT")


    def test_same_m15_finam_jwt_verified_seam_generates_frozen_signal(self):
        from IntradayLab.m15_robot.finam_trading import M15FinamTradingAPI
        api = object.__new__(M15FinamTradingAPI)
        now = at(10, 15)
        seed = bar_frame(at(10))
        def row(opened):
            return {
                "timestamp": opened.isoformat(),
                "open": {"value": "100"}, "high": {"value": "102"},
                "low": {"value": "99"}, "close": {"value": "101"},
                "volume": {"value": "200"},
            }
        schedule = {"sessions": [{"type": "CORE_TRADING", "interval": {
            "start_time": at(9).isoformat(), "end_time": at(12).isoformat(),
        }}]}
        raw = {"symbol": "CNYRUBF@RTSX",
               "bars": [row(at(9,45)), row(at(10)), row(at(10,15))]}
        params = dict(
            api=api, m15_account_id="M15-FAKE", instrument="CNYRUBF",
            authenticated_seed=seed, observed_at=now,
            interval_start=at(9,45).isoformat(),
            interval_end=at(10,30).isoformat(),
            verified_open_labels=True,
        )
        from IntradayLab.m15_robot.continuation import M15HistoryContinuityError
        with (patch.object(M15FinamTradingAPI, "account", return_value={
                   "account_id": "M15-FAKE", "status": "ACCOUNT_ACTIVE"}) as account,
              patch.object(M15FinamTradingAPI, "schedule", return_value=schedule) as session,
              patch.object(M15FinamTradingAPI, "bars_m15", return_value=raw) as bars,
              patch("IntradayLab.t3_m15_t1_entry_retest_v1.primary.features",
                    return_value=[sample_feature(now)]) as features):
            signal = latest_verified_finam_signal(**params)
            self.assertIsInstance(signal, M15Signal)
            self.assertEqual(signal.completed_at, now)
            self.assertEqual(signal.instrument, "CNYRUBF")
            self.assertEqual(signal.direction, "LONG")
            self.assertEqual(len(features.call_args.args[0]), 2)
            account.assert_called_once_with("M15-FAKE")
            session.assert_called_once_with("CNYRUBF@RTSX")
            bars.assert_called_once()
            with self.assertRaisesRegex(ValueError, "OPEN_LABEL_PROOF_REQUIRED"):
                latest_verified_finam_signal(**dict(params, verified_open_labels=False))
            with self.assertRaisesRegex(M15HistoryContinuityError,
                                        "IMMUTABLE_HISTORY_CHANGED"):
                bad = seed.copy()
                bad.loc[:, "Close"] = 100.5
                latest_verified_finam_signal(**dict(params, authenticated_seed=bad))

class RiskPortFromH1(unittest.TestCase):
    def test_stop_outward_grid_projection(self):
        self.assertEqual(project_stop("LONG", Decimal("95.8"), Decimal("0.5")), Decimal("95.5"))
        self.assertEqual(project_stop("SHORT", Decimal("104.2"), Decimal("0.5")), Decimal("104.5"))
        self.assertEqual(initial_stop("LONG", Decimal("100"), Decimal("2.1"), Decimal("0.5")), Decimal("95.5"))
        self.assertEqual(initial_stop("SHORT", Decimal("100"), Decimal("2.1"), Decimal("0.5")), Decimal("104.5"))

    def test_entry_requires_exact_tick_grid(self):
        with self.assertRaisesRegex(ValueError, "GRID"):
            require_on_grid(Decimal("100.3"), Decimal("0.5"))

    def test_r15_and_margin_cap(self):
        s = size_r15(
            realized_equity=Decimal("100000"), entry=Decimal("100"), stop=Decimal("95"),
            contract=authority(), direction="LONG", available_margin_cash=Decimal("100000"),
        )
        self.assertEqual(s.risk_budget, Decimal("1500"))
        self.assertEqual(s.by_risk, 30)
        self.assertEqual(s.by_margin, 50)
        self.assertEqual(s.final_quantity, 30)
        self.assertEqual(s.initial_nominal_risk, Decimal("1500"))

    def test_funds_limit_below_r15(self):
        # A SHORT stop must be ABOVE its entry; never weaken the risk guard.
        with self.assertRaisesRegex(ValueError, "M15_STOP_WRONG_SIDE"):
            size_r15(
                realized_equity=Decimal("100000"), entry=Decimal("100"), stop=Decimal("95"),
                contract=authority(), direction="SHORT", available_margin_cash=Decimal("3999"),
            )
        s = size_r15(
            realized_equity=Decimal("100000"), entry=Decimal("100"), stop=Decimal("105"),
            contract=authority(), direction="SHORT", available_margin_cash=Decimal("3999"),
        )
        self.assertEqual(s.risk_budget, Decimal("1500"))
        self.assertEqual(s.by_risk, 30)
        self.assertEqual(s.by_margin, 1)
        self.assertEqual(s.final_quantity, 1)
        self.assertEqual(s.reason, "OK")

    def test_aggregate_budget_fails_closed(self):
        s = size_r15(
            realized_equity=Decimal("100000"), entry=Decimal("100"), stop=Decimal("95"),
            contract=authority(), direction="LONG", available_margin_cash=Decimal("100000"),
            already_committed_initial_risk=Decimal("6000"),
        )
        self.assertEqual(s.final_quantity, 0)
        self.assertEqual(s.reason, "ZERO_RISK_OR_MARGIN_CAPACITY")

    def test_partial_aggregate_budget(self):
        s = size_r15(
            realized_equity=Decimal("100000"), entry=Decimal("100"), stop=Decimal("95"),
            contract=authority(), direction="LONG", available_margin_cash=Decimal("100000"),
            already_committed_initial_risk=Decimal("5300"),
        )
        self.assertEqual(s.risk_budget, Decimal("700"))
        self.assertEqual(s.final_quantity, 14)

    def test_zero_quantity_is_not_promoted(self):
        s = size_r15(
            realized_equity=Decimal("1000"), entry=Decimal("100"), stop=Decimal("95"),
            contract=authority(), direction="LONG", available_margin_cash=Decimal("999"),
        )
        self.assertEqual(s.final_quantity, 0)

    def test_trailing_tightens_after_survived_bar_only(self):
        p = TrailingState("USDRUBF", "LONG", Decimal("100"), Decimal("96"), Decimal("100"))
        a = ratchet_after_survived_completed_bar(
            p, completed_at=at(10, 30), high=Decimal("115"), low=Decimal("100"),
            atr=Decimal("2"), price_step=Decimal("1"),
        )
        self.assertEqual(a.active_stop, Decimal("108"))
        b = ratchet_after_survived_completed_bar(
            a, completed_at=at(10, 45), high=Decimal("113"), low=Decimal("109"),
            atr=Decimal("4"), price_step=Decimal("1"),
        )
        self.assertEqual(b.active_stop, Decimal("108"))
        with self.assertRaisesRegex(ValueError, "REPLAY_OR_OUT_OF_ORDER"):
            ratchet_after_survived_completed_bar(
                a, completed_at=at(10, 30), high=Decimal("115"), low=Decimal("100"),
                atr=Decimal("2"), price_step=Decimal("1"),
            )


class IndependentAccounts(unittest.TestCase):
    def test_identity_rejects_shared_h1_account(self):
        h = account_fingerprint("H1-ACCOUNT")
        with self.assertRaisesRegex(ValueError, "REUSE"):
            validate_independent_binding(
                m15_account_id="H1-ACCOUNT", h1_account_sha256=h,
                m15_runtime_root=Path(gettempdir()) / "intraday_m15",
                h1_runtime_root=Path(gettempdir()) / "tradingsystem_h1",
                repository_root=Path(gettempdir()) / "m15_repo",
            )

    def test_separate_account_and_state_can_be_proven(self):
        h = account_fingerprint("H1-ACCOUNT")
        v = validate_independent_binding(
            m15_account_id="M15-ACCOUNT", h1_account_sha256=h,
            m15_runtime_root=Path(gettempdir()) / "intraday_m15",
            h1_runtime_root=Path(gettempdir()) / "tradingsystem_h1",
            repository_root=Path(gettempdir()) / "m15_repo",
        )
        self.assertNotEqual(v, h)

    def test_rejects_nested_h1_runtime_path(self):
        with self.assertRaisesRegex(ValueError, "OVERLAP"):
            validate_independent_binding(
                m15_account_id="M15-ACCOUNT", h1_account_sha256=account_fingerprint("H1-ACCOUNT"),
                m15_runtime_root=Path(gettempdir()) / "trading_h1" / "m15",
                h1_runtime_root=Path(gettempdir()) / "trading_h1",
                repository_root=Path(gettempdir()) / "m15_repo",
            )

    def test_no_real_order_surface(self):
        with self.assertRaises(M15NotAuthorized):
            prohibit_real_order({"order": "BUY"})


if __name__ == "__main__":
    unittest.main()
