"""One historical Open-only entry and resident Stop/Take execution model."""
from decimal import Decimal, ROUND_CEILING, ROUND_FLOOR


def entry_geometry(open_price, direction, stop, tick, target_r, *,
                   target_mode='GROSS_R', cost_ticks_per_side=1):
    # Only the scalar Open reaches this adapter. No entry H/L/C/Volume.
    if direction not in (-1, 1) or tick <= 0 or target_r <= 0 or cost_ticks_per_side < 0:
        raise ValueError('INVALID_EXECUTION_PARAMETERS')
    if target_mode not in ('GROSS_R', 'FULL_NET_C1_R'):
        raise ValueError('INVALID_TARGET_MODE')
    if not open_price.is_finite() or open_price <= 0 or open_price % tick:
        return None
    risk = direction * (open_price-stop)
    if risk <= 0:
        return None
    distance = target_r*risk
    if target_mode == 'FULL_NET_C1_R':
        # A causal plan assumes the exit tick equals the observed entry tick.
        # The realized ledger still charges the actual dated exit tick.
        round_trip = Decimal(2)*tick*Decimal(cost_ticks_per_side)
        distance = target_r*(risk+round_trip)+round_trip
    raw = open_price + direction*distance
    take = (raw/tick).to_integral_value(
        rounding=ROUND_CEILING if direction == 1 else ROUND_FLOOR)*tick
    return risk, take


def entry_admission(open_price, direction, stop, tick, constraints):
    """Optional scalar-Open constraints; never receives a bar or future fields.

    Return generic reason codes; a caller may label its declared constraints.
    Open validity is checked by the common engine before this function.
    """
    reference = constraints.get('directional_reference')
    if reference is not None and direction*(open_price-Decimal(str(reference))) < Decimal(str(
            constraints.get('minimum_reference_ticks', 0)))*tick:
        return 'OPEN_REFERENCE_LIMIT'
    risk = direction*(open_price-stop)
    if risk <= 0:
        return 'INVALID_RISK'
    if risk < Decimal(str(constraints.get('minimum_risk_ticks', 0)))*tick:
        return 'RISK_BELOW_MINIMUM_TICKS'
    return None


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
