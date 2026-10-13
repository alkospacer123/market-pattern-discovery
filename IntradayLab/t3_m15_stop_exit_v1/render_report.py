"""Reproducible presentation of already frozen replay results; no strategy logic."""
import json
from pathlib import Path
import hashlib
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

HERE=Path(__file__).resolve().parent
ROOT=HERE/'results'
RULES=('CONTROL','S1','S2','S3')
VERSIONS=('BASELINE','OPTIMIZED')
SYMBOLS=('USDRUBF','CNYRUBF','GLDRUBF','IMOEXF')
matplotlib.rcParams['svg.hashsalt']='t3_m15_stop_exit_v1'
matplotlib.rcParams.update({'font.size':10,'axes.spines.top':False,'axes.spines.right':False})


def load(name):return pd.read_csv(ROOT/(name+'.csv'))
def fmt(x):
    if x is None or pd.isna(x):return '—'
    if isinstance(x,(float,np.floating)):return f'{x:.3f}'
    return str(x)
def table(f,columns):
    # Each tuple is (field, displayed name).
    out=['| '+' | '.join(label for field,label in columns)+' |','|'+'|'.join('---' for c in columns)+'|']
    out.extend('| '+' | '.join(fmt(row[field]) for field,label in columns)+' |' for row in f.to_dict('records'))
    return '\n'.join(out)+'\n'
def dump(name,obj):(HERE/name).write_text(json.dumps(obj,sort_keys=True,indent=2,allow_nan=False)+'\n')

def charts(overall,years,monthly,trades):
    fig,axes=plt.subplots(1,2,figsize=(12,4.2),sharey=True,layout='constrained')
    colors={'2023':'#356cab','2024':'#db8039','ALL':'#309187'}
    for ax,v in zip(axes,VERSIONS):
        for off,period in [(-.23,'2023'),(0,'2024'),(.23,'ALL')]:
            values=[]
            for r in RULES:
                f=overall if period=='ALL' else years[years.year.eq(int(period))]
                values.append(float(f[f.version.eq(v)&f.rule.eq(r)].gross_PF.iloc[0]))
            ax.bar(np.arange(4)+off,values,width=.22,label=period,color=colors[period])
        ax.axhline(2,color='#444',linestyle='--',linewidth=1,label='Research goal 2.0')
        ax.set_xticks(range(4),RULES);ax.set_title(v);ax.set_ylim(0,2.25);ax.grid(axis='y',alpha=.2)
    axes[0].set_ylabel('Gross PF — all four instruments');axes[1].legend(fontsize=8)
    fig.savefig(HERE/'gross_pf.svg',metadata={'Date':None});plt.close(fig)
    months=sorted(monthly.month.unique())
    labels=[v+' / '+r for v in VERSIONS for r in RULES]
    values=np.array([[float(monthly[monthly.version.eq(v)&monthly.rule.eq(r)&monthly.month.eq(m)].gross_R.iloc[0]) for m in months] for v in VERSIONS for r in RULES])
    fig,ax=plt.subplots(figsize=(16,5),layout='constrained')
    scale=float(abs(values).max());im=ax.imshow(values,cmap='RdBu',vmin=-scale,vmax=scale,aspect='auto')
    ax.set_xticks(range(len(months)),months,rotation=55,ha='right',fontsize=8);ax.set_yticks(range(8),labels)
    for y in range(8):
        for x in range(len(months)):ax.text(x,y,f'{values[y,x]:.1f}',ha='center',va='center',fontsize=7,color='white' if abs(values[y,x])>scale*.55 else '#222')
    ax.set_title('Monthly closed-trade Gross R — complete available 2023–2024, all four instruments')
    fig.colorbar(im,ax=ax,label='Gross R');fig.savefig(HERE/'monthly_gross_R.svg',metadata={'Date':None});plt.close(fig)
    fig,axes=plt.subplots(1,2,figsize=(12,4),layout='constrained')
    for ax,v in zip(axes,VERSIONS):
        for r,color in [('CONTROL','#68788a'),('S1','#247c6b')]:
            f=trades[trades.version.eq(v)&trades.rule.eq(r)].sort_values(['exit_time','instrument','trade_id'],kind='mergesort')
            times=pd.to_datetime(f.exit_time,utc=True)
            ax.plot(times,f.gross_R.cumsum(),label=r,color=color,linewidth=1.3)
        ax.set_title(v);ax.set_ylabel('Cumulative CLOSED Gross R');ax.legend();ax.grid(alpha=.2)
    fig.suptitle('Bookkeeping sequence, not capital / mark-to-market portfolio equity')
    fig.savefig(HERE/'control_s1_closed_R.svg',metadata={'Date':None});plt.close(fig)


