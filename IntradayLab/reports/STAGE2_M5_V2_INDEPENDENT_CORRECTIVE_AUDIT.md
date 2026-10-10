# Stage 2 M5 v2 — независимый corrective audit

Аудит 2026-10-09. **Из 82 неизвестных исходов доказательно разрешено 0; осталось 82.**
Все они начинаются с физически отсутствующего ценового пути уже открытой модельной
позиции. Независимый разбор не выявил ошибки загрузчика, календаря, времени или
исполнения, исправление которой позволяло бы восстановить эти исходы. `Net=null`
сохранён для каждого случая. Не создавались годовые результаты или фиктивные цены.

Исправлены **4 класса дефектов производной отчётности/диагностики**: неоднозначный
общий PF, область полноты метрик при PARTIAL_COVERAGE, причины null/статусы и
использование Close свечи выхода в диагностике возврата Momentum «до выхода».
Стратегии, execution adapter, настройки, исходные CSV и замороженные v1/v2 не изменены.

## Фактическая исходная точка

До работы GitHub API и git fetch независимо подтвердили:

| Объект | HEAD SHA | Base / состояние |
| --- | --- | --- |
| main | `f5dec0a73bf1273f9490502fbc0b9588f9315260` | фактический main |
| PR #443 | `0da11cf86169d5cedf3386549ebe244ca5204fd0` | main, OPEN, не merged |
| PR #444 | `f33e236e1a4f69cd614bb77bd988ba2b6d3f153e` | main, OPEN, не merged |
| PR #445 | `9b404949767356a8b58ca25758d99dfce014f482` | ветка #443, Draft, не merged |
| PR #447 | `90369e12332e738da222dfe510120747c6ce9e80` | ветка #443, Draft, не merged |

Полная финальная инвентаризация открытых PR дополнительно обнаружила и проверила:

| Объект | HEAD SHA | Base / состояние |
| --- | --- | --- |
| PR #446 | `938d7d81f5d7105c470c27c78eec57156948d50c` | main, Draft, не merged |
| PR #448 | `2505f4b2f04d6b66c92bed422bbc29b57a942851` | ветка #447, Draft, не merged |

Прочитаны GitHub metadata и полный documentation diff обоих PR. #446 приводит
M5/M15 aggregate evidence для восьми исходных entry targets, но сам исключает
broker-fill/flat proof и указывает, что его прежняя large-file inspection
получила multi-year payload. Этот способ доступа не использован в настоящем
аудите: здесь исходные M15 не читались и защищённые 2024+ CSV bytes не получены.
Согласие двух экспортированных TF не восстанавливает 82 иных ценовых пути.
#448 документирует bounded strategy architecture research в Stage 2 и numerical
optimization только после acceptance, с отдельными gates MTF. Это совместимо
с будущими отдельными гипотезами ниже; новые архитектуры сейчас не запускались,
изменения roadmap из соседней ветки не cherry-picked и не merged.

Corrective branch `corrective/intraday-stage2-m5-v2-independent-audit` создана
непосредственно от HEAD #447. Base нового Draft PR —
`corrective/intraday-stage2-m5-conditional-v2`. SHA нового коммита и URL PR
фиксируются в финальном handoff GitHub; commit не включает самоссылочный SHA.
Ни один существующий PR не менялся и не объединялся.

Прочитаны `AGENTS.md` и актуальный `IntradayLab/ROADMAP.md` с HEAD #447. Работа
остаётся внутри разрешённого Stage 2, двух M5 стратегий и восьми независимых
запусков 2023 года. Исторические положения roadmap о v1 не заменяются результатом
v2. Stage 3, MTF, Walk Forward, TRUE OOS и LIVE не начинались.

## Независимые исходные данные

