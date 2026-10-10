# Проверяемые ручные трассировки 2023

34 целевых примеров из фиксированных вариантов #451. Все timestamps — MSK (UTC+3), start-label. OHLCV ниже — короткие цитаты для аудита; исходный набор не копируется. В печати индикаторы округлены до 12 значащих цифр; сравнение использует Decimal и полную точность.

Строка CSV означает номер строки после распаковки, включая заголовок; ключ = run / architecture / scenario / signal_id. Источник — frozen 2023 prefix с SHA256 из audit.json. Все сравнения oracle ↔ journal: MATCH.

| № | Покрытие | Ключ |
| --- | --- | --- |
| 1 | VWAP_MR: LONG TAKE | VWAP_MR_USDRUBF / FROZEN_V2__NONE / C1_T10 / VWAP_MR_USDRUBF_000029 |
| 2 | VWAP_MR: LONG STOP | VWAP_MR_USDRUBF / FROZEN_V2__NONE / C1_T10 / VWAP_MR_USDRUBF_000028 |
| 3 | VWAP_MR: SHORT TAKE | VWAP_MR_USDRUBF / FROZEN_V2__NONE / C1_T10 / VWAP_MR_USDRUBF_000006 |
| 4 | VWAP_MR: SHORT STOP | VWAP_MR_USDRUBF / FROZEN_V2__NONE / C1_T10 / VWAP_MR_USDRUBF_000001 |
| 5 | MOMENTUM: LONG TAKE | MOMENTUM_USDRUBF / FROZEN_V2__NONE / C1_T10 / MOMENTUM_USDRUBF_000001 |
| 6 | MOMENTUM: LONG STOP | MOMENTUM_USDRUBF / FROZEN_V2__NONE / C1_T10 / MOMENTUM_USDRUBF_000019 |
| 7 | MOMENTUM: SHORT TAKE | MOMENTUM_USDRUBF / FROZEN_V2__NONE / C1_T10 / MOMENTUM_USDRUBF_000051 |
| 8 | MOMENTUM: SHORT STOP | MOMENTUM_USDRUBF / FROZEN_V2__NONE / C1_T10 / MOMENTUM_USDRUBF_000058 |
| 9 | Momentum BREAKEVEN_STOP, LONG | MOMENTUM_USDRUBF / ENTRY_MANAGEMENT__NONE / C1_T10 / MOMENTUM_USDRUBF_000330 |
| 10 | Momentum BREAKEVEN_STOP, SHORT | MOMENTUM_USDRUBF / ENTRY_MANAGEMENT__NONE / C1_T10 / MOMENTUM_USDRUBF_000248 |
| 11 | Momentum TRAIL_STOP, LONG | MOMENTUM_USDRUBF / ENTRY_MANAGEMENT__NONE / C1_T10 / MOMENTUM_USDRUBF_000197 |
| 12 | Momentum TRAIL_STOP, SHORT | MOMENTUM_USDRUBF / ENTRY_MANAGEMENT__NONE / C1_T10 / MOMENTUM_USDRUBF_000759 |
| 13 | FAILED_BREAKOUT | MOMENTUM_USDRUBF / ENTRY_MANAGEMENT__NONE / C1_T10 / MOMENTUM_USDRUBF_000030 |
| 14 | MOMENTUM_NO_PROGRESS_30M | MOMENTUM_USDRUBF / ENTRY_MANAGEMENT__NONE / C1_T10 / MOMENTUM_USDRUBF_000194 |
| 15 | VWAP_PREMISE_FAILED | VWAP_MR_USDRUBF / PAYABLE_CAP_FULL_M5__NONE / C1_T10 / VWAP_MR_USDRUBF_000030 |
| 16 | VWAP_NO_PROGRESS_30M | VWAP_MR_USDRUBF / PAYABLE_CAP_FULL_M5__NONE / C1_T10 / VWAP_MR_USDRUBF_000305 |
| 17 | MAX_HOLD | VWAP_MR_USDRUBF / FROZEN_V2__NONE / C1_T10 / VWAP_MR_USDRUBF_000020 |
| 18 | SESSION_FLAT | VWAP_MR_USDRUBF / FROZEN_V2__NONE / C1_T10 / VWAP_MR_USDRUBF_000030 |
| 19 | Stop-first при Stop/Take в одной свече | VWAP_MR_GLDRUBF / FROZEN_V2__NONE / C1_T10 / VWAP_MR_GLDRUBF_000092 |
| 20 | Stop на свече входа | VWAP_MR_USDRUBF / FROZEN_V2__NONE / C1_T10 / VWAP_MR_USDRUBF_000016 |
| 21 | Stop: худший Open при гэпе | VWAP_MR_USDRUBF / FROZEN_V2__NONE / C1_T10 / VWAP_MR_USDRUBF_000260 |
| 22 | Неизвестный путь: цена и P&L null | VWAP_MR_USDRUBF / FROZEN_V2__NONE / C1_T10 / VWAP_MR_USDRUBF_000124 |
| 23 | T15: позднее подтверждение session flat | VWAP_MR_USDRUBF / FROZEN_V2__NONE / C1_T15_DELAY / VWAP_MR_USDRUBF_000134 |
| 24 | CNY: датированный tick 0.001 | VWAP_MR_CNYRUBF / FROZEN_V2__NONE / C1_T10 / VWAP_MR_CNYRUBF_000684 |
| 25 | GLD: главный победитель FULL M30 | MOMENTUM_GLDRUBF / FULL_M5__M30 / C1_T10 / MOMENTUM_GLDRUBF_000312 |
| 26 | MR payable-cap и причинный M15 | VWAP_MR_USDRUBF / PAYABLE_CAP_ENTRY__M15 / C1_T10 / VWAP_MR_USDRUBF_000020 |
| 27 | Momentum: причинный H1 | MOMENTUM_USDRUBF / ENTRY_MANAGEMENT__H1 / C1_T10 / MOMENTUM_USDRUBF_000201 |
| 28 | BREAKOUT_NOT_PERSISTENT | MOMENTUM_USDRUBF / ENTRY_MANAGEMENT__NONE / C1_T10 / MOMENTUM_USDRUBF_000001 |
| 29 | NO_BAR_NO_MODEL_FILL | VWAP_MR_USDRUBF / FROZEN_V2__NONE / C1_T10 / VWAP_MR_USDRUBF_000134 |
| 30 | MTF_INCOMPLETE_CHILD_BUCKET | VWAP_MR_USDRUBF / FROZEN_V2__M30 / C1_T10 / VWAP_MR_USDRUBF_000419 |
| 31 | MOMENTUM_ADX_DI_REGIME | MOMENTUM_USDRUBF / FULL_M5__NONE / C1_T10 / MOMENTUM_USDRUBF_000002 |
| 32 | Мартовская граница: вход запрещён | VWAP_MR_USDRUBF / FROZEN_V2__NONE / C1_T10 / VWAP_MR_USDRUBF_000281 |
| 33 | Take touch без tick penetration: nonfill | VWAP_MR_USDRUBF / FROZEN_V2__NONE / C1_T10 / VWAP_MR_USDRUBF_000014 |
| 34 | Take на свече входа запрещён | VWAP_MR_USDRUBF / FROZEN_V2__NONE / C1_T10 / VWAP_MR_USDRUBF_000031 |

## 1. VWAP_MR: LONG TAKE

`VWAP_MR_USDRUBF / FROZEN_V2__NONE / C1_T10 / VWAP_MR_USDRUBF_000029`. Signal CSV строка **30**; ledger строка **10**.

Сигнал 2023-01-09 16:55:00, Close доступен 2023-01-09 17:05:00; ready 2023-01-09 17:05:00; exact scheduled Open 2023-01-09 17:10:00. Направление LONG; status/reason **MODELLED / CONDITIONAL_OPEN_SCENARIO**.

ATR12 = сумма прошлых 12 TR / 12 = 1.30000000000 / 12 = **0.108333333333**. VWAP = 671030.610000 / 9592 = **69.9573196414**; локальный anchor 2023-01-09 14:05:00; prior bars 34.

12 TR, исключая signal bar (2023-01-09 15:55:00 … 2023-01-09 16:50:00): `0.06, 0.05, 0.06, 0.05, 0.10, 0.06, 0.08, 0.07, 0.26, 0.08, 0.22, 0.21`.

Условие сигнала: **69.85 ≤ 69.8513884744; 69.8489863080 < 69.86 < 69.9573196414**. ATR14 0.114601687832; ADX14 35.6128087831; +DI/-DI 27.6937218665 / 27.0992437191. Архитектура FROZEN_V2 определяет, используются ли эти контексты.

Initial Stop **69.70**, frozen Take **69.96**, cap **69.88**, dated tick 0.01. Swing последних 3 включая сигнал [69.57, 69.95].

Boundary entry check: scheduled end 2023-01-09 17:15:00 ≤ B−30 2023-01-09 18:20:00 = True; окно signal/entry совпадает True.

Stop raw Close−direction×1.5ATR12 = 69.6975000000, округление up → 69.70.

Take raw 69.9573196414, округление up → 69.96; original cap raw Close+direction×0.25ATR12 = 69.8870833333.

Scheduled Open 69.86: signed risk 0.16, reward 0.10, direction×(Open−cap) -0.02 ≤0. Entry-quality ruler: risk≥4tick 0.04 = True; reward−2tick 0.08 ≥ risk+2tick 0.18 = False. Entry-quality ruler применяется только ENTRY/FULL/payable, не FROZEN_V2.

| Start MSK | Роль | O | H | L | C | V |
| --- | --- | --- | --- | --- | --- | --- |
| 2023-01-09 16:50:00 | previous, source row 770 | 69.75 | 69.95 | 69.75 | 69.85 | 185 |
| 2023-01-09 16:55:00 | signal, source row 771 | 69.87 | 69.89 | 69.8 | 69.86 | 210 |
| 2023-01-09 17:10:00 | scheduled entry, source row 774 | 69.86 | 70.02 | 69.86 | 69.99 | 356 |
| 2023-01-09 17:15:00 | EXIT, source row 775 | 70 | 70.01 | 69.94 | 69.98 | 221 |

Решения и исполнения (сравнение с execution_events.csv.gz: MATCH):

- 2023-01-09 17:05:00: ENTRY_ORDER SUBMITTED, FIXED_SIGNAL; price null; ack —; flags —.
- 2023-01-09 17:10:00: ENTRY MODELLED, CONDITIONAL_OPEN_SCENARIO; price 69.86; ack 2023-01-09 17:20:00; flags —.
- 2023-01-09 17:15:00: EXIT MODELLED, TAKE; price 69.96; ack 2023-01-09 17:25:00; flags —.

Exit **69.96**, reason **TAKE**, interval [2023-01-09 17:15:00, 2023-01-09 17:20:00), ack 2023-01-09 17:25:00. Gross = 1×(69.96−69.86) = **0.10**; C1 = 0.01 + 0.01 = 0.02; Net = **0.08**; initial risk = |entry−initial stop| = 0.16; Net R = **0.5**. Flat deadline breach False. Oracle ↔ ledger: **MATCH**.

## 2. VWAP_MR: LONG STOP

`VWAP_MR_USDRUBF / FROZEN_V2__NONE / C1_T10 / VWAP_MR_USDRUBF_000028`. Signal CSV строка **29**; ledger строка **9**.

Сигнал 2023-01-09 11:55:00, Close доступен 2023-01-09 12:05:00; ready 2023-01-09 12:05:00; exact scheduled Open 2023-01-09 12:10:00. Направление LONG; status/reason **MODELLED / CONDITIONAL_OPEN_SCENARIO**.

ATR12 = сумма прошлых 12 TR / 12 = 1.39000000000 / 12 = **0.115833333333**. VWAP = 674145.873333 / 9502 = **70.9477871325**; локальный anchor 2023-01-09 10:00:00; prior bars 23.

12 TR, исключая signal bar (2023-01-09 10:55:00 … 2023-01-09 11:50:00): `0.11, 0.18, 0.10, 0.09, 0.10, 0.05, 0.12, 0.07, 0.12, 0.14, 0.11, 0.20`.

Условие сигнала: **70.76 ≤ 70.8357505757; 70.8319537992 < 70.84 < 70.9477871325**. ATR14 0.149627029533; ADX14 null; +DI/-DI 13.3114606938 / 25.2154906444. Архитектура FROZEN_V2 определяет, используются ли эти контексты.

Initial Stop **70.67**, frozen Take **70.95**, cap **70.86**, dated tick 0.01. Swing последних 3 включая сигнал [70.71, 70.99].

Boundary entry check: scheduled end 2023-01-09 12:15:00 ≤ B−30 2023-01-09 13:30:00 = True; окно signal/entry совпадает True.

Stop raw Close−direction×1.5ATR12 = 70.6662500000, округление up → 70.67.

Take raw 70.9477871325, округление up → 70.95; original cap raw Close+direction×0.25ATR12 = 70.8689583333.

Scheduled Open 70.83: signed risk 0.16, reward 0.12, direction×(Open−cap) -0.03 ≤0. Entry-quality ruler: risk≥4tick 0.04 = True; reward−2tick 0.10 ≥ risk+2tick 0.18 = False. Entry-quality ruler применяется только ENTRY/FULL/payable, не FROZEN_V2.

| Start MSK | Роль | O | H | L | C | V |
| --- | --- | --- | --- | --- | --- | --- |
| 2023-01-09 11:50:00 | previous, source row 711 | 70.91 | 70.91 | 70.74 | 70.76 | 193 |
| 2023-01-09 11:55:00 | signal, source row 712 | 70.74 | 70.85 | 70.71 | 70.84 | 238 |
| 2023-01-09 12:10:00 | scheduled entry, source row 715 | 70.83 | 70.87 | 70.75 | 70.84 | 529 |
| 2023-01-09 12:15:00 | EXIT, source row 716 | 70.8 | 70.83 | 70.53 | 70.59 | 672 |

Решения и исполнения (сравнение с execution_events.csv.gz: MATCH):

- 2023-01-09 12:05:00: ENTRY_ORDER SUBMITTED, FIXED_SIGNAL; price null; ack —; flags —.
- 2023-01-09 12:10:00: ENTRY MODELLED, CONDITIONAL_OPEN_SCENARIO; price 70.83; ack 2023-01-09 12:20:00; flags —.
- 2023-01-09 12:15:00: EXIT MODELLED, STOP; price 70.67; ack 2023-01-09 12:25:00; flags —.

Exit **70.67**, reason **STOP**, interval [2023-01-09 12:15:00, 2023-01-09 12:20:00), ack 2023-01-09 12:25:00. Gross = 1×(70.67−70.83) = **-0.16**; C1 = 0.01 + 0.01 = 0.02; Net = **-0.18**; initial risk = |entry−initial stop| = 0.16; Net R = **-1.125**. Flat deadline breach False. Oracle ↔ ledger: **MATCH**.

## 3. VWAP_MR: SHORT TAKE

`VWAP_MR_USDRUBF / FROZEN_V2__NONE / C1_T10 / VWAP_MR_USDRUBF_000006`. Signal CSV строка **7**; ledger строка **3**.

Сигнал 2023-01-04 11:50:00, Close доступен 2023-01-04 12:00:00; ready 2023-01-04 12:00:00; exact scheduled Open 2023-01-04 12:05:00. Направление SHORT; status/reason **MODELLED / CONDITIONAL_OPEN_SCENARIO**.

ATR12 = сумма прошлых 12 TR / 12 = 1.93000000000 / 12 = **0.160833333333**. VWAP = 646358.923333 / 9045 = **71.4603563663**; локальный anchor 2023-01-04 10:00:00; prior bars 22.

12 TR, исключая signal bar (2023-01-04 10:50:00 … 2023-01-04 11:45:00): `0.07, 0.11, 0.35, 0.15, 0.23, 0.14, 0.11, 0.15, 0.15, 0.09, 0.14, 0.24`.

Условие сигнала: **71.7 ≥ 71.6166263426; 71.4603563663 < 71.58 < 71.6211896996**. ATR14 0.159704530811; ADX14 null; +DI/-DI 23.3310547825 / 21.5078259206. Архитектура FROZEN_V2 определяет, используются ли эти контексты.

Initial Stop **71.82**, frozen Take **71.46**, cap **71.54**, dated tick 0.01. Swing последних 3 включая сигнал [71.47, 71.77].

Boundary entry check: scheduled end 2023-01-04 12:10:00 ≤ B−30 2023-01-04 13:30:00 = True; окно signal/entry совпадает True.

Stop raw Close−direction×1.5ATR12 = 71.8212500000, округление down → 71.82.

Take raw 71.4603563663, округление down → 71.46; original cap raw Close+direction×0.25ATR12 = 71.5397916667.

Scheduled Open 71.77: signed risk 0.05, reward 0.31, direction×(Open−cap) -0.23 ≤0. Entry-quality ruler: risk≥4tick 0.04 = True; reward−2tick 0.29 ≥ risk+2tick 0.07 = True. Entry-quality ruler применяется только ENTRY/FULL/payable, не FROZEN_V2.

| Start MSK | Роль | O | H | L | C | V |
| --- | --- | --- | --- | --- | --- | --- |
| 2023-01-04 11:45:00 | previous, source row 207 | 71.55 | 71.77 | 71.53 | 71.7 | 288 |
| 2023-01-04 11:50:00 | signal, source row 208 | 71.71 | 71.72 | 71.54 | 71.58 | 262 |
| 2023-01-04 12:05:00 | scheduled entry, source row 211 | 71.77 | 71.79 | 71.67 | 71.7 | 341 |
| 2023-01-04 12:10:00 | EXIT, source row 212 | 71.7 | 71.7 | 71.4 | 71.4 | 453 |

Решения и исполнения (сравнение с execution_events.csv.gz: MATCH):

- 2023-01-04 12:00:00: ENTRY_ORDER SUBMITTED, FIXED_SIGNAL; price null; ack —; flags —.
- 2023-01-04 12:05:00: ENTRY MODELLED, CONDITIONAL_OPEN_SCENARIO; price 71.77; ack 2023-01-04 12:15:00; flags —.
- 2023-01-04 12:10:00: EXIT MODELLED, TAKE; price 71.46; ack 2023-01-04 12:20:00; flags —.

Exit **71.46**, reason **TAKE**, interval [2023-01-04 12:10:00, 2023-01-04 12:15:00), ack 2023-01-04 12:20:00. Gross = -1×(71.46−71.77) = **0.31**; C1 = 0.01 + 0.01 = 0.02; Net = **0.29**; initial risk = |entry−initial stop| = 0.05; Net R = **5.8**. Flat deadline breach False. Oracle ↔ ledger: **MATCH**.

## 4. VWAP_MR: SHORT STOP

`VWAP_MR_USDRUBF / FROZEN_V2__NONE / C1_T10 / VWAP_MR_USDRUBF_000001`. Signal CSV строка **2**; ledger строка **2**.

Сигнал 2023-01-03 11:40:00, Close доступен 2023-01-03 11:50:00; ready 2023-01-03 11:50:00; exact scheduled Open 2023-01-03 11:55:00. Направление SHORT; status/reason **MODELLED / CONDITIONAL_OPEN_SCENARIO**.

ATR12 = сумма прошлых 12 TR / 12 = 1.78000000000 / 12 = **0.148333333333**. VWAP = 440742.693333 / 6291 = **70.0592423038**; локальный anchor 2023-01-03 10:00:00; prior bars 20.

12 TR, исключая signal bar (2023-01-03 10:40:00 … 2023-01-03 11:35:00): `0.20, 0.17, 0.26, 0.16, 0.16, 0.18, 0.07, 0.09, 0.16, 0.06, 0.11, 0.16`.

Условие сигнала: **70.26 ≥ 70.2050977216; 70.0592423038 < 70.19 < 70.2075756372**. ATR14 0.160918881987; ADX14 null; +DI/-DI 27.9889540398 / 16.0900273272. Архитектура FROZEN_V2 определяет, используются ли эти контексты.

