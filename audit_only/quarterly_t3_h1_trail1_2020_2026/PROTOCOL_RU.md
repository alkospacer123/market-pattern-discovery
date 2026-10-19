# Протокол EXPLORATORY REPLAY — продолжение PR #555

Дата: 19.10.2026, Europe/Moscow. Исходный main: `38489db7e69336548a583f968f13aab49c20913b`. Прежний DATA_BLOCKED preflight: commit `7404fc23f2e92344fd5aea66924b74410f777ebe`, полный байтовый снимок в `prior_preflight/`.

## Разрешённый допуск и пять состояний

Пользователь явно разрешил описательный исторический расчёт на шести исходных рядах без паспорта склейки. Отсутствие паспорта больше не блокирует вычисления этого эксперимента. Оно не считается устранённым и блокирует валидацию физической торгуемой доходности. Это изменение допуска исследовательских данных, не стратегии.

Состояния независимы: COMPUTATIONAL_AUDIT=PASS/FAIL, SOURCE_INTEGRITY=PASS/FAIL, ROLL_PROVENANCE=UNVERIFIED, EXPLORATORY_REPLAY=COMPLETE/INCOMPLETE, TRADABLE_QUARTERLY_PERFORMANCE=NOT_VALIDATED. Положительный PF не определяет ни одно состояние аудита. Экономическое утверждение относится только к выборочному среднему предоставленных рядов.

## Источники и convention

Ровно шесть файлов `/workspace/market-pattern-data/futures_quarterly/{instrument}/{instrument}_H1.csv`: Si, CNY, GD, MIX, BR, NG. PRIMARY4=Si/CNY/GD/MIX, ADDITIONAL2=BR/NG, ALL6=все. Никакого отбора по результату.

SHA256 проверяется против прежнего source audit, Stage5 identity и оригинального data commit. До loading проверяются исходный порядок, уникальность timestamps, конечность чисел и OHLC geometry. Поскольку source order строгий и дубликатов нет, сортировка/дедупликация DataLoader ничего не меняет. Источник read-only; свечи не копируются в GitHub. Исходный файл после исполнения повторно хешируется.

Принято исследовательское допущение open-labelled H1 / Europe/Moscow, close availability=open+1h. Поставщик его не подтвердил. Последний доступный close — 16.09.2026 00:00+03:00; позже свечей нет. CNY начинается 21.04.2022 11:00+03:00. Подозрительные свечи и гэпы не удаляются и не исправляются; новая склейка не строится. Исторический аудит качества и неизвестная roll provenance сохраняются.

## Неизменённая Stage7

`T3_H1_candidate_v3`, `T3-H1-4e73cdb77246`, production reference `TRAIL1__N4_01__FULL__R15`. Полный набор: EMA100, slope lookback5, ADX period14/threshold20, breakout20, ATR14, ATR average20, stop_atr2.5, trail_atr3.0. Шестиполевой candidate payload с SHA256 `4e73cdb77246cb07b5953160b9fc0ab36bfd4bd6d9a7f7faaae7e6e392ee340a` дополняется frozen defaults; все девять значений сверяются со Stage7. Source hashes и восемь provenance-файлов должны совпасть.

H4 — четыре завершённых наблюдаемых H1 внутри локального дня, публикация на последнем close; это не новая четырёхчасовая resample-сетка. Donchian — предыдущие 20 H1 без текущего бара. Вход SIGNAL_CLOSE. На entry bar нет управления позицией. Одна позиция на рынок, без пирамидинга. Первоначальный риск фиксирован. TRAIL1 наблюдает +1R на завершённом post-entry баре и активирует сохранённый candidate только перед следующим событием. Стоп tighten-only. Сначала входящий stop test, потом extrema/candidate. LONG gap fill=min(open,stop), SHORT=max(open,stop). EXIT раньше независимого нового ENTRY на том же close. Никаких дополнительных режимов, часов и фильтров нет.

## PRIMARY и метрики

C1: normalized tick0.001, один тик на сторону, два за круг. Это не реальные биржевые комиссии. `r=abs(entry−initial_stop)`, `GrossR=sign*(exit−entry)/r`, `CostR=0.002/r`, `NetR=GrossR−CostR`. Риск r не пересчитывается при подтягивании стопа.

