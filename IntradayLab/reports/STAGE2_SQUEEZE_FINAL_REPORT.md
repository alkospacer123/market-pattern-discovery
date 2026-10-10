# IntradayLab — Stage 2 Volatility Squeeze Breakout v1

2026-10-10, Europe/Moscow. **STAGE2_SQUEEZE_NO_ECONOMIC_BASELINE_PASS**. Обе фиксированные архитектуры технически воспроизведены и прошли независимую алгоритмическую проверку. Прибыльный и достаточно регулярный Baseline не найден. Исследование данного пакета завершено; внешняя приёмка остаётся за пользователем. Stage 3 и следующая стратегия не запускаются.

## Summary — семь обязательных ответов

**1. Сделки за всю доступную историю 2023:** T10 дал 4 USD и 3 CNY сделки в каждой архитектуре; GLD/IMOEX — 0. M5 и M30 используют те же 7 уникальных входов; повторные архитектуры и стресс не являются дополнительными независимыми сделками. Все 7 закрыты, UNKNOWN=0. Ни история, ни убыточные месяцы не сокращались.

| Архитектура | Инструмент | Входы/закрытые/UNKNOWN | LONG/SHORT | Сделок/наблюдаемый день | Сделок/месяц покрытия | Net PF C1: закрытая диагностика | Полный годовой Net/PF/DD |
| --- | --- | --- | --- | --- | --- | --- | --- |
| SQUEEZE_M30_M5 | USDRUBF | 4/4/0 | 2/2 | 0.0158 | 0.3333 | 0.6667 | null / null / null |
| SQUEEZE_M30_M5 | CNYRUBF | 3/3/0 | 2/1 | 0.0119 | 0.25 | 0 | null / null / null |
| SQUEEZE_M30_M5 | GLDRUBF | 0/0/0 | 0/0 | 0 | 0 | — | null / null / null |
| SQUEEZE_M30_M5 | IMOEXF | 0/0/0 | 0/0 | 0 | 0 | — | null / null / null |
| SQUEEZE_M5 | USDRUBF | 4/4/0 | 2/2 | 0.0158 | 0.3333 | 0.6667 | null / null / null |
| SQUEEZE_M5 | CNYRUBF | 3/3/0 | 2/1 | 0.0119 | 0.25 | 0 | null / null / null |
| SQUEEZE_M5 | GLDRUBF | 0/0/0 | 0/0 | 0 | 0 | — | null / null / null |
| SQUEEZE_M5 | IMOEXF | 0/0/0 | 0/0 | 0 | 0 | — | null / null / null |

**2. Net PF после C1:** USD 0,667 и CNY 0 для обеих архитектур; GLD/IMOEX PF не определён без сделок. Это закрытые диагностические подвыборки всей доступной истории, **не полный годовой PF**. Полные годовые Net/PF/DD отсутствуют у всех 8 основных запусков и 8 стрессов из-за физического неполного покрытия и/или начала истории в середине года. Нет подмены full-period столбцов закрытыми результатами.

**3. Реальные 3R:** одна и та же LONG USD-сделка 20.02.2023 достигла Take и NetR=3 в M5 и M30. Остальные инструменты — 0; T15 — 0. Планируемый net Reward/initial-risk у всех реальных входов равен 3. Фактическое average-net-win/average-net-loss USD=2,0 (0,12/0,06), CNY не определён без победителей. Среднее фактическое NetR по всем известным сделкам USD=−0,02083, CNY=−1,40741. Это отдельные определения; одно не подставляется вместо другого.

**4. Месяцы:** по закрытой диагностике USD:1 положительный,3 отрицательных,8 без сделок (8,33% положительных из 12). Лучший активный — февраль +0,12; худший — июль −0,10; серия отрицательных месяцев июль–август:2. CNY:0 положительных,2 отрицательных,10 без сделок; худший активный октябрь −0,017, лучший активный декабрь −0,006 (ноль в прочих наблюдаемых закрытых подвыборках); максимальная серия отрицательных календарных месяцев 1. GLD:6 месяцев покрытия без сделок, первые 6 месяцев NO_COVERAGE. IMOEX:2 месяца покрытия без сделок, первые 10 NO_COVERAGE. **Знаки частичных месяцев не сертифицируют календарный результат**: ни один прибыльный месяц USD не имеет полного покрытия; у CNY декабрь — подтверждённый полностью покрытый отрицательный месяц. Полные 12-месячные таблицы ниже.

