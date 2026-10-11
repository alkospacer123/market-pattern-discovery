"""Frozen CLOSED-only metrics and exhaustive, instrument-local selection."""
from collections import Counter
from decimal import Decimal as D, localcontext

NA = 'NOT_AVAILABLE'
EPS = D(0)
MONTHS = [f'2023-{m:02d}' for m in range(1,13)]


def exit_month(t):
    # Intrabar exits have an observed exit interval, not a fabricated instant.
    return str(t['exit_at'] or t['exit_interval_start'])[:7]


def economics(trades):
    with localcontext() as ctx:
        ctx.prec=50
        ordered=sorted(trades,key=lambda t:(t['resolved_at'],t['signal_id']))
        r=[D(t['net_R_c1']) for t in ordered];p=[D(t['net_c1']) for t in ordered]
        def profit_factor(values):
            gain=sum((v for v in values if v>0),D(0))
            loss=-sum((v for v in values if v<0),D(0))
            return gain/loss if loss else NA
        def mean(values): return sum(values,D(0))/len(values) if values else NA
        curve=peak=dd=D(0)
        for v in r:
            curve+=v;peak=max(peak,curve);dd=max(dd,peak-curve)
        monthly={m:sum((D(t['net_R_c1']) for t in ordered if exit_month(t)==m),D(0)) for m in MONTHS}
        monthly={m:D(0) if abs(v)<=EPS else v for m,v in monthly.items()}
        wins=[v for v in r if v>0];losers=[v for v in r if v<0]
        gains=sum(wins,D(0));month_gains=sum((v for v in monthly.values() if v>0),D(0))
        return dict(CLOSED=len(r),entry_days=len({str(t['entry_at'])[:10] for t in ordered}),
            entry_months=len({str(t['entry_at'])[:7] for t in ordered}),
            Net_R=sum(r,D(0)),Net_price=sum(p,D(0)),PF_R=profit_factor(r),PF_price=profit_factor(p),
            PF_unavailable_reason='NO_NEGATIVE_CLOSED_PNL' if not any(v<0 for v in r) else '',
            expectancy_R=mean(r),win_rate=D(len(wins))/len(r) if r else NA,
            average_winner_R=mean(wins),average_loser_R=mean(losers),
            average_winner_price=mean([v for v in p if v>0]),
            average_loser_price=mean([v for v in p if v<0]),
            conditional_closed_only_DD_R=dd if r else NA,
            positive_exit_months=sum(v>0 for v in monthly.values()),
            negative_exit_months=sum(v<0 for v in monthly.values()),
            zero_exit_months=sum(v==0 for v in monthly.values()),
            ideal_12_positive_months=all(v>0 for v in monthly.values()),
            largest_winner_share_R=max(wins)/gains if gains else NA,
            largest_positive_month_share_R=max(monthly.values())/month_gains if month_gains else NA,
            gross_price=sum((D(t['gross']) for t in ordered),D(0)),
            C1_price=sum((D(t['cost_c1']) for t in ordered),D(0)),
            gross_R=sum((D(t['gross_R']) for t in ordered),D(0)),
            C1_R=sum((D(t['cost_R']) for t in ordered),D(0)),
            metric_scope='CONDITIONAL_CLOSED_ONLY; initial gross-risk R; no continuous broker equity')


def enough(m,s):
    return m['CLOSED']>=s['minimum_closed'] and m['entry_days']>=s['minimum_entry_days'] and m['entry_months']>=s['minimum_entry_months']


def compare(value,limit,op):
    return value!=NA and op(D(value),D(limit))


def criteria(m,s):
    return dict(sample=enough(m,s),
        PF_R=compare(m['PF_R'],s['minimum_PF_R'],lambda a,b:a>=b),
        PF_price=compare(m['PF_price'],s['minimum_PF_price'],lambda a,b:a>=b),
        positive_expectancy=compare(m['expectancy_R'],0,lambda a,b:a>b),
        months=m['positive_exit_months']>=s['minimum_positive_exit_months'],
        conditional_DD=compare(m['conditional_closed_only_DD_R'],s['maximum_conditional_closed_only_DD_R'],lambda a,b:a<=b),
        trade_concentration=compare(m['largest_winner_share_R'],s['maximum_largest_winner_share_R'],lambda a,b:a<=b),
        month_concentration=compare(m['largest_positive_month_share_R'],s['maximum_largest_positive_month_share_R'],lambda a,b:a<=b))


