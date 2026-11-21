# H1, M15 и старое ядро: карта роли, сохранности и осторожной уборки

Срез после merged #583 (GitHub recursive tree untruncated). **Много файлов не означает ненужность.**

| Путь | Количество и роль | Решение |
| --- | --- | --- |
| `TradingSystemLab/` | 3 059 файлов, 2 508 в `results/`, 252 в `stage8_robot/`; V20 imports `stage8_robot` | **KEEP**, H1 historic freeze/tests/research, no auto LIVE |
| `IntradayLab/` | 2 722, 490 в `results/`, 1 979 в семействах `t3_m15_*`; V20 imports `core` | **KEEP**, M15 frozen baselines/results, core shared |
| `src/` и `tests/` | 86 и 50: старое Market Pattern Discovery core и тесты | **KEEP_PENDING_DEPENDENCY_AUDIT** |
| `docs/`, `config/`, `results/`, `audit_only/` | 34, 17, 17, 16: исходные методы, конфиги и аудит | **KEEP_PENDING_PROVENANCE_AUDIT** |
| `pyproject.toml`, `.github/workflows/` | Исполняемая конфигурация и обязательная CI | **KEEP**, не ломать Main Admission / imports |

Старый корневой AGENTS с запретом 2025 относится к frozen историческому research, **не** универсален для V20/TRL. Проектный research split старой H1/M15 можно сохранить для воспроизведения, но не навязывать актуальной TRL. READMEs H1/M15 содержат датированные LIVE-статусы, не новую брокерскую телеметрию.

**Удалять только при доказанном gate:** точный список+SHA → imports/CI/config/links → уникальность исходного исследования → приватность и проверенный архив → offline regression → отдельное разрешение на Merge. Git history и branch сами по себе не являются автономным Recovery. При отсутствии доказательства — KEEP.
