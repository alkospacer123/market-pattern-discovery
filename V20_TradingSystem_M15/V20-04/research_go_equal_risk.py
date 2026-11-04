"""Offline-only N4 equity/GO-balanced admission research (2023-2026 YTD).

Keeps all frozen historical fills/exits fixed, like research_go_reservation.
Only changes integer quantity admitted to the existing reference trades.
GO is one dated owner snapshot, NOT historical directional margin; prospective
risks use the last fully completed frozen ATR14, not a future trade's ATR.
No FINAM connection, trading methods, local robots or LIVE file changes.
"""
from __future__ import annotations

from bisect import bisect_left
from collections import defaultdict
import math
import pandas as pd

from research_go_reservation import SYMS, CAPITAL_RISK


class CompletedBarRisk:
    """For a hypothetical future N4 position, use only the latest completed bar."""

    def __init__(self, prepared, rub_per_price, ticks_rub, ticks_price):
        self.points = {}
        for symbol in SYMS:
            frame = prepared[symbol]
            t = list(pd.to_datetime(frame.Datetime))
            v = []
            for atr in frame.atr:
                if pd.isna(atr) or not math.isfinite(float(atr)) or atr <= 0:
                    v.append(float("nan"))
                else:
                    # Outward grid estimate: a whole tick cannot be risk-free.
                    ticks = math.ceil((2.0 * float(atr)) / ticks_price[symbol] - 1e-9)
                    v.append(max(1, ticks) * ticks_rub[symbol] + 2*ticks_rub[symbol])
            self.points[symbol] = (t, v)

    def risk(self, symbol, at):
        t, values = self.points[symbol]
        # Bar's Open timestamp labels its 15-minute interval; it is only
        # completed at timestamp+15m. Do not look into the entry bar.
        k = bisect_left(t, pd.Timestamp(at)) - 1
        return values[k] if k >= 0 and math.isfinite(values[k]) else None


def balanced_integer_plan(*, free_cash, instruments, stop_rub, go_rub,
                          equity, fee_rub):
    """One-lot floor for every eligible FLAT symbol, then fill the weakest risk.

    Quantities are integer; NO leverage and NO discretionary stop widening.
    The max-min greedy process consumes free GO when it can improve a symbol
    below its 1.5%-risk ceiling. This is a hypothetical plan, not an order.
    If even one lot per eligible symbol does not fit, return None.
    """
    limit = CAPITAL_RISK * equity
    valid = [s for s in instruments if
             s in stop_rub and stop_rub[s] is not None and
             math.isfinite(stop_rub[s]) and stop_rub[s] > 0 and
             stop_rub[s] <= limit + 1e-8]
    unit_cash = {s:go_rub[s]+fee_rub[s] for s in valid}
    if any(unit_cash[s] <= 0 for s in valid):
        raise ValueError("INVALID_GO_OR_COST")
    if sum(unit_cash.values()) > free_cash + 1e-8:
        return None
    q = {s:1 for s in valid}
    remaining = free_cash - sum(unit_cash.values())
    while True:
        feasible = [s for s in valid
                    if (q[s]+1)*stop_rub[s] <= limit+1e-8
                    and unit_cash[s] <= remaining+1e-8]
        if not feasible:
            break
        # Equalize actual RUB at risk, not allocation of GO or lot counts.
        s = min(feasible,key=lambda symbol:
                (q[symbol]*stop_rub[symbol],
                 (q[symbol]+1)*stop_rub[symbol],
                 SYMS.index(symbol)))
        q[s] += 1
        remaining -= unit_cash[s]
    assert remaining >= -1e-6
    assert sum(q[s]*unit_cash[s] for s in valid) <= free_cash+1e-6
    assert all(q[s]*stop_rub[s] <= limit+1e-6 for s in valid)
    return q


