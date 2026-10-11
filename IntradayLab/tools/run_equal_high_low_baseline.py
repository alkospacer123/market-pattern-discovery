#!/usr/bin/env python3
"""One preregistered A_v1 2023 run in the common Backtester; Oracle is separate."""
import argparse
from collections import Counter
from datetime import date
from decimal import Decimal as D
import json
from pathlib import Path
import sys

ROOT=Path(__file__).resolve().parents[2];sys.path.insert(0,str(ROOT));LAB=ROOT/'IntradayLab'
from IntradayLab.core.backtester import Backtester
from IntradayLab.core.calendar import MarketRules
from IntradayLab.core.data_loader import load_market_data
from IntradayLab.core.metrics import summarize,distribution_metrics,assess_baseline,closed_metrics
from IntradayLab.core.reports import csv_write,dump,coverage,table_row
from IntradayLab.strategies.equal_high_low_m5 import EqualHighLowM5
from IntradayLab.tools.equal_high_low_contract import CONFIG,OUT,verify_freeze,check_output,bounded_reads,protected_check
from IntradayLab.tools.audit_equal_high_low_baseline import episodes,replay


def assessed(trades,signals,source,cfg):
    m=summarize(trades,signals,source);m['distribution']=distribution_metrics(trades)
    m.update(assess_baseline(m,m['distribution'],cfg['classification_policy']))
    closed=[t for t in trades if t['status']=='CLOSED'];fills=[t for t in trades if t['model_filled']]
    eligible=[s for s in signals if s['base_reason']=='SIGNAL']
    available=sum(c['status']!='PRE_INCEPTION' for c in source)
    m.update(raw_directional_candidates=len(signals),ambiguous_directional_candidates=len(signals)-len(eligible),
        ambiguous_M5_events=len({s['signal_at'] for s in signals if s['base_reason']=='AMBIGUOUS_BOTH_SIDES'}),
        rejected_known_entries=sum(s['status'] in ('REJECTED','NONFILL') for s in eligible),
        unknown_entry_attempts=sum(s['status']=='UNKNOWN' for s in eligible),
        rejection_reasons=dict(sorted(Counter(s['reason'] for s in eligible if s['reason']).items())),
        all_candidate_refusal_reasons=dict(sorted(Counter(s['reason'] for s in signals if s['reason']).items())),
        unknown_reasons=dict(sorted(Counter(t['unknown_reason'] for t in trades if t['status']=='UNKNOWN').items())),
        available_calendar_trading_days=available,
        fill_days=len({str(t['signal_at'])[:10] for t in fills}),
        model_fills_per_available_day=D(len(fills))/available if available else None,
        model_fills_per_fill_day=D(len(fills))/len({str(t['signal_at'])[:10] for t in fills}) if fills else None)
    m['economics']=dict(gross_price=sum((t['gross'] for t in closed),D(0)),
        C1_price=sum((t['cost_c1'] for t in closed),D(0)),net_price=sum((t['net_c1'] for t in closed),D(0)),
        gross_R=sum((t['gross_R'] for t in closed),D(0)),C1_R=sum((t['cost_R'] for t in closed),D(0)),
        net_R=sum((t['net_R_c1'] for t in closed),D(0)),
        planned_net_net_R_min=min((t['planned_net_to_net_R'] for t in fills),default=None),
        planned_net_net_R_max=max((t['planned_net_to_net_R'] for t in fills),default=None),
        stop_risk_ticks_min=min((t['risk']/t['entry_tick'] for t in fills),default=None),
        stop_risk_ticks_max=max((t['risk']/t['entry_tick'] for t in fills),default=None),
        adverse_stop_gap_exits=sum(t['exit_reason']=='STOP' and t['exit_at'] is not None for t in closed),
        scope='conditional known closures only; incompatible prices never pooled')
    return m


