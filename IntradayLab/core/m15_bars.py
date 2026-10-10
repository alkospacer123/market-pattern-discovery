"""Exact M5 -> M15 observations, with a separately observed Open scalar.

Incomplete parents have NaN H/L/C and zero volume and cannot be observations.
Their first-child Open remains usable at the boundary without inventing a path.
"""
from datetime import timedelta
from decimal import Decimal
from .models import Bar

FIVE = timedelta(minutes=5)
FIFTEEN = timedelta(minutes=15)


def full_slots(window, step=FIFTEEN):
    a, z = window
    at = a.replace(minute=0, second=0, microsecond=0)
    while at < a:
        at += step
    while at + step <= z:
        yield at
        at += step


def aggregate_m15(rows, rules, start, end_exclusive):
    if any(b.duration != FIVE or at != b.start or at.tzinfo != rules.zone or
           at.second or at.microsecond or at.minute % 5 or at.date() >= end_exclusive
           for at, b in rows.items()):
        raise ValueError('M15_SOURCE_LABEL_DURATION_OR_FUTURE')
    parents, diagnostic = {}, []
    day = start
    while day < end_exclusive:
        for window in rules.windows(day):
            for at in full_slots(window):
                clocks = tuple(at+i*FIVE for i in range(3))
                children = [rows.get(t) for t in clocks]
                valid = all(b is not None and b.valid for b in children)
                first = children[0]
                rec = dict(start=at, closed_at=at+FIFTEEN, window_start=window[0],
                    window_end=window[1], valid=valid,
                    child_m5_starts=','.join(str(t) for t in clocks),
                    missing_m5_starts=','.join(str(t) for t,b in zip(clocks,children) if b is None),
                    invalid_m5_starts=','.join(str(t) for t,b in zip(clocks,children) if b is not None and not b.valid),
                    open_observed=first is not None, problem='' if valid else 'M15_INCOMPLETE_CHILDREN')
                diagnostic.append(rec)
                if valid:
                    parents[at] = Bar(at,FIFTEEN,first.open,max(b.high for b in children),
                        min(b.low for b in children),children[-1].close,
                        sum((b.volume for b in children),Decimal(0)))
                elif first is not None:
                    parents[at] = Bar(at,FIFTEEN,first.open,Decimal('NaN'),Decimal('NaN'),
                        Decimal('NaN'),Decimal(0),'M15_INCOMPLETE_CHILDREN')
        day += timedelta(days=1)
    return parents, diagnostic
