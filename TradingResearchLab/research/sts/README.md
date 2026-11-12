# STS — Shallow Trend System

**2026-11-11 | RESEARCH ONLY | LIVE_UNCHANGED**

**Согласованная архитектура:** STS = **три независимых торговых ядра / три стратегии / три отдельных счёта / три отдельных капитала**. Каждое ядро работает по собственному модулю семейства Shallow, имеет собственные сигналы, позиции, ГО, риск на сделку и ограничение риска счёта. Это **не** одна программа с одним общим счётом. Общие методология, интерфейсы исследовательской аналитики и портфельное наблюдение **не объединяют средства и риск-бюджеты**.

- **STS-1:** Classic Shallow Pullback — замороженная базовая стратегия.
- **STS-2:** новый отобранный модуль семейства Shallow (пока нет утверждённого кандидата).
- **STS-3:** другой новый отобранный модуль семейства Shallow (пока нет утверждённого кандидата).

Реестр модулей открыт: Micro / Flag / Sideways / Dynamic / любые будущие разновидности продолжения тренда. Их можно добавлять и заменять через годы по итогам квартальных независимых проверок. **Не требуется удерживать первоначальные пять модулей.**

### Конкурирующие портфели

- **A. Действующая V20:** Shallow + OBV + Inside, 3 отдельных счёта.
- **B. Shallow-only:** один Shallow TP6+защита и единый банк — **отдельная финансовая альтернатива, не STS**.
- **C. STS:** Classic + два доказанных Shallow-модуля на 3 отдельных счетах. До доказательств C — только research candidate.

Сохранить A или B — допустимое итоговое решение. До него LIVE не менять.

### Документация

- [Концепция и жизненный цикл](STS_CONCEPT.md)
- [Подпрограмма roadmap](STS_ROADMAP.md)
- [Сопоставимый тест трёх отдельных счетов](STS_TEST_PROTOCOL.md)
- [Историческая исследовательская база](EVIDENCE_REGISTER.md)
- [R040: новый сравнительный денежный тест 3 счетов](TRL_R_2026_040_STS_Three_Accounts_Research.md)
- [STS-EXP-001: односчётная Shallow-only альтернатива](EXPERIMENT_001_INITIAL_CASH_BENCHMARK.md)
- [Воспроизводимый STS-EXP-001](experiments/sts_exp_001_replay.py)

Работа в существующих TradingResearchLab/research и TRL Journal. Не создавать второй репозиторий, отдельный монитор, не дублировать исторические OHLCV/тестеры. Не изменять FINAM, токены, production SQLite, реальные заявки, живые стратегии, Windows Tasks. Подпрограмма не меняет основной TRL Roadmap.

### Продолжение — R041 (11.11.2026)

[Отчёт R041 — OBV / Inside / новый Two-Leg и Sweep](TRL_R_2026_041_STS_OBV_Inside_New_Modules_Research.md) · [Правила, замороженные до проверки](experiments/R041_FROZEN_PROTOCOL.md) · [TRL Journal](../../journal/2026-11-11-sts-r041.md).

Результат: Two-Leg условно улучшает исторический трёхсчётный портфель при замене Inside и TP6+защита, но основная прибыль происходит **при пересечении с Classic**, а не в слабые дни; Sweep не прошёл. **Внедрение не разрешено, V20 сохраняется.** Код, csv и независимые проверки арифметики сохранены в архиве исследования R041; не запускать на LIVE.

## Новое исследование 11.11.2026: R042

[TRL-R-2026-042: Reclaim Retest и Volume Dry Reset](TRL_R_2026_042_STS_New_Modules_Research.md) — два заранее зафиксированных новых способа коррекции. Три отдельных счёта по 45k/500k/1m; замены OBV и Inside проверены на C1, GO Oct/Nov, BASE/TP6+защита. Ни один модуль пока не пригоден для замены: RETEST REJECT, DRY ARCHIVE_FORWARD_ONLY. [Замороженный протокол](experiments/r042/FROZEN_PROTOCOL.md). Полный воспроизводимый ZIP с офлайн-скриптами и историческими данными сохранён как артефакт исследования. LIVE неизменён.

