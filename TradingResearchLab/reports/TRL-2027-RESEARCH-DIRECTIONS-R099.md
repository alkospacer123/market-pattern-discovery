# TRL — направления исследований 2027 и предварительный тест R099

**Дата среза:** 26.11.2026.  
**Базовый MAIN:** `f0d289bd64536975dbcf3ec25ed1811c06116119`.  
**Режим:** AUTHORIZED_OFFLINE_RESEARCH / RESEARCH_ONLY.  
**Статус R099:** **REJECT_CURRENT_BASELINE**.  
**Статус расчёта:** `REPRODUCIBLE_VERIFIED` для двух byte-identical offline-запусков и дополнительной независимой векторизованной сверки ledger/HAC.  
**V20 / FINAM / production / капитал / LIVE:** не изменялись.

## 1. Решение для владельца

1. **R099 отклонён без постфактум-оптимизации.** Положительная статистическая зависимость первого и последнего получасовых интервалов USDRUBF не превратилась в торговое преимущество: Net C2 составил **−25 440 ₽ на 1 лот**, PF C2 — **0,5277**, все четыре календарных сегмента убыточны.
2. **Не продолжать этот baseline** подбором session time, порога, long-only/short-only, стопов или фильтров. Такие действия после известного результата потребуют нового ID и будут новым development, а не подтверждением R099.
3. **На 2027 год приоритет отдать новым механизмам и качеству данных:** cross-asset lead-lag, самостоятельному среднесрочному trend/volatility исследованию на расширенной истории, event-based post-shock drift, фактическому исполнению и forward-only untouched данным.
4. **Положительный результат на 2023–2026 сам по себе не будет кандидатом.** История уже многократно использована; нужен новый frozen protocol, экономический запас, robustness и действительно новый forward/untouched участок.
5. **Никаких изменений V20 по итогам R099.** Исследование не связано с TP6, Protect3, HOLD5, EXT2 или распределением 60/30/45 и не даёт основания менять их.

## 2. Что было изучено и как выбрана гипотеза

Учтены genealogy V1–V24 и доступные первичные документы R040–R098: opening-range/first-hour идеи, compression/squeeze, retest, ранние входы, MOM8/EXT2, trailing, HOLD5, капитал/ГО/лоты и ограничения исполнения. Для V1–V24 часть архивов отсутствует, поэтому полная новизна любой intraday-конструкции не может быть доказана по одному реестру.

Научное основание выбранного направления:

