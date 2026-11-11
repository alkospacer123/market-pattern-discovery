# INITIAL STOP FORENSICS V1 — T3/H1 и T3/M15

**Более короткие стопы не удовлетворяют главному критерию ни в H1, ни в M15: отрицательных CLOSED-месяцев больше, худший месяц глубже.** Рост суммы собственных R не подтверждает денежного улучшения. Статус: **RESEARCH REPLAY PASS; CASH NET / RUB DD / CASH RETURN NOT_VALIDATED**. Только фиксированные альтернативы. Один Draft PR, без merge/auto-merge и без LIVE. Ретроспективный replay известного historical TRUE OOS не является новым независимым OOS.

## Источники, сверка и единицы

main на старте: `38489db7e69336548a583f968f13aab49c20913b`. PR557 `5836971e7ff8e472d8128c675c4f837b40a036ef`, PR518 `d85cf85083d6fea047a1a960c9ead441f7b4a6ed`. SHA источников и журналов проверены до вычислений; [SOURCE_MANIFEST.json](SOURCE_MANIFEST.json). H1 читается из git blob `50f1fd2178c18b7ab3bd969be82ad01f47a34745`, M15 — чистый checkout `f8486b446cf3d5f9f3cba6dfec32bdef8fd184c8`. Текущий H1 checkout данных имеет другие bytes и не использовался. Протокол зарегистрирован коммитом `b29400d1` до расчётов; [PROTOCOL_RU.md](PROTOCOL_RU.md).

Fresh CONTROL: 202418 полей frozen журналов, плюс 4385052 полей полного состояния PR557; ноль расхождений. H1 355 CLOSED /141 INITIAL_STOP, PF2.206747, +172.416620R (Baseline+historical OOS без WF). M15 1114/356, PF1.778435,+390.442918R. H1 WF63 CLOSED проверен отдельно. [CONTROL_RECONCILIATION.json](CONTROL_RECONCILIATION.json), [CSV](CONTROL_RECONCILIATION.csv).

H1: `TRAIL1__N4_01__FULL__R15`, `T3_H1_candidate_v3`; parameter SHA256 `4e73cdb77246cb07b5953160b9fc0ab36bfd4bd6d9a7f7faaae7e6e392ee340a`. Initial2.5/2.0/1.5 ATR, trail3.0 ATR, естественный +1R TRAIL1 и исходная задержка. M15: `T3_M15_T1_TRAIL35_N4_R15` / `T1_NEXT_OPEN_TRAIL_3p5`, Initial2.0/1.5 ATR, trail3.5. Completed signals [10:00,18:00) МСК; NEXT_OPEN только при adjacency. N4 неизменен: USDRUBF/CNYRUBF/GLDRUBF/IMOEXF.

Gross R каждого варианта имеет собственный Risk0. Уменьшение Risk0 само меняет знаменатель и +1R H1: такой рост R не доказывает рост денег. Общие сигналы дополнительно сравнены по цене выхода в CONTROL R0. H1 C1 =0.002/Risk0 round trip — нормированные исследовательские расходы, не брокерский Net; M15 GROSS_ONLY.

Все новые календарные таблицы — МСК. Frozen H1 UTC attribution использована только для reconciliation. H1 Baseline2023–2024 и historical OOS2025–2026 — отдельные cold-start циклы. Их объединённая строка является описательной суммой неперекрывающихся месяцев, DD/капитализация для неё не определены. WF folds не входят в неё. 2023 — частичный N4; 2026 — неполный срез, октябрь NO_DATA. Завершающие наблюдения: H1 до 16.09.2026 00:00 МСК; M15 USD/CNY до 30.08.2026 19:00, GLD/IMOEX до 16.09.2026 00:00.

## H1: календарный результат

| Initial variant | CLOSED | PF | E[R] | Gross R | C1 R | Win share | Avg win | Avg loss |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| CONTROL | 355 | 2.2067 | 0.4857 | 172.4166 | 169.8279 | 0.5662 | 1.5686 | -0.9278 |
| STOP_2p0 | 374 | 2.3023 | 0.5499 | 205.6808 | 202.3164 | 0.5080 | 1.9138 | -0.8584 |
| STOP_1p5 | 413 | 2.1064 | 0.5610 | 231.6789 | 226.9430 | 0.4140 | 2.5795 | -0.8653 |


### CLOSED_R, месяцы