Read-only source HEAD и фактический GitHub source main:
`f8486b446cf3d5f9f3cba6dfec32bdef8fd184c8`.
Для каждого файла проверены индексный blob SHA, чистота source checkout и
неизменность метаданных файла до/после чтения. Полные CSV не хешировались и не
читались. Независимый reader использует **unbuffered `read(1)`**, ровно header плюс
объявленный 2023 row budget, без следующей строки или EOF-пробы. Полученные
timestamp/OHLCV независимо сопоставлены со всеми строками штатного загрузчика:
**0 удалённых/изменённых строк, 0 расхождений**. `verification.json` v2 не является
источником доказательства: проверяющий алгоритм был заново выполнен с перехваченными
записями в память, а исходные CSV прочитаны отдельным reader.

| Инструмент | Строки 2023 | Blob SHA | SHA-256 физического prefix |
| --- | ---: | --- | --- |
| USDRUBF | 42 576 | `2b621e1c0aa9a84838d95d4c139257889b6f825e` | `047de8fbc74fbe98028cd236b67bf11823b4e6b9f79a6488113a1d0f43947e1d` |
| CNYRUBF | 39 362 | `01d667868daaa5610cc8794bf90fe0f276e33686` | `42e30caf28909da46226cd2e163739f1c97d00a3a80780d0f2550a05884c9bc9` |
| GLDRUBF | 18 428 | `4b1f36bce33b0eeb684edb04f9faf51a636f240d` | `14d0094ed8a842aabbd66da567a4cc46e2adef11f6a66d40c5d9e942b1e7fc1b` |
| IMOEXF | 4 429 | `41b83b109b177d4522e53486950104845d357d99` | `7bd7d9aafee7e0bf467e12e4ec36ab5c4537ee73a37788e5a24ed84a0861ae6c` |

Один проход: **104 795 строк / 5 833 704 байта**. Отдельные проверочные проходы
используют тот же ограниченный prefix. Прочитано из 2024 WF и 2025+ TRUE OOS:
**0 байт**. Другие таймфреймы не читались. Нет копирования source CSV в репозиторий.

Все восемь первоначальных отсутствий подтверждены физически. В таблице все
времена — 2023, МСК UTC+3, start-label; даты соседей совпадают с датой пропуска.

| Стратегия | Инструмент | Отсутствующий start-label | Предыдущая свеча | Следующая свеча |
| --- | --- | --- | --- | --- |
| VWAP | USDRUBF | 02.02 15:40:00 | 15:35:00 | 15:45:00 |
| VWAP | CNYRUBF | 06.01 17:15:00 | 17:05:00 | 17:25:00 |
| VWAP | GLDRUBF | 17.08 16:00:00 | 15:55:00 | 16:05:00 |
| VWAP | IMOEXF | 30.11 17:20:00 | 17:15:00 | 17:25:00 |
| Momentum | USDRUBF | 03.02 16:15:00 | 16:10:00 | 16:20:00 |
| Momentum | CNYRUBF | 19.01 15:25:00 | 15:20:00 | 15:30:00 |
| Momentum | GLDRUBF | 12.07 11:40:00 | 11:35:00 | 11:55:00 |
| Momentum | IMOEXF | 15.11 16:25:00 | 16:20:00 | 16:30:00 |

Для каждого случая точный ISO timestamp, соседние timestamps, blob SHA и
`loader_filter_cause=false` находятся в новом `verification.json`. Все восемь
slots находятся внутри объявленного допустимого окна, не затронуты holidays,
March clearing exception, future quarantine или volume filter. Физическое
отсутствие не доказывает биржевой halt, отсутствие сделок или обменный NONFILL.
Восемь исходных missing-entry событий и 82 missing-position исхода — разные группы.

## Каждый из 82 неизвестных исходов

`unresolved_cases.csv` содержит ровно 82 уникальных signal_id: instrument,
strategy, direction, entry time/price, Stop/Take, первый пропуск, все timestamps
113 POSITION_PATH наблюдений, время обнаружения, соседние свечи, blob SHA,
запланированный Time/Session Exit, pending order, conditional reduce-all и ack,
причину неопределённости, статус восстановления и требуемые дополнительные данные.

