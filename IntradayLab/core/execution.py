"""One historical Open-only entry and resident Stop/Take execution model."""
from decimal import Decimal, ROUND_CEILING, ROUND_FLOOR


def entry_geometry(open_price, direction, stop, tick, target_r):
    # Only the scalar Open reaches this adapter. No entry H/L/C/Volume.
    if direction not in (-1, 1) or tick <= 0 or target_r <= 0:
        raise ValueError('INVALID_EXECUTION_PARAMETERS')
    if not open_price.is_finite() or open_price <= 0 or open_price % tick:
        return None
    risk = direction * (open_price-stop)
    if risk <= 0:
        return None
    raw = open_price + direction*target_r*risk
    take = (raw/tick).to_integral_value(
        rounding=ROUND_CEILING if direction == 1 else ROUND_FLOOR)*tick
    return risk, take


def at_open(open_price, direction, stop, deadline_due):
    if (open_price <= stop if direction == 1 else open_price >= stop):
        return open_price, 'STOP'
    return (open_price, 'SCHEDULED') if deadline_due else None


def in_bar(bar, direction, stop, take, allow_take):
    stop_hit = bar.low <= stop if direction == 1 else bar.high >= stop
    take_hit = bar.high >= take if direction == 1 else bar.low <= take
    if stop_hit:
        return stop, 'STOP', take_hit
    if take_hit and allow_take:
        return take, 'TAKE', False
    return None


def cost(entry_tick, exit_tick, ticks_per_side):
    return Decimal(ticks_per_side)*(entry_tick+exit_tick)