Initial Stop **70.41**, frozen Take **70.05**, cap **70.16**, dated tick 0.01. Swing последних 3 включая сигнал [70.02, 70.26].

Boundary entry check: scheduled end 2023-01-03 12:00:00 ≤ B−30 2023-01-03 13:30:00 = True; окно signal/entry совпадает True.

Stop raw Close−direction×1.5ATR12 = 70.4125000000, округление down → 70.41.

Take raw 70.0592423038, округление down → 70.05; original cap raw Close+direction×0.25ATR12 = 70.1529166667.

Scheduled Open 70.18: signed risk 0.23, reward 0.13, direction×(Open−cap) -0.02 ≤0. Entry-quality ruler: risk≥4tick 0.04 = True; reward−2tick 0.11 ≥ risk+2tick 0.25 = False. Entry-quality ruler применяется только ENTRY/FULL/payable, не FROZEN_V2.

| Start MSK | Роль | O | H | L | C | V |
| --- | --- | --- | --- | --- | --- | --- |
| 2023-01-03 11:35:00 | previous, source row 33 | 70.13 | 70.26 | 70.1 | 70.26 | 133 |
| 2023-01-03 11:40:00 | signal, source row 34 | 70.24 | 70.24 | 70.14 | 70.19 | 117 |
| 2023-01-03 11:55:00 | scheduled entry, source row 37 | 70.18 | 70.2 | 70.16 | 70.2 | 39 |
| 2023-01-03 12:30:00 | EXIT, source row 44 | 70.3 | 70.42 | 70.3 | 70.35 | 202 |

Решения и исполнения (сравнение с execution_events.csv.gz: MATCH):

- 2023-01-03 11:50:00: ENTRY_ORDER SUBMITTED, FIXED_SIGNAL; price null; ack —; flags —.
- 2023-01-03 11:55:00: ENTRY MODELLED, CONDITIONAL_OPEN_SCENARIO; price 70.18; ack 2023-01-03 12:05:00; flags —.
- 2023-01-03 12:30:00: EXIT MODELLED, STOP; price 70.41; ack 2023-01-03 12:40:00; flags —.

Exit **70.41**, reason **STOP**, interval [2023-01-03 12:30:00, 2023-01-03 12:35:00), ack 2023-01-03 12:40:00. Gross = -1×(70.41−70.18) = **-0.23**; C1 = 0.01 + 0.01 = 0.02; Net = **-0.25**; initial risk = |entry−initial stop| = 0.23; Net R = **-1.08695652174**. Flat deadline breach False. Oracle ↔ ledger: **MATCH**.

## 5. MOMENTUM: LONG TAKE

`MOMENTUM_USDRUBF / FROZEN_V2__NONE / C1_T10 / MOMENTUM_USDRUBF_000001`. Signal CSV строка **46554**; ledger строка **4405**.

Сигнал 2023-01-03 11:35:00, Close доступен 2023-01-03 11:45:00; ready 2023-01-03 11:45:00; exact scheduled Open 2023-01-03 11:50:00. Направление LONG; status/reason **MODELLED / CONDITIONAL_OPEN_SCENARIO**.

ATR12 = сумма прошлых 12 TR / 12 = 1.91000000000 / 12 = **0.159166666667**. VWAP = 432530.463333 / 6174 = **70.0567643883**; локальный anchor 2023-01-03 10:00:00; prior bars 19.

12 TR, исключая signal bar (2023-01-03 10:35:00 … 2023-01-03 11:30:00): `0.29, 0.20, 0.17, 0.26, 0.16, 0.16, 0.18, 0.07, 0.09, 0.16, 0.06, 0.11`.

Условие сигнала: **Close 70.26 > prior-12 edge 70.2; range [69.76, 70.2]**. ATR14 0.164066488294; ADX14 null; +DI/-DI 29.5636788872 / 16.9952903746. Архитектура FROZEN_V2 определяет, используются ли эти контексты.

Initial Stop **70.03**, frozen Take **70.74**, cap **70.29**, dated tick 0.01. Swing последних 3 включая сигнал [70.01, 70.26].

Boundary entry check: scheduled end 2023-01-03 11:55:00 ≤ B−30 2023-01-03 13:30:00 = True; окно signal/entry совпадает True.

Stop raw Close−direction×1.5ATR12 = 70.0212500000, округление up → 70.03.

Take raw 70.7375000000, округление up → 70.74; original cap raw Close+direction×0.25ATR12 = 70.2997916667.

Scheduled Open 70.2: signed risk 0.17, reward 0.54, direction×(Open−cap) -0.09 ≤0. Entry-quality ruler: risk≥4tick 0.04 = True; reward−2tick 0.52 ≥ risk+2tick 0.19 = True. Entry-quality ruler применяется только ENTRY/FULL/payable, не FROZEN_V2.

| Start MSK | Роль | O | H | L | C | V |
| --- | --- | --- | --- | --- | --- | --- |
| 2023-01-03 11:30:00 | previous, source row 32 | 70.04 | 70.13 | 70.02 | 70.13 | 147 |
| 2023-01-03 11:35:00 | signal, source row 33 | 70.13 | 70.26 | 70.1 | 70.26 | 133 |
| 2023-01-03 11:50:00 | scheduled entry, source row 36 | 70.2 | 70.2 | 70.16 | 70.18 | 24 |
| 2023-01-03 13:00:00 | EXIT, source row 50 | 70.68 | 70.84 | 70.67 | 70.77 | 314 |

Решения и исполнения (сравнение с execution_events.csv.gz: MATCH):

- 2023-01-03 11:45:00: ENTRY_ORDER SUBMITTED, FIXED_SIGNAL; price null; ack —; flags —.
- 2023-01-03 11:50:00: ENTRY MODELLED, CONDITIONAL_OPEN_SCENARIO; price 70.2; ack 2023-01-03 12:00:00; flags —.
- 2023-01-03 13:00:00: EXIT MODELLED, TAKE; price 70.74; ack 2023-01-03 13:10:00; flags —.

Exit **70.74**, reason **TAKE**, interval [2023-01-03 13:00:00, 2023-01-03 13:05:00), ack 2023-01-03 13:10:00. Gross = 1×(70.74−70.2) = **0.54**; C1 = 0.01 + 0.01 = 0.02; Net = **0.52**; initial risk = |entry−initial stop| = 0.17; Net R = **3.05882352941**. Flat deadline breach False. Oracle ↔ ledger: **MATCH**.

## 6. MOMENTUM: LONG STOP

`MOMENTUM_USDRUBF / FROZEN_V2__NONE / C1_T10 / MOMENTUM_USDRUBF_000019`. Signal CSV строка **46572**; ledger строка **4407**.

Сигнал 2023-01-04 11:45:00, Close доступен 2023-01-04 11:55:00; ready 2023-01-04 11:55:00; exact scheduled Open 2023-01-04 12:00:00. Направление LONG; status/reason **MODELLED / CONDITIONAL_OPEN_SCENARIO**.

ATR12 = сумма прошлых 12 TR / 12 = 1.76000000000 / 12 = **0.146666666667**. VWAP = 627596.230000 / 8783 = **71.4557930092**; локальный anchor 2023-01-04 10:00:00; prior bars 21.

12 TR, исключая signal bar (2023-01-04 10:45:00 … 2023-01-04 11:40:00): `0.07, 0.07, 0.11, 0.35, 0.15, 0.23, 0.14, 0.11, 0.15, 0.15, 0.09, 0.14`.

Условие сигнала: **Close 71.7 > prior-12 edge 71.65; range [71.07, 71.65]**. ATR14 0.158143340873; ADX14 null; +DI/-DI 25.3737925426 / 23.3909318734. Архитектура FROZEN_V2 определяет, используются ли эти контексты.

Initial Stop **71.48**, frozen Take **72.14**, cap **71.73**, dated tick 0.01. Swing последних 3 включая сигнал [71.43, 71.77].

Boundary entry check: scheduled end 2023-01-04 12:05:00 ≤ B−30 2023-01-04 13:30:00 = True; окно signal/entry совпадает True.

Stop raw Close−direction×1.5ATR12 = 71.4800000000, округление up → 71.48.

Take raw 72.1400000000, округление up → 72.14; original cap raw Close+direction×0.25ATR12 = 71.7366666667.

Scheduled Open 71.65: signed risk 0.17, reward 0.49, direction×(Open−cap) -0.08 ≤0. Entry-quality ruler: risk≥4tick 0.04 = True; reward−2tick 0.47 ≥ risk+2tick 0.19 = True. Entry-quality ruler применяется только ENTRY/FULL/payable, не FROZEN_V2.

| Start MSK | Роль | O | H | L | C | V |
| --- | --- | --- | --- | --- | --- | --- |
| 2023-01-04 11:40:00 | previous, source row 206 | 71.48 | 71.6 | 71.47 | 71.55 | 195 |
| 2023-01-04 11:45:00 | signal, source row 207 | 71.55 | 71.77 | 71.53 | 71.7 | 288 |
| 2023-01-04 12:00:00 | scheduled entry, source row 210 | 71.65 | 71.84 | 71.65 | 71.77 | 179 |
| 2023-01-04 12:10:00 | EXIT, source row 212 | 71.7 | 71.7 | 71.4 | 71.4 | 453 |

Решения и исполнения (сравнение с execution_events.csv.gz: MATCH):

- 2023-01-04 11:55:00: ENTRY_ORDER SUBMITTED, FIXED_SIGNAL; price null; ack —; flags —.
- 2023-01-04 12:00:00: ENTRY MODELLED, CONDITIONAL_OPEN_SCENARIO; price 71.65; ack 2023-01-04 12:10:00; flags —.
- 2023-01-04 12:10:00: EXIT MODELLED, STOP; price 71.48; ack 2023-01-04 12:20:00; flags —.

Exit **71.48**, reason **STOP**, interval [2023-01-04 12:10:00, 2023-01-04 12:15:00), ack 2023-01-04 12:20:00. Gross = 1×(71.48−71.65) = **-0.17**; C1 = 0.01 + 0.01 = 0.02; Net = **-0.19**; initial risk = |entry−initial stop| = 0.17; Net R = **-1.11764705882**. Flat deadline breach False. Oracle ↔ ledger: **MATCH**.

## 7. MOMENTUM: SHORT TAKE

`MOMENTUM_USDRUBF / FROZEN_V2__NONE / C1_T10 / MOMENTUM_USDRUBF_000051`. Signal CSV строка **46604**; ledger строка **4414**.

Сигнал 2023-01-09 11:50:00, Close доступен 2023-01-09 12:00:00; ready 2023-01-09 12:00:00; exact scheduled Open 2023-01-09 12:05:00. Направление SHORT; status/reason **MODELLED / CONDITIONAL_OPEN_SCENARIO**.

ATR12 = сумма прошлых 12 TR / 12 = 1.28000000000 / 12 = **0.106666666667**. VWAP = 657295.473333 / 9264 = **70.9515839090**; локальный anchor 2023-01-09 10:00:00; prior bars 22.

12 TR, исключая signal bar (2023-01-09 10:50:00 … 2023-01-09 11:45:00): `0.09, 0.11, 0.18, 0.10, 0.09, 0.10, 0.05, 0.12, 0.07, 0.12, 0.14, 0.11`.

Условие сигнала: **Close 70.76 < prior-12 edge 70.88; range [70.88, 71.21]**. ATR14 0.150367570266; ADX14 null; +DI/-DI 14.2648191330 / 25.4867074158. Архитектура FROZEN_V2 определяет, используются ли эти контексты.

Initial Stop **70.92**, frozen Take **70.44**, cap **70.74**, dated tick 0.01. Swing последних 3 включая сигнал [70.74, 71.03].

Boundary entry check: scheduled end 2023-01-09 12:10:00 ≤ B−30 2023-01-09 13:30:00 = True; окно signal/entry совпадает True.

Stop raw Close−direction×1.5ATR12 = 70.9200000000, округление down → 70.92.

Take raw 70.4400000000, округление down → 70.44; original cap raw Close+direction×0.25ATR12 = 70.7333333333.

Scheduled Open 70.85: signed risk 0.07, reward 0.41, direction×(Open−cap) -0.11 ≤0. Entry-quality ruler: risk≥4tick 0.04 = True; reward−2tick 0.39 ≥ risk+2tick 0.09 = True. Entry-quality ruler применяется только ENTRY/FULL/payable, не FROZEN_V2.

| Start MSK | Роль | O | H | L | C | V |
| --- | --- | --- | --- | --- | --- | --- |
| 2023-01-09 11:45:00 | previous, source row 710 | 70.99 | 70.99 | 70.88 | 70.94 | 177 |
| 2023-01-09 11:50:00 | signal, source row 711 | 70.91 | 70.91 | 70.74 | 70.76 | 193 |
| 2023-01-09 12:05:00 | scheduled entry, source row 714 | 70.85 | 70.89 | 70.7 | 70.84 | 628 |
| 2023-01-09 12:20:00 | EXIT, source row 717 | 70.59 | 70.66 | 70.26 | 70.37 | 1238 |

Решения и исполнения (сравнение с execution_events.csv.gz: MATCH):

- 2023-01-09 12:00:00: ENTRY_ORDER SUBMITTED, FIXED_SIGNAL; price null; ack —; flags —.
- 2023-01-09 12:05:00: ENTRY MODELLED, CONDITIONAL_OPEN_SCENARIO; price 70.85; ack 2023-01-09 12:15:00; flags —.
- 2023-01-09 12:20:00: EXIT MODELLED, TAKE; price 70.44; ack 2023-01-09 12:30:00; flags —.

Exit **70.44**, reason **TAKE**, interval [2023-01-09 12:20:00, 2023-01-09 12:25:00), ack 2023-01-09 12:30:00. Gross = -1×(70.44−70.85) = **0.41**; C1 = 0.01 + 0.01 = 0.02; Net = **0.39**; initial risk = |entry−initial stop| = 0.07; Net R = **5.57142857143**. Flat deadline breach False. Oracle ↔ ledger: **MATCH**.

## 8. MOMENTUM: SHORT STOP

`MOMENTUM_USDRUBF / FROZEN_V2__NONE / C1_T10 / MOMENTUM_USDRUBF_000058`. Signal CSV строка **46611**; ledger строка **4415**.

Сигнал 2023-01-09 15:45:00, Close доступен 2023-01-09 15:55:00; ready 2023-01-09 15:55:00; exact scheduled Open 2023-01-09 16:00:00. Направление SHORT; status/reason **MODELLED / CONDITIONAL_OPEN_SCENARIO**.

ATR12 = сумма прошлых 12 TR / 12 = 0.980000000000 / 12 = **0.0816666666667**. VWAP = 437136.783333 / 6239 = **70.0652000855**; локальный anchor 2023-01-09 14:05:00; prior bars 20.

12 TR, исключая signal bar (2023-01-09 14:45:00 … 2023-01-09 15:40:00): `0.05, 0.03, 0.09, 0.11, 0.21, 0.07, 0.04, 0.08, 0.07, 0.09, 0.08, 0.06`.

Условие сигнала: **Close 69.77 < prior-12 edge 69.83; range [69.83, 70.09]**. ATR14 0.105528497468; ADX14 null; +DI/-DI 12.3636107450 / 37.7872643974. Архитектура FROZEN_V2 определяет, используются ли эти контексты.

Initial Stop **69.89**, frozen Take **69.52**, cap **69.75**, dated tick 0.01. Swing последних 3 включая сигнал [69.76, 69.93].

Boundary entry check: scheduled end 2023-01-09 16:05:00 ≤ B−30 2023-01-09 18:20:00 = True; окно signal/entry совпадает True.

Stop raw Close−direction×1.5ATR12 = 69.8925000000, округление down → 69.89.

Take raw 69.5250000000, округление down → 69.52; original cap raw Close+direction×0.25ATR12 = 69.7495833333.

Scheduled Open 69.85: signed risk 0.04, reward 0.33, direction×(Open−cap) -0.10 ≤0. Entry-quality ruler: risk≥4tick 0.04 = True; reward−2tick 0.31 ≥ risk+2tick 0.06 = True. Entry-quality ruler применяется только ENTRY/FULL/payable, не FROZEN_V2.

| Start MSK | Роль | O | H | L | C | V |
| --- | --- | --- | --- | --- | --- | --- |
| 2023-01-09 15:40:00 | previous, source row 756 | 69.88 | 69.88 | 69.83 | 69.85 | 83 |
| 2023-01-09 15:45:00 | signal, source row 757 | 69.85 | 69.85 | 69.76 | 69.77 | 161 |
| 2023-01-09 16:00:00 | scheduled entry, source row 760 | 69.85 | 69.86 | 69.81 | 69.84 | 273 |
| 2023-01-09 16:40:00 | TP, source row 768 | 69.53 | 69.6 | 69.52 | 69.59 | 214 |
| 2023-01-09 16:50:00 | EXIT, source row 770 | 69.75 | 69.95 | 69.75 | 69.85 | 185 |

Решения и исполнения (сравнение с execution_events.csv.gz: MATCH):

- 2023-01-09 15:55:00: ENTRY_ORDER SUBMITTED, FIXED_SIGNAL; price null; ack —; flags —.
- 2023-01-09 16:00:00: ENTRY MODELLED, CONDITIONAL_OPEN_SCENARIO; price 69.85; ack 2023-01-09 16:10:00; flags —.
- 2023-01-09 16:40:00: TP NONFILL, TOUCH_WITHOUT_TICK_PENETRATION; price null; ack 2023-01-09 16:50:00; flags —.
- 2023-01-09 16:50:00: EXIT MODELLED, STOP; price 69.89; ack 2023-01-09 17:00:00; flags —.

Exit **69.89**, reason **STOP**, interval [2023-01-09 16:50:00, 2023-01-09 16:55:00), ack 2023-01-09 17:00:00. Gross = -1×(69.89−69.85) = **-0.04**; C1 = 0.01 + 0.01 = 0.02; Net = **-0.06**; initial risk = |entry−initial stop| = 0.04; Net R = **-1.5**. Flat deadline breach False. Oracle ↔ ledger: **MATCH**.

## 9. Momentum BREAKEVEN_STOP, LONG

`MOMENTUM_USDRUBF / ENTRY_MANAGEMENT__NONE / C1_T10 / MOMENTUM_USDRUBF_000330`. Signal CSV строка **52125**; ledger строка **5283**.

Сигнал 2023-02-15 17:50:00, Close доступен 2023-02-15 18:00:00; ready 2023-02-15 18:00:00; exact scheduled Open 2023-02-15 18:05:00. Направление LONG; status/reason **MODELLED / CONDITIONAL_OPEN_SCENARIO**.

ATR12 = сумма прошлых 12 TR / 12 = 0.790000000000 / 12 = **0.0658333333333**. VWAP = 572567.740000 / 7714 = **74.2244931294**; локальный anchor 2023-02-15 14:05:00; prior bars 45.

12 TR, исключая signal bar (2023-02-15 16:50:00 … 2023-02-15 17:45:00): `0.02, 0.04, 0.05, 0.19, 0.10, 0.06, 0.04, 0.04, 0.10, 0.05, 0.05, 0.05`.

Условие сигнала: **Close 74.36 > prior-12 edge 74.32; range [74.07, 74.32]**. ATR14 0.0565883510442; ADX14 17.7084743417; +DI/-DI 21.6001666140 / 17.9661034412. Архитектура ENTRY_MANAGEMENT определяет, используются ли эти контексты.

Initial Stop **74.28**, frozen Take **74.56**, cap **74.37**, dated tick 0.01. Swing последних 3 включая сигнал [74.26, 74.36].

Boundary entry check: scheduled end 2023-02-15 18:10:00 ≤ B−30 2023-02-15 18:20:00 = True; окно signal/entry совпадает True.

