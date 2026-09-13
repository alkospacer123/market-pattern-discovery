from __future__ import annotations
from dataclasses import dataclass, field
import math

from .prices import adverse_fill, align_price, price_to_ticks


def allocate_contracts(initial_qty: int) -> tuple[int, int, int]:
    """Floor 50% and 30%; the final leg receives the deterministic remainder."""
    if initial_qty < 0 or int(initial_qty) != initial_qty:
        raise ValueError("initial_qty must be a non-negative integer")
    q1, q2 = math.floor(initial_qty * .5), math.floor(initial_qty * .3)
    return q1, q2, initial_qty - q1 - q2


@dataclass
class Position:
    direction: str
    entry: float
    initial_stop: float
    contracts: int
    remaining_fraction: float = 1.0
    stop: float = field(init=False)
    next_target: int = 0
    realized_r: float = 0.0
    closed: bool = False
    remaining_contracts: int = field(init=False)
    gross_pnl: float = 0.0
    net_pnl: float = 0.0
    commissions: float = 0.0

    def __post_init__(self):
        self.stop = self.initial_stop
        self.remaining_contracts = self.contracts

    @property
    def risk(self) -> float:
        return abs(self.entry - self.initial_stop)

    def target_price(self, multiple: float, tick_size: float | None = None) -> float:
        raw = self.entry + self.risk * multiple * (1 if self.direction == "LONG" else -1)
        return align_price(raw, tick_size) if tick_size else raw


class BaselineExitManager:
    """Conservative OHLC executor.

    The active stop is checked before targets. Stop moves caused by a target
    never become eligible until the next bar, preventing invented intrabar
    ordering. Gaps fill from the adverse open, never at the crossed stop.
    """
    def __init__(self, levels=(1., 2., 3.), fractions=(.5, .3, .2), policy="STOP_FIRST",
                 tick_size: float = .01, tick_value_per_contract: float = 1.,
                 commission_per_contract: float = 0., slippage_ticks: float = 0.,
                 lower_tf_available: bool = False, allow_lower_tf_fallback: bool = False):
        if len(levels) != len(fractions) or abs(sum(fractions) - 1) > 1e-9:
            raise ValueError("Exit levels/fractions must align and fractions sum to one")
        normalized = policy.lower()
        if normalized == "lower_tf" and not lower_tf_available:
            if not allow_lower_tf_fallback:
                raise ValueError("intrabar_policy=lower_tf requires lower-timeframe data")
            normalized = "stop_first"
        if normalized not in {"stop_first"}:
            raise ValueError("unknown intrabar policy")
        self.levels, self.fractions, self.policy = tuple(levels), tuple(fractions), normalized
        self.tick_size, self.tick_value = tick_size, tick_value_per_contract
        self.commission, self.slippage_ticks = commission_per_contract, slippage_ticks

    def _fill(self, p: Position, event: str, base: float, qty: int) -> dict:
        side = "SELL" if p.direction == "LONG" else "BUY"
        price = adverse_fill(base, side, self.slippage_ticks, self.tick_size)
        signed = (price - p.entry) * (1 if p.direction == "LONG" else -1)
        gross = signed / self.tick_size * self.tick_value * qty
        fee = self.commission * qty
        p.gross_pnl += gross; p.commissions += fee; p.net_pnl += gross - fee
        initial_r_cash = p.risk / self.tick_size * self.tick_value * p.contracts
        p.realized_r = p.gross_pnl / initial_r_cash if initial_r_cash else 0.
        return {"event": event, "price": price, "quantity": qty,
                "fraction": qty / p.contracts if p.contracts else 0., "commission": fee}

    def process(self, position: Position, high: float, low: float, open_price: float | None = None) -> list[dict]:
        if position.closed: return []
        open_price = position.entry if open_price is None else open_price
        # Validated market prices are on-grid. Nearest conversion also absorbs
        # harmless binary-float residue from synthetic arithmetic in tests.
        high_tick, low_tick = price_to_ticks(high, self.tick_size), price_to_ticks(low, self.tick_size)
        # Stop crossing uses the actual OHLC inequality (off-grid synthetic
        # values must not be rounded into a false touch).
        stop_hit = low <= position.stop if position.direction == "LONG" else high >= position.stop
        target = position.target_price(self.levels[position.next_target], self.tick_size) if position.next_target < len(self.levels) else None
        target_tick = price_to_ticks(target, self.tick_size) if target is not None else None
        target_hit = target is not None and (high_tick >= target_tick if position.direction == "LONG" else low_tick <= target_tick)
        if stop_hit:  # STOP_FIRST for every ambiguous combination.
            gap = open_price < position.stop if position.direction == "LONG" else open_price > position.stop
            base = open_price if gap else position.stop
            event = self._fill(position, "STOP", base, position.remaining_contracts)
            position.remaining_contracts = 0; position.remaining_fraction = 0.; position.closed = True
            return [event]
        if not target_hit: return []
        allocations = allocate_contracts(position.contracts)
        events = []
        # Multiple targets may occur in an unambiguous no-stop bar.
        while position.next_target < len(self.levels):
            i = position.next_target
            target = position.target_price(self.levels[i], self.tick_size)
            target_tick = price_to_ticks(target, self.tick_size)
            hit = high_tick >= target_tick if position.direction == "LONG" else low_tick <= target_tick
            if not hit: break
            qty = allocations[i] if i < 2 else position.remaining_contracts
            if qty:
                events.append(self._fill(position, f"TP{i+1}", target, qty))
                position.remaining_contracts -= qty
            position.next_target += 1
            if position.next_target == 1: position.stop = align_price(position.entry, self.tick_size)
            elif position.next_target == 2: position.stop = position.target_price(1., self.tick_size)
            elif position.next_target == len(self.levels): position.closed = True
        position.remaining_fraction = position.remaining_contracts / position.contracts if position.contracts else 0.
        return events

    def charge_entry(self, position: Position) -> float:
        fee = self.commission * position.contracts
        position.commissions += fee; position.net_pnl -= fee
        return fee

    def r_metrics(self, position: Position) -> dict[str, float]:
        initial_r_cash = position.risk / self.tick_size * self.tick_value * position.contracts
        return {"gross_R": position.gross_pnl / initial_r_cash if initial_r_cash else 0.,
                "net_R": position.net_pnl / initial_r_cash if initial_r_cash else 0.}