Для **каждой** позиции независимо просканированы все M5 между входом и первым
пропуском. Проверены приоритет выхода по заранее поданной market close заявке,
Stop-first, entry-bar Stop, запрет entry-bar Take и исторический tick penetration.
Не найдено пропущенного однозначного Stop/Take/Time/Session Exit до возникновения
неопределённости. Все входы существуют физически и соответствуют известному Open.
Все 113 неопределённых observations отсутствуют непосредственно в CSV и совпадают
с `execution_events.csv` и `missing_bar_diagnostics.csv`; per-run счётчики совпали
с `results.json`.

| Первичная взаимно исключающая категория | До | После |
| --- | ---: | ---: |
| Реально недостающий ценовой путь | 82 | 82 |
| Ошибка загрузчика/фильтра/времени | 0 | 0 |
| Ошибка исполнения/закрытия | 0 | 0 |
| Иная объективно неразрешимая причина без missing-path | 0 | 0 |

Дополнительный признак **OBJECTIVELY_UNRESOLVABLE_WITH_AVAILABLE_2023_M5** установлен
для всех 82. Он не прибавляется повторно к первичным категориям. Восемь позиций
уже имели MAX_HOLD/SESSION_FLAT order при возникновении uncertainty; пять случаев
содержат пропуск на/после первого планового Time/Session slot. Их возможный
исход и survival до цены следующего исполнения также не определяются.

На missing slot возможны Stop, Take с penetration и сохранение позиции. OHLCV
соседних баров не ограничивает экстремумы и Open внутри пропуска. Поэтому нельзя
восстановить выход по следующему удобному бару, автоматически выбрать Stop/Take
или считать прошлый Net нулём. Все 82 сохраняют пустые exit/Gross/exit C1/total C1/
Net/exit quantity. Известен entry C1; неизвестная сторона не получает фиктивной цены
или стоимости. Conditional reduce-all подтверждает только flat по контракту v2,
а не реальный fill, исход или P&L сделки.

Для восстановления нужны независимо полученные missing M5 OHLCV для перечисленных
slots, включая Open планового выхода. Если бар отсутствует вследствие остановки
торгов, нужны датированные halt/resumption сведения и ценовая/исполнительная
информация, достаточная для конкретных Stop/Take/survival ветвей. Объявление halt
само по себе не восстанавливает цену или фактический fill. Реальное биржевое P&L
дополнительно требует quantity/fill/cost/order reconciliation. 2024/2025 не решают
эту задачу и не используются. Также нужна более ранняя история 2023 GLD/IMO, если
она существовала: июльский/ноябрьский inception не создаёт полный календарный год.

## Execution model и breach GLDRUBF

| Контроль | Независимый результат |
| --- | --- |
| FINAM / MSK UTC+3 / start-label | поддержан attestation экспортёра; provider metadata независимо не сертифицирована |
| OHLCV t+10; strict later M5 Open | все 7 813 signals и 2 140 entries проверены; обычный entry start = signal start+15m |
| One-bar TTL / NO_BAR_NO_MODEL_FILL | все 61 случая физически отсутствуют; нет fills, retiming или permanent latch; позже есть допустимые entries |
| Gap reset / causal warm-up | independently enumerated 7 813 fixed-rule opportunities; 13 prior contiguous bars, shifted 12 ATR/range; VWAP gap/window reset |
| Frozen protection и параметры | independently enumerated direction/ATR/range/rounded Stop/Take/cap совпали; v1/v2 parameters одинаковы |
| Stop-first / entry-bar TP / tick penetration / adverse gap | все 2 058 accounted exits и все pre-gap пути проверены непосредственно по OHLCV; no entry-bar Take |
| Conditional close / reduce-all | каждый unknown-path scenario заранее заказан; только admissible observed slot; ack = start+10; цена/quantity/Net прошлого не приписаны |
| B−25 → B−20 → B−10 | верно для непрерывного nominal сценария; один реальный missing-bar breach сохранён |
| CNY tick 27.09.2023 19:00 | до switch .01, начиная со switch .001; независимый side-dated расчёт и boundary regression |
| C1 | один historical tick на каждую известную исполненную сторону, без дополнительных regular fee/spread/slippage |

