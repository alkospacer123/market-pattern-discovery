# STS — реестр подтверждённой исторической базы

**Срез 11.11.2026 | Research, OOS_COMPROMISED.** Источники: воспроизводимые отчёты TRL-R-022/026/028/031/033/038/039 в архиве TRL Project; исходные файлы и их SHA не копировать без необходимости.

| Исследование | Исторический факт | Интерпретация |
|---|---|---|
| R022 | EMA20_REBOUND BASE: 1123 сделок PF1,694; LOW_NOISE_REACCEL: 411 PF1,384 | Повторять те же сигналы под иными именами бессмысленно |
| R026 | Shallow+Deep+Breakout: 2289 сделок PF1,694, DD закрытых 55,92R | Три трендовых робота не означают качество портфеля |
| R031 | 779 ретроспективных трендов, 366 без новой сделки Shallow | Доступны дополнительные структуры; profitable capture ещё не доказан |
| R033 | Regression Channel Escape BASE: 610 PF1,851; после gate Shallow 451 PF1,776 | Дедупликация меняет экономику системы |
| R038 | V20 FULL TP6+защита, 45/45/45k GO Oct: +381 608 ₽ PF1,881 closed DD11 774 ₽ | Контроль A; **TP6 здесь эксперимент, не LIVE** |
| R039 | Classic frozen BASE 773 PF1,934 +505,48R; TP6+защита 808 PF1,987 +499,29R. Classic+Micro+Sideways unified TP6+защита: 1051 PF1,900 +601,58R, но PF2025 1,337 против 1,700 у Classic | Не одобрять текущую тройку модулей, даже при большем ΣR |
| STS-EXP-001 | Shallow-only 135k GO Oct, TP6+защита: риск 0,5% = +298 628 ₽ PF1,967 DD10 782 ₽; риск 1,5% = +666 387 ₽ PF1,991 DD26 874 ₽ | Сначала уравнять риск/маржу/MTM, затем делать вывод |

**Аудиторские исходные архивы:** R038 ZIP SHA256 `4fa12f0d823cb8f6642715076a4ac25c3963ff9372371165fa115e5d7e83aa1c`; R039 ZIP SHA256 `7b233bd3330e5100a5369b2297e2058f9f8f8524c4d82248609ab9d55588d1ef`. R038 baseline parity 1523, R039 Classic parity 773 BASE / 808 TP6+защита.

**Пробелы:** ни одного независимого TRUE OOS; статичный GO, отсутствуют реальные комиссии/спред/частичное исполнение, полная intraday MTM DD и единый денежный реплей A/B/C. Средства на одном и нескольких счетах не эквивалентны без ограничений ГО. Пока `STS_CONTINUE / LIVE_UNCHANGED`.

## R040 — исправленный трёхсчётный денежный replay, 11.11.2026

**STS = 3 отдельных ядра / 3 собственных счёта / 3 капитала.** При 45 000 ₽/счёт, GO proxy Oct-2026 и экспериментальном TP6+защита: V20 Classic+OBV+Inside = +381 608 ₽, PF ₽1,845, closed DD11 774,50 ₽, 40/45 прибыльных месяцев; STS Classic+Micro+Dynamic = +401 564 ₽, PF ₽1,739, closed DD23 157,60 ₽, 37/45. 2025 PF: V20 1,554; STS 1,368. Остальные пять комбинаций не выигрывают по ₽/PF/DD одновременно. Пересчёт всех 3 банков (45k/500k/1m), обоих GO и двух выходов — [R040](TRL_R_2026_040_STS_Three_Accounts_Research.md). 10 exact parity R039 + 12 exact financial parity R038 PASS. **NO_REPLACEMENT / STS_CONTINUE / LIVE_UNCHANGED**.

Shallow-only с общим банком — *отдельная альтернативная гипотеза*, не STS; прежние результаты STS-EXP-001 нельзя трактовать как тест новой трёхсчётной архитектуры.

