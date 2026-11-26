# TRL-R-2026-100 — USDRUBF First-to-Last Half-Hour Momentum

> Канонический ID: R100; оригинальный ID пакета Kimi: R099. [История переназначения и неизменяемые доказательства](TRL-R100-ID-PROVENANCE.md).

**Дата:** 26.11.2026. **Категория:** NEW_STRATEGY / RESEARCH_ONLY.  
**Итог:** **REJECT / REJECT_CURRENT_BASELINE**.  
**Воспроизводимость:** `REPRODUCIBLE_VERIFIED` для двух byte-identical offline-запусков и отдельной векторизованной сверки ledger/HAC; не для TRUE OOS или торгового преимущества.  
**LIVE / V20 / FINAM / капитал:** без изменений.

| Поле | Значение |
|---|---|
| Исследователь | Kimi, самостоятельный TRL-агент; GPT-review не имитировался |
| Источник идеи | Elaut, Frommel, Lampaert, *Intraday momentum in FX markets: Disentangling informed trading from liquidity provision*, Journal of Financial Markets, DOI [10.1016/j.finmar.2016.05.004](https://doi.org/10.1016/j.finmar.2016.05.004), транзакции RUB/USD MICEX 2005–2014; Gao, Han, Li, Zhou, *Market intraday momentum*, JFE 129(2), 2018, DOI [10.1016/j.jfineco.2018.05.009](https://doi.org/10.1016/j.jfineco.2018.05.009) |
| Предполагаемый механизм прибыли | Закрытие нежелательного инвентаря поставщиков ликвидности и нежелание нести overnight risk могут создавать поток конца основной сессии в направлении первого получасового движения. Это исходная гипотеза, не подтверждённый механизм на 2023–2026 |
| Инструмент / TF / сессия | Бессрочный USDRUBF, M5, фиксированная основная сессия 10:00–18:50 MSK; weekend-сессии не торгуются |
| Точные правила | `P0=Close 18:45` предыдущей наблюдаемой сессии; `P1=Close 10:25`; знак `P1-P0` задаёт long/short; Market-вход по `Open 18:20`; выход по `Close 18:45`; 1 лот; без SL/TP/Protect/HOLD/EXT и переноса позиции |
| Frozen baseline | [FROZEN_PROTOCOL.md](experiments/r100/FROZEN_PROTOCOL.md), SHA256 `ea2e066085b016b53be58f947b95e9b37aca99554cc5cdfbeff442f8684ffee0`, заморожен 26.11.2026 в 11:37:04 UTC до вычисления результатов |
| Источник данных | `alkospacer123/market-pattern-data`, commit `f8486b446cf3d5f9f3cba6dfec32bdef8fd184c8`, `forever/USDRUBF/USDRUBF_M5.csv`; 159752 строки, 03.01.2023 09:00 — 30.08.2026 18:55 |
| SHA256 / roll / timezone | M5 SHA256 `3758ed99e4ec0c712af09575ddc74f0437f2fcddda05df2c5d27268296037786`; Git blob SHA1 `2b621e1c0aa9a84838d95d4c139257889b6f825e`; roll не требуется; naive timestamps интерпретированы как начало бара MSK, отдельный export metadata отсутствует |
| Development / validation / OOS | Весь период — `RETROSPECTIVE_DEVELOPMENT_NOT_TRUE_OOS`; отдельного validation и untouched TRUE OOS нет; Walk-Forward не заявляется |
| Уже использованные периоды / варианты | 2023–2026 ранее многократно использованы TRL; выполнен один baseline и только заранее перечисленные diagnostics; никаких sweep времени, порогов, сторон или фильтров |
| Код / конфигурация | [run_r099.py](experiments/r100/run_r099.py), SHA256 `56e99cd46a6f63eefe13be4fd2d95296bc1c67116a5cada929fdb52a858a2fdb`; базовый MAIN `f0d289bd64536975dbcf3ec25ed1811c06116119`; pandas/numpy, без сети |
| Расходы / ГО | C1/C2/C4 = 1/2/4 тика adverse drag на каждую сторону; тик 0,01 RUB, лот USD 1000; это модельные сценарии, не фактические spread/fees/slippage. Исторические ГО, комиссии, стакан, очередь и partial fills отсутствуют |
| Допуск и покрытие | 925 weekday-кандидатов; 922 eligible, включая 12 zero-signal дней; 910 сделок; 3 исключения (0,324%). Data gate не пройден из-за zero-signal доли 1,302% > 1% |
| Primary statistics | `beta=0,0354943`, Newey–West lag 5, two-sided `p=0,0162874`, `R²=0,0150831`: положительная, но слабая межинтервальная связь |
| Экономика 1 лота | Gross `+10 960 ₽`; Net C1 `−7 240 ₽`, PF `0,8315`; Net C2 `−25 440 ₽`, PF `0,5277`; Net C4 `−61 840 ₽`, PF `0,2229` |
| Годы Net C2 | 2023 `−5 450 ₽`; 2024 `−5 820 ₽`; 2025 `−8 420 ₽`; 2026 YTD `−5 750 ₽` |
| Bootstrap C2 | Среднее на eligible-сессию `−27,592 ₽`; 95% circular moving-block CI `[−36,432; −18,319] ₽`; block 20, 20000 resamples, seed 20261126 |
| Концентрация | После удаления 10 лучших сделок Net C2 `−29 620 ₽`; положительных годов нет, поэтому доля лучшего положительного года `UNDEFINED` |
| Причинность и ledger | Prefix/future controls: 922/922, mismatch 0; 910 уникальных ledger-дат; ошибок пересчёта Net из fills 0; clean replay совпал по всем шести аналитическим файлам; отдельная vectorized pivot/shift проверка и statsmodels HAC — PASS |
| TF witnesses | M5→M30 first30: 922 проверки, mismatch 0. Frozen M15 18:30 close: mismatch 807; M30 18:30 close: mismatch 106. Дополнительный M15 18:45 diagnostic: mismatch 105. Расхождения зафиксированы, не скорректированы постфактум |
| Ограничения | Нет TRUE OOS, фактических издержек/ГО/стакана и export timezone metadata; fixed 18:45 не во всех периодах совпадает с фактическим концом основной сессии; независимо сверены ledger и HAC, но bootstrap и все diagnostics второй реализацией не переписаны |
| Решение | **Отклонить текущий baseline и не продолжать его оптимизацию.** Положительный beta не компенсирует отрицательную экономику и устойчивые годовые потери. Не выбирать short-only, другую сессию или порог по этим результатам |
| Следующее действие | Сохранить R100 в Negative Research Index. Для нового исследования — новый ID и механизм; приоритет 2027: cross-asset lead-lag, расширение истории, forward-only данные и фактическая микроструктура исполнения |
| Доказательства | [Итоговый отчёт](../reports/TRL-2027-RESEARCH-DIRECTIONS-R100.md) · [Journal](../journal/2026-11-26-r100-usdrubf-first-last-momentum.md) · [ledger](experiments/r100/artifacts/daily_ledger.csv) · [statistics](experiments/r100/artifacts/statistical_tests.json) · [controls](experiments/r100/artifacts/controls.json) · [replay](experiments/r100/artifacts/replay_verification.json) · [independent check](experiments/r100/artifacts/independent_verification.json) |

**Вывод:** научно обоснованный отрицательный результат является завершённым исследованием. R100 не становится кандидатом, не улучшает V20 и не даёт основания для LIVE.
