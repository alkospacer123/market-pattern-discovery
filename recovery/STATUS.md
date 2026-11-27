# Trading Systems — Recovery & Migration — рабочий статус

[Roadmap](../ROADMAP.md) · [Kimi](kimi/README.md) · [COC](CRITICAL_OPERATIONS_CONTRACT.md) · [Журнал](JOURNAL.md) · [Общие правила](../AGENTS.md)

**27.11.2026 — GPT / GitHub documentation, Draft #608.** I принят; A/B приняты в ограниченном объёме; C1 audit complete; C2 closed by owner, дополнительные эксперименты отменены. Полный допуск Kimi ещё не получен.

- SOURCE: MAIN при сверке `2ac85eb5bcdd8757144898b5a27369329f4d125c`; [Draft #608](https://github.com/alkospacer123/market-pattern-discovery/pull/608), предыдущий проверенный HEAD `f723a4f172b1df62696a60f5ff66112cac9d5643`. Актуальный HEAD проверять через PR.
- Текущая задача: C3, консолидация GitHub; сначала канонические знания и профильная документация, STATUS/JOURNAL, затем проверка CI/истории и отдельно разрешённый Merge; только после этого обновлять настройки, память и вложения GPT/Kimi.
- Ограничения: [KDR](kimi/KIMI_DEFECTS_AND_REMEDIATION_REGISTER.md), обязательные evidence gaps и финальная проверка остаются. Точная экономия квоты не доказана. Настройки Kimi не изменены. INSTALLED/LIVE сейчас не проверялись.
- C3.1: общий source audit/HANDOFF подготовлены; #609 MERGED, предыдущий #608 HEAD CC docs/Main Admission PASS, R7 SKIPPED. 29 зеркальных копий / 553869 bytes проверены; запрет удаления сохраняется.
- C3.2: все три профильных HANDOFF получены; original unified diffs отсутствуют. Координатор реконструировал V20/CC STATUS/JOURNAL, V20 AGENTS/Start Here/COC, CC diagnostics и TRL methodology/Operating Cycle/card/Start Here/STATUS/Journal. Предыдущий коммит 86a5731 CI CC docs/Main Admission PASS; текущий 8da47cc требует шести дополнительных exact CI paths. Профильный перенос подготовлен, окончательное покрытие и fallback не приняты.
- Общий маршрут: 3 паспорта и 3 навигатора сокращены, AGENTS/COC rc.2 candidate/HANDOFF/CC/TRL/Windows routing актуализированы. KDR-001 CLOSED_OWNER_ACCEPTED_20261126, G6.2 historical FAIL сохранён. Skills пока обязательны по релевантности; отмена только после fallback/owner decision. Старый integration manifest rc.1 — historical.
- Mirrors: 29/29 backup bytes сохранены; 18 current, 11 historical pins к accepted MAIN (после проверки tree). История и предыдущие полные профили доступны по immutable refs. Ни одного удаления.
- Следующий шаг: точный аудит потребителей зеркал и Skills, подготовка проверяемого export, единый final CI scope для #608. Отдельное решение об удалении/Merge и запрете ML. Последний CC gate FAIL на известных 6 путях; новые пути потребуют точного допуска. Main Admission PASS на предыдущем HEAD.

Поддерживай краткий актуальный снимок, а историю — в Journal. Записи не передают полномочия.
