# Предрегистрация: A6+S1 Bounded Trailing Optimization v1

2023–2024 DEVELOPMENT_EXPOSED. **GROSS_ONLY / COSTS_DEFERRED / NOT_LIVE_READY.**

Только `IntradayLab/t3_m15_a6_s1_trail_optimization_v1/`. Существующие исследования, ROADMAP, TradingSystemLab, действующий робот и pinned market-pattern-data read-only. Полный фактический GitHub main `d555765f8a5c02261e9bfbc97cafed9a16ec76cd`; #501/#503/#504 MERGED. Старый checkout #500 не обновляется; новый sparse checkout содержит только IntradayLab и корневые metadata. Полный local-to-main diff просмотрен; внешние шесть docs TradingSystemLab #502 унаследованы из main и не входят в task diff. Подробности START_GATE/PR_CONTEXT/READ_REFERENCES_SHA256.

## Пять конфигураций и критерии

Ровно TRAIL_275=2.75, TRAIL_300=3.00 (BASELINE control), TRAIL_325=3.25, TRAIL_350=3.50 (OPTIMIZED control), TRAIL_375=3.75. Коэффициент одинаков для четырёх инструментов, LONG/SHORT и обоих лет. Никаких дополнительных значений, фильтров, стратегий, scores или расширения диапазона после результата, включая граничный максимум. Повторы/две реализации — проверки тех же конфигураций, не дополнительные поисковые испытания.

Архитектура неизменна: EMA75, H1 slope lookback5, ADX14>20, H1 ATR14/ATRMean20>1, A6 strict current completed H1 ratio>previous completed H1 ratio, Donchian20.shift(1), initial Stop 2 signal-M15 ATR, S1 activation +1 immutable initial R. Без T1/ограничения часов. `engine.py` и `scalar.py` — побайтные копии #504; исполняются исключительно C1/NEXT_OPEN. Оставшиеся внутренние исторические ветви этих модулей не запускаются на OHLC и не создают дополнительных конфигураций.

Приоритет: ежегодный Gross PF≥1.70 в каждом году; предпочтительно строго >2 в каждом году. `ANNUAL_PF_MINIMUM_MET` true исключительно при выполнении обоих лет и категория `ANNUAL_PF_GATE_MET`; иначе `NOT MET`. Это не статус торговой готовности. Месячная стабильность: ориентир 20–24 положительных месяцев из 24, меньше зависимости от ноября/лучшего/трёх лучших месяцев, без явного ухудшения худших месяцев, DD и крупных победителей. `MONTHLY_STABILITY_IMPROVED` — отдельное аргументированное заключение с цифрами относительно обоих контролей, без подобранного score/cutoff. Ежегодный PASS при ухудшении месяцев не объявляет победителя. Изолированный успех только 2024 помечается как потенциально переобученный.

Если все пять ниже ежегодного минимума: **ANNUAL_PF_TARGET_NOT_MET**, отрицательный результат сохраняется; STOP. Следующая возможная задача — архитектура входа/режима по уже установленному диагнозу, после отдельного решения пользователя; не расширение trailing.

## Исполнение и данные

Исходный NEXT_OPEN #504 сохраняется. Сигнал по завершённому M15 Close. Pending исполняется только при Close(next)=Close(signal)+15min, по Open(next) до использования extrema исполнения. При отсутствии смежного бара skip, без ожидания следующего; terminal pending отдельно. Initial Stop=actual entry−side×2×completed signal ATR; R=abs(entry−initial Stop), неизменный. Stop действует на execution bar. Затем adverse Open gap, Stop-first; только пережитая свеча обновляет extrema/S1. S1 достигает ≥1R на завершённой пережитой свече, действует со следующей наблюдаемой свечи. Signal/exit свечи не дают будущих favorable extrema для Stop/S1/MFE.

H1 — daily ordinal-блоки четырёх смежных завершённых M15; неполные/gapped блоки исключаются без перепаковки. Индикаторы/Donchian/позиции/риск/S1 намеренно пересекают дни, сессии и 2023/2024 как #504. Сначала выход, затем сигнал на том же Close и возможный pending re-entry. Нет ликвидации OPEN на границах. Год/месяц CLOSED определяется историческим Close выходной свечи, точный intrabar момент неизвестен.

