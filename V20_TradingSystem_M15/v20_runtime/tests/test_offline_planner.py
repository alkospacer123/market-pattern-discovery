"""Focused new-code tests only. No FINAM credentials, orders, tasks or H1 writes."""
import unittest
from datetime import datetime, timedelta
from decimal import Decimal

from V20_TradingSystem_M15.v20_runtime.offline_planner import (
    OfflinePlanner, FrozenSignal, LIVE_ENABLED,
)

T = datetime(2026, 10, 21, 10, 0)


def plan(p, strategy, symbol, *, at=T + timedelta(minutes=15),
         signal_at=T, side=1, atr="0.013", margin="10000",
         available="150000", equity="500000", costs="50"):
    return p.reference_next_open(
        FrozenSignal(strategy, symbol, side, signal_at, Decimal(atr)),
        at=at, entry_open="10.00", realized_equity=equity,
        price_step="0.01", tick_value="100",
        initial_margin=margin, available_cash=available,
        trade_lot_size=1, cost_buffer_per_contract=costs,
    )


class OfflineEntryTests(unittest.TestCase):
    def test_default_denies_live(self):
        self.assertIs(LIVE_ENABLED, False)

    def test_reuses_h1_tick_grid_long(self):
        p = OfflinePlanner("SHALLOW_PULLBACK")
        x = plan(p, "SHALLOW_PULLBACK", "CNYRUBF")
        self.assertEqual(x.initial_stop, Decimal("9.97"))
        self.assertEqual(x.reference_stop_risk, Decimal("0.03"))
        # 7500/(300 stop RUB + 50 conservatively reserved costs) -> 21.
        # But GO limits to 150000/10000 -> 15.
        self.assertEqual(x.quantity, 15)
        self.assertEqual(x.margin_required, Decimal("150000"))
        self.assertEqual(x.mode, "OFFLINE_REFERENCE_NOT_ORDER")

    def test_h1_short_outward_grid(self):
        p = OfflinePlanner("OBV_PRESSURE")
        x = plan(p, "OBV_PRESSURE", "USDRUBF", side=-1)
        self.assertEqual(x.direction, "SHORT")
        self.assertEqual(x.initial_stop, Decimal("10.03"))
        self.assertEqual(x.quantity, 15)

    def test_risk_plus_fees_can_reduce_quantity(self):
        p = OfflinePlanner("INSIDE_DAY_RELEASE")
        x = plan(p, "INSIDE_DAY_RELEASE", "IMOEXF",
                 available="999999", costs="200")
        self.assertEqual(x.quantity, 15)  # 7500/(300+200)
        self.assertLessEqual(
            Decimal(x.quantity) * Decimal("500"),
            x.cash_risk_cap,
        )

    def test_rejects_gap_in_next_open(self):
        p = OfflinePlanner("SHALLOW_PULLBACK")
        with self.assertRaisesRegex(ValueError, "NOT_IMMEDIATE_NEXT_OPEN"):
            plan(p, "SHALLOW_PULLBACK", "USDRUBF", at=T + timedelta(minutes=30))

    def test_rejects_strategy_leak_between_accounts(self):
        p = OfflinePlanner("SHALLOW_PULLBACK")
        with self.assertRaisesRegex(ValueError, "ACCOUNT_STRATEGY_OR_SYMBOL_MISMATCH"):
            plan(p, "OBV_PRESSURE", "USDRUBF")

    def test_enforces_symbol_and_session_caps(self):
        p = OfflinePlanner("SHALLOW_PULLBACK")
        plan(p, "SHALLOW_PULLBACK", "USDRUBF")
        with self.assertRaisesRegex(ValueError, "ONE_OPEN_POSITION"):
            plan(p, "SHALLOW_PULLBACK", "USDRUBF")
        p.mark_flat("USDRUBF")
        with self.assertRaisesRegex(ValueError, "ONE_NEW_ENTRY"):
            plan(p, "SHALLOW_PULLBACK", "USDRUBF")
        plan(p, "SHALLOW_PULLBACK", "CNYRUBF")
        with self.assertRaisesRegex(ValueError, "TWO_NEW_ENTRIES"):
            plan(p, "SHALLOW_PULLBACK", "GLDRUBF")

    def test_accounts_do_not_block_each_other(self):
        p = OfflinePlanner("SHALLOW_PULLBACK")
        q = OfflinePlanner("OBV_PRESSURE")
        self.assertEqual(plan(p, "SHALLOW_PULLBACK", "CNYRUBF").quantity, 15)
        self.assertEqual(plan(q, "OBV_PRESSURE", "CNYRUBF").quantity, 15)

    def test_insufficient_margin_fails_closed(self):
        p = OfflinePlanner("SHALLOW_PULLBACK")
        with self.assertRaisesRegex(ValueError, "INSUFFICIENT_RISK_OR_MARGIN_CAPACITY"):
            plan(p, "SHALLOW_PULLBACK", "USDRUBF", available="1")

    def test_bad_grid_fails_closed(self):
        p = OfflinePlanner("SHALLOW_PULLBACK")
        with self.assertRaises(ValueError):
            p.reference_next_open(
                FrozenSignal("SHALLOW_PULLBACK", "USDRUBF", 1, T, Decimal("0.013")),
                at=T + timedelta(minutes=15), entry_open="10.001",
                realized_equity=500000, price_step="0.01",
                tick_value=100, initial_margin=10000,
                available_cash=150000, trade_lot_size=1,
                cost_buffer_per_contract=50,
            )

    def test_next_session_reopens_after_flat(self):
        p = OfflinePlanner("SHALLOW_PULLBACK")
        plan(p, "SHALLOW_PULLBACK", "USDRUBF")
        p.mark_flat("USDRUBF")
        nxt = T + timedelta(days=1)
        x = plan(p, "SHALLOW_PULLBACK", "USDRUBF",
                 signal_at=nxt, at=nxt + timedelta(minutes=15))
        self.assertEqual(x.quantity, 15)


if __name__ == "__main__":
    unittest.main()