## R041 — роль OBV/Inside, выделение капитала, Two-Leg и Sweep (11.11.2026)

Детали: [полный отчёт](TRL_R_2026_041_STS_OBV_Inside_New_Modules_Research.md). V20 60/30/45 тыс. ₽ TP6+защита: +422224.1 ₽ / PF ₽1.914 / closed DD12940.9 ₽ / 42/45; BASE +423132.5 ₽ / PF1.889 / DD17172.5 ₽ / 34/45. У 11 убыточных месяцев Shallow BASE OBV принёс −3308 ₽, Inside +3692 ₽; это не системная страховка.

Новое: TWO_LEG_RESET 390 сделок / +121484.9 ₽ / PF1.998 (45k, Oct GO proxy, TP6). Замена Inside: +456585.5 ₽ / PF1.879 / DD12586.6 ₽ против V20 +381607.6 ₽ / PF1.845 / DD11774.5 ₽; 40/45 прибыльных месяцев в обоих. В 171 непересекающейся с Classic/Micro сделке PF1.059: новый кандидат **не доказал независимый денежный edge**, слабые дни Classic остаются слабыми. SWEEP_RECLAIM REJECT. Все цифры исторический OOS_COMPROMISED, нет реальных комиссий и MTM. `KEEP_V20 / STS_CONTINUE / LIVE_UNCHANGED`.

## R042 — Reclaim Retest и Volume Dry Reset (11.11.2026)

[Полный отчёт](TRL_R_2026_042_STS_New_Modules_Research.md) и [протокол до прогона](experiments/r042/FROZEN_PROTOCOL.md): RETEST BASE 25 сделок/PF R1,226; DRY RESET BASE 68 сделок/PF R2,423. GO Oct, TP6+защита 3×45k: действующий V20 +381 608 ₽ / PF ₽1,845 / closed DD11 775 ₽; Classic+OBV+DRY +354 154 ₽ / PF1,841 / DD12 956 ₽; Classic+DRY+Inside +274 067 ₽ / PF1,930 / DD11 049 ₽. DRY пересекается с однонаправленной Classic-позицией в 33/68 случаях; после удаления 5 денежных выигрышей P&L -486 ₽; в убыточные месяцы Classic -982 ₽. Статичные ГО и C1, не TRUE OOS. Независимый loop-аудит 101 сырого сигнала PASS. **RETEST=REJECT_CORE / DRY=ARCHIVE_FOR_FORWARD / NO_REPLACEMENT / LIVE_UNCHANGED.**

## R043 — H1/H4 Ledge и Multi-Session Staircase, 11.11.2026

[Отчёт R043](TRL_R_2026_043_STS_MTF_Staircase_Research.md), [исходные правила](experiments/r043/FROZEN_PROTOCOL.md), независимый audit 321 cash trades PASS. MTF Ledge BASE 313 сделок PF R1,628; TP6+protect 316 PF R1,500; 2025 TP6 PF R1,214. Staircase BASE 22 сделки PF R2,826; убыточные 2024/2026, после пяти лучших −8,22R. Три собственных счёта 45k, GO Oct, TP6: V20 +381608 ₽ / PF ₽1,845 / DD11775 ₽; замена Inside на MTF +382499 ₽ / PF1,762 / DD14651 ₽. Остальные замены хуже по совокупности. Статичные GO/C1, closed DD не MTM, **НЕ TRUE OOS**. **Решение** `NO_REPLACEMENT / LIVE_UNCHANGED`, Staircase только архив будущего prospective.

## R045 — V20 против Shallow-only, money/MTM/GO risk, 11.11.2026

