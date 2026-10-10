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


def distribution_metrics(trades):
    """Additional closed-only distribution diagnostics, without pooling money.

    Call per instrument for price-unit statistics. R statistics can describe
    independent research trades, but never establish a continuous equity curve.
    Month attribution is the signal date, as in the common report tables.
    """
    closed = [t for t in trades if t['status']=='CLOSED']
    winners = [t for t in closed if t['net_R_c1'] > 0]
    losers = [t for t in closed if t['net_R_c1'] < 0]
    def mean(rows, key):
        return sum((t[key] for t in rows), Decimal(0))/len(rows) if rows else None
    monthly = {}
    for t in closed:
        month = str(t['signal_at'])[:7]
        monthly[month] = monthly.get(month, Decimal(0))+t['net_R_c1']
    gain = sum((t['net_R_c1'] for t in winners), Decimal(0))
    month_gain = sum((x for x in monthly.values() if x > 0), Decimal(0))
    return dict(unique_trade_days=len({str(t['signal_at'])[:10] for t in closed}),
                average_winner_R=mean(winners, 'net_R_c1'), average_loser_R=mean(losers, 'net_R_c1'),
                average_winner_price=mean(winners, 'net_c1'), average_loser_price=mean(losers, 'net_c1'),
                active_months=len(monthly), positive_months=sum(x > 0 for x in monthly.values()),
                negative_months=sum(x < 0 for x in monthly.values()),
                zero_closed_economy_months=12-sum(x != 0 for x in monthly.values()),
                largest_winner_share_R=max((t['net_R_c1'] for t in winners), default=Decimal(0))/gain if gain else None,
                largest_positive_month_share_R=max(monthly.values(), default=Decimal(0))/month_gain if month_gain else None,
                top_three_winners_share_R=sum(sorted((t['net_R_c1'] for t in winners), reverse=True)[:3], Decimal(0))/gain if gain else None,
                monthly_closed_Net_R=dict(sorted(monthly.items())))


def assess_baseline(summary, distribution, policy):
    """Apply declared evidence criteria; no candidate-specific fixed verdict.

    Incomplete data has a separate conditional economic diagnosis. This helper
    does not alter the original summarize contract or authorize another stage.
    """
    d = summary['conditional_closed_only_C1']
    minimum_sample = (d['closed'] >= policy['minimum_closed_trades'] and
                      distribution['unique_trade_days'] >= policy['minimum_unique_trade_days'] and
                      distribution['active_months'] >= policy['minimum_active_months'])
    expectancy = d['Expectancy_R']
    positive = expectancy is not None and expectancy > 0
    pf_pass = all(d[key] is not None and d[key] >= Decimal(policy[goal]) for key, goal in (
        ('PF_C1_price', 'goal_PF_C1_price'), ('PF_C1_R', 'goal_PF_C1_R')))
    stable = (distribution['positive_months'] >= policy['minimum_positive_months'] and
              distribution['positive_months'] >= Decimal(policy['minimum_positive_active_month_fraction'])*distribution['active_months'])
    unconcentrated = all(distribution[key] is not None and distribution[key] <= Decimal(policy[limit]) for key, limit in (
        ('largest_winner_share_R', 'maximum_largest_winner_share'),
        ('largest_positive_month_share_R', 'maximum_largest_positive_month_share')))
    checks = dict(complete=summary['annual_complete'], enough_sample=minimum_sample,
                  positive_expectancy=positive, PF_goal_met=pf_pass,
                  monthly_stability=stable, concentration_acceptable=unconcentrated)
    negative = expectancy is not None and expectancy <= 0
    conditional = ('NO ECONOMIC BASELINE PASS' if negative else 'INSUFFICIENT_EVIDENCE'
                   if not minimum_sample else 'CONDITIONAL_CRITERIA_MET' if positive and pf_pass and stable and unconcentrated
                   else 'POSITIVE_EXPECTANCY_BELOW_EVIDENCE_CRITERIA')
    status = ('INCONCLUSIVE' if not summary['annual_complete'] else 'NO ECONOMIC BASELINE PASS'
              if negative else 'INCONCLUSIVE' if not minimum_sample or expectancy is None
              else 'ECONOMICALLY_PROMISING_BASELINE' if all(checks.values()) else 'NO ECONOMIC BASELINE PASS')
    return dict(status=status, economic_diagnostic=conditional, evidence_checks=checks,
                optimization_allowed=False)