Stop raw ATR14 74.2751174734; structure 74.2917058245; дальний min = 74.2751174734, округление up к tick → 74.28.

Take raw 74.5575000000, округление up → 74.56; original cap raw Close+direction×0.25ATR12 = 74.3764583333.

Scheduled Open 74.34: signed risk 0.06, reward 0.22, direction×(Open−cap) -0.03 ≤0. Entry-quality ruler: risk≥4tick 0.04 = True; reward−2tick 0.20 ≥ risk+2tick 0.08 = True. Entry-quality ruler применяется только ENTRY/FULL/payable, не FROZEN_V2.

| Start MSK | Роль | O | H | L | C | V |
| --- | --- | --- | --- | --- | --- | --- |
| 2023-02-15 17:45:00 | previous, source row 5287 | 74.29 | 74.32 | 74.27 | 74.32 | 74 |
| 2023-02-15 17:50:00 | signal, source row 5288 | 74.32 | 74.36 | 74.32 | 74.36 | 258 |
| 2023-02-15 18:05:00 | delivered decision candle, source row 5291 | 74.34 | 74.48 | 74.34 | 74.48 | 600 |
| 2023-02-15 18:15:00 | delivered decision candle, source row 5293 | 74.4 | 74.4 | 74.34 | 74.37 | 507 |
| 2023-02-15 18:20:00 | EXIT, source row 5294 | 74.37 | 74.38 | 74.33 | 74.36 | 223 |

Решения и исполнения (сравнение с execution_events.csv.gz: MATCH):

- 2023-02-15 18:00:00: ENTRY_ORDER SUBMITTED, FIXED_SIGNAL; price null; ack —; flags —.
- 2023-02-15 18:05:00: ENTRY MODELLED, CONDITIONAL_OPEN_SCENARIO; price 74.34; ack 2023-02-15 18:15:00; flags —.
- 2023-02-15 18:15:00: STOP_AMEND_ORDER SUBMITTED, BE; price 74.36; ack —; flags —.
- 2023-02-15 18:25:00: EXIT_ORDER SUBMITTED, SESSION_FLAT; price null; ack —; flags —.
- 2023-02-15 18:20:00: STOP_AMENDMENT MODELLED, BE; price 74.36; ack 2023-02-15 18:30:00; flags —.
- 2023-02-15 18:20:00: EXIT MODELLED, BREAKEVEN_STOP; price 74.36; ack 2023-02-15 18:30:00; flags —.

BE: delivered Close progress 0.14/0.06 = 2.33333333333R; BE = entry + direction×2tick = 74.36; best delivered extreme 74.48, ATR14 0.0611860813572, trail raw 74.3576278373. Stop 74.36 decided 2023-02-15 18:15:00, effective 2023-02-15 18:20:00 > decision. Свечи до effective сохраняют прежнюю защиту.

Exit **74.36**, reason **BREAKEVEN_STOP**, interval [2023-02-15 18:20:00, 2023-02-15 18:25:00), ack 2023-02-15 18:30:00. Gross = 1×(74.36−74.34) = **0.02**; C1 = 0.01 + 0.01 = 0.02; Net = **0.00**; initial risk = |entry−initial stop| = 0.06; Net R = **0**. Flat deadline breach False. Oracle ↔ ledger: **MATCH**.

## 10. Momentum BREAKEVEN_STOP, SHORT

`MOMENTUM_USDRUBF / ENTRY_MANAGEMENT__NONE / C1_T10 / MOMENTUM_USDRUBF_000248`. Signal CSV строка **52043**; ledger строка **5277**.

Сигнал 2023-02-07 12:15:00, Close доступен 2023-02-07 12:25:00; ready 2023-02-07 12:25:00; exact scheduled Open 2023-02-07 12:30:00. Направление SHORT; status/reason **MODELLED / CONDITIONAL_OPEN_SCENARIO**.

ATR12 = сумма прошлых 12 TR / 12 = 0.400000000000 / 12 = **0.0333333333333**. VWAP = 200762.586667 / 2826 = **71.0412550130**; локальный anchor 2023-02-07 10:00:00; prior bars 27.

12 TR, исключая signal bar (2023-02-07 11:15:00 … 2023-02-07 12:10:00): `0.03, 0.01, 0.05, 0.07, 0.05, 0.03, 0.03, 0.01, 0.02, 0.02, 0.03, 0.05`.

Условие сигнала: **Close 70.99 < prior-12 edge 71.02; range [71.02, 71.12]**. ATR14 0.0392396588609; ADX14 21.1007142007; +DI/-DI 21.8339775565 / 25.2565826462. Архитектура ENTRY_MANAGEMENT определяет, используются ли эти контексты.

Initial Stop **71.04**, frozen Take **70.89**, cap **70.99**, dated tick 0.01. Swing последних 3 включая сигнал [70.99, 71.07].

Boundary entry check: scheduled end 2023-02-07 12:35:00 ≤ B−30 2023-02-07 13:30:00 = True; окно signal/entry совпадает True.

Stop raw ATR14 71.0488594883; structure 71.0396198294; дальний max = 71.0488594883, округление down к tick → 71.04.

Take raw 70.8900000000, округление down → 70.89; original cap raw Close+direction×0.25ATR12 = 70.9816666667.

Scheduled Open 71: signed risk 0.04, reward 0.11, direction×(Open−cap) -0.01 ≤0. Entry-quality ruler: risk≥4tick 0.04 = True; reward−2tick 0.09 ≥ risk+2tick 0.06 = True. Entry-quality ruler применяется только ENTRY/FULL/payable, не FROZEN_V2.

| Start MSK | Роль | O | H | L | C | V |
| --- | --- | --- | --- | --- | --- | --- |
| 2023-02-07 12:10:00 | previous, source row 4197 | 71.06 | 71.07 | 71.02 | 71.03 | 60 |
| 2023-02-07 12:15:00 | signal, source row 4198 | 71.04 | 71.04 | 70.99 | 70.99 | 145 |
| 2023-02-07 12:30:00 | scheduled entry, source row 4201 | 71 | 71 | 70.98 | 71 | 53 |
| 2023-02-07 12:50:00 | delivered decision candle, source row 4205 | 70.96 | 70.96 | 70.95 | 70.95 | 16 |
| 2023-02-07 13:00:00 | delivered decision candle, source row 4207 | 70.96 | 71 | 70.95 | 71 | 75 |
| 2023-02-07 13:05:00 | EXIT, source row 4208 | 71 | 71 | 71 | 71 | 5 |

Решения и исполнения (сравнение с execution_events.csv.gz: MATCH):

- 2023-02-07 12:25:00: ENTRY_ORDER SUBMITTED, FIXED_SIGNAL; price null; ack —; flags —.
- 2023-02-07 12:30:00: ENTRY MODELLED, CONDITIONAL_OPEN_SCENARIO; price 71; ack 2023-02-07 12:40:00; flags —.
- 2023-02-07 13:00:00: STOP_AMEND_ORDER SUBMITTED, BE; price 70.98; ack —; flags —.
- 2023-02-07 13:10:00: EXIT_ORDER SUBMITTED, MOMENTUM_NO_PROGRESS_30M; price null; ack —; flags —.
  Расчёт: delivered Close 71, signed Close−frozen edge/swing 0.02; age 30m, progress -0, 0.5 initialR 0.020.
- 2023-02-07 13:05:00: STOP_AMENDMENT MODELLED, BE; price 70.98; ack 2023-02-07 13:15:00; flags —.
- 2023-02-07 13:05:00: EXIT MODELLED, BREAKEVEN_STOP; price 71; ack 2023-02-07 13:15:00; flags ADVERSE_STOP_GAP.

BE: delivered Close progress 0.05/0.04 = 1.25R; BE = entry + direction×2tick = 70.98; best delivered extreme 70.95, ATR14 0.0359179838202, trail raw 71.0218359676. Stop 70.98 decided 2023-02-07 13:00:00, effective 2023-02-07 13:05:00 > decision. Свечи до effective сохраняют прежнюю защиту.

Exit **71**, reason **BREAKEVEN_STOP**, interval [2023-02-07 13:05:00, 2023-02-07 13:10:00), ack 2023-02-07 13:15:00. Gross = -1×(71−71) = **-0**; C1 = 0.01 + 0.01 = 0.02; Net = **-0.02**; initial risk = |entry−initial stop| = 0.04; Net R = **-0.5**. Flat deadline breach False. Oracle ↔ ledger: **MATCH**.

## 11. Momentum TRAIL_STOP, LONG

`MOMENTUM_USDRUBF / ENTRY_MANAGEMENT__NONE / C1_T10 / MOMENTUM_USDRUBF_000197`. Signal CSV строка **51992**; ledger строка **5274**.

Сигнал 2023-01-31 12:05:00, Close доступен 2023-01-31 12:15:00; ready 2023-01-31 12:15:00; exact scheduled Open 2023-01-31 12:20:00. Направление LONG; status/reason **MODELLED / CONDITIONAL_OPEN_SCENARIO**.

ATR12 = сумма прошлых 12 TR / 12 = 0.710000000000 / 12 = **0.0591666666667**. VWAP = 219980.116667 / 3121 = **70.4838566699**; локальный anchor 2023-01-31 10:00:00; prior bars 25.

12 TR, исключая signal bar (2023-01-31 11:05:00 … 2023-01-31 12:00:00): `0.03, 0.10, 0.06, 0.02, 0.05, 0.04, 0.06, 0.08, 0.08, 0.07, 0.04, 0.08`.

Условие сигнала: **Close 70.52 > prior-12 edge 70.51; range [70.32, 70.51]**. ATR14 0.0723438190929; ADX14 null; +DI/-DI 31.6744896706 / 23.0826034077. Архитектура ENTRY_MANAGEMENT определяет, используются ли эти контексты.

Initial Stop **70.42**, frozen Take **70.70**, cap **70.53**, dated tick 0.01. Swing последних 3 включая сигнал [70.39, 70.56].

Boundary entry check: scheduled end 2023-01-31 12:25:00 ≤ B−30 2023-01-31 13:30:00 = True; окно signal/entry совпадает True.

Stop raw ATR14 70.4114842714; structure 70.4738280905; дальний min = 70.4114842714, округление up к tick → 70.42.

Take raw 70.6975000000, округление up → 70.70; original cap raw Close+direction×0.25ATR12 = 70.5347916667.

Scheduled Open 70.53: signed risk 0.11, reward 0.17, direction×(Open−cap) 0.00 ≤0. Entry-quality ruler: risk≥4tick 0.04 = True; reward−2tick 0.15 ≥ risk+2tick 0.13 = True. Entry-quality ruler применяется только ENTRY/FULL/payable, не FROZEN_V2.

| Start MSK | Роль | O | H | L | C | V |
| --- | --- | --- | --- | --- | --- | --- |
| 2023-01-31 12:00:00 | previous, source row 3347 | 70.4 | 70.47 | 70.39 | 70.47 | 35 |
| 2023-01-31 12:05:00 | signal, source row 3348 | 70.47 | 70.56 | 70.46 | 70.52 | 314 |
| 2023-01-31 12:20:00 | scheduled entry, source row 3351 | 70.53 | 70.55 | 70.52 | 70.55 | 85 |
| 2023-01-31 12:25:00 | delivered decision candle, source row 3352 | 70.57 | 70.65 | 70.57 | 70.64 | 228 |
| 2023-01-31 12:40:00 | STOP_AMENDMENT, source row 3355 | 70.67 | 70.7 | 70.62 | 70.65 | 83 |
| 2023-01-31 13:00:00 | delivered decision candle, source row 3359 | 70.74 | 70.75 | 70.72 | 70.75 | 91 |
| 2023-01-31 13:15:00 | STOP_AMENDMENT, source row 3362 | 70.72 | 70.76 | 70.72 | 70.74 | 75 |
| 2023-01-31 13:20:00 | delivered decision candle, source row 3363 | 70.74 | 70.77 | 70.73 | 70.76 | 78 |
| 2023-01-31 13:25:00 | delivered decision candle, source row 3364 | 70.74 | 70.79 | 70.74 | 70.79 | 54 |
| 2023-01-31 13:35:00 | EXIT, source row 3366 | 70.71 | 70.71 | 70.66 | 70.67 | 92 |

Решения и исполнения (сравнение с execution_events.csv.gz: MATCH):

- 2023-01-31 12:15:00: ENTRY_ORDER SUBMITTED, FIXED_SIGNAL; price null; ack —; flags —.
- 2023-01-31 12:20:00: ENTRY MODELLED, CONDITIONAL_OPEN_SCENARIO; price 70.53; ack 2023-01-31 12:30:00; flags —.
- 2023-01-31 12:35:00: STOP_AMEND_ORDER SUBMITTED, BE; price 70.55; ack —; flags —.
- 2023-01-31 12:40:00: STOP_AMENDMENT MODELLED, BE; price 70.55; ack 2023-01-31 12:50:00; flags —.
- 2023-01-31 13:10:00: STOP_AMEND_ORDER SUBMITTED, TRAIL; price 70.64; ack —; flags —.
- 2023-01-31 13:15:00: STOP_AMENDMENT MODELLED, TRAIL; price 70.64; ack 2023-01-31 13:25:00; flags —.
- 2023-01-31 13:30:00: STOP_AMEND_ORDER SUBMITTED, TRAIL; price 70.67; ack —; flags —.
- 2023-01-31 13:35:00: EXIT_ORDER SUBMITTED, SESSION_FLAT; price null; ack —; flags —.
- 2023-01-31 13:35:00: STOP_AMENDMENT MODELLED, TRAIL; price 70.67; ack 2023-01-31 13:45:00; flags —.
- 2023-01-31 13:35:00: EXIT MODELLED, TRAIL_STOP; price 70.67; ack 2023-01-31 13:45:00; flags —.

BE: delivered Close progress 0.11/0.11 = 1R; BE = entry + direction×2tick = 70.55; best delivered extreme 70.65, ATR14 0.0682882605454, trail raw 70.5134234789. Stop 70.55 decided 2023-01-31 12:35:00, effective 2023-01-31 12:40:00 > decision. Свечи до effective сохраняют прежнюю защиту.

TRAIL: delivered Close progress 0.22/0.11 = 2R; BE = entry + direction×2tick = 70.55; best delivered extreme 70.75, ATR14 0.0590770280033, trail raw 70.6318459440. Stop 70.64 decided 2023-01-31 13:10:00, effective 2023-01-31 13:15:00 > decision. Свечи до effective сохраняют прежнюю защиту.

TRAIL: delivered Close progress 0.23/0.11 = 2.09090909091R; BE = entry + direction×2tick = 70.55; best delivered extreme 70.77, ATR14 0.0540951425656, trail raw 70.6618097149. Stop 70.67 decided 2023-01-31 13:30:00, effective 2023-01-31 13:35:00 > decision. Свечи до effective сохраняют прежнюю защиту.

Exit **70.67**, reason **TRAIL_STOP**, interval [2023-01-31 13:35:00, 2023-01-31 13:40:00), ack 2023-01-31 13:45:00. Gross = 1×(70.67−70.53) = **0.14**; C1 = 0.01 + 0.01 = 0.02; Net = **0.12**; initial risk = |entry−initial stop| = 0.11; Net R = **1.09090909091**. Flat deadline breach False. Oracle ↔ ledger: **MATCH**.

## 12. Momentum TRAIL_STOP, SHORT

`MOMENTUM_USDRUBF / ENTRY_MANAGEMENT__NONE / C1_T10 / MOMENTUM_USDRUBF_000759`. Signal CSV строка **52554**; ledger строка **5318**.

Сигнал 2023-04-21 11:15:00, Close доступен 2023-04-21 11:25:00; ready 2023-04-21 11:25:00; exact scheduled Open 2023-04-21 11:30:00. Направление SHORT; status/reason **MODELLED / CONDITIONAL_OPEN_SCENARIO**.

ATR12 = сумма прошлых 12 TR / 12 = 0.410000000000 / 12 = **0.0341666666667**. VWAP = 240090.576667 / 2941 = **81.6356942083**; локальный anchor 2023-04-21 10:00:00; prior bars 15.

12 TR, исключая signal bar (2023-04-21 10:15:00 … 2023-04-21 11:10:00): `0.04, 0.04, 0.05, 0.05, 0.00, 0.01, 0.01, 0.02, 0.03, 0.08, 0.02, 0.06`.

Условие сигнала: **Close 81.51 < prior-12 edge 81.53; range [81.53, 81.72]**. ATR14 0.0380612244898; ADX14 null; +DI/-DI 12.1983914209 / 31.6353887399. Архитектура ENTRY_MANAGEMENT определяет, используются ли эти контексты.

Initial Stop **81.56**, frozen Take **81.40**, cap **81.51**, dated tick 0.01. Swing последних 3 включая сигнал [81.51, 81.59].

Boundary entry check: scheduled end 2023-04-21 11:35:00 ≤ B−30 2023-04-21 13:30:00 = True; окно signal/entry совпадает True.

Stop raw ATR14 81.5670918367; structure 81.5490306122; дальний max = 81.5670918367, округление down к tick → 81.56.

Take raw 81.4075000000, округление down → 81.40; original cap raw Close+direction×0.25ATR12 = 81.5014583333.

Scheduled Open 81.51: signed risk 0.05, reward 0.11, direction×(Open−cap) -0.00 ≤0. Entry-quality ruler: risk≥4tick 0.04 = True; reward−2tick 0.09 ≥ risk+2tick 0.07 = True. Entry-quality ruler применяется только ENTRY/FULL/payable, не FROZEN_V2.

| Start MSK | Роль | O | H | L | C | V |
| --- | --- | --- | --- | --- | --- | --- |
| 2023-04-21 11:10:00 | previous, source row 12664 | 81.58 | 81.58 | 81.53 | 81.53 | 177 |
| 2023-04-21 11:15:00 | signal, source row 12665 | 81.56 | 81.56 | 81.51 | 81.51 | 346 |
| 2023-04-21 11:30:00 | scheduled entry, source row 12668 | 81.51 | 81.53 | 81.51 | 81.52 | 80 |
| 2023-04-21 11:50:00 | delivered decision candle, source row 12672 | 81.48 | 81.49 | 81.44 | 81.45 | 174 |
| 2023-04-21 12:00:00 | delivered decision candle, source row 12674 | 81.44 | 81.46 | 81.39 | 81.41 | 299 |
| 2023-04-21 12:05:00 | STOP_AMENDMENT, source row 12675 | 81.42 | 81.44 | 81.41 | 81.43 | 125 |
| 2023-04-21 12:15:00 | delivered decision candle, source row 12677 | 81.41 | 81.41 | 81.31 | 81.34 | 676 |
| 2023-04-21 12:20:00 | delivered decision candle, source row 12678 | 81.31 | 81.34 | 81.3 | 81.33 | 194 |
| 2023-04-21 12:25:00 | delivered decision candle, source row 12679 | 81.32 | 81.34 | 81.26 | 81.33 | 290 |
| 2023-04-21 12:30:00 | STOP_AMENDMENT, source row 12680 | 81.31 | 81.37 | 81.31 | 81.34 | 97 |
| 2023-04-21 12:35:00 | EXIT, source row 12681 | 81.37 | 81.38 | 81.35 | 81.36 | 70 |

Решения и исполнения (сравнение с execution_events.csv.gz: MATCH):

