"""Research only: fixed-bank GO admission comparison on frozen 2023-2026 trades.

This is a cash-aware filter of the already accepted frozen trade ledger, NOT a
re-simulation of signals that would become eligible after a skipped order.
No broker, no live modules, no changed strategy/order/risk rules. Nominal GO
is the historical snapshot supplied in research_cap4, not a GO time series.
"""
from __future__ import annotations

from collections import defaultdict
import math

import pandas as pd

CAPITAL_RISK = 0.015
SYMS = ("CNYRUBF", "GLDRUBF", "IMOEXF", "USDRUBF")


def compare(ledger: pd.DataFrame, bank: int, method: str, go: dict,
            rub_per_price: dict, tick_rub: dict) -> dict:
    assert method in ("half", "n4")
    assert bank > 0 and set(go) == set(SYMS)
    events = []
    rows = list(ledger.itertuples(index=False))
    for i, t in enumerate(rows):
        entering = pd.Timestamp(t.entry_time)
        exiting = pd.Timestamp(t.exit_time)
        assert entering <= exiting
        # Previously opened exits release GO before a same-time entry; an
        # entry-bar stop is settled only after the entry attempt.
        events.append((entering, 1, SYMS.index(t.symbol), i, True))
        events.append((exiting, 2 if exiting == entering else 0,
                       SYMS.index(t.symbol), i, False))
    events.sort()
    active = {}
    equity_points = [0.0]
    profit, loss = 0.0, 0.0
    year_pnl = defaultdict(lambda: [0.0, 0.0, 0])
    stats = dict(signals=len(rows), accepted=0, risk_skips=0, go_skips=0,
                 gross_lots=0, max_open_positions=0,
                 max_used_go=0, max_broker_used_go_with_cost=0)
    realized = 0.0
    trades = []
    for at, _, _, i, opening in events:
        t = rows[i]
        symbol = t.symbol
        if not opening:
            held = active.pop(i, None)
            if held is None:
                continue
            qty, charge = held
            pnl = float(t.net_R) * abs(float(t.risk)) * rub_per_price[symbol] * qty
            realized += pnl
            if pnl > 0:
                profit += pnl
                year_pnl[str(at.year)][0] += pnl
            elif pnl < 0:
                loss -= pnl
                year_pnl[str(at.year)][1] -= pnl
            year_pnl[str(at.year)][2] += 1
            equity_points.append(realized)
            trades.append((i, symbol, qty, pnl))
            continue
        # Monetary stop risk includes a per-lot C1 fee/slippage buffer as
        # in the existing CAP4 risk diagnostic.
        stop_risk = abs(float(t.risk)) * rub_per_price[symbol]
        fee_cost = 2 * tick_rub[symbol]
        risk_per_lot = stop_risk + fee_cost
        risk_qty = math.floor((CAPITAL_RISK * bank) / risk_per_lot + 1e-10) if risk_per_lot > 0 else 0
        if risk_qty < 1:
            stats["risk_skips"] += 1
            continue
        used_go = sum(go[rows[j].symbol] * qty for j, (qty, _) in active.items())
        used_cost = sum(c for qty, c in active.values())
        available = bank - used_go - used_cost
        if method == "half":
            # One position can consume at most half the nominal bankroll in
            # GO. The next position can thus get its own half at entry.
            allowed_go = min(available, bank * 0.5)
        else:
            # Reserve one lot of every currently flat OTHER N4 instrument.
            occupied = {rows[j].symbol for j in active}
            assert symbol not in occupied, "FROZEN_REPLAY_SAME_SYMBOL_ALREADY_OPEN"
            reserve = sum(go[s] + 2 * tick_rub[s]
                          for s in SYMS if s != symbol and s not in occupied)
            allowed_go = available - reserve
        unit_need = go[symbol] + fee_cost
        margin_qty = math.floor((allowed_go + 1e-9) / unit_need)
        qty = min(risk_qty, margin_qty)
        if qty < 1:
            stats["go_skips"] += 1
            continue
        active[i] = (qty, fee_cost * qty)
        stats["accepted"] += 1
        stats["gross_lots"] += qty
        stats["max_open_positions"] = max(stats["max_open_positions"], len(active))
        stats["max_used_go"] = max(stats["max_used_go"], used_go + qty * go[symbol])
        stats["max_broker_used_go_with_cost"] = max(
            stats["max_broker_used_go_with_cost"],
            used_go + used_cost + qty * unit_need)
    assert stats["accepted"] == stats["signals"] - stats["risk_skips"] - stats["go_skips"]
    assert not active, "FROZEN_REPLAY_UNCLOSED_TRADE_IN_COMPARISON"
    assert all(math.isfinite(x) for x in (profit, loss, realized))
    peak = equity_points[0]
    max_dd = 0.0
    for value in equity_points:
        peak = max(peak, value)
        max_dd = max(max_dd, peak - value)
    stats.update(
        bank=bank, method=method,
        net_rub=round(realized, 2),
        pf_rub=round(profit / loss, 4) if loss > 0 else None,
        closed_dd_rub=round(max_dd, 2),
        avg_lots_per_accepted=round(stats["gross_lots"] / stats["accepted"], 3)
        if stats["accepted"] else 0,
        years={year: {"closed": z[2],
                      "net_rub": round(z[0] - z[1], 2),
                      "pf_rub": round(z[0] / z[1], 4) if z[1] > 0 else None}
               for year, z in sorted(year_pnl.items())}
    )
    return stats