def row(symbol,trades,signals,source,cfg,**labels):
    r=table_row(symbol,trades,signals,source,**labels);m=assessed(trades,signals,source,cfg)
    r.update(status=m['status'],economic_diagnostic=m['economic_diagnostic'])
    r.update({'conditional_'+k:v for k,v in m['conditional_closed_only_C1'].items()})
    r.update({'conditional_'+k:v for k,v in m['distribution'].items()})
    r.update(m['economics'])
    if not any(c['valid_bars'] for c in source):
        for key in ('PF_C1_price','PF_C1_R','Net_R','Net_price','Expectancy_R','Win_Rate','Max_DD_R','cost_C1'):
            r['conditional_'+key]=None
        for key in ('gross_price','C1_price','net_price','gross_R','C1_R','net_R'):
            r[key]=None
    for k in ('raw_directional_candidates','ambiguous_directional_candidates','rejected_known_entries','unknown_entry_attempts',
              'model_fills_per_available_day','model_fills_per_fill_day','fill_days','available_calendar_trading_days','rejection_reasons','unknown_reasons'):
        r[k]=m[k]
    return r


def diagnostic(raw,signals,trades,cfg,output):
    target=output/'diagnostics';target.mkdir(exist_ok=True)
    oracle_s=[];oracle_t=[];comparison=[];ms={}
    for symbol in cfg['instruments']:
        observations={at:(b.open,b.high,b.low,b.close,b.volume) for at,b in raw[symbol].items()}
        os,ot=replay(symbol,observations,episodes(symbol,observations),close_oracle=True)
        oracle_s.extend(os);oracle_t.extend(ot)
        ms[symbol]=dict(conditional_closed_only=closed_metrics(ot),signals=sum(s['base_reason']=='SIGNAL' for s in os),
            model_fills=sum(t['model_filled'] for t in ot),unknown=sum(t['status']=='UNKNOWN' for t in ot),
            refusal_reasons=dict(sorted(Counter(s['reason'] for s in os if s['reason']).items())))
        by_s={s['signal_id']:s for s in os};by_t={t['signal_id']:t for t in ot};next_t={t['signal_id']:t for t in trades}
        for s in (x for x in signals if x['instrument']==symbol):
            o=by_s[s['signal_id']];oq=by_t.get(s['signal_id'],{});nq=next_t.get(s['signal_id'],{})
            comparison.append(dict(signal_id=s['signal_id'],instrument=symbol,direction=s['direction'],signal_at=s['signal_at'],
                signal_close=s['signal_close'],next_open=s.get('entry_open'),next_status=s['status'],next_reason=s['reason'],
                oracle_entry_close=o.get('entry_open'),oracle_status=o['status'],oracle_reason=o['reason'],
                directional_entry_displacement=s['direction']*(s['entry_open']-s['signal_close']) if s.get('entry_open') is not None else None,
                next_trade_status=nq.get('status'),oracle_trade_status=oq.get('status'),
                next_net_R=nq.get('net_R_c1'),oracle_net_R=oq.get('net_R_c1'),
                diagnostic_only=True,economic_pass_allowed=False))
    csv_write(target/'close_oracle_signals.csv',oracle_s);csv_write(target/'close_oracle_trades.csv',oracle_t)
    csv_write(target/'entry_comparison.csv',comparison)
    dump(target/'close_oracle_metrics.json',dict(mode='ENTRY_CLOSE_ORACLE',diagnostic_only=True,economic_pass_allowed=False,
        assumptions='Idealized signal Close fill at signal end; actual next M5 path thereafter; no execution proof. Separate occupancy/funnel.',instruments=ms))
    lines=['# ENTRY_CLOSE_ORACLE vs ENTRY_NEXT_OPEN\n',
        '**Oracle is an idealized diagnostic. It never contributes to Baseline status or economic PASS.**\n',
        'Both scenarios use the same completed signals and structural Stop/limits. Oracle uses signal Close; the trade ledger uses the immediately next Open. Each has its own position occupancy and UNKNOWN path. Entry-bar Take is disabled in both. Prices/Net are never pooled across instruments.\n']
    lines+=table(['Instrument','Next fills','Next CLOSED','Next UNKNOWN','Oracle fills','Oracle CLOSED','Oracle UNKNOWN','Next Net R','Oracle diagnostic Net R'],[
        [s,sum(t['model_filled'] for t in trades if t['instrument']==s),sum(t['status']=='CLOSED' for t in trades if t['instrument']==s),sum(t['status']=='UNKNOWN' for t in trades if t['instrument']==s),
         ms[s]['model_fills'],ms[s]['conditional_closed_only']['closed'],ms[s]['unknown'],closed_metrics([t for t in trades if t['instrument']==s])['Net_R'],ms[s]['conditional_closed_only']['Net_R']] for s in cfg['instruments']])
    lines+=['Full paired directional candidates, refused entries and conditional outcomes: entry_comparison.csv. Oracle profits are hypothetical, and cannot rescue a failed NEXT_OPEN Baseline.\n']
    (target/'Execution_Comparison.md').write_text('\n'.join(lines))