- Elaut, Frommel, Lampaert, *Intraday momentum in FX markets: Disentangling informed trading from liquidity provision*, Journal of Financial Markets, DOI [10.1016/j.finmar.2016.05.004](https://doi.org/10.1016/j.finmar.2016.05.004). Работа непосредственно исследует транзакции RUB/USD MICEX 2005–2014 и связывает intraday momentum прежде всего с liquidity demand и нежеланием поставщиков ликвидности нести overnight risk.
- Gao, Han, Li, Zhou, *Market intraday momentum*, Journal of Financial Economics 129(2), 2018, DOI [10.1016/j.jfineco.2018.05.009](https://doi.org/10.1016/j.jfineco.2018.05.009). Общий механизм первого/последнего получасового интервала, но не доказательство эффекта на MOEX 2023–2026.
- Li, Sakkas, Urquhart, *Intraday time series momentum: global evidence and links to market characteristics*, Journal of Financial Markets 57, 2022, 100619, DOI [10.1016/j.finmar.2021.100619](https://doi.org/10.1016/j.finmar.2021.100619). Международный контекст, не прямой тест USDRUBF.

**Почему USDRUBF:** у механизма есть прямой российский FX-прецедент; бессрочный контракт устраняет roll; pinned M5/M15/M30 физически доступны. Это обоснование выбора до теста, а не доказательство прибыльности.

**Чем R099 отличался от прошлых работ:** исследовалась причинная межинтервальная зависимость и отдельный 30-минутный контракт конца сессии, а не opening-range breakout, запрет первого часа, squeeze/retest, trailing или перераспределение капитала V20.

## 3. Карта направлений 2027

Оценка ниже относится к исследовательскому приоритету, а не к ожидаемой доходности. До frozen test все торговые эффекты — `UNPROVEN`.

| Приоритет | Направление | Механизм, который имеет смысл проверить | Данные / ранняя go/no-go проверка | Главные риски и отличие от прошлых работ | Решение |
|---:|---|---|---|---|---|
| 1 | **Cross-asset FX lead-lag: CNYRUBF ↔ USDRUBF** | Общий RUB-фактор, разная скорость price discovery и асинхронное предоставление ликвидности могут создавать короткий causal lead-lag, а не просто одновременную корреляцию | Уже доступны pinned M5; сначала только timestamp/liquidity alignment и out-of-sample-by-time predictive check без торговли; затем отдельный frozen baseline | Stale-котировки, общий фактор вместо переноса информации, синхронные timestamp не доказывают порядок событий, costs могут поглотить эффект. Не повтор R099: источник сигнала — другой инструмент | **NEXT_RESEARCH_CANDIDATE**, новый ID; не тестировано |
| 2 | **Самостоятельный среднесрочный trend/volatility portfolio** | Медленная реакция на макроинформацию и премия за перенос трендового риска; волатильность задаёт экспозицию ex ante, а не подбирается как entry-filter V20 | Нужна более длинная daily/H1 история и единый календарь инструментов; текущие 2023–2026 недостаточны для сильного заявления | Повтор V20 при простой смене названий, параметрический overfit, ограниченные четыре инструмента, vol sizing не должен маскировать слабый сигнал | **HOLD_FOR_LONGER_HISTORY / NEW_ID** |
| 3 | **Signed post-shock drift вместо compression breakout** | После редкого информационного шока дальнейшее движение может отражать постепенное переваривание новости и inventory adjustment; проверяется event study с заранее заданным горизонтом | Нужны объективные ex-ante shock definitions и достаточное число событий; go/no-go — минимальный N и устойчивость до расчёта PF | Малое N, выбор порога по известным событиям, сходство с R049/R068 при неосторожной формулировке. Compression/squeeze/breakout не повторять | **IDEA_ONLY**, только при отличном механизме и достаточном N |
| 4 | **Execution/liquidity как отдельный источник улучшения V20** | Spread, depth, очередь и время исполнения могут изменять realised edge без изменения прогноза; это измерение стоимости и вместимости, а не новая «прибыльная» OHLCV-фильтрация | Нужны anonymized event-time order/fill, spread/depth, фактические fees/ГО; OHLCV touch недостаточен | Нет данных — нет вывода; риск выдать модельный fill за наблюдённый. Прямо продолжает ограничения R067/R097/R098 | **HIGH_VALUE_DATA_PROGRAM**, не alpha candidate |
| 5 | **Forward-only untouched OOS и session/provenance registry** | Устраняет главный методологический дефект: повторное использование 2018–2026 и неоднозначные границы сессий | С 2027 сохранять raw bytes, export timezone/bar convention, расписание сессий, SHA256 и contamination ledger до просмотра результатов | Не даёт прибыль само по себе; требует дисциплины и запрета подгонки под forward | **MANDATORY_FOUNDATION** |

**Собственная оценка:** направление 1 сейчас наиболее рационально как следующий эксперимент, потому что у него есть другой источник информации и доступные данные. Но оно не должно запускаться автоматически как серия переборов: сначала один frozen mechanism test и жёсткий отказ при слабом экономическом эффекте. Направления 4–5 важнее для долгосрочной ценности V20, чем очередной исторический sweep.

## 4. Frozen design R099

Протокол [FROZEN_PROTOCOL.md](../research/experiments/r099/FROZEN_PROTOCOL.md) зафиксирован **26.11.2026 11:37:04 UTC**, SHA256 `ea2e066085b016b53be58f947b95e9b37aca99554cc5cdfbeff442f8684ffee0`, до вычисления сигналов, корреляций, PF и P&L.

- Вход: `market-pattern-data`, commit `f8486b446cf3d5f9f3cba6dfec32bdef8fd184c8`.
- M5 SHA256: `3758ed99e4ec0c712af09575ddc74f0437f2fcddda05df2c5d27268296037786`.
- `P0`: Close 18:45 предыдущей наблюдаемой сессии; `P1`: Close 10:25; сигнал доступен в 10:30.
- `rF=ln(P1/P0)`, `rL=ln(X/E)`, где `E=Open 18:20`, `X=Close 18:45`.
- Long при `P1>P0`, short при `P1<P0`, иначе сделки нет; один лот; выход в 18:50 по последнему Close.
- Обязательные шесть M5-баров первого и шесть последнего интервалов; пропуски не импутируются.
- C1/C2/C4 — 1/2/4 тика adverse drag на каждую сторону. Это **не наблюдённые** исторические издержки.
- Запрещены optimization, смена сессии/порога/стороны и новые варианты под тем же ID.

## 5. Фактические результаты

### 5.1 Покрытие и данные

| Проверка | Результат |
|---|---:|
| Raw M5 rows | 159752 |
| Период raw data | 03.01.2023 09:00 — 30.08.2026 18:55 |
| NA / duplicate timestamps / non-monotonic / invalid OHLCV | 0 / 0 / 0 / 0 |
| Weekday main-session candidates | 925 |
| Eligible, включая zero-signal | 922 |
| Nonzero trades | 910 |
| Zero-signal days | 12 (1,302% eligible) |
| Excluded days | 3 (0,324% candidates) |
| Prefix/future mismatch | 0 / 0 из 922 |
| Ledger net-recalculation mismatch | 0 из 910 |

Исключены 03.01.2023 (нет предыдущего Close 18:45), 20.01.2023 (нет 18:40), 13.09.2023 (нет первого получасового интервала). Ни один пропуск не заполнялся.

### 5.2 Primary predictive test

OLS `rL = alpha + beta*rF`, Newey–West HAC lag 5:

| N | beta | beta SE | t | two-sided p | R² |
|---:|---:|---:|---:|---:|---:|
| 922 | 0,0354943 | 0,0147744 | 2,4024 | **0,0162874** | 0,0150831 |

**Интерпретация:** направление статистической связи положительно и проходит заранее заданный predictive gate. Но R² около 1,5% не означает достаточный денежный edge, а p-value не измеряет прибыль после издержек.

### 5.3 Денежный результат одного лота

| Сценарий | Gross, ₽ | Net, ₽ | Mean/trade, ₽ | PF | Win rate | Trade-close Max DD, ₽ | Sharpe 252 |
|---|---:|---:|---:|---:|---:|---:|---:|
| C1 | +10 960 | **−7 240** | −7,956 | 0,8315 | 42,31% | 8 290 | −1,012 |
| C2 | +10 960 | **−25 440** | −27,956 | 0,5277 | 36,81% | 25 480 | −3,555 |
| C4 | +10 960 | **−61 840** | −67,956 | 0,2229 | 20,22% | 61 700 | −8,640 |

Gross положителен, но уже C1 отрицателен. Это означает, что исходный денежный запас слишком мал: модельный adverse drag делает стратегию убыточной даже в самом мягком из трёх сценариев. Фактические издержки могут отличаться; вывод относится к frozen model, а не к утверждению о каждом возможном реальном исполнении.

| Год | Trades | Net C2, ₽ | PF C2 |
|---|---:|---:|---:|
| 2023 | 247 | −5 450 | 0,6234 |
| 2024 | 250 | −5 820 | 0,5695 |
| 2025 | 250 | −8 420 | 0,4834 |
| 2026 YTD | 163 | −5 750 | 0,3992 |

Bootstrap C2 по всем 922 eligible-дням: среднее **−27,592 ₽/сессию**, 95% CI **[−36,432; −18,319] ₽**. После удаления 10 лучших сделок: **−29 620 ₽**. Положительных годов нет, поэтому годовая доля положительного Net не определена.

Benchmarks C2 на 922 eligible-днях: Always Long Net **−45 990 ₽**, PF **0,3228**; Always Short Net **−27 770 ₽**, PF **0,4973**. Это диагностика интервала, не разрешение выбрать Always Short или short-only как новую стратегию.

## 6. Применение заранее замороженных gates

| Gate | Факт | Итог |
|---|---|---|
| Data: N≥850, exclusions≤2%, zero-signal≤1% | N=922 и exclusions=0,324% проходят; zero-signal=1,302% не проходит | **FAIL** |
| Predictive: beta>0, HAC p<0,05 | beta=0,03549; p=0,01629 | **PASS** |
| Economic: mean C2>0 и lower 95% CI>0 | mean=−27,592 ₽; CI полностью ниже нуля | **FAIL** |
| PF: C2≥1,10 и C4>1,00 | 0,5277 и 0,2229 | **FAIL** |
| Years: минимум 3/4 положительных, обязательно 2025/2026 | 0/4 положительных | **FAIL** |
| Concentration: Net без top-10>0; годовая концентрация≤60% | Net без top-10=−29 620 ₽; положительных годов нет | **FAIL** |
| Причинные controls | Prefix/future 922/922 без mismatch | **PASS** |

**Протокольное решение:** `REJECT_CURRENT_BASELINE`. Ни один gate не смягчался после просмотра результата.

## 7. Воспроизводимость и witnesses

Canonical run: 26.11.2026 11:56:18–11:56:47 UTC. Clean replay: 11:56:48–11:57:11 UTC. Отдельные процессы и output-каталоги; одинаковые pinned inputs, protocol и code.

Побайтово совпали:

- `controls.json` — SHA256 `fc6b5e2b4b3d5f43fdd427f7f3bdaa7644ec7954919de44dbd921f1311a5f80e`;
- `daily_ledger.csv` — `f038be621ddb35468c7fc6002060d71a66977466dfd4e5627b35d7c4a2a2c3a9`;
- `data_quality.json` — `ea7ec58d35a13f8bbce8880b588e30a921ccb578da388ef409ab58ff0e5fa272`;
- `excluded_days.csv` — `b1d2806328d99d675634082d1a80b3083a17534c1eacfc9aa9e9e9edabf92b18`;
- `metrics.csv` — `08bfab4a643223489491ba010ea715a56474094ae038a8cc3de39724d8d8672a`;
- `statistical_tests.json` — `96ead285b99d3016acefbc27ba3d097905214d5140407efbbb3832f9808ae722`.

`run.log` различается только фактическими timestamps; смысловые поля `eligible=922`, `trades=910`, `decision=REJECT_CURRENT_BASELINE` совпали. Подробности: [replay_verification.json](../research/experiments/r099/artifacts/replay_verification.json).

Дополнительно `independent_check.py` отдельной векторизованной pivot/shift-логикой восстановил 922 eligible-дня и 910 сделок. Все сравниваемые поля `P0/P1/E/X`, direction, Gross и Net C1/C2/C4 совпали с canonical ledger; максимальное денежное расхождение `1,35×10⁻¹¹ ₽`. Независимый statsmodels HAC с явной finite-sample correction дал beta `0,035494289895536525` и p `0,01628737229568263`; расхождения с canonical находятся на уровне floating-point. Свидетельство: [independent_verification.json](../research/experiments/r099/artifacts/independent_verification.json). Bootstrap и остальные diagnostics второй реализацией не переписывались.

### Cross-timeframe ограничение

- M5→M30 first30: **922 проверки, 0 mismatch**.
- Frozen M15 18:30→M5 18:45 close: **807 mismatch**; этот comparator структурно сопоставляет разные номинальные интервалы и не должен интерпретироваться как 807 ошибок цены.
- Frozen M30 18:30→M5 18:45 close: **106 mismatch**.
- Дополнительный post-freeze data-quality diagnostic M15 18:45→M5 18:45: **105 mismatch**.

Расхождения закрытия сосредоточены в 2026 данных и показывают, что фиксированная граница 18:45 не является надёжным универсальным описанием конца основной сессии на всём периоде. Например, в части 2026 присутствуют M5 18:50/18:55 и последующие бары, а M15/M30 агрегируют иной интервал. Граница **не переносилась** после результата. Для будущих исследований требуется официальный session calendar с историческими изменениями и явный export bar convention.

## 8. Технические исправления без изменения гипотезы

До финального canonical run были исправлены только реализационные ошибки и полнота обязательных diagnostics:

1. первый запуск остановился на неверном имени колонки bootstrap (`net_rub` вместо `net_rub_c2`);
2. промежуточный merge типов `date` ошибочно дал нулевой bootstrap-ряд; исправлено приведением дат к общему строковому формату;
3. prefix/future controls расширены с 910 nonzero trades до всех 922 eligible days, как требует протокол;
4. добавлены месячные диагностики и benchmarks на всех eligible days; benchmark bps нормированы на размер лота;
5. добавлен отдельный M15 18:45 data-quality diagnostic, не влияющий на сигнал/P&L/gates.

Frozen protocol и его SHA256 не менялись. Эти исправления не являются новыми торговыми вариантами; ошибочные промежуточные outputs не использовались для выбора правил. Полная хронология — в [RUNBOOK.md](../research/experiments/r099/RUNBOOK.md) и [CONTAMINATION_LEDGER.md](../research/experiments/r099/CONTAMINATION_LEDGER.md).

## 9. Что результат не доказывает

- Не доказывает отсутствие любого intraday momentum на MOEX, других инструментах или в других механизмах.
- Не превращает положительный beta в прибыль и не оправдывает подбор short-only после результата.
- Не является TRUE OOS или Walk-Forward. Независимо переписаны ledger/HAC, но не bootstrap и не весь комплект diagnostics.
- Не оценивает реальную доходность на счёт, ГО, ёмкость, очередь, spread, комиссии и partial fills.
- Не переносит `REPRODUCIBLE_VERIFIED` на R060/R097 или другие исторические работы.
- Не даёт статусов CANDIDATE, INSTALLED или LIVE.

## 10. Следующий исследовательский порядок

1. **Не оптимизировать R099.** Закрыть как отрицательный результат и сохранить ledger/negative index.
2. **До нового теста** подготовить historical session/provenance registry и правила работы с изменением расписания.
3. **Для cross-asset lead-lag** создать новый Research ID и frozen protocol до расчёта доходностей; сначала проверить timestamp alignment, stale bars и causal availability, затем один baseline с C1/C2/C4 и заранее заданными gates.
4. **Для V20 Evolution** запрашивать не новые исторические sweep, а anonymized fact fills/fees/ГО и микроструктуру. Без них сохранять `HOLD_DATA`.
5. **С 2027** формировать untouched forward набор: frozen hypothesis до чтения результата, append-only contamination ledger, никакого возврата к подгонке на forward после публикации.

## 11. Доказательства

- [Research Card R099](../research/TRL_R_2026_099_USDRUBF_FIRST_LAST_MOMENTUM.md)
- [Frozen protocol](../research/experiments/r099/FROZEN_PROTOCOL.md)
- [Код](../research/experiments/r099/run_r099.py)
- [Runbook](../research/experiments/r099/RUNBOOK.md)
- [Witness matrix](../research/experiments/r099/WITNESS_MATRIX.md)
- [Contamination ledger](../research/experiments/r099/CONTAMINATION_LEDGER.md)
- [Run manifest](../research/experiments/r099/artifacts/run_manifest.json)
- [Journal](../journal/2026-11-26-r099-usdrubf-first-last-momentum.md)
