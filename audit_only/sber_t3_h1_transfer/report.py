"""Deterministic presentation only; never changes signals, parameters or costs."""
from pathlib import Path
import json
import pandas as pd
from . import study

HERE=Path(__file__).resolve().parent
RESULTS=HERE/'results/evaluation'


def n4_comparison(out):
    source=study.ROOT/'TradingSystemLab/results/post_v3_analysis/stage6_unified_candidate_comparison/portfolio_trade_scaling_registry.csv'
    assert study.sha(source)=='8f0493f5dd4edf087881622005efde0531c6146903a38c362e72dbc508071b1e'
    n=pd.read_csv(source)
    n=n[(n.variant=='TRAIL1') & n.instrument.isin(['USDRUBF','CNYRUBF','GLDRUBF','IMOEXF']) & n.lifecycle.isin(['baseline','historical_true_oos'])].copy()
    n['exit']=pd.to_datetime(n.exit_time,utc=True).dt.tz_convert('Europe/Moscow')
    n['entry']=pd.to_datetime(n.entry_time,utc=True).dt.tz_convert('Europe/Moscow')
    assert not n.source_trade_id.duplicated().any()
    s=pd.read_csv(out/'all_trades.csv')
    s['exit']=pd.to_datetime(s.exit_time,utc=True).dt.tz_convert('Europe/Moscow')
    endpoint=pd.Timestamp('2026-09-15 21:00:00',tz='UTC').tz_convert('Europe/Moscow')
    rows=[]
    for year in [2024,2025,2026]:
        start=pd.Timestamp(f'{year}-01-01',tz='Europe/Moscow')
        end=min(pd.Timestamp(f'{year+1}-01-01',tz='Europe/Moscow')-pd.Timedelta(nanoseconds=1),endpoint)
        for label,g,r_column in [('N4_NORMALIZED_C1',n,'strategy_R'),('SBER_LONG_SHORT_C1',s[s.scenario=='LONG_SHORT_C1'],'net_R'),('SBER_LONG_ONLY_C1',s[s.scenario=='LONG_ONLY_C1'],'net_R')]:
            g=g[(g.exit>=start)&(g.exit<=end)].sort_values(['exit','source_trade_id'] if 'source_trade_id' in g else ['exit','trade_id'])
            x=g[r_column]; curve=pd.concat([pd.Series([0.]),x.reset_index(drop=True).cumsum()],ignore_index=True)
            rows.append({'series':label,'year':year,'window_start':start,'window_end':end,'trades':len(g),
                         'normalized_net_PF':float(x[x>0].sum()/-x[x<0].sum()) if (x<0).any() else None,
                         'normalized_net_R':float(x.sum()),'max_closed_R_DD':float((curve-curve.cummax()).min()),
                         'comparison_scope':'same nominal normalized C1 only; different assets/scales and basket breadth; no capital-return ranking'})
    study.write_csv(out/'n4_same_window.csv',pd.DataFrame(rows))
    return pd.DataFrame(rows)


