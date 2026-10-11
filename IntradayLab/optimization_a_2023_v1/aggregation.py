"""Frozen CLOSED-only metrics and exhaustive, instrument-local selection."""
from collections import Counter
from decimal import Decimal as D, localcontext

NA = 'NOT_AVAILABLE'
EPS = D('1e-20')
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
        ambiguous_directional_events=sum(s['base_reason']!='SIGNAL' for s in result.signals),
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
    keys=('touches','stop_buffer_ticks','target_net_R')
    for row in candidates:
        neighbors=[]
        for other in candidates:
            if row['instrument']!=other['instrument']: continue
            delta=[abs(int(row[k])-int(other[k])) for k in keys]
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
            months_pass=sum(r['pass_months'] for r in rows),
            base_study_criteria_pass=sum(all(r[k] for k in r if k.startswith('pass_') and k!='pass_neighbors') for r in rows),
            full_criteria_pass=len(passed),ranked_ids=[r['configuration_id'] for r in passed],
            result=policy['candidate_status'] if passed else policy['no_candidate_status'])
    return neighborhoods,dict(criteria=s,instruments=selected,evaluations=len(candidates),
        overall_result=policy['candidate_status'] if any(v['full_criteria_pass'] for v in selected.values()) else policy['no_candidate_status'],
        external_independent_review_required=True,no_automatic_advance=True)


def report(policy,freeze,candidates,monthly,selection):
    def f(v): return f'{v:.6f}' if isinstance(v,D) else str(v)
    def table(headers,rows):
        return ['| '+' | '.join(headers)+' |','|'+'|'.join(['---']*len(headers))+'|',
            *['| '+' | '.join(f(v) for v in row)+' |' for row in rows],'']
    lines=['# Optimization A Equal High/Low — bounded frozen 2023 grid','',
        '**'+selection['overall_result']+'**','',
        f'Base main: `{policy["base_main"]}`. Pre-P&L freeze: `{freeze}`.',
        '72 fixed configurations × USDRUBF/CNYRUBF = 144 evaluations. Complete exhaustive search; no added variants, direction selection, or early stop.',
        'All results below are profit after model C1 costs, not actual broker commissions. Prices are instrument quotation units and never pooled. CLOSED-only economics are conditional on coverage and assumed FLAT after excluded positions. No complete annual PF/return, continuous equity or broker Max DD is established.',
        'Take distance = R × (gross initial risk + planned 2 entry ticks) + planned 2 entry ticks, rounded outward. Net_R uses gross initial risk; planned net/net R and realized net/net R have distinct ledger fields. Actual C1 uses dated entry and exit ticks.',
        'One attempt per maximal equal-extreme sequence; completed candles only; immediate next Open admission, structural Stop unchanged, entry-bar Take disabled, Stop-first, 120-minute/session-flat deadline. CNY tick .01 before 2023-09-27 19:00 MSK, .001 thereafter.',
        'Sample requires 100 CLOSED / 40 entry dates / 6 entry months. Both PF ≥2, expectancy >0, ≥9 positive exit months, conditional DD ≤20R, largest winner ≤25%, largest positive month ≤50%; two adjacent neighbors need 100 CLOSED, positive expectancy, PF R ≥1.5. Local 2023 stability diagnosis is not Robustness.',
        'Monthly zero sign uses the registry 1e-20 R numerical tolerance. PF without losses is NOT_AVAILABLE; zero/no-trade months are not positive. Independent algorithm audit does not replace external Draft PR review.','']
    lines+=table(['Instrument','Evaluated','Sample','Both PF','Months ≥9','Base criteria','All criteria'],[
        [symbol,*[selection['instruments'][symbol][k] for k in ('evaluated','sample_pass','both_PF_pass','months_pass','base_study_criteria_pass','full_criteria_pass')]] for symbol in policy['instruments']])
    lines+=['Reproduce from a clean checkout with the pinned read-only source:',
        '```bash','python -m IntradayLab.optimization_a_2023_v1.validate --data-root /workspace/market-pattern-data --output IntradayLab/work/fresh_optimization_a_validation','```',
        'The validation command runs canonical + two full repeats and the independent auditor, checks freeze dependencies and every preexisting repository path, and refuses existing outputs. Source OHLC is not copied into this repository.','',
        'All candidate criteria and reasons: all_candidates.csv. Complete exact monthly and directional metrics: monthly_results.csv and direction_results.csv. Full events, CLOSED trades, SKIP, EXCLUDED, rejected/nonfill and coverage: evaluations/<ID>/<instrument>/. Selection ranks contain only fully qualified configurations.',
        'Counterfactual legacy replay for T3/SB1/TP3 validates frozen A_v1 paths; comparator_gap_policy.csv explains differences from V2 entry skipping and consequent occupancy. This is an audit of the historical comparator, not an added Optimization variant.','']
    for symbol in policy['instruments']:
        lines += ['## '+symbol,'',selection['instruments'][symbol]['result'],'']
        for r in [c for c in candidates if c['instrument']==symbol]:
            lines+=['### '+r['configuration_id'],'',f'Status: **{r["status"]}**. Failures: {r["failure_reasons"] or "none"}.',
                f'CLOSED {r["CLOSED"]}, entry dates {r["entry_days"]}, entry months {r["entry_months"]}; SKIP {r["DATA_GAP_SKIP"]}, EXCLUDED {r["DATA_QUALITY_EXCLUDED"]}, exclusion share {f(r["exclusion_fraction"])}; conditional FLAT CLOSED {r["conditional_flat_CLOSED"]}.',
                f'Net {f(r["Net_R"])} R; PF R / price {f(r["PF_R"])} / {f(r["PF_price"])}; expectancy {f(r["expectancy_R"])} R; win rate {f(r["win_rate"])}; average winner / loser {f(r["average_winner_R"])} / {f(r["average_loser_R"])} R.',
                f'Conditional CLOSED-only DD {f(r["conditional_closed_only_DD_R"])} R; largest winner share {f(r["largest_winner_share_R"])}; largest positive month share {f(r["largest_positive_month_share_R"])}. Positive / negative / zero months {r["positive_exit_months"]} / {r["negative_exit_months"]} / {r["zero_exit_months"]}; ideal 12/12: {r["ideal_12_positive_months"]}. Qualifying adjacent neighbors: {r["positive_neighbor_count"]}.','']
            rows=[m for m in monthly if m['instrument']==symbol and m['configuration_id']==r['configuration_id']]
            lines+=table(['Exit month','CLOSED','Net R','PF R','PF price','Incomplete days','SKIP','EXCLUDED'],[[m[k] for k in ('month','CLOSED','Net_R','PF_R','PF_price','incomplete_days','DATA_GAP_SKIP','DATA_QUALITY_EXCLUDED')] for m in rows])
    lines+=['## Evidence limits','',
        'Missing entry Open produces no entry, C1 or P&L; no later substitution. Excluded positions retain known entry evidence and unknown outcomes; same-day entries are blocked. Counts and fractions describe possible selection bias, especially CNY. Incomplete coverage also exists on days without an exclusion. Closed-only DD follows resolved trade order and is conditional.',
        'No GLDRUBF/IMOEXF evaluation, 2024+ reads, Robustness, WF, TRUE OOS, LIVE, portfolio sizing, merge or auto-merge. Frozen Baselines, Master Registry, TradingSystemLab and Draft #472 remain unchanged. STOP after one Draft PR.','']
    return '\n'.join(lines)
