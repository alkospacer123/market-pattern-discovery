# Trading Systems — Recovery & Migration — рабочий статус

[Roadmap](../ROADMAP.md) · [Kimi](kimi/README.md) · [COC](CRITICAL_OPERATIONS_CONTRACT.md) · [Журнал](JOURNAL.md) · [Общие правила](../AGENTS.md)

**27.11.2026 — GPT / GitHub documentation, Draft #608.** I принят; A/B приняты в ограниченном объёме; C1 audit complete; C2 closed by owner, дополнительные эксперименты отменены. Полный допуск Kimi ещё не получен.

- SOURCE: MAIN при сверке `2ac85eb5bcdd8757144898b5a27369329f4d125c`; [Draft #608](https://github.com/alkospacer123/market-pattern-discovery/pull/608), предыдущий проверенный HEAD `f6c28ad4027fdc1fdfc8c279671f5c3001f3bd1e`. Актуальный HEAD проверять через PR.
- Текущая задача: C3, консолидация GitHub; сначала канонические знания и профильная документация, STATUS/JOURNAL, затем проверка CI/истории и отдельно разрешённый Merge; только после этого обновлять настройки, память и вложения GPT/Kimi.
- Ограничения: [KDR](kimi/KIMI_DEFECTS_AND_REMEDIATION_REGISTER.md), обязательные evidence gaps и финальная проверка остаются. Точная экономия квоты не доказана. Настройки Kimi не изменены. INSTALLED/LIVE сейчас не проверялись.
- C3.1: общий source audit/HANDOFF подготовлены; #609 MERGED, предыдущий #608 HEAD CC docs/Main Admission PASS, R7 SKIPPED. 29 зеркальных копий / 553869 bytes проверены; запрет удаления сохраняется.
- C3.2: 3 профильных HANDOFF получены, оригинальные unified diff недоступны. Реконструкция координатором: V20/CC STATUS/JOURNAL, V20 AGENTS/Start Here и COC. CC diagnostics, TRL документы, переход mirrors/manifests и routing Skills остаются; original patches не применялись.
- Следующий шаг: проверить CI, согласовать точный оставшийся scope, собрать и проверить fallback; отдельные решения об удалении, отключении Skill и Merge. Не менять runtime, Intel, FINAM или LIVE.

Поддерживай краткий актуальный снимок, а историю — в Journal. Записи не передают полномочия.