| Variant | + | − | 0 | Worst R | Median R | Max − streak |
| --- | --- | --- | --- | --- | --- | --- |
| CONTROL | 28 | 15 | 2 | -4.2133 | 1.2177 | 3 |
| STOP_2p0 | 24 | 19 | 2 | -7.6928 | 0.8155 | 3 |
| STOP_1p5 | 25 | 18 | 2 | -7.5904 | 0.5722 | 3 |


- STOP_2p0: NEGATIVE→POSITIVE нет; POSITIVE→NEGATIVE 2024-05, 2024-08, 2025-06, 2026-04.
- STOP_1p5: NEGATIVE→POSITIVE 2024-12, 2025-02; POSITIVE→NEGATIVE 2024-05, 2024-08, 2025-06, 2025-08, 2026-04.

### MTM_R, месяцы

| Variant | + | − | 0 | Worst R | Median R | Max − streak |
| --- | --- | --- | --- | --- | --- | --- |
| CONTROL | 30 | 13 | 2 | -4.7643 | 2.5696 | 2 |
| STOP_2p0 | 27 | 16 | 2 | -8.0443 | 1.3090 | 3 |
| STOP_1p5 | 28 | 15 | 2 | -8.0591 | 1.5430 | 3 |


- STOP_2p0: NEGATIVE→POSITIVE нет; POSITIVE→NEGATIVE 2024-02, 2025-06, 2026-04.
- STOP_1p5: NEGATIVE→POSITIVE 2025-02; POSITIVE→NEGATIVE 2024-02, 2025-06, 2026-04.

### Отдельные cold-start циклы H1

| Lifecycle | Variant | Closed | PF | Gross R | Negative months |
| --- | --- | --- | --- | --- | --- |
| baseline | CONTROL | 171 | 2.3519 | 83.2408 | 9 |
| baseline | STOP_2p0 | 177 | 2.2881 | 91.8613 | 11 |
| baseline | STOP_1p5 | 194 | 2.1474 | 106.2302 | 10 |
| historical_true_oos | CONTROL | 184 | 2.0968 | 89.1758 | 6 |
| historical_true_oos | STOP_2p0 | 197 | 2.3140 | 113.8195 | 8 |
| historical_true_oos | STOP_1p5 | 219 | 2.0738 | 125.4487 | 8 |

### WF — каждый fold отдельно, без включения в основные итоги

| Fold | Variant | Closed | PF | Gross R | Negative months | Closed DD R | MTM DD R |
| --- | --- | --- | --- | --- | --- | --- | --- |
| WF01 | CONTROL | 12 | 1.8646 | 4.3230 | 1 | 2.2620 | 3.1418 |
| WF01 | STOP_2p0 | 12 | 2.1315 | 5.6967 | 1 | 3.0345 | 4.2208 |
| WF01 | STOP_1p5 | 14 | 1.0326 | 0.2670 | 1 | 4.3498 | 5.6209 |
| WF02 | CONTROL | 19 | 5.0083 | 24.2370 | 0 | 2.4050 | 4.4350 |
| WF02 | STOP_2p0 | 20 | 4.4034 | 27.2270 | 0 | 2.1978 | 4.7352 |
| WF02 | STOP_1p5 | 21 | 5.5078 | 36.7877 | 0 | 2.6574 | 4.6177 |
| WF03 | CONTROL | 18 | 2.7017 | 6.8069 | 0 | 2.3116 | 3.0731 |
| WF03 | STOP_2p0 | 18 | 3.0697 | 8.2786 | 0 | 2.1395 | 3.7049 |
| WF03 | STOP_1p5 | 19 | 2.4937 | 8.6385 | 0 | 2.5627 | 5.1393 |
| WF04 | CONTROL | 14 | 5.7632 | 11.8201 | 1 | 2.0596 | 6.3491 |
| WF04 | STOP_2p0 | 15 | 3.6507 | 12.1984 | 1 | 2.3177 | 7.4364 |
| WF04 | STOP_1p5 | 15 | 5.0411 | 17.9568 | 0 | 2.0993 | 9.2485 |


### Просадка отдельных жизненных циклов

| Lifecycle | Variant | CLOSED DD R | Completed MTM DD R |
| --- | --- | --- | --- |
| baseline | CONTROL | 10.5175 | 11.7577 |
| baseline | STOP_2p0 | 10.7903 | 12.7185 |
| baseline | STOP_1p5 | 14.9989 | 17.5698 |
| historical_true_oos | CONTROL | 14.1403 | 14.5007 |
| historical_true_oos | STOP_2p0 | 7.7020 | 10.7320 |
| historical_true_oos | STOP_1p5 | 18.2250 | 19.9813 |


