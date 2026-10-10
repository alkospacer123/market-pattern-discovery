"""Conditional daily research tables; independent arithmetic/coverage reconciliation."""
from collections import Counter
import csv
from datetime import date, datetime, timedelta
from decimal import Decimal as D
import json
from pathlib import Path

import audit_orb_false_break_fade_v2 as independent
import run_orb_false_break_fade as old_report
import orb_false_break_fade_replay as storage

LAB=Path(__file__).resolve().parents[1]
FIVE=timedelta(minutes=5)


def economic_row(trades):
    c1=old_report.summary(trades,'c1');c2=old_report.summary(trades,'c2')
    # The oracle recomputes dated costs from entry/exit prices, never trusts nets.
    for scenario,actual in [('c1',c1),('c2',c2)]:
        expected=independent.statistics(trades,scenario)
        for key,value in expected.items():
            if actual[key]!=value:
                raise AssertionError(('Independent statistics',scenario,key,actual[key],value))
    return dict(fills=sum(t['model_filled'] for t in trades),closed=c1['closed_trades'],
                unknown=sum(t['status']=='UNKNOWN' for t in trades),
                unknown_possible_entry=sum(t['status']=='UNKNOWN' and not t['model_filled'] for t in trades),
                PF_C1=c1['net_PF'],PF_C2=c2['net_PF'],PF_R_C1=c1['net_PF_R'],PF_R_C2=c2['net_PF_R'],
                expectancy_R_C1=c1['expectancy_R'],expectancy_R_C2=c2['expectancy_R'],
                net_R_C1=c1['net_R'],net_R_C2=c2['net_R'],gross=c1['gross'],cost_C1=c1['cost'],cost_C2=c2['cost'],
                net_quote_C1=c1['net'],net_quote_C2=c2['net'],win_rate_C1=c1['win_rate'],
                average_win_C1=c1['average_win_price'],average_loss_C1=c1['average_loss_price'],realized_RR_C1=c1['realized_reward_risk'],
                diagnostic_DD_R_C1=c1['max_drawdown_R'],diagnostic_DD_R_C2=c2['max_drawdown_R'],worst_R_C1=c1['worst_trade_R'],
                largest_winner_share=c1['largest_winner_share'],top3_winners_share=c1['top3_winners_share'],
                annual_net=None,annual_pf=None,annual_dd=None,conditional_independent_days=True)


def coverage_tables(raw,source_coverage,config):
    summary=[];events=[]
    for symbol,rows in raw.items():
        first=min(rows);last=max(rows);counts=Counter()
        cov_by_day={x['date']:x for x in source_coverage if x['instrument']==symbol}
        d=date(2023,1,1)
        while d.year==2023:
            windows=independent.oracle.calendar(d)
            if not windows:
                events.append(dict(instrument=symbol,date=str(d),kind='PLANNED_CALENDAR_CLOSED',start=datetime.combine(d,datetime.min.time()),end=datetime.combine(d+timedelta(days=1),datetime.min.time())))
                counts['calendar_closed_days']+=1
            else:
                expected=valid=missing=zero=0
                for start,end in windows:
                    if d<first.date():
                        events.append(dict(instrument=symbol,date=str(d),kind='PRE_INCEPTION',start=start,end=end))
                        continue
                    t=start
                    while t<end:
                        expected+=1
                        b=rows.get(t)
                        if b is None:
                            missing+=1
                            events.append(dict(instrument=symbol,date=str(d),kind='ABSENT_EXPECTED_M5',start=t,end=t+FIVE))
                        elif b[4]<=0:
                            zero+=1
                            events.append(dict(instrument=symbol,date=str(d),kind='INVALID_ZERO_VOLUME_M5',start=t,end=t+FIVE))
                        else:valid+=1
                        t+=FIVE
                if d>=first.date():
                    counts['expected_days']+=1;counts['observed_days']+=valid>0
                    counts['complete_days']+=missing+zero==0
                    counts['missing_expected_m5']+=missing;counts['zero_volume_expected_m5']+=zero
                    counts['valid_expected_m5']+=valid;counts['expected_m5']+=expected
                else:counts['pre_inception_trading_days']+=1
                c=cov_by_day[str(d)]
                if (c['expected_bars'],c['valid_bars'],c['missing_bars'],c['zero_volume_bars'])!=(expected,valid,missing,zero):
                    raise AssertionError(('Independent coverage',symbol,str(d)))
                events.append(dict(instrument=symbol,date=str(d),kind='PLANNED_INTRADAY_BREAK',start=windows[0][1],end=windows[1][0]))
                counts['planned_intraday_break_days']+=1
            d+=timedelta(days=1)
        summary.append(dict(instrument=symbol,first_source=first,last_source=last,source_rows_2023=len(rows),
                            covered_calendar_months=len({t.month for t in rows if independent.oracle.calendar(t.date()) and 10<=t.hour<19}),
                            **counts,source_ref=config['source_ref']))
    return summary,events