def table(headers,rows):
    def f(v):return '—' if v is None else f'{v:.6f}' if isinstance(v,D) else str(v)
    return ['| '+' | '.join(headers)+' |','|'+'|'.join(['---']*len(headers))+'|',
        *['| '+' | '.join(f(v) for v in r)+' |' for r in rows],'']


def report(output,cfg,freeze,digest,metrics,months,directions,cov):
    lines=['# EQUAL_HIGH_LOW_M5 — A_v1 Baseline 2023','',
        '**Baseline: '+metrics['baseline_status']+'. No Optimization authorized.**','',
        'One fixed family A hypothesis, four instruments, entire available 2023 M5. Profit is after model C1 costs, not confirmed actual commissions. All economics shown are conditional known closures. Incomplete coverage/UNKNOWN prevents full annual PF, Net and continuous equity/DD claims. Incompatible futures price P&L is never summed into portfolio money.','',
        f'Base main `{cfg["base_main"]}`; pre-P&L freeze `{freeze}`; config SHA-256 `{digest}`.','',
        '## Frozen parameters and execution','']
    lines+=table(['Parameter','Value'],list(cfg['parameters'].items()))
    lines+=['Signal M5 must be fully complete. At its end: process previous exposed interval, current Open protection/deadline, signal, then admission and fill at the immediate next M5 Open at that same timestamp. No waiting M5. Only that Open scalar reaches admission/geometry. Stop is never shifted; FULL_NET_C1_R=3 sets gross distance=3s+8t with outward rounding. net_R_c1 uses initial gross risk s; planned full net/net ratio uses s+2t.','',
        'One opportunity per maximal equal-extreme run: consume on first qualifying three-bar window, including busy/rejected/ambiguous cases. Reset only when that extreme changes, or gap/invalid/session/day/tick boundary occurs. Close at the extreme does not qualify; a later first valid three-bar window may qualify once. Cluster ID includes symbol, day, side, run start and historical-grid level. Simultaneous sides are both rejected and consumed. No round-level or indicator filter.','',
        'Inherited approved daytime windows 10:00–14:00 and 14:05–18:50 MSK (dated March lunch adjustment); flat at window end−5m. No extra 17:00 deadline or reserve filter. Hold <=120 calendar minutes. Entry-bar Take remains disabled; Stop permitted, Stop-first on conflict, adverse Stop gaps use actual Open. Missing/invalid next Open is UNKNOWN possible fill, never replaced by later Open. Missing exposed path leaves P&L blank, blocks current day; later days assume conditional FLAT.','',
        '## Signals and admission','']
    ms=metrics['instruments']
    lines+=table(['Instrument','Raw directional','Signals','Ambiguous candidates','Accepted fills','Known refusals','Unknown entries','CLOSED','UNKNOWN','Fills/day'],[
        [s,m['raw_directional_candidates'],m['signals'],m['ambiguous_directional_candidates'],m['model_fills'],m['rejected_known_entries'],m['unknown_entry_attempts'],m['closed'],m['unknown'],m['model_fills_per_available_day']] for s,m in ms.items()])
    lines+=['Raw directional candidates include the two sides of ambiguous M5 events. Signals exclude those ambiguity rejections. Accepted means model fill; orders include submission attempts before Open geometry is resolved.','', '## Conditional C1 economics','']
    lines+=table(['Instrument','Gross price','C1 price','Net price','Gross R','C1 R','Net R','PF price','PF R','Expectancy R','DD R'],[
        [s,*[m['economics'][k] for k in ('gross_price','C1_price','net_price','gross_R','C1_R','net_R')],*[m['conditional_closed_only_C1'][k] for k in ('PF_C1_price','PF_C1_R','Expectancy_R','Max_DD_R')]] for s,m in ms.items()])
    lines+=table(['Instrument','Avg win R','Avg loss R','Avg win price','Avg loss price','Trade days','+ / − months','Largest winner','Top3 winners','Largest + month'],[
        [s,*[m['distribution'][k] for k in ('average_winner_R','average_loser_R','average_winner_price','average_loser_price','unique_trade_days')],f'{m["distribution"]["positive_months"]}/{m["distribution"]["negative_months"]}',*[m['distribution'][k] for k in ('largest_winner_share_R','top_three_winners_share_R','largest_positive_month_share_R')]] for s,m in ms.items()])
    for s,m in ms.items():
        lines += [s+': **'+m['status']+'**; conditional economy **'+m['economic_diagnostic']+'**.',
            'Refusals: `'+json.dumps(m['all_candidate_refusal_reasons'],sort_keys=True)+'`.',
            'Exits: `'+json.dumps(m['conditional_closed_only_C1']['exit_reasons'],sort_keys=True)+'`; UNKNOWN: `'+json.dumps(m['unknown_reasons'],sort_keys=True)+'`.','']
    lines+=['## LONG / SHORT','']
    lines+=table(['Instrument','Side','Signals','Fills','CLOSED','UNKNOWN','Net R','PF price','PF R'],[
        [r['instrument'],r['direction'],r['signals'],r['model_fills'],r['closed'],r['unknown'],r['conditional_Net_R'],r['conditional_PF_C1_price'],r['conditional_PF_C1_R']] for r in directions])
    lines+=['## All twelve calendar months','']
    lines+=table(['Month','Instrument','Signals','Fills','CLOSED','UNKNOWN','Net R','PF price','PF R','Coverage'],[
        [r['month'],r['instrument'],r['signals'],r['model_fills'],r['closed'],r['unknown'],r['conditional_Net_R'],r['conditional_PF_C1_price'],r['conditional_PF_C1_R'],r['coverage_classification']] for r in sorted(months,key=lambda r:(r['month'],cfg['instruments'].index(r['instrument'])))])
    lines+=['## Coverage and limits','']
    lines+=table(['Instrument','Rows','First','Complete / incomplete / pre-inception days','Missing / invalid slots'],[
        [r['instrument'],r['source_rows_2023'],r['first'],f'{r["complete_days"]}/{r["incomplete_days"]}/{r["pre_inception_days"]}',f'{r["missing_bars"]}/{r["invalid_bars"]}'] for r in cov])
    lines+=['Only four exact read-only 2023 prefixes from `'+cfg['source_ref']+'`. CNY tick 0.01 → 0.001 from 2023-09-27 19:00 MSK. Zero price bytes 2024+ read. Source/grid receipts in input_provenance.json and validation.json. Real execution/funding/margin/capital are unproved; normalized research only.','',
        'Implementation-independent backward-run/forward-path auditor, coverage and CSV economics: Independent_Audit.md and audit.json. Byte repeats, default-mode regressions and protected-file receipts: validation.json. This is task-agent algorithmic audit, not external human signoff.','',
        'ENTRY_CLOSE_ORACLE is isolated under diagnostics/. It uses an idealized signal Close and can never qualify economic PASS. Its metrics are excluded from this report and Baseline classification.','',
        '## Allowed next action','',
        'STOP after this first Baseline and Draft PR without merge. Review the audit and limitations; negative C1 expectancy has NO ECONOMIC BASELINE PASS and cannot advance to Optimization. No automatic new candidate. B 4/7/10 (eventually 4–10), C separate approaches, touch/Stop/Take 2/3/5/7/10R optimization, trailing, MTF and filters remain documented future tasks only. 2024 WF and 2025+ TRUE OOS remain closed.','']
    (output/'Baseline_Report.md').write_text('\n'.join(lines))