### Initial Stop, trailing и крупные победители

| Variant | Initial count | Initial R | Trailing count | Trailing R | Trailing losses | Top5 R | Top10 R |
| --- | --- | --- | --- | --- | --- | --- | --- |
| CONTROL | 141 | -141.3090 | 214 | 313.7256 | 13 | 45.2574 | 69.7581 |
| STOP_2p0 | 150 | -150.0460 | 224 | 355.7268 | 34 | 56.5718 | 86.3190 |
| STOP_1p5 | 183 | -183.7692 | 230 | 415.4481 | 59 | 73.7405 | 113.3996 |


### A. Что наблюдается перед первоначальным стопом

**OBSERVED:** 141 INITIAL_STOP. Доказанное отсутствие +0.5R до стопа: 94 (66.7%); ещё 0 случаев неопределённы на exit bar. EARLY_ADVERSE_MOVE: 118 (83.7%). Преобладающее наблюдение — раннее adverse движение; низкий follow-through также частый и пересекающийся признак. Эти категории пересекаются и не доказывают ошибку сигнала. Результат зависит от выбранных формальных порогов.

- MFE +0.5R: до стопа 47, AMBIGUOUS 0, не наблюдалось 94.
- MFE +1.0R: до стопа 0, AMBIGUOUS 0, не наблюдалось 141.
- MFE +1.5R: до стопа 0, AMBIGUOUS 0, не наблюдалось 141.
- MFE +2.0R: до стопа 0, AMBIGUOUS 0, не наблюдалось 141.

Удержание execution bars: {'1': 3, '2-4': 23, '5-8': 28, '9-16': 30, '>16': 57}. День выхода: {'LATER': 38, 'NEXT_OBSERVED_TRADING_DAY': 56, 'ENTRY_DAY': 47}. Immediate adverse Open: 48; adverse Close первой пережитой свечи: 94; −0.5R за первые 4 бара: 71.

Из 141 H1 INITIAL_STOP только 3 приходятся на первую допустимую свечу; 57 держались более 16 свечей. Ранний adverse признак не означает мгновенное выбивание: значим и последующий слабый follow-through.

Post-stop 1 полных следующих observed trading day(s): CENSORED 2/141; entry recovery 53; −1.5R continuation 98; порядок {'NEITHER_OBSERVED': 15, 'RECOVERY_ONLY_OBSERVED': 28, 'ADVERSE_FIRST': 8, 'RECOVERY_FIRST': 16, 'ADVERSE_ONLY_OBSERVED': 73, 'AMBIGUOUS_SAME_BAR': 1}.
Post-stop 2 полных следующих observed trading day(s): CENSORED 2/141; entry recovery 67; −1.5R continuation 104; порядок {'RECOVERY_ONLY_OBSERVED': 30, 'RECOVERY_FIRST': 19, 'ADVERSE_FIRST': 17, 'ADVERSE_ONLY_OBSERVED': 67, 'AMBIGUOUS_SAME_BAR': 1, 'NEITHER_OBSERVED': 7}.

| Days | Censored | Entry | +0.5R | +1R | +1.5R | +2R | −1.5R | −2R | Entry-touch bars | Close crossings |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 1 | 2 | 53 | 28 | 15 | 6 | 4 | 98 | 57 | 223 | 99 |
| 2 | 2 | 67 | 41 | 26 | 16 | 9 | 104 | 71 | 369 | 163 |

Наблюдаемые hits включают известные hits в CENSORED-окнах; отсутствие hit в таких окнах не признано отрицательным результатом.


| Variant | MFE−exit R0 | Positive MFE returned R0 | Loss below entry R0 |
| --- | --- | --- | --- |
| CONTROL | 474.3541 | 331.4769 | 142.8772 |
| STOP_2p0 | 569.7834 | 411.8446 | 157.9388 |
| STOP_1p5 | 739.8898 | 530.4821 | 209.4078 |

MFE−exit включает возврат положительного MFE и последующий убыток ниже entry; прибыль, возвращённая рынку, показана отдельно. Все величины здесь в собственном Risk0 варианта.


### B–C. Изменённые убытки и потерянные победители