def summaries(config,symbol,result,coverage,policy,freeze,code_sha):
    label=dict(configuration_id=config['configuration_id'],instrument=symbol)
    m=dict(label,**{k:v for k,v in config.items() if k!='configuration_id'},**economics(result.trades),
        source_sha=policy['source_ref'],strategy_sha256=code_sha,freeze_commit=freeze,
        accepted_entries=sum(s['model_filled'] for s in result.signals),
        DATA_GAP_SKIP=len(result.data_gap_skips),DATA_QUALITY_EXCLUDED=len(result.data_quality_exclusions),
        conditional_flat_CLOSED=sum(bool(t['prior_exclusion_requires_flat_assumption']) for t in result.trades),
        complete_coverage_days=sum(c['status']=='COMPLETE' for c in coverage),
        incomplete_coverage_days=sum(c['status']=='INCOMPLETE' for c in coverage))
    with localcontext() as ctx:
        ctx.prec=50
        m['exclusion_fraction']=D(m['DATA_QUALITY_EXCLUDED'])/m['accepted_entries'] if m['accepted_entries'] else NA
        attempted=m['accepted_entries']+m['DATA_GAP_SKIP']
        m['skip_fraction_of_fills_and_skips']=D(m['DATA_GAP_SKIP'])/attempted if attempted else NA
    s=policy['selection']
    m['sample_failure_reasons']='|'.join(name for name,actual,threshold in (('CLOSED_BELOW_100',m['CLOSED'],s['minimum_closed']),('ENTRY_DAYS_BELOW_40',m['entry_days'],s['minimum_entry_days']),('ENTRY_MONTHS_BELOW_6',m['entry_months'],s['minimum_entry_months'])) if actual<threshold)
    checks=criteria(m,policy['selection'])
    m.update({f'pass_{k}':v for k,v in checks.items()})
    months=[];directions=[]
    for month in MONTHS:
        cohort=[t for t in result.trades if exit_month(t)==month]
        cov=[c for c in coverage if c['date'][:7]==month]
        months.append(dict(label,month=month,**economics(cohort),
            complete_days=sum(c['status']=='COMPLETE' for c in cov),
            incomplete_days=sum(c['status']=='INCOMPLETE' for c in cov),
            valid_bars=sum(c['valid_bars'] for c in cov),missing_bars=sum(c['missing_bars'] for c in cov),
            invalid_bars=sum(c['invalid_bars'] for c in cov),
            accepted_entries=sum(c['accepted_entries'] for c in cov),
            DATA_GAP_SKIP=sum(c['data_gap_skips'] for c in cov),
            DATA_QUALITY_EXCLUDED=sum(c['data_quality_excluded'] for c in cov),
            coverage_scope='ENTRY_DATE counts; CLOSED economics by EXIT_DATE'))
    for side in (1,-1):
        directions.append(dict(label,direction='LONG' if side==1 else 'SHORT',
            **economics([t for t in result.trades if t['direction']==side]),
            DATA_GAP_SKIP=sum(s['direction']==side for s in result.data_gap_skips),
            DATA_QUALITY_EXCLUDED=sum(t['direction']==side for t in result.data_quality_exclusions)))
    funnel=dict(label,raw_directional_events=len(result.signals),
        signals=sum(s['base_reason']=='SIGNAL' for s in result.signals),
        ambiguous_directional_events=sum(s['base_reason']=='AMBIGUOUS_BOTH_SIDES' for s in result.signals),
        final_close_not_rejected_events=sum(s['base_reason'] in ('SECOND_CLOSE_NOT_REJECTED','THIRD_CLOSE_NOT_REJECTED') for s in result.signals),
        admissions=sum(s['order_admitted'] for s in result.signals),
        rejects=sum(s['base_reason']=='SIGNAL' and s['status']=='REJECTED' for s in result.signals),
        nonfills=sum(s['status']=='NONFILL' for s in result.signals),
        fills=m['accepted_entries'],SKIP=m['DATA_GAP_SKIP'],EXCLUDED=m['DATA_QUALITY_EXCLUDED'],CLOSED=m['CLOSED'],
        reason_counts=dict(sorted(Counter(s['reason'] for s in result.signals if s['reason']).items())))
    assert funnel['signals']==funnel['rejects']+funnel['nonfills']+funnel['fills']+funnel['SKIP']
    assert funnel['fills']==funnel['CLOSED']+funnel['EXCLUDED']
    return m,months,directions,funnel


