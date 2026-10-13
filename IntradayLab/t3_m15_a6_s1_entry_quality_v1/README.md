# T3/M15 A6+S1 Entry Quality Diagnostics v1

**Результат: `NO_SUPPORTED_ENTRY_CHANGE`.** SHORT2024 чаще теряет промежуточное наблюдаемое продолжение0,5–1 initial R до S1. Доступные признаки не дают убедительного общего входного разделителя, сохраняющего крупные тренды по обоим годам/рынкам/слабым месяцам. Новые фильтры и стратегии не запускались.

**GROSS_ONLY / COSTS_DEFERRED / NOT_LIVE_READY. 2023–2024 DEVELOPMENT_EXPOSED.**

[Русский отчёт](results/REPORT.md), [все24 месяца](results/MONTHLY_DETAIL.md), [все фиксированные разрезы](results/CUTS_DETAIL.md), [машинное решение](results/DECISION.json).

CONTROL: actual main `57599b39ed1d7a93a84b97747388408291f30276` уже включает MERGED #505/#506. Data pin `f8486b446cf3d5f9f3cba6dfec32bdef8fd184c8`. Единственная конфигурация A6+S1 / NEXT_OPEN / TRAIL_375, без T1. Полностью воспроизведены исходные trades, Stop decisions, signal decisions, gaps, period/terminal OPEN и все опубликованные summary/monthly поля #505, журналы #506 и user targets. Любое расхождение CONTROL останавливает pipeline.

480 CLOSED/1 OPEN, PF2023 2,207278 / R+90,390672; PF2024 1,772134 / R+122,131984; полный PF1,911934 / R+212,522656,20/24 положительных месяцев, DD12,628056R. SHORT2024 148 CLOSED/PF1,473497/R+38,321290. Все frozen параметры совпадают с #505/#506; engine/scalar/metrics — побайтные копии. [Происхождение](SOURCE_ORIGIN.json), [PR context](PR_CONTEXT.json), [SPEC](SPEC.json), [протокол](PROTOCOL.md), [freeze receipt](FREEZE.json).

CSV/JSON содержат все2017 исходных сигналов,480 CLOSED features/outcomes,1 OPEN,54 annual/full scopes,432 month/instrument/direction cells,1674 fixed cuts,3168 feature distributions,2340 funnel rows,639 matched instrument/dates,24 matched cohorts,83 original≥2R winner IDs и216 outcome-anatomy rows. Все≥5R отмечены в winner_entries. Полный trade/Stop/entry/gap/OPEN журнал — `results/control/`; обе независимые репродукции сохранены. Raw quotes не копируются.

Независимая вычислительная сверка: stdlib/scalar features/replay/диагностика, primary pandas/object. Аудитор не импортирует primary engine/diagnostics/metrics. Общие metadata/serialization/comparison; автор один, человеческое ревью PENDING. [Аудит](audit/AUDIT_RESULT.json), [сверка отчётных дополнений и выводов](audit/CONCLUSION_REVIEW.json), [25 Markdown tables](audit/PRESENTATION_AUDIT.json), [два побайтных повтора](REPEATABILITY.json), [защита области](SCOPE_CHECK.json), [SHA inventory](ARTIFACT_SHA256.json).

Команды из корня репозитория, Python3.12 и requirements.txt; runtime — в source manifest:

```sh
export PYTHONDONTWRITEBYTECODE=1
python IntradayLab/t3_m15_a6_s1_entry_quality_v1/run.py --data-root /workspace/market-pattern-data
python IntradayLab/t3_m15_a6_s1_entry_quality_v1/audit.py --data-root /workspace/market-pattern-data
python IntradayLab/t3_m15_a6_s1_entry_quality_v1/report.py
python IntradayLab/t3_m15_a6_s1_entry_quality_v1/audit_presentation.py
python IntradayLab/t3_m15_a6_s1_entry_quality_v1/repeat.py
python IntradayLab/t3_m15_a6_s1_entry_quality_v1/seal.py
```

35 causal fixtures:26 execution и9 diagnostic. Source readers timestamp-first и прекращают чтение до numeric suffix2025+. Full hashes — opaque bytes. Day/session rules эталона сохранены; MFE — lower bound survived bars, Stop-candle extrema неизвестны. Available signal fields отделены от future market windows/trade outcomes. Отсев по CSV не моделируется; новые occupancy/повторные входы неизвестны без separately authorized replay. Простые отчётные outcome bands написаны после получения разрезов и независимо сверены; frozen computational code после результатов не менялся.

Все добавления repo только в этом каталоге. TradingSystemLab, live robot, ROADMAP, прежние исследования, оригинальный checkout и data read-only. Costs/slippage/funding/ticks/sizing/капитал/live fills отложены. Никаких Optimization/Robustness/Walk Forward/TRUE OOS/trading. Один **Draft PR**, безMerge/Auto-Merge; **STOP** после создания.