STOP_2p0: из 141 исходных INITIAL_STOP на более ранней свече закрыто 75, цена выхода улучшилась в CONTROL R0 у 141, собственный R улучшился у 15, в прибыль перешло 2. Same-bar exits не считаются доказанно более ранними по wall-clock. Gross сумма собственных R изменилась на +19.29%; это не изменение cash-return.
STOP_2p0, исходные top-5: CONTROL 45.2574R; matched variant exits 45.2574 CONTROL R0; несопоставимых/OPEN 0.
STOP_2p0, исходные top-10: CONTROL 69.7581R; matched variant exits 64.6046 CONTROL R0; несопоставимых/OPEN 0.
STOP_2p0: TRAIL1 активирован раньше на 121 общих сигналах; 29 trailing exits произошли до CONTROL activation. Их сумма изменения цены выхода -13.3882 CONTROL R0. Это вклад группы с механически более ранним trailing; отдельный causal PnL эффект активации и initial distance не идентифицирован без дополнительной модели. Все trigger/activation timestamps приведены в comparison CSV.
STOP_1p5: из 141 исходных INITIAL_STOP на более ранней свече закрыто 105, цена выхода улучшилась в CONTROL R0 у 141, собственный R улучшился у 27, в прибыль перешло 2. Same-bar exits не считаются доказанно более ранними по wall-clock. Gross сумма собственных R изменилась на +34.37%; это не изменение cash-return.
STOP_1p5, исходные top-5: CONTROL 45.2574R; matched variant exits 34.4781 CONTROL R0; несопоставимых/OPEN 0.
STOP_1p5, исходные top-10: CONTROL 69.7581R; matched variant exits 53.8253 CONTROL R0; несопоставимых/OPEN 0.
STOP_1p5: TRAIL1 активирован раньше на 162 общих сигналах; 49 trailing exits произошли до CONTROL activation. Их сумма изменения цены выхода -13.9952 CONTROL R0. Это вклад группы с механически более ранним trailing; отдельный causal PnL эффект активации и initial distance не идентифицирован без дополнительной модели. Все trigger/activation timestamps приведены в comparison CSV.

| Variant | Common | Loss earlier | Loss price improved | Loss→win | Wins→loss | New | Missed | Total ΔownR | Lost winner profit share |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| STOP_2p0 | 357 | 77 | 141 | 2 | 23 | 19 | 1 | 33.2642 | 0.1613 |
| STOP_1p5 | 358 | 109 | 141 | 2 | 53 | 56 | 0 | 59.2623 | 0.3479 |


Lost winner profit share = сумма ухудшения цены выхода исходных победителей в CONTROL R0 / сумма положительных CONTROL R, только общие закрытые сигналы; улучшения других сделок её не компенсируют. Пропуски и OPEN показаны отдельно. ΔownR сравнивает суммы собственных R и не является денежной доходностью. [LOST_WINNERS.csv](LOST_WINNERS.csv), [LARGE_WINNERS.csv](LARGE_WINNERS.csv), [NEW_AND_MISSED_ENTRIES.csv](NEW_AND_MISSED_ENTRIES.csv).

### D–F. Вердикт для владельца

**STOP_2p0: по главному критерию укорочение не оправдано.** CLOSED negative 15→19 (исчезло 0, появилось 4); MTM negative 13→16. Худший CLOSED-месяц -4.2133→-7.6928R. PF 2.2067→2.3023, expectancy 0.4857→0.5499R; рост ownR не компенсирует ухудшение количества и глубины отрицательных месяцев. Денежный Net отсутствует.
**STOP_1p5: по главному критерию укорочение не оправдано.** CLOSED negative 15→18 (исчезло 2, появилось 5); MTM negative 13→15. Худший CLOSED-месяц -4.2133→-7.5904R. PF 2.2067→2.1064, expectancy 0.4857→0.5610R; рост ownR не компенсирует ухудшение количества и глубины отрицательных месяцев. Денежный Net отсутствует.

**REPLAY_CONFIRMED:** месячные переходы, изменения PF/expectancy/DD, новые/пропущенные входы и потерянные победители подтверждены полным replay сигналов, занятости и стопов. Исходные сделки не заменялись MAE-эвристикой. Показатели DD нужно оценивать по каждому cold-start циклу, CLOSED и MTM отдельно.

