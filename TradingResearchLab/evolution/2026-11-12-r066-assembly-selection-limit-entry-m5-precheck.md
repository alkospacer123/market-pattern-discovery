# TRL-R066 — выбор целевой сборки V20 и M5-предпроверка лимитных входов

**Дата:** 12.11.2026. **Статус:** `TARGET_ASSEMBLY_SELECTED_RESEARCH / M5_PRICE_TOUCH_AUDIT_PASS / FULL_LIMIT_CASH_REPLAY_PENDING / LIVE_UNCHANGED`.

## Выбор целевой сборки

**Research target — V20 Shallow60k / OBV30k / Inside45k + TP6+Protect3 + EXT2_NOOPP_BOTH_3SYMS** (135k общий банк, отдельные счета). EXT2 применяется только к Shallow/OBV на CNY/USD/GLD, не Inside/IMOEX. Замороженная LIVE V20 45/45/45 BASE без TP6 остаётся отдельным действующим эталоном и не меняется.

| Исторический R060–R061 OCT GO/C1, 135k | Net ₽ | PF | Мес +/45 | Max M15-close DD ₽ |
|---|---:|---:|---:|---:|
| **V20 60/30/45 + EXT2** | **443168.20** | 2.002896 | **43** | **18666.90** |
| Shallow83.0769/Inside51.9231 + MOM8 | 503504.20 | **2.138506** | 41 | 20530.20 |
| Shallow-only 135k TP6 baseline R051 | 666386.60 | 1.991 | 39 | 33484 |

V20 выбран при приоритете месячной регулярности, меньшей M15 DD и более сбалансированного риска; это **не** утверждение его превосходства по всем метрикам. На новых доступных свечах 16.09–12.11 V20+EXT2 OCT C1 +20709.9 ₽/PF2.110/DD8764.2, Shallow83/52+MOM8 +20905.7 ₽/PF1.974/DD11776.8. Цель PF2025 >=1.7 ещё НЕ достигнута (V20+EXT2 PF2025≈1.6245 при C1). TP6, защита и EXT2 не установлены в действующих LIVE роботах; исследованная история не TRUE OOS. Сохранять финалистов как ref, не подбирать новые пороги по 2023–2026.

## Источники лимитного анализа

Original R060 cash ledger: `OCT2026_PROXY/V20_603045/EXT2_NOOPP_BOTH_3SYMS`, **1436** исполненных market-NEXT_OPEN сделок. Из Library смонтированы **4 исторических N4 M5**: CNY/GLD/IMOEX/USD из GitHub `alkospacer123/market-pattern-data/forever/<symbol>/<symbol>_M5.csv`. Размер и SHA256 оригиналов в R066 манифесте. **1377/1436 (95.89%)** точных M5 timestamp, **0 тиков** расхождение между M5 Open и модельной ценой M15 NEXT_OPEN. 59 без точного M5: CNY46, GLD3, IMOEX3, USD7; CNY M5 заканчивается 30.04.2026, не равняться с новой историей 2026 целиком.

## M5 price-touch preliminary ONLY — НЕ fill rates

Берём entry reference=P0 из исполнимой исторической market-версии. Для BUY лимит на тик лучше=P0−tick, для SELL=P0+tick. До исходного exit timestamp и в течение N минут от entry: M5 LOW<=limit или HIGH>=limit — `TOUCH`; ниже/выше лимита дополнительно на 1 tick — `PENETRATION`. Это **только верхняя граница возможности**, M5 bar содержит всю пяти-минутку и не фиксирует очередь/latency/события внутри бара. В консервативной чувствительности исключается первая 5-минутная свеча.

**Из 1377 точно сопоставленных исходных входов:**
- 5min, включая first M5, P0 better 1tick: **1070/1377=77.71% TOUCH**, 946/1377=68.70% PENETRATION.
- 15min, включая first M5: **1171/1377=85.04% TOUCH**, **1092/1377=79.30% PENETRATION**.
- 15min, только после 5min задержки: **947/1377=68.77% TOUCH**, **899/1377=65.29% PENETRATION**.
- Для задержанных 5–15min TOUCH исходно прибыльные market сделки **62.69% (528 в базе)**, исходно убыточные **72.56% (849 в базе)**. **Риск adverse selection**: пассивная цена встречается чаще при будущих проигрышах и может пропускать сильные победные продолжения. Динамику последующих сделок/GO/стоп/TP не пересчитали — не приписывать этой доле реальный fill rate или прибыль.
- 15min touch P0 better1tick по символам (совпавшие M5): CNY313/385=81.30%, GLD365/416=87.74%, IMOEX232/264=87.88%, USD261/312=83.65%. Для GLD это особенно НЕ доказательство ликвидности или полных fills.

## Полный тест лимитов — необходимые условия до выбора

Четыре режима при одинаковых сигналах+TP6/EXT2:
1. `MARKET_NEXT_OPEN`: подтверждённый R060 cash baseline.
2. `LIMIT_P0`: по опорной цене рынка (BUY P0, SELL P0), с полным отсутствием гарантированного исполнения.
3. `LIMIT_AGGRESSIVE_1T`: BUY P0+tick / SELL P0−tick как ограничение цены, **не утверждать заполнение**, если нет достоверной ask/bid.
4. `SPLIT_50_50`: часть LIMIT_AGGRESSIVE и часть LIMIT_P0 или пассивный P0±tick, с отдельным журналом каждой дочерней заявки/исполнения, отменой остатка по timeout и optional market fallback как отдельный сценарий.

Окна ожидания 5/10/15min; закрытие всех неподтверждённых pending заявок до ограничений сессии; no future OHLC/5min close at order placement; adverse drift, пропущенные TP6 большие winners, последующее занятие GO, целые лоты, partial fill, стоп и TP по **фактическому** исполненному объёму/средней цене; PF, ₽, сделки, +месяцы, M15/DD, 2025 PF, GLD stop slippage/commission. Не переносить готовые market exits механически на задержанные лимиты. Без исторических bid/ask/trades/order log **полного достоверного сравнительного заполнения пассивных и частичных лимитов нет**; M5 только optimistic/pessimistic bounds. FINAM в ответе владельцу подтвердил, что order может исполниться несколькими trades с одним order_id и разными trade_id и что /orders, /trades, состояние счёта не атомарны. Подтверждена дневная судьба DAY лимитов. Официальные public docs: https://api.finam.ru/docs/rest/ и https://www.moex.com/a2863 .

## Вывод

**Решение по составу Research: SELECT V20_603045_EXT2_TP6_PROTECT3**. **Решение по лимитам: HOLD / M5 price-touch precheck complete / robust causal cash+orderbook proof not done.** До доказанного преимущества оставить MARKET как эталон исполнения. Никакого технического изменения LIVE, задач, production SQLite, токенов, API POST/DELETE. Реализация новой заявки/partial-fill recovery — только отдельный LIVE проект после research approval.

**Воспроизводимые артефакты:** `TRL-R066-Assembly-Decision-and-M5-Limit-Precheck.md` SHA256 `97385270e703991d2c423aa7e8ec950659a09eb228e063c33ba5b8a7633d5e9f`; ZIP `TRL-R066-Limit-M5-Precheck-Reproducible.zip` SHA256 `1780bf3a028237ef9165c465a6a7f2f373f5860d16603fc91366d9e53563bfbe` (4 original M5 files, cash ledger R060, Python audit, per-trade and summary CSV, checksum manifest); independent clean-folder rerun PASS. **LIVE changes = 0.**