Основной replay непрерывен от начала доступного ряда до последней завершённой свечи; ежегодных reset нет. Непогашенные позиции на конце сохраняются в open_positions.csv, не ликвидируются искусственно и не попадают в закрытый R. Полные закрытые сделки — trades.csv; все ENTRY/HOLD/EXIT события с trigger/activation/tighten флагами — trail1_trace.csv. signals.csv включает все eligible сигналы, даже когда позиция уже открыта; entered отмечает принятые входы.

Год/месяц/квартал определяются по московскому exit timestamp. Net PF — сумма положительных NetR / абсолютная сумма отрицательных; Gross PF аналогично по GrossR. При отсутствии отрицательных наблюдений PF пустой/неопределённый, не ноль. Win% означает NetR>0; average loss отрицателен. Closed-R DD=min(curve−running_max), начальная точка0; знак DD неположителен. Порядок выходов — timestamp/instrument/trade_id. Годовой DD считается по закрытиям года с локальной начальной точкой0, без сброса торгового состояния. Максимальная серия убытков использует NetR<0, нулевой результат прерывает серию.

Совокупные PF считаются из объединённых сделок, не средним PF. R суммируется без произвольных лотов и весов капитала. CNY до апреля 2022 — NO_DATA, в индивидуальных таблицах не нулевая торговля. Агрегаты используют фактически доступные рынки; 2020–2021 PRIMARY4/ALL6 имеют PARTIAL_SOURCE_COVERAGE. 2026 неполный. Все годовые таблицы включают ALL/LONG/SHORT, остальные направления и периоды раскрываются в robustness/monthly/quarterly.

Устойчивость: худший год/квартал/месяц по NetR среди периодов с закрытиями; число положительных/отрицательных доступных лет; NetR/PF после условного исключения top1/3/5 положительных сделок. Доля крупнейших сделок имеет знаменатель сумма положительных NetR. Эти исключения — диагностика концентрации, не новая стратегия.

## Неизвестная склейка: заранее заданная диагностика

Квартальные proxy anchors — третий четверг марта/июня/сентября/декабря, окна ±3 и ±7 календарных дней (крайние дни полностью). Дополнительно третий четверг каждого месяца ±3 дня для всех рынков; особенно для energy квартальное окно нельзя считать достаточным. Это условные даты, а не подтверждённые expiries или roll transitions. Определения фиксированы до чтения результатов, не подбирались по PF.

Для каждой закрытой сделки отмечаются пересечения окон/anchors, близость entry/exit и крупные гэпы во время позиции. В концентрации учитываются eligible signals, фактические ENTRY (включая открытые на конце позиции), EXIT, stop tests, tighten, trigger/activation и прибыль по exit timestamp. potential_window_metrics.csv детализирует закрытый cohort; открытые позиции раскрыты отдельно и их ENTRY входят в roll_concentration.csv. База — фактические наблюдаемые H1 рядом/вне окон, в том числе signal rate/1000 баров.

Большой гэп — abs(Open−previousClose)/previousClose≥3% ИЛИ abs(Open−previousClose)/previousATR≥2.5. ATR только предыдущего бара; при отсутствии ATR возможен процентный критерий. Предикат не определяет происхождение гэпа. Строго различаются gap на entry bar и gap при уже открытой позиции (entry_time<gap_bar_close≤exit_time).

В roll_sensitivity.csv основной результат ORIGINAL_CONTINUOUS_SERIES сохранён полностью. ATTRIBUTION_OMIT_* — post-hoc разложение уже закрытых сделок, без нового replay, без освобождения позиции/новых сигналов и без правки исходных цен. STOP_LEVEL_FILL_ARITHMETIC_CREDIT_ONLY возвращает adverse gap-stop penalty при неизменной последовательности выходов; это не исполнимый fill через гэп. Эти сценарии нельзя применять в production или интерпретировать как предложенные фильтры. Календарная близость не доказывает causal roll effect, а отсутствие близости не подтверждает качество ряда.

## N4 и v2

N4 — исключительно аутентифицированный Stage6 TRAIL1 ledger: 418 физических строк, 63 Walk Forward исключены, 355 baseline/historical_true_oos доступны для сравнения. CANONICAL не используется. Для каждого года/пары и PRIMARY4 определяется общий source/lifecycle интервал, а не границы сделок. 2020–2022: NO_DATA/NO_COMMON_COVERAGE. В 2023 полная четвёрка доступна только с ноября; не называется полным годом.