def select(candidates,policy):
    neighborhoods=[];selected={};s=policy['selection']
    keys=tuple(policy['grid_order'])
    for row in candidates:
        neighbors=[]
        for other in candidates:
            if row['instrument']!=other['instrument']: continue
            delta=[abs(policy['grid'][k].index(int(row[k]))-policy['grid'][k].index(int(other[k]))) for k in keys]
            if sum(delta)!=1: continue
            good=(other['CLOSED']>=s['neighbor_minimum_closed'] and
                compare(other['expectancy_R'],0,lambda a,b:a>b) and
                compare(other['PF_R'],s['neighbor_minimum_PF_R'],lambda a,b:a>=b))
            neighborhoods.append(dict(instrument=row['instrument'],configuration_id=row['configuration_id'],
                neighbor_id=other['configuration_id'],changed_parameter=keys[delta.index(1)],
                neighbor_CLOSED=other['CLOSED'],neighbor_expectancy_R=other['expectancy_R'],
                neighbor_PF_R=other['PF_R'],neighbor_qualifies=good,
                diagnosis='LOCAL_2023_PARAMETER_STABILITY; NOT_ROBUSTNESS'))
            if good: neighbors.append(other['configuration_id'])
        row['positive_neighbor_count']=len(neighbors)
        row['pass_neighbors']=len(neighbors)>=s['minimum_positive_neighbor_count']
        failures=[k.removeprefix('pass_') for k,v in row.items() if k.startswith('pass_') and not v]
        row['failure_reasons']='|'.join(failures)
        row['status']=('INSUFFICIENT_SAMPLE' if not row['pass_sample'] else
            policy['candidate_status'] if not failures else 'DOES_NOT_QUALIFY')
        row['rank']=NA
    for symbol in policy['instruments']:
        rows=[r for r in candidates if r['instrument']==symbol]
        passed=[r for r in rows if not r['failure_reasons']]
        passed.sort(key=lambda r:(-r['positive_exit_months'],-min(r['PF_R'],r['PF_price']),
            r['conditional_closed_only_DD_R'],-r['CLOSED'],r['configuration_id']))
        for i,r in enumerate(passed,1): r['rank']=i
        selected[symbol]=dict(evaluated=len(rows),sample_pass=sum(r['pass_sample'] for r in rows),
            both_PF_pass=sum(r['pass_PF_R'] and r['pass_PF_price'] for r in rows),
            sample_and_both_PF_pass=sum(r['pass_sample'] and r['pass_PF_R'] and r['pass_PF_price'] for r in rows),
            neighbors_pass=sum(r['pass_neighbors'] for r in rows),
            months_pass=sum(r['pass_months'] for r in rows),
            base_study_criteria_pass=sum(all(r[k] for k in r if k.startswith('pass_') and k!='pass_neighbors') for r in rows),
            full_criteria_pass=len(passed),ranked_ids=[r['configuration_id'] for r in passed],
            result=policy['candidate_status'] if passed else policy['no_candidate_status'])
    return neighborhoods,dict(criteria=s,instruments=selected,evaluations=len(candidates),
        overall_result=policy['candidate_status'] if any(v['full_criteria_pass'] for v in selected.values()) else policy['no_candidate_status'],
        external_independent_review_required=True,no_automatic_advance=True)


