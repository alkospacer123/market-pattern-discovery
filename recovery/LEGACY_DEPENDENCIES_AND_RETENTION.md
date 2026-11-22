> **R7 final cleanup transition 22.11.2026:** original 16-file `audit_only` H1 STOP/TICK GRID dataset is staged for removal from the daily `main` tree after exact archive parity and source/link scan. The original is pinned by [archive passport](H1_STOP_TICK_GRID_ARCHIVE_20261012.md) at protected commit `09bca5641cb5bb367e84505ebfc6f8c7f35e2620`; historic `KEEP IN MAIN` wording below remains dated evidence of pre-final R7, not a current instruction. Full external dependency closure is UNKNOWN; no H1/M15/V20/CC/TRL source will be modified.

> **POST-MERGE update 22.11.2026:** #585 и #586 фактически MERGED, `main=4f118ee1cdeced15406136401faabe4fdc3bb847`. Слова «не объединён», «draft» и прежние status snapshot ниже исторические, не актуальный GitHub статус. Новый [реестр retained research](RETAINED_RESEARCH_CLASSIFICATION_2026-11-22.md) содержит точные Git trees H1/M15, 22 M15 studies и решение **KEEP audit_only**. Никаких новых удалений не разрешено.

> **Срез и правило чтения 22.11.2026:** таблица описывает структуру именно очищенного дерева #586, а не утверждает, что GitHub `main` уже объединён. [Закреплённый архив](https://github.com/alkospacer123/market-pattern-discovery/tree/09bca5641cb5bb367e84505ebfc6f8c7f35e2620), [проверки и исторические ограничения](R7_ROOT_LEGACY_EXTRACTION_GATE_2026-11-22.md); принятие в `main` определяется только фактическим статусом PR #585 → #586 и SHA ветки. Деревья защищённых V20/CC/TRL/H1/M15/audit не менялись относительно базы #585.

# H1, M15 и старое ядро: карта роли, сохранности и осторожной уборки

Срез после merged #583 (GitHub recursive tree untruncated). **Много файлов не означает ненужность.** Подробная [путь-за-путём ревизия старой корневой платформы](ROOT_LEGACY_AUDIT_2026-11-21.md) охватывает `docs/`, `research/`, `schemas/`, `scripts/` и шесть отчётов в корне.

| Путь | Количество и роль | Решение |
| --- | --- | --- |
| `TradingSystemLab/` | 3 059 файлов, 2 508 в `results/`, 252 в `stage8_robot/`; V20 imports `stage8_robot` | **KEEP**, H1 historic freeze/tests/research, no auto LIVE |
| `IntradayLab/` | 2 722, 490 в `results/`, 1 979 в семействах `t3_m15_*`; V20 imports `core` | **KEEP**, M15 frozen baselines/results, core shared |
| `src/` и `tests/` | 86 и 50: старое Market Pattern Discovery core и тесты | **ARCHIVED_IN_THIS_TREE**, старые blobs доступны по архивному SHA; реестр исторических потребителей остаётся с его исходными refs |
| `docs/`, `config/`, `results/` | 34, 17, 17: старые документы/конфиги/результаты | **ARCHIVED_IN_THIS_TREE**, сохранены исходники в `archive/pre-root-legacy-20261122` | 
| `audit_only/` | 16: исторический stop-tick-grid с H1-связями | **KEEP IN MAIN**, не включён в удаление |
| корневой `pyproject.toml` | Old Market Pattern Discovery packaging/CLI | **ARCHIVED_IN_THIS_TREE**, исторические команды запускать только в архивном checkout |
| `.github/workflows/` | Действующие CI | **KEEP IN MAIN**, необходимо доказать compatibility после выноса |

Старый корневой AGENTS с запретом 2025 относится к frozen историческому research, **не** универсален для V20/TRL. Проектный research split старой H1/M15 можно сохранить для воспроизведения, но не навязывать актуальной TRL. READMEs H1/M15 содержат датированные LIVE-статусы, не новую брокерскую телеметрию.

**Удалять только при доказанном gate:** точный список+SHA → imports/CI/config/links → уникальность исходного исследования → приватность и проверенный архив → offline regression → отдельное разрешение на Merge. Git history и branch сами по себе не являются автономным Recovery. При отсутствии доказательства — KEEP.

**22.11 дополнительный защитный случай:** корневой `research_domains.md` не удаляем без замены — `TradingSystemLab/README.md` ссылается на него. В PR #586 предусмотрен малый **archive pointer** без изменения H1/CC дерева и отдельный автоматический static link gate. Оригинальный CC03 `scope_audit.py` остаётся с известным historical mismatch к уже изменившемуся корню. Отдельная Windows-native приёмка исходного CC03 (757 PASS, 15 предусмотренных skip, 15/15 остальных этапов) и новая immutable Git-tree проверка успешно прошли; старый scope failure не объявляется PASS. См. датированный gate.