- 2023-04-21 11:25:00: ENTRY_ORDER SUBMITTED, FIXED_SIGNAL; price null; ack —; flags —.
- 2023-04-21 11:30:00: ENTRY MODELLED, CONDITIONAL_OPEN_SCENARIO; price 81.51; ack 2023-04-21 11:40:00; flags —.
- 2023-04-21 12:00:00: STOP_AMEND_ORDER SUBMITTED, BE; price 81.49; ack —; flags —.
- 2023-04-21 12:10:00: STOP_AMEND_ORDER SUBMITTED, TRAIL; price 81.46; ack —; flags —.
- 2023-04-21 12:05:00: STOP_AMENDMENT MODELLED, BE; price 81.49; ack 2023-04-21 12:15:00; flags —.
- 2023-04-21 12:15:00: STOP_AMENDMENT MODELLED, TRAIL; price 81.46; ack 2023-04-21 12:25:00; flags —.
- 2023-04-21 12:25:00: STOP_AMEND_ORDER SUBMITTED, TRAIL; price 81.39; ack —; flags —.
- 2023-04-21 12:30:00: STOP_AMEND_ORDER SUBMITTED, TRAIL; price 81.38; ack —; flags —.
- 2023-04-21 12:35:00: STOP_AMEND_ORDER SUBMITTED, TRAIL; price 81.35; ack —; flags —.
- 2023-04-21 12:30:00: STOP_AMENDMENT MODELLED, TRAIL; price 81.39; ack 2023-04-21 12:40:00; flags —.
- 2023-04-21 12:35:00: STOP_AMENDMENT MODELLED, TRAIL; price 81.38; ack 2023-04-21 12:45:00; flags —.
- 2023-04-21 12:35:00: EXIT MODELLED, TRAIL_STOP; price 81.38; ack 2023-04-21 12:45:00; flags —.

BE: delivered Close progress 0.06/0.05 = 1.2R; BE = entry + direction×2tick = 81.49; best delivered extreme 81.44, ATR14 0.0352067557866, trail raw 81.5104135116. Stop 81.49 decided 2023-04-21 12:00:00, effective 2023-04-21 12:05:00 > decision. Свечи до effective сохраняют прежнюю защиту.

TRAIL: delivered Close progress 0.10/0.05 = 2R; BE = entry + direction×2tick = 81.49; best delivered extreme 81.39, ATR14 0.0399997026936, trail raw 81.4699994054. Stop 81.46 decided 2023-04-21 12:10:00, effective 2023-04-21 12:15:00 > decision. Свечи до effective сохраняют прежнюю защиту.

TRAIL: delivered Close progress 0.17/0.05 = 3.4R; BE = entry + direction×2tick = 81.49; best delivered extreme 81.31, ATR14 0.0436695870327, trail raw 81.3973391741. Stop 81.39 decided 2023-04-21 12:25:00, effective 2023-04-21 12:30:00 > decision. Свечи до effective сохраняют прежнюю защиту.

TRAIL: delivered Close progress 0.18/0.05 = 3.6R; BE = entry + direction×2tick = 81.49; best delivered extreme 81.3, ATR14 0.0434074736732, trail raw 81.3868149473. Stop 81.38 decided 2023-04-21 12:30:00, effective 2023-04-21 12:35:00 > decision. Свечи до effective сохраняют прежнюю защиту.

TRAIL: delivered Close progress 0.18/0.05 = 3.6R; BE = entry + direction×2tick = 81.49; best delivered extreme 81.26, ATR14 0.0460212255537, trail raw 81.3520424511. Stop 81.35 decided 2023-04-21 12:35:00, effective 2023-04-21 12:40:00 > decision. Свечи до effective сохраняют прежнюю защиту.

Exit **81.38**, reason **TRAIL_STOP**, interval [2023-04-21 12:35:00, 2023-04-21 12:40:00), ack 2023-04-21 12:45:00. Gross = -1×(81.38−81.51) = **0.13**; C1 = 0.01 + 0.01 = 0.02; Net = **0.11**; initial risk = |entry−initial stop| = 0.05; Net R = **2.2**. Flat deadline breach False. Oracle ↔ ledger: **MATCH**.

## 13. FAILED_BREAKOUT

`MOMENTUM_USDRUBF / ENTRY_MANAGEMENT__NONE / C1_T10 / MOMENTUM_USDRUBF_000030`. Signal CSV строка **51825**; ledger строка **5263**.

Сигнал 2023-01-05 16:45:00, Close доступен 2023-01-05 16:55:00; ready 2023-01-05 16:55:00; exact scheduled Open 2023-01-05 17:00:00. Направление LONG; status/reason **MODELLED / CONDITIONAL_OPEN_SCENARIO**.

ATR12 = сумма прошлых 12 TR / 12 = 0.72 / 12 = **0.06**. VWAP = 105903.673333 / 1473 = **71.8965874632**; локальный anchor 2023-01-05 14:05:00; prior bars 32.

12 TR, исключая signal bar (2023-01-05 15:45:00 … 2023-01-05 16:40:00): `0.08, 0.05, 0.02, 0.05, 0.06, 0.06, 0.10, 0.07, 0.04, 0.11, 0.05, 0.03`.

Условие сигнала: **Close 71.98 > prior-12 edge 71.96; range [71.71, 71.96]**. ATR14 0.0593402118815; ADX14 14.5002119502; +DI/-DI 35.7087664773 / 18.4625919673. Архитектура ENTRY_MANAGEMENT определяет, используются ли эти контексты.

Initial Stop **71.90**, frozen Take **72.16**, cap **71.99**, dated tick 0.01. Swing последних 3 включая сигнал [71.89, 71.98].

Boundary entry check: scheduled end 2023-01-05 17:05:00 ≤ B−30 2023-01-05 18:20:00 = True; окно signal/entry совпадает True.

Stop raw ATR14 71.8909896822; structure 71.9303298941; дальний min = 71.8909896822, округление up к tick → 71.90.

Take raw 72.16, округление up → 72.16; original cap raw Close+direction×0.25ATR12 = 71.9950.

Scheduled Open 71.98: signed risk 0.08, reward 0.18, direction×(Open−cap) -0.01 ≤0. Entry-quality ruler: risk≥4tick 0.04 = True; reward−2tick 0.16 ≥ risk+2tick 0.10 = True. Entry-quality ruler применяется только ENTRY/FULL/payable, не FROZEN_V2.

| Start MSK | Роль | O | H | L | C | V |
| --- | --- | --- | --- | --- | --- | --- |
| 2023-01-05 16:40:00 | previous, source row 434 | 71.93 | 71.94 | 71.91 | 71.94 | 52 |
| 2023-01-05 16:45:00 | signal, source row 435 | 71.95 | 71.98 | 71.94 | 71.98 | 55 |
| 2023-01-05 17:00:00 | delivered decision candle, source row 438 | 71.98 | 71.99 | 71.96 | 71.96 | 44 |
| 2023-01-05 17:15:00 | EXIT, source row 441 | 72.01 | 72.01 | 71.96 | 71.96 | 60 |

Решения и исполнения (сравнение с execution_events.csv.gz: MATCH):

- 2023-01-05 16:55:00: ENTRY_ORDER SUBMITTED, FIXED_SIGNAL; price null; ack —; flags —.
- 2023-01-05 17:00:00: ENTRY MODELLED, CONDITIONAL_OPEN_SCENARIO; price 71.98; ack 2023-01-05 17:10:00; flags —.
- 2023-01-05 17:10:00: EXIT_ORDER SUBMITTED, FAILED_BREAKOUT; price null; ack —; flags —.
  Расчёт: delivered Close 71.96, signed Close−frozen edge/swing 0.00; age 0m, progress -0.02, 0.5 initialR 0.040.
- 2023-01-05 17:15:00: EXIT MODELLED, FAILED_BREAKOUT; price 72.01; ack 2023-01-05 17:25:00; flags —.

Exit **72.01**, reason **FAILED_BREAKOUT**, interval [2023-01-05 17:15:00, 2023-01-05 17:20:00), ack 2023-01-05 17:25:00. Gross = 1×(72.01−71.98) = **0.03**; C1 = 0.01 + 0.01 = 0.02; Net = **0.01**; initial risk = |entry−initial stop| = 0.08; Net R = **0.125**. Flat deadline breach False. Oracle ↔ ledger: **MATCH**.

## 14. MOMENTUM_NO_PROGRESS_30M

`MOMENTUM_USDRUBF / ENTRY_MANAGEMENT__NONE / C1_T10 / MOMENTUM_USDRUBF_000194`. Signal CSV строка **51989**; ledger строка **5273**.

Сигнал 2023-01-30 15:50:00, Close доступен 2023-01-30 16:00:00; ready 2023-01-30 16:00:00; exact scheduled Open 2023-01-30 16:05:00. Направление LONG; status/reason **MODELLED / CONDITIONAL_OPEN_SCENARIO**.

ATR12 = сумма прошлых 12 TR / 12 = 1.12000000000 / 12 = **0.0933333333333**. VWAP = 330739.580000 / 4728 = **69.9533798646**; локальный anchor 2023-01-30 14:05:00; prior bars 21.

12 TR, исключая signal bar (2023-01-30 14:50:00 … 2023-01-30 15:45:00): `0.03, 0.06, 0.19, 0.10, 0.08, 0.12, 0.06, 0.09, 0.12, 0.11, 0.06, 0.10`.

Условие сигнала: **Close 70.18 > prior-12 edge 70.14; range [69.83, 70.14]**. ATR14 0.0803826462581; ADX14 null; +DI/-DI 36.1300753121 / 11.1080078005. Архитектура ENTRY_MANAGEMENT определяет, используются ли эти контексты.

Initial Stop **70.06**, frozen Take **70.46**, cap **70.20**, dated tick 0.01. Swing последних 3 включая сигнал [70.04, 70.2].

Boundary entry check: scheduled end 2023-01-30 16:10:00 ≤ B−30 2023-01-30 18:20:00 = True; окно signal/entry совпадает True.

Stop raw ATR14 70.0594260306; structure 70.0998086769; дальний min = 70.0594260306, округление up к tick → 70.06.

Take raw 70.4600000000, округление up → 70.46; original cap raw Close+direction×0.25ATR12 = 70.2033333333.

Scheduled Open 70.19: signed risk 0.13, reward 0.27, direction×(Open−cap) -0.01 ≤0. Entry-quality ruler: risk≥4tick 0.04 = True; reward−2tick 0.25 ≥ risk+2tick 0.15 = True. Entry-quality ruler применяется только ENTRY/FULL/payable, не FROZEN_V2.

| Start MSK | Роль | O | H | L | C | V |
| --- | --- | --- | --- | --- | --- | --- |
| 2023-01-30 15:45:00 | previous, source row 3218 | 70.05 | 70.14 | 70.05 | 70.14 | 109 |
| 2023-01-30 15:50:00 | signal, source row 3219 | 70.14 | 70.2 | 70.14 | 70.18 | 287 |
| 2023-01-30 16:05:00 | scheduled entry, source row 3222 | 70.19 | 70.25 | 70.16 | 70.16 | 132 |
| 2023-01-30 16:35:00 | delivered decision candle, source row 3228 | 70.19 | 70.2 | 70.19 | 70.2 | 4 |
| 2023-01-30 16:50:00 | EXIT, source row 3231 | 70.18 | 70.18 | 70.11 | 70.16 | 105 |

Решения и исполнения (сравнение с execution_events.csv.gz: MATCH):

- 2023-01-30 16:00:00: ENTRY_ORDER SUBMITTED, FIXED_SIGNAL; price null; ack —; flags —.
- 2023-01-30 16:05:00: ENTRY MODELLED, CONDITIONAL_OPEN_SCENARIO; price 70.19; ack 2023-01-30 16:15:00; flags —.
- 2023-01-30 16:45:00: EXIT_ORDER SUBMITTED, MOMENTUM_NO_PROGRESS_30M; price null; ack —; flags —.
  Расчёт: delivered Close 70.2, signed Close−frozen edge/swing 0.06; age 30m, progress 0.01, 0.5 initialR 0.065.
- 2023-01-30 16:50:00: EXIT MODELLED, MOMENTUM_NO_PROGRESS_30M; price 70.18; ack 2023-01-30 17:00:00; flags —.

Exit **70.18**, reason **MOMENTUM_NO_PROGRESS_30M**, interval [2023-01-30 16:50:00, 2023-01-30 16:55:00), ack 2023-01-30 17:00:00. Gross = 1×(70.18−70.19) = **-0.01**; C1 = 0.01 + 0.01 = 0.02; Net = **-0.03**; initial risk = |entry−initial stop| = 0.13; Net R = **-0.230769230769**. Flat deadline breach False. Oracle ↔ ledger: **MATCH**.

## 15. VWAP_PREMISE_FAILED

`VWAP_MR_USDRUBF / PAYABLE_CAP_FULL_M5__NONE / C1_T10 / VWAP_MR_USDRUBF_000030`. Signal CSV строка **7351**; ledger строка **1130**.

Сигнал 2023-01-10 12:50:00, Close доступен 2023-01-10 13:00:00; ready 2023-01-10 13:00:00; exact scheduled Open 2023-01-10 13:05:00. Направление LONG; status/reason **MODELLED / CONDITIONAL_OPEN_SCENARIO**.

ATR12 = сумма прошлых 12 TR / 12 = 1.140 / 12 = **0.095**. VWAP = 460290.436667 / 6599 = **69.7515436682**; локальный anchor 2023-01-10 10:00:00; prior bars 34.

12 TR, исключая signal bar (2023-01-10 11:50:00 … 2023-01-10 12:45:00): `0.17, 0.06, 0.16, 0.14, 0.05, 0.10, 0.12, 0.05, 0.08, 0.03, 0.05, 0.13`.

Условие сигнала: **69.64 ≤ 69.6598120618; 69.6565436682 < 69.71 < 69.7515436682**. ATR14 0.0966475716640; ADX14 15.8947069304; +DI/-DI 19.8414553935 / 24.0417855895. Архитектура PAYABLE_CAP_FULL_M5 определяет, используются ли эти контексты.

Initial Stop **69.57**, frozen Take **69.76**, cap **69.64**, dated tick 0.01. Swing последних 3 включая сигнал [69.6, 69.76].

Boundary entry check: scheduled end 2023-01-10 13:10:00 ≤ B−30 2023-01-10 13:30:00 = True; окно signal/entry совпадает True.

Stop raw ATR14 69.5650286425; structure 69.59; дальний min = 69.5650286425, округление up к tick → 69.57.

Take raw 69.7515436682, округление up → 69.76; original cap raw Close+direction×0.25ATR12 = 69.73375.

DI aligned = False; ADX≥25 = False; Momentum требует обе проверки; MR блокирует только strong adverse DI.

Payable bound (Take + Stop − direction×4tick)/2 = 69.645; cap округлён в безопасную сторону. Risk(cap) 0.07; reward(cap)−2tick 0.10.

Scheduled Open 69.63: signed risk 0.06, reward 0.13, direction×(Open−cap) -0.01 ≤0. Entry-quality ruler: risk≥4tick 0.04 = True; reward−2tick 0.11 ≥ risk+2tick 0.08 = True. Entry-quality ruler применяется только ENTRY/FULL/payable, не FROZEN_V2.

| Start MSK | Роль | O | H | L | C | V |
| --- | --- | --- | --- | --- | --- | --- |
| 2023-01-10 12:45:00 | previous, source row 893 | 69.76 | 69.76 | 69.63 | 69.64 | 116 |
| 2023-01-10 12:50:00 | signal, source row 894 | 69.64 | 69.72 | 69.6 | 69.71 | 276 |
| 2023-01-10 13:05:00 | scheduled entry, source row 897 | 69.63 | 69.65 | 69.63 | 69.64 | 46 |
| 2023-01-10 13:20:00 | delivered decision candle, source row 900 | 69.65 | 69.65 | 69.58 | 69.58 | 43 |
| 2023-01-10 13:35:00 | EXIT, source row 903 | 69.59 | 69.59 | 69.59 | 69.59 | 21 |

Решения и исполнения (сравнение с execution_events.csv.gz: MATCH):

- 2023-01-10 13:00:00: ENTRY_ORDER SUBMITTED, FIXED_SIGNAL; price null; ack —; flags —.
- 2023-01-10 13:05:00: ENTRY MODELLED, CONDITIONAL_OPEN_SCENARIO; price 69.63; ack 2023-01-10 13:15:00; flags —.
- 2023-01-10 13:30:00: EXIT_ORDER SUBMITTED, VWAP_PREMISE_FAILED; price null; ack —; flags —.
  Расчёт: delivered Close 69.58, signed Close−frozen edge/swing -0.02; age 15m, progress -0.05, 0.5 initialR 0.030.
- 2023-01-10 13:35:00: EXIT MODELLED, VWAP_PREMISE_FAILED; price 69.59; ack 2023-01-10 13:45:00; flags —.

Exit **69.59**, reason **VWAP_PREMISE_FAILED**, interval [2023-01-10 13:35:00, 2023-01-10 13:40:00), ack 2023-01-10 13:45:00. Gross = 1×(69.59−69.63) = **-0.04**; C1 = 0.01 + 0.01 = 0.02; Net = **-0.06**; initial risk = |entry−initial stop| = 0.06; Net R = **-1**. Flat deadline breach False. Oracle ↔ ledger: **MATCH**.

## 16. VWAP_NO_PROGRESS_30M

`VWAP_MR_USDRUBF / PAYABLE_CAP_FULL_M5__NONE / C1_T10 / VWAP_MR_USDRUBF_000305`. Signal CSV строка **7626**; ledger строка **1134**.

Сигнал 2023-03-21 16:25:00, Close доступен 2023-03-21 16:35:00; ready 2023-03-21 16:35:00; exact scheduled Open 2023-03-21 16:40:00. Направление LONG; status/reason **MODELLED / CONDITIONAL_OPEN_SCENARIO**.

ATR12 = сумма прошлых 12 TR / 12 = 1.0500 / 12 = **0.0875**. VWAP = 245246.933333 / 3192 = **76.8317460317**; локальный anchor 2023-03-21 14:05:00; prior bars 28.

12 TR, исключая signal bar (2023-03-21 15:25:00 … 2023-03-21 16:20:00): `0.15, 0.07, 0.07, 0.03, 0.10, 0.17, 0.11, 0.12, 0.10, 0.07, 0.03, 0.03`.

Условие сигнала: **76.71 ≤ 76.7463744241; 76.7442460317 < 76.76 < 76.8317460317**. ATR14 0.0709395853344; ADX14 14.1774154237; +DI/-DI 22.2164449160 / 27.0937162552. Архитектура PAYABLE_CAP_FULL_M5 определяет, используются ли эти контексты.

Initial Stop **76.66**, frozen Take **76.84**, cap **76.73**, dated tick 0.01. Swing последних 3 включая сигнал [76.7, 76.78].

Boundary entry check: scheduled end 2023-03-21 16:45:00 ≤ B−30 2023-03-21 18:20:00 = True; окно signal/entry совпадает True.

Stop raw ATR14 76.6535906220; structure 76.69; дальний min = 76.6535906220, округление up к tick → 76.66.

Take raw 76.8317460317, округление up → 76.84; original cap raw Close+direction×0.25ATR12 = 76.781875.

DI aligned = False; ADX≥25 = False; Momentum требует обе проверки; MR блокирует только strong adverse DI.

Payable bound (Take + Stop − direction×4tick)/2 = 76.73; cap округлён в безопасную сторону. Risk(cap) 0.07; reward(cap)−2tick 0.09.

Scheduled Open 76.71: signed risk 0.05, reward 0.13, direction×(Open−cap) -0.02 ≤0. Entry-quality ruler: risk≥4tick 0.04 = True; reward−2tick 0.11 ≥ risk+2tick 0.07 = True. Entry-quality ruler применяется только ENTRY/FULL/payable, не FROZEN_V2.

