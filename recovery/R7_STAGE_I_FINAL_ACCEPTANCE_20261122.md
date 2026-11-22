# R7 Stage I — окончательное решение о H1 audit_only и handoff в Kimi

**Дата:** 22.11.2026. **Проверенная база GitHub:** `alkospacer123/market-pattern-discovery/main=bb8c46c1db89ca2b5311f22c755bb4e51ce8f7d6` до документационного PR #589. **Вердикт:** `R7_MAIN_CLEANUP_COMPLETE_IN_APPROVED_SCOPE / RETAIN_H1_AUDIT_DEPENDENCY / NO_LIVE_CHANGE`.

## Что действительно убрано

- [PR #583](https://github.com/alkospacer123/market-pattern-discovery/pull/583) — 11 594 исторических A/B/C + BBW Git-файла.
- [PR #586](https://github.com/alkospacer123/market-pattern-discovery/pull/586) — 233 root legacy объекта; исходная отдельная Market Pattern Discovery доступна по защищённому `archive/pre-root-legacy-20261122@09bca5641cb5bb367e84505ebfc6f8c7f35e2620`.
- [PR #587](https://github.com/alkospacer123/market-pattern-discovery/pull/587) и [#588](https://github.com/alkospacer123/market-pattern-discovery/pull/588) MERGED, исходные refs и source blobs проверены; [#580](https://github.com/alkospacer123/market-pattern-discovery/pull/580) и [#581](https://github.com/alkospacer123/market-pattern-discovery/pull/581) CLOSED WITHOUT MERGE, ветки сохранены. Основные пять системных trees не изменены.

## Доказанная зависимость, которую нельзя удалить ради косметики

Кандидат [#590](https://github.com/alkospacer123/market-pattern-discovery/pull/590) предлагал выведение последних 16 файлов `audit_only/stop_tick_grid_20261012/`. Папка имела идентичный archived Git tree `1a184db9d4d856948611442262635573a6699d10`, archive blob parity 16/16. Однако точный [CI run 44998434881](https://github.com/alkospacer123/market-pattern-discovery/actions/runs/44998434881) остановил удаление (`BROKEN_ACTIVE_IMPORT_OR_SCRIPT_REFERENCE`):

1. `TradingSystemLab/stage8_robot/signal_execution_diagnostic.py` — Git blob `33f20607c828223d426718768ff3f4669dd31956`. `ACCEPTED=ROOT/'audit_only/stop_tick_grid_20261012/full_available_raw_signals.csv'`, затем `pd.read_csv(ACCEPTED)` в `diagnose()`; файла в main после удаления не было бы.
2. `TradingSystemLab/stage8_robot/tests/replay_stop_tick_grid.py` — Git blob `23889f765919866357cf034a7c725fab81f4c840`. Добавляет каталог audit в `sys.path`, импортирует `from audit import authenticate_exact_sources, authority, HASHES, S5, S6, economics`, читает `lifecycle_admitted_entries.csv` и `full_available_raw_signals.csv`. Это фактические H1 offline research/test dependencies.

**Решение:** PR #590 закрыт **без Merge**, исходная branch/CI история сохранена, `audit_only` остаётся в `main` **целиком и побайтово неизменным**. Цель «чистый GitHub» означает чистую структуру и корректные статусы, а не удаление необходимых CSV/модулей. Не переписывать H1 code только для удаления каталога и не подменять доказательный FAIL PASS.

**Граница вывода:** H1 diagnostic/replay — offline, не V20 LIVE execution. Не утверждать, что эти модули обязательно исполняются текущим V20 worker или FINAM. Также не утверждать, что их физическая воспроизводимость независимо повторена 22.11: CI был source/static-only, необходимый frozen data replay не запускался. Внешние потребители/ZIP/XLSX неизвестны.

## Состояние после R7 и следующий этап

- Рабочий GitHub содержит V20, Control Center, TRL, необходимые H1/M15 исходники/исследования и 16 H1 audit объектов; старое автономное root ядро отсутствует.
- Kimi должен читать `audit_only` только в запросном H1 research-контексте, **не** как четвёртый проект знаний и **не** как действующий LIVE runbook.
- [Классификация retained research](RETAINED_RESEARCH_CLASSIFICATION_2026-11-22.md), [Roadmap](../ROADMAP.md), [паспорта трёх систем](README.md) и [Kimi Phase II package](kimi/README.md) образуют навигацию без удаления независимых первоисточников.
- **Stage I принят в ограниченном объёме**, защита важных деревьев/архивных refs сохранена, начало Stage II допустимо. **Нет** подтверждённого Kimi setup/exam, FINAM LIVE review или независимого Recovery/cold restore.

**Безопасность:** ни CI, ни этот GitHub handoff не изменяли установленный на Intel код, Windows Scheduled Tasks, SLTP, kill switch, брокерские позиции/заявки, DPAPI или реальные торговые данные.