def main():
    all_scope=load('overall_report');overall=all_scope[all_scope.scope.eq('ALL_FOUR')]
    all_years=load('yearly_report');years=all_years[all_years.scope.eq('ALL_FOUR')]
    monthly=load('monthly_report');pool_monthly=monthly[monthly.scope.eq('ALL_FOUR')]
    directions=load('direction_report');nov=load('november_dependence');changes=load('winner_loss_changes')
    attribution=load('gross_R_attribution');activation=load('activation_report');winners=load('large_winners')
    trades=load('trades');charts(overall,years,pool_monthly,trades)
    source=json.loads((ROOT/'SOURCE_MANIFEST.json').read_text())
    core=[('version','Версия'),('rule','Механика'),('gross_PF','Gross PF'),('gross_R','Gross R'),('gross_expectancy_R','Exp R'),('closed_trades','CLOSED'),('open_terminal_positions','terminal OPEN')]
    annual_core=core[:2]+[('year','Период')]+core[2:]
    combined=pd.concat([years,overall.assign(year='ALL')],ignore_index=True).sort_values(['version','rule','year'],key=lambda x:x.astype(str),kind='mergesort')
    notes=[]
    notes.append('''# T3/M15 Stop & Exit v1 — экспериментальный отчёт

**COSTS_DEFERRED / GROSS_ONLY / NOT_LIVE_READY. Внешний review и решение пользователя: PENDING. Draft PR, STOP без merge/auto-merge.**

Исследовательская цель **не достигнута**: ни S1, ни S2, ни S3 не дают полного Gross PF ≥2 на четырёх инструментах. S1 даёт наиболее полезный standalone вклад в Gross R 2024 при небольшом изменении Gross R 2023, но увеличивает просадку и остаётся ниже PF 2. S2 уменьшает убытки ценой более сильного сокращения победителей. S3 ограничивает часть трендов, а новые входы преимущественно ухудшают итог. Все исходы сохранены; параметры после просмотра результатов не подбирали.

## База, preregistration и область данных

Фактический GitHub `main` перед началом совпал с ожидаемым `bc4f95f48b332f43d79ed10f26fc03c5ad01cd97` (merged #495); изменений после него нет. Данные `market-pattern-data` @ `f8486b446cf3d5f9f3cba6dfec32bdef8fd184c8` чистые и read-only. Спецификация и SHA зафиксированы **до любых результатов этого пакета** в коммите `d6728adac580070a69c7ea9b33b1f7f9fe59cd73`; причинный engine, unit-тесты и независимый auditor зафиксированы перед S-результатами в `4beb8813`.

Использован весь фактически доступный M15 prefix 2023–2024. Перед первой строкой 2025+ проверяется только timestamp, OHLC этой строки не загружается. Полные исходные SHA-256 вычисляются как непрозрачные байты для целостности; это не чтение будущих OHLC для анализа. **2023 и 2024 — development-exposed; 2024 не является независимым WF.**''')
    notes.append(table(pd.DataFrame(source['sources']),[('instrument','Инструмент'),('first_close','Первый Close MSK'),('last_close','Последний Close MSK'),('used_candles','M15')]))
    notes.append('''## Фиксированные механики и исполнение

| Механика | Правило |
|---|---|
| CONTROL | Изначальный Stop 2 ATR, оригинальный ATR trailing: BASELINE 3.0, OPTIMIZED 3.5. |
| S1 TRAIL_AFTER_1R | До подтверждённого +1 первоначального R Stop фиксирован. После пережитой завершённой свечи разрешён оригинальный trailing по накопленному с входа благоприятному экстремуму. |
| S2 BREAK_EVEN_1R | Оригинальный trailing действует всегда; после пережитой свечи с +1R Stop ужесточён не хуже входа. |
| S3 LOCK_1R_AFTER_2R | Оригинальный trailing действует всегда; после пережитой свечи с +2R Stop ужесточён не хуже входа +1 первоначальный R. |

SHORT полностью зеркален. Первоначальный риск неизменен: `abs(entry-initial_stop)`; равенство порогу проходит. EMA75, H1, ADX14>20, Donchian20, ATR14, H1 ATRMean20, slope lookback5 и остальные исходные параметры не менялись. Нет S-комбинаций или A6/A7-фильтра.

Сначала исполняется старый действующий Stop: неблагоприятный gap Open, затем intrabar Low для LONG / High для SHORT. **На Stop-свече не обновляются экстремумы, активация и новый Stop.** Пережитая полная свеча подтверждает порог и ratchet, новый Stop действует на следующей фактической свече. Возврат через новый Stop внутри trigger-свечи не вызывает ретроактивного выхода. Stop никогда не ослабляется. Signal High/Low не входят в после-входной экстремум.

Сохраняются исходные Close-входы и same-Close re-entry после Stop; физическая исполнимость входа ровно по signal Close не доказана. Непрерывные Stop-цены не приводятся к tick grid. Protective exit сохраняет историческую метку Close свечи; точный intrabar timestamp неизвестен. Межсессионные/выходные/годовые переходы переносят состояние, риск и Stop без reset или forced flat. Нет искусственных свечей и терминальной ликвидации.

## Воспроизведение контроля

**PASS: 741 BASELINE + 701 OPTIMIZED = 1 442 CLOSED и по одной terminal OPEN IMOEXF.** С #490 сверены все 19 исходных полей механики; с #495 — все 39 общих полей gross-only контроля, включая сигнал, контекст, Stop, выходы, порядок и occupancy-связанные метки. Все исходные поля terminal OPEN сохранены. Расхождений 0 при абсолютном числовом допуске 1e-8; максимальное отличие цены 5.46e-12. Старые C1/net поля исключены из этого gross-only сопоставления; расходы здесь не вычисляются и не вычитаются. [Машинный контроль](results/CONTROL_REPRODUCTION.json), [пустой diff](results/CONTROL_DIFF.csv).

## Полный период и оба календарных года

Год/месяц CLOSED определяется исторической меткой выхода MSK. Terminal OPEN относится к году/месяцу входа и не означает snapshot на конец каждого года. Каждая из восьми version/mechanic имеет одну terminal OPEN IMOEXF; её unrealized Gross R приводится отдельно и не прибавляется к CLOSED Gross R. [OPEN_POSITIONS](results/OPEN_POSITIONS.json).

Gross PF = сумма положительных Gross R / абсолютная сумма отрицательных Gross R; нулевые сделки не входят в эти суммы. `—` означает неопределённый PF без отрицательной суммы (не PF=0), либо отсутствие значения. Expectancy = сумма Gross R / CLOSED. Сумма R по четырём инструментам — учётная сумма нормированных сделок, **не доходность портфеля**.''')
    notes.append(table(combined,annual_core))
    notes.append('''![Gross PF for 2023, 2024 and full period](gross_pf.svg)

## Регулярность, худшие месяцы, losing streak и closed-trade DD

Все фактически доступные месяцы включены, в том числе нулевые; GLD/IMOEX не получают искусственные месяцы до запуска. `L trade` — максимальная серия CLOSED с Gross R<0; нулевая/положительная сделка сбрасывает серию. `L month` — отрицательные месяцы подряд. DD рассчитан по cumulative CLOSED R с началом в нуле, в порядке `exit_time / instrument / trade_id`, без mark-to-market открытого риска.''')
    notes.append(table(combined,[('version','Версия'),('rule','Механика'),('year','Период'),('positive_months','+'),('negative_months','−'),('zero_months','0'),('worst_month','Худший месяц'),('worst_month_R','R худшего'),('max_losing_trade_streak','L trade'),('max_losing_month_streak','L month'),('max_drawdown_R','DD R')]))
    notes.append('![Monthly Gross R](monthly_gross_R.svg)\n\n![Control and S1 closed-trade R](control_s1_closed_R.svg)')
    notes.append('''## Концентрация и удаление крупнейших победителей

Top5/Top10 доли относятся к сумме **положительных** R. Удаление победителей — диагностическая чувствительность того же replay, не новый запуск или стратегия.''')
    notes.append(table(combined,[('version','Версия'),('rule','Механика'),('year','Период'),('top5_share_positive_R','Top5/+R'),('top10_share_positive_R','Top10/+R'),('gross_R_without_top5','R без top5'),('gross_PF_without_top5','PF без top5'),('gross_R_without_top10','R без top10'),('gross_PF_without_top10','PF без top10')]))
    notes.append('''## Четыре инструмента: 2023, 2024 и полный период

Ни один инструмент не исключён. Все годовые частоты, expectancy, терминальные OPEN и gross-показатели доступны ниже; полный набор концентрации, календаря и риска — в [INSTRUMENT_DIRECTION_DETAIL](INSTRUMENT_DIRECTION_DETAIL.md) и CSV.''')
    instrument=pd.concat([all_years[all_years.scope.ne('ALL_FOUR')],all_scope[all_scope.scope.ne('ALL_FOUR')].assign(year='ALL')],ignore_index=True)
    notes.append(table(instrument,annual_core[:3]+[('scope','Инструмент')]+annual_core[3:]))
    notes.append('## LONG/SHORT: все четыре инструмента вместе\n')
    notes.append(table(directions[directions.scope.eq('ALL_FOUR')],annual_core[:3]+[('direction','Направление')]+annual_core[3:]))
    notes.append('''По каждому инструменту LONG/SHORT для 2023/2024/ALL — [INSTRUMENT_DIRECTION_DETAIL](INSTRUMENT_DIRECTION_DETAIL.md); каждый календарный месяц отдельно для инструмента и направления — [MONTHLY_DETAIL](MONTHLY_DETAIL.md) и [monthly_direction_report.csv](results/monthly_direction_report.csv).''')
    notes.append('## Исходные CLOSED ≥2R: сохранённые, потерянные и уменьшенные\n\nСопоставление по точным `version/instrument/direction/entry_time`. Сохранённые: новый R не меньше исходного с допуском 1e-8; это сохранность результата, не гарантия идентичной длительности. «Потеря» означает отсутствие исходного входа из-за новой хронологии occupancy; «сокращены» — присутствующий вход с меньшим R. OPEN выделяется отдельно. Это диагностика, не входной фильтр.\n')
    pool_change=changes[changes.scope.eq('ALL_FOUR')]
    notes.append(table(pool_change,[('version','Версия'),('rule','Механика'),('year','Исх. год'),('original_trend_winners','Исх. ≥2R'),('trend_fully_preserved','Сохранены'),('trend_entries_lost','Потеря входа'),('trend_outcomes_reduced','Сокращены'),('trend_open_unresolved','OPEN'),('trend_turned_nonpositive','Стали ≤0'),('trend_reduced_below_2R','Стали <2R')]))
    notes.append('## Изменение исходных убытков и новые входы\n')
    notes.append(table(pool_change,[('version','Версия'),('rule','Механика'),('year','Исх. год'),('original_losses','Исх. убытков'),('loss_entries_eliminated','Нет входа'),('losses_reduced_or_reversed','Улучшены'),('losses_worsened','Ухудшены'),('losses_unchanged','Без изменения'),('losses_open_unresolved','OPEN'),('matched_original_loss_R_change','Δ matched loss R'),('new_entries','Новых CLOSED'),('new_open_entries','Новых OPEN'),('new_entry_positive_R','Новые +R'),('new_entry_negative_R','Новые −R объём')]))
    notes.append('## Полное разложение изменения Gross R\n\nМатчинг исходных победителей и убытков, отсутствующие CLOSED исходы и новые CLOSED входы объясняют полный Δ R. Годовые перенесения отдельно сохранены в CSV; в этом запуске они нулевые. [gross_R_attribution.csv](results/gross_R_attribution.csv) содержит проверяемое равенство всех компонентов и итогового Δ.\n')
    notes.append(table(attribution[attribution.scope.eq('ALL_FOUR')&attribution.year.eq('ALL')&attribution.rule.ne('CONTROL')],[('version','Версия'),('rule','Механика'),('matched_original_winners_delta_R','Δ исх. победителей'),('matched_original_losses_delta_R','Δ исх. убытков'),('matched_zero_delta_R','Δ нулевых'),('absent_closed_outcome_delta_R','Отсутствующие исходы'),('new_closed_entry_R','Новые CLOSED R'),('gross_R_change','Полный ΔR')]))
    notes.append('## Ноябрь 2024 и 2024 без ноября: только диагностическая чувствительность\n\nУдаление ноября не меняет replay, не создаёт новую выборку для отбора и не является Robustness/WF. Полные чувствительности каждого инструмента — в CSV.\n')
    notes.append(table(nov[nov.scope.eq('ALL_FOUR')],[('version','Версия'),('rule','Механика'),('gross_PF_2024','PF 2024'),('gross_R_2024','R 2024'),('november_trades','CLOSED ноября'),('november_PF','PF ноября'),('november_R','R ноября'),('ex_november_PF','PF без ноября'),('ex_november_R','R без ноября'),('ex_november_positive_months','+мес без ноября'),('ex_november_max_drawdown_R','DD без ноября')]))
    notes.append('''## Причины результата каждой механики

**S1.** Более позднее разрешение trailing позволяет части исходных проигрышей восстановиться; итоговый matched-loss эффект +29.640R / +24.308R (BASELINE / OPTIMIZED) на полном периоде. Однако 136 / 85 matched-убытков становятся хуже, в то время как улучшаются только 44 / 33: улучшение суммы обеспечивают более крупные изменения отдельных исходов. В 2024 matched-loss вклад +34.489R / +24.826R, но longer occupancy устраняет 3 / 2 исходных победителя ≥2R и другие исходы. Новых входов нет, CLOSED 741→718 / 701→689. 78/81 и 88/90 крупных исходных победителей сохранены, уменьшенных matched ≥2R нет. R 2023 −1.616R (−1.7%) / +1.060R (+1.1%). Все четыре инструмента в 2024 остаются положительными, но BASELINE IMOEXF чуть ухудшается; OPTIMIZED SHORT 2024 R 30.666→29.963 тоже не улучшается.

S1 повышает 2024 R 50.206→74.132 / 80.102→97.030 и PF 1.230→1.318 / 1.363→1.424. BASELINE плюс месяцев 2024 6→8; OPTIMIZED 8→8. 2024 без ноября −0.322→+24.883 / +25.916→+43.958R. Top10 концентрация полного периода слегка ниже контроля. **Цена улучшения:** full/2024 DD 23.677→26.510 / 26.126→28.471R, частота ниже; цель PF 2 остаётся недостигнутой. Отложенный trailing не устраняет все ранние слабые входы: до +1R остаётся полный исходный риск.

**S2.** BE улучшает 75 / 88 исходных убытков без ухудшения matched-убытков; matched-loss вклад +22.320 / +34.862R. Но matched-победители теряют −36.938 / −62.441R: 5 / 11 исходных ≥2R превращаются в неположительные исходы. Новые 12 / 20 CLOSED дают только +5.993 / +12.649R нетто gross. Полный ΔR −8.624 / −14.929; PF почти не меняется, expectancy и R ниже. Концентрация растёт; OPTIMIZED теряет две положительные календарные месячные суммы в 2023. В 2024 BASELINE USD становится отрицательным (−4.127R). BE защищает уже развившееся движение ценой преждевременного выхода из части трендов. Gap может исполнить ниже BE, поэтому активация не обещает безубыточность.

**S3.** Исходные убытки почти не затрагиваются: вклад 0 / +1.049R, поскольку +2R достигнут лишь частью сделок. По 6 исходных ≥2R имеют уменьшенный результат; у ORIGINAL ≥2R нет потерянных входов и неположительных matched-выходов. LOCK может сохранить прибыль после разворота, но также раньше закрывает продолжающийся тренд. Новые 10 / 14 CLOSED дают −3.897 / −6.141R. Полный ΔR −7.673 / −1.924; PF ниже обоих контролей. 2024 OPTIMIZED R слегка выше (+0.431R), PF ниже, DD лучше; этого недостаточно для устойчивого улучшения двух версий. Lock +1R не гарантирует +1R fill при неблагоприятном gap.

Это объяснение **детерминированных изменений данной модели**, не доказательство причин рыночного режима или универсального преимущества. Численные правила не менялись после просмотра исходов.''')
    notes.append('## Активации и последний источник Stop при выходе\n\n«Последний источник» — последнее строгое ужесточение Stop; равные предложения сохраняют прежний источник. `updates` считает любое изменение Stop (ATR или BE/LOCK). Полный bar-by-bar журнал сохраняет все проверки и предложения.\n')
    notes.append(table(activation[activation.scope.eq('ALL_FOUR')&activation.year.eq('ALL')],[('version','Версия'),('rule','Механика'),('closed_trades','CLOSED'),('threshold_activated_trades','Порог активирован'),('initial_stop_exits','Initial Stop'),('ATR_TRAIL_last_stop','ATR Stop'),('BE_last_stop','BE Stop'),('LOCK_last_stop','LOCK Stop'),('gap_exits','Gap'),('activated_nonpositive_exits','Активирован и R≤0')]))
    notes.append('## A6/A7: неизменные исторические ориентиры #495\n\nОни не запускались в этом пакете и не комбинировались с S1/S2/S3. Строки перенесены из frozen CSV #495 без изменения значений; независимый auditor сравнивает каждую строку. Старые дополнительные поля отчётов сохраняют исходное значение/определение.\n')
    hist=pd.concat([load('historical_A6_A7_yearly_report').query("scope == 'ALL_FOUR'"),load('historical_A6_A7_overall_report').query("scope == 'ALL_FOUR'").assign(year='ALL')],ignore_index=True)
    notes.append(table(hist,annual_core))
    notes.append('''S1 сохраняет больше полного Gross R и 2023 R, чем исторический A6, но его PF ниже и DD выше. Сравнение не разрешает комбинаций. A6/A7 также не дают полного PF 2; выбор следующей работы остаётся за пользователем после review.

## Качество, аудит и повторяемость

20 причинных unit-тестов PASS до просмотра вариантов. Тесты включают LONG/SHORT, Stop-before-ratchet и Stop-before-activation, точные BE/LOCK пороги, благоприятный экстремум сигнальной/Stop-свечи, same-bar ambiguity, gap до/после активации, immutable risk, отсутствие ослабления Stop, обе версии trailing, terminal OPEN, same-Close re-entry/occupancy, сессии/выходные/границу года, H1 gaps и prefix-invariance, запрет парсинга 2025+ OHLC.

Отдельный standard-library auditor заново читает только разрешённый raw prefix, независимо вычисляет рекурсивные ATR/EMA/ADX, H1 и Donchian, затем полный replay. Он реконструирует extrema из пережитого пути, независимо выбирает ratchet и проверяет каждую закрытую сделку, каждую Stop-проверку/активацию, все occupancy решения и terminal OPEN. Также заново сверяет все поля центральных отчётов, lineage, winner/loss, ноября, активаций, R attribution, A6/A7-истории, источников и SHA. Числовой допуск 1e-8, ненумерические поля точно.

**Аудит реализации выполнен тем же автором; внешний независимый человеческий review остаётся PENDING.** Это не заменяется словом PASS. Два свежих процесса повторяют все generated артефакты с прямым сравнением bytes и SHA-256. Подробности: [INDEPENDENT_AUDIT](INDEPENDENT_AUDIT.md), [AUDIT_RESULTS](AUDIT_RESULTS.json), [REPEATABILITY](REPEATABILITY.json), [TEST_RESULTS](TEST_RESULTS.txt), [SCOPE_CHECK](SCOPE_CHECK.json).

## Артефакты и ограничения

[EXPERIMENT_SPECS](EXPERIMENT_SPECS.json), [PREREGISTRATION](PREREGISTRATION.json), [SOURCE_MANIFEST](results/SOURCE_MANIFEST.json), [GENERATED_SHA256](results/GENERATED_SHA256.json), [ARTIFACT_SHA256](ARTIFACT_SHA256.json) фиксируют параметры, код, данные и результаты.

Полный общий [журнал CLOSED](results/trades.csv), отдельные CONTROL/S1/S2/S3, [bar-by-bar Stop](results/stop_decisions.csv), [входы/occupancy](results/entry_opportunities.csv), [lineage](results/trade_lineage.csv), [winner/loss](results/winner_loss_changes.csv) и [top5/top10 исходных победителей](results/large_winners.csv) доступны для review. Все gross метрики в `overall/yearly/monthly/instrument/direction/monthly_direction_report.csv`, включая OPEN, expectancy, форму выигрышей/убытков, календарь, losing streak, DD и концентрацию.

Рыночные CSV не копируются в discovery. Изменения только в новом `IntradayLab/t3_m15_stop_exit_v1/`; исходные исследования, ROADMAP, TradingSystemLab, data, robot, конфигурации брокера и реальные счета не изменяются. Нет Optimization, Robustness, Walk Forward, TRUE OOS, LIVE, следующих комбинаций или порогов. Нет C1, комиссий, spread/slippage/funding или иных вычетов. Это gross-only исследование, не deployable net economics. Следующее действие — внешний review и решение пользователя; **STOP на Draft PR**.''')
    (HERE/'EXPERIMENT_REPORT.md').write_text('\n\n'.join(notes)+'\n')
    risk_cols=[('positive_months','+мес'),('negative_months','−мес'),('zero_months','0мес'),('worst_month','Худший'),('worst_month_R','R худшего'),('max_losing_trade_streak','L trade'),('max_losing_month_streak','L month'),('max_drawdown_R','DD R')]
    concentration_cols=[('top5_share_positive_R','Top5/+R'),('top10_share_positive_R','Top10/+R'),('gross_R_without_top5','R −top5'),('gross_PF_without_top5','PF −top5'),('gross_R_without_top10','R −top10'),('gross_PF_without_top10','PF −top10')]
    detail=['# Инструменты и направления — полный диагностический набор\n\nGROSS_ONLY / COSTS_DEFERRED / NOT_LIVE_READY. Год CLOSED по выходу; terminal OPEN по входу. ALL = полный период. Полный контекст и определения — EXPERIMENT_REPORT.md.']
    ids=[('version','Версия'),('rule','Механика'),('scope','Инструмент'),('year','Период')]
    detail += ['## Каждый инструмент: календарь и риск',table(instrument,ids+risk_cols),'## Каждый инструмент: концентрация и удаление победителей',table(instrument,ids+concentration_cols)]
    for label,extra in [('PF/R/expectancy/частота',core[2:]),('Календарь/риск',risk_cols),('Концентрация',concentration_cols)]:
        detail += ['## LONG/SHORT: '+label,table(directions,ids+[('direction','Направление')]+extra)]
    detail += ['## Изменения исходных ≥2R и убытков: каждый инструмент и год',table(changes,[('version','Версия'),('rule','Механика'),('scope','Инструмент'),('year','Период'),('trend_fully_preserved','≥2R сохранены'),('trend_entries_lost','≥2R нет входа'),('trend_outcomes_reduced','≥2R сокращены'),('losses_reduced_or_reversed','Убытки улучшены'),('losses_worsened','Убытки хуже'),('new_entries','Новых CLOSED')]),'## Top5/Top10 исходные cohort',table(winners,[('version','Версия'),('rule','Механика'),('scope','Инструмент'),('year','Период'),('top_n','Top N'),('original_positive_R','Исх. R'),('entries_lost','Нет входа'),('fully_preserved','Сохранены'),('reduced','Сокращены'),('open_unresolved','OPEN'),('matched_variant_R','Matched R')])]
    (HERE/'INSTRUMENT_DIRECTION_DETAIL.md').write_text('\n\n'.join(detail)+'\n')
    detail=['# Каждый доступный календарный месяц\n\nGROSS_ONLY / COSTS_DEFERRED / NOT_LIVE_READY. MSK, CLOSED по выходу; OPEN — terminal по месяцу входа, не historical snapshot. До позднего старта нет искусственных месяцев. PF — при отсутствии negative R не определён.']
    cols=[('month','Месяц')]+core[2:]
    md=load('monthly_direction_report')
    for v in VERSIONS:
        for r in RULES:
            for s in ('ALL_FOUR',*SYMBOLS):
                f=monthly[monthly.version.eq(v)&monthly.rule.eq(r)&monthly.scope.eq(s)]
                detail += [f'## {v} / {r} / {s}',table(f,cols)]
                f=md[md.version.eq(v)&md.rule.eq(r)&md.scope.eq(s)]
                detail += [table(f,[('month','Месяц'),('direction','Направление')]+core[2:])]
    (HERE/'MONTHLY_DETAIL.md').write_text('\n\n'.join(detail)+'\n')
    objective={'status':'OBJECTIVE_NOT_REACHED','full_period_target_gross_PF':2.0,'all_four_instruments':True,
        'any_standalone_full_period_PF_ge_2':bool((overall[overall.rule.ne('CONTROL')].gross_PF>=2).any()),
        'S1_2024_all_four_positive_gross_R_both_controls':bool((all_years[all_years.rule.eq('S1')&all_years.year.eq(2024)].gross_R>0).all()),
        'retrospective_thresholds_added':False,'qualitative_tradeoffs':'S1 improves 2024 R but increases DD and loses some entries; S2/S3 do not improve both controls consistently.',
        '2024_independent_WF':False,'external_audit':'PENDING','next_action':'STOP_EXTERNAL_REVIEW_USER_DECISION',
        'labels':['GROSS_ONLY','COSTS_DEFERRED','NOT_LIVE_READY'],
        'full_period':[{'version':r.version,'rule':r.rule,'gross_PF':r.gross_PF,'gross_R':r.gross_R,'closed':int(r.closed_trades),'open_terminal':int(r.open_terminal_positions)} for r in overall.itertuples()]}
    dump('OBJECTIVE_ASSESSMENT.json',objective)
    # Matplotlib emits trailing spaces in SVG path coordinates. Canonicalize
    # presentation bytes without changing the rendered geometry or table values.
    for name in ('EXPERIMENT_REPORT.md','INSTRUMENT_DIRECTION_DETAIL.md','MONTHLY_DETAIL.md',
                 'gross_pf.svg','monthly_gross_R.svg','control_s1_closed_R.svg'):
        target=HERE/name
        target.write_text('\n'.join(line.rstrip() for line in target.read_text().splitlines()).rstrip()+'\n')
    dump('PRESENTATION_SHA256.json',{p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in sorted(HERE.iterdir()) if p.suffix in ('.md','.svg')})
    print(json.dumps({'presentation':'COMPLETE','objective':objective['status']},sort_keys=True))

if __name__=='__main__':main()