def render(out=RESULTS):
    summary=pd.read_csv(out/'summary.csv')
    annual=pd.read_csv(out/'annual.csv')
    months=pd.read_csv(out/'monthly.csv')
    quarters=pd.read_csv(out/'quarterly.csv')
    directions=pd.read_csv(out/'directions.csv')
    data=json.loads((out/'data_audit.json').read_text())
    audit=json.loads((out/'audit.json').read_text())
    n4=n4_comparison(out)
    selection=summary[summary.period!='FULL']
    supported=((selection.net_R>0)&(selection.net_PF>1)).all()
    rejected=((selection.net_R<0)&(selection.net_PF<1)).all()
    verdict='SUPPORTED' if supported else 'NOT_SUPPORTED' if rejected else 'MIXED'
    worst_months=months.loc[months.groupby('scenario').net_R.idxmin()]
    worst_dd=months.loc[months.groupby('scenario').max_closed_R_DD.idxmin()]
    worst_years=annual.loc[annual.groupby('scenario').net_R.idxmin()]
    worst_quarters=quarters.loc[quarters.groupby('scenario').net_R.idxmin()]
    def table(frame,cols): return frame[cols].to_markdown(index=False,floatfmt='.4f')
    text=f'''# SBER: независимое историческое исследование T3/H1/TRAIL1

Вердикт переноса: **{verdict}** по заранее зафиксированному описательному правилу.
Это внешний эксперимент, SBER не включён в `TRAIL1__N4_01__FULL__R15`.
Main: `{study.MAIN}`. CSV SHA256: `{study.DATA_SHA}`.

## Данные и границы

В источнике {data['raw_rows']} строк, использовано {data['usable_rows']}.
Начало: {data['first_open']}; последнее исходное открытие: {data['last_source_open']}.
Последний допустимый close: {data['last_authorized_close']}.
Последняя свеча открытия 16:00 19.10.2026 исключена как потенциально неполная.
Дубликатов/невалидных OHLC/нечисловых значений: 0/0/0; zero volume: {data['zero_volume']}.
Паузы >72h: {data['gaps_over_72h']}; открытия с gap >5%: {data['gaps_over_5pct']}.
Часовые метки согласуются с предполагаемой московской шкалой открытий, но её
происхождение не подтверждено независимой документацией поставщика.
Исторические UTC offsets Москвы сохранены. Разрывы не заполнялись.
Состав сессий/H4 и число блоков через разрывы: `data_yearly.csv`, `session_hours.csv`;
крупные разрывы: `extreme_gaps.csv`. Смена часов меняет состав последовательных H4.
Плоские бары по часам: `flat_bars_by_hour.csv`; свечи с range или изменением close
>10%: `price_extremes.csv`. Регулярные flat bars могут отражать особенности сессий/
выгрузки; их происхождение не доказано, они сохранены без постфактум-фильтрации.
Группировка выполняется по дате закрытия: закрытие 00:00 относится к новому дню.

## Результаты в R

R — исходная ценовая дистанция риска на одну акцию; суммы R не равны процентам
депозита. Все таблицы по дате выхода MSK. Пустые PF при отсутствии отрицательных
сделок не интерпретируются как ноль. 2011 начинается 17 ноября; 2026 неполный.

{table(summary,['scenario','period','trades','gross_PF','net_PF','gross_R','cost_R','net_R','expectancy_R','win_rate','max_closed_R_DD'])}

## Каждый год

{table(annual,['scenario','year','trades','gross_PF','net_PF','net_R','max_closed_R_DD'])}

## Направления и концентрация

{table(directions,['scenario','direction','trades','net_PF','net_R','avg_winner_R','avg_loser_R','win_rate','max_closed_R_DD'])}

{table(summary[summary.period=='FULL'],['scenario','top1_share_positive_R','top5_share_positive_R','top10_share_positive_R','net_R_without_top5','gap_exits'])}

## Негативные периоды

Худшие годы по net R:

{table(worst_years,['scenario','year','net_R','net_PF','max_closed_R_DD'])}

Худшие кварталы по net R:

{table(worst_quarters,['scenario','quarter','net_R','net_PF','max_closed_R_DD'])}

Худшие месяцы по net R:

{table(worst_months,['scenario','month','net_R','net_PF','max_closed_R_DD'])}

Худшие месяцы по DD закрытой суммы R (внутри каждого месяца, начальная кривая 0):

{table(worst_dd,['scenario','month','net_R','max_closed_R_DD'])}

Полная календарная сетка всех месяцев, включая нулевые: `monthly.csv`.
Полные кварталы: `quarterly.csv`; cohort по дате входа: `entry_cohorts.csv`.
Открытые позиции без выдуманного финального закрытия: `open_positions.json`.
Закрытый DD не измеряет внутрипозиционные убытки, margin call или риск гэпа.

## N4: совпадающие окна и ограничения

{table(n4,['series','year','trades','normalized_net_PF','normalized_net_R','max_closed_R_DD'])}

Общие окна: 2024, 2025 и 2026 до 16.09.2026 00:00 MSK включительно;
SBER до октября в основных таблицах не подставляется в сентябрьское сравнение.
N4 взят из аутентифицированного ledger Stage6, только baseline и historical_true_oos,
без повторного учёта WF. Номинальная формула C1 совпадает, но .002 price units
имеет разный экономический смысл у разных инструментов. Это сравнение только
нормированных исследовательских чисел; полная сопоставимость реальных расходов
не установлена. N4 — четыре инструмента, SBER — один; ранжирование доходности
капитала невозможно. Подтверждённые Stage7 проценты N4 (контекст): 2024 +165.28%,
2025 +74.38%, 2026 до сентября +88.31%, MaxDD -19.96%, CAGR +122.44%.
Они не сопоставляются напрямую с суммой SBER R. До 2024 нет полного общего N4 окна.

## Исполнение и акции

LONG_SHORT_C1 — теоретическая симметрия без гарантии доступности short/borrow,
исторических запретов коротких продаж, платы займа и margin requirements.
LONG_ONLY_C1 — самостоятельный replay, не постфильтрация LS ledger.
LONG_ONLY_STOCK_PROXY — физически допустимое направление shares и диагностическая
сетка .01 RUB с округлением stop вниз и условными расходами .02 RUB/акцию round trip.
Историческая сетка и лот не аутентифицированы; ориентир 10 акций/лот не используется
для расчёта размера позиции. Реальные broker/exchange fees, short borrow, slippage,
дивиденды, налоги и funding не установлены. Не рассчитаны капитал/R15/целые лоты/
cash caps: из этого исследования нельзя получить проверенную доходность счёта.
Сценарий stock proxy не заменяет исходный C1. Тик .001 не выдан за тик SBER.

Вход на том же close, который сформировал сигнал, — идеализация замороженного
исследования: в реальности после получения OHLC этот close может быть недоступен.
Нет bid/ask, очереди, ликвидности и внутрибара; gap fill по open остаётся идеализацией
первой доступной сделки, в остановку биржи исполнение не выдумывается.
Ряд принят как raw/unadjusted; дивидендные и корпоративные гэпы не исправлялись.
Дивиденды LONG не начисляются; дивидендные выплаты SHORT не списываются.

## Аудит и воспроизводимость

Общий статус расчётного аудита: **{audit['status']}**. Все расхождения и максимальные
численные отклонения сохранены в `audit.json`. Неизменённые research-authority
и production replay сверены на идентичных данных. Отдельный scalar implementation
повторяет индикаторы и сделки; это независимость кода одного исполнителя,
не внешняя экспертная рецензия. Все сценарии запущены дважды с полным совпадением
SHA256 trade CSV и traces. Разработка 2011–2024, тесты и setup hash заморожены до
единственной оценки 2025–2026; gate `EVALUATION_ACCESS.json`. Повтор служил только
детерминированной сверке. `prefix_invariance.json` подтверждает неизменность pre-2025.
Все исходные frozen файлы проверяются SHA до запуска; production не изменён.
Использовались только локальные данные, без FINAM/счетов/реальных операций.
Точные команды, логи, число тестов и freeze находятся рядом с отчётом.
'''
    (HERE/'REPORT_RU.md').write_text(text)
    study.write_json(out/'verdict.json',{'main_sha':study.MAIN,'verdict':verdict,'rule':'preregistered descriptive portability, not significance or production approval'})


if __name__=='__main__':render()