| Start MSK | Роль | O | H | L | C | V |
| --- | --- | --- | --- | --- | --- | --- |
| 2023-03-21 16:20:00 | previous, source row 8917 | 76.72 | 76.73 | 76.7 | 76.71 | 83 |
| 2023-03-21 16:25:00 | signal, source row 8918 | 76.72 | 76.78 | 76.71 | 76.76 | 81 |
| 2023-03-21 16:40:00 | scheduled entry, source row 8921 | 76.71 | 76.73 | 76.7 | 76.72 | 79 |
| 2023-03-21 17:15:00 | delivered decision candle, source row 8928 | 76.76 | 76.76 | 76.71 | 76.71 | 53 |
| 2023-03-21 17:30:00 | EXIT, source row 8931 | 76.71 | 76.79 | 76.7 | 76.77 | 334 |

Решения и исполнения (сравнение с execution_events.csv.gz: MATCH):

- 2023-03-21 16:35:00: ENTRY_ORDER SUBMITTED, FIXED_SIGNAL; price null; ack —; flags —.
- 2023-03-21 16:40:00: ENTRY MODELLED, CONDITIONAL_OPEN_SCENARIO; price 76.71; ack 2023-03-21 16:50:00; flags —.
- 2023-03-21 17:25:00: EXIT_ORDER SUBMITTED, VWAP_NO_PROGRESS_30M; price null; ack —; flags —.
  Расчёт: delivered Close 76.71, signed Close−frozen edge/swing 0.01; age 35m, progress 0.00, 0.5 initialR 0.025.
- 2023-03-21 17:30:00: EXIT MODELLED, VWAP_NO_PROGRESS_30M; price 76.71; ack 2023-03-21 17:40:00; flags —.

Exit **76.71**, reason **VWAP_NO_PROGRESS_30M**, interval [2023-03-21 17:30:00, 2023-03-21 17:35:00), ack 2023-03-21 17:40:00. Gross = 1×(76.71−76.71) = **0.00**; C1 = 0.01 + 0.01 = 0.02; Net = **-0.02**; initial risk = |entry−initial stop| = 0.05; Net R = **-0.4**. Flat deadline breach False. Oracle ↔ ledger: **MATCH**.

## 17. MAX_HOLD

`VWAP_MR_USDRUBF / FROZEN_V2__NONE / C1_T10 / VWAP_MR_USDRUBF_000020`. Signal CSV строка **21**; ledger строка **8**.

Сигнал 2023-01-06 11:30:00, Close доступен 2023-01-06 11:40:00; ready 2023-01-06 11:40:00; exact scheduled Open 2023-01-06 11:45:00. Направление LONG; status/reason **MODELLED / CONDITIONAL_OPEN_SCENARIO**.

ATR12 = сумма прошлых 12 TR / 12 = 1.44 / 12 = **0.12**. VWAP = 261832.913333 / 3645 = **71.8334467307**; локальный anchor 2023-01-06 10:00:00; prior bars 18.

12 TR, исключая signal bar (2023-01-06 10:30:00 … 2023-01-06 11:25:00): `0.13, 0.14, 0.18, 0.12, 0.07, 0.11, 0.16, 0.07, 0.08, 0.09, 0.19, 0.10`.

Условие сигнала: **71.71 ≤ 71.7166469205; 71.7134467307 < 71.75 < 71.8334467307**. ATR14 0.122843476676; ADX14 null; +DI/-DI 12.1922402270 / 30.8592776219. Архитектура FROZEN_V2 определяет, используются ли эти контексты.

Initial Stop **71.57**, frozen Take **71.84**, cap **71.78**, dated tick 0.01. Swing последних 3 включая сигнал [71.51, 71.75].

Boundary entry check: scheduled end 2023-01-06 11:50:00 ≤ B−30 2023-01-06 13:30:00 = True; окно signal/entry совпадает True.

Stop raw Close−direction×1.5ATR12 = 71.570, округление up → 71.57.

Take raw 71.8334467307, округление up → 71.84; original cap raw Close+direction×0.25ATR12 = 71.7800.

Scheduled Open 71.68: signed risk 0.11, reward 0.16, direction×(Open−cap) -0.10 ≤0. Entry-quality ruler: risk≥4tick 0.04 = True; reward−2tick 0.14 ≥ risk+2tick 0.13 = True. Entry-quality ruler применяется только ENTRY/FULL/payable, не FROZEN_V2.

| Start MSK | Роль | O | H | L | C | V |
| --- | --- | --- | --- | --- | --- | --- |
| 2023-01-06 11:25:00 | previous, source row 542 | 71.71 | 71.75 | 71.65 | 71.71 | 81 |
| 2023-01-06 11:30:00 | signal, source row 543 | 71.7 | 71.75 | 71.66 | 71.75 | 100 |
| 2023-01-06 11:45:00 | scheduled entry, source row 546 | 71.68 | 71.7 | 71.65 | 71.67 | 291 |
| 2023-01-06 12:30:00 | delivered decision candle, source row 555 | 71.69 | 71.69 | 71.59 | 71.63 | 262 |
| 2023-01-06 12:45:00 | EXIT, source row 558 | 71.72 | 71.76 | 71.7 | 71.75 | 33 |

Решения и исполнения (сравнение с execution_events.csv.gz: MATCH):

- 2023-01-06 11:40:00: ENTRY_ORDER SUBMITTED, FIXED_SIGNAL; price null; ack —; flags —.
- 2023-01-06 11:45:00: ENTRY MODELLED, CONDITIONAL_OPEN_SCENARIO; price 71.68; ack 2023-01-06 11:55:00; flags —.
- 2023-01-06 12:40:00: EXIT_ORDER SUBMITTED, MAX_HOLD; price null; ack —; flags —.
- 2023-01-06 12:45:00: EXIT MODELLED, MAX_HOLD; price 71.72; ack 2023-01-06 12:55:00; flags —.

Exit **71.72**, reason **MAX_HOLD**, interval [2023-01-06 12:45:00, 2023-01-06 12:50:00), ack 2023-01-06 12:55:00. Gross = 1×(71.72−71.68) = **0.04**; C1 = 0.01 + 0.01 = 0.02; Net = **0.02**; initial risk = |entry−initial stop| = 0.11; Net R = **0.181818181818**. Flat deadline breach False. Oracle ↔ ledger: **MATCH**.

## 18. SESSION_FLAT

`VWAP_MR_USDRUBF / FROZEN_V2__NONE / C1_T10 / VWAP_MR_USDRUBF_000030`. Signal CSV строка **31**; ledger строка **11**.

Сигнал 2023-01-10 12:50:00, Close доступен 2023-01-10 13:00:00; ready 2023-01-10 13:00:00; exact scheduled Open 2023-01-10 13:05:00. Направление LONG; status/reason **MODELLED / CONDITIONAL_OPEN_SCENARIO**.

ATR12 = сумма прошлых 12 TR / 12 = 1.140 / 12 = **0.095**. VWAP = 460290.436667 / 6599 = **69.7515436682**; локальный anchor 2023-01-10 10:00:00; prior bars 34.

12 TR, исключая signal bar (2023-01-10 11:50:00 … 2023-01-10 12:45:00): `0.17, 0.06, 0.16, 0.14, 0.05, 0.10, 0.12, 0.05, 0.08, 0.03, 0.05, 0.13`.

Условие сигнала: **69.64 ≤ 69.6598120618; 69.6565436682 < 69.71 < 69.7515436682**. ATR14 0.0966475716640; ADX14 15.8947069304; +DI/-DI 19.8414553935 / 24.0417855895. Архитектура FROZEN_V2 определяет, используются ли эти контексты.

Initial Stop **69.57**, frozen Take **69.76**, cap **69.73**, dated tick 0.01. Swing последних 3 включая сигнал [69.6, 69.76].

Boundary entry check: scheduled end 2023-01-10 13:10:00 ≤ B−30 2023-01-10 13:30:00 = True; окно signal/entry совпадает True.

Stop raw Close−direction×1.5ATR12 = 69.5675, округление up → 69.57.

Take raw 69.7515436682, округление up → 69.76; original cap raw Close+direction×0.25ATR12 = 69.73375.

Scheduled Open 69.63: signed risk 0.06, reward 0.13, direction×(Open−cap) -0.10 ≤0. Entry-quality ruler: risk≥4tick 0.04 = True; reward−2tick 0.11 ≥ risk+2tick 0.08 = True. Entry-quality ruler применяется только ENTRY/FULL/payable, не FROZEN_V2.

| Start MSK | Роль | O | H | L | C | V |
| --- | --- | --- | --- | --- | --- | --- |
| 2023-01-10 12:45:00 | previous, source row 893 | 69.76 | 69.76 | 69.63 | 69.64 | 116 |
| 2023-01-10 12:50:00 | signal, source row 894 | 69.64 | 69.72 | 69.6 | 69.71 | 276 |
| 2023-01-10 13:05:00 | scheduled entry, source row 897 | 69.63 | 69.65 | 69.63 | 69.64 | 46 |
| 2023-01-10 13:25:00 | delivered decision candle, source row 901 | 69.59 | 69.7 | 69.58 | 69.62 | 304 |
| 2023-01-10 13:40:00 | EXIT, source row 904 | 69.59 | 69.63 | 69.57 | 69.63 | 30 |

Решения и исполнения (сравнение с execution_events.csv.gz: MATCH):

- 2023-01-10 13:00:00: ENTRY_ORDER SUBMITTED, FIXED_SIGNAL; price null; ack —; flags —.
- 2023-01-10 13:05:00: ENTRY MODELLED, CONDITIONAL_OPEN_SCENARIO; price 69.63; ack 2023-01-10 13:15:00; flags —.
- 2023-01-10 13:35:00: EXIT_ORDER SUBMITTED, SESSION_FLAT; price null; ack —; flags —.
- 2023-01-10 13:40:00: EXIT MODELLED, SESSION_FLAT; price 69.59; ack 2023-01-10 13:50:00; flags —.

Exit **69.59**, reason **SESSION_FLAT**, interval [2023-01-10 13:40:00, 2023-01-10 13:45:00), ack 2023-01-10 13:50:00. Gross = 1×(69.59−69.63) = **-0.04**; C1 = 0.01 + 0.01 = 0.02; Net = **-0.06**; initial risk = |entry−initial stop| = 0.06; Net R = **-1**. Flat deadline breach False. Oracle ↔ ledger: **MATCH**.

## 19. Stop-first при Stop/Take в одной свече

`VWAP_MR_GLDRUBF / FROZEN_V2__NONE / C1_T10 / VWAP_MR_GLDRUBF_000092`. Signal CSV строка **39989**; ledger строка **3673**.

Сигнал 2023-09-06 11:15:00, Close доступен 2023-09-06 11:25:00; ready 2023-09-06 11:25:00; exact scheduled Open 2023-09-06 11:30:00. Направление LONG; status/reason **MODELLED / CONDITIONAL_OPEN_SCENARIO**.

ATR12 = сумма прошлых 12 TR / 12 = 71.9000000000 / 12 = **5.99166666667**. VWAP = 9326598.63333 / 1539 = **6060.16805285**; локальный anchor 2023-09-06 10:00:00; prior bars 15.

12 TR, исключая signal bar (2023-09-06 10:15:00 … 2023-09-06 11:10:00): `13.3, 0.2, 3.5, 7, 4.3, 14.5, 4.3, 9.8, 2.0, 3.2, 4.9, 4.9`.

Условие сигнала: **6051 ≤ 6054.50985280; 6054.17638618 < 6060 < 6060.16805285**. ATR14 6.49081632653; ADX14 null; +DI/-DI 38.8067913850 / 22.5829272127. Архитектура FROZEN_V2 определяет, используются ли эти контексты.

Initial Stop **6051.1**, frozen Take **6060.2**, cap **6061.4**, dated tick 0.1. Swing последних 3 включая сигнал [6050.1, 6060].

Boundary entry check: scheduled end 2023-09-06 11:35:00 ≤ B−30 2023-09-06 13:30:00 = True; окно signal/entry совпадает True.

Stop raw Close−direction×1.5ATR12 = 6051.01250000, округление up → 6051.1.

Take raw 6060.16805285, округление up → 6060.2; original cap raw Close+direction×0.25ATR12 = 6061.49791667.

Scheduled Open 6060: signed risk 8.9, reward 0.2, direction×(Open−cap) -1.4 ≤0. Entry-quality ruler: risk≥4tick 0.4 = True; reward−2tick 0.0 ≥ risk+2tick 9.1 = False. Entry-quality ruler применяется только ENTRY/FULL/payable, не FROZEN_V2.

| Start MSK | Роль | O | H | L | C | V |
| --- | --- | --- | --- | --- | --- | --- |
| 2023-09-06 11:10:00 | previous, source row 5890 | 6055.1 | 6055.1 | 6050.8 | 6051 | 85 |
| 2023-09-06 11:15:00 | signal, source row 5891 | 6052.1 | 6060 | 6050.1 | 6060 | 135 |
| 2023-09-06 11:30:00 | scheduled entry, source row 5894 | 6060 | 6060 | 6060 | 6060 | 54 |
| 2023-09-06 11:40:00 | EXIT, source row 5896 | 6060 | 6060.6 | 6050.9 | 6060 | 254 |

Решения и исполнения (сравнение с execution_events.csv.gz: MATCH):

- 2023-09-06 11:25:00: ENTRY_ORDER SUBMITTED, FIXED_SIGNAL; price null; ack —; flags —.
- 2023-09-06 11:30:00: ENTRY MODELLED, CONDITIONAL_OPEN_SCENARIO; price 6060; ack 2023-09-06 11:40:00; flags —.
- 2023-09-06 11:40:00: EXIT MODELLED, STOP; price 6051.1; ack 2023-09-06 11:50:00; flags AMBIGUOUS_STOP_TP.

Exit **6051.1**, reason **STOP**, interval [2023-09-06 11:40:00, 2023-09-06 11:45:00), ack 2023-09-06 11:50:00. Gross = 1×(6051.1−6060) = **-8.9**; C1 = 0.1 + 0.1 = 0.2; Net = **-9.1**; initial risk = |entry−initial stop| = 8.9; Net R = **-1.02247191011**. Flat deadline breach False. Oracle ↔ ledger: **MATCH**.

## 20. Stop на свече входа

`VWAP_MR_USDRUBF / FROZEN_V2__NONE / C1_T10 / VWAP_MR_USDRUBF_000016`. Signal CSV строка **17**; ledger строка **7**.

Сигнал 2023-01-05 17:15:00, Close доступен 2023-01-05 17:25:00; ready 2023-01-05 17:25:00; exact scheduled Open 2023-01-05 17:30:00. Направление SHORT; status/reason **MODELLED / CONDITIONAL_OPEN_SCENARIO**.

ATR12 = сумма прошлых 12 TR / 12 = 0.620000000000 / 12 = **0.0516666666667**. VWAP = 123470.876667 / 1717 = **71.9108192584**; локальный anchor 2023-01-05 14:05:00; prior bars 38.

12 TR, исключая signal bar (2023-01-05 16:15:00 … 2023-01-05 17:10:00): `0.10, 0.07, 0.04, 0.11, 0.05, 0.03, 0.04, 0.02, 0.02, 0.03, 0.04, 0.07`.

Условие сигнала: **72.04 ≥ 71.9601015892; 71.9108192584 < 71.96 < 71.9624859251**. ATR14 0.0546247589190; ADX14 20.5136466807; +DI/-DI 35.1491370590 / 18.5442156986. Архитектура FROZEN_V2 определяет, используются ли эти контексты.

Initial Stop **72.03**, frozen Take **71.91**, cap **71.95**, dated tick 0.01. Swing последних 3 включая сигнал [71.95, 72.05].

Boundary entry check: scheduled end 2023-01-05 17:35:00 ≤ B−30 2023-01-05 18:20:00 = True; окно signal/entry совпадает True.

Stop raw Close−direction×1.5ATR12 = 72.0375000000, округление down → 72.03.

Take raw 71.9108192584, округление down → 71.91; original cap raw Close+direction×0.25ATR12 = 71.9470833333.

Scheduled Open 71.99: signed risk 0.04, reward 0.08, direction×(Open−cap) -0.04 ≤0. Entry-quality ruler: risk≥4tick 0.04 = True; reward−2tick 0.06 ≥ risk+2tick 0.06 = True. Entry-quality ruler применяется только ENTRY/FULL/payable, не FROZEN_V2.

| Start MSK | Роль | O | H | L | C | V |
| --- | --- | --- | --- | --- | --- | --- |
| 2023-01-05 17:10:00 | previous, source row 440 | 71.98 | 72.05 | 71.98 | 72.04 | 114 |
| 2023-01-05 17:15:00 | signal, source row 441 | 72.01 | 72.01 | 71.96 | 71.96 | 60 |
| 2023-01-05 17:30:00 | EXIT, source row 444 | 71.99 | 72.1 | 71.99 | 72.08 | 176 |

Решения и исполнения (сравнение с execution_events.csv.gz: MATCH):

- 2023-01-05 17:25:00: ENTRY_ORDER SUBMITTED, FIXED_SIGNAL; price null; ack —; flags —.
- 2023-01-05 17:30:00: ENTRY MODELLED, CONDITIONAL_OPEN_SCENARIO; price 71.99; ack 2023-01-05 17:40:00; flags —.
- 2023-01-05 17:30:00: EXIT MODELLED, STOP; price 72.03; ack 2023-01-05 17:40:00; flags AMBIGUOUS_ENTRY_EXIT.

Exit **72.03**, reason **STOP**, interval [2023-01-05 17:30:00, 2023-01-05 17:35:00), ack 2023-01-05 17:40:00. Gross = -1×(72.03−71.99) = **-0.04**; C1 = 0.01 + 0.01 = 0.02; Net = **-0.06**; initial risk = |entry−initial stop| = 0.04; Net R = **-1.5**. Flat deadline breach False. Oracle ↔ ledger: **MATCH**.

## 21. Stop: худший Open при гэпе

`VWAP_MR_USDRUBF / FROZEN_V2__NONE / C1_T10 / VWAP_MR_USDRUBF_000260`. Signal CSV строка **261**; ledger строка **89**.

Сигнал 2023-03-10 15:35:00, Close доступен 2023-03-10 15:45:00; ready 2023-03-10 15:45:00; exact scheduled Open 2023-03-10 15:50:00. Направление SHORT; status/reason **MODELLED / CONDITIONAL_OPEN_SCENARIO**.

ATR12 = сумма прошлых 12 TR / 12 = 0.3900 / 12 = **0.0325**. VWAP = 172594.093333 / 2270 = **76.0326402349**; локальный anchor 2023-03-10 14:05:00; prior bars 18.

12 TR, исключая signal bar (2023-03-10 14:35:00 … 2023-03-10 15:30:00): `0.04, 0.04, 0.07, 0.03, 0.04, 0.02, 0.02, 0.02, 0.02, 0.01, 0.04, 0.04`.

Условие сигнала: **76.08 ≥ 76.0640107034; 76.0326402349 < 76.06 < 76.0651402349**. ATR14 0.0319117406438; ADX14 null; +DI/-DI 23.5255696881 / 21.1177598191. Архитектура FROZEN_V2 определяет, используются ли эти контексты.

Initial Stop **76.10**, frozen Take **76.03**, cap **76.06**, dated tick 0.01. Swing последних 3 включая сигнал [76.04, 76.1].

Boundary entry check: scheduled end 2023-03-10 15:55:00 ≤ B−30 2023-03-10 18:20:00 = True; окно signal/entry совпадает True.

Stop raw Close−direction×1.5ATR12 = 76.10875, округление down → 76.10.

Take raw 76.0326402349, округление down → 76.03; original cap raw Close+direction×0.25ATR12 = 76.051875.

Scheduled Open 76.06: signed risk 0.04, reward 0.03, direction×(Open−cap) -0.00 ≤0. Entry-quality ruler: risk≥4tick 0.04 = True; reward−2tick 0.01 ≥ risk+2tick 0.06 = False. Entry-quality ruler применяется только ENTRY/FULL/payable, не FROZEN_V2.