Momentum GLDRUBF `MOMENTUM_GLDRUBF_000291`, 06.10.2023: LONG entry **13:00**,
Stop 5799.9, Take 5822.0; entry 5804.4. SESSION_FLAT order **13:35**, запланированный
scenario **13:40**, но бар **13:40** физически отсутствует. Соседи **13:35 / 13:45**.
Отсутствие обнаружено **13:50**, то есть в момент B−10. Conditional reduce-all на
наблюдаемом **13:45** подтверждён только **13:55**. Это breach на пять минут, не
соблюдение B−10; outcome/Net остаются UNRESOLVED/null. Переобозначение ack временем
сценария или благоприятный выход в 13:35 запрещены и не выполнялись.

## Исправленная отчётность

Замороженные v1/v2 файлы не перезаписаны. Все corrective outputs находятся в
`results/stage2_m5_v2_corrective_review/`, с отдельной schema/provenance/checksums.

1. **Общий PF:** ранее 192 из 312 строк имели числовой общий PF, который новая
   политика запрещает представлять как полный. `PF=full_PF`; известное закрытое
   подмножество публикуется только как `net_PF_closed_diagnostic`. Gross PF также
   имеет явное closed-diagnostic имя.
2. **Полнота периода:** ранее 75 PARTIAL_COVERAGE строк имели `full_PF`, 78 — общий
   `net_model_c1`. Новые full fields требуют полного календарного периода внутри
   объявленных approved windows и полного conditional execution accounting.
   Inception month учитывает slots до начала source, а year/direction наследуют
   годовое coverage. Отдельно сохранены точные closed-only Net/Gross/C1.
3. **Null/status:** ранее 115 строк имели `full_PF=null` без причины null в общем
   PF field. Новые full/closed причины разделены: NO_COVERAGE, UNRESOLVED,
   PARTIAL_COVERAGE, NO_CLOSED_TRADES, NO_LOSSES. Полный ZERO_TRADES означает Net=0,
   PF=null; NO_COVERAGE означает Net=null. Execution accounting и coverage независимы.
   Итоговые verdicts в новых results и verification одинаковы, без stale PENDING.
4. **Momentum before-exit diagnostic:** прежний алгоритм включал Close свечи
   выхода, включая entry-bar Stop. Удалены **329** ошибочных before-exit flags:
   USD 186, CNY 96, GLD 40, IMO 7. Теперь Close обязан завершиться до начала
   exit interval; отдельный causal flag требует availability start+10 до exit
   start. Пересечение breakout edge и нахождение внутри полного frozen range
   различаются явно. Unknown trades не получают false или восстановленную историю.
   Это downstream diagnostic ошибка; торговые решения не использовали этот field.

Все годовые и годовые directional `PF/full_PF/Net/Drawdown` — **null**. Истинный
полный intrabar Drawdown по M5 OHLCV не восстанавливается даже при полном учёте:
`Drawdown=null`, отдельно известные closed-trade DD и observed-close MTM diagnostics.
После неизвестной сделки накопленный MTM остаётся null. Локальный полный месяц
может иметь полный conditional Net/PF независимо от неизвестного результата
предшествующего месяца, если текущий месяц покрыт, flat подтверждён и нет переносимой
неопределённой экспозиции. Это не восстановление общей equity.

Доказательно полны только **6 run-months / 18 month-direction rows** по контракту:

