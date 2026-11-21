# R7 — единое выведение старой Market Pattern Discovery из рабочего корня (22.11.2026)

**СТАТУС: DRAFT_CANDIDATE / ARCHIVE_GIT_REF_CREATED / MAIN_UNCHANGED / DELETE_GATE_BLOCKED.** Это PR-кандидат, не утверждение, что перенос уже произведён в `main`.

## Источник и архив

- Исходный `main` до этого этапа: `e52dd90ef3e85c6ccc3b075f934df3ea8f5ffa8d` (#583 и #584 уже merged); полный оригинал доступен в [immutable-by-SHA дереве](https://github.com/alkospacer123/market-pattern-discovery/tree/09bca5641cb5bb367e84505ebfc6f8c7f35e2620).
- Создана отдельная ветка-указатель `archive/pre-root-legacy-20261122` на `09bca5641cb5bb367e84505ebfc6f8c7f35e2620` (четыре документационных коммита после `e52dd90ef3e85c6ccc3b075f934df3ea8f5ffa8d`, непосредственный родитель cleanup-кандидата). Поэтому точный Git SHA и mode совпадают для **всех 234** удаляемых файлов. Старый `archive/pre-r7-cleanup` остаётся на `f15d565755b996252081ed49ed5a094ee1e8d820` без изменений. **Ветки и Git history не являются автономной резервной копией**; финальный Recovery по дорожной карте — позже.
- В отдельном публичном `market-pattern-archive` ничего не публиковалось; в том числе не переносились приватные внешние артефакты, Windows-файлы, DPAPI, журналы и торговые настройки.

## Единственный согласованный пакет удаления из активного дерева

| Исходный root path | Git blobs до выноса | Классификация |
| --- | ---: | --- |
| `docs/` | 34 | Старые отчёты autonomous/Phase 4–7 |
| `research/` | 4 | Историческая EXP-000001 и гипотезы |
| `schemas/` | 6 | Контракт старого research движка |
| `scripts/` | 7 | Старые CLI запускатели |
| `src/` | 86 | Старое ядро `market_pattern_discovery` |
| `tests/` | 50 | Тесты этого ядра |
| `config/` | 17 | Конфиги и четыре binary .u32 |
| `results/` | 17 | Старые execution/research результаты |
| `evidence/` | 5 | Исторический audit evidence |
| Шесть корневых `ARTIFACT_*`, `CURRENT_ARTIFACT_*`, `*MEMORY*`, `SMOKE_RUN_*` отчётов | 6 | Legacy smoke/handoff, не V20 LIVE |
| `pyproject.toml`, `research_domains.md` | 2 | Packaging старого ядра и legacy domains |
| **Итого** | **234** | 9 каталогов + 8 одиночных файлов |

**Не удаляются и не изменяются:** `V20_TradingSystem_M15/`, `ControlCenter/`, `TradingResearchLab/`, `TradingSystemLab/`, `IntradayLab/`, `audit_only/`, `.github/`; FINAM, Windows Tasks и установленный LIVE не затрагиваются. `recovery/` и root документация дополняются навигацией, без правок runtime-кода.

## Gate перед Merge

1. Автоматически сравнить исходный `main`, архивную ветку на `09bca5641cb5bb367e84505ebfc6f8c7f35e2620` и кандидат: **234 удаления только по указанным путям**, ни одной модификации Git SHA/mode retained исходников, все 234 архивных Git objects доступны.
2. Пройти полную обратную проверку импортов и путей (`src.market_pattern_discovery`, `market_pattern_discovery.*`, `docs/`, `config/`, `schemas/`, scripts/CLI, `pyproject`) в V20/CC/TRL/H1/M15/recovery и GitHub workflow. Исторические ссылки исправить на pinned archive commit, активные зависимости — сохранить или мигрировать. Нельзя ошибочно трактовать 0 совпадений в выборке как closure.
3. Изолированно сравнить offline regression retained V20/CC/H1/M15/TRL и проверить воспроизводимость старого research **из архивного checkout**, включая binary/index, JSON/CSV. Отдельно снять известный `HOLD_SYMLINK_NATIVE` и проверить целостность старого тестового окружения.
4. CI Main Admission должен быть зелёным на **точном финальном head SHA**. Это не LIVE/FINAM/SLTP PASS. По существующему workflow значительная часть R7-защитных jobs привязана к #583 и не запускается автоматически на новом PR.
5. Выполнить операторский review полного diff, GitHub metadata/refs, protected dependencies, возможных внешних данных и только затем явно разрешить **отдельный Merge**. До приёмки старый `main` неизменен.

**Цель:** активная база знаний Kimi содержит только V20/CC/TRL и необходимые общие H1/M15/audit зависимости; восстановление замороженных старых экспериментов — через pinned archive SHA, без объявления их новым LIVE.
