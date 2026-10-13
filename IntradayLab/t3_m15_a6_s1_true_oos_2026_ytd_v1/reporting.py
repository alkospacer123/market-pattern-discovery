"""YTD accounting and Russian disclosure; no strategy decisions or cost model."""
import csv
from datetime import datetime, timedelta
import json
import math
from pathlib import Path
import pandas as pd
import common as C

START=datetime(2026,1,1,tzinfo=C.TZ)
FEATURES=['ATR','PreviousATR','PriorHigh','PriorLow','H1ADX','H1PreviousADX','H1Slope',
          'H1PreviousSlope','H1ATRRatio','H1PreviousATRRatio','H1AvailableAt','H1PreviousAvailableAt','Signal']

def persist_features(frames,d):
    rows=[]
    for symbol in C.SYMBOLS:
        for at,r in frames[symbol].iterrows():
            rows.append({'instrument':symbol,'close_time':at}|{
                k:None if pd.isna(r[k]) else int(r[k]) if k=='Signal' else r[k] for k in FEATURES})
    C.write_csv(d/'indicators.csv',rows)

def historical_control(primary,scalar,metric):
    expected={2023:2.2072776314,2024:1.7721337045,2025:1.5813075953}
    rows=[]
    for year,pf in expected.items():
        selected=[r for r in primary['trades'] if r['exit_time'].year==year]
        value=metric(selected)
        other=metric([r for r in scalar['trades'] if r['exit_time'].year==year])
        assert abs(value['gross_PF']-pf)<1e-9,('HISTORICAL_PF_STOP',year,value)
        assert abs(other['gross_PF']-pf)<1e-9,('SCALAR_HISTORICAL_PF_STOP',year,other)
        month_r=[sum(r['gross_R'] for r in selected if r['exit_time'].month==m) for m in range(1,13)]
        opened=primary['OPEN_POSITIONS'] if year==2025 else [r for r in primary['PERIOD_END_OPEN_POSITIONS'] if r['month']==f'{year}-12']
        rows.append({'year':str(year),**value,'OPEN':len(opened),'positive_months':sum(v>0 for v in month_r),
                     'negative_months':sum(v<0 for v in month_r),'calendar_months':12})
    y=rows[-1]
    assert y['closed']==300 and y['OPEN']==1 and abs(y['gross_R']-86.8766134312305)<1e-8
    start=datetime(2025,1,1,tzinfo=C.TZ)
    cohort=metric([r for r in primary['trades'] if r['exit_time'].year==2025 and r['signal_time']>=start and r['entry_time']>=start])
    assert cohort['closed']==299 and abs(cohort['gross_PF']-1.563150474)<1e-9
    op=primary['OPEN_POSITIONS'][0]
    assert (op['instrument'],op['direction'],op['trade_id'])==('USDRUBF','LONG','T3-M15-Si-000215')
    return {'status':'PASS','years':rows,'WF2025_status':'WF_MIXED','WF2025_new_cohort':dict(cohort,OPEN=1)}

def diagnostics(rows,monthly):
    seq=sorted(rows,key=lambda r:(r['exit_time'],r['instrument'],r['trade_id']))
    run=maximum=0
    for r in seq:
        run=run+1 if r['gross_R']<0 else 0;maximum=max(maximum,run)
    mr=mmax=0
    for r in monthly:
        mr=mr+1 if r['gross_R']<0 else 0;mmax=max(mmax,mr)
    winners=sorted((r for r in rows if r['gross_R']>0),key=lambda r:(-r['gross_R'],r['exit_time'],r['instrument'],r['trade_id']))
    profit=sum(r['gross_R'] for r in winners);loss=-sum(r['gross_R'] for r in rows if r['gross_R']<0)
    total=sum(r['gross_R'] for r in rows)
    result={'max_losing_trade_run':maximum,'max_negative_month_run':mmax}
    for n in (1,5,10):
        value=sum(r['gross_R'] for r in winners[:n])
        result.update({f'top{n}_winners_R':value,f'top{n}_share_positive_R':value/profit if profit else None,
                       f'ex_top{n}_winners_R':total-value,f'ex_top{n}_winners_PF':(profit-value)/loss if loss else None})
    ranked=sorted(monthly,key=lambda r:(-r['gross_R'],r['month']))
    for n in (1,3):
        value=sum(r['gross_R'] for r in ranked[:n])
        result.update({f'top{n}_months_R':value,f'top{n}_share_total_R':value/total if total>0 else None})
    return result,winners[:10]

