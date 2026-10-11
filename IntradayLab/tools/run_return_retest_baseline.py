"""One frozen C_v1 run through the unchanged common Backtester."""
import argparse
from collections import Counter
from datetime import date
from decimal import Decimal as D
from pathlib import Path
from IntradayLab.core.backtester import Backtester
from IntradayLab.core.calendar import MarketRules
from IntradayLab.core.data_loader import load_market_data
from IntradayLab.core.data_quality import DataQualityResult
from IntradayLab.core.metrics import closed_metrics, distribution_metrics
from IntradayLab.core.reports import csv_write, dump, write_data_quality_reports
from IntradayLab.strategies.return_retest_rejection_m5 import ReturnRetestRejectionM5
from IntradayLab.tools.return_retest_contract import OUT, verify_freeze, check_output, protected_check, bounded_reads


def total(values):
    return sum(values, D(0))


def diagnostic(trades, pooled=False):
    m = closed_metrics(trades)
    m.update(Gross_R=total(t['gross_R'] for t in trades), Cost_R=total(t['cost_R'] for t in trades))
    if pooled:
        for k in ('PF_C1_price', 'Net_price', 'cost_C1'):
            m[k] = None
    return m


def stats(values):
    return dict(count=len(values), minimum=min(values) if values else None,
        maximum=max(values) if values else None, mean=total(values)/len(values) if values else None,
        histogram=dict(sorted(Counter(str(v) for v in values).items())))


def count_summary(ss, tt, xx, ee):
    return dict(first_approaches=sum(e['event']=='FIRST' for e in ee),
        second_approaches=sum(e['event']=='SECOND' for e in ee),
        third_approaches=sum(e['event']=='THIRD' for e in ee),
        signals=sum(s['base_reason']=='SIGNAL' for s in ss),
        signals_LONG=sum(s['base_reason']=='SIGNAL' and s['direction']==1 for s in ss),
        signals_SHORT=sum(s['base_reason']=='SIGNAL' and s['direction']==-1 for s in ss),
        detected_candidates=len(ss), refusals=sum(s['status'] in ('REJECTED','NONFILL') for s in ss),
        skips=sum(s['status']=='DATA_GAP_SKIP' for s in ss),
        accepted_entries=sum(s['model_filled'] for s in ss), closed=len(tt), excluded=len(xx))


def research_metrics(result, events, coverage):
    instruments = {}
    for symbol in sorted({c['instrument'] for c in coverage}):
        ss=[s for s in result.signals if s['instrument']==symbol]
        tt=[t for t in result.trades if t['instrument']==symbol]
        xx=[t for t in result.data_quality_exclusions if t['instrument']==symbol]
        ee=[e for e in events if e['instrument']==symbol]
        cc=[c for c in coverage if c['instrument']==symbol]
        counts=count_summary(ss,tt,xx,ee)
        fills=tt+xx
        d=distribution_metrics(tt)
        e=diagnostic(tt)
        instruments[symbol]=dict(counts=counts, economics=e, distribution=d,
            exclusion_fraction=D(len(xx))/len(fills) if fills else None,
            refusal_reasons=dict(sorted(Counter(s['reason'] for s in ss if s['reason']).items())),
            reset_reasons=dict(sorted(Counter(e.get('reason') for e in ee if e['event']=='RESET').items())),
            geometry=dict(retreat_depth_ticks=stats([v for s in ss for v in s['retreat_depth_ticks']]),
                approach_separation_bars=stats([v for s in ss for v in s['approach_separation_bars']]),
                observed_touch_width_ticks=stats([s['observed_touch_width_ticks'] for s in ss]),
                allowed_zone_width_ticks=4, stop_ticks=stats([t['risk']/t['entry_tick'] for t in fills])),
            exit_attribution={reason:dict(count=len(rows), Gross_R=total(t['gross_R'] for t in rows),
                Cost_R=total(t['cost_R'] for t in rows), Net_R=total(t['net_R_c1'] for t in rows))
                for reason in ('STOP','TAKE','TIME','SESSION_FLAT')
                for rows in [[t for t in tt if t['exit_reason']==reason]]},
            loss_attribution={reason:dict(count=len(rows), Net_R=total(t['net_R_c1'] for t in rows))
                for reason in ('STOP','TAKE','TIME','SESSION_FLAT')
                for rows in [[t for t in tt if t['exit_reason']==reason and t['net_R_c1']<0]]},
            coverage=dict(complete_days=sum(c['status']=='COMPLETE' for c in cc),
                incomplete_days=sum(c['status']=='INCOMPLETE' for c in cc),
                pre_inception_days=sum(c['status']=='PRE_INCEPTION' for c in cc),
                expected_bars=sum(c['expected_bars'] for c in cc), valid_bars=sum(c['valid_bars'] for c in cc),
                missing_bars=sum(c['missing_bars'] for c in cc), invalid_bars=sum(c['invalid_bars'] for c in cc)),
            technical_correctness='PENDING_INDEPENDENT_AUDIT',
            conditional_economics='NEGATIVE_AFTER_C1' if e['Expectancy_R'] is not None and e['Expectancy_R']<=0 else 'POSITIVE_CONDITIONAL' if tt else 'NO_CLOSED_EVIDENCE',
            data_sufficiency='INCOMPLETE_SOURCE_OR_OUTCOMES' if xx or any(c['status']!='COMPLETE' for c in cc) else 'COMPLETE_MODEL_COHORT',
            prospective_optimization='TECHNICALLY_REVIEWABLE; common eligibility thresholds and separate approval required; low initial PF is not a veto')
    pooled=diagnostic(result.trades,pooled=True)
    dist=distribution_metrics(result.trades)
    for key in ('average_winner_price','average_loser_price'):
        dist[key]=None
    return dict(instruments=instruments, totals=count_summary(result.signals,result.trades,result.data_quality_exclusions,events),
        pooled_normalized_R=pooled, pooled_R_distribution=dist,
        pooled_price_PF=None, continuous_equity=None, annual_account_returns=None,
        scope='Known closed outcomes, normalized initial-risk units; no cash portfolio or continuous equity',
        optimization_executed=False, minimum_optimization_sample_rules='Not selected in this Baseline')


