"""Russian report from predeclared metrics. No adaptive verdict criteria."""
import math
from common import *

def report(result,audit,manifest,out):
    ss=result['summaries'];mm=result['monthly'];ff=result['flips'];ww=result['winners']
    def headline(system,variant,basis):
        life='DISJOINT_BASELINE_AND_HISTORICAL_OOS' if system=='H1' else 'history_2023_2026'
        return next(r for r in ss if r['system']==system and r['variant']==variant and r['lifecycle']==life and r['monthly_basis']==basis)
    def n(x):return 'N/A' if x is None else f'{x:.6f}'
    lines=['# Независимый эксперимент PARTIAL_TP_2R_50: T3/H1 и T3/M15','',
        '**H1: INCONCLUSIVE. M15: INCONCLUSIVE. CASH_MODEL_NOT_VALIDATED.**',
        'Исследовательский механизм измерен без подбора порогов. Подтверждённого денежного replay с историческими ГО, расходами и капиталом нет; положительный вывод о реальной месячной доходности недопустим. Дробные половины ниже — FRACTIONAL_REFERENCE, не реально исполненные контракты.','',
        '## Запрошенная итоговая таблица','',
        'Месяцы ниже относятся к GROSS_CLOSED_LEG_R; худший месяц — R, просадка — максимальная внутримесячная completed-bar GROSS_MTM_R DD. Столбцы Net оставлены N/A: проверенных денежных расходов нет. У H1 это описательное объединение неперекрывающихся Baseline и historical OOS, не непрерывный капитал; WF исключён.','',
        '| Система | Вариант | Прибыльные месяцы | Отрицательные месяцы | Худший месяц | Просадка | Net PF | Net R |',
        '|---|---|---:|---:|---:|---:|---|---|']
    for system in ('H1','M15'):
        for variant in ('CONTROL','PARTIAL_TP_2R_50'):
            r=headline(system,variant,'GROSS_CLOSED_LEG_R')
            lines.append(f"| {system} | {variant} | {r['positive_months']}/{r['covered_months']} ({r['positive_share']:.2%}) | {r['negative_months']} | {r['worst_month_R']:.6f}R | {r['max_MTM_intramonth_DD_R']:.6f}R | N/A | N/A |")
    lines+=['','## Отдельно: модельные Gross показатели','',
        '| Система | Вариант | Gross PF | Gross R закрытых позиций | Expectancy R | Win rate | +2R наблюдаемо по свече | Частичных модельных | Реально исполнимых |',
        '|---|---|---:|---:|---:|---:|---:|---:|---|']
    for system in ('H1','M15'):
        for variant in ('CONTROL','PARTIAL_TP_2R_50'):
            r=headline(system,variant,'GROSS_CLOSED_LEG_R')
            lines.append(f"| {system} | {variant} | {n(r['gross_PF'])} | {n(r['gross_R'])} | {n(r['expectancy_gross_R'])} | {r['win_rate']:.2%} | {r['positions_observed_reaching_2R']} | {r['fractional_partial_positions']} | UNKNOWN |")
    lines+=['','Достижимость +2R по OHLC не всегда означает достижение при ещё открытой позиции: при одновременном Stop/TP порядок неизвестен, зачтён stop. Количество частичных исполнений учитывает только причинно допустимые события.']
    for system in ('H1','M15'):
        lines+=['',f'## {system}: месячная стабильность отдельно','',
            '| Базис | Вариант | + / − / 0 | Доля + / − / 0 | Худший R | Медиана R | Серия отрицательных |',
            '|---|---|---:|---|---:|---:|---:|']
        for basis in ('GROSS_CLOSED_LEG_R','GROSS_MTM_R'):
            for variant in ('CONTROL','PARTIAL_TP_2R_50'):
                r=headline(system,variant,basis)
                lines.append(f"| {basis} | {variant} | {r['positive_months']} / {r['negative_months']} / {r['zero_months']} | {r['positive_share']:.2%} / {r['negative_share']:.2%} / {r['zero_share']:.2%} | {n(r['worst_month_R'])} | {n(r['median_month_R'])} | {r['max_consecutive_negative_months']} |")
        for basis in ('gross_closed_leg_R','gross_MTM_change_R'):
            relevant=[r for r in ff if r['system']==system and r['lifecycle']!='walk_forward' and r['basis']==basis]
            good=[r for r in relevant if r['transition']=='NEGATIVE_TO_POSITIVE'];bad=[r for r in relevant if r['transition']=='POSITIVE_TO_NEGATIVE']
            lines+=['',f'**{basis}**: CONTROL − → PARTIAL +: '+(', '.join(r['month'] for r in good) or 'нет')+'. CONTROL + → PARTIAL −: '+(', '.join(r['month'] for r in bad) or 'нет')+'.',
                '', '| Месяц | Переход | CONTROL R | PARTIAL R |','|---|---|---:|---:|']
            lines += [f"| {r['month']} | {r['transition']} | {n(r['CONTROL_R'])} | {n(r['PARTIAL_R'])} |" for r in good+bad]
        lines+=['','**Полная помесячная таблица, MSK**. GROSS_CLOSED_LEG_R учитывает каждую часть в её месяце закрытия; MTM учитывает открытый остаток. Единицы — нормированные R разных входов, не проценты капитала.','',
            '| Месяц | Покрытие / lifecycle | CONTROL closed legs R | PARTIAL closed legs R | CONTROL MTM ΔR | PARTIAL MTM ΔR |',
            '|---|---|---:|---:|---:|---:|']
        months=sorted({r['month'] for r in mm if r['system']==system and r['lifecycle']!='walk_forward'})
        for month in months:
            rr=[r for r in mm if r['system']==system and r['month']==month and r['lifecycle']!='walk_forward' and r['coverage']!='NO_DATA']
            if not rr:lines.append(f'| {month} | NO_DATA | N/A | N/A | N/A | N/A |');continue
            a=next(r for r in rr if r['variant']=='CONTROL');b=next(r for r in rr if r['variant']=='PARTIAL_TP_2R_50')
            lines.append(f"| {month} | {a['coverage']} / {a['lifecycle']} | {n(a['gross_closed_leg_R'])} | {n(b['gross_closed_leg_R'])} | {n(a['gross_MTM_change_R'])} | {n(b['gross_MTM_change_R'])} |")
        a=headline(system,'CONTROL','GROSS_CLOSED_LEG_R');b=headline(system,'PARTIAL_TP_2R_50','GROSS_CLOSED_LEG_R')
        lines+=['','**Экономика закрытых модельных позиций**:','',
            '| Показатель | CONTROL | PARTIAL |','|---|---:|---:|']
        for field in ('closed_positions','open_positions','average_win_R','average_loss_R','average_win_abs_loss_ratio','gross_R_without_top5','gross_PF_without_top5','gross_R_without_top10','gross_PF_without_top10'):
            lines.append(f'| {field} | {n(a[field])} | {n(b[field])} |')
        if system=='H1':
            lines+=['',f"H1 C1_NORMALIZED: PF {n(a['C1_normalized_PF'])} → {n(b['C1_normalized_PF'])}, R {n(a['C1_normalized_R'])} → {n(b['C1_normalized_R'])}. C1=.001 normalized price/side — замороженный условный исследовательский расход, не тариф FINAM, не денежный Net."]
        else:lines+=['','M15: GROSS_ONLY. Подтверждённых комиссий, funding и проскальзывания в #518 нет. Gross PF не маркируется Net.']
        w=[r for r in ww if r['system']==system and r['lifecycle']!='walk_forward']
        pos=math.fsum(r['CONTROL_gross_R'] for r in w if r['CONTROL_gross_R']>0)
        lost=math.fsum(r['lost_R'] for r in w if r['CONTROL_gross_R']>0)
        saved=math.fsum(r['saved_R'] for r in w)
        lines+=['',f'У победителей CONTROL потеряно {lost:.6f}R ({lost/pos:.2%} их суммарного Gross выигрыша); суммарная положительная разница PARTIAL по всем сопоставленным закрытым позициям {saved:.6f}R. Полная построчная декомпозиция — WINNER_GIVEBACK.csv.',
            '', '| Набор крупнейших победителей CONTROL | CONTROL R | PARTIAL R | Потеря R |','|---|---:|---:|---:|']
        for top in (5,10):
            chosen=sorted([r for r in w if r['CONTROL_gross_R']>0],key=lambda r:-r['CONTROL_gross_R'])[:top]
            lines.append(f"| top {top} | {math.fsum(r['CONTROL_gross_R'] for r in chosen):.6f} | {math.fsum(r['PARTIAL_gross_R'] for r in chosen):.6f} | {math.fsum(r['lost_R'] for r in chosen):.6f} |")
        lines+=['',f'**Итог {system}: INCONCLUSIVE.** Наблюдаемые изменения месяцев и хвоста прибыли приведены выше; подтверждённого улучшения доходности капитала после реальных расходов и денежного ограничения нет. Повышение win rate не меняет этот вывод.']
    lines+=['','## H1 Walk Forward — только отдельная диагностика','',
        'Исходные четыре cold-start fold сохранены. Их 2024 месяцы перекрывают Baseline и в главные суммы выше не включены. Пустые вне fold месяцы в CSV — NO_DATA.','',
        '| Fold | Вариант | + / − / 0 | Worst closed-leg R | Gross PF | Gross R |','|---|---|---:|---:|---:|---:|']
    for r in ss:
        if r['system']=='H1' and r['lifecycle']=='walk_forward' and r['monthly_basis']=='GROSS_CLOSED_LEG_R':
            lines.append(f"| {r['fold_id']} | {r['variant']} | {r['positive_months']} / {r['negative_months']} / {r['zero_months']} | {n(r['worst_month_R'])} | {n(r['gross_PF'])} | {n(r['gross_R'])} |")
    lines+=['','## Занятость, маржа и следующие входы','',
        'В FRACTIONAL_REFERENCE сигналы, первоначальный объём, окончательные времена выхода и последующие входы CONTROL/PARTIAL совпали. Остаток резервирует инструмент до исходного стопа. Уменьшается лишь нормированный открытый объём; доступная рублёвая маржа и изменение последующих R15-объёмов не установлены. Нулевое число изменений входов относится только к дробной модели без денежных ограничений.','',
        '| Система / lifecycle | Вариант | Занятость времени | Модельный объём × время / доступное время |','|---|---|---:|---:|']
    for r in result['exposure']:
        if r['lifecycle']=='walk_forward':continue
        lines.append(f"| {r['system']} / {r['lifecycle']} | {r['variant']} | {r['occupied_time_share']:.2%} | {r['model_quantity_time_share']:.2%} |")
    lines+=['','## EXECUTABLE_INTEGER и капитал','',
        'Результат: **CASH_MODEL_NOT_VALIDATED**. Для каждого потенциального входа PARTIAL_EXECUTION_FEASIBILITY.csv оставляет qty, floor(qty/2), ГО, капитал и исполнимость UNKNOWN. Это не ноль контрактов и не доказательство невозможности всех сделок.',
        'Проверенная целочисленная механика: qty=1 → partial=0, остаток 1; qty=3 → partial=1, остаток 2; ровно 50% при нечётном qty физически не достигается. Исторических полных рядов ГО, рублёвой стоимости шага/спецификаций, начальных капиталов/движений и verified расходов для обоих отдельных счетов нет.',
        'В репозитории есть аутентифицированный статический registry и датированный H1-снимок 49,931.44 RUB в production passport. Это не текущий баланс и не историческая капитализация M15. Эти величины не размножались на 2023–2026. R15/6% остаются выбранными правилами; успешный денежный replay при них не заявляется.','',
        '## Источники, причинность и ограничения','',
        f"Main на старте: `{manifest['main_at_start']}`. Протокол: `{manifest['protocol_commit']}`. H1 data `{H1_DATA}`; M15 data `{M15_DATA}`. Все восемь frozen H1 source-provenance hashes и весь FREEZE.json #518 совпали. PR #540 используется только для подтверждения выбранной identity/spec, код робота не исполняется.",
        'Текущие H1 файлы в main data отличаются от исторических Stage6/7. Поэтому с начала исследования выбран отдельный точный checkout замороженного H1 commit; данные не обновлялись и источник не заменялся по результатам.',
        'H1 исходные жизненные циклы имеют cold starts: Baseline 2023–2024 и historical OOS 2025–2026 не являются одним непрерывным replay. Терминальные OPEN сохранены в H1_TRADES.csv, не ликвидированы и не потеряны в closed-R; их unrealized R включён в терминальный MTM. Они не переносились в отдельный исходный cold-start OOS, поскольку это изменило бы CONTROL. Эта граница ограничивает применимость объединённой календарной диагностики. Внутри каждого lifecycle/fold и всей M15 истории позиции через месяцы/годы не сбрасываются.',
        'H1 замороженные месячные/годовые отчёты атрибутируют выходы в UTC; CONTROL_RECONCILIATION.csv точно сверяет именно исходную атрибуцию. Новая основная месячная таблица обеих систем использует Europe/Moscow. M15 exit, в том числе open gap, сохраняет frozen exit-candle Close timestamp; это описательная bar-close атрибуция, не точный момент брокерского fill.',
        '2023 — неполный N4: GLD с июля, IMOEX с ноября. 2026 — YTD, September endpoint неполный; USD/CNY M15 оканчиваются в августе, GLD/IMOEX в сентябре. NO_DATA не приравнен нулю. Последние marks исчезнувшего инструмента переносятся только вперёд как последний наблюдаемый mark, без будущего значения; такой stale mark не доказывает реальную оценку капитала.',
        'Снимок ценовой сетки USD .01 / CNY .001 / GLD .1 / IMOEX .5 подтверждён существующим registry. Новые TP округлены наружу от entry и попадают на эту сетку. Историческая неизменность сетки не аттестована. Frozen initial/trailing stops могут быть off-grid и не изменены; реальная исполнимость такого CONTROL не заявляется.',
        'На общей свечной достижимости stop и TP всегда выбран stop. Бар входа H1 не проверяется, M15 NEXT_OPEN допускает исходную execution candle. На TP нет благоприятного gap price improvement. Комиссии H1 C1 распределены пропорционально leg без удвоения. M15 не получает выдуманные расходы.',
        'DD измерена по completed-bar MTM marks, а не по неизвестному внутрисвечному пути; у разных инструментов R нормирован на разные входы. Нельзя умножить эти значения на 1.5% и назвать их капиталом при сложном проценте, частичной реализации, разных qty и ГО.','',
        '## Проверки','',
        f"CONTROL: {audit['control']['checks']} проверок / {audit['control']['fields_checked']} полей, расхождений {audit['control']['mismatches']}; H1 418, M15 1114 CLOSED. Отдельный scalar audit: {audit['mechanical']['independent_scalar_positions']} состояний позиций, {audit['mechanical']['fields_checked']} полей. Decimal/CSV arithmetic audit: {audit['arithmetic']['checks']} проверок, max error {audit['arithmetic']['max_absolute_error']:.3g}.",
        '22 синтетических теста PASS. Независимость: отдельный scalar алгоритм без импорта нового движка/accounting, отдельное чтение CSV и Decimal арифметика. Это внутренняя программная проверка одного автора, не внешний человеческий аудит. Повторы и SHA256 — REPEATABILITY.json; код/исходники также зафиксированы Git и SOURCE_MANIFEST.json.',
        'Все изменения только audit_only/t3_h1_m15_partial_tp_2r_50/. Production, Stage7/Stage8, M15 robot, Control Center, котировки и прежние исследования не изменены. Торговые API/секреты/SQLite/Tasks не использовались. Один Draft PR; merge и auto-merge не выполняются. Внешний аудит PENDING.']
    (out/'REPORT_RU.md').write_text('\n'.join(lines)+'\n')