def enrich(summary,out,frames,old,end,metric,history):
    summary['historical_comparison']=history['years']
    summary['OPEN']=len(out['OPEN_POSITIONS'])
    coverage=[]
    for symbol,f in frames.items():
        part=f.loc[f.index>=START]
        coverage.append({'instrument':symbol,'loaded_bars_2023_YTD':len(f),'bars_2026':len(part),
                         'first_2026_close':part.index[0] if len(part) else None,
                         'last_available_open':f.index[-1]-C.STEP,'last_available_close':f.index[-1],
                         'uncovered_tail_start':f.index[-1], 'uncovered_tail_end_exclusive':end,
                         'tail_days':(end-f.index[-1]).total_seconds()/86400})
    summary['source_coverage']=coverage
    for month in summary['monthly']:
        year,m=map(int,month['month'].split('-'))
        lo=datetime(year,m,1,tzinfo=C.TZ)
        hi=datetime(year+(m==12),1 if m==12 else m+1,1,tzinfo=C.TZ)
        states=[]
        for r in month['coverage']:
            at=frames[r['instrument']].index
            used=at[(at>=lo)&(at<min(hi,end))]
            r.update(first_close=used[0] if len(used) else None,last_close=used[-1] if len(used) else None)
            r['coverage']='NO_COVERAGE' if not len(used) else 'PARTIAL_SOURCE_END' if at[-1]<min(hi,end) and at[-1]>=lo else 'PARTIAL_YTD_CUTOFF' if hi>end else 'AVAILABLE_SOURCE_PREFIX'
            states.append(r['coverage'])
        month['coverage_status']='NO_COVERAGE' if all(v=='NO_COVERAGE' for v in states) else 'PARTIAL' if any(v!='AVAILABLE_SOURCE_PREFIX' for v in states) else 'AVAILABLE_SOURCE_PREFIX'
        month['result_sign']='NO_COVERAGE' if month['coverage_status']=='NO_COVERAGE' else 'POSITIVE' if month['gross_R']>0 else 'NEGATIVE' if month['gross_R']<0 else 'ZERO'
    closed=[r for r in out['trades'] if START<=r['exit_time']<end]
    summary['diagnostics'],summary['top_winners']=diagnostics(closed,summary['monthly'])
    for r in summary['slices']:
        r['OPEN']=sum((r['scope']=='ALL_FOUR' or x['instrument']==r['scope']) and (r['direction']=='ALL' or x['direction']==r['direction']) for x in out['OPEN_POSITIONS'])
    inherited=old['OPEN_POSITIONS'][0]
    key=(inherited['instrument'],inherited['trade_id'])
    final=next(r for r in out['trades']+out['OPEN_POSITIONS'] if (r['instrument'],r['trade_id'])==key)
    for field in ('entry_price','initial_stop','initial_risk','signal_time','entry_time','direction'):
        assert inherited[field]==final[field],('CARRY_IMMUTABLE_CHANGED',field)
    first=next(r for r in out['stop_decisions'] if (r['instrument'],r['trade_id'])==key and r['bar_close_time']>=START)
    assert first['active_stop']==inherited['active_stop'] and first['activation_time_before']==inherited['activation_time']
    summary['carry']={'status':'PASS','method':'Full canonical prefix replay preserves all position and recursive indicator state',
                      'no_reset':True,'no_forced_liquidation':True,'start_position':inherited,'first_2026_stop':first,'outcome':final}
    summary['coverage_limitation']='Source prefix only; exchange calendar/delivery completeness not independently certified. No interpolation or synthetic fills.'

def tables(summary):
    historical=summary['historical_comparison']+[{'year':'2026 YTD',**summary['calendar_CLOSED'],'OPEN':summary['OPEN'],
        'positive_months':summary['positive_months'],'negative_months':summary['negative_months'],
        'calendar_months':summary['coverage_months_with_any_M15_bars']}]
    monthly=[{k:r[k] for k in ('month','closed','gross_PF','gross_R','coverage_status','result_sign')} for r in summary['monthly']]
    return {'comparison':historical,'monthly':monthly,'slices':summary['slices'],'coverage':summary['source_coverage'],
            'top_winners':[{k:r[k] for k in ('instrument','direction','trade_id','entry_time','exit_time','gross_R')} for r in summary['top_winners']]}