**HYPOTHESIS:** малый follow-through, раннее adverse движение и post-stop recovery описывают пути цены; они не устанавливают рыночную ошибку и не дают причинного нового фильтра. Один удачный набор месяцев/PF недостаточен для выбора стопа. Исполнимый Net не подтверждён; автоматический переход не обоснован. Окончательное решение — владельцу после просмотра потерь крупных победителей и месячных таблиц.

## M15: календарный результат

| Initial variant | CLOSED | PF | E[R] | Gross R | C1 R | Win share | Avg win | Avg loss |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| CONTROL | 1114 | 1.7784 | 0.3505 | 390.4429 | — | 0.4201 | 1.9060 | -0.7776 |
| STOP_1p5 | 1183 | 1.6423 | 0.3621 | 428.4143 | — | 0.3584 | 2.5835 | -0.8800 |


### CLOSED_R, месяцы

| Variant | + | − | 0 | Worst R | Median R | Max − streak |
| --- | --- | --- | --- | --- | --- | --- |
| CONTROL | 35 | 10 | 0 | -10.2299 | 5.7248 | 2 |
| STOP_1p5 | 33 | 12 | 0 | -15.0600 | 7.2997 | 2 |


- STOP_1p5: NEGATIVE→POSITIVE 2024-06, 2026-04; POSITIVE→NEGATIVE 2024-04, 2024-10, 2025-01, 2025-04.

### MTM_R, месяцы

| Variant | + | − | 0 | Worst R | Median R | Max − streak |
| --- | --- | --- | --- | --- | --- | --- |
| CONTROL | 34 | 11 | 0 | -10.2299 | 6.5873 | 2 |
| STOP_1p5 | 34 | 11 | 0 | -15.0600 | 7.3135 | 1 |


- STOP_1p5: NEGATIVE→POSITIVE 2024-06, 2026-04; POSITIVE→NEGATIVE 2024-10, 2025-04.

### Просадка отдельных жизненных циклов

| Lifecycle | Variant | CLOSED DD R | Completed MTM DD R |
| --- | --- | --- | --- |
| history_2023_2026 | CONTROL | 17.1981 | 20.9131 |
| history_2023_2026 | STOP_1p5 | 36.6501 | 36.7223 |


### Initial Stop, trailing и крупные победители

| Variant | Initial count | Initial R | Trailing count | Trailing R | Trailing losses | Top5 R | Top10 R |
| --- | --- | --- | --- | --- | --- | --- | --- |
| CONTROL | 356 | -356.0531 | 758 | 746.4960 | 289 | 62.1428 | 104.5518 |
| STOP_1p5 | 567 | -567.2617 | 616 | 995.6760 | 191 | 82.8571 | 139.2526 |


### A. Что наблюдается перед первоначальным стопом

**OBSERVED:** 356 INITIAL_STOP. Доказанное отсутствие +0.5R до стопа: 288 (80.9%); ещё 10 случаев неопределённы на exit bar. EARLY_ADVERSE_MOVE: 336 (94.4%). Преобладающее наблюдение — раннее adverse движение; низкий follow-through также частый и пересекающийся признак. Эти категории пересекаются и не доказывают ошибку сигнала. Результат зависит от выбранных формальных порогов.

- MFE +0.5R: до стопа 58, AMBIGUOUS 10, не наблюдалось 288.
- MFE +1.0R: до стопа 1, AMBIGUOUS 4, не наблюдалось 351.
- MFE +1.5R: до стопа 0, AMBIGUOUS 1, не наблюдалось 355.
- MFE +2.0R: до стопа 0, AMBIGUOUS 0, не наблюдалось 356.

Удержание execution bars: {'1': 32, '2-4': 133, '5-8': 105, '9-16': 75, '>16': 11}. День выхода: {'ENTRY_DAY': 356}. Immediate adverse Open: 0; adverse Close первой пережитой свечи: 237; −0.5R за первые 4 бара: 314.

В M15 270/356 INITIAL_STOP наступили за первые 8 execution bars (75.8%); 32 на первой свече. Здесь early adverse и low follow-through чаще сопровождаются коротким удержанием.

Post-stop 1 полных следующих observed trading day(s): CENSORED 1/356; entry recovery 272; −1.5R continuation 294; порядок {'ADVERSE_ONLY_OBSERVED': 82, 'ADVERSE_FIRST': 128, 'RECOVERY_ONLY_OBSERVED': 60, 'RECOVERY_FIRST': 82, 'NEITHER_OBSERVED': 2, 'AMBIGUOUS_SAME_BAR': 2}.
Post-stop 2 полных следующих observed trading day(s): CENSORED 1/356; entry recovery 286; −1.5R continuation 306; порядок {'ADVERSE_ONLY_OBSERVED': 70, 'ADVERSE_FIRST': 141, 'RECOVERY_ONLY_OBSERVED': 50, 'RECOVERY_FIRST': 93, 'AMBIGUOUS_SAME_BAR': 2}.

