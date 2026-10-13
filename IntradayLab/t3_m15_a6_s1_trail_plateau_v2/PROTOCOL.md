# Предрегистрация — Trailing Plateau Verification v2

**2023–2024 DEVELOPMENT_EXPOSED. GROSS_ONLY / COSTS_DEFERRED / NOT_LIVE_READY.**

База: фактический GitHub main `0546e10d9977687a77638d76847b205c99223e16`, PR #505 MERGED. Основной read-only источник — `t3_m15_a6_s1_trail_optimization_v1`, исполнение — `t3_m15_execution_sensitivity_v1`. Все их опубликованные artifact inventories и исходные freeze Git blobs проверены до новых результатов (SOURCE_ORIGIN.json). Данные `market-pattern-data` pinned `f8486b446cf3d5f9f3cba6dfec32bdef8fd184c8`, clean, read-only. ROADMAP и AGENTS прочитаны; явное GROSS_ONLY/COSTS_DEFERRED пользователя имеет приоритет над общей costs-фразой AGENTS.

## Ограничение поиска и замороженный эталон

Ровно пять точек: TRAIL_350=3.500 — существующий контроль; TRAIL_3625=3.625 — новый эксперимент; TRAIL_375=3.750 — неизменный исследовательский лидер; TRAIL_3875=3.875 и TRAIL_400=4.000 — новые эксперименты. **Ровно три новых значения.** Только trail_atr меняется; одинаково для четырёх инструментов, обоих направлений и обоих лет. Других исторических replay конфигураций нет. Повтор/независимая реализация сверяют те же точки и не расширяют поиск. Ни уплотнения, ни продолжения выше 4.000/ниже 3.625, кроме существующего 3.500, после просмотра результатов. Исторические опубликованные #497/#504 учитываются как reference без их повторного испытания.

TRAIL_375 не становится окончательно утверждённой стратегией. Его original config/trades/Stops/signals/OPEN/индикаторы/results неизменны. Контроль: PF2023 2.2072776314, PF2024 1.7721337045, PF_ALL 1.9119337996, R_ALL +212.522656, 480 CLOSED/1 terminal OPEN, 9/12 +месяцев 2023, 11/12 2024, 20/24 общий, CLOSED-R DD 12.628056, ноябрь2024 44.0056% годового R. PF округляется к 10 знакам; R/DD к 6; доля к 4 процентным знакам. **Любое содержательное CONTROL несовпадение = STOP**, без новых экспериментов/подбора параметров.

## Неизменная архитектура и причинность

A6+S1: EMA75, H1 slope5, ADX14>20, ATR14, ATRMean20, H1 ATRRatio>1 и strict ratio текущего завершённого H1>предыдущего завершённого H1; Donchian20.shift(1). Initial Stop=entry−side×2×ATR завершённого signal M15; immutable initial R=abs(entry−initial Stop). S1 после favorable extreme ≥+1 initial R пережитой завершённой свечи. LONG/SHORT, без T1/ограничений часов. `engine.py` и `scalar.py` побайтно совпадают с источником #505 и #504; здесь используются только C1/NEXT_OPEN.

H1 — дневные ordinal-блоки четырёх **смежных** завершённых M15. Gapped/неполные блоки пропускаются, без перепаковки. H1 доступен лишь на четвёртом Close. Рекурсивные EMA/ATR/ADX, Donchian, позиции/S1/риск пересекают дни/сессии/границу года по исходной спецификации. Никаких новых индикаторов.

Сигнал на завершённом Close. Pending исполняется по Open непосредственно следующей смежной M15, execution Close=signal Close+15min. Вход не использует extrema execution candle. Нет смежного Open — skip, без ожидания произвольного будущего Open. Последний unresolved pending отдельный, без 2025 OHLC. Stop действует уже на execution bar. Затем adverse gap Open через активный Stop закрывает по Open. Stop-first: экстремумы exit candle не меняют S1/MFE/trailing. На пережитой свече экстремум обновляется, S1 может активироваться на Close; ratchet Stop действует со следующей наблюдаемой свечи и не ослабляется. После выхода сигнал того же Close может создать повторный вход. Occupied signals не ставятся в очередь. Terminal/period OPEN не ликвидируются.

## Порядок, Git freeze и независимая проверка

До первого нового результата подготовить и закоммитить этот протокол, SPEC, весь исполняемый/аудиторский/отчётный код, repeat/seal и synthetic tests. FREEZE.json с commit и SHA256 фиксирует код; guard каждого запуска сверяет текущие bytes и Git blobs и отсутствие results в freeze commit. Неизменность всего кода после результатов проверяется отдельно. Source quotes не копируются.

В каждом primary запуске сначала полные причинные tests, dataframe и отдельные streaming features, сверка всех 98 305 bar feature/signal/H1 availability полей между реализациями; затем **полные** TRAIL_350 и TRAIL_375 primary и scalar replay. Сравниваются все опубликованные поля #505 trade/Stop/signal/occupancy/gaps/terminal OPEN/period OPEN и все поля summary/monthly instrument×side×year/month, не только агрегаты. Abs tolerance 1e−8, никакие trade/Stop/price mismatch не игнорируются. Sparse CSV schema допускает только пустое значение для отсутствующего необязательного поля. Ветка новых 3.625/3.875/4.000 недостижима до обоих CONTROL PASS и feature PASS.

