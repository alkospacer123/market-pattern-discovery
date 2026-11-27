# Trading Systems — Recovery & Migration — рабочий статус

[Roadmap](../ROADMAP.md) · [Kimi](kimi/README.md) · [COC](CRITICAL_OPERATIONS_CONTRACT.md) · [Журнал](JOURNAL.md) · [Общие правила](../AGENTS.md)

**27.11.2026 — GPT / GitHub documentation, Draft #608.** I принят; A/B приняты в ограниченном объёме; C1 audit complete; C2 closed by owner, дополнительные эксперименты отменены. Полный допуск Kimi ещё не получен.

- SOURCE: MAIN при сверке `373d7aea7cba69fa1f01c4378b06488554e788f7`; [Draft #608](https://github.com/alkospacer123/market-pattern-discovery/pull/608), предыдущий проверенный HEAD `95637f5bea33a93b856d5aea9565538712d3ad99`. Актуальный HEAD проверять через PR.
- Текущая задача: C3, консолидация GitHub; сначала канонические знания и профильная документация, STATUS/JOURNAL, затем проверка CI/истории и отдельно разрешённый Merge; только после этого обновлять настройки, память и вложения GPT/Kimi.
- Ограничения: [KDR](kimi/KIMI_DEFECTS_AND_REMEDIATION_REGISTER.md), обязательные evidence gaps и финальная проверка остаются. Точная экономия квоты не доказана. Настройки Kimi не изменены. INSTALLED/LIVE сейчас не проверялись.
- C3.1: начат перенос общего source audit и HANDOFF в существующие документы. 29 точных копий / 553869 bytes проверены по tree/blob. CI исходного HEAD: CC docs FAIL (STATUS/JOURNAL отсутствуют в allowlist), Main Admission PASS, R7 SKIPPED. Нужна отдельная узкая CI-актуализация без ослабления protected source gates; запрет удаления в текущем mixed docs gate сохраняется.
- Следующий шаг: профильные чаты сверяют уникальные требования Skills, паспорта/source maps и статусы; затем проверка потребителей, безопасного fallback, согласование удаления и CI scope. Не менять runtime, Intel, FINAM или LIVE.

Поддерживай краткий актуальный снимок, а историю — в Journal. Записи не передают полномочия.