| Start MSK | Роль | O | H | L | C | V |
| --- | --- | --- | --- | --- | --- | --- |
| 2023-03-10 15:30:00 | previous, source row 7759 | 76.08 | 76.1 | 76.06 | 76.08 | 293 |
| 2023-03-10 15:35:00 | signal, source row 7760 | 76.08 | 76.08 | 76.04 | 76.06 | 90 |
| 2023-03-10 15:50:00 | scheduled entry, source row 7763 | 76.06 | 76.06 | 76.01 | 76.01 | 197 |
| 2023-03-10 15:55:00 | TP, source row 7764 | 76.03 | 76.05 | 76.03 | 76.05 | 20 |
| 2023-03-10 16:00:00 | TP, source row 7765 | 76.04 | 76.04 | 76.03 | 76.04 | 11 |
| 2023-03-10 16:15:00 | EXIT, source row 7768 | 76.1 | 76.1 | 76.06 | 76.06 | 216 |

Решения и исполнения (сравнение с execution_events.csv.gz: MATCH):

- 2023-03-10 15:45:00: ENTRY_ORDER SUBMITTED, FIXED_SIGNAL; price null; ack —; flags —.
- 2023-03-10 15:50:00: ENTRY MODELLED, CONDITIONAL_OPEN_SCENARIO; price 76.06; ack 2023-03-10 16:00:00; flags —.
- 2023-03-10 15:55:00: TP NONFILL, TOUCH_WITHOUT_TICK_PENETRATION; price null; ack 2023-03-10 16:05:00; flags —.
- 2023-03-10 16:00:00: TP NONFILL, TOUCH_WITHOUT_TICK_PENETRATION; price null; ack 2023-03-10 16:10:00; flags —.
- 2023-03-10 16:15:00: EXIT MODELLED, STOP; price 76.1; ack 2023-03-10 16:25:00; flags ADVERSE_STOP_GAP.

Exit **76.1**, reason **STOP**, interval [2023-03-10 16:15:00, 2023-03-10 16:20:00), ack 2023-03-10 16:25:00. Gross = -1×(76.1−76.06) = **-0.04**; C1 = 0.01 + 0.01 = 0.02; Net = **-0.06**; initial risk = |entry−initial stop| = 0.04; Net R = **-1.5**. Flat deadline breach False. Oracle ↔ ledger: **MATCH**.

## 22. Неизвестный путь: цена и P&L null

`VWAP_MR_USDRUBF / FROZEN_V2__NONE / C1_T10 / VWAP_MR_USDRUBF_000124`. Signal CSV строка **125**; ledger строка **44**.

Сигнал 2023-02-01 15:50:00, Close доступен 2023-02-01 16:00:00; ready 2023-02-01 16:00:00; exact scheduled Open 2023-02-01 16:05:00. Направление SHORT; status/reason **MODELLED / CONDITIONAL_OPEN_SCENARIO**.

ATR12 = сумма прошлых 12 TR / 12 = 0.84 / 12 = **0.07**. VWAP = 159172.443333 / 2271 = **70.0891428152**; локальный anchor 2023-02-01 14:05:00; prior bars 21.

12 TR, исключая signal bar (2023-02-01 14:50:00 … 2023-02-01 15:45:00): `0.06, 0.04, 0.08, 0.03, 0.09, 0.08, 0.15, 0.05, 0.03, 0.07, 0.07, 0.09`.

Условие сигнала: **70.17 ≥ 70.1589002217; 70.0891428152 < 70.09 < 70.1591428152**. ATR14 0.0799747175656; ADX14 null; +DI/-DI 24.0332786307 / 6.45467875224. Архитектура FROZEN_V2 определяет, используются ли эти контексты.

Initial Stop **70.19**, frozen Take **70.08**, cap **70.08**, dated tick 0.01. Swing последних 3 включая сигнал [70.08, 70.19].

Boundary entry check: scheduled end 2023-02-01 16:10:00 ≤ B−30 2023-02-01 18:20:00 = True; окно signal/entry совпадает True.

Stop raw Close−direction×1.5ATR12 = 70.195, округление down → 70.19.

Take raw 70.0891428152, округление down → 70.08; original cap raw Close+direction×0.25ATR12 = 70.0725.

Scheduled Open 70.09: signed risk 0.10, reward 0.01, direction×(Open−cap) -0.01 ≤0. Entry-quality ruler: risk≥4tick 0.04 = True; reward−2tick -0.01 ≥ risk+2tick 0.12 = False. Entry-quality ruler применяется только ENTRY/FULL/payable, не FROZEN_V2.

| Start MSK | Роль | O | H | L | C | V |
| --- | --- | --- | --- | --- | --- | --- |
| 2023-02-01 15:45:00 | previous, source row 3562 | 70.11 | 70.17 | 70.1 | 70.17 | 17 |
| 2023-02-01 15:50:00 | signal, source row 3563 | 70.17 | 70.19 | 70.09 | 70.09 | 16 |
| 2023-02-01 16:05:00 | scheduled entry, source row 3566 | 70.09 | 70.15 | 70.09 | 70.15 | 44 |
| 2023-02-01 16:20:00 | delivered decision candle, source row missing | missing | missing | missing | missing | missing |
| 2023-02-01 16:35:00 | MODEL_FLAT_CONFIRMATION, source row 3571 | 70.1 | 70.14 | 70.1 | 70.14 | 99 |

Решения и исполнения (сравнение с execution_events.csv.gz: MATCH):

- 2023-02-01 16:00:00: ENTRY_ORDER SUBMITTED, FIXED_SIGNAL; price null; ack —; flags —.
- 2023-02-01 16:05:00: ENTRY MODELLED, CONDITIONAL_OPEN_SCENARIO; price 70.09; ack 2023-02-01 16:15:00; flags —.
- 2023-02-01 16:20:00: POSITION_PATH UNRESOLVED, MISSING_BAR_STOP_TAKE_OR_EXPOSURE_OUTCOME_UNKNOWN; price null; ack 2023-02-01 16:30:00; flags —.
- 2023-02-01 16:30:00: EXIT_ORDER SUBMITTED, DATA_GAP_EMERGENCY; price null; ack —; flags —.
- 2023-02-01 16:35:00: MODEL_FLAT_CONFIRMATION CONDITIONAL_MODEL_FLAT, REDUCE_ALL_POSSIBLE_EXPOSURE_BRANCHES_NOT_A_KNOWN_TRADE_EXIT; price null; ack 2023-02-01 16:45:00; flags —.

Путь неизвестен: MISSING_PATH_EMERGENCY_OBLIGATIONS_UNRESOLVED. Conditional model flat 2023-02-01 16:35:00, ack 2023-02-01 16:45:00; **exit / Gross / exit C1 / total C1 / Net / R = null**. Entry C1 известен отдельно.

## 23. T15: позднее подтверждение session flat

`VWAP_MR_USDRUBF / FROZEN_V2__NONE / C1_T15_DELAY / VWAP_MR_USDRUBF_000134`. Signal CSV строка **11847**; ledger строка **1251**.

Сигнал 2023-02-03 13:00:00, Close доступен 2023-02-03 13:15:00; ready 2023-02-03 13:15:00; exact scheduled Open 2023-02-03 13:20:00. Направление LONG; status/reason **MODELLED / CONDITIONAL_OPEN_SCENARIO**.

ATR12 = сумма прошлых 12 TR / 12 = 0.5100 / 12 = **0.0425**. VWAP = 402728.330000 / 5716 = **70.4563208537**; локальный anchor 2023-02-03 10:00:00; prior bars 36.

12 TR, исключая signal bar (2023-02-03 12:00:00 … 2023-02-03 12:55:00): `0.05, 0.05, 0.05, 0.06, 0.04, 0.05, 0.04, 0.09, 0.03, 0.02, 0.01, 0.02`.

Условие сигнала: **70.41 ≤ 70.4139531040; 70.4138208537 < 70.42 < 70.4563208537**. ATR14 0.0392109437688; ADX14 14.3916925391; +DI/-DI 24.3148284928 / 26.2022873809. Архитектура FROZEN_V2 определяет, используются ли эти контексты.

Initial Stop **70.36**, frozen Take **70.46**, cap **70.43**, dated tick 0.01. Swing последних 3 включая сигнал [70.41, 70.44].

Boundary entry check: scheduled end 2023-02-03 13:25:00 ≤ B−30 2023-02-03 13:30:00 = True; окно signal/entry совпадает True.

Stop raw Close−direction×1.5ATR12 = 70.35625, округление up → 70.36.

Take raw 70.4563208537, округление up → 70.46; original cap raw Close+direction×0.25ATR12 = 70.430625.

Scheduled Open 70.4: signed risk 0.04, reward 0.06, direction×(Open−cap) -0.03 ≤0. Entry-quality ruler: risk≥4tick 0.04 = True; reward−2tick 0.04 ≥ risk+2tick 0.06 = False. Entry-quality ruler применяется только ENTRY/FULL/payable, не FROZEN_V2.

| Start MSK | Роль | O | H | L | C | V |
| --- | --- | --- | --- | --- | --- | --- |
| 2023-02-03 12:55:00 | previous, source row 3871 | 70.42 | 70.42 | 70.41 | 70.41 | 44 |
| 2023-02-03 13:00:00 | signal, source row 3872 | 70.41 | 70.42 | 70.41 | 70.42 | 19 |
| 2023-02-03 13:20:00 | delivered decision candle, source row 3876 | 70.4 | 70.43 | 70.38 | 70.38 | 258 |
| 2023-02-03 13:40:00 | EXIT, source row 3880 | 70.42 | 70.43 | 70.41 | 70.43 | 34 |

Решения и исполнения (сравнение с execution_events.csv.gz: MATCH):

- 2023-02-03 13:15:00: ENTRY_ORDER SUBMITTED, FIXED_SIGNAL; price null; ack —; flags —.
- 2023-02-03 13:20:00: ENTRY MODELLED, CONDITIONAL_OPEN_SCENARIO; price 70.4; ack 2023-02-03 13:35:00; flags —.
- 2023-02-03 13:35:00: EXIT_ORDER SUBMITTED, SESSION_FLAT; price null; ack —; flags —.
- 2023-02-03 13:50:00: FLAT_TARGET UNCONFIRMED, NO_CONFIRMED_FLAT_AT_B_MINUS_10; price null; ack —; flags —.
- 2023-02-03 13:40:00: EXIT MODELLED, SESSION_FLAT; price 70.42; ack 2023-02-03 13:55:00; flags —.

Exit **70.42**, reason **SESSION_FLAT**, interval [2023-02-03 13:40:00, 2023-02-03 13:45:00), ack 2023-02-03 13:55:00. Gross = 1×(70.42−70.4) = **0.02**; C1 = 0.01 + 0.01 = 0.02; Net = **0.00**; initial risk = |entry−initial stop| = 0.04; Net R = **0**. Flat deadline breach True. Oracle ↔ ledger: **MATCH**.

## 24. CNY: датированный tick 0.001

`VWAP_MR_CNYRUBF / FROZEN_V2__NONE / C1_T10 / VWAP_MR_CNYRUBF_000684`. Signal CSV строка **23861**; ledger строка **2496**.

Сигнал 2023-09-28 12:45:00, Close доступен 2023-09-28 12:55:00; ready 2023-09-28 12:55:00; exact scheduled Open 2023-09-28 13:00:00. Направление SHORT; status/reason **MODELLED / CONDITIONAL_OPEN_SCENARIO**.

ATR12 = сумма прошлых 12 TR / 12 = 0.14100 / 12 = **0.01175**. VWAP = 516362.461333 / 38896 = **13.2754643494**; локальный anchor 2023-09-28 10:00:00; prior bars 33.

12 TR, исключая signal bar (2023-09-28 11:45:00 … 2023-09-28 12:40:00): `0.014, 0.023, 0.022, 0.005, 0.006, 0.007, 0.023, 0.011, 0.008, 0.010, 0.006, 0.006`.

Условие сигнала: **13.289 ≥ 13.2866950413; 13.2754643494 < 13.284 < 13.2872143494**. ATR14 0.00975850846596; ADX14 58.0102875099; +DI/-DI 32.5589088083 / 21.1654682226. Архитектура FROZEN_V2 определяет, используются ли эти контексты.

Initial Stop **13.301**, frozen Take **13.275**, cap **13.282**, dated tick 0.001. Swing последних 3 включая сигнал [13.279, 13.296].

Boundary entry check: scheduled end 2023-09-28 13:05:00 ≤ B−30 2023-09-28 13:30:00 = True; окно signal/entry совпадает True.

Stop raw Close−direction×1.5ATR12 = 13.301625, округление down → 13.301.

Take raw 13.2754643494, округление down → 13.275; original cap raw Close+direction×0.25ATR12 = 13.2810625.

Scheduled Open 13.29: signed risk 0.011, reward 0.015, direction×(Open−cap) -0.008 ≤0. Entry-quality ruler: risk≥4tick 0.004 = True; reward−2tick 0.013 ≥ risk+2tick 0.013 = True. Entry-quality ruler применяется только ENTRY/FULL/payable, не FROZEN_V2.

| Start MSK | Роль | O | H | L | C | V |
| --- | --- | --- | --- | --- | --- | --- |
| 2023-09-28 12:40:00 | previous, source row 28098 | 13.292 | 13.292 | 13.286 | 13.289 | 1636 |
| 2023-09-28 12:45:00 | signal, source row 28099 | 13.287 | 13.287 | 13.279 | 13.284 | 2408 |
| 2023-09-28 13:00:00 | scheduled entry, source row 28102 | 13.29 | 13.297 | 13.29 | 13.293 | 422 |
| 2023-09-28 13:25:00 | delivered decision candle, source row 28107 | 13.283 | 13.287 | 13.28 | 13.284 | 480 |
| 2023-09-28 13:40:00 | EXIT, source row 28110 | 13.28 | 13.28 | 13.271 | 13.272 | 578 |

Решения и исполнения (сравнение с execution_events.csv.gz: MATCH):

- 2023-09-28 12:55:00: ENTRY_ORDER SUBMITTED, FIXED_SIGNAL; price null; ack —; flags —.
- 2023-09-28 13:00:00: ENTRY MODELLED, CONDITIONAL_OPEN_SCENARIO; price 13.29; ack 2023-09-28 13:10:00; flags —.
- 2023-09-28 13:35:00: EXIT_ORDER SUBMITTED, SESSION_FLAT; price null; ack —; flags —.
- 2023-09-28 13:40:00: EXIT MODELLED, SESSION_FLAT; price 13.28; ack 2023-09-28 13:50:00; flags —.

Exit **13.28**, reason **SESSION_FLAT**, interval [2023-09-28 13:40:00, 2023-09-28 13:45:00), ack 2023-09-28 13:50:00. Gross = -1×(13.28−13.29) = **0.01**; C1 = 0.001 + 0.001 = 0.002; Net = **0.008**; initial risk = |entry−initial stop| = 0.011; Net R = **0.727272727273**. Flat deadline breach False. Oracle ↔ ledger: **MATCH**.

## 25. GLD: главный победитель FULL M30

`MOMENTUM_GLDRUBF / FULL_M5__M30 / C1_T10 / MOMENTUM_GLDRUBF_000312`. Signal CSV строка **114023**; ledger строка **7846**.

Сигнал 2023-10-09 16:40:00, Close доступен 2023-10-09 16:50:00; ready 2023-10-09 16:50:00; exact scheduled Open 2023-10-09 16:55:00. Направление SHORT; status/reason **MODELLED / CONDITIONAL_OPEN_SCENARIO**.

ATR12 = сумма прошлых 12 TR / 12 = 110.000000000 / 12 = **9.16666666667**. VWAP = 32209866.0667 / 5407 = **5957.06788731**; локальный anchor 2023-10-09 14:05:00; prior bars 31.

12 TR, исключая signal bar (2023-10-09 15:40:00 … 2023-10-09 16:35:00): `14.6, 6, 6.6, 10.0, 9, 6.2, 12, 7.7, 4.8, 9.2, 13.3, 10.6`.

Условие сигнала: **Close 5924.5 < prior-12 edge 5928.8; range [5928.8, 5972.6]**. ATR14 9.12328745236; ADX14 30.8261307766; +DI/-DI 17.0609662362 / 29.4200756967. Архитектура FULL_M5 определяет, используются ли эти контексты.

Initial Stop **5938.1**, frozen Take **5897.0**, cap **5922.3**, dated tick 0.1. Swing последних 3 включая сигнал [5924.5, 5942.2].

Boundary entry check: scheduled end 2023-10-09 17:00:00 ≤ B−30 2023-10-09 18:20:00 = True; окно signal/entry совпадает True.

Stop raw ATR14 5938.18493118; structure 5933.36164373; дальний max = 5938.18493118, округление down к tick → 5938.1.

Take raw 5897.00000000, округление down → 5897.0; original cap raw Close+direction×0.25ATR12 = 5922.20833333.

DI aligned = True; ADX≥25 = True; Momentum требует обе проверки; MR блокирует только strong adverse DI.

MTF: parents 2023-10-09 15:30:00 / 2023-10-09 16:00:00, direction -1; available 2023-10-09 16:35:00 ≤ decision 2023-10-09 16:50:00; eligible True.

Parent 2023-10-09 15:30:00, агрегат O/H/L/C/V `5969.4, 5976, 5953.5, 5955, 1130`; все 6 children: `15:30, 15:35, 15:40, 15:45, 15:50, 15:55`.

Parent 2023-10-09 16:00:00, агрегат O/H/L/C/V `5955.6, 5964, 5935, 5941.8, 1048`; все 6 children: `16:00, 16:05, 16:10, 16:15, 16:20, 16:25`.

Scheduled Open 5924.5: signed risk 13.6, reward 27.5, direction×(Open−cap) -2.2 ≤0. Entry-quality ruler: risk≥4tick 0.4 = True; reward−2tick 27.3 ≥ risk+2tick 13.8 = True. Entry-quality ruler применяется только ENTRY/FULL/payable, не FROZEN_V2.

| Start MSK | Роль | O | H | L | C | V |
| --- | --- | --- | --- | --- | --- | --- |
| 2023-10-09 16:35:00 | previous, source row 9081 | 5933.2 | 5939.4 | 5928.8 | 5933.5 | 156 |
| 2023-10-09 16:40:00 | signal, source row 9082 | 5931.3 | 5933.3 | 5924.5 | 5924.5 | 101 |
| 2023-10-09 16:55:00 | scheduled entry, source row 9085 | 5924.5 | 5932.9 | 5911.1 | 5911.1 | 478 |
| 2023-10-09 17:10:00 | delivered decision candle, source row 9088 | 5916 | 5916.1 | 5900 | 5900 | 770 |
| 2023-10-09 17:25:00 | STOP_AMENDMENT, source row 9091 | 5917 | 5918 | 5917 | 5917.4 | 19 |
| 2023-10-09 17:45:00 | delivered decision candle, source row 9095 | 5912 | 5912 | 5884.9 | 5889.9 | 882 |
| 2023-10-09 17:50:00 | delivered decision candle, source row 9096 | 5890.1 | 5891.2 | 5877.4 | 5881.3 | 992 |
| 2023-10-09 17:55:00 | delivered decision candle, source row 9097 | 5881.8 | 5898.5 | 5874.5 | 5888.3 | 452 |
| 2023-10-09 18:00:00 | delivered decision candle, source row 9098 | 5889 | 5894.3 | 5873.1 | 5873.1 | 349 |
| 2023-10-09 18:05:00 | delivered decision candle, source row 9099 | 5873.1 | 5880 | 5871 | 5871 | 197 |
| 2023-10-09 18:10:00 | delivered decision candle, source row 9100 | 5871 | 5883.2 | 5871 | 5882 | 355 |
| 2023-10-09 18:15:00 | STOP_AMENDMENT, source row 9101 | 5882 | 5882 | 5848.3 | 5848.3 | 2159 |
| 2023-10-09 18:20:00 | STOP_AMENDMENT, source row 9102 | 5852.5 | 5859 | 5843.3 | 5849.5 | 1002 |
| 2023-10-09 18:25:00 | EXIT, source row 9103 | 5849.5 | 5862 | 5844 | 5853 | 195 |

