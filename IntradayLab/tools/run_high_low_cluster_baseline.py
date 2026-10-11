#!/usr/bin/env python3
"""Exactly one frozen B duration, existing common NEXT_OPEN engine, no Oracle."""
import argparse
from collections import Counter
from datetime import date
from decimal import Decimal as D
import json
from pathlib import Path
import sys
ROOT=Path(__file__).resolve().parents[2];sys.path.insert(0,str(ROOT))
from IntradayLab.core.backtester import Backtester
from IntradayLab.core.calendar import MarketRules
from IntradayLab.core.data_loader import load_market_data
from IntradayLab.core.reports import csv_write,dump,coverage
from IntradayLab.strategies.high_low_cluster_m5 import HighLowClusterM5
from IntradayLab.tools.run_equal_high_low_baseline import assessed as base_assessed, row as base_row, table
from IntradayLab.tools.high_low_cluster_contract import LAB,verify_freeze,check_output,output_path,bounded_reads,protected_check


def mean(values):
    return sum(values,D(0))/len(values) if values else None


def assessed(trades,signals,source,cfg):
    m=base_assessed(trades,signals,source,cfg)
    fills=[t for t in trades if t['model_filled']];closed=[t for t in trades if t['status']=='CLOSED']
    m.update(detected_accumulations=len(signals),unique_detected_episodes=len({s['episode_id'] for s in signals}),
        ambiguous_directional_candidates=sum(s['base_reason']=='AMBIGUOUS_BOTH_SIDES' for s in signals),
        close_at_boundary_candidates=sum(s['base_reason']=='CLOSE_AT_BOUNDARY' for s in signals))
    m['geometry']=dict(mean_stop_ticks=mean([t['risk']/t['entry_tick'] for t in fills]),
        mean_C1_initial_risk_R=mean([t['planned_C1']/t['risk'] for t in fills]),
        min_C1_initial_risk_R=min((t['planned_C1']/t['risk'] for t in fills),default=None),
        max_C1_initial_risk_R=max((t['planned_C1']/t['risk'] for t in fills),default=None),
        mean_entry_distance_ticks=mean([t['entry_distance_ticks'] for t in fills]),
        mean_directional_open_vs_signal_close_ticks=mean([t['open_vs_close_ticks'] for t in fills]),
        mean_target_distance_ticks=mean([t['rounded_take_distance']/t['entry_tick'] for t in fills]),
        mean_known_holding_lower_minutes=mean([t['holding_lower_minutes'] for t in closed]),
        mean_known_holding_upper_minutes=mean([t['holding_upper_minutes'] for t in closed]),
        stop_ticks_histogram=dict(sorted(Counter(str(t['risk']/t['entry_tick']) for t in fills).items())),
        boundary_touch_histogram=dict(sorted(Counter(str(s['boundary_touches']) for s in signals).items())))
    m['loss_attribution']={reason:dict(count=len(rows),gross_R=sum((t['gross_R'] for t in rows),D(0)),
        cost_R=sum((t['cost_R'] for t in rows),D(0)),net_R=sum((t['net_R_c1'] for t in rows),D(0)),
        mean_holding_lower_minutes=mean([t['holding_lower_minutes'] for t in rows]),
        mean_holding_upper_minutes=mean([t['holding_upper_minutes'] for t in rows]))
        for reason in ('STOP','TAKE','TIME','SESSION_FLAT')
        for rows in [[t for t in closed if t['exit_reason']==reason]]}
    return m


def report_row(symbol,trades,signals,source,cfg,**labels):
    r=base_row(symbol,trades,signals,source,cfg,**labels);m=assessed(trades,signals,source,cfg)
    r.update({k:m[k] for k in ('detected_accumulations','unique_detected_episodes',
        'ambiguous_directional_candidates','close_at_boundary_candidates')})
    r.update(m['geometry'])
    return r