Data pin `f8486b446cf3d5f9f3cba6dfec32bdef8fd184c8`, только forever M15 USDRUBF/CNYRUBF/GLDRUBF/IMOEXF, 98 305 наблюдаемых свечей 2023–2024. Late starts GLD 2023-07-11 и IMOEX 2023-11-14 сохранены. Timestamp-first парсеры останавливаются до OHLC 2025+; full-file SHA/hash-object только opaque bytes. Raw quotes не копируются. История ограничена START≤Close<2025-01-01 МСК, как #504. NO_COVERAGE до старта отдельно от нулевого торгового месяца; denominator 24.

## Порядок и контроль

До первого нового trailing-результата реализовать spec/source/config/tests/report/audit/repeat, пройти synthetic причинные fixtures, создать Git freeze commit; FREEZE.json с SHA каждого исходника ссылается на этот commit. Freeze guard проверяет текущие bytes и Git blobs; в freeze commit results отсутствуют.

Сначала primary и отдельный scalar CONTROL TRAIL_300/350: все доступные #504 CLOSED/Stop/signal/occupancy/gap/terminal OPEN/period OPEN поля с abs tolerance1e−8; обязательные PF/R/DD совпадают после округления к шести десятичным. Failure блокирует все candidate computations. Контроль не ограничивается агрегатами. #497 SIGNAL_CLOSE сравнивается только как опубликованный исторический reference, без нового replay иной модели исполнения.

Две вычислительные реализации: pandas/dataframe/object vs stdlib streaming/dict; metrics numpy vs отдельная scalar арифметика. `audit.py` не импортирует primary engine/analysis/metrics. Один автор; внешнее human review PENDING. Два свежих полных subprocess replay+audit должны совпасть по прямым bytes и SHA256 каждого generated CSV/JSON/MD, включая контрольные журналы и отчёты. Любое исправление frozen code после результата требует прозрачного timing/reason/diff/identity disclosure; скрытых изменений правил нет.

## Отчётность и lineage

Все пять: годы/полный период PF/R/expectancy/CLOSED/OPEN/WIN share/mean WIN/LOSS/DD/loss streak; все 24 месяца с LONG/SHORT и вкладами инструментов, instrument×direction detail и coverage. Worst month/max negative-month run, top1/top3 shares и PF/R без них; November2024 и PF/R без ноября. Исключения — арифметическая sensitivity текущих CLOSED, не альтернативная первичная оценка/перезапуск.

Стабильный entry ID=instrument|direction|signal_time, отдельно исходный и новый последовательный trade_id. Для исходных ≥2R/≥5R обоих контролей показать preserved/improved R, partially reduced nonnegative R, turned negative, lost entry (occupancy отдельно), terminal OPEN; новые входы и результаты; top5/top10. Entry match и сохранённый R не означают economic equivalence. Полная экономическая эквивалентность требует одинаковых entry/risk, exit/OPEN, activation, MFE/MAE и последовательности effective Stops/extrema (tolerance1e−8). Неактивное trail proposal до S1 само по себе не считается экономическим изменением. Отдельная атрибуция ΔR только trailing/occupancy невозможна без запрещённых дополнительных counterfactual replay и не заявляется.

CLOSED-R DD — accumulation с начальным0 в порядке exit_time/instrument/trade_id; не капитал/MTM. Occupancy=stop-checked observed bars/observed bars excluding first per instrument, без синтетических gaps. Все CSV/JSON/MD и отрицательные результаты публикуются.

Пользователь прямо разрешил GROSS_ONLY/COSTS_DEFERRED; это имеет приоритет над общей фразой AGENTS об обязательных costs. Реальная цена tick/grid, sizing, costs/funding и fill остаются отложенными. Никаких Robustness/WF/TRUE OOS/LIVE/broker endpoints/ордеров. Один Draft PR, NO MERGE / NO AUTO-MERGE, затем STOP.