Две панели: EXIT_DATE_WINDOW (все выходы общего интервала, включая позиции из предыдущего периода), FULLY_CONTAINED_TRADES (entry и exit внутри общего интервала). Основные годовые quarterly totals не изменяются. Frequency — число закрытий на 365.25 календарных дней наблюдаемого общего интервала, не прогноз. N4 имеет cold start2025; quarterly v3 непрерывен, что раскрывается. Различия источников/ценового масштаба/C1 исключают причинную атрибуцию только типу контракта.

v2 — только опубликованная T3_H1_candidate_v2, stop2.0/ATR average30, без идентичного TRAIL1. 2020–2024 повторяет только этот frozen candidate существующей функцией _execute и сверяется с пятью опубликованными year_report rows. 2025–2026 берёт существующий ledger, cold start2025. Ни grid, ни поиск не запускаются. Published net сохраняется. Legacy normalizer v2 использует уже-cost-adjusted profit_R как gross_R и вычитает C1 ещё раз; отдельно раскрывается нормализация published_net+cost_R к одному C1 и true gross=published_net+2cost_R. Frozen-код и старые артефакты не исправляются.

## Реальный вычислительный аудит и воспроизводимость

Instrumented replay сверяется на всех исторических закрытых сделках с unchanged research authority и production replay. Независимый scalar_audit вычисляет EMA/ATR/ADX/Donchian/H4/signals/lifecycle без shared indicator/state math. Сверяются все реальные сигналы, значения используемых индикаторов, закрытые сделки и каждый post-entry management event. Production DecisionCore дополнительно прогоняется по всем таким событиям. Проверяются initialR, причинность trigger/activation, gap fills, tighten-only, запрет entry-bar управления и повторной позиции.

На исторических префиксах в 2021/2023/2025/2026 (по доступности) индикаторы/сигналы и закрытые scalar сделки совпадают с полным потоком до cut. Синтетические perturbation/adversarial тесты сохранены дополнительно. Это не удостоверяет point-in-time доступность supplier adjustments, только причинность вычислений над предоставленным рядом.

Допуски scalar fields: abs2e-10/rel2e-12; Decimal trade arithmetic abs2e-9/rel2e-10; таблицы PF/sum/DD проверяются отдельной Decimal арифметикой. Старые published v2 показатели сверяются с rel2e-9/abs2e-8 с учётом сериализации. Отдельно проверены московская атрибуция, порядок, суммы направлений/годов/инструментов/корзин.

Текущая точка воспроизведения:

```bash
PYTHONDONTWRITEBYTECODE=1 python audit_only/quarterly_t3_h1_trail1_2020_2026/reproduce_exploratory.py \
  --data-root /workspace/market-pattern-data --scratch-root /workspace/work
PYTHONDONTWRITEBYTECODE=1 python audit_only/quarterly_t3_h1_trail1_2020_2026/build_report.py
```

Python3.12/pandas2.2.3; тесты используют stdlib unittest. Первый скрипт выполняет **два полных исторических прогона** во вновь созданных scratch directories (включая все реальные сверки и сравнения), сравнивает SHA256 каждого генерируемого CSV/JSON, запускает 11 прежних и 4 новых теста и только после успеха копирует результат в текущий isolated audit-каталог. Ожидаемый exit code0. Logs с длительностью тестов и статические Markdown не входят в сравнение двух расчётных запусков; исходники дополнительно хешируются в source_manifest. build_report строит отчёты из согласованных артефактов.

Прежние preflight.py/reproduce.py сохранены как исходная стадия DATA_BLOCKED и не являются текущим full-replay entry point. Старый README/QA/отчёты сохранены в prior_preflight, без перезаписи старых исследований TradingSystemLab.

2020–2024 ранее исследован, 2025–2026 ранее просмотрен. Новый TRUE OOS не заявляется; оптимизации/выбора стратегии на них нет. SECONDARY, реальные расходы и FULL/R15 капитал-модель не рассчитываются без authenticated specs. Production, H1/M15, FINAM, ControlCenter и frozen authority не меняются. Один существующий Draft PR #555, без merge/auto-merge; затем STOP для внешнего аудита.