def cell(value):
    if value is None:return 'N/A'
    if isinstance(value,float):return f'{value:.9f}'
    return str(C.plain(value)).replace('|',' / ').replace('\n',' ')

def table(name,rows,fields):
    return ['<!-- dataset '+name+' -->','| '+' | '.join(fields)+' |','| '+' | '.join(['---']*len(fields))+' |']+[
        '| '+' | '.join(cell(r.get(k)) for k in fields)+' |' for r in rows]+['']

def publish(summary,out,old,d):
    data=tables(summary)
    for name,rows in data.items():C.write_csv(d/(name+'.csv'),rows)
    C.write_json(d/'REPORT_TABLES.json',data)
    closed=[r for r in out['trades'] if START<=r['exit_time']]
    C.write_csv(d/'trades_2026.csv',closed)
    C.write_csv(d/'new_2026_trades.csv',[r for r in closed if r['entry_time']>=START and r['signal_time']>=START])
    C.write_csv(d/'inherited_2025_trades.csv',[r for r in closed if r['entry_time']<START or r['signal_time']<START])
    C.write_json(d/'CARRY.json',summary['carry'])
    C.write_json(d/'DIAGNOSTICS.json',summary['diagnostics'])
    C.write_csv(d/'monthly_instrument_coverage.csv',[dict(month=r['month'],**v) for r in summary['monthly'] for v in r['coverage']])
    base=summary['calendar_CLOSED'];diag=summary['diagnostics'];last=summary['last_available_bar_close']
    report=['# OOS 2026 YTD — T3/M15 A6+S1 NEXT_OPEN TRAIL_375','',
        '**GROSS_ONLY / OOS_2026_YTD / NOT_LIVE_READY.** Все четыре инструмента, LONG и SHORT; параметры и исполнение заморожены. Оптимизация не проводилась.',
        '',f"Окно: [2026-01-01T00:00:00+03:00, {summary['data_cutoff_end_exclusive'].isoformat()}). Последняя причинно доступная свеча: **{last.isoformat()}**. Вывод относится только к фактически покрытому префиксу, а не полному календарному 2026.",
        '',f"**Gross PF {base['gross_PF']:.9f}; Gross R {base['gross_R']:+.9f}R; {base['closed']} CLOSED / {summary['OPEN']} terminal OPEN.** Expectancy {base['expectancy_R']:+.9f}R; средняя прибыль {cell(base['avg_win_R'])}R; средний убыток {cell(base['avg_loss_R'])}R. Победители/убытки: {base['wins']}/{base['losses']}.",
        '', 'Комиссии FINAM/MOEX, спред, проскальзывание, фандинг, дивидендные денежные поправки и искусственные R-штрафы не вычитаются. Это Gross PF и Gross R; сумма R не является доходностью капитала. Реальные расходы учитываются отдельно по брокерским исполнениям.',
        '', '## Сравнение замороженных периодов','']
    report+=table('comparison',data['comparison'],['year','closed','OPEN','gross_PF','gross_R','positive_months','negative_months','calendar_months'])
    report+=['2023–2024 — DEVELOPMENT_EXPOSED; 2025 — frozen Walk Forward WF_MIXED, новая cohort 299 CLOSED / 1 OPEN, PF 1,563150474. Контроль полных торговых журналов и опубликованных индикаторов выполнен до чтения OHLCV 2026.', '', '## Календарные месяцы 2026','']
    report+=table('monthly',data['monthly'],['month','closed','gross_PF','gross_R','coverage_status','result_sign'])
    report+=['AVAILABLE_SOURCE_PREFIX означает наблюдаемый префикс источника, без независимой сертификации биржевого календаря. PARTIAL раскрывает неполное покрытие хотя бы одного инструмента. NO_COVERAGE не считается нулевым или отрицательным торговым месяцем; PF без убытков или без сделок — N/A.', '', '## Инструменты и направления','']
    report+=table('slices',data['slices'],['scope','direction','closed','OPEN','gross_PF','gross_R','expectancy_R','avg_win_R','avg_loss_R','closed_R_drawdown'])
    report+=['## Coverage и непокрытый хвост','']
    report+=table('coverage',data['coverage'],['instrument','loaded_bars_2023_YTD','bars_2026','first_2026_close','last_available_open','last_available_close','uncovered_tail_end_exclusive','tail_days'])
    report+=['CSV timestamp — начало M15; в журнале используется завершение = timestamp + 15 минут. Исключено OHLCV свечей с завершением >= cutoff. Межсессионные и внутренние наблюдаемые разрывы опубликованы в observed_gaps.csv; отсутствующие бары не восстановлены.', '', '## Новые входы и перенос из 2025','',
        'Новые входы (signal и entry в 2026): '+json.dumps(C.plain(summary['new_2026_entry_CLOSED']),ensure_ascii=False)+'.', '',
        'Унаследованные CLOSED: '+json.dumps(C.plain(summary['inherited_pre_2026_CLOSED']),ensure_ascii=False)+'.', '',
        f"Перенесён USDRUBF LONG **T3-M15-Si-000215**: entry {summary['carry']['start_position']['entry_price']}, initial Stop {summary['carry']['start_position']['initial_stop']}, initial R {summary['carry']['start_position']['initial_risk']}; S1 на границе не активен. Непрерывный replay сохраняет Stop, экстремумы, S1, счётчики и рекурсивные индикаторы. Полное начальное состояние, первое решение 2026 и исход — CARRY.json. Сброса в Новый год и принудительного закрытия на YTD нет.", '',
        '## Просадка, серии и концентрация','',f"Максимальная CLOSED-R просадка **{base['closed_R_drawdown']:.9f}R**; максимальная серия проигрышей **{diag['max_losing_trade_run']}**; серия отрицательных месяцев **{diag['max_negative_month_run']}**.", '',
        'Диагностика концентрации: '+json.dumps(diag,ensure_ascii=False)+'. Исключения top-победителей только арифметическая диагностика; основной результат включает все сделки.', '']
    report+=table('top_winners',data['top_winners'],['instrument','direction','trade_id','entry_time','exit_time','gross_R'])
    report+=['## Оценка устойчивости','',f"Положительные/отрицательные покрытые месяцы: **{summary['positive_months']}/{summary['negative_months']}**, против 7/5 в 2025 и 20 положительных из 24 в 2023–2024. Покрыто {summary['coverage_months_with_any_M15_bars']} месяцев хотя бы частично; непокрытые месяцы не расширяют доказательную базу.", '',
        'Положительный Gross PF поддерживает гипотезу сохранения трендового преимущества на доступном OOS-префиксе, если PF > 1. Регулярность месяцев, отрицательные instrument×side, CLOSED-R просадка и зависимость от больших победителей ограничивают этот вывод. Более слабая месячная регулярность ослабляет устойчивость TRAIL_375 даже при положительном суммарном R. Неполный YTD не позволяет объявить годовую стабильность или готовность к LIVE.', '',
        '## Проверка и артефакты','', 'control/HISTORICAL_CONTROL.json: полные primary/scalar журналы W4, PF/R/число сделок 2023–2025 и published indicators. FEATURE_CONTROL.json: все индикаторные поля primary против scalar. AUDIT.json: полный replay и причинность. INDEPENDENT_AUDIT.json: свежий отдельный scalar-процесс без импорта primary runner/engine/reporting, независимая арифметика и сверка Markdown. REPEATABILITY.json: первый запуск плюс два полных повтора, direct bytes и SHA256.', '',
        'Полные primary/ и scalar/: trades.csv, stop_decisions.csv, entry_opportunities.csv, observed_gaps.csv, OPEN_POSITIONS.json и PERIOD_END_OPEN_POSITIONS.json. Дополнительно indicators.csv, SOURCE_RECEIPTS.json, monthly.csv, slices.csv, coverage.csv, monthly_instrument_coverage.csv, trades_2026.csv, new_2026_trades.csv, inherited_2025_trades.csv, DIAGNOSTICS.json и CARRY.json.', '',
        '**Независимость вычислительная; внешнее человеческое ревью PENDING. Draft PR #513, NO MERGE / NO AUTO-MERGE. STOP для независимой проверки ChatGPT и решения пользователя.**']
    (d/'REPORT_RU.md').write_text('\n'.join(report)+'\n',encoding='utf-8')
