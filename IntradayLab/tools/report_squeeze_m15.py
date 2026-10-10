#!/usr/bin/env python3
"""Build fixed-cohort report and four-architecture comparison without retuning."""
import csv,json
from pathlib import Path
from decimal import Decimal as D
from run_squeeze_m15 import write_csv
LAB=Path(__file__).resolve().parents[1]
OUT=LAB/'results/stage2_squeeze_m15_v1'


def read(p):return list(csv.DictReader(p.open()))
def number(value,places=6):
    if value is None or value=='':return 'null'
    x=D(str(value));return str(x.quantize(D(10)**-places)).rstrip('0').rstrip('.') if x else '0'
def table(headers,rows):
    return '\n'.join(['| '+' | '.join(headers)+' |','| '+' | '.join('---' for _ in headers)+' |']+['| '+' | '.join(str(x) for x in r)+' |' for r in rows])


def build():
    metrics=read(OUT/'metrics.csv');monthly=read(OUT/'monthly_results.csv');costs=read(OUT/'sensitivity.csv');directions=read(OUT/'direction_results.csv')
    base=[r for r in metrics if r['scenario']=='T10'];primary={ (r['instrument'],r['architecture']):r for r in base}
    order=['USDRUBF','CNYRUBF','GLDRUBF','IMOEXF'];arches=['SQUEEZE_M15','SQUEEZE_H1_M15'];base=[primary[s,a] for s in order for a in arches]
    old=read(LAB/'results/stage2_squeeze_v1/sensitivity.csv')
    comparison=[]
    for origin,rows in [('stage2_squeeze_v1',old),('stage2_squeeze_m15_v1',costs)]:
        for r in rows:
            comparison.append(dict(frozen_version=origin,source_artifact=f'{origin}/sensitivity.csv',**r))
    write_csv(OUT/'four_architecture_comparison.csv',comparison)
    text=['# IntradayLab — Stage 2 SQUEEZE_M15 / SQUEEZE_H1_M15, итоговый отчёт','','**FEASIBILITY PASS / NO ECONOMIC BASELINE PASS** для обеих новых фиксированных архитектур. Технически полноценная M15-система реализуема; положительные USD-выборки слишком малы и нерегулярны для устойчивого Baseline. Ни одна из четырёх исследованных архитектур Squeeze не квалифицирована для Stage3. Высокий PF H1 на пяти сделках не служит основанием для выбора параметров или продвижения.','',
'База: фактический GitHub `main` `7643513a7ce718b142454fe094186c3e6bbb4605`, PR #455 и #456 MERGED. Новая пара — самостоятельные M15-индикаторы, сигналы, M15 Open, защита и выходы. H1 меняет исключительно допуск входа. Прежняя M5/M30-пара, её правила, движки, конфигурации, журналы и экономическое отклонение остаются неизменны.','',
'## Причинность и заморозка','',
'[Пререгистрация](STAGE2_SQUEEZE_M15_PREREGISTRATION.md), [конфигурация](../config/stage2_squeeze_m15_v1.json), SHA-256 `54e3cef5509807622882059ba354bea638cc4781261757d692ac71fdd7424b56`, коммит `2bb22c5` до первых исторических P&L. Семисвечной прогрев105мин выбран технически против100мин BB20 M5, минимум две M15-свечи сжатия30мин. Максимальная непрерывная серия18свечей исключает стандартный BB20. [Техническая проверка](STAGE2_SQUEEZE_M15_FEASIBILITY.md) и отдельная независимая feasibility выполнены до доходностей.','',
'Источник — оригинальные read-only M5-префиксы2023 `market-pattern-data/forever`,104795строк,5833704байта вместе с заголовками. Ноль байт2024/2025+. Exact3/12 существующих завершённых M5 образуют M15/H1 внутри одного непрерывного исторического исследовательского окна; неполные родители недопустимы. Стандартная сетка, доступность M15 T+20/25 и H1 T+65/70; оба задержанных сигнала входят не раньше M15 Open T+30. T10/T15 действительно имеют одинаковые исполнения; различается время получения/подтверждения на5мин.','',
'Сохраняются принятые окна10:00–14:00 и14:05–18:50, с датированным мартовским возобновлением14:15. Исторические свидетельства и ограничения календаря — [Stage1.2](STAGE1_2_SESSION_MTF_AUDIT.md), включая MOEX n55032/n55200 и остановку13.09.2023. На13сентября отсутствующие утренние M5 не восстанавливаются; после возобновления нужен новый прогрев. Неполный PM14:00 и хвост18:45 не становятся M15. Полный архив всех venue-исключений и native higher-TF finalization не сертифицирован; вывод относится к ранее принятому ограниченному исследовательскому контракту. H1 требует актуальную пару и все доступные M5 через момент решения, без stale fallback/переноса через клиринг.','',
'Структурный Stop, outward Take с планируемым net≥3R, ограничение extension/risk/target, Stop-first, худший Open при adverse gap, запрет entry-bar Take и проникновение1тик сохраняют экономическую идею. Common session-flat13:15/18:15 имеет запас доB−10 и приT15;120мин max hold и failed-breakout выход на строго будущем M15 Open. Нет гарантии фактического исполнения, капитал/ГО/реальная комиссия не моделируются. UNKNOWN при отсутствующем target или открытом пути сохраняет null прошлой экономики даже после conditional reduce-all. В реальных новых исполнениях UNKNOWN=0; отдельные synthetic adversaries проверяют эти ветки.','',
'## Первичная воронка и исполнения — C1 T10','',
'Во всех таблицах численные P&L — **собственные единицы котировки инструмента, CLOSED-ONLY DIAGNOSTIC**, прибыль после модельных издержекC1. Разные котировки не суммируются в RUB-портфель. C1 — исторический тик каждой исполненной стороны, CNY до/после27.09.2023 19:00.','',
 table(['Инструмент','Архитектура','Сжатия≥2','Пробои','Заявки','NONFILL','Исполнено L/S','UNKNOWN'],[[r['instrument'],r['architecture'],r['confirmed_squeeze_episodes'],r['confirmed_signals'],r['model_orders'],r['nonfills'],f"{r['entries']} ({r['long_entries']}/{r['short_entries']})",r['unknown']] for r in base]),'',
'[Вся исходная воронка](../results/stage2_squeeze_m15_v1/funnel_stages.csv) от2023 M5 через полные M15, готовые индикаторы, эпизоды и расширения к причинным допускам; [все конечные причины](../results/stage2_squeeze_m15_v1/filter_funnel.csv). Непройденная геометрия на actual Open — NONFILL, без повторного входа. IMOEX технически даёт25подтверждённых сжатий/7пробоев; единственная заявка не исполнилась из-за extension>0.5ATR. Его пустая торговая выборка получена после успешного прогрева и причинных сигналов.','',
'## Закрытая экономика и риск — C1','',
 table(['Инструмент','Архитектура','Gross','C1','Net','Net PF','Expectancy','Σ Net R','DD закрытого журнала','Net≥3R'],[[r['instrument'],r['architecture']]+[number(r[k]) for k in ('closed_gross','closed_cost','closed_net','closed_net_PF','closed_expectancy','closed_net_R','closed_realized_DD')]+[r['realized_net_3R']] for r in base]),'',
'PF=null уCNY: два выигрыша без наблюдённых убытков, `NO_LOSSES`, а не доказанный бесконечный PF. IMOEX: `NO_TRADES`, Net/Gross/C1=0 только для пустой закрытой выборки; expectancy/PF/DD=null. DD — максимальная подтверждённая реализованная просадка известных закрытых сделок по времени acknowledgement; она не является полной годовой equity-просадкой или внутрисделочным mark-to-market DD. Все открытые позиции закрываются внутри окна, но непокрытые исходные периоды всё равно препятствуют полным годовым показателям.','',
'Минимальный планируемый Net RR=3 для всех11уникальных M15-исполнений. Это план, не средняя реализованная прибыль: CNY не достиг net3R, GLD завершился Stop. USD standalone имеет4консервативно наблюдённых gross3R и3реализованных net≥3R; H1 —3/2. Favorable High/Low Stop/market exit-свечи не доказывает предшествующий путь и не завышает MFE.','',
'## Дополнительная замена расходов C2','',
 table(['Инструмент','Архитектура','Net C2','PF C2','Expectancy C2'],[[r['instrument'],r['architecture']]+[number(r[k]) for k in ('closed_net','closed_net_PF','closed_expectancy')] for r in costs if r['scenario']=='T10' and r['cost']=='C2']),'',
'C2=2*C1, на тех же executions/Stop/Take/exit; дополнительных replay-архитектур нет. USD standalone PF падает ниже1.6; H1 сохраняетPF2.5 на пяти сделках. Это не достаточное свидетельство стабильности. T10/T15 совпадают по fills/уровням/P&L/месячным знакам и C2; нельзя считать эти одинаковые пути независимыми подтверждениями.','',
'## Частота, месяцы и концентрация','',
 table(['Инструмент','Архитектура','Сделок/ожид.день','Сделок/доступный месяц','+ / − / нулевые сделки / без сделок / NO_COVERAGE','Top1 выигрыш','Top3 выигрыша','Net безTop1'],[[r['instrument'],r['architecture'],number(r['trades_per_expected_day']),number(r['trades_per_available_month']),f"{r['positive_closed_months']} / {r['negative_closed_months']} / {r['zero_net_trade_months']} / {r['zero_trade_months']} / {r['no_coverage_months']}",number(r['largest_winner_share']),number(r['top3_winner_share']),number(r['closed_net_without_top1'])] for r in base]),'',
'Знаки в колонкемесяцев относятся к закрытым подвыборкам; подтверждённые календарные знаки требуют COVERED безUNKNOWN. УUSD standalone все4положительных месяца частично покрыты; подтверждённый декабрь отрицателен, октябрь безсделок. УH1 USD все3положительных месяца частично покрыты; октябрь/декабрь подтверждённо безсделок. УCNY один полностью покрытый положительный декабрь, оба исполнения только в нём;11остальных месяцев частично покрыты. GLD:6NO_COVERAGE,6частично покрытых, один наблюдённый отрицательный октябрь. IMOEX:10NO_COVERAGE и2частично покрытых безсделок.','',
'Итого standalone11уникальных исполнений за254ожидаемых торговых дня совокупного доступного календаря≈0.0433/день; H1 сохраняет8изних≈0.0315/день. Это подсчёт возможностей, без денежного суммирования. Нет искусственной квоты сделок; задача регулярных положительных месяцев фактически не достигнута. Largest month share USD0.419/0.387; Top3 выигрыша87%? Точное значение standalone85.714%, H1 100%. CNY весь результат в одном месяце. Малый cohort остаётся основным ограничением.','',
'Все12месяцев ниже: `P`=частичное покрытие, `C`=полное по принятому source-calendar, `N`=NO_COVERAGE. Значения сP — исключительно закрытые подвыборки;0P — отсутствие известных сделок, не полный нулевой месячный P&L.','']
    months=[]
    for r in base:
        rows=[m for m in monthly if (m['instrument'],m['architecture'],m['scenario'],m['cost'])==(r['instrument'],r['architecture'],'T10','C1')]
        months.append([r['instrument'],r['architecture']]+['N' if m['coverage_status']=='NO_COVERAGE' else number(m['closed_net'])+('C' if m['coverage_status']=='COVERED' else 'P') for m in rows])
    text += [table(['Инструмент','Архитектура']+[f'{m:02d}' for m in range(1,13)],months),'',
'[384месячные строки C1/C2 × T10/T15](../results/stage2_squeeze_m15_v1/monthly_results.csv), [64направленных экономических строки](../results/stage2_squeeze_m15_v1/direction_results.csv), [дневная/недельная/месячная частота](../results/stage2_squeeze_m15_v1/frequency_report.csv), [M15 coverage](../results/stage2_squeeze_m15_v1/coverage_m15.csv). Полные годовые Net/PF/DD у всех16запусков=null. Нет восстановленных свечей, вымышленных annualPF или скрытых непокрытых месяцев.','',
'## Сравнение самостоятельного M15 и H1→M15','',
'H1 удаляет уUSD3исполнения: один Take +0.18 и два Stop/убытка суммарно−0.15. Net уменьшается0.28→0.25, PFрастёт2.333→5.167, число позитивных подмесяцев4→3 и число сделок8→5. C2 Net0.12→0.15. Новых freed-entry fills нет. CNY/GLD/IMOEX исполнения не изменились; число неисполненных заявокCNY/GLD уменьшается на1. Это выборочная фильтрация, без независимой достаточной повторяемости или преимущества по регулярности. [Парное сравнение](../results/stage2_squeeze_m15_v1/m15_h1_comparison.csv).','',
'## Все четыре исследованные архитектуры','',
'Значения старой пары только прочитаны из её неизменного frozen ledger/report; ничего не пересчитано и не подобрано по лучшемуPF. Каждая строка ниже — отдельный заранее объявленный complete hypothesis. Сравнение временных масштабов включает фиксированные технические различия7/2против20/3, а не чистую причинную attribution одного TF.','']
    rows=[]
    for a in ('SQUEEZE_M5','SQUEEZE_M30_M5','SQUEEZE_M15','SQUEEZE_H1_M15'):
        origin=old if a in ('SQUEEZE_M5','SQUEEZE_M30_M5') else costs
        by={r['instrument']:r for r in origin if r['architecture']==a and r['scenario']=='T10' and r['cost']=='C1'}
        rows.append([a]+[f"{by[s]['entries']} сделок; Net {number(by[s]['closed_net'])}; PF {number(by[s]['closed_net_PF'])}" for s in order]+['NO ECONOMIC BASELINE PASS'])
    text += [table(['Архитектура']+order+['Вердикт'],rows),'',
'`SQUEEZE_M5`: экономически отрицательная малочисленная USD/CNY выборка, нольGLD/IMOEX; замороженный вердикт PR#456 сохранён. `SQUEEZE_M30_M5`: M30 не меняет исполнений и не улучшает принятое отрицательное заключение. `SQUEEZE_M15`: USD лучше известной M5-подвыборки, но8сделок и четыре частично покрытых позитивных месяца, C2PF1.414, одинGLDStop, дваCNYвыигрыша только в декабре, нольIMOEX не дают прибыльного регулярного плато. `SQUEEZE_H1_M15`: редкий USD PF5.167 на5сделках и C2PF2.5 не обеспечивают достаточное число повторений, полностью подтверждённые положительные месяцы или диверсификацию; остальныеинструменты не улучшаются.','',
'[Все32фиксированные сценария и C2-замены (64экономические строки)](../results/stage2_squeeze_m15_v1/four_architecture_comparison.csv). PF≥1.6, предпочтительно>2, положительная expectancy и планируемые3R оцениваются вместе с количеством независимых исполнений, достаточным покрытием, месяцами и концентрацией. ИзолированныйPFпорог не является PASS. Итог bounded Stage2: **NO ECONOMIC BASELINE PASS для каждой из четырёх исследованных архитектур**; отрицательные/недостаточные результаты сохраняются.','',
'## Независимая проверка и воспроизводимость','',
'**INDEPENDENT TRADING LOGIC PASS: 651721 проверенных полей, 0 расхождений. Полный пакет IntradayLab:192 tests PASS; отдельный финальный аудитор:11 synthetic regressions PASS.**','',
'[Независимый аудитор](../tools/audit_squeeze_m15.py) самостоятельно читает raw2023, строит родителей/индикаторы/циклы и отдельный execution state machine, затем считает экономику, месяцы и частоту. Ни replay, ни его индикаторы, календарь, geometry или метрики не импортируются. Reconstruction зафиксирована до чтения опубликованных журналов. [Результат аудита](../results/stage2_squeeze_m15_v1/independent/independent_audit.json); [ручные трассировки всех11уникальных fills](../results/stage2_squeeze_m15_v1/manual_traces.md), включая raw children, геометрию, H1 и экономику.','',
'Два replay и два прохода reporting побайтово одинаковы, gzipmtime=0. [Исходные returns hashes](../results/stage2_squeeze_m15_v1/first_returns_snapshot.json), [репликация](../results/stage2_squeeze_m15_v1/reproducibility.json), [история исключительно дополнения отчётности](../results/stage2_squeeze_m15_v1/reporting_correction_history.json). Config/replay/runner после первого исторического P&L не изменены; trading journals, первичная экономика, fills/защита/выходы побайтово совпадают с первым run. Дополнены M15 coverage и детализация воронки/месячных статусов.','',
'Независимая первая сверка обнаружила отличие только в terminal_at неиспользованных циклов: batch-аудитор аннотировал reset на следующем допустимом родителе вместо первого недопустимого aligned clock. Аудитор исправил собственную аннотацию и сохраняет историю; ни один сигнал/исполнение/результат/основнойдвижок не изменён.','',
'[Финальные SHA-256](../results/stage2_squeeze_m15_v1/SHA256SUMS), [защищённые деревья до работы](../results/stage2_squeeze_m15_v1/initial_state.json), итоговая проверка main/diff/source/protected в pre_publication_verification.json. Только IntradayLab; Draft PR безMerge, безStage3, Robustness, WalkForward, TRUE OOS илиLIVE.','']
    report='\n'.join(text).replace('Top3 выигрыша87%? Точное значение standalone85.714%, H1 100%.','Top3 выигрыша standalone85.714%, H1 100%.')
    (LAB/'reports/STAGE2_SQUEEZE_M15_FINAL_REPORT.md').write_text(report)

if __name__=='__main__':build()
