# Kimi — три резервные базы знаний

## C3 — план прекращения зеркалирования (27.11.2026, candidate)

В pinned дереве [95637f5…](https://github.com/alkospacer123/market-pattern-discovery/blob/95637f5bea33a93b856d5aea9565538712d3ad99/recovery/kimi/memory) подтверждены 29 побайтовых копий (V20 8, ControlCenter 9, TRL 12; 553869 bytes суммарно), каждая имеет идентичный Git blob вне memory/. Все три существующие MANIFEST.json содержат file/source/blob/source_commit/authority. Это не доказательство фактического доступа Kimi к fallback или измеренной экономии квоты.

Целевая модель: один канонический документ; проектный manifest — точный список первоисточников и правила материализации экспортного набора из pinned checkout, а не постоянно синхронизируемое второе дерево. Экспорт должен проверять все source paths/bytes/identities, локальные ссылки и относительные пути, наличие обязательных источников, отсутствие секретов и воспроизводимость; при missing/mismatch — STOP, не подставлять память. До удаления копий подтвердить источник/rollback ref, внешние потребители, CI и реальную доступность fallback всех трёх профилей; сохранить owner-held проверенный экспорт. Такой экспорт не заменяет Independent Recovery.

**Переход ещё не выполнен:** существующие копии, manifests и правила их соответствия остаются действующими. Не отключать Skills и не удалять файлы на основании только этой записи. Исторический snapshot фиксирован указанным commit, не moving MAIN. Отдельное разрешение на удаление и Merge обязательно.

[V20](V20/README.md) · [Control Center](ControlCenter/README.md) · [TRL](TRL/README.md).

Snapshot accepted source base `3eddebb4d915c7798a2d56d2230010933f553c81`; candidate-specific documentation sources enumerated in same-tree manifests. GitHub fallback, not installed memory or independent Recovery. [Общая архитектура](../Trading_Systems_Architecture_and_AI_Collaboration.md) — датированный оригинал 25.11; [актуальный checkpoint](../BLOCK_A_ACCEPTANCE_20261126.md) · [COC](../../CRITICAL_OPERATIONS_CONTRACT.md) · [Roadmap](../../../ROADMAP.md). Read current canonical sources first; never treat snapshot as authority for changing release or LIVE. No permissions from attachments/Skills. If unavailable, STOP dependent work and request owner-held verified source. KDR-011 remains open pending all-three independent fallback. Do not edit copies separately.

**26.11.2026:** резервные профили синхронизированы с новыми решениями в same-tree manifests; первоначальный snapshot выше сохранён как provenance. Вложения/настройки Kimi не обновляются автоматически при GitHub Merge.