def report(output,cfg,freeze,digest,doc,months,rounds,touches,cov):
    n=cfg['parameters']['cluster_bars'];ms=doc['instruments']
    lines=[f'# HIGH_LOW_CLUSTER_M5 — B{n}_v1 Baseline 2023','',
        f'**{doc["baseline_status"]}**. Экономический диагноз известных закрытий указан отдельно. Optimization не разрешена.','',
        f'Base `{cfg["base_main"]}`; freeze `{freeze}`; config SHA-256 `{digest}`; source `{cfg["source_ref"]}`. Pre-P&L unittest: **{cfg.get("pre_pnl_unittest_count")} PASS**.','',
        'Все результаты после модельных издержек C1. UNKNOWN не имеет выдуманного P&L. Ценовые единицы разных инструментов не суммируются. DD известных закрытий условна и не является непрерывной кривой брокерского счёта.','',
        '## Замороженные правила','']
    lines+=table(['Parameter','Value'],list(cfg['parameters'].items()))
    lines+=['Первое сформированное окно из N завершённых M5 обрабатывается один раз внутри причинного эпизода с общим диапазоном <=3 исторических тиков. Ширина окна 1–3, >=2 экстремума на внешней границе; нулевая ширина исключена. CLOSE_AT_BOUNDARY также расходует эпизод, сигнал не формирует. При двух допустимых направлениях оба отклонены. ID эпизода одинаков для B4/B7/B10; cluster_id включает модель. Не считать выборки независимыми. Полные сбросы и окончания: episodes.csv; причинные характеристики на момент формирования: signals.csv.','',
        'NEXT_OPEN — Open непосредственно следующей M5, совпадает по времени с завершением сигнальной. Stop: граница +/- один тик, без переноса. Риск 3–12 тиков и удаление 0–4 тика проверяются по фактическому Open. Совместно эти правила дают допустимый риск **3–5 тиков**, C1/R **0,40–0,667**. Take gross distance=3s+8t, то есть **17–23 тика** при допустимом риске; полный плановый net/net RR=3. Hold <=120 календарных минут, flat за M5 до конца окна. Stop-first, Stop-gap по Open, Take на входной свече запрещён. Общий Backtester не изменён.','',
        'Сессии 10:00–14:00, 14:05–18:50 MSK; 13–20 марта PM с 14:15. Round grid: USD 0,10 RUB и CNY 0,05 RUB из ROADMAP; GLD 10 RUB/грамм, IMOEX 10 индексных пунктов как фиксированные десятичные ориентиры. ROUND_NEAR: внешняя граница <=1 исторического тика от ближайшего узла, остальные ORDINARY_FAR; ближайший при равенстве — больший узел. Это диагностические разрезы без фильтра входа.','',
        '## Накопления и входы','']
    lines+=table(['Instrument','Detected','Signals','Fills','Refused','Unknown entry','CLOSED','UNKNOWN','Fills/day'],[
        [s,m['detected_accumulations'],m['signals'],m['model_fills'],m['rejected_known_entries'],m['unknown_entry_attempts'],m['closed'],m['unknown'],m['model_fills_per_available_day']] for s,m in ms.items()])
    lines+=['## Условная экономика известных закрытий','']
    lines+=table(['Instrument','Gross R','C1 R','Net R','Net price','PF R','PF price','WR','E[R]','DD R','+ / − months'],[
        [s,m['economics']['gross_R'],m['economics']['C1_R'],m['economics']['net_R'],m['economics']['net_price'],
         m['conditional_closed_only_C1']['PF_C1_R'],m['conditional_closed_only_C1']['PF_C1_price'],
         m['conditional_closed_only_C1']['Win_Rate'],m['conditional_closed_only_C1']['Expectancy_R'],
         m['conditional_closed_only_C1']['Max_DD_R'],f'{m["distribution"]["positive_months"]}/{m["distribution"]["negative_months"]}'] for s,m in ms.items()])
    lines+=table(['Instrument','Avg win R','Avg loss R','Stop mean ticks','C1/risk mean','Trade days','Largest winner share','Largest + month share'],[
        [s,m['distribution']['average_winner_R'],m['distribution']['average_loser_R'],m['geometry']['mean_stop_ticks'],m['geometry']['mean_C1_initial_risk_R'],m['distribution']['unique_trade_days'],m['distribution']['largest_winner_share_R'],m['distribution']['largest_positive_month_share_R']] for s,m in ms.items()])
    for symbol,m in ms.items():
        lines += [f'### {symbol}: {m["status"]}; известные закрытия: {m["economic_diagnostic"]}','',
            'Причины всех отказов: `'+json.dumps(m['all_candidate_refusal_reasons'],sort_keys=True)+'`.','',
            'UNKNOWN: `'+json.dumps(m['unknown_reasons'],sort_keys=True)+'`.','']
        lines+=table(['Exit','Count','Gross R','C1 R','Net R','Mean hold lower / upper min'],[
            [k,v['count'],v['gross_R'],v['cost_R'],v['net_R'],f'{v["mean_holding_lower_minutes"]} / {v["mean_holding_upper_minutes"]}'] for k,v in m['loss_attribution'].items()])
        lines+=['Риск мал относительно C1; для TAKE требуется пройти значительно больше первоначального Stop. STOP вносит отрицательные исходы; C1 дополнительно вычитается из всех закрытий. TIME/SESSION_FLAT показывают недостижение Take до срока; их P&L приведён отдельно. Поздний Open оценивается только по наблюдаемому смещению и отказам, без контрфактического заявления, что вход по Close был исполним или прибыльнее.','']
    lines+=['## Календарные месяцы','']
    lines+=table(['Instrument','Month','CLOSED','UNKNOWN','Net R known','Coverage'],[
        [r['instrument'],r['month'],r['closed'],r['unknown'],r['conditional_Net_R'],r['coverage_classification']] for r in months])
    lines+=['До появления инструмента NO_COVERAGE — не нулевая доходность. Все 12 календарных месяцев присутствуют; нулевые торговые месяцы с историей отражены отдельно от отсутствующей истории.','', '## Круглые и обычные уровни','']
    lines+=table(['Instrument','Level','Detected','Fills','CLOSED','UNKNOWN','Net R','PF R','PF price'],[
        [r['instrument'],r['level_type'],r['detected_accumulations'],r['model_fills'],r['closed'],r['unknown'],r['conditional_Net_R'],r['conditional_PF_C1_R'],r['conditional_PF_C1_price']] for r in rounds])
    lines+=['## Реальные касания внешней границы','']
    lines+=table(['Instrument','Touches','Detected','Fills','CLOSED','UNKNOWN','Net R','PF R'],[
        [r['instrument'],r['boundary_touches'],r['detected_accumulations'],r['model_fills'],r['closed'],r['unknown'],r['conditional_Net_R'],r['conditional_PF_C1_R']] for r in touches])
    lines+=['LONG/SHORT и средние победа/убыток в R и ценах — direction_report.csv и instrument_report.csv. Удаление Close/Open и все исходные экстремумы — signals.csv; holding нижняя/верхняя границы учитывают неизвестное внутрисвечное время выхода.','', '## Полнота данных','']
    lines+=table(['Instrument','Rows','First','Complete / incomplete / pre-inception','Missing / invalid'],[
        [r['instrument'],r['source_rows_2023'],r['first'],f'{r["complete_days"]}/{r["incomplete_days"]}/{r["pre_inception_days"]}',f'{r["missing_bars"]}/{r["invalid_bars"]}'] for r in cov])
    lines+=['Только четыре точных префикса 2023, ноль ценовых байтов 2024+. GLD с 11 июля, IMOEX с 14 ноября; CNY тик 0,01 → 0,001 с 27 сентября 19:00 MSK. UNKNOWN блокирует текущий день; последующие дни используют явное предположение FLAT. Годовые PF/Net/DD остаются null при неполных данных. Независимый алгоритмический аудит не импортирует торговую стратегию или Backtester; это не внешний человеческий signoff. Проверки: audit.json, validation.json, artifact_hashes.json.','',
        'STOP после B4/B7/B10. Нет Optimization, Robustness, WF, TRUE OOS, модели C, новых фильтров или автоматического Merge.','']
    (output/'Baseline_Report.md').write_text('\n'.join(lines))