Решения и исполнения (сравнение с execution_events.csv.gz: MATCH):

- 2023-10-09 16:50:00: ENTRY_ORDER SUBMITTED, FIXED_SIGNAL; price null; ack —; flags —.
- 2023-10-09 16:55:00: ENTRY MODELLED, CONDITIONAL_OPEN_SCENARIO; price 5924.5; ack 2023-10-09 17:05:00; flags —.
- 2023-10-09 17:20:00: STOP_AMEND_ORDER SUBMITTED, BE; price 5924.3; ack —; flags —.
- 2023-10-09 17:25:00: STOP_AMENDMENT MODELLED, BE; price 5924.3; ack 2023-10-09 17:35:00; flags —.
- 2023-10-09 17:55:00: STOP_AMEND_ORDER SUBMITTED, TRAIL; price 5908.9; ack —; flags —.
- 2023-10-09 18:00:00: STOP_AMEND_ORDER SUBMITTED, TRAIL; price 5901.7; ack —; flags —.
- 2023-10-09 18:05:00: STOP_AMEND_ORDER SUBMITTED, TRAIL; price 5900.5; ack —; flags —.
- 2023-10-09 18:00:00: STOP_AMENDMENT MODELLED, TRAIL; price 5908.9; ack 2023-10-09 18:10:00; flags —.
- 2023-10-09 18:10:00: STOP_AMEND_ORDER SUBMITTED, TRAIL; price 5900.2; ack —; flags —.
- 2023-10-09 18:05:00: STOP_AMENDMENT MODELLED, TRAIL; price 5901.7; ack 2023-10-09 18:15:00; flags —.
- 2023-10-09 18:15:00: STOP_AMEND_ORDER SUBMITTED, TRAIL; price 5897.5; ack —; flags —.
- 2023-10-09 18:10:00: STOP_AMENDMENT MODELLED, TRAIL; price 5900.5; ack 2023-10-09 18:20:00; flags —.
- 2023-10-09 18:20:00: EXIT_ORDER SUBMITTED, MAX_HOLD; price null; ack —; flags —.
- 2023-10-09 18:15:00: STOP_AMENDMENT MODELLED, TRAIL; price 5900.2; ack 2023-10-09 18:25:00; flags —.
- 2023-10-09 18:20:00: STOP_AMENDMENT MODELLED, TRAIL; price 5897.5; ack 2023-10-09 18:30:00; flags —.
- 2023-10-09 18:25:00: EXIT MODELLED, MAX_HOLD; price 5849.5; ack 2023-10-09 18:35:00; flags —.

BE: delivered Close progress 24.5/13.6 = 1.80147058824R; BE = entry + direction×2tick = 5924.3; best delivered extreme 5900, ATR14 11.4942141700, trail raw 5922.98842834. Stop 5924.3 decided 2023-10-09 17:20:00, effective 2023-10-09 17:25:00 > decision. Свечи до effective сохраняют прежнюю защиту.

TRAIL: delivered Close progress 34.6/13.6 = 2.54411764706R; BE = entry + direction×2tick = 5924.3; best delivered extreme 5884.9, ATR14 12.0328141596, trail raw 5908.96562832. Stop 5908.9 decided 2023-10-09 17:55:00, effective 2023-10-09 18:00:00 > decision. Свечи до effective сохраняют прежнюю защиту.

TRAIL: delivered Close progress 43.2/13.6 = 3.17647058824R; BE = entry + direction×2tick = 5924.3; best delivered extreme 5877.4, ATR14 12.1590417197, trail raw 5901.71808344. Stop 5901.7 decided 2023-10-09 18:00:00, effective 2023-10-09 18:05:00 > decision. Свечи до effective сохраняют прежнюю защиту.

TRAIL: delivered Close progress 36.2/13.6 = 2.66176470588R; BE = entry + direction×2tick = 5924.3; best delivered extreme 5874.5, ATR14 13.0048244540, trail raw 5900.50964891. Stop 5900.5 decided 2023-10-09 18:05:00, effective 2023-10-09 18:10:00 > decision. Свечи до effective сохраняют прежнюю защиту.

TRAIL: delivered Close progress 51.4/13.6 = 3.77941176471R; BE = entry + direction×2tick = 5924.3; best delivered extreme 5873.1, ATR14 13.5901941358, trail raw 5900.28038827. Stop 5900.2 decided 2023-10-09 18:10:00, effective 2023-10-09 18:15:00 > decision. Свечи до effective сохраняют прежнюю защиту.

TRAIL: delivered Close progress 53.5/13.6 = 3.93382352941R; BE = entry + direction×2tick = 5924.3; best delivered extreme 5871, ATR14 13.2623231261, trail raw 5897.52464625. Stop 5897.5 decided 2023-10-09 18:15:00, effective 2023-10-09 18:20:00 > decision. Свечи до effective сохраняют прежнюю защиту.

Exit **5849.5**, reason **MAX_HOLD**, interval [2023-10-09 18:25:00, 2023-10-09 18:30:00), ack 2023-10-09 18:35:00. Gross = -1×(5849.5−5924.5) = **75.0**; C1 = 0.1 + 0.1 = 0.2; Net = **74.8**; initial risk = |entry−initial stop| = 13.6; Net R = **5.5**. Flat deadline breach False. Oracle ↔ ledger: **MATCH**.

## 26. MR payable-cap и причинный M15

`VWAP_MR_USDRUBF / PAYABLE_CAP_ENTRY__M15 / C1_T10 / VWAP_MR_USDRUBF_000020`. Signal CSV строка **5877**; ledger строка **1063**.

Сигнал 2023-01-06 11:30:00, Close доступен 2023-01-06 11:40:00; ready 2023-01-06 11:40:00; exact scheduled Open 2023-01-06 11:45:00. Направление LONG; status/reason **MODELLED / CONDITIONAL_OPEN_SCENARIO**.

ATR12 = сумма прошлых 12 TR / 12 = 1.44 / 12 = **0.12**. VWAP = 261832.913333 / 3645 = **71.8334467307**; локальный anchor 2023-01-06 10:00:00; prior bars 18.

12 TR, исключая signal bar (2023-01-06 10:30:00 … 2023-01-06 11:25:00): `0.13, 0.14, 0.18, 0.12, 0.07, 0.11, 0.16, 0.07, 0.08, 0.09, 0.19, 0.10`.

Условие сигнала: **71.71 ≤ 71.7166469205; 71.7134467307 < 71.75 < 71.8334467307**. ATR14 0.122843476676; ADX14 null; +DI/-DI 12.1922402270 / 30.8592776219. Архитектура PAYABLE_CAP_ENTRY определяет, используются ли эти контексты.

Initial Stop **71.57**, frozen Take **71.84**, cap **71.68**, dated tick 0.01. Swing последних 3 включая сигнал [71.51, 71.75].

Boundary entry check: scheduled end 2023-01-06 11:50:00 ≤ B−30 2023-01-06 13:30:00 = True; окно signal/entry совпадает True.

Stop raw Close−direction×1.5ATR12 = 71.570, округление up → 71.57.

Take raw 71.8334467307, округление up → 71.84; original cap raw Close+direction×0.25ATR12 = 71.7800.

Payable bound (Take + Stop − direction×4tick)/2 = 71.685; cap округлён в безопасную сторону. Risk(cap) 0.11; reward(cap)−2tick 0.14.

MTF: parents 2023-01-06 11:00:00 / 2023-01-06 11:15:00, direction 0; available 2023-01-06 11:35:00 ≤ decision 2023-01-06 11:40:00; eligible True.

Parent 2023-01-06 11:00:00, агрегат O/H/L/C/V `71.78, 71.79, 71.6, 71.6, 587`; все 3 children: `11:00, 11:05, 11:10`.

Parent 2023-01-06 11:15:00, агрегат O/H/L/C/V `71.6, 71.75, 71.51, 71.71, 452`; все 3 children: `11:15, 11:20, 11:25`.

Scheduled Open 71.68: signed risk 0.11, reward 0.16, direction×(Open−cap) 0.00 ≤0. Entry-quality ruler: risk≥4tick 0.04 = True; reward−2tick 0.14 ≥ risk+2tick 0.13 = True. Entry-quality ruler применяется только ENTRY/FULL/payable, не FROZEN_V2.

| Start MSK | Роль | O | H | L | C | V |
| --- | --- | --- | --- | --- | --- | --- |
| 2023-01-06 11:25:00 | previous, source row 542 | 71.71 | 71.75 | 71.65 | 71.71 | 81 |
| 2023-01-06 11:30:00 | signal, source row 543 | 71.7 | 71.75 | 71.66 | 71.75 | 100 |
| 2023-01-06 11:45:00 | scheduled entry, source row 546 | 71.68 | 71.7 | 71.65 | 71.67 | 291 |
| 2023-01-06 12:30:00 | delivered decision candle, source row 555 | 71.69 | 71.69 | 71.59 | 71.63 | 262 |
| 2023-01-06 12:45:00 | EXIT, source row 558 | 71.72 | 71.76 | 71.7 | 71.75 | 33 |

Решения и исполнения (сравнение с execution_events.csv.gz: MATCH):

- 2023-01-06 11:40:00: ENTRY_ORDER SUBMITTED, FIXED_SIGNAL; price null; ack —; flags —.
- 2023-01-06 11:45:00: ENTRY MODELLED, CONDITIONAL_OPEN_SCENARIO; price 71.68; ack 2023-01-06 11:55:00; flags —.
- 2023-01-06 12:40:00: EXIT_ORDER SUBMITTED, MAX_HOLD; price null; ack —; flags —.
- 2023-01-06 12:45:00: EXIT MODELLED, MAX_HOLD; price 71.72; ack 2023-01-06 12:55:00; flags —.

Exit **71.72**, reason **MAX_HOLD**, interval [2023-01-06 12:45:00, 2023-01-06 12:50:00), ack 2023-01-06 12:55:00. Gross = 1×(71.72−71.68) = **0.04**; C1 = 0.01 + 0.01 = 0.02; Net = **0.02**; initial risk = |entry−initial stop| = 0.11; Net R = **0.181818181818**. Flat deadline breach False. Oracle ↔ ledger: **MATCH**.

## 27. Momentum: причинный H1

`MOMENTUM_USDRUBF / ENTRY_MANAGEMENT__H1 / C1_T10 / MOMENTUM_USDRUBF_000201`. Signal CSV строка **57238**; ledger строка **5553**.

Сигнал 2023-01-31 12:55:00, Close доступен 2023-01-31 13:05:00; ready 2023-01-31 13:05:00; exact scheduled Open 2023-01-31 13:10:00. Направление LONG; status/reason **MODELLED / CONDITIONAL_OPEN_SCENARIO**.

ATR12 = сумма прошлых 12 TR / 12 = 0.700000000000 / 12 = **0.0583333333333**. VWAP = 331820.480000 / 4704 = **70.5400680272**; локальный anchor 2023-01-31 10:00:00; prior bars 35.

12 TR, исключая signal bar (2023-01-31 11:55:00 … 2023-01-31 12:50:00): `0.04, 0.08, 0.10, 0.05, 0.03, 0.04, 0.10, 0.05, 0.06, 0.08, 0.04, 0.03`.

Условие сигнала: **Close 70.74 > prior-12 edge 70.71; range [70.39, 70.71]**. ATR14 0.0613137224651; ADX14 22.9967990668; +DI/-DI 36.7889434162 / 12.9802095657. Архитектура ENTRY_MANAGEMENT определяет, используются ли эти контексты.

Initial Stop **70.65**, frozen Take **70.92**, cap **70.75**, dated tick 0.01. Swing последних 3 включая сигнал [70.65, 70.74].

Boundary entry check: scheduled end 2023-01-31 13:15:00 ≤ B−30 2023-01-31 13:30:00 = True; окно signal/entry совпадает True.

Stop raw ATR14 70.6480294163; structure 70.6793431388; дальний min = 70.6480294163, округление up к tick → 70.65.

Take raw 70.9150000000, округление up → 70.92; original cap raw Close+direction×0.25ATR12 = 70.7545833333.

MTF: parents 2023-01-31 11:00:00 / 2023-01-31 12:00:00, direction 1; available 2023-01-31 13:05:00 ≤ decision 2023-01-31 13:05:00; eligible True.

Parent 2023-01-31 11:00:00, агрегат O/H/L/C/V `70.38, 70.51, 70.32, 70.4, 1031`; все 12 children: `11:00, 11:05, 11:10, 11:15, 11:20, 11:25, 11:30, 11:35, 11:40, 11:45, 11:50, 11:55`.

Parent 2023-01-31 12:00:00, агрегат O/H/L/C/V `70.4, 70.74, 70.39, 70.74, 1932`; все 12 children: `12:00, 12:05, 12:10, 12:15, 12:20, 12:25, 12:30, 12:35, 12:40, 12:45, 12:50, 12:55`.

Scheduled Open 70.72: signed risk 0.07, reward 0.20, direction×(Open−cap) -0.03 ≤0. Entry-quality ruler: risk≥4tick 0.04 = True; reward−2tick 0.18 ≥ risk+2tick 0.09 = True. Entry-quality ruler применяется только ENTRY/FULL/payable, не FROZEN_V2.

| Start MSK | Роль | O | H | L | C | V |
| --- | --- | --- | --- | --- | --- | --- |
| 2023-01-31 12:50:00 | previous, source row 3357 | 70.69 | 70.71 | 70.68 | 70.71 | 209 |
| 2023-01-31 12:55:00 | signal, source row 3358 | 70.7 | 70.74 | 70.7 | 70.74 | 396 |
| 2023-01-31 13:10:00 | scheduled entry, source row 3361 | 70.72 | 70.74 | 70.72 | 70.72 | 73 |
| 2023-01-31 13:25:00 | delivered decision candle, source row 3364 | 70.74 | 70.79 | 70.74 | 70.79 | 54 |
| 2023-01-31 13:40:00 | EXIT, source row 3367 | 70.67 | 70.68 | 70.64 | 70.67 | 56 |

Решения и исполнения (сравнение с execution_events.csv.gz: MATCH):

- 2023-01-31 13:05:00: ENTRY_ORDER SUBMITTED, FIXED_SIGNAL; price null; ack —; flags —.
- 2023-01-31 13:10:00: ENTRY MODELLED, CONDITIONAL_OPEN_SCENARIO; price 70.72; ack 2023-01-31 13:20:00; flags —.
- 2023-01-31 13:35:00: EXIT_ORDER SUBMITTED, SESSION_FLAT; price null; ack —; flags —.
- 2023-01-31 13:40:00: EXIT MODELLED, SESSION_FLAT; price 70.67; ack 2023-01-31 13:50:00; flags —.

Exit **70.67**, reason **SESSION_FLAT**, interval [2023-01-31 13:40:00, 2023-01-31 13:45:00), ack 2023-01-31 13:50:00. Gross = 1×(70.67−70.72) = **-0.05**; C1 = 0.01 + 0.01 = 0.02; Net = **-0.07**; initial risk = |entry−initial stop| = 0.07; Net R = **-1**. Flat deadline breach False. Oracle ↔ ledger: **MATCH**.

## 28. BREAKOUT_NOT_PERSISTENT

`MOMENTUM_USDRUBF / ENTRY_MANAGEMENT__NONE / C1_T10 / MOMENTUM_USDRUBF_000001`. Signal CSV строка **51796**; ledger отсутствует.

Сигнал 2023-01-03 11:35:00, Close доступен 2023-01-03 11:45:00; ready 2023-01-03 11:45:00; exact scheduled Open 2023-01-03 11:50:00. Направление LONG; status/reason **NONFILL / BREAKOUT_NOT_PERSISTENT**.

ATR12 = сумма прошлых 12 TR / 12 = 1.91000000000 / 12 = **0.159166666667**. VWAP = 432530.463333 / 6174 = **70.0567643883**; локальный anchor 2023-01-03 10:00:00; prior bars 19.

12 TR, исключая signal bar (2023-01-03 10:35:00 … 2023-01-03 11:30:00): `0.29, 0.20, 0.17, 0.26, 0.16, 0.16, 0.18, 0.07, 0.09, 0.16, 0.06, 0.11`.

Условие сигнала: **Close 70.26 > prior-12 edge 70.2; range [69.76, 70.2]**. ATR14 0.164066488294; ADX14 null; +DI/-DI 29.5636788872 / 16.9952903746. Архитектура ENTRY_MANAGEMENT определяет, используются ли эти контексты.

Initial Stop **70.02**, frozen Take **70.74**, cap **70.29**, dated tick 0.01. Swing последних 3 включая сигнал [70.01, 70.26].

Boundary entry check: scheduled end 2023-01-03 11:55:00 ≤ B−30 2023-01-03 13:30:00 = True; окно signal/entry совпадает True.

Stop raw ATR14 70.0139002676; structure 70.1179667559; дальний min = 70.0139002676, округление up к tick → 70.02.

Take raw 70.7375000000, округление up → 70.74; original cap raw Close+direction×0.25ATR12 = 70.2997916667.

Scheduled Open 70.2: signed risk 0.18, reward 0.54, direction×(Open−cap) -0.09 ≤0. Entry-quality ruler: risk≥4tick 0.04 = True; reward−2tick 0.52 ≥ risk+2tick 0.20 = True. Entry-quality ruler применяется только ENTRY/FULL/payable, не FROZEN_V2.

| Start MSK | Роль | O | H | L | C | V |
| --- | --- | --- | --- | --- | --- | --- |
| 2023-01-03 11:30:00 | previous, source row 32 | 70.04 | 70.13 | 70.02 | 70.13 | 147 |
| 2023-01-03 11:35:00 | signal, source row 33 | 70.13 | 70.26 | 70.1 | 70.26 | 133 |
| 2023-01-03 11:50:00 | scheduled entry, source row 36 | 70.2 | 70.2 | 70.16 | 70.18 | 24 |

Решения и исполнения (сравнение с execution_events.csv.gz: MATCH):

- 2023-01-03 11:45:00: ENTRY_ORDER SUBMITTED, FIXED_SIGNAL; price null; ack —; flags —.
- 2023-01-03 11:50:00: ENTRY NONFILL, BREAKOUT_NOT_PERSISTENT; price null; ack 2023-01-03 12:00:00; flags —.

Модельный вход не создан; цена исполнения/C1/P&L отсутствуют. Oracle ↔ signal status/reason: **MATCH**.

## 29. NO_BAR_NO_MODEL_FILL

`VWAP_MR_USDRUBF / FROZEN_V2__NONE / C1_T10 / VWAP_MR_USDRUBF_000134`. Signal CSV строка **135**; ledger отсутствует.

Сигнал 2023-02-02 15:25:00, Close доступен 2023-02-02 15:35:00; ready 2023-02-02 15:35:00; exact scheduled Open 2023-02-02 15:40:00. Направление LONG; status/reason **NO_BAR_NO_MODEL_FILL / NO_BAR_NO_MODEL_FILL**.

ATR12 = сумма прошлых 12 TR / 12 = 0.410000000000 / 12 = **0.0341666666667**. VWAP = 55944.3900000 / 798 = **70.1057518797**; локальный anchor 2023-02-02 14:05:00; prior bars 16.

12 TR, исключая signal bar (2023-02-02 14:25:00 … 2023-02-02 15:20:00): `0.04, 0.02, 0.02, 0.02, 0.02, 0.05, 0.05, 0.05, 0.03, 0.06, 0.03, 0.02`.

