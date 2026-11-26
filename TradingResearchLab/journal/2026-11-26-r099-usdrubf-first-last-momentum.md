# TRL Journal — 26.11.2026 — R099 и направления 2027

**Направление:** Research / NEW_STRATEGY.  
**Статус:** RESEARCH_COMPLETE / **REJECT_CURRENT_BASELINE** / LIVE_UNCHANGED.

**Задача:** после ноябрьского цикла выбрать перспективные направления 2027 и проверить одну новую, механистически обоснованную гипотезу без повторения opening-range, squeeze/retest, MOM8/EXT2, trailing и capital sweep.

**Выбор:** USDRUBF first-to-last half-hour momentum. Основание — публикация Elaut, Frommel, Lampaert о RUB/USD MICEX и механизме liquidity provision/overnight inventory; дополнительный общий источник — Gao et al. Полная новизна среди V1–V24 не доказана из-за недоступных архивов, но точная конструкция в доступном реестре не восстановлена.

**Frozen protocol:** 2026-11-26T11:37:04Z, SHA256 `ea2e066085b016b53be58f947b95e9b37aca99554cc5cdfbeff442f8684ffee0`. До freeze вычислялись только источник, покрытие и базовое качество данных, не доходности/PF. Один baseline, фиксированные 10:00–18:50 MSK, один лот, C1/C2/C4, никаких последующих фильтров.

**Данные:** `market-pattern-data@f8486b446cf3d5f9f3cba6dfec32bdef8fd184c8`; USDRUBF M5 SHA256 `3758ed99e4ec0c712af09575ddc74f0437f2fcddda05df2c5d27268296037786`. 159752 строки; 922 eligible; 910 trades; 3 exclusions; NA/duplicates/non-monotonic/OHLC errors = 0. Весь период 2023–2026 — retrospective development, не TRUE OOS.

**Результат:** beta=0,0354943, HAC p=0,0162874, R²=0,0150831 — predictive gate PASS. Но Gross +10960 ₽ превращается в Net C1 −7240 ₽, C2 −25440 ₽, C4 −61840 ₽. PF C2=0,5277, C4=0,2229. Net C2 по годам: −5450/−5820/−8420/−5750 ₽. Bootstrap C2 mean −27,592 ₽ на eligible-сессию, 95% CI [−36,432; −18,319]. Без 10 лучших сделок Net C2 −29620 ₽. Data gate FAIL из-за 12 zero-signal дней (1,302%>1%); остальные экономические/yearly/concentration gates также FAIL.

**Witnesses:** prefix/future 922/922 без mismatch; ledger 910 уникальных дат и 0 ошибок Net identity; M5→M30 first30 0/922 mismatch. Frozen close witnesses: M15 807 и M30 106 mismatch; дополнительный M15 18:45 diagnostic — 105 mismatch. Это зафиксированное ограничение session/provenance, прежде всего 2026, а не повод перенести границу после результата.

**Replay:** финальные canonical и clean offline runs выполнены в отдельных процессах/каталогах; шесть аналитических outputs совпали побайтово. Код SHA256 `56e99cd46a6f63eefe13be4fd2d95296bc1c67116a5cada929fdb52a858a2fdb`. Дополнительная vectorized pivot/shift реализация и statsmodels HAC независимо восстановили ledger и regression с floating-point расхождениями не более 1,35×10⁻¹¹ ₽ для денежных полей. `REPRODUCIBLE_VERIFIED` относится к расчёту; bootstrap/все diagnostics второй реализацией не переписаны, TRUE OOS отсутствует.

**Решение:** текущий R099 baseline отклонить, не оптимизировать и не переносить в V20. Статистическая предсказуемость не равна торговому преимуществу. Результат внесён в Research Registry и Negative Research Index.

**Приоритеты 2027:** cross-asset CNYRUBF↔USDRUBF lead-lag как следующий новый mechanism candidate; более длинная история для standalone trend/volatility; отдельный event-based post-shock drift только при достаточном N; фактические fills/fees/ГО/depth для V20; обязательный forward-only untouched OOS и session/provenance registry. Все торговые эффекты этих направлений пока UNPROVEN.

**Операции LIVE/V20/FINAM/капитал:** 0. GPT-review не выполнялся и не имитировался.

Ссылки: [итоговый отчёт](../reports/TRL-2027-RESEARCH-DIRECTIONS-R099.md), [Research Card](../research/TRL_R_2026_099_USDRUBF_FIRST_LAST_MOMENTUM.md), [manifest](../research/experiments/r099/artifacts/run_manifest.json).
