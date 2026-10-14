# Зафиксированный протокол — TRAIL_375 WF 2025

Основание: явное разрешение пользователя 13.10.2026. До первого raw-read фиксируются этот протокол, SPEC, USER_AUTHORIZATION, все executable modules и synthetic tests в отдельном Git commit. Фактический main fa188b51fbd27df5a51a43a9742bc772a1c17abd; #510/#511 merged. Предыдущие исследования, ROADMAP, TradingSystemLab/робот и data не изменяются.

Все интервалы полуоткрытые Europe/Moscow: DEVELOPMENT [2023-01-01,2025-01-01), W1 [2025-01-01,2025-04-01), W2 [2025-04-01,2025-07-01), W3 [2025-07-01,2025-10-01), W4 [2025-10-01,2026-01-01). TRUE OOS [2026-01-01,2027-01-01) закрыт.

Стратегия, конфигурация и численная семантика неизменны. engine/scalar/primary_metrics/scalar_metrics — побайтные копии #510. common содержит прежние независимые scalar indicators, меняются только base/access adapter. Исходные небезопасные полные load/hash входы заблокированы; raw данные читает только safe_source. Копия engine.read_source не используется на реальных файлах, только старый synthetic fixture. Внутренний rule C1 — A6+S1, не расходы.

## Защита данных

Data HEAD и tree blob ID проверяются только Git metadata, pin f8486b446cf3d5f9f3cba6dfec32bdef8fd184c8. Ни hash-object, ни full-file SHA256 raw source не разрешены. Два отдельных timestamp-first parser используют unbuffered FileIO. OHLCV suffix прочитывается/декодируется/хешируется только если start+15m строго меньше текущего cutoff. На будущем годе допускаются только четыре ASCII-байта sentinel year; никакой timestamp/coverage 2026 не вычисляется, numeric suffix не читается. Python runtime audit hook допускает только четыре M15 source paths из reader. Byte counters, prefix SHA256, poisoned suffix/read-spy tests документируют доступ. Нет системного syscall-trace; аудит application-level и source inspection раскрыты без притворного OS-сертификата.

Проверка sorting/duplicates/OHLC и coverage проводится только на разрешённом prefix. Будущая часть и её full-file hashes не исследуются. Если граница, CONTROL, каузальность, pin или полные журналы не подтверждаются, WF_INVALID и STOP; результаты не использовать. Нет попытки прочитать закрытые строки для проверки хвоста. Raw quotes не копируются; trade/Stop и derived-indicator журналы разрешены.

## Порядок и carry

Сначала полный 2023–2024 CONTROL: обе реализации, все indicator fields, все trade/Stop/signal/gap/terminal OPEN/monthly OPEN, summary/monthly и полные #510 diagnostics, а также #505–#508. Точные контрольные величины из #511, tolerance 1e-8. Любое расхождение — STOP до WF.

Далее W1 → W2 → W3 → W4. Каждый блок читается только до собственной границы, результаты/полные журналы/indicator frontier/OPEN/pending и SHA SEAL коммитятся перед следующим чтением. Для минимального изменения канонического кода каждый блок реконструирует непрерывное состояние expanding replay от исходного 2023 начала. Это не refit и не reset на границе: внутри каждого replay нет квартальной ветки. Точное равенство старого feature prefix и полных sealed trade/Stop/gap/settled-signal журналов проверяется. Initial R, Stop/S1, extrema, IDs, occupancy, pending сохраняются через всю историю. Последний pending в sealed prefix может причинно разрешиться только в следующем блоке. Снимок frontier содержит prefix provenance и последние features; resume выполняется из полного разрешённого prefix, не из усечённого lookback.

IMOEXF T3-M15-IMOEXF-000090 унаследован из декабря 2024 и никогда не считается новым входом WF. Канонический exit Close определяет календарный период полного CLOSED R; даже gap fill по Open сохраняет canonical exit Close. Событие ровно end принадлежит следующему блоку. OPEN не ликвидируется и не включается в CLOSED PF/R. Будущее закрытие из 2026 не используется.

## Отчётность и решение

Для каждого квартала, cumulative WF, всего года и всех 12 месяцев: календарные CLOSED, новые signal+entry 2025 CLOSED и inherited development; четыре инструмента, LONG/SHORT и instrument×side. Квартальные entry_cohorts отдельно определяются по обоим timestamps внутри квартала; исходы только известные к seal horizon. Все отрицательные и N/A сохраняются. Calendar denominators не сокращаются при пропусках.

CLOSED/OPEN; PF, R, expectancy, win rate, mean WIN/LOSS R; положительные/отрицательные/нулевые месяцы; worst month; losing trades/months and full runs; CLOSED-R DD и все recovery episodes; holding time; вклад сторон/инструментов; top-1/3/5/10 winners с ID и результаты исключения; лучший/три лучших месяца и доли (N/A если R<=0); leave-one-instrument-out; фиксированные −0,05R и −0,10R/CLOSED; marked-R = CLOSED R+U_end−U_start и времена/staleness OPEN. Ни R, ни marked-R не доходность капитала. Реальные costs deferred.

Ранжирование локально в каждом периоде: winners descending gross_R, exit_time,instrument,trade_id; months descending R, calendar tie. Диагностики арифметические, без нового торгового replay и сочетания сценариев.

Применяются неизменные критерии #511: WF_INVALID → WF_INSUFFICIENT_EVIDENCE (нет проверенного разрешённого покрытия/ CLOSED / определённого PF) → WF_GROSS_EDGE_NOT_CONFIRMED (full calendar либо new WF cohort R<=0/PF<=1/expectancy<=0) → WF_MIXED (положительный общий знак, но отрицательные кварталы/стороны/инструменты/фиксированные diagnostics) → WF_REVIEW_REQUIRED. Нет автоматического PASS и новых fitted DD/month/concentration/count thresholds. Исторические PF1.70/2.0, 20/24, DD12.628056 — справочные, не допуск WF. Покрытие: 48 instrument-month с разрешёнными барами, observed days, readiness и gaps; это проверка source coverage, не независимая сертификация биржевого календаря.

## Независимость и завершение

Две реализации features/position и арифметики, fresh stdlib/scalar auditor с собственной selection/recovery/presentation проверкой, pre-read causal synthetic tests. Два свежих полных повтора в новых каталогах/процессах, каждый CONTROL + четыре квартала + auditor; все CSV/JSON/MD/results/audit побайтно и SHA256 совпадают с первым. Автор один, внешнее человеческое ревью PENDING.

В конце actual GitHub main, protected SHA inventories и полный diff сверяются. Один Draft PR, NO MERGE/NO AUTO-MERGE, STOP для внешнего аудита и решения пользователя. Никакого TRUE OOS, LIVE, брокерских действий или изменения параметров.

DEVELOPMENT_2023_2024_EXPOSED / WF_2025_AUTHORIZED / TRUE_OOS_2026_LOCKED / GROSS_ONLY / COSTS_DEFERRED / NOT_LIVE_READY.
