# Trading Systems — Recovery & Migration — рабочий статус

[Roadmap](../ROADMAP.md) · [Kimi](kimi/README.md) · [COC](CRITICAL_OPERATIONS_CONTRACT.md) · [Журнал](JOURNAL.md) · [Общие правила](../AGENTS.md)

**27.11.2026 — GPT / GitHub documentation, Draft #608.** I принят; A/B приняты в ограниченном объёме; C1 audit complete; C2 closed by owner, дополнительные эксперименты отменены. Полный допуск Kimi ещё не получен.

- SOURCE: MAIN при сверке `2ac85eb5bcdd8757144898b5a27369329f4d125c`; [Draft #608](https://github.com/alkospacer123/market-pattern-discovery/pull/608), предыдущий проверенный HEAD `8da47cca39adfda0b46955b2776717b67f4d39ec`. Актуальный HEAD проверять через PR.
- Текущая задача: C3, консолидация GitHub; сначала канонические знания и профильная документация, STATUS/JOURNAL, затем проверка CI/истории и отдельно разрешённый Merge; только после этого обновлять настройки, память и вложения GPT/Kimi.
- Ограничения: [KDR](kimi/KIMI_DEFECTS_AND_REMEDIATION_REGISTER.md), обязательные evidence gaps и финальная проверка остаются. Точная экономия квоты не доказана. Настройки Kimi не изменены. INSTALLED/LIVE сейчас не проверялись.
- C3.1: общий source audit/HANDOFF подготовлены; #609 MERGED, предыдущий #608 HEAD CC docs/Main Admission PASS, R7 SKIPPED. 29 зеркальных копий / 553869 bytes проверены; запрет удаления сохраняется.
- C3.2: все три профильных HANDOFF получены; original unified diffs отсутствуют. Координатор реконструировал V20/CC STATUS/JOURNAL, V20 AGENTS/Start Here/COC, CC diagnostics и TRL methodology/Operating Cycle/card/Start Here/STATUS/Journal. Предыдущий коммит 86a5731 CI CC docs/Main Admission PASS; текущий 8da47cc требует шести дополнительных exact CI paths. Профильный перенос подготовлен, окончательное покрытие и fallback не приняты.
- Mirrors: 29/29 bytes соответствуют MANIFEST; 25/29 текущим canonical blobs, 4/29 TRL — прежнему accepted MAIN (явно pinned historical fallback). 553869 bytes. Ничего не удалено, установленный Skill не отключён.
- Следующий шаг: общий routing/паспорта и COC/KDR актуализировать, проверить потребителей, подготовить воспроизводимый canonical-path export и единый точный CI scope, отдельно согласовать удаление и Merge. Решение о Skill-only запрете ML отдельно; исследовательские расчёты не запускать.

Поддерживай краткий актуальный снимок, а историю — в Journal. Записи не передают полномочия.