**5. T15/C2:** при T15 остаются 2 USD-сделки (1L/1S), Net +0,06/PF 2,0, и 1 CNY LONG, Net −0,009/PF 0. Исчезает T10 победитель 3R; появляется другой USD LONG с failed-breakout выходом +1,714R. Это нестабильный состав, а не доказанное улучшение. C2 на исходных T10 fills: USD Net −0,14/PF 0,417; CNY −0,029/PF 0. T15+C2: USD +0,02/PF 1,25; CNY −0,011/PF 0. GLD/IMOEX по-прежнему без входов.

**6. M30:** не улучшает фактическую экономику этой выборки. В T10/T15 сохранены все входы M5, освобождённых входов 0; один дополнительный USD заказ отвергнут фильтром, но в M5 он тоже не исполнился. Логика контекста проверена; отсутствие эффекта не является разрешением выбирать другой фильтр.

**7. Решение:** отклонить испытанные `SQUEEZE_M5` и `SQUEEZE_M30_M5` как кандидаты прибыльного регулярного Baseline. Частота около 0,028 уникальных сделок на ожидаемый торговый день всего по 4 инструментам, отрицательная основная экономика, отсутствие выигрышей CNY, отсутствие сделок GLD/IMOEX и один 100%-ный источник положительного USD P&L не удовлетворяют исследовательским целям. PF 2 на двух T15-сделках не принимается. Это отказ в Baseline PASS для испытанных правил, не статистическое доказательство отрицательной полной годовой прибыли или невозможности любой Squeeze-стратегии.

## Входные данные, сохранность и причинность