## R043 — H1/H4 и двухдневная коррекция (11.11.2026)

[Отчёт R043](TRL_R_2026_043_STS_MTF_Staircase_Research.md) · [Frozen protocol](experiments/r043/FROZEN_PROTOCOL.md) · [Воспроизводимый код](experiments/r043/run_r043.py) · [Аудит](experiments/r043/audit_r043.py). Проверены две новые структуры: H1/H4 Ledge (313 BASE-сделок, PF R1,628) и Multi-Session Staircase (22 BASE, PF R2,826, но 2024/2026 убыточные и top5-зависимость). В трёх отдельных счетах ни одна не оправдала замену OBV/Inside. `NO_REPLACEMENT / LIVE_UNCHANGED`. Следующая проверка только с реальной новой независимой информацией, без подбора на старой истории.

## R045 — денежный риск и M15 equity (11.11.2026)

[Отчёт R045](TRL_R_2026_045_V20_vs_Shallow_MTM_Research.md) · [замороженный протокол](experiments/r045/FROZEN_PROTOCOL.md) · [общий Journal](../../journal/2026-11-11-sts-r045-v20-shallow-mtm.md). 60 historical offline сценариев, 20 точных денежных parity PASS. Три модели: A V20 45/45/45, B V20 60/30/45, C Shallow-only с единым капиталом (C не STS). Для 135k ГО Oct TP6: B +422224 ₽ / M15DD18667 ₽; C при риске 0,667% +404160 ₽ / M15DD16563 ₽. При GO Nov C 0,5% +285066 ₽ / M15DD11416 ₽ против B +283607 ₽ / M15DD15818 ₽. GO занимает почти весь банк, комиссия FINAM и истинная внутрисвечная MTM не проверены. **HOLD_FORWARD / KEEP_V20_LIVE**, Shallow-only low-risk оставить исследовательским кандидатом; объединение счетов STS НЕ одобрено.

## R046 — Inside и сигнальные пробелы ноября 2026

[Подробный R046](TRL_R_2026_046_Inside_and_Missed_Trends_Research.md) · [замороженные правила Drive](experiments/r046/FROZEN_PROTOCOL.md) · [Journal](../../journal/2026-11-11-sts-r046-inside-missed-trends.md). Из пользовательских M15 CSV за 9–10 ноября frozen Classic/OBV/Inside не дали raw сигналов по USD/CNY/IMOEX (по GLD frozen Shallow 3 и OBV 2); CSV обрываются 11.11 в 08:30, скрин 17:55 вне данных. Исследовательский Drive Continuation находит ноябрьские breakouts без коррекции, но исторически GO Oct TP6 PF1,506, 2026 YTD убыточен, при замене Inside портфельная DD примерно удваивается — `REJECT_CORE`.

Отдельно Shallow90k TP6+Inside45k TP6: +485202 ₽ / M15DD21827 ₽; с Inside BASE +510709 ₽ / M15DD22907 ₽, Oct GO, против V20 60/30/45 TP6 +422224 ₽ / M15DD18667 ₽. Inside положителен в 3/6 отрицательных месяцев Shallow90, не является постоянной защитой. **Двухсчётный Shallow+Inside — CANDIDATE_FOR_FORWARD, но LIVE V20 пока неизменна; V20 не объявлена оптимальной моделью.**

## R047 — Missed Trend Opportunities: почему пропускаются тренды

[Полный отчёт R047](TRL_R_2026_047_Missed_Trend_Opportunities.md) · [Фиксированный протокол](experiments/r047/FROZEN_PROTOCOL.md) · [Офлайн-код и аудит](experiments/r047/REPRODUCE_RU.md) · [Journal](../../journal/2026-11-11-sts-r047-missed-trends.md).