def compare_equal_risk(ledger, bank, go, rub_per_price, tick_rub, reference):
    assert bank > 0
    rows = list(ledger.itertuples(index=False))
    events = []
    for i,t in enumerate(rows):
        entry = pd.Timestamp(t.entry_time); exit_ = pd.Timestamp(t.exit_time)
        assert exit_ >= entry
        events.append((entry,1,SYMS.index(t.symbol),i,True))
        events.append((exit_,2 if exit_ == entry else 0,SYMS.index(t.symbol),i,False))
    events.sort()
    active = {}
    risk_skips = go_skips = fallback_half = risk_proxies_missing = 0
    eligible_four = 0
    accepted = lots = 0
    gross_win = gross_loss = realized = 0.0
    year = defaultdict(lambda:[0.0,0.0,0])
    nav = [0.0]
    usage = []
    for time, _, _, i, opening in events:
        t = rows[i]; symbol = t.symbol
        if not opening:
            position = active.pop(i,None)
            if position is None:
                continue
            quantity, fee = position
            pnl = float(t.net_R)*abs(float(t.risk))*rub_per_price[symbol]*quantity
            realized += pnl
            if pnl > 0:
                gross_win += pnl;year[str(time.year)][0] += pnl
            elif pnl < 0:
                gross_loss -= pnl;year[str(time.year)][1] -= pnl
            year[str(time.year)][2] += 1
            nav.append(realized)
            continue
        fee_one = 2*tick_rub[symbol]
        risk_one = abs(float(t.risk))*rub_per_price[symbol] + fee_one
        risk_qty = math.floor((CAPITAL_RISK*bank)/risk_one + 1e-10)
        if risk_qty < 1:
            risk_skips+=1;continue
        occupied = {rows[j].symbol for j in active}
        assert symbol not in occupied
        used = sum(go[rows[j].symbol]*quantity + fee for j,(quantity,fee) in active.items())
        free = bank - used
        remaining_symbols = [s for s in SYMS if s not in occupied]
        projected = {s:(risk_one if s == symbol else reference.risk(s,time))
                     for s in remaining_symbols}
        if any(r is None for r in projected.values()):
            risk_proxies_missing += 1
        if all(projected.get(s) is not None and
               projected[s] <= CAPITAL_RISK*bank
               for s in remaining_symbols):
            eligible_four += 1
        fees = {s:2*tick_rub[s] for s in remaining_symbols}
        q_plan = balanced_integer_plan(
            free_cash=free, instruments=remaining_symbols,
            stop_rub=projected,go_rub=go,equity=bank,fee_rub=fees)
        if q_plan is None:
            # The requested four-way ability cannot be honored. Keep a
            # conservative 50% nominal position cap and label each fallback;
            # do not pretend this is equal-risk four-way balancing.
            fallback_half += 1
            qty = min(risk_qty,math.floor((min(free,bank/2) + 1e-8) /
                    (go[symbol] + fee_one)))
        else:
            qty = min(risk_qty,q_plan.get(symbol,0))
        if qty < 1:
            go_skips += 1
            continue
        cost = fee_one*qty
        assert used + qty*go[symbol]+cost <= bank + 1e-6
        active[i] = (qty,cost)
        accepted += 1;lots += qty
        usage.append((used + qty*go[symbol]+cost)/bank)
    assert not active
    assert accepted + risk_skips + go_skips == len(rows)
    peak = 0;maximum_dd = 0
    for x in nav:
        peak=max(peak,x);maximum_dd=max(maximum_dd,peak-x)
    return dict(bank=bank,method="equal_risk4",signals=len(rows),
        accepted=accepted,risk_skips=risk_skips,go_skips=go_skips,
        fallback_half_admissions=fallback_half,
        four_way_risk_eligible_observations=eligible_four,
        missing_reference_risk_observations=risk_proxies_missing,
        avg_lots=round(lots/accepted,3) if accepted else 0,
        max_cash_usage_pct=round(100*max(usage),2) if usage else 0,
        avg_cash_usage_pct=round(100*sum(usage)/len(usage),2) if usage else 0,
        net_rub=round(realized,2),
        pf_rub=round(gross_win/gross_loss,4) if gross_loss>0 else None,
        closed_dd_rub=round(maximum_dd,2),
        years={yr:{"closed":z[2],"net_rub":round(z[0]-z[1],2),
                   "pf_rub":round(z[0]/z[1],4) if z[1]>0 else None}
               for yr,z in sorted(year.items())})
