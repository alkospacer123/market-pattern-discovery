# T3/M15 Early Risk Protection v1

**Отрицательный результат: `NEGATIVE_RESULT_REJECT_EARLY_PROTECT_05`.** Правило +0,5 initial R → защитный Stop −0,5 initial R сокращает часть убытков, но ухудшает оба годовых PF, месячную регулярность, DD и сохранение крупных трендов. Следующее значение не подбиралось.

**GROSS_ONLY / COSTS_DEFERRED / NOT_LIVE_READY. 2023–2024 DEVELOPMENT_EXPOSED.**

[Полный русский отчёт](results/REPORT.md) · [Все инструменты и направления](results/DETAIL.md) · [Решение](results/DECISION.json) · [Протокол](PROTOCOL.md)

| Показатель | CONTROL | EARLY_PROTECT_05 |
| --- | --- | --- |
| PF 2023 | 2,207278 | 2,079559 |
| PF 2024 | 1,772134 | 1,592508 |
| Gross R 2023–2024 | +212,522656R | +166,770771R |
| CLOSED / terminal OPEN | 480 / 1 | 504 / 1 |
| Положительные месяцы | 20/24 (9+11) | 18/24 (8+10) |
| Худший полный месяц | −4,943501R, март 2023 | −9,683926R, февраль 2024 |
| CLOSED-R DD | 12,628056R | 19,321756R |
| Ноябрь / Gross R 2024 | 44,005603% | 57,914655% |

Все 32 исходных SHORT2024 MFE0,5–1R сохранили вход и действительно получили защитный Stop со следующей наблюдаемой свечи. Все 32 убытка уменьшены, экономия +15,613523R. Но на полном пути уменьшено 96 исходных убытков (+40,775234R), а 39 исходных прибыльных сделок закрыты раньше с убытком (потеря 99,262166R). Из 83 исходных победителей ≥2R потеряны 15, из 21 ≥5R — 5; все они превратились в −0,5R. Потеря на исходных ≥2R: 68,186037R; на вложенном подмножестве ≥5R: 31,688893R. Эти две потери нельзя складывать.

Занятость пересчитана причинно: 24 новых исполненных входа, 0 потерянных исходных входов; 54 изменения причин/исполнения и 93 изменения занятости/identity владельца позиции. Новые CLOSED дают +13,664741R, matched исходные CLOSED меняются на −59,416626R; итог −45,751885R. SHORT2024 PF снизился 1,473497 → 1,255147. LONG PF тоже ухудшился в обоих годах. В 2024 PF снизился у всех четырёх инструментов. Без ноября2024 PF нового пути 1,260466 против исходных 1,452043.

База — actual main `6c853d7bd3d7d02cbef81266c4c3e6fb9c3d0838`; PR #507 MERGED, #505/#506 MERGED. Data pin `f8486b446cf3d5f9f3cba6dfec32bdef8fd184c8`, чистый read-only источник. CONTROL полностью совпадает со всеми trade/Stop/signal/gap/OPEN журналами #505/#506/#507 и опубликованной экономикой #505. Исходная диагностика32 проверена по точным ID. Параметры и execution grammar сохранены; только один новый механизм. Поле replay `rule=C1` — унаследованный кодовый alias A6+S1, оно не означает вычет издержек C1. Raw source quotes не копируются, OHLC2025+ не читается/не парсится; полные hashes считают непрозрачные bytes.

Заморозка торгового кода, формул, SPEC и 38 причинных тестов до первого нового результата: опубликованный commit **`10ce4fd0cd4edb641fc6785f15109a9bd5c68f39`**, receipt commit `324134d2`. После результата исправлена **только проверка форматирования Markdown-чисел**: равные `0` и `0.000000` ошибочно считались различными. Исходные код, freeze receipt, FAIL и одна строка расхождения сохранены в [correction_history](correction_history/); [описание поправки](PRESENTATION_CORRECTION.json). Код стратегии, indicators, metrics, joins, параметры и causal tests побайтно неизменны; [сверка исходного результата](CORRECTION_RESULT_INVARIANCE.json) подтверждает неизменность всех вычислительных артефактов, кроме metadata SOURCE_MANIFEST. Текущий [FREEZE](FREEZE.json) честно отмечает, что поправка аудитора сделана после результата. Новых правил или результатов стратегия не получала.

Независимая вычислительная сверка — отдельные stdlib/scalar indicators, dictionary position machine, joins и metrics против pandas/object primary. **1 354 341 поле, 0 расхождений; max delta 5,68e−14; tolerance1e−8.** Полный feature-control: 98 305 M15 / 1 867 799 полей, 0 расхождений. **23 100 causal-bar checks PASS; 38 synthetic tests PASS.** Все 10 Markdown-таблиц / 2 366 cells и DECISION независимо проверены по scalar результатам. Два дополнительных свежих полных primary+scalar pipeline сверяются прямыми bytes и SHA256 в [REPEATABILITY](REPEATABILITY.json). Один автор; независимость вычислительная, внешнее человеческое ревью **PENDING**.

CSV/JSON: 90 annual/full scope rows, 720 monthly cells, 505 entry identities с CLOSED/OPEN, 2 017 signal comparisons,32 causal cases,83 winner IDs и45 effect scopes. Полные raw replay журналы обеих реализаций сохранены в `results/control`, `results/control_scalar`, `results/experiment`, `audit/control`, `audit/experiment`. Исходный OPEN не ликвидирован искусственно. Времена — MSK UTC+3. Все24 месяца сохранены, GLDRUBF начинает историю в июле2023, IMOEXF в ноябре2023; NO_COVERAGE отдельно.

Воспроизведение из корня репозитория, Python3.12 и requirements.txt:

```sh
export PYTHONDONTWRITEBYTECODE=1
python IntradayLab/t3_m15_early_risk_protection_v1/run.py --data-root /workspace/market-pattern-data
python IntradayLab/t3_m15_early_risk_protection_v1/audit.py --data-root /workspace/market-pattern-data
python IntradayLab/t3_m15_early_risk_protection_v1/report.py
python IntradayLab/t3_m15_early_risk_protection_v1/audit_presentation.py
python IntradayLab/t3_m15_early_risk_protection_v1/repeat.py
python IntradayLab/t3_m15_early_risk_protection_v1/seal.py
```

Repeat требует ещё не существующих `/workspace/work/early_risk_repeat_1` и `_2`; для новой независимой репродукции используйте чистую среду с read-only source pin. Freeze guard проверяет SHA и Git commit. Снимки source/branch/protected scope — START_GATE, PR_CONTEXT, FINAL_MAIN_CHECK и SCOPE_CHECK; полный SHA inventory — ARTIFACT_SHA256.

Только новый каталог. TradingSystemLab, робот, ROADMAP, прежние исследования, source data и исходный checkout неизменны. Costs/slippage/funding/ticks/sizing/капитал/live fills отложены. Robustness/WF/TRUE OOS/LIVE и дополнительные варианты не запускались. Один **Draft PR / NO MERGE / NO AUTO-MERGE**. **STOP после создания PR.**