Условие сигнала: **70.07 ≤ 70.0725563502; 70.0715852130 < 70.09 < 70.1057518797**. ATR14 0.0354956268222; ADX14 null; +DI/-DI 20.8213552361 / 21.3655030801. Архитектура FROZEN_V2 определяет, используются ли эти контексты.

Initial Stop **70.04**, frozen Take **70.11**, cap **70.09**, dated tick 0.01. Swing последних 3 включая сигнал [70.06, 70.12].

Boundary entry check: scheduled end 2023-02-02 15:45:00 ≤ B−30 2023-02-02 18:20:00 = True; окно signal/entry совпадает True.

Stop raw Close−direction×1.5ATR12 = 70.0387500000, округление up → 70.04.

Take raw 70.1057518797, округление up → 70.11; original cap raw Close+direction×0.25ATR12 = 70.0985416667.

| Start MSK | Роль | O | H | L | C | V |
| --- | --- | --- | --- | --- | --- | --- |
| 2023-02-02 15:20:00 | previous, source row 3727 | 70.09 | 70.09 | 70.07 | 70.07 | 53 |
| 2023-02-02 15:25:00 | signal, source row 3728 | 70.06 | 70.09 | 70.06 | 70.09 | 29 |
| 2023-02-02 15:40:00 | scheduled entry, source row missing | missing | missing | missing | missing | missing |

Решения и исполнения (сравнение с execution_events.csv.gz: MATCH):

- 2023-02-02 15:35:00: ENTRY_ORDER SUBMITTED, FIXED_SIGNAL; price null; ack —; flags —.
- 2023-02-02 15:40:00: ENTRY_OUTCOME NO_BAR_NO_MODEL_FILL, NO_BAR_NO_MODEL_FILL; price null; ack 2023-02-02 15:50:00; flags —.

Модельный вход не создан; цена исполнения/C1/P&L отсутствуют. Oracle ↔ signal status/reason: **MATCH**.

## 30. MTF_INCOMPLETE_CHILD_BUCKET

`VWAP_MR_USDRUBF / FROZEN_V2__M30 / C1_T10 / VWAP_MR_USDRUBF_000419`. Signal CSV строка **1884**; ledger отсутствует.

Сигнал 2023-04-12 17:20:00, Close доступен 2023-04-12 17:30:00; ready 2023-04-12 17:30:00; exact scheduled Open 2023-04-12 17:35:00. Направление LONG; status/reason **FILTERED / MTF_INCOMPLETE_CHILD_BUCKET**.

ATR12 = сумма прошлых 12 TR / 12 = 0.660 / 12 = **0.055**. VWAP = 175686.356667 / 2136 = **82.2501669788**; локальный anchor 2023-04-12 16:15:00; prior bars 13.

12 TR, исключая signal bar (2023-04-12 16:20:00 … 2023-04-12 17:15:00): `0.03, 0.07, 0.07, 0.02, 0.02, 0.04, 0.12, 0.13, 0.04, 0.04, 0.02, 0.06`.

Условие сигнала: **82.17 ≤ 82.1959765749; 82.1951669788 < 82.2 < 82.2501669788**. ATR14 null; ADX14 null; +DI/-DI null / null. Архитектура FROZEN_V2 определяет, используются ли эти контексты.

Initial Stop **82.12**, frozen Take **82.26**, cap **82.21**, dated tick 0.01. Swing последних 3 включая сигнал [82.15, 82.22].

Boundary entry check: scheduled end 2023-04-12 17:40:00 ≤ B−30 2023-04-12 18:20:00 = True; окно signal/entry совпадает True.

Stop raw Close−direction×1.5ATR12 = 82.1175, округление up → 82.12.

Take raw 82.2501669788, округление up → 82.26; original cap raw Close+direction×0.25ATR12 = 82.21375.

MTF block: MTF_INCOMPLETE_CHILD_BUCKET; последняя ожидаемая пара не заменяется старой. Nominal latest parent 2023-04-12 16:30:00, available minimum 2023-04-12 17:05:00.

Expected parent 2023-04-12 16:00:00; children `16:00 observed, 16:05 observed, 16:10 MISSING, 16:15 observed, 16:20 observed, 16:25 observed`.

Expected parent 2023-04-12 16:30:00; children `16:30 observed, 16:35 observed, 16:40 observed, 16:45 observed, 16:50 observed, 16:55 observed`.

Scheduled Open 82.23: signed risk 0.11, reward 0.03, direction×(Open−cap) 0.02 ≤0. Entry-quality ruler: risk≥4tick 0.04 = True; reward−2tick 0.01 ≥ risk+2tick 0.13 = False. Entry-quality ruler применяется только ENTRY/FULL/payable, не FROZEN_V2.

| Start MSK | Роль | O | H | L | C | V |
| --- | --- | --- | --- | --- | --- | --- |
| 2023-04-12 17:15:00 | previous, source row 11571 | 82.2 | 82.21 | 82.15 | 82.17 | 74 |
| 2023-04-12 17:20:00 | signal, source row 11572 | 82.19 | 82.2 | 82.18 | 82.2 | 30 |
| 2023-04-12 17:35:00 | scheduled entry, source row 11575 | 82.23 | 82.23 | 82.22 | 82.22 | 77 |

Решения и исполнения (сравнение с execution_events.csv.gz: MATCH):

- 2023-04-12 17:30:00: ENTRY_ORDER SUBMITTED, FIXED_SIGNAL; price null; ack —; flags —.
- 2023-04-12 17:30:00: ENTRY_CANCEL CANCELLED, MTF_INCOMPLETE_CHILD_BUCKET; price null; ack —; flags —.

Модельный вход не создан; цена исполнения/C1/P&L отсутствуют. Oracle ↔ signal status/reason: **MATCH**.

## 31. MOMENTUM_ADX_DI_REGIME

`MOMENTUM_USDRUBF / FULL_M5__NONE / C1_T10 / MOMENTUM_USDRUBF_000002`. Signal CSV строка **59660**; ledger отсутствует.

Сигнал 2023-01-03 12:20:00, Close доступен 2023-01-03 12:30:00; ready 2023-01-03 12:30:00; exact scheduled Open 2023-01-03 12:35:00. Направление LONG; status/reason **FILTERED / MOMENTUM_ADX_DI_REGIME**.

ATR12 = сумма прошлых 12 TR / 12 = 1.0500 / 12 = **0.0875**. VWAP = 471988.086667 / 6736 = **70.0694903009**; локальный anchor 2023-01-03 10:00:00; prior bars 28.

12 TR, исключая signal bar (2023-01-03 11:20:00 … 2023-01-03 12:15:00): `0.16, 0.06, 0.11, 0.16, 0.12, 0.05, 0.06, 0.04, 0.05, 0.10, 0.03, 0.11`.

Условие сигнала: **Close 70.29 > prior-12 edge 70.26; range [70.01, 70.26]**. ATR14 0.117595896412; ADX14 23.2630359963; +DI/-DI 30.4823168101 / 14.9910987184. Архитектура FULL_M5 определяет, используются ли эти контексты.

Initial Stop **70.12**, frozen Take **70.56**, cap **70.31**, dated tick 0.01. Swing последних 3 включая сигнал [70.15, 70.3].

Boundary entry check: scheduled end 2023-01-03 12:40:00 ≤ B−30 2023-01-03 13:30:00 = True; окно signal/entry совпадает True.

Stop raw ATR14 70.1136061554; structure 70.2012020518; дальний min = 70.1136061554, округление up к tick → 70.12.

Take raw 70.5525, округление up → 70.56; original cap raw Close+direction×0.25ATR12 = 70.311875.

DI aligned = True; ADX≥25 = False; Momentum требует обе проверки; MR блокирует только strong adverse DI.

Scheduled Open 70.39: signed risk 0.27, reward 0.17, direction×(Open−cap) 0.08 ≤0. Entry-quality ruler: risk≥4tick 0.04 = True; reward−2tick 0.15 ≥ risk+2tick 0.29 = False. Entry-quality ruler применяется только ENTRY/FULL/payable, не FROZEN_V2.

| Start MSK | Роль | O | H | L | C | V |
| --- | --- | --- | --- | --- | --- | --- |
| 2023-01-03 12:15:00 | previous, source row 41 | 70.16 | 70.26 | 70.15 | 70.26 | 41 |
| 2023-01-03 12:20:00 | signal, source row 42 | 70.24 | 70.3 | 70.24 | 70.29 | 123 |
| 2023-01-03 12:35:00 | scheduled entry, source row 45 | 70.39 | 70.53 | 70.39 | 70.5 | 314 |

Решения и исполнения (сравнение с execution_events.csv.gz: MATCH):

- 2023-01-03 12:30:00: ENTRY_ORDER SUBMITTED, FIXED_SIGNAL; price null; ack —; flags —.
- 2023-01-03 12:30:00: ENTRY_CANCEL CANCELLED, MOMENTUM_ADX_DI_REGIME; price null; ack —; flags —.

Модельный вход не создан; цена исполнения/C1/P&L отсутствуют. Oracle ↔ signal status/reason: **MATCH**.

## 32. Мартовская граница: вход запрещён

`VWAP_MR_USDRUBF / FROZEN_V2__NONE / C1_T10 / VWAP_MR_USDRUBF_000281`. Signal CSV строка **282**; ledger отсутствует.

Сигнал 2023-03-15 13:35:00, Close доступен 2023-03-15 13:45:00; ready 2023-03-15 13:45:00; exact scheduled Open 2023-03-15 13:50:00. Направление SHORT; status/reason **SKIPPED / KNOWN_BOUNDARY_ENTRY_CUTOFF**.

ATR12 = сумма прошлых 12 TR / 12 = 0.400000000000 / 12 = **0.0333333333333**. VWAP = 830736.553333 / 10964 = **75.7694776845**; локальный anchor 2023-03-15 10:00:00; prior bars 43.

12 TR, исключая signal bar (2023-03-15 12:35:00 … 2023-03-15 13:30:00): `0.02, 0.13, 0.03, 0.02, 0.04, 0.05, 0.03, 0.02, 0.02, 0.02, 0.00, 0.02`.

Условие сигнала: **75.83 ≥ 75.8018977145; 75.7694776845 < 75.79 < 75.8028110179**. ATR14 0.0364013671972; ADX14 39.1858198279; +DI/-DI 32.7893845840 / 30.6459479167. Архитектура FROZEN_V2 определяет, используются ли эти контексты.

Initial Stop **75.84**, frozen Take **75.76**, cap **75.79**, dated tick 0.01. Swing последних 3 включая сигнал [75.79, 75.85].

Boundary entry check: scheduled end 2023-03-15 13:55:00 ≤ B−30 2023-03-15 13:30:00 = False; окно signal/entry совпадает True.

Stop raw Close−direction×1.5ATR12 = 75.8400000000, округление down → 75.84.

Take raw 75.7694776845, округление down → 75.76; original cap raw Close+direction×0.25ATR12 = 75.7816666667.

Scheduled Open 75.86: signed risk -0.02, reward 0.10, direction×(Open−cap) -0.07 ≤0. Entry-quality ruler: risk≥4tick 0.04 = False; reward−2tick 0.08 ≥ risk+2tick 0.00 = True. Entry-quality ruler применяется только ENTRY/FULL/payable, не FROZEN_V2.

| Start MSK | Роль | O | H | L | C | V |
| --- | --- | --- | --- | --- | --- | --- |
| 2023-03-15 13:30:00 | previous, source row 8230 | 75.85 | 75.85 | 75.83 | 75.83 | 28 |
| 2023-03-15 13:35:00 | signal, source row 8231 | 75.83 | 75.83 | 75.79 | 75.79 | 288 |
| 2023-03-15 13:50:00 | scheduled entry, source row 8234 | 75.86 | 75.87 | 75.83 | 75.84 | 129 |

Решения и исполнения (сравнение с execution_events.csv.gz: MATCH):


Модельный вход не создан; цена исполнения/C1/P&L отсутствуют. Oracle ↔ signal status/reason: **MATCH**.

## 33. Take touch без tick penetration: nonfill

`VWAP_MR_USDRUBF / FROZEN_V2__NONE / C1_T10 / VWAP_MR_USDRUBF_000014`. Signal CSV строка **15**; ledger строка **6**.

Сигнал 2023-01-05 12:05:00, Close доступен 2023-01-05 12:15:00; ready 2023-01-05 12:15:00; exact scheduled Open 2023-01-05 12:20:00. Направление SHORT; status/reason **MODELLED / CONDITIONAL_OPEN_SCENARIO**.

ATR12 = сумма прошлых 12 TR / 12 = 1.28000000000 / 12 = **0.106666666667**. VWAP = 581642.246667 / 8117 = **71.6572929243**; локальный anchor 2023-01-05 10:00:00; prior bars 25.

12 TR, исключая signal bar (2023-01-05 11:05:00 … 2023-01-05 12:00:00): `0.07, 0.10, 0.07, 0.04, 0.16, 0.15, 0.25, 0.11, 0.05, 0.08, 0.07, 0.13`.

Условие сигнала: **71.85 ≥ 71.7619504132; 71.6572929243 < 71.67 < 71.7639595910**. ATR14 0.134495317078; ADX14 null; +DI/-DI 22.6865064726 / 26.3061436400. Архитектура FROZEN_V2 определяет, используются ли эти контексты.

Initial Stop **71.83**, frozen Take **71.65**, cap **71.65**, dated tick 0.01. Swing последних 3 включая сигнал [71.63, 71.95].

Boundary entry check: scheduled end 2023-01-05 12:25:00 ≤ B−30 2023-01-05 13:30:00 = True; окно signal/entry совпадает True.

Stop raw Close−direction×1.5ATR12 = 71.8300000000, округление down → 71.83.

Take raw 71.6572929243, округление down → 71.65; original cap raw Close+direction×0.25ATR12 = 71.6433333333.

Scheduled Open 71.75: signed risk 0.08, reward 0.10, direction×(Open−cap) -0.10 ≤0. Entry-quality ruler: risk≥4tick 0.04 = True; reward−2tick 0.08 ≥ risk+2tick 0.10 = False. Entry-quality ruler применяется только ENTRY/FULL/payable, не FROZEN_V2.

| Start MSK | Роль | O | H | L | C | V |
| --- | --- | --- | --- | --- | --- | --- |
| 2023-01-05 12:00:00 | previous, source row 379 | 71.91 | 71.95 | 71.82 | 71.85 | 215 |
| 2023-01-05 12:05:00 | signal, source row 380 | 71.83 | 71.86 | 71.63 | 71.67 | 252 |
| 2023-01-05 12:20:00 | scheduled entry, source row 383 | 71.75 | 71.75 | 71.65 | 71.7 | 135 |
| 2023-01-05 12:25:00 | TP, source row 384 | 71.71 | 71.73 | 71.65 | 71.72 | 243 |
| 2023-01-05 12:35:00 | EXIT, source row 386 | 71.78 | 71.86 | 71.77 | 71.83 | 222 |

Решения и исполнения (сравнение с execution_events.csv.gz: MATCH):

- 2023-01-05 12:15:00: ENTRY_ORDER SUBMITTED, FIXED_SIGNAL; price null; ack —; flags —.
- 2023-01-05 12:20:00: ENTRY MODELLED, CONDITIONAL_OPEN_SCENARIO; price 71.75; ack 2023-01-05 12:30:00; flags —.
- 2023-01-05 12:25:00: TP NONFILL, TOUCH_WITHOUT_TICK_PENETRATION; price null; ack 2023-01-05 12:35:00; flags —.
- 2023-01-05 12:35:00: EXIT MODELLED, STOP; price 71.83; ack 2023-01-05 12:45:00; flags —.

Exit **71.83**, reason **STOP**, interval [2023-01-05 12:35:00, 2023-01-05 12:40:00), ack 2023-01-05 12:45:00. Gross = -1×(71.83−71.75) = **-0.08**; C1 = 0.01 + 0.01 = 0.02; Net = **-0.10**; initial risk = |entry−initial stop| = 0.08; Net R = **-1.25**. Flat deadline breach False. Oracle ↔ ledger: **MATCH**.

## 34. Take на свече входа запрещён

`VWAP_MR_USDRUBF / FROZEN_V2__NONE / C1_T10 / VWAP_MR_USDRUBF_000031`. Signal CSV строка **32**; ledger строка **12**.

Сигнал 2023-01-10 15:50:00, Close доступен 2023-01-10 16:00:00; ready 2023-01-10 16:00:00; exact scheduled Open 2023-01-10 16:05:00. Направление LONG; status/reason **MODELLED / CONDITIONAL_OPEN_SCENARIO**.

ATR12 = сумма прошлых 12 TR / 12 = 0.580000000000 / 12 = **0.0483333333333**. VWAP = 144680.180000 / 2077 = **69.6582474723**; локальный anchor 2023-01-10 14:05:00; prior bars 21.

12 TR, исключая signal bar (2023-01-10 14:50:00 … 2023-01-10 15:45:00): `0.04, 0.03, 0.07, 0.03, 0.1, 0.05, 0.08, 0.03, 0.06, 0.03, 0.03, 0.03`.

Условие сигнала: **69.59 ≤ 69.6113190996; 69.6099141390 < 69.62 < 69.6582474723**. ATR14 0.0431006163661; ADX14 null; +DI/-DI 29.0944412293 / 31.4336420146. Архитектура FROZEN_V2 определяет, используются ли эти контексты.

Initial Stop **69.55**, frozen Take **69.66**, cap **69.63**, dated tick 0.01. Swing последних 3 включая сигнал [69.56, 69.63].

Boundary entry check: scheduled end 2023-01-10 16:10:00 ≤ B−30 2023-01-10 18:20:00 = True; окно signal/entry совпадает True.

Stop raw Close−direction×1.5ATR12 = 69.5475000000, округление up → 69.55.

Take raw 69.6582474723, округление up → 69.66; original cap raw Close+direction×0.25ATR12 = 69.6320833333.

Scheduled Open 69.63: signed risk 0.08, reward 0.03, direction×(Open−cap) 0.00 ≤0. Entry-quality ruler: risk≥4tick 0.04 = True; reward−2tick 0.01 ≥ risk+2tick 0.10 = False. Entry-quality ruler применяется только ENTRY/FULL/payable, не FROZEN_V2.

| Start MSK | Роль | O | H | L | C | V |
| --- | --- | --- | --- | --- | --- | --- |
| 2023-01-10 15:45:00 | previous, source row 928 | 69.59 | 69.6 | 69.59 | 69.59 | 28 |
| 2023-01-10 15:50:00 | signal, source row 929 | 69.6 | 69.63 | 69.59 | 69.62 | 63 |
| 2023-01-10 16:05:00 | scheduled entry, source row 932 | 69.63 | 69.68 | 69.63 | 69.67 | 134 |
| 2023-01-10 16:10:00 | EXIT, source row 933 | 69.67 | 69.68 | 69.65 | 69.65 | 22 |

Решения и исполнения (сравнение с execution_events.csv.gz: MATCH):

- 2023-01-10 16:00:00: ENTRY_ORDER SUBMITTED, FIXED_SIGNAL; price null; ack —; flags —.
- 2023-01-10 16:05:00: ENTRY MODELLED, CONDITIONAL_OPEN_SCENARIO; price 69.63; ack 2023-01-10 16:15:00; flags —.
- 2023-01-10 16:10:00: EXIT MODELLED, TAKE; price 69.66; ack 2023-01-10 16:20:00; flags —.

Exit **69.66**, reason **TAKE**, interval [2023-01-10 16:10:00, 2023-01-10 16:15:00), ack 2023-01-10 16:20:00. Gross = 1×(69.66−69.63) = **0.03**; C1 = 0.01 + 0.01 = 0.02; Net = **0.01**; initial risk = |entry−initial stop| = 0.08; Net R = **0.125**. Flat deadline breach False. Oracle ↔ ledger: **MATCH**.