| Run | Месяц | Полный conditional Net C1 | Полный conditional PF |
| --- | --- | ---: | ---: |
| VWAP USDRUBF | 2023-10 | -1.770 | 0.335 |
| VWAP USDRUBF | 2023-12 | -1.690 | 0.302 |
| VWAP CNYRUBF | 2023-12 | -0.152 | 0.474 |
| Momentum USDRUBF | 2023-10 | 1.250 | 1.357 |
| Momentum USDRUBF | 2023-12 | -1.910 | 0.487 |
| Momentum CNYRUBF | 2023-12 | -0.161 | 0.608 |

312 corrective rows: 96 NO_COVERAGE, 99 UNRESOLVED, 99 PARTIAL_COVERAGE,
18 COMPLETE. В 96 ALL-direction run-months: 32 NO_COVERAGE, 32 UNRESOLVED,
26 PARTIAL_COVERAGE, 6 COMPLETE. Прежние 28 NEGATIVE / 3 POSITIVE / 1 ZERO_TRADES
среди учтённых локальных результатов не являются 32 полными календарными месяцами.
ZERO_TRADES отдельно покрыт регрессией, но единственный прежний нулевой bucket
имеет PARTIAL_COVERAGE и не получает фиктивный полный Net=0.

## Экономика восьми неизменённых запусков

Все значения ниже — **закрытое известное подмножество**, normalized quote units
соответствующего инструмента. Это не годовая прибыль и не рублёвый account result;
суммировать инструменты как портфель нельзя. C1 включает только известные стороны
полностью учтённых round trips. Каждый Gross/Net/C1/PF/Expectancy проверен заново.

| Run | Входы / учтено / unknown | Gross | C1 | Net diagnostic | Gross PF | Net PF diagnostic | Net expectancy | Stop / Take / Time+Session |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| VWAP USDRUBF | 548 / 545 / 3 | -5.060 | 10.900 | -15.960 | 0.770 | 0.436 | -0.0293 | 290 / 212 / 43 |
| VWAP CNYRUBF | 367 / 345 / 22 | -1.395 | 4.416 | -5.811 | 0.510 | 0.083 | -0.0168 | 216 / 105 / 24 |
| VWAP GLDRUBF | 126 / 114 / 12 | -51.000 | 22.800 | -73.800 | 0.845 | 0.784 | -0.6474 | 61 / 47 / 6 |
| VWAP IMOEXF | 21 / 13 / 8 | 36.500 | 13.000 | 23.500 | 7.083 | 3.136 | 1.8077 | 4 / 8 / 1 |
| Momentum USDRUBF | 595 / 594 / 1 | 2.730 | 11.880 | -9.150 | 1.093 | 0.759 | -0.0154 | 399 / 83 / 112 |
| Momentum CNYRUBF | 313 / 300 / 13 | -0.106 | 3.048 | -3.154 | 0.959 | 0.371 | -0.0105 | 203 / 42 / 55 |
| Momentum GLDRUBF | 147 / 126 / 21 | 85.600 | 25.200 | 60.400 | 1.203 | 1.138 | 0.4794 | 83 / 20 / 23 |
| Momentum IMOEXF | 23 / 21 / 2 | -28.500 | 21.000 | -49.500 | 0.517 | 0.340 | -2.3571 | 16 / 3 / 2 |

Итого 2 058 известных exits: Stop **1 272 (61.81%)**, Take **520 (25.27%)**,
MAX_HOLD **83**, SESSION_FLAT **183**, совокупные Time/Session **266 (12.93%)**.
Доли только от известного подмножества; unknown outcomes в знаменатель не скрываются.

Entry-level потенциальная бинарная экономика проверена независимо. `R` — distance
до frozen Stop, `T` — distance до frozen Take, `C` — projected 2 dated ticks:
net R/R=`(T-C)/(R+C)`, break-even WR=`(R+C)/(R+T)`. При T<=C положительная бинарная
expectancy невозможна даже при 100% Take. Реальные Time/Session/gap exits меняют
payoff; это потенциальные, а не гарантированные WR/RR. Медианы каждого field
вычисляются отдельно и не обязаны удовлетворять отношению медиан.

