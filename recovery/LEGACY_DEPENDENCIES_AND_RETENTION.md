> **Дополнение 22.11.2026:** эта таблица относится к предложенному целостному выносу root legacy, а не уже слитому `main`. [Архивный снимок](https://github.com/alkospacer123/market-pattern-discovery/tree/09bca5641cb5bb367e84505ebfc6f8c7f35e2620), [gate](R7_ROOT_LEGACY_EXTRACTION_GATE_2026-11-22.md). Главные H1/M15/TRL корни и Git object modes неизменны. Статус **DRAFT / MERGE BLOCKED**.

# H1, M15 и старое ядро: карта роли, сохранности и осторожной уборки

Срез после merged #583 (GitHub recursive tree untruncated). **Много файлов не означает ненужность.** Подробная [путь-за-путём ревизия старой корневой платформы](ROOT_LEGACY_AUDIT_2026-11-21.md) охватывает `docs/`, `research/`, `schemas/`, `scripts/` и шесть отчётов в корне.

| Путь | Количество и роль | Решение |
| --- | --- | --- |
| `TradingSystemLab/` | 3 059 файлов, 2 508 в `results/`, 252 в `stage8_robot/`; V20 imports `stage8_robot` | **KEEP**, H1 historic freeze/tests/research, no auto LIVE |
| `IntradayLab/` | 2 722, 490 в `results/`, 1 979 в семействах `t3_m15_*`; V20 imports `core` | **KEEP**, M15 frozen baselines/results, core shared |
| `src/` и `tests/` | 86 и 50: старое Market Pattern Discovery core и тесты | **DRAFT_ARCHIVE_EXTRACTION**, прежние Git blobs доступны по pinned archive commit; не Merge до зависимости/реплея |
| `docs/`, `config/`, `results/` | 34, 17, 17: старые документы/конфиги/результаты | **DRAFT_ARCHIVE_EXTRACTION**, сохранены исходники в `archive/pre-root-legacy-20261122` | 
| `audit_only/` | 16: исторический stop-tick-grid с H1-связями | **KEEP IN MAIN**, не включён в удаление |
| корневой `pyproject.toml` | Old Market Pattern Discovery packaging/CLI | **DRAFT_ARCHIVE_EXTRACTION**, исторические команды запускать только в архивном checkout |
| `.github/workflows/` | Действующие CI | **KEEP IN MAIN**, необходимо доказать compatibility после выноса |

Старый корневой AGENTS с запретом 2025 относится к frozen историческому research, **не** универсален для V20/TRL. Проектный research split старой H1/M15 можно сохранить для воспроизведения, но не навязывать актуальной TRL. READMEs H1/M15 содержат датированные LIVE-статусы, не новую брокерскую телеметрию.

**Удалять только при доказанном gate:** точный список+SHA → imports/CI/config/links → уникальность исходного исследования → приватность и проверенный архив → offline regression → отдельное разрешение на Merge. Git history и branch сами по себе не являются автономным Recovery. При отсутствии доказательства — KEEP.