def calendar_rows(result, events, cov, symbols):
    output=[]
    for symbol in symbols+['ALL_R_DIAGNOSTIC']:
        for month in range(1,13):
            label=f'2023-{month:02d}'
            match=lambda r: (symbol=='ALL_R_DIAGNOSTIC' or r['instrument']==symbol)
            ss=[s for s in result.signals if match(s) and s['date'][:7]==label]
            tt=[t for t in result.trades if match(t) and str(t['signal_at'])[:7]==label]
            xx=[t for t in result.data_quality_exclusions if match(t) and str(t['signal_at'])[:7]==label]
            ee=[e for e in events if match(e) and str(e['observed_at'])[:7]==label]
            cc=[c for c in cov if match(c) and c['date'][:7]==label]
            observed=any(c['valid_bars'] for c in cc)
            status='NO_COVERAGE' if not observed else 'PARTIAL_DATA' if xx or any(c['status']!='COMPLETE' for c in cc) else 'COMPLETE'
            econ=diagnostic(tt,pooled=symbol=='ALL_R_DIAGNOSTIC')
            econ.pop('closed')
            if not observed:
                econ={k:None for k in econ}
            output.append(dict(instrument=symbol, month=label, coverage_status=status,
                **count_summary(ss,tt,xx,ee), **econ))
    return output


def table(headers, rows):
    return ['| '+' | '.join(headers)+' |','| '+' | '.join(['---']*len(headers))+' |']+[
        '| '+' | '.join(str(v) if v is not None else 'null' for v in r)+' |' for r in rows]


