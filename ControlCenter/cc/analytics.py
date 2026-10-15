"""Separate demo ledgers; no account aggregation API."""
from collections import defaultdict
from .models import Trade
from .freshness import MSK


def monthly(trades: tuple[Trade, ...] | None) -> list[dict]:
    if trades is None:
        return []
    totals = defaultdict(lambda: [0, 0., 0.])
    for trade in trades:
        # Group separately by scope even if a caller supplies mixed input.
        key = (trade.provenance.account_scope, trade.exit_at.astimezone(MSK).strftime('%Y-%m'))
        totals[key][0] += 1
        totals[key][1] += trade.net_pnl
        totals[key][2] += trade.commission
    return [{"Счёт DEMO": scope, "Месяц MSK": month, "Сделок": row[0],
             "Net PnL DEMO, ₽": row[1], "Комиссии DEMO, ₽": row[2]}
            for (scope, month), row in sorted(totals.items())]