| Run | Entry Stop / Take median ticks | Net R/R median | Break-even WR median | Цели <= C1: signals / entries |
| --- | ---: | ---: | ---: | --- |
| VWAP USDRUBF | 7.5 / 8 | 0.556 | 64.29% | 246/1464; 27/548 |
| VWAP CNYRUBF | 2 / 3 | 0.083 | 92.31% | 693/1055; 179/367 |
| VWAP GLDRUBF | 51 / 56 | 1.000 | 50.00% | 9/360; 1/126 |
| VWAP IMOEXF | 6 / 10 | 0.846 | 54.17% | 12/60; 0/21 |
| Momentum USDRUBF | 7 / 25 | 2.313 | 30.19% | 0/2621; 0/595 |
| Momentum CNYRUBF | 3 / 15 | 1.632 | 38.00% | 11/1309; 2/313 |
| Momentum GLDRUBF | 50 / 183 | 2.930 | 25.44% | 0/821; 0/147 |
| Momentum IMOEXF | 6 / 26 | 2.500 | 28.57% | 0/123; 0/23 |

До CNY switch 650/682 VWAP signal targets не покрывают C1; median Take 1 tick
против C1 2 ticks. Это структурное основание будущего cost/tick-aware admission
эксперимента, не доказательство прибыльности фильтра.

| Momentum | Open вернулся за breakout edge | Entry-bar Stop | Stop <=10m | Close вернулся до exit | Возврат уже observable до exit |
| --- | ---: | ---: | ---: | ---: | ---: |
| USDRUBF | 258/595 | 153 | 269 | 262/594 | 187/594 |
| CNYRUBF | 106/313 | 89 | 149 | 106/300 | 70/300 |
| GLDRUBF | 72/147 | 33 | 57 | 50/126 | 35/126 |
| IMOEXF | 13/23 | 4 | 9 | 9/21 | 6/21 |

Open/ранние Stop показатели не изменены; counts Close до выхода исправлены.
Все возвраты — OHLCV proxies, а не доказательство биржевого false breakout.
Данные оправдывают отдельную ограниченную причинную гипотезу качества пробоя,
но не выбор индикатора/порога или использование Close свечи выхода как predictor.

Уже объявленная чувствительность Momentum GLDRUBF t+15 availability / t+20 Open
повторена в памяти без новых параметров: **129 entries / 104 accounted / 25 unknown**,
closed Net **−149.4**, closed PF **0.598**, против baseline **+60.4 / 1.138** с
21 unknown. Знак меняется на неполных разных популяциях; annual profitability
остаётся неизвестной. Нового sweep или выбора лучшей задержки не было.

## Выполненные проверки и воспроизводимость

**114 тестов реально выполнены, OK, без skips**: 100 существующих и 14 новых.
Регрессии проверяют неполный PF, partial/calendar coverage, полный месяц,
NO_COVERAGE vs ZERO_TRADES, причины NO_LOSSES, перенос unknown через месяц,
нулевую закрытую сделку, physical sentinel/no read-ahead, switch ticks,
March clearing, Close свечи выхода и разделение физического Close/availability.
Лог сохранён в `test_execution.log`, его SHA входит в provenance/verification.

Проверены все 2 140 entry и 2 058 полностью учтённых exits, все 82 неизвестных,
113 path events, 61 отсутствующий TTL target и **полный independently enumerated
набор 7 813 signal opportunities**, включая direction и frozen protection.
Заново выполнен прежний independent integer/features/payoff checker:
9 953 economics records и 312 старых metric rows, 0 arithmetic/linkage mismatches.
Новый independent path scanner проверяет также отсутствие более раннего выхода,
чего одно сопоставление уже выбранного exit bar не доказывает.