Из 779 ex-post трендовых эпизодов R031 **366** без принятого Classic-входа: **334** не имели RAW сигнала, **32** были отклонены исследовательскими ограничениями. Из 366 эпизодов **196** не охвачены даже четырьмя предыдущими альтернативами. Разметка ex-post — не causal trading label и не OOS.

Новые замороженные кандидаты: Early Trend Resume (до полного EMA50/200 подтверждения) и Tight Drift Break (короткая направленная пауза без обычного отката). В 3×45k Oct GO TP6 V20 +381608 ₽, PF1,845, closed DD11775 ₽; ни одна замена на эти модули не улучшила экономику. **Early 822 денежные сделки +13893 ₽ PF1,058** (C2 отрицательный), хотя в каталоге R031 найдено 156 пропущенных ex-post событий. **Tight 21 сделка +9906 ₽ PF2,757**, но лишь 1/366 пропущенных эпизодов и результат отрицательный после исключения top5 выигрышей. Решение: EARLY_REJECT_CORE / DRIFT_ARCHIVE_FORWARD / LIVE_UNCHANGED.

## R048 — Early Trend Quality (11.11.2026)

[Подробный R048](TRL_R_2026_048_Early_Trend_Quality_Research.md) · [замороженный протокол](experiments/r048/FROZEN_PROTOCOL.md) · [воспроизведение](experiments/r048/REPRODUCE_RU.md) · [запись Journal](../../journal/2026-11-11-sts-r048-early-quality.md).

Четыре предзаданных фильтра R047 Early (ER16, подтверждение пробоя закрытием, ограничение ATR, ER+acceptance) проверены полным replay на N4 2023–Sep2026, по отдельному счёту 45k, Oct/Nov GO proxy, BASE/TP6+защита, C1/C2/C4, пропущенные ex-post эпизоды и замена OBV/Inside в трёх отдельных капиталах. Лучший Oct TP6 Early+Acceptance: 623 сделки / +30262 ₽ / PF1,155 / closedDD18536 ₽. На C2 PF1,079, C4 результат отрицателен; 2023 убыточен. При замене Inside тройка +365362 ₽ / PF1,617 / closedDD15749 ₽ против V20 +381608 ₽ / PF1,845 / DD11775 ₽. 500 причинных тестов и 11444 independent cash checks PASS; 12 CSV независимого ZIP replay побайтно совпали. **REJECT_CORE / ARCHIVE_DIAGNOSTIC / LIVE_UNCHANGED**. Исходный R047 Early не давал 9–10 ноября USD/CNY сигналов, его фильтры не могут восполнить этот пробел.

## R049 — попытки начала тренда после сжатия диапазона

[Исследование](TRL_R_2026_049_Compression_Release_Research.md) · [оригинальный frozen-протокол](experiments/r049/FROZEN_PROTOCOL.md) · [Journal](../../journal/2026-11-11-sts-r049-compression.md). Два момента входа для **одного** механизма Compression Release (не два отдельных доказанных ядра). Oct GO 45k: BREAK BASE +27073 ₽ PF1.473, но убыточен 2025 и зависим от top5; BREAK TP6 +1314 ₽ PF1.024, HOLD TP6 +826 ₽ PF1.062 / 33 сделки. При GO Nov оба TP6 убыточны. Замены OBV/Inside на этих трех отдельных счетах не улучшают прибыль frozen V20. 718 проверок причинности, 654 арифметических сделок, 9 CSV совпали при автономном перепуске. **Решение `REJECT_CORE / ARCHIVE_MECHANISM / STS_CONTINUE / LIVE_UNCHANGED`**. Следующий приоритет: будущие данные после freeze и каталог всех попыток начала тренда, включая ложные, без нового подбора порогов на старой истории.

## R050 — причинный анализ всех стартов тренда (11.11.2026)

