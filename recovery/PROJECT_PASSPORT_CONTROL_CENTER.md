# Control Center V20 — паспорт

**ACTIVE operator panel, not a trading algorithm.** Каталог `ControlCenter/`; действующий UI `v20_app.py`, адаптер `v20_admin_control.py`, `controller/`, `cc/`, `tests/`. READONLY refresh и операторский CC-07 — отдельные контуры. CC-03/H1/8501 — сохранённая историческая ветвь, не V20.

## Канонические источники по задаче

- [STATUS](../ControlCenter/STATUS.md) и [JOURNAL](../ControlCenter/JOURNAL.md) — актуальный срез, принятые SOURCE changes и installed/LIVE gaps.
- [Start Here](../ControlCenter/docs/V20_START_HERE_SOURCE_MAP.md), [README](../ControlCenter/README.md) и [CC-08](../ControlCenter/docs/V20_CC08_OPERATIONS.md) — архитектура, установка, диагностика и источник состояния.
- [CC-07 command contract](../ControlCenter/docs/V20_CC07_COMMAND_CONTRACT.md), [data/security/tests](../ControlCenter/docs/V20_DATA_SECURITY_TESTS.md), [COC](CRITICAL_OPERATIONS_CONTRACT.md) — gates, unknown outcome, provenance, freshness, regressions.
- [Общий AGENTS](../AGENTS.md), [HANDOFF](kimi/EXAM_AND_HANDOFF.md) — полномочия, Git identity и совместная работа.

HTTP 200, локальный HEALTHY, Task Running и датированная установка не доказывают broker FLAT/SLTP. FAILED_UNKNOWN не повторять. Не выполнять операторские команды, FINAM, Task changes, установку или rollback без отдельного разрешения. H1/CC-03 frozen provenance сохраняется.

**C3.2 candidate 27.11.2026:** [предыдущая редакция](https://github.com/alkospacer123/market-pattern-discovery/blob/2ac85eb5bcdd8757144898b5a27369329f4d125c/recovery/PROJECT_PASSPORT_CONTROL_CENTER.md) сохраняет датированный installed locator/blob, решение по #602 и прежний exam scope. Текущий статус и доказательства — профильный STATUS/JOURNAL; повторных экзаменов не требуется. Fallback/Skill migration не приняты.