def fmt(x):
    return 'null' if x is None else f'{x:.3f}' if isinstance(x,D) else str(x)


def build(out,config,raw,signals,trades,days,oldsignals,oldtrades,monthly,coverage,metrics,audit):
    scenarios=[];directions=[];bands=[];three=[];comparisons=[]
    with (LAB/'results/stage2_orb_false_break_fade_m5_v1/signals.csv').open() as f:
        strict_signals=list(csv.DictReader(f))
    strict=json.loads((LAB/'results/stage2_orb_false_break_fade_m5_v1/metrics.json').read_text())
    coverage_summary,coverage_events=coverage_tables(raw,coverage,config)
    month_checks=0;statistic_cohorts=0
    for arch in config['architectures']:
        for symbol in config['instruments']:
            key=arch+'_'+symbol
            cohort=[t for t in trades if t['architecture']==arch and t['instrument']==symbol]
            ss=[s for s in signals if s['architecture']==arch and s['instrument']==symbol]
            os=[s for s in oldsignals if s['architecture']==arch and s['instrument']==symbol]
            ot=[t for t in oldtrades if t['architecture']==arch and t['instrument']==symbol]
            dd=[d for d in days if d['architecture']==arch and d['instrument']==symbol]
            mm=[m for m in monthly if m['architecture']==arch and m['instrument']==symbol]
            econ=economic_row(cohort);statistic_cohorts+=1
            signs=Counter(m['diagnostic_sign'] for m in mm)
            covered=12-signs['NO_COVERAGE'];entry_days={t['entry_at'].date() for t in cohort if t['model_filled']}
            observed=sum(d['source_observed'] for d in dd)
            current_by_id={s['signal_id']:s for s in os}
            latched=[s for s in strict_signals if s['architecture']==arch and s['instrument']==symbol and s['reason']=='UNKNOWN_POSITION_BLOCK']
            recovered=[s['signal_id'] for s in latched if current_by_id[s['signal_id']]['reason']!='UNKNOWN_POSITION_BLOCK']
            r=dict(architecture=arch,instrument=symbol,signals=metrics[key]['common_reclaim_signals'],after_filters=metrics[key]['accepted_signals'],
                   admitted_orders=sum(s['order_admitted'] for s in ss),observed_days=observed,expected_day_experiments=len(dd),
                   entry_days=len(entry_days),days_without_entries=observed-len(entry_days),fills_per_observed_day=D(econ['fills'])/observed,
                   positive_months=signs['POSITIVE'],negative_months=signs['NEGATIVE'],zero_months=signs['ZERO'],uncovered_months=signs['NO_COVERAGE'],
                   positive_covered_month_share=D(signs['POSITIVE'])/covered if covered else None,
                   old_strict_unknown_blocked=len(latched),restored_after_yearly_unknown_latch=len(recovered),
                   restored_model_fills=sum(t['signal_id'] in recovered and t['model_filled'] for t in ot),
                   restored_closed=sum(t['signal_id'] in recovered and t['status']=='CLOSED' for t in ot),**econ)
            scenarios.append(r)
            metrics[key].update(research_summary=r,direction_diagnostics={},month_signs=dict(signs),
                               daily_experiments=len(dd),observed_days=observed,admitted_orders=r['admitted_orders'],
                               all_event_reasons=dict(Counter(s['reason'] for s in ss)),exit_reasons=dict(Counter(t['exit_reason'] for t in cohort)))
            for direction,name in [(1,'LONG'),(-1,'SHORT')]:
                group=[t for t in cohort if t['direction']==direction]
                dr=dict(architecture=arch,instrument=symbol,direction=name,**economic_row(group))
                directions.append(dr);metrics[key]['direction_diagnostics'][name]=dr;statistic_cohorts+=1
            for name in ['LE_2_TICKS','GT_2_LE_5_TICKS','GT_5_TICKS']:
                group=[]
                for t in cohort:
                    if not t['model_filled'] or t.get('risk') is None:continue
                    risk_ticks=t['risk']/independent.oracle.grid(symbol,t['entry_at'])
                    label='LE_2_TICKS' if risk_ticks<=2 else 'GT_2_LE_5_TICKS' if risk_ticks<=5 else 'GT_5_TICKS'
                    if label==name:group.append(t)
                ratios=[2*independent.oracle.grid(symbol,t['entry_at'])/t['risk'] for t in group]
                bands.append(dict(architecture=arch,instrument=symbol,stop_band=name,
                                  expected_C1_to_risk_mean=sum(ratios,D(0))/len(ratios) if ratios else None,
                                  expected_C2_to_risk_mean=2*sum(ratios,D(0))/len(ratios) if ratios else None,**economic_row(group)))
                statistic_cohorts+=1
            for m in mm:
                mt=[t for t in cohort if str(t['signal_at']).startswith(m['month'])]
                check=economic_row(mt);statistic_cohorts+=1
                for source,field in [('PF_C1','diagnostic_PF_c1'),('PF_C2','diagnostic_PF_c2'),('net_R_C1','diagnostic_net_R_c1'),('net_R_C2','diagnostic_net_R_c2'),('expectancy_R_C1','diagnostic_expectancy_R_c1')]:
                    if check[source]!=m[field]:raise AssertionError(('Monthly economics',key,m['month'],source))
                    month_checks+=1
                ms=[s for s in ss if s['date'].startswith(m['month'])]
                m.update(raw_signals=sum(s.get('v2_original_base_reason')=='SIGNAL' for s in ms),
                         after_filters=sum(s['base_reason']=='SIGNAL' for s in ms),admitted_orders=sum(s['order_admitted'] for s in ms),
                         model_fills=check['fills'],unknown_possible_entry=check['unknown_possible_entry'],
                         diagnostic_DD_R_C1=check['diagnostic_DD_R_C1'],win_rate_C1=check['win_rate_C1'])
            for model,ts,sigs in [('v1_strict',None,None),('v1_daywise',ot,os),('v2_daywise',cohort,ss)]:
                if model=='v1_strict':
                    c=strict[key];x=c['closed_only_diagnostic']['c1'];y=c['closed_only_diagnostic']['c2']
                    row=dict(fills=c['model_fills'],closed=c['closed_trades'],unknown=c['unknown'],PF_C1=x['net_PF'],PF_C2=y['net_PF'],expectancy_R_C1=x['expectancy_R'],net_R_C1=x['net_R'],annual_net=c['annual_net_c1'],annual_pf=c['annual_net_PF_c1'],annual_dd=c['annual_max_DD_R_c1'])
                else:row=economic_row(ts);statistic_cohorts+=1
                three.append(dict(architecture=arch,instrument=symbol,model=model,
                                  raw_signals=metrics[key]['common_reclaim_signals'],
                                  restored_after_yearly_unknown_latch=len(recovered) if model=='v1_daywise' else None,**row))
    by_key={(s['architecture'],s['instrument']):s for s in scenarios}
    for a,b in [('A_BASE','B_IND'),('A_BASE','C_MTF'),('B_IND','D_MTF_IND'),('C_MTF','D_MTF_IND')]:
        for symbol in config['instruments']:
            before=by_key[a,symbol];after=by_key[b,symbol]
            comparisons.append(dict(comparison=a+'->'+b,instrument=symbol,before_fills=before['fills'],after_fills=after['fills'],
                                    before_PF_C1=before['PF_C1'],after_PF_C1=after['PF_C1'],before_PF_C2=before['PF_C2'],after_PF_C2=after['PF_C2'],
                                    delta_diagnostic_Net_R_C1=after['net_R_C1']-before['net_R_C1'],
                                    before_expectancy_R=before['expectancy_R_C1'],after_expectancy_R=after['expectancy_R_C1'],
                                    filter_attribution_is_descriptive_not_causal=True))
    for name,rows in [('scenario_summary.csv',scenarios),('direction_report.csv',directions),('stop_risk_report.csv',bands),
                      ('three_models.csv',three),('architecture_comparison.csv',comparisons),('coverage_report.csv',coverage_summary),('coverage_events.csv',coverage_events),('monthly.csv',monthly)]:
        old_report.write_csv(out/name,rows)
    audit.update(independent_metric_cohorts=statistic_cohorts,independent_month_fields=month_checks,
                 independent_coverage='PASS',monthly_rows=len(monthly),C1_C2_same_fill_ledger=True,
                 future_M5_feature_leakage='PASS',synthetic_cases='see validation.json / tests.log')
    storage.dump(out/'independent_audit.json',audit)
    lines=['# ORB False-Break Fade v2 — 2023 conditional daywise research','',
           '**INCONCLUSIVE_UNRESOLVED. No accepted economic Baseline.** UNKNOWN and incomplete coverage prevent a verified continuous-account annual Net/PF/DD; these fields remain null. The tables below contain only known closed trades from independent days with an explicit, unproven starting FLAT assumption. UNKNOWN exposures and unknown entry orders remain in the ledger, with null outcomes.',
           '', 'v2 was formulated after inspecting v1 outcomes on 2023. Its configuration was frozen before this repeat at `6843dbf8037a9df6eae6f88e8d1301c9f60e24bd`; it is an exploratory in-sample retest, not independent OOS confirmation. No thresholds, dates, instruments, Stop or execution rules were tuned.',
           '', 'A uses pure M5, B adds SMA14 ATR with 0.30 sweep threshold over actual completed observations across sessions, C vetoes only a completed M15 close accepting a breakout beyond the opposite OR boundary, D combines the two. No M15 context is explicitly neutral. All use the immutable v1 entry/exit engine; A economics equal v1 daywise exactly. The one-full-M5 waiting period supplies timing only. Boundary Open fills are historical model assumptions, not proven broker fills.',
           '', '| Architecture | Instrument | Signals | After filters | Admitted | Fills | Closed | UNKNOWN | PF C1 | PF C2 | Exp R C1 | + / − / 0 / uncovered |',
           '|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---|']
    for r in scenarios:
        fields=[r[k] for k in ['architecture','instrument','signals','after_filters','admitted_orders','fills','closed','unknown','PF_C1','PF_C2','expectancy_R_C1']]
        lines.append('| '+' | '.join(map(fmt,fields))+f" | {r['positive_months']} / {r['negative_months']} / {r['zero_months']} / {r['uncovered_months']} |")
    lines+=['','PF uses quote-unit P&L separately within each instrument; PF in normalized R is supplied too. Expectancy R weights each known closed trade by its own initial risk. Quote units across instruments are never summed into money/portfolio returns. Counts across architectures describe alternative experiments, not a pooled traded portfolio.',
            '', '## UNKNOWN restart and factor contributions','', '| Architecture | Strict fills / closed / UNKNOWN | v1 daywise fills / closed / UNKNOWN | v2 daywise fills / closed / UNKNOWN | Strict-latched signals restored in v1 daywise |', '|---|---:|---:|---:|---:|']
    for arch in config['architectures']:
        cells=[]
        for model in ['v1_strict','v1_daywise','v2_daywise']:
            group=[r for r in three if r['architecture']==arch and r['model']==model]
            cells.append(' / '.join(str(sum(int(r[k]) for r in group)) for k in ['fills','closed','unknown']))
        restored=sum(r['restored_after_yearly_unknown_latch'] for r in scenarios if r['architecture']==arch)
        lines.append('| '+arch+' | '+' | '.join(cells)+f' | {restored} |')
    base=[metrics['A_BASE_'+s] for s in config['instruments']]
    oldready=sum(s.get('atr_ready',False) for s in oldsignals if s['architecture']=='A_BASE' and s['base_reason']=='SIGNAL')
    lines+=['',f"Of {sum(m['common_reclaim_signals'] for m in base)} common reclaim signals, ATR readiness is {oldready} in v1 and {sum(m['atr14_v2_ready'] for m in base)} in v2; v2 sweep threshold passes {sum(m['atr14_v2_pass'] for m in base)}. M15 vetoes {sum(m['m15_veto'] for m in base)} signals. D admits {sum(r['after_filters'] for r in scenarios if r['architecture']=='D_MTF_IND')} filtered signals and has {sum(r['fills'] for r in scenarios if r['architecture']=='D_MTF_IND')} fills. The sixteen source-level comparisons are in `three_models.csv`; the v1 strict/daywise change isolates the yearly UNKNOWN latch, while the v1/v2 daywise change isolates feature gates.",
            '', 'ATR and M15 effects are descriptive on the fixed 2023 sample. `architecture_comparison.csv` reports A→B, A→C, B→D and C→D for each instrument. Filtering consumes the first attempt; it never recycles episodes. Occupancy and within-day UNKNOWN can also change admitted membership. Read frequency, C2, normalized expectancy and concentration together with PF.',
            '', '**ATR: reduces known losses in normalized R on this sample, without establishing a profitable factor.** A→B expectancy R improves on all four instruments, but three remain negative; GLD has only 20 known closes, +0.040 R expectancy but quote PF0.845. B has 173 fills versus A262 and every C2 quote PF is below1. ATR rejects135 of336 sweeps; unavailable-ATR rejects fall264→0. These are conditional in-sample improvements, not proof of robust economics.',
            '', '**M15: no consistent economic improvement.** A→C reduces fills262→252. USD PF0.964→1.023 remains below the target with negative R expectancy; CNY R expectancy worsens, GLD PF and expectancy worsen, IMOEX known outcomes are unchanged. The new veto removes14 common signals versus the old277 direction/no-context rejections.',
            '', '**Combination: no reliable synergy.** D has165 fills and152 known closes. Relative to B, USD improves slightly while GLD loses its small positive R expectancy, CNY R expectancy worsens, and IMOEX known outcomes stay unchanged. All four D expectancy R values are negative and C2 PF below1. There is no profitable Baseline to carry forward.',
            '', '## Months and frequency','', 'Every cell below is closed-only diagnostic Net R C1. `*` means that month has unresolved outcomes, `p` incomplete data, `—` no source coverage. Positive/negative/zero month counts in the first table use instrument-specific **Net quote P&L**, not the sum of normalized R; the two weight trades differently. Signs are descriptive known-cohort signs, even where a full monthly result remains unknown.',
            '', '| Scenario | Jan | Feb | Mar | Apr | May | Jun | Jul | Aug | Sep | Oct | Nov | Dec |','|---|'+ '|'.join(['---:']*12)+'|']
    for r in scenarios:
        mm=[m for m in monthly if m['architecture']==r['architecture'] and m['instrument']==r['instrument']]
        cells=['—' if m['classification']=='NO_COVERAGE' else fmt(m['diagnostic_net_R_c1'])+('*' if m['classification']=='UNKNOWN' else 'p' if m['classification']=='PARTIAL_DATA' else '') for m in mm]
        lines.append('| '+r['architecture']+' '+r['instrument']+' | '+' | '.join(cells)+' |')
    lines+=['','`monthly.csv` contains 192 rows, counts, C1/C2 Net/PF/expectancy, covered days and missing-bar classification. Positive share is positive / all source-covered months, including covered zero-trade months. `scenario_summary.csv` records frequency, no-entry days, positive share, win rate, realized reward/risk, worst trade, diagnostic drawdown and largest/top-three winning-P&L concentration. `direction_report.csv` separates LONG and SHORT for every scenario.',
            '', '| Scenario | LONG / SHORT fills | C1 win rate | Net R | Diagnostic DD R | Worst R | Largest / top3 winner share | Positive covered months |','|---|---:|---:|---:|---:|---:|---:|---:|']
    for r in scenarios:
        dirs=[x for x in directions if x['architecture']==r['architecture'] and x['instrument']==r['instrument']]
        ls=' / '.join(str(next(x['fills'] for x in dirs if x['direction']==side)) for side in ['LONG','SHORT'])
        lines.append(f"| {r['architecture']} {r['instrument']} | {ls} | {fmt(r['win_rate_C1'])} | {fmt(r['net_R_C1'])} | {fmt(r['diagnostic_DD_R_C1'])} | {fmt(r['worst_R_C1'])} | {fmt(r['largest_winner_share'])} / {fmt(r['top3_winners_share'])} | {fmt(r['positive_covered_month_share'])} |")
    lines+=['','## Stop and transaction-cost diagnosis','', '| Architecture | Stop band | Fills / closed / UNKNOWN | C1 Net R | C2 Net R | Mean modeled C1 / initial price risk |', '|---|---|---:|---:|---:|---:|']
    for arch in config['architectures']:
        for name in ['LE_2_TICKS','GT_2_LE_5_TICKS','GT_5_TICKS']:
            g=[b for b in bands if b['architecture']==arch and b['stop_band']==name];n=sum(b['fills'] for b in g)
            mean=sum((b['expected_C1_to_risk_mean']*b['fills'] for b in g if b['fills']),D(0))/n if n else None
            lines.append(f"| {arch} | {name} | {n} / {sum(b['closed'] for b in g)} / {sum(b['unknown'] for b in g)} | {fmt(sum((b['net_R_C1'] for b in g),D(0)))} | {fmt(sum((b['net_R_C2'] for b in g),D(0)))} | {fmt(mean)} |")
    lines+=['','`stop_risk_report.csv` separates all 48 instrument/architecture/band cases, including PF C1/C2 and expectancy. No minimum-Stop filter is added. C1 one tick per side and C2 two ticks per side replace costs on exactly the same fills. Cost/risk of one or more means costs can consume the entire gross risk before profit; the band evidence must be read with its sample count, not treated as a new optimized threshold.',
            '', 'In A, the23 known trades with Stop≤2 ticks have20 negative,2 zero and1 positive net C1 outcomes (aggregate −50.5 R; C2 −86.5 R). Their modeled C1 is at least1R and can exceed the 1.5R target for a one-tick risk. The >2–5 group has44 known closes and−18.033 R C1; the >5 group has179 known closes and−9.270 R C1. Small Stops are particularly harmful, but larger Stops also do not establish profitable aggregate diagnostics. Normalized R sums here are descriptive equal-risk statistics across instruments, not money or an actual portfolio curve. No filter is introduced from these observations.',
            '', '## Coverage and independent audit','', '| Instrument | Source rows | Observed / expected days | Missing expected M5 | Before-inception trading days |','|---|---:|---:|---:|---:|']
    for c in coverage_summary:
        lines.append(f"| {c['instrument']} | {c['source_rows_2023']} | {c['observed_days']} / {c['expected_days']} | {c['missing_expected_m5']} | {c.get('pre_inception_trading_days',0)} |")
    lines+=['','`coverage_events.csv` distinguishes actual absent expected M5, invalid volume, planned intraday/calendar closures and pre-inception periods. Windows retain the frozen historical contract: 10:00–14:00 and 14:05–18:50 MSK, with 14:15 reopening March13–20. A gap in an expected slot is an observed source absence, not proof of its market cause. No synthetic OHLC or gap repair is used. USD/CNY start Jan3, GLD Jul11, IMOEX Nov14. Historical CNY tick is 0.01 before Sep27 19:00 MSK and 0.001 after, validated by original boundary tests and every real trade.',
            '', f"**Independent internal algorithm audit {audit['status']}**, {audit['checked_fields']} gate/signal/trade field comparisons, {audit['control_fields']} A-control trade fields, {len(audit['discrepancies'])} discrepancies; {statistic_cohorts} independently reconciled economic cohorts and {month_checks} monthly fields. The auditor uses a separate bounded source reader, backward OR/M15 reconstruction, prefix-sum ATR, independent gate selection and separate chronological trade state machine. It never calls production trade-outcome functions. `trade_source_map.csv` maps every modeled trade/UNKNOWN to source M5 row references, including absent slots. Original synthetic tests cover Stop-first, entry-bar Take suppression, gaps, outward targets, Time/Session Flat, execution clocks and UNKNOWN/NONFILL; added cases cover daily restart, ATR continuity, stale M15 and deliberate gate corruption. This is internal algorithm verification; external PR review remains pending.",
            '', 'Both readers verify fixed 2023 prefix bytes/SHA-256; 2024+ bytes read = 0. Validation records deterministic repetition, tests, protected blobs, data ref and remote heads. Annual strict Net/PF/DD are never filled with daily assumptions; all old v1 artifacts and TradingSystemLab remain unchanged.',
            '', 'Technical corrections in this retest: constrain daywise outputs to the new v2 directory; exclude each manifest from its own hashes so repeats are stable; preserve NO_OR/daily flags on physically absent whole dates; use actual covered bars in monthly coverage; report C2 and modeled cost/risk for Stop groups; enforce frozen v2 config bytes; independently reconstruct filter gates before trade audit. The first real run caught a forward-path reason-label error (GLD Aug1): a later signal was labelled UNKNOWN_POSITION_BLOCK before the future missing slot. The daywise wrapper now reports POSITION_BUSY until the gap is reached; this changes no fills or economics and leaves strict v1 unchanged. An adversarial regression case verifies it.',
            '', '## Decision','', '**INCONCLUSIVE_UNRESOLVED — no economic Baseline PASS.** Daywise diagnostics can identify weak or promising in-sample cohorts but cannot establish uninterrupted full-year account economics with missing paths. The targeted PF≥1.6 also requires positive expectancy, enough independent trades, monthly regularity, acceptable concentration and C2 durability; a single high PF is insufficient. Stop at existing Draft PR #463, without merge, Stage3, Walk Forward, TRUE OOS or another strategy.']
    (out/'REPORT.md').write_text('\n'.join(lines)+'\n')