[Исследование](TRL_R_2026_045_V20_vs_Shallow_MTM_Research.md) · 60 сценариев, 20 historical exact parity PASS, полная серия M15-close equity, 3 банка, 2 GO, BASE и TP6. Капитал 135k, GO Oct, TP6: B=V20 60/30/45 +422224 ₽, PF1,914, closedDD12941 ₽, M15DD18667 ₽, 42/45 месяцев; C=Shallow-only риск 0,667% +404160 ₽, PF1,995, M15DD16563 ₽, 39/45. GO Nov: B +283607 ₽ / M15DD15818 ₽; C риск 0,5% +285066 ₽ / M15DD11416 ₽. GO reserve peak ~98–100% всего банка, статичные прокси, реальные FINAM расходы, variation margin, стоповые гэпы, true intrabar MTM и TRUE OOS отсутствуют. Нельзя выбрать B только по 42 месяцам или C только по +666k ₽ при 1,5% риске. **HOLD_FORWARD / KEEP_V20_LIVE / SHALLOW_ONLY_LOW_RISK_CANDIDATE**. 

### R046 (11.11.2026)

Четыре новые пользовательские M15 CSV 2026-10-01—11.11 08:30; на 9–10.11 USD/CNY/IMOEX frozen исследовательские Shallow/OBV/Inside не генерируют RAW сигналы, GLD имеет 3 Shallow + 2 OBV сырьевых сигнальных бара (это **не** подтверждённые LIVE заявки). Новый заранее зафиксированный в истории (но после просмотра ноября) Drive Continuation захватывает USDRUBF, CNYRUBF, IMOEXF, однако на 45k/GO Oct/TP6 исторически 729 сделок PF ₽1,506, +119494 ₽, DD16939 ₽, 2026 YTD отрицателен. При замене Inside: общий портфель +454595 ₽ PF1,717 closed DD24169 ₽ против V20 +381608 ₽ PF1,845 DD11775 ₽. Другая конфигурация Shallow90k TP6 + Inside45k BASE исторически +510709 ₽ PF2,022 M15DD22907 ₽ при Oct GO, но не прошла независимый форвард. [R046](TRL_R_2026_046_Inside_and_Missed_Trends_Research.md). `DRIVE_REJECT_CORE / SHALLOW_INSIDE_FORWARD_CANDIDATE / LIVE_UNCHANGED`.

### R047 — пропущенные тренды и новые механизмы (11.11.2026)

Источник: [исследовательский отчёт](TRL_R_2026_047_Missed_Trend_Opportunities.md), [frozen protocol SHA256](experiments/r047/FROZEN_PROTOCOL.md), [offline reproducibility](experiments/r047/REPRODUCE_RU.md). Из 779 ex-post трендовых эпизодов **366** без принятого Classic (334 RAW отсутствует, 32 ограничения); 196 без входов всех четырёх предшествующих альтернатив Deep/SecondImpulse/H4Break/Auction. Это **не** 366 доказуемо торгуемых возможностей и **не** независимая выборка.

GO Oct TP6 +3R→+1R, банк 45k: Early 822 сделки PF ₽1,058, net +13893 ₽, closedDD21027 ₽; **156 ex-post missed events**, но 166 сделок внутри задним числом выбранных событий дают +76526 ₽, остальные 656 — −62633 ₽; при издержках C2 общая прибыль −3368 ₽. Tight Drift 21 сделка PF ₽2,757 +9906 ₽, покрыт лишь 1 missed event; без top5 −3503 ₽. Портфель V20 3×45k +381608 ₽ PF1,845 closedDD11775 ₽; все замены экономически хуже по сочетанию прибыли/устойчивости. Classic exact 773/808 PASS, 394 prefix checks, independent arithmetic 3133 trades PASS, автономный повторный replay six CSV byte identical. Последние ноябрьские пользовательские CSV обрываются 11.11 08:30; у нового Early USD/CNY 9–10.11 сигналов нет. Решение: EARLY_REJECT_CORE / TIGHT_ARCHIVE_FORWARD / NO_REPLACEMENT / LIVE_UNCHANGED.