Frozen replay повторён **в памяти**: `signals.csv`, `execution_events.csv` и
`trade_ledger.csv` **byte-identical** исходному v2. Никаких replacement strategy
outputs не создаётся. Reporting correction дважды выполнена с одним test log;
все **10 corrective artifacts** byte-identical по SHA256SUMS. Это независимые
проверяющие алгоритмы в одной задаче, не второй человек или agent audit.

```bash
mkdir -p work
PYTHONDONTWRITEBYTECODE=1 python -m unittest discover -s IntradayLab/tests -v > work/tests.log 2>&1
PYTHONDONTWRITEBYTECODE=1 python IntradayLab/tools/independent_corrective_review.py --data-root /workspace/market-pattern-data --test-log work/tests.log
cp IntradayLab/results/stage2_m5_v2_corrective_review/SHA256SUMS work/first_SHA256SUMS
PYTHONDONTWRITEBYTECODE=1 python IntradayLab/tools/independent_corrective_review.py --data-root /workspace/market-pattern-data --test-log work/tests.log
cmp work/first_SHA256SUMS IntradayLab/results/stage2_m5_v2_corrective_review/SHA256SUMS
```

Новые JSON/CSV детерминированы при одном test log. Новый запуск тестов может менять
строку времени выполнения и потому SHA самого log/provenance; это не изменение
расчётов. Script проверяет прежние 21 v2 artifact hashes до/после и их SHA256SUMS,
никогда не пишет в v2. Frozen v1 manifest SHA
`7b3a1bd786cee3eca09111f906481a3ab38067c79ec9d0d0d0720c21710319ac` и v2 manifest SHA
`66913447c5e6d4aca53b79cbb62b6d2fb701f21c6198f3d957d962bbe96ef66a` сохранены.

Изменения исключительно внутри IntradayLab. Все root tree/blob IDs вне него
равны фактическому main и родителю #447, включая TradingSystemLab
`7ee08c92fdd5cef92f4a4a6f00a4d26b89fab6b2` и BBW
`7f9990cf12e4421e54a02fd98e507f1e4ef06cb0`. Source checkout чист. Stage 1, v1,
v2 configs/code/results, робот и другие проекты не изменены.

## Вердикты и следующая минимальная задача

| Gate | Verdict | Практическая граница |
| --- | --- | --- |
| Execution model | **PASS в объявленном conditional v2 контракте** | Код/источник/арифметика/причинность подтверждены; реальное исполнение не сертифицировано; конкретный B−10 breach не PASS |
| Research completeness | **NEEDS FIX / ADDITIONAL 2023 EVIDENCE REQUIRED** | 82 unresolved, partial coverage и неполный inception; годовые показатели null |
| VWAP economic viability | **INCONCLUSIVE / NO PASS** | 3 отрицательных известных подмножества; CNY cost/target defect economics; позитивный IMO неполон |
| Momentum economic viability | **INCONCLUSIVE / NO PASS** | 3 отрицательных подмножества; позитивный GLD неполон и меняет знак при объявленной задержке |

Следующая минимальная задача Stage 2 — **отдельно получить/проверить перечисленные
наблюдения 2023 и закрыть input/reconciliation gate**, сохранив неизвестное там,
где ценовой путь не восстановлен. Если их получить нельзя, явно зафиксировать
предел исследуемой истории и неопределённости до экономического acceptance.

Отдельные будущие эксперименты имеют основания, но не реализованы и не разрешены
этим PR: (1) один predeclared cost/tick-aware VWAP admission filter с frozen
Stop/Take, C1 и оценкой opportunities; (2) один causal breakout-quality Momentum
filter с заранее объявленным information time/delay, без Close свечи выхода и
подбора ради PF. Сначала устранить/явно ограничить data gate; потом отдельный
контракт сравнения. PR #444 не merged и не является начатой optimization.

**Volatility Squeeze Breakout** остаётся следующим предусмотренным roadmap
кандидатом после assessment первых двух стратегий. Здесь он не реализован.
Никакого Merge и изменения торговой методологии.