def report(output, cfg, manifest, research, months):
    lines=['# RETURN_RETEST_REJECTION_M5 / C_v1 / Baseline 2023','',
        'Результат после модельных издержек C1; только известные CLOSED. Неполные исходы могут смещать PF.','',
        f'Base `{cfg["base_main"]}`; pre-P&L freeze `{manifest["pre_pnl_freeze_commit"]}`; config SHA-256 `{manifest["config_sha256"]}`.','',
        'Торговая логика, исполнение, runner и независимый аудит заморожены до первого исторического P&L. Общий Backtester не изменён.','',
        '## Конфигурация','']+table(['Параметр','Значение'],cfg['parameters'].items())
    lines+=['', 'Детальные правила и разрешение неоднозначностей: [preregistration](../../reports/RETURN_RETEST_C_V1_PREREGISTRATION.md). NEXT_OPEN, DATA_GAP_SKIP_V2, C1 один датированный тик на сторону; Stop-first/Stop-gap, без Take на входной свече, flat за M5 до конца окна.','',
        '## Экономика известных закрытий','']
    lines+=table(['Инструмент','CLOSED','SKIP','EXCLUDED','Gross R','Cost R','Net R','PF R','PF price','WR','E[R]','DD R'],[
        [s,m['counts']['closed'],m['counts']['skips'],m['counts']['excluded'],*[m['economics'][k] for k in ('Gross_R','Cost_R','Net_R','PF_C1_R','PF_C1_price','Win_Rate','Expectancy_R','Max_DD_R')]] for s,m in research['instruments'].items()])
    lines+=['', 'Суммарные результаты — research_metrics.json: только счётчики и нормализованные R; общий ценовой PF отсутствует. DD — максимальная наблюдаемая просадка известных закрытий, не непрерывная equity при EXCLUDED.','', '## Подходы и сигналы','']
    lines+=table(['Инструмент','Первый','Второй','Третий','LONG','SHORT','Входы','Отказы','Дни сделок','Активные месяцы'],[
        [s,*[m['counts'][k] for k in ('first_approaches','second_approaches','third_approaches','signals_LONG','signals_SHORT','accepted_entries','refusals')],m['distribution']['unique_trade_days'],m['distribution']['active_months']] for s,m in research['instruments'].items()])
    for s,m in research['instruments'].items():
        lines+=['',f'## {s}','',f'Условная экономика: **{m["conditional_economics"]}**. Данные: **{m["data_sufficiency"]}**.','',
            'Отказы: `'+str(m['refusal_reasons'])+'`.','',
            'Средние победа/убыток, концентрация, откаты, интервалы подходов, ширина зоны и Stop: research_metrics.json; полные исходные значения: signals.csv и construction_events.csv.','']
        lines+=table(['Выход','Число','Gross R','Cost R','Net R'],[[k,v['count'],v['Gross_R'],v['Cost_R'],v['Net_R']] for k,v in m['exit_attribution'].items()])
        lines+=['', 'STOP означает движение к структурному Stop, в том числе неблагоприятный gap. TIME/SESSION_FLAT — выход до достижения Take; C1 уменьшает каждый известный результат. Разрез именно убыточных закрытий сохранён в loss_attribution; причинность рыночного режима из этих данных не утверждается.','']
    lines+=['## Все календарные месяцы','']+table(['Инструмент','Месяц','CLOSED','SKIP','EXCLUDED','Net R','Полнота'],[
        [r['instrument'],r['month'],r['closed'],r['skips'],r['excluded'],r['Net_R'],r['coverage_status']] for r in months])
    lines+=['', 'NO_COVERAGE до начала истории не является нулевой доходностью; месяцы с историей и без сделок имеют нулевую известную сумму. Coverage_report содержит каждый календарный исследовательский день/слот, включая PRE_INCEPTION.','',
        '## Оценка и границы','',
        'Технический итог и детерминизм — validation.json и audit.json. Число CLOSED, торговые дни и активные месяцы раскрыты отдельно. Пригодность к будущей Optimization технически проверяема после PASS аудита; достаточность выборки требует общих порогов, заданных до будущего ранжирования. Низкий исходный PF не отвергает семейство C. Отрицательная условная экономика не объявляется прибыльной.','',
        'A_v1 и B4/B7/B10 — разные конструкции; их неизменные UNKNOWN и результаты сравниваются отдельно в Comparison.md. Совпадения сигналов не складываются в независимые сделки.','',
        'Источник pinned 2023 M5, ноль прочитанных ценовых байтов 2024+. USDRUBF/CNYRUBF с 3 января, GLDRUBF с 11 июля, IMOEXF с 14 ноября. После EXCLUDED текущий день блокируется; последующие независимые дни явно условно FLAT. Обычный trades.csv содержит только CLOSED.','',
        'STOP после Baseline C. Optimization, Robustness, WF, TRUE OOS и следующие стратегии не выполнялись; Draft PR без merge/auto-merge.','']
    (output/'Baseline_Report.md').write_text('\n'.join(lines))


def run(data_root, output):
    cfg, freeze, digest=verify_freeze()
    check_output(output); protected_check(data_root,cfg)
    rules=MarketRules(cfg)
    with bounded_reads(data_root,cfg) as reads:
        data, provenance=load_market_data(data_root,cfg,rules)
    combined=DataQualityResult([],[],[],[],[]); events=[]
    for symbol in cfg['instruments']:
        strategy=ReturnRetestRejectionM5(cfg['parameters'])
        result=Backtester(rules,**cfg['execution']).run(strategy,symbol,data[symbol],
            start=date(2023,1,1),end_exclusive=date(2024,1,1))
        for name in ('signals','trades','days','data_gap_skips','data_quality_exclusions'):
            getattr(combined,name).extend(getattr(result,name))
        events.extend(strategy.construction_events)
    combined.validate()
    write_data_quality_reports(output,combined,data,cfg,rules)
    from IntradayLab.core.reports import data_quality_coverage
    cov=data_quality_coverage(data,cfg,rules,combined)
    research=research_metrics(combined,events,cov)
    months=calendar_rows(combined,events,cov,cfg['instruments'])
    csv_write(output/'construction_events.csv',events)
    csv_write(output/'days.csv',combined.days)
    csv_write(output/'monthly_report.csv',months)
    directions=[]
    for symbol in cfg['instruments']:
        for side in (-1,1):
            trades=[t for t in combined.trades if t['instrument']==symbol and t['direction']==side]
            directions.append(dict(instrument=symbol,direction=side,**diagnostic(trades),**distribution_metrics(trades)))
    csv_write(output/'direction_report.csv',directions)
    dump(output/'research_metrics.json',research)
    dump(output/'input_provenance.json',dict(source_ref=cfg['source_ref'],instruments=provenance,actual_python_read_guard=reads))
    manifest=dict(base_main=cfg['base_main'],pre_pnl_freeze_commit=freeze,config_sha256=digest,
        execution_code_sha256=cfg['execution_code_sha256'],parameters_changed_after_pnl=False,
        entry_mode='ENTRY_NEXT_OPEN',data_gap_policy='DATA_GAP_SKIP_V2',research_phase='BASELINE')
    dump(output/'manifest.json',manifest); dump(output/'config.json',cfg)
    report(output,cfg,manifest,research,months)
    return research['totals']


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--data-root',type=Path,required=True);p.add_argument('--output',type=Path,default=OUT)
    a=p.parse_args();print(run(a.data_root,a.output))