[Полный отчёт](TRL_R_2026_050_Trend_Start_Attempts_Research.md) · [frozen protocol](experiments/r050/FROZEN_PROTOCOL.md) · [Journal](../../journal/2026-11-11-sts-r050-trend-start-attempts.md). 2842 первые стартовые попытки по фиксированному пробою 16 предшествующих M15-баров; 2841 валидный двухчасовой исход: +0.5 ATR 1096 (38.6%), -0.5 ATR 1145 (40.3%), нейтрально 600. Качество закрытия свечи даёт +3.72 п.п. исторических продолжений, но не серьёзный trading edge. На 45k GO Oct TP6: START_ALL 1491 сделка +135340 ₽ PF1.296 DD19830 ₽; START_ACCEPT 1201 +113730 ₽ PF1.298 DD15743 ₽. Замена Inside увеличивает ₽ портфеля, но снижает PF и увеличивает DD на 64%. `REJECT_CORE / RETAIN_DIAGNOSTIC / LIVE_UNCHANGED`. Отдельный офлайн ZIP с исходными данными/кодом/журналом в отчёте разговора; R050 не OOS.

## R051 — месячная статистика V20 / капитал / GLD (11.11.2026)

[Исследовательский отчёт R051](TRL_R_2026_051_V20_Monthly_Allocation_GLD_Research.md) · [Journal](../../journal/2026-11-11-sts-r051-portfolio-monthly-gld.md). На SHA-verified R045 источниках заново исполнены 148 сценариев для N4/N3 без GLDRUBF, BASE/TP6+защита, ГО Oct/Nov, общий стартовый банк 135k ₽. 20/20 денежный parity PASS. Excel/полный CSV и автономный ZIP представлены в TRL-диалоге. В GO Oct/N4/TP6 Shallow+Inside 60/40 +461857 ₽ PF2.007 M15DD20035 ₽ (40/45 месяцев), 70/30 +496776 ₽ PF1.968 DD23939 ₽. Без GLD 60/40 +372736 ₽, M15DD22404 ₽; повышенные +30 тик/сторона GLD в FULL replay +420727 ₽, но реальная ликвидность не подтверждена. `SH_INSIDE_60_40_FORWARD_CANDIDATE / LIVE_UNCHANGED`. 2026 покрыт не полностью и TRUE OOS нет.

### R051 — месячный разрез, распределение капитала и исключение GLD

[Исследовательский отчёт R051](TRL_R_2026_051_Monthly_Portfolio_Allocation_GLD.md) · [Journal](../../journal/2026-11-11-sts-r051-monthly-portfolio-gld.md). Отдельная книга в TRL: 45 месяцев × 3 робота × N4 по двум выходам, двум статичным GO, с GLD и без; 148 повторных денежных сценариев, 20 exact parity PASS. Sh+Inside 60/40 N4 Oct TP6 = +461857 ₽ PF2.007 M15DD20035 ₽ (40/45 месяцев), Shallow-only low-risk 0.667% = +404160 PF1.995 DD16563 ₽. N3 без GLD не гарантирует снижения DD. `FORWARD_CANDIDATE / LIVE_UNCHANGED`.

### R052 — V20 independence, limit execution and Shallow versions (12.11.2026)

[R052 report](TRL_R_2026_052_V20_Independence_Limits_Shallow_Variants.md) · [frozen protocol](experiments/r052/FROZEN_PROTOCOL.md) · [Journal](../../journal/2026-11-12-sts-r052-independence-limit-shallow.md). Signal types differ, but all share EMA trend and FINAM/execution dependencies. Daily cash PnL corr Shallow–Inside 0.098, Shallow–OBV 0.344. Shallow window/depth four variants: FAST2 851 PF1.814; LONG5 542 PF1.829; DEEP3 894 PF1.850; TIGHT3 486 PF1.848 vs Classic 736 PF1.961 (45k Oct GO TP6). No new core approved. Limit NEXT_OPEN passive one-tick OHLC price touch 89.1% entry bar N4, versus 71.5% on next up-to-four M15 bars; touch is **not execution**, and cannot prove GLD fill. Need actual L2/prints/broker fills. Isolated replay 19 CSV PASS. TP6 future LIVE choice belongs to separate project; no LIVE changes here.