def run(data_root,output):
    check_output(output);cfg,freeze,digest=verify_freeze();protected_check(data_root,cfg)
    rules=MarketRules(cfg)
    with bounded_reads(data_root,cfg) as read_guard:
        raw,receipts=load_market_data(data_root,cfg,rules)
    output.mkdir(parents=True,exist_ok=True)
    engine=Backtester(rules,entry_mode=cfg['execution']['entry_mode'],
        allow_entry_bar_take=cfg['execution']['allow_entry_bar_take'],
        cost_ticks_per_side=cfg['execution']['cost_ticks_per_side'])
    ss=[];tt=[];dd=[];cc=[];gg=[];months=[];instruments=[];directions=[];cov_summary=[];metrics={}
    for symbol in cfg['instruments']:
        signals,trades,days=engine.run(EqualHighLowM5(cfg['parameters']),symbol,raw[symbol],
            start=date.fromisoformat(cfg['start']),end_exclusive=date.fromisoformat(cfg['end_exclusive']))
        source,gaps=coverage(symbol,raw[symbol],cfg,rules)
        ss.extend(signals);tt.extend(trades);dd.extend(days);cc.extend(source);gg.extend(gaps)
        metrics[symbol]=assessed(trades,signals,source,cfg)
        instruments.append(row(symbol,trades,signals,source,cfg))
        for month in range(1,13):
            label=f'2023-{month:02d}'
            months.append(row(symbol,[t for t in trades if str(t['signal_at']).startswith(label)],
                [s for s in signals if s['date'].startswith(label)],[c for c in source if c['date'].startswith(label)],cfg,month=label))
        for side in (-1,1):
            directions.append(row(symbol,[t for t in trades if t['direction']==side],
                [s for s in signals if s['direction']==side],source,cfg,direction='LONG' if side==1 else 'SHORT'))
        cov_summary.append(dict(instrument=symbol,source_rows_2023=len(raw[symbol]),first=str(min(raw[symbol])),last=str(max(raw[symbol])),
            complete_days=sum(c['status']=='COMPLETE' for c in source),incomplete_days=sum(c['status']=='INCOMPLETE' for c in source),
            pre_inception_days=sum(c['status']=='PRE_INCEPTION' for c in source),missing_bars=sum(c['missing_bars'] for c in source),invalid_bars=sum(c['invalid_bars'] for c in source)))
    for name,rows in [('signals',ss),('trades',tt),('days',dd),('coverage_daily',cc),('coverage_events',gg),('monthly_report',months),
                      ('instrument_report',instruments),('direction_report',directions),('coverage_summary',cov_summary),
                      ('rejected_entries',[s for s in ss if not s['model_filled']]),('unknown_report',[t for t in tt if t['status']=='UNKNOWN'])]:
        csv_write(output/(name+'.csv'),rows)
    totals={k:sum(m[k] for m in metrics.values()) for k in ('raw_directional_candidates','signals','ambiguous_directional_candidates','model_fills','rejected_known_entries','unknown_entry_attempts','closed','unknown')}
    status='INCONCLUSIVE' if any(not m['annual_complete'] for m in metrics.values()) else 'NO ECONOMIC BASELINE PASS' if any(m['status']=='NO ECONOMIC BASELINE PASS' for m in metrics.values()) else 'BASELINE_REQUIRES_EVIDENCE_REVIEW'
    doc=dict(strategy=cfg['strategy'],version='A_v1',entry_mode='ENTRY_NEXT_OPEN',baseline_status=status,
        research_phase='BASELINE',optimization_allowed=False,totals_counts_only=totals,
        instruments=metrics,pooled_price_portfolio=None,oracle_used_for_classification=False)
    dump(output/'metrics.json',doc);dump(output/'funnel.json',dict(totals_counts_only=totals,instruments={s:{k:m[k] for k in ('signals','model_fills','rejected_known_entries','unknown_entry_attempts','closed','unknown','all_candidate_refusal_reasons')} for s,m in metrics.items()}))
    dump(output/'input_provenance.json',dict(source_ref=cfg['source_ref'],instruments=receipts,actual_python_read_guard=read_guard))
    dump(output/'manifest.json',dict(base_main=cfg['base_main'],pre_pnl_freeze_commit=freeze,config_sha256=digest,
        source_ref=cfg['source_ref'],execution_code_sha256=cfg['execution_code_sha256'],parameters_changed_after_pnl=False,
        oracle_diagnostic_only=True,pr_472_head_unchanged=cfg['pr_472_head'],scope_manifest=cfg['scope_manifest']))
    diagnostic(raw,ss,tt,cfg,output);report(output,cfg,freeze,digest,doc,months,directions,cov_summary)
    return doc


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--data-root',type=Path,required=True);p.add_argument('--output',type=Path,default=OUT)
    a=p.parse_args();r=run(a.data_root,a.output);print(json.dumps(dict(status=r['baseline_status'],counts=r['totals_counts_only']),sort_keys=True))