def run(data_root,output,n):
    cfg,freeze,digest=verify_freeze(n);check_output(output,n);protected_check(data_root,cfg)
    rules=MarketRules(cfg)
    with bounded_reads(data_root,cfg) as reads:
        raw,receipts=load_market_data(data_root,cfg,rules)
    output.mkdir(parents=True,exist_ok=True)
    ss=[];tt=[];cc=[];gg=[];dd=[];episodes=[];months=[];directions=[];rounds=[];touches=[];instruments=[];cov_summary=[];metrics={}
    engine=Backtester(rules,entry_mode='ENTRY_NEXT_OPEN',allow_entry_bar_take=False,cost_ticks_per_side=1)
    for symbol in cfg['instruments']:
        strategy=HighLowClusterM5(cfg['parameters'])
        signals,trades,days=engine.run(strategy,symbol,raw[symbol],start=date(2023,1,1),end_exclusive=date(2024,1,1))
        by_id={s['signal_id']:s for s in signals}
        for s in signals:
            op=s.get('entry_open')
            s['entry_distance_ticks']=s['direction']*(op-s['cluster_level'])/s['entry_tick'] if op is not None else None
            s['open_vs_close_ticks']=s['direction']*(op-s['signal_close'])/s['entry_tick'] if op is not None else None
        for t in trades:
            s=by_id[t['signal_id']]
            for k in ('episode_id','level_type','boundary_touches','cluster_bars','cluster_min','cluster_max',
                'cluster_width_ticks','cluster_level','round_distance_ticks','signal_close','entry_distance_ticks','open_vs_close_ticks'):
                t[k]=s[k]
            t['holding_lower_minutes']=D(str((t['exit_interval_start']-t['entry_at']).total_seconds()/60)) if t['status']=='CLOSED' else None
            t['holding_upper_minutes']=D(str((t['exit_interval_end']-t['entry_at']).total_seconds()/60)) if t['status']=='CLOSED' else None
        source,gaps=coverage(symbol,raw[symbol],cfg,rules)
        ss.extend(signals);tt.extend(trades);dd.extend(days);cc.extend(source);gg.extend(gaps);episodes.extend(strategy.episode_records)
        metrics[symbol]=assessed(trades,signals,source,cfg)
        instruments.append(report_row(symbol,trades,signals,source,cfg))
        for month in range(1,13):
            label=f'2023-{month:02d}'
            months.append(report_row(symbol,[t for t in trades if str(t['signal_at'])[:7]==label],[s for s in signals if s['date'][:7]==label],[c for c in source if c['date'][:7]==label],cfg,month=label))
        for side in (-1,1):
            directions.append(report_row(symbol,[t for t in trades if t['direction']==side],[s for s in signals if s['direction']==side],source,cfg,direction='LONG' if side==1 else 'SHORT'))
        for level_type in ('ALL','ROUND_NEAR','ORDINARY_FAR'):
            rounds.append(report_row(symbol,[t for t in trades if level_type=='ALL' or t['level_type']==level_type],[s for s in signals if level_type=='ALL' or s['level_type']==level_type],source,cfg,level_type=level_type))
        for count in range(2,n):
            touches.append(report_row(symbol,[t for t in trades if t['boundary_touches']==count],[s for s in signals if s['boundary_touches']==count],source,cfg,boundary_touches=count))
        cov_summary.append(dict(instrument=symbol,source_rows_2023=len(raw[symbol]),first=str(min(raw[symbol])),last=str(max(raw[symbol])),complete_days=sum(c['status']=='COMPLETE' for c in source),incomplete_days=sum(c['status']=='INCOMPLETE' for c in source),pre_inception_days=sum(c['status']=='PRE_INCEPTION' for c in source),missing_bars=sum(c['missing_bars'] for c in source),invalid_bars=sum(c['invalid_bars'] for c in source)))
    files=dict(signals=ss,trades=tt,episodes=episodes,days=dd,coverage_daily=cc,coverage_events=gg,monthly_report=months,
        instrument_report=instruments,direction_report=directions,round_report=rounds,boundary_touch_report=touches,
        coverage_summary=cov_summary,rejected_entries=[s for s in ss if not s['model_filled']],unknown_report=[t for t in tt if t['status']=='UNKNOWN'])
    for name,rows in files.items():csv_write(output/(name+'.csv'),rows)
    totals={k:sum(m[k] for m in metrics.values()) for k in ('detected_accumulations','signals','model_fills','rejected_known_entries','unknown_entry_attempts','closed','unknown')}
    status='INCONCLUSIVE' if any(not m['annual_complete'] for m in metrics.values()) else 'NO ECONOMIC BASELINE PASS' if any(m['status']=='NO ECONOMIC BASELINE PASS' for m in metrics.values()) else 'BASELINE_REQUIRES_EVIDENCE_REVIEW'
    doc=dict(strategy=cfg['strategy'],version=f'B{n}_v1',entry_mode='ENTRY_NEXT_OPEN',baseline_status=status,research_phase='BASELINE',optimization_allowed=False,totals_counts_only=totals,instruments=metrics,pooled_price_portfolio=None)
    dump(output/'metrics.json',doc);dump(output/'config.json',cfg)
    dump(output/'input_provenance.json',dict(source_ref=cfg['source_ref'],instruments=receipts,actual_python_read_guard=reads))
    dump(output/'manifest.json',dict(base_main=cfg['base_main'],pre_pnl_freeze_commit=freeze,config_sha256=digest,source_ref=cfg['source_ref'],execution_code_sha256=cfg['execution_code_sha256'],parameters_changed_after_pnl=False,all_three_frozen_together=True))
    report(output,cfg,freeze,digest,doc,months,rounds,touches,cov_summary)
    return doc


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--data-root',type=Path,required=True);p.add_argument('--bars',type=int,choices=(4,7,10),required=True);p.add_argument('--output',type=Path)
    a=p.parse_args();m=run(a.data_root,a.output or output_path(a.bars),a.bars);print(json.dumps(dict(model=m['version'],status=m['baseline_status'],counts=m['totals_counts_only']),sort_keys=True))