### R053 — три отдельных Shallow, три выхода, лимитные заявки (12.11.2026)

[Подробный R053](TRL_R_2026_053_Three_Shallow_and_Limits_Research.md) · [protocol](experiments/r053/FROZEN_PROTOCOL.md) · [Journal](../../journal/2026-11-12-sts-r053-three-shallow-limits.md). В GO Oct TP6+защита Classic/Fast2/Deep3 (3×45k) +638187 ₽ PF1.871 M15-closeDD28173 ₽/39 прибыльных месяцев; V20 45/45/45 +381608 ₽ PF1.845 DD16701 ₽/40. 102 дополнительные posthoc тренда без Classic (из 779), но Fast/Deep вне пересекающихся позиций Classic суммарно убыточны (−38337/−7564 ₽), одновременная коррелированная экспозиция велика. Выбор исследовательской архитектуры исполнения: capped aggressive IOC + book depth gate + стоп на фактический fill, без заявлений об исторически оптимальном fill. TP6+protect пользователь утвердил для будущей отдельной задачи LIVE. `HISTORICAL_NET_UP / NO_CORE_APPROVAL / LIVE_UNCHANGED`.

## R054 (12.11.2026) — 3 Shallow без дублирования
[Результаты R054](TRL_R_2026_054_Shallow_Gated_Risk_Parity_Report.md) · [исправление протокола](experiments/r054/PROTOCOL_CORRECTION.md) · [Journal](../../journal/2026-11-12-sts-r054-gated-risk-parity.md). Три самостоятельных 45k счёта Classic/Fast/Deep против двухсчётной Shallow+Inside60/40, 135k total, ex-ante риск ≤6%. Oct GO TP6+protect3: независимая тройка +638187 ₽ PF1.871 M15DD28173; синхронная blocking тройка +322282 ₽ PF1.785 M15DD13684; Sh+Inside60/40 +461857 ₽ PF2.007 M15DD20035. Первоначальная односторонняя gate имела структурный баг и отвергнута, итог **R054-B exploratory**, не независимый OOS. Включён аудит 9+18+4 parity и 13,827 ledger cash rows. Прежняя кандидатная лимитная схема: +1 тик, до 60 секунд, отменить остаток, без Market chase; IOC не ранее согласованный выбор. `NO_LIVE_CHANGE`.

## R055 — физическая коррекция Shallow и LIMIT DAY

[Отчёт R055](TRL_R_2026_055_Physical_Pullbacks_and_Limit_Orders.md) · [протокол](experiments/r055/FROZEN_PROTOCOL.md) · [Journal](../../journal/2026-11-12-sts-r055-physical-pullbacks-finam-limits.md). Восьми заранее зафиксированным вариантам физического отката удалось найти новые сигналы, но вне позиций Classic денежный вклад слабый: PB_DEEP3 +662 ₽, PB_LONG5 +5211 ₽ на 45k OctGO TP6+protect3. Ни один вариант не превзошёл Classic по исходному PF; ADX>=20 и растущий хуже без него. Ноябрьские безоткатные движения USD/CNY/IMOEX остались без новых RAW сигналов. По исполнению основной исследовательский вариант — обычная LIMIT DAY с предельной ценой, без обязательной отмены через 60 секунд; остаток нельзя оставлять после закрытия позиции/истечения сигнала. Не менять существующий стоп 100%, любые изменения LIVE только в профильном проекте. NO_NEW_CORE_APPROVAL / LIMIT_DAY_FORWARD_CANDIDATE.