| Days | Censored | Entry | +0.5R | +1R | +1.5R | +2R | −1.5R | −2R | Entry-touch bars | Close crossings |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 1 | 1 | 272 | 234 | 191 | 164 | 137 | 294 | 232 | 2625 | 1268 |
| 2 | 1 | 286 | 262 | 230 | 206 | 186 | 306 | 260 | 3551 | 1693 |

Наблюдаемые hits включают известные hits в CENSORED-окнах; отсутствие hit в таких окнах не признано отрицательным результатом.


| Variant | MFE−exit R0 | Positive MFE returned R0 | Loss below entry R0 |
| --- | --- | --- | --- |
| CONTROL | 1660.1390 | 1158.5646 | 501.5745 |
| STOP_1p5 | 2129.2297 | 1462.2224 | 667.0073 |

MFE−exit включает возврат положительного MFE и последующий убыток ниже entry; прибыль, возвращённая рынку, показана отдельно. Все величины здесь в собственном Risk0 варианта.


### B–C. Изменённые убытки и потерянные победители

STOP_1p5: из 356 исходных INITIAL_STOP на более ранней свече закрыто 194, цена выхода улучшилась в CONTROL R0 у 356, собственный R улучшился у 1, в прибыль перешло 0. Same-bar exits не считаются доказанно более ранними по wall-clock. Gross сумма собственных R изменилась на +9.73%; это не изменение cash-return.
STOP_1p5, исходные top-5: CONTROL 62.1428R; matched variant exits 62.1428 CONTROL R0; несопоставимых/OPEN 0.
STOP_1p5, исходные top-10: CONTROL 104.5518R; matched variant exits 95.7057 CONTROL R0; несопоставимых/OPEN 0.

| Variant | Common | Loss earlier | Loss price improved | Loss→win | Wins→loss | New | Missed | Total ΔownR | Lost winner profit share |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| STOP_1p5 | 1114 | 267 | 419 | 0 | 67 | 69 | 0 | 37.9714 | 0.1830 |


Lost winner profit share = сумма ухудшения цены выхода исходных победителей в CONTROL R0 / сумма положительных CONTROL R, только общие закрытые сигналы; улучшения других сделок её не компенсируют. Пропуски и OPEN показаны отдельно. ΔownR сравнивает суммы собственных R и не является денежной доходностью. [LOST_WINNERS.csv](LOST_WINNERS.csv), [LARGE_WINNERS.csv](LARGE_WINNERS.csv), [NEW_AND_MISSED_ENTRIES.csv](NEW_AND_MISSED_ENTRIES.csv).

### D–F. Вердикт для владельца

**STOP_1p5: по главному критерию укорочение не оправдано.** CLOSED negative 10→12 (исчезло 2, появилось 4); MTM negative 11→11. Худший CLOSED-месяц -10.2299→-15.0600R. PF 1.7784→1.6423, expectancy 0.3505→0.3621R; рост ownR не компенсирует ухудшение количества и глубины отрицательных месяцев. Денежный Net отсутствует.

**REPLAY_CONFIRMED:** месячные переходы, изменения PF/expectancy/DD, новые/пропущенные входы и потерянные победители подтверждены полным replay сигналов, занятости и стопов. Исходные сделки не заменялись MAE-эвристикой. Показатели DD нужно оценивать по каждому cold-start циклу, CLOSED и MTM отдельно.

**HYPOTHESIS:** малый follow-through, раннее adverse движение и post-stop recovery описывают пути цены; они не устанавливают рыночную ошибку и не дают причинного нового фильтра. Один удачный набор месяцев/PF недостаточен для выбора стопа. Исполнимый Net не подтверждён; автоматический переход не обоснован. Окончательное решение — владельцу после просмотра потерь крупных победителей и месячных таблиц.

## Полная доказательная таблица и ограничения