GitHub main перед работой=`01e092112efd408f331c0a2b95f04e75187573bd` (Merge #454), root tree=`b9c54d14f39536fb5908534c0ae64a8c38bfdca8`. Новая ветка непосредственно от origin/main: `research/intraday-stage2-squeeze-20261010`. Сохранены 25 защищённых root IDs и SHA-256 всех 205 принятых Lab-файлов: [initial_state.json](../results/stage2_squeeze_v1/initial_state.json). VWAP/Momentum остаются **TRADING LOGIC PASS / NO ECONOMIC BASELINE PASS / REJECT CANDIDATE**, без изменения старых конфигураций/движков/аудитов/результатов.

Источник read-only `alkospacer123/market-pattern-data@f8486b446cf3d5f9f3cba6dfec32bdef8fd184c8`, только 4 M5 физических префикса. Unbuffered read читает точный заранее аттестованный byte budget, не следующую строку/EOF. Год проверяется до разбора цен. Всего 104795 строк 2023; **0 байтов 2024 WF и 2025+ TRUE OOS**. Старшие файлы вообще не нужны: M30 строится из точных существующих детей. Окна 10:00–14:00 /14:05–18:50;13–20 марта PM14:15. Сентябрьская остановка не передана стратегии как будущий запрет: физические пропуски наблюдаются и сбрасывают контекст. 31.08 USD/CNY отсутствует. Сессии/дни/пропуски не пересекаются.

| Инструмент | Первая/последняя исходная строка | M5 строк 2023 | Байтов | Допустимых наблюдений | Пропусков после начала | Дни наблюдаемые/ожидаемые |
| --- | --- | --- | --- | --- | --- | --- |
| USDRUBF | 2023-01-03 09:00:00 / 2023-12-29 23:45:00 | 42576 | 2342431 | 26471 | 187 | 253/254 |
| CNYRUBF | 2023-01-03 09:00:00 / 2023-12-29 23:45:00 | 39362 | 2212189 | 25388 | 1270 | 253/254 |
| GLDRUBF | 2023-07-11 10:00:00 / 2023-12-29 23:45:00 | 18428 | 1044351 | 12088 | 932 | 124/124 |
| IMOEXF | 2023-11-14 10:00:00 / 2023-12-29 23:45:00 | 4429 | 234733 | 3004 | 566 | 34/34 |

C1 — один действующий tick на каждую исполненную сторону. USD 0,01, GLD 0,1, IMOEX 0,5; CNY 0,01 до 27.09.2023 19:00 MSK, затем 0,001; стороны датируются отдельно. Исторический CNY переход не пересекает допущенное daytime окно. Нормализованные единицы котировки, один абстрактный модельный exposure; нет RUB портфельной суммы, GO/капитала/процентов доходности или подтверждения реальных комиссий/fills.

## Замороженная самостоятельная архитектура

[Preregistration](STAGE2_SQUEEZE_PREREGISTRATION.md) и [config](../config/stage2_squeeze_v1.json), SHA-256 `a1e3c1a3bc7f0de5f90fe9243ce2a14e64a7bc1c380400e5516de3f284098255`, закреплены коммитом `bc47fc59223fd90431f751060093a53b02c8740a` до P&L. Основная реализация/первый аудитор коммит `94e38bdb60c5dbe19b0cbf8c7abe37f7e9315f5b`; [pre-return fingerprints](../results/stage2_squeeze_v1/pre_returns_freeze.json) — `55cfa65`. До доходностей 166 тестов PASS. Никаких параметров/кода/результатов BBW или TradingSystemLab не использовано.

BB20=SMA20±2 populationσ, denominator20. KC20=EMA20±1,5 WilderATR20. EMA seed=SMA первых 20 Close, alpha2/21; ATR seed=mean первых 20 TR (первый H−L), затем(19ATR+TR)/20. Decimal34. Индикатор использует текущую уже завершённую доставленную свечу; после gap/window reset снова 20 наблюдений. Строгое BB внутри KC минимум 3 свечи. Диапазон включает все true свечи, начиная с первых двух. Первый off фиксирует диапазон; первый off-Close за его границей подтверждает направление и расходует цикл, даже если заказ отсеян/NONFILL. Inside/equality ждёт; новый true/gap/window заменяет неиспользованный диапазон. Сигнальная свеча никогда не входит в пробиваемый диапазон. Это не rolling12-bar Momentum и не переименование принятого движка.

Вход строго будущий точный M5 Open: T+15 при T10, T+20 при T15. Направление должно сохраниться, extension≤0,5 signalATR, cap округляется внутрь. Stop=edge−direction×0,25 signalATR; LONG вверх/SHORT вниз по принятому Stage 1 округлению, без подведения после Open. Минимум риска 4ticks. Take из actual Open=Open+direction×(3initialRisk+2entryTick), outward rounding. Gross target≤3signalATR проверяется при signal Close и actual Open. Это заранее заданный guard разумности внутридневной цели, а не будущая сопротивляющая цена/venue band. Все 7 фактических T10 целей требуют в среднем 1,614ATR у USD и 1,231ATR у CNY; бессмысленные стопы не исправлялись ради 3R.

Resident conditional Stop от входа — модельное допущение, а не доказанная брокерская атомарность. Stop touch, худший Open при adverse gap, Stop-first; Take только после entry-bar и проникновения 1tick, без благоприятного gap credit. Close внутри исходного inclusive диапазона после доставки вызывает будущий Open exit. MAX_HOLD120 мин: request entryStart+115; acknowledgement позже. Session requestB−25/T10 илиB−30/T15, flat ackB−10; новый entry full candle должен закончиться≤B−30. Самый ранний уже поставленный exit сохраняется, session timer приоритетен. Нет BE/trailing.

Missing target даёт NO_BAR_NO_MODEL_FILL без позиции и расходов; entry не повторяется. Missing exposed path —UNKNOWN с null payoff и условной future reduce-all; следующая свеча не восстанавливает прошлую прибыль. В данном пакете реальные UNKNOWN, missing-entry orders и B−10 breaches=0; соответствующие неблагоприятные ветви испытаны синтетически, без вымышленных исторических сделок.

M30 использует `DERIVED_EXACT_COMPLETED_M5_V1`: последняя ожидаемая пара соседних M30 в одном окне, шесть существующих положительных children каждый, доступность последнего child T+10/T+15 (M30 T+35/T+40). Missing/undelivered child запрещает пару без stale fallback. Sustained+1=оба C>O и второй C>первого;−1 симметрично; иначе 0. Отсеять только устойчивое adverse направление, но отсутствие контекста запрещает вход. MTF меняет исключительно допуск входа; цена, Stop/Take и exits всегда M5. Нативная доставка FINAM не сертифицируется.

## Воронка сигналов и частота T10

| Инструмент | True Squeeze M5 свечей | Сырых эпизодов | Подтверждённых ≥3 | Без breakout | Сигналов | M5/M30 заказов | Отсеянных M5 | NONFILL M5 | Входов M5/M30 |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| USDRUBF | 2490 | 393 | 262 | 106 | 156 | 19/18 | 137 | 15 | 4/4 |
| CNYRUBF | 1936 | 369 | 219 | 116 | 103 | 9/9 | 94 | 6 | 3/3 |
| GLDRUBF | 244 | 46 | 27 | 12 | 15 | 3/3 | 12 | 3 | 0/0 |
| IMOEXF | 62 | 18 | 9 | 4 | 5 | 0/0 | 5 | 0 | 0/0 |

Сырые эпизоды — не отдельные сделки; true свечи посчитаны отдельно. Из 517 подтверждённых сжатий 279 дают направленный сигнал,31 M5 заказ и 7 входов.238 подтверждённых эпизодов не имеют направленного выхода. Полный [squeeze_cycles.csv.gz](../results/stage2_squeeze_v1/squeeze_cycles.csv.gz) сохраняет и эти несобытия.

| Инструмент | Сделок/ожидаемый день | Сделок/неделю календаря покрытия | Месяц покрытия | Дней без сделок на наблюдаемой истории | Отдельных отсутствующих дней |
| --- | --- | --- | --- | --- | --- |
| USDRUBF | 0.0157 | 0.0769 | 0.3333 | 249 | 1 |
| CNYRUBF | 0.0118 | 0.0577 | 0.25 | 250 | 1 |
| GLDRUBF | 0 | 0 | 0 | 124 | 0 |
| IMOEXF | 0 | 0 | 0 | 34 | 0 |

Для M30 частота входов идентична. Детальные дни/недели/месяцы и отсутствующие данные —[frequency_report.csv](../results/stage2_squeeze_v1/frequency_report.csv).2–3 сделки/день —ориентир, не квота; качество ради частоты не снижалось. До позднесентябрьского уменьшения tick CNY ни одной сделки: min4ticks и 0,25ATR protection часто несовместимы с малым наблюдаемым диапазоном.

Причины всех отказов M5 (включая exact Open NONFILL, отдельный status/clock сохранён в signals):

| Инструмент | Причины и количества |
| --- | --- |
| USDRUBF | {"BREAKOUT_NOT_PERSISTENT": 6, "EXTENSION_OVER_0_5_ATR": 64, "KNOWN_BOUNDARY_ENTRY_CUTOFF": 52, "RISK_BELOW_FOUR_TICKS": 30} |
| CNYRUBF | {"BREAKOUT_NOT_PERSISTENT": 3, "EXTENSION_OVER_0_5_ATR": 64, "KNOWN_BOUNDARY_ENTRY_CUTOFF": 23, "RISK_BELOW_FOUR_TICKS": 10} |
| GLDRUBF | {"BREAKOUT_NOT_PERSISTENT": 1, "EXTENSION_OVER_0_5_ATR": 4, "KNOWN_BOUNDARY_ENTRY_CUTOFF": 10} |
| IMOEXF | {"EXTENSION_OVER_0_5_ATR": 1, "KNOWN_BOUNDARY_ENTRY_CUTOFF": 2, "RISK_BELOW_FOUR_TICKS": 2} |

Экономический ceiling3ATR не был причиной реального отказа в этом пакете; основной барьер —задержанный extension, граница сессии и риск относительно tick. Период 20 со сбросом требует 100 мин непрерывного прогрева и оставляет короткую часть разрешённого окна; разреженные GLD/IMOEX чаще не прогреваются. Это архитектурная диагностика, а не основание тихо сокращать период, переносить контекст или изменять параметры.

## Gross, C1, Net и направления

| Инструмент | Gross | C1 | Net | PF | Expectancy | Win rate | Avg net win/loss | Факт net win/loss RR | NetR sum/mean | Подтверждённый closed DD |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| USDRUBF | 0.02 | 0.08 | -0.06 | 0.6667 | -0.015 | 0.25 | 0.12/0.06 | 2 | -0.0833/-0.0208 | 0.18 |
| CNYRUBF | -0.017 | 0.006 | -0.023 | 0 | -0.0077 | 0 | —/0.0077 | — | -4.2222/-1.4074 | 0.023 |
| GLDRUBF | 0 | 0 | 0 | — | — | — | —/— | — | 0/— | — |
| IMOEXF | 0 | 0 | 0 | — | — | — | —/— | — | 0/— | — |

Таблица одинаковых исполнений M5/M30; все суммы —CLOSED-ONLY, не full annual. USD после единственного победителя входит в просадку 0,18; до последнего известного exit она не восстановлена (170,18 календарных суток от high-water). CNY closed curve также не восстановлена, исключительно отрицательная. DD учитывает подтверждённые закрытые результаты, а не вымышленный equity/полный intrabar путь.

| Инструмент | Направление | Входы | Gross | C1 | Net | PF | Mean NetR |
| --- | --- | --- | --- | --- | --- | --- | --- |
| USDRUBF | LONG | 2 | 0.14 | 0.04 | 0.1 | 6 | 1.3333 |
| USDRUBF | SHORT | 2 | -0.12 | 0.04 | -0.16 | 0 | -1.375 |
| CNYRUBF | LONG | 2 | -0.013 | 0.004 | -0.017 | 0 | -1.3611 |
| CNYRUBF | SHORT | 1 | -0.004 | 0.002 | -0.006 | 0 | -1.5 |
| GLDRUBF | LONG | 0 | 0 | 0 | 0 | — | — |
| GLDRUBF | SHORT | 0 | 0 | 0 | 0 | — | — |
| IMOEXF | LONG | 0 | 0 | 0 | 0 | — | — |
| IMOEXF | SHORT | 0 | 0 | 0 | 0 | — | — |

USD LONG PF 6 на двух сделках не имеет самостоятельной доказательной силы. Единственный победитель даёт 100% positive Net; без него USD Net −0,18. Top1/Top3/Top5 concentration=100%. CNY положительного вклада не имеет. Суммы инструментов в RUB портфель не объединяются.

## Качество выхода

| Инструмент | Stop | Take | Failed breakout | Time120 | Session flat | ≥1R / ≥2R / ≥3R | NetR≥3 | Ранее≥1R, exit до Take |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| USDRUBF | 2 | 1 | 0 | 0 | 1 | 2/1/1 | 1 | 1 |
| CNYRUBF | 3 | 0 | 0 | 0 | 0 | 0/0/0 | 0 | 0 |
| GLDRUBF | 0 | 0 | 0 | 0 | 0 | 0/0/0 | 0 | 0 |
| IMOEXF | 0 | 0 | 0 | 0 | 0 | 0/0/0 | 0 | 0 |

R excursion —консервативный known-path ruler от первоначального риска. Entry-bar favorable экстремумы и High/Low Stop/market-exit свечи не доказывают порядок; известная цена actual exit учитывается. UNKNOWN было бы lower bound, не полным MFE. Early potential winner означает уже наблюдавшийся≥1R, закрытый доTake, а не утверждение о будущем победителе: здесь USD session-flat 15 мая. В основной выборке 4 из 7 входов получают Stop наentry candle. T15 содержит 1 failed-breakout USD exit с Net +1,714R,1 USD Stop и 1 CNY Stop; Take=0. Новое сопровождение после этого не добавлялось.

## Все календарные месяцы 2023

Ниже каждая таблица относится **к обеим архитектурам T10**, поскольку все их trade/month rows по исполнению и P&L совпали. Отдельные записи каждой архитектуры иT15 находятся в [monthly_results.csv](../results/stage2_squeeze_v1/monthly_results.csv), всего 192 month rows. L/S —число входов; Net L/S —закрытая экономика сторон. UNKNOWN=0 во всех месяцах. PF без убытков или без сделок оставлен null (—), не infinity/PASS. `P`=PARTIAL_DATA; `L`=PARTIAL_LAUNCH; `C`=COVERED; `N`=NO_COVERAGE. В частичных месяцах Gross/C1/Net/PF/R —только закрытые диагностические значения; full month Net/PF/DD=null. NO_COVERAGE остаётся—, не нулевой доходностью.

### USDRUBF — SQUEEZE_M5 и SQUEEZE_M30_M5

| Месяц | Сделки L/S | Gross | C1 | Net | PF | NetR | Net L/S | Покрытие / пропуски | UNKNOWN | Статус closed subset |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 2023-01 | 0/0 | 0 | 0 | 0 | — | 0 | 0/0 | P / 7 | 0 | NO_TRADES |
| 2023-02 | 1/0 | 0.14 | 0.02 | 0.12 | — | 3 | 0.12/0 | P / 5 | 0 | POSITIVE |
| 2023-03 | 0/0 | 0 | 0 | 0 | — | 0 | 0/0 | P / 4 | 0 | NO_TRADES |
| 2023-04 | 0/0 | 0 | 0 | 0 | — | 0 | 0/0 | P / 6 | 0 | NO_TRADES |
| 2023-05 | 1/0 | 0 | 0.02 | -0.02 | 0 | -0.3333 | -0.02/0 | P / 7 | 0 | NEGATIVE |
| 2023-06 | 0/0 | 0 | 0 | 0 | — | 0 | 0/0 | P / 4 | 0 | NO_TRADES |
| 2023-07 | 0/1 | -0.08 | 0.02 | -0.1 | 0 | -1.25 | 0/-0.1 | P / 1 | 0 | NEGATIVE |
| 2023-08 | 0/1 | -0.04 | 0.02 | -0.06 | 0 | -1.5 | 0/-0.06 | P / 109 | 0 | NEGATIVE |
| 2023-09 | 0/0 | 0 | 0 | 0 | — | 0 | 0/0 | P / 43 | 0 | NO_TRADES |
| 2023-10 | 0/0 | 0 | 0 | 0 | — | 0 | 0/0 | C / 0 | 0 | NO_TRADES |
| 2023-11 | 0/0 | 0 | 0 | 0 | — | 0 | 0/0 | P / 1 | 0 | NO_TRADES |
| 2023-12 | 0/0 | 0 | 0 | 0 | — | 0 | 0/0 | C / 0 | 0 | NO_TRADES |

### CNYRUBF — SQUEEZE_M5 и SQUEEZE_M30_M5

| Месяц | Сделки L/S | Gross | C1 | Net | PF | NetR | Net L/S | Покрытие / пропуски | UNKNOWN | Статус closed subset |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 2023-01 | 0/0 | 0 | 0 | 0 | — | 0 | 0/0 | P / 113 | 0 | NO_TRADES |
| 2023-02 | 0/0 | 0 | 0 | 0 | — | 0 | 0/0 | P / 94 | 0 | NO_TRADES |
| 2023-03 | 0/0 | 0 | 0 | 0 | — | 0 | 0/0 | P / 204 | 0 | NO_TRADES |
| 2023-04 | 0/0 | 0 | 0 | 0 | — | 0 | 0/0 | P / 185 | 0 | NO_TRADES |
| 2023-05 | 0/0 | 0 | 0 | 0 | — | 0 | 0/0 | P / 152 | 0 | NO_TRADES |
| 2023-06 | 0/0 | 0 | 0 | 0 | — | 0 | 0/0 | P / 152 | 0 | NO_TRADES |
| 2023-07 | 0/0 | 0 | 0 | 0 | — | 0 | 0/0 | P / 119 | 0 | NO_TRADES |
| 2023-08 | 0/0 | 0 | 0 | 0 | — | 0 | 0/0 | P / 150 | 0 | NO_TRADES |
| 2023-09 | 0/0 | 0 | 0 | 0 | — | 0 | 0/0 | P / 90 | 0 | NO_TRADES |
| 2023-10 | 1/1 | -0.013 | 0.004 | -0.017 | 0 | -2.7222 | -0.011/-0.006 | P / 2 | 0 | NEGATIVE |
| 2023-11 | 0/0 | 0 | 0 | 0 | — | 0 | 0/0 | P / 9 | 0 | NO_TRADES |
| 2023-12 | 1/0 | -0.004 | 0.002 | -0.006 | 0 | -1.5 | -0.006/0 | C / 0 | 0 | NEGATIVE |

### GLDRUBF — SQUEEZE_M5 и SQUEEZE_M30_M5

| Месяц | Сделки L/S | Gross | C1 | Net | PF | NetR | Net L/S | Покрытие / пропуски | UNKNOWN | Статус closed subset |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 2023-01 | — | — | — | — | — | — | —/— | N / 0 | 0 | NO_COVERAGE |
| 2023-02 | — | — | — | — | — | — | —/— | N / 0 | 0 | NO_COVERAGE |
| 2023-03 | — | — | — | — | — | — | —/— | N / 0 | 0 | NO_COVERAGE |
| 2023-04 | — | — | — | — | — | — | —/— | N / 0 | 0 | NO_COVERAGE |
| 2023-05 | — | — | — | — | — | — | —/— | N / 0 | 0 | NO_COVERAGE |
| 2023-06 | — | — | — | — | — | — | —/— | N / 0 | 0 | NO_COVERAGE |
| 2023-07 | 0/0 | 0 | 0 | 0 | — | 0 | 0/0 | L / 183 | 0 | NO_TRADES |
| 2023-08 | 0/0 | 0 | 0 | 0 | — | 0 | 0/0 | P / 212 | 0 | NO_TRADES |
| 2023-09 | 0/0 | 0 | 0 | 0 | — | 0 | 0/0 | P / 238 | 0 | NO_TRADES |
| 2023-10 | 0/0 | 0 | 0 | 0 | — | 0 | 0/0 | P / 90 | 0 | NO_TRADES |
| 2023-11 | 0/0 | 0 | 0 | 0 | — | 0 | 0/0 | P / 143 | 0 | NO_TRADES |
| 2023-12 | 0/0 | 0 | 0 | 0 | — | 0 | 0/0 | P / 66 | 0 | NO_TRADES |

### IMOEXF — SQUEEZE_M5 и SQUEEZE_M30_M5

| Месяц | Сделки L/S | Gross | C1 | Net | PF | NetR | Net L/S | Покрытие / пропуски | UNKNOWN | Статус closed subset |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 2023-01 | — | — | — | — | — | — | —/— | N / 0 | 0 | NO_COVERAGE |
| 2023-02 | — | — | — | — | — | — | —/— | N / 0 | 0 | NO_COVERAGE |
| 2023-03 | — | — | — | — | — | — | —/— | N / 0 | 0 | NO_COVERAGE |
| 2023-04 | — | — | — | — | — | — | —/— | N / 0 | 0 | NO_COVERAGE |
| 2023-05 | — | — | — | — | — | — | —/— | N / 0 | 0 | NO_COVERAGE |
| 2023-06 | — | — | — | — | — | — | —/— | N / 0 | 0 | NO_COVERAGE |
| 2023-07 | — | — | — | — | — | — | —/— | N / 0 | 0 | NO_COVERAGE |
| 2023-08 | — | — | — | — | — | — | —/— | N / 0 | 0 | NO_COVERAGE |
| 2023-09 | — | — | — | — | — | — | —/— | N / 0 | 0 | NO_COVERAGE |
| 2023-10 | — | — | — | — | — | — | —/— | N / 0 | 0 | NO_COVERAGE |
| 2023-11 | 0/0 | 0 | 0 | 0 | — | 0 | 0/0 | L / 402 | 0 | NO_TRADES |
| 2023-12 | 0/0 | 0 | 0 | 0 | — | 0 | 0/0 | P / 164 | 0 | NO_TRADES |

## T15 и C2 sensitivity / M5–M30

C2 —только двойной C1 на тех же fills, входах и уровнях; Take не пересчитывается и новые фильтры не вводятся. Две архитектуры совпадают по исполнениям в каждом stress scenario, поэтому таблица применяется к M5 иM30. Для каждого сценария полный годовой Net/PF/DD=null.

| Инструмент | T10 entries | T10 C1 Net/PF | T10 C2 Net/PF | T15 entries | T15 C1 Net/PF | T15 C2 Net/PF |
| --- | --- | --- | --- | --- | --- | --- |
| USDRUBF | 4 | -0.06 / 0.6667 | -0.14 / 0.4167 | 2 | 0.06 / 2 | 0.02 / 1.25 |
| CNYRUBF | 3 | -0.023 / 0 | -0.029 / 0 | 1 | -0.009 / 0 | -0.011 / 0 |
| GLDRUBF | 0 | 0 / — | 0 / — | 0 | 0 / — | 0 / — |
| IMOEXF | 0 | 0 / — | 0 / — | 0 | 0 / — | 0 / — |

T15 сохраняет 2 из 7 T10 входов, исключает 5 и освобождает 1 новый; итог 3. По M5–M30 в каждом сценарии retained=все входы, removed=0, freed=0. [Сравнение](../results/stage2_squeeze_v1/m5_m30_comparison.csv) использует IDs фактических входов, а не двусмысленное отношение числа сделок. USD T15 единственный положительный exit снова даёт 100% positive Net; его PF 2 не обладает sample size/month diversity, приC2 уже 1,25.

## Независимая проверка, трассировки и изменения

Независимый [audit_squeeze.py](../tools/audit_squeeze.py) не импортирует Replay, индикаторы, календарь или метрики основного алгоритма. Сначала самостоятельно читает raw prefixes, вычисляет индикаторы по отдельным сегментам (variance=E[C²]−E[C]²; EMA/ATR через взвешенную историю, Decimal50), восстанавливает все сжатия и несигнальные исходы, затем отдельной clock state machine получает signals/orders/fills/Stop/Take/failed/time/session/unknown. Только затем читает опубликованные CSV как цель сравнения. **505,747 полей PASS**,16 запусков, ноль расхождений. Числовой tolerance1e−24×max(1,abs(expected)) для разных precision; timestamps/statuses/counts/цены наtick —сопоставлены напрямую. Проверены все 4 source hashes и нулевое чтение protected years.

Проверены все индикаторные строки, raw episodes, LONG/SHORT signals, ranges, availability/strict future slots, caps/NONFILL, initial risk/Take/C1, последовательность exits, каждый ledger/event field, all monthly/direction economics, PF/expectancy/R/DD/concentration, частота days/weeks/months иC2. M30 пересчитан из source kids, включая отсутствие context и adverse rejects. Нет UNKNOWN в реальных Squeeze-выборках; original82 VWAP/Momentum unknown не переписаны.

[Manual traces](../results/stage2_squeeze_v1/manual_traces.md):11 реальных signal/trade traces (все 7 основных уникальных входов, T15 failed breakout, задержанный NONFILL исходного победителя, M30 admit/reject), реальное подтверждённое сжатие без сигнала, реальный отсутствующий M30 ребёнок и 31 августа. Показаны source row/OHLCV,20Close/TR, индикаторы, все range children, decision/entry/exit clocks, цены и арифметика. Отдельно явно помечены synthetic Stop-first/adverse gap, unknown, missing entry,120 мин иB−10; отсутствие таких исторических случаев не заменяется выдуманными сделками.

**169 tests PASS** (166 до первого P&L; последующие 3 добавили проверку классификации покрытия, обнаружения испорченного payoff и возраста all-loss DD). Есть future mutation, каждый из 6 missing M30 children, late child delivery, Stop/TP penetration, LONG/SHORT, gap UNKNOWN, session/T15/max120/failed causality. [Тесты](../tests/test_squeeze.py).

Зафиксированы только reporting corrections: январь USD/CNY PARTIAL_LAUNCH→PARTIAL_DATA, неверная короткая commit-reference в pre-return metadata и clock начального zero-equity peak для all-loss DD age. [История и старые hashes](../results/stage2_squeeze_v1/reporting_correction_history.json). Config и торговый squeeze_replay.py после первого P&L не изменены; signals/events/ledger/cycles/features/M5–M30 сравнение до/после побайтово идентичны. Не было изменения сигнала/Stop/Take/фильтра ради результата.

Два окончательных основных исполнения и два независимых исполнения побайтово совпадают; deterministic gzipmtime=0. [Reproducibility](../results/stage2_squeeze_v1/reproducibility.json), [independent_audit.json](../results/stage2_squeeze_v1/independent_audit.json), [SHA256SUMS](../results/stage2_squeeze_v1/SHA256SUMS). Промежуточный полный independent reconstructed журнал остаётся work/; опубликованы компактный JSON и реальные traces.

## Воспроизведение и Draft gate

В чистом checkout ветки, Python3.12 stdlib, источник read-only наf8486b4; каждый output должен быть новым:

```bash
PYTHONDONTWRITEBYTECODE=1 python -m unittest discover -s IntradayLab/tests -v
PYTHONDONTWRITEBYTECODE=1 python IntradayLab/tools/run_squeeze.py --data-root /workspace/market-pattern-data --output /workspace/work/squeeze-repeat-a
PYTHONDONTWRITEBYTECODE=1 python IntradayLab/tools/run_squeeze.py --data-root /workspace/market-pattern-data --output /workspace/work/squeeze-repeat-b
diff -r /workspace/work/squeeze-repeat-a /workspace/work/squeeze-repeat-b
PYTHONDONTWRITEBYTECODE=1 python IntradayLab/tools/audit_squeeze.py --data-root /workspace/market-pattern-data --results /workspace/work/squeeze-repeat-a --output /workspace/work/squeeze-audit-repeat
PYTHONDONTWRITEBYTECODE=1 python IntradayLab/tools/squeeze_traces.py --data-root /workspace/market-pattern-data --results /workspace/work/squeeze-repeat-a --audit-folder /workspace/work/squeeze-audit-repeat --output /workspace/work/squeeze-traces-repeat.md
cmp /workspace/work/squeeze-traces-repeat.md IntradayLab/results/stage2_squeeze_v1/manual_traces.md
git diff --check
```

Актуальные ROADMAP/PROJECT_CONTEXT отражают завершённый аудит и Merge #454, запуск/окончание этого кандидата; исторические результаты не переписаны. Полный remote diff, base/main/head, защищённые roots и 205 старых Lab hashes проверяются в publication verification. Создаётся только Draft PR; merge запрещён. После публикации работа останавливается до независимой пользовательской приёмки. Никаких Stage 3/Robustness/WF/OOS/LIVE или иных стратегий.
