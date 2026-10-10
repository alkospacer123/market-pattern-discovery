"""Deterministic C1 metrics; closed-only diagnostics never repair UNKNOWN."""
from collections import Counter
from decimal import Decimal


def closed_metrics(trades):
    closed = sorted((t for t in trades if t['status']=='CLOSED'),
                    key=lambda t: (t['resolved_at'], t['signal_id']))
    rs = [t['net_R_c1'] for t in closed]
    ps = [t['net_c1'] for t in closed]
    def pf(values):
        gains = sum((x for x in values if x > 0), Decimal(0))
        losses = -sum((x for x in values if x < 0), Decimal(0))
        return gains/losses if losses else None
    curve = peak = dd = Decimal(0)
    for r in rs:
        curve += r
        peak = max(peak, curve)
        dd = max(dd, peak-curve)
    return dict(closed=len(closed), PF_C1_price=pf(ps), PF_C1_R=pf(rs),
                PF_no_losses=bool(ps) and not any(x < 0 for x in ps),
                Net_R=sum(rs, Decimal(0)), Net_price=sum(ps, Decimal(0)),
                Expectancy_R=sum(rs, Decimal(0))/len(rs) if rs else None,
                Win_Rate=Decimal(sum(x > 0 for x in rs))/len(rs) if rs else None,
                Max_DD_R=dd if rs else None,
                cost_C1=sum((t['cost_c1'] for t in closed), Decimal(0)),
                exit_reasons=dict(sorted(Counter(t['exit_reason'] for t in closed).items())))


def summarize(trades, signals, coverage):
    diagnostic = closed_metrics(trades)
    complete = bool(coverage) and all(c['status']=='COMPLETE' for c in coverage)
    unknown = sum(t['status']=='UNKNOWN' for t in trades)
    conditional = any(t.get('prior_unknown_requires_flat_assumption') for t in trades)
    credible = complete and not unknown and not conditional
    annual = {k: diagnostic[k] if credible else None for k in (
        'PF_C1_price', 'PF_C1_R', 'Net_R', 'Expectancy_R', 'Win_Rate', 'Max_DD_R')}
    return dict(events=len(signals), signals=sum(s['base_reason']=='SIGNAL' for s in signals),
                admitted_orders=sum(s['order_admitted'] for s in signals),
                model_fills=sum(t['model_filled'] for t in trades),
                closed=diagnostic['closed'], unknown=unknown,
                unknown_possible_entry=sum(t['status']=='UNKNOWN' and not t['model_filled'] for t in trades),
                post_unknown_conditional_closed=sum(t['status']=='CLOSED' and t.get('prior_unknown_requires_flat_assumption', False) for t in trades),
                rejection_reasons=dict(sorted(Counter(s['reason'] for s in signals if s['reason']).items())),
                annual_complete=credible, annual=annual, conditional_closed_only_C1=diagnostic,
                status='INCONCLUSIVE' if not credible else 'NO ECONOMIC BASELINE PASS' if diagnostic['Expectancy_R'] is None or diagnostic['Expectancy_R'] <= 0 else 'BASELINE_REQUIRES_EVIDENCE_REVIEW',
                economic_diagnostic='NO ECONOMIC BASELINE PASS' if diagnostic['Expectancy_R'] is not None and diagnostic['Expectancy_R'] <= 0 else 'INSUFFICIENT_EVIDENCE',
                optimization_allowed=False)