Каждая CONTROL и alternative сделка имеет signal/entry/exit times, entry/ATR/stop/Risk0, exit type, costs, MAE/MFE, first excursion bounds, held bars, wall-clock и observed trading minutes. [H1_TRADE_FORENSICS.csv](H1_TRADE_FORENSICS.csv), [M15_TRADE_FORENSICS.csv](M15_TRADE_FORENSICS.csv). [H1_BAR_PATH.csv.gz](H1_BAR_PATH.csv.gz) / [M15_BAR_PATH.csv.gz](M15_BAR_PATH.csv.gz) содержат запрошенные High/Low во время позиций, нормированные экстремумы, gaps, stop entering/next/candidate и статус trail; это торговые диагностические события, не копия исходных OHLCV. Полные causal state journals сохранены отдельно.

H1 entry-bar H/L исключены; M15 execution bar доступна стопу. На exit bar favourable High/Low не признаётся достигнутым до стопа: guaranteed MFE использует пережитые bars и известный Open; observed upper bound сохраняется отдельно. Для первого intrabar excursion timestamp — верхняя граница интервала. Frozen exit label — Close даже при Open fill; actual_exit_time_lower/upper и exposure lower/upper показывают эту неопределённость.

Post-stop начинается со следующей свечи после стопа, использует CONTROL R0. Окно включает остаток текущего дня и 1/2 следующих полных наблюдаемых даты Open МСК; конец последней даты подтверждается наличием следующей даты в истории. Без exchange calendar это не доказательство полного биржевого покрытия. Entry-touch count — число наблюдаемых баров с entry в диапазоне; completed-close crossings считаются отдельно; количество реальных внутрисвечных пересечений UNKNOWN. Same-bar first recovery/adverse = AMBIGUOUS, если Open не установил порядок. Отсутствие полного окна = CENSORED. [POST_STOP_1D_2D.csv](POST_STOP_1D_2D.csv).

Помесячные CLOSED/MTM и C1: [STOP_VARIANT_MONTHLY.csv](STOP_VARIANT_MONTHLY.csv). Статистика всех отдельных циклов и WF folds: [STOP_VARIANT_SUMMARY.csv](STOP_VARIANT_SUMMARY.csv). [MONTH_SIGN_TRANSITIONS.csv](MONTH_SIGN_TRANSITIONS.csv). NO_DATA не включается в знаменатель и не превращается в 0; переносы открытых позиций отмечены в monthly и marks. MTM sum ffill использует только последнюю наблюдаемую цену, включая устаревшую отметку инструмента после его последнего бара; это раскрыто, цены не интерполированы.

## Денежная исполнимость

R15=1.5% realized equity на новую позицию, номинальный совокупный лимит 6% сохранён. Static registry содержит ticks USD0.01/10RUB, CNY0.001/1RUB, GLD0.1/0.1RUB, IMOEX0.5/5RUB; lot granularity1. Это подтверждённый статический snapshot, не полная историческая authority.

Frozen research stops off-grid не округлялись. В [CAPITAL_FEASIBILITY.csv](CAPITAL_FEASIBILITY.csv) отдельно дана чувствительность outward rounding и изменения Risk0/однолотового риска по static specs; [STOP_GRID_SUMMARY.csv](STOP_GRID_SUMMARY.csv) — off-grid initial/trailing observations. Результат на округлённой сетке не представлен как executable backtest. Qty=floor(min(risk budget/risk per lot, available margin/dated GO)), дополнительно ограничение общего reserved risk 6%; без капитала, dated GO и спецификаций qty неизвестен. Нельзя автоматически умножать Gross R на 1.5%.

Полных рядов initial equity/cashflows, исторического ГО, спецификаций/tick value и документированных fees/slippage/funding нет. **Executable Net, рублёвая просадка и cash-return NOT_VALIDATED.** H1 C1 не заменяет эти расходы. Данные FINAM, токены, LIVE SQLite, Windows Tasks, production H1/M15 и Control Center не запускались и не менялись.

## Аудит и воспроизводимость

Синтетические тесты: 30 PASS. Отдельный verifier заново проверяет все trade/signal/stop/marks, stdlib M15 features, forensic observations, post-stop и CSV/Decimal арифметику календаря. [AUDIT.json](AUDIT.json). Независимость — отдельный verifier agent и существующие scalar authority; human external audit PENDING. После code freeze выполняются минимум два свежих полных повтора, direct bytes + SHA256 всех generated artifacts; [REPEATABILITY.json](REPEATABILITY.json), [SHA256SUMS](SHA256SUMS).

Остановка на Draft PR. Никакого LIVE изменения и рекомендации автоматического перехода.