Затем полный causal replay каждого нового значения на всех четырёх forever за весь доступный 2023–2024; все Stops, S1, выходы, занятость, повторные входы и OPEN пересчитываются с сырых pinned M15. Нельзя создавать варианты фильтрацией старого trade CSV. После primary — отдельный stdlib streaming/dict/scalar replay всех пяти. Аудитор не импортирует primary engine/analysis/metrics/descriptive. Тот же автор: независимость **вычислительная**, внешнее human review PENDING. Контроль scalar повторяется до независимых кандидатов. Два свежих subprocess полных replay+audit повторяют все generated CSV/JSON/MD, включая primary/scalar control, feature receipt, reports, TABLES JSON и presentation audit; direct bytes и SHA256 должны совпасть.

## Метрики и заранее заданные таблицы

Для всех пяти: PF2023, PF2024 (минимум ≥1.70 каждый, предпочительно >2 каждый); полный PF/R/expectancy, CLOSED/terminal OPEN, годовой period OPEN; WIN/LOSS/доля/mean WIN/LOSS. Полные 24 месяца, отдельно ежегодные положительные/отрицательные/нулевые, худший месяц, последовательности отрицательных месяцев, CLOSED-R DD и losing-trade streak. Все USDRUBF/CNYRUBF/GLDRUBF/IMOEXF×LONG/SHORT по году/полностью/месяцу. GLD late start 2023-07-11 и IMOEX 2023-11-14; NO_COVERAGE до старта отличен от нулевого месяца; календарный denominator неизменно 24 или 12.

Концентрация ноября2024, лучшего/трёх лучших месяцев от **годового net signed Gross R**; R<=0 — доля NA. PF/R без них — только arithmetic sensitivity existing CLOSED, не первичная экономика/новый replay. Top5/top10 winners отдельно. CLOSED-R DD — cumsum R с начальным0, порядок exit_time/instrument/trade_id; не MTM/капитал/процентная доходность.

Полная lineage исходных входов относительно **TRAIL_350 и frozen TRAIL_375**: natural entry ID=instrument|direction|signal_time. Для ≥2R/≥5R cohorts по original exit year: preserved/improved, partially reduced, turned loss, lost entry, lost_due_occupancy, terminal OPEN, still>=threshold, matched R sum. Отдельно каждый новый entry и outcome. Economic path equivalence строже identity: entry/risk, exit/OPEN/S1/MFE/MAE и вся последовательность effective Stops/extrema. Неактивная proposal до S1 сама по себе не economic change. Механизм trailing/occupancy связан; отдельного численного causal ΔR attribution нет, дополнительные counterfactual replay запрещены.

Frequency/holding: CLOSED/calendar month, executed entries/1000 всех observed bars указанного scope. Сигналы/входы — signal year; CLOSED/holding — exit year. holding_bars — observed stop-checked bars, включая execution bar. elapsed hours = exit Close−execution Open timestamp, включая ночи/weekends/gaps; intrabar exit moment неизвестен. CLOSED-only mean/median/p90/max, p90 linear interpolation. Все instrument×side×year значения публикуются. Occupancy сохраняет исходный denominator observed bars **кроме первого** каждого инструмента. Negative-month runs публикуются с start/end/length/R, все группы; нулевой/NO_COVERAGE месяц прерывает отрицательную серию.

## Решение без нового рейтинга

Главный вопрос — устойчив ли соседний участок около3.75, а не максимум одной точки. Оценка описательная, без подбора новых cutoffs, score/весов и без автоматического выбора maximal PF. A: сопоставимая экономика соседей, ежегодный минимум и месячная регулярность. B: улучшение на4.00 при недостаточной регулярности/соседней устойчивости, не объявлять граничную точку победителем. C: только3.75 проходит, повышенный риск fitting, без дополнительных коэффициентов ради PASS. D: улучшение PF сопровождается худшими месяцами/DD/retention; оценить компромисс. Возможна смесь сценариев с явными фактами.

Обязательно отдельно ответить: сохраняется ли TRAIL_375 как лучший сбалансированный кандидат; подтверждена ли соседняя область; улучшены ли месяцы; снижена ли концентрация2024; как изменился SHORT2024; негативные эффекты; **закончить ли численную Optimization trailing и перейти к исследованию качества входов**. Переход лишь рекомендовать, не запускать. Бесконечное расширение trailing не разрешено при любом исходе.

## Scope и завершение

Изменения только `IntradayLab/t3_m15_a6_s1_trail_plateau_v2/`. ROADMAP, предыдущие исследования, котировки и исходный checkout неизменны. TradingSystemLab/робот/стратегии/results/config запрещено менять. Seal проверяет actual GitHub main, frozen hashes, protected reference SHA256, staged/committed diff, неизменный TradingSystemLab Git tree, clean pinned data и source checkout.

Полные CSV/JSON/MD, отрицательные результаты и любые технические ошибки сохраняются. **Один Draft PR. NO MERGE / NO AUTO-MERGE. STOP для независимого аудита.** Не запускать Robustness/Walk Forward/TRUE OOS/LIVE/брокерские действия. 2023–2024 не независимое доказательство будущей доходности. Costs/funding/tick/grid/sizing/реальные fills отложены; Next Open не гарантирует broker fill.
