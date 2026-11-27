# Trading Systems — Recovery & Migration — рабочий статус

[Roadmap](../ROADMAP.md) · [Kimi](kimi/README.md) · [COC](CRITICAL_OPERATIONS_CONTRACT.md) · [Журнал](JOURNAL.md) · [Общие правила](../AGENTS.md)

**27.11.2026 — C3.2 / Draft #608.** I принят; G0–G6/A/B приняты в документированных пределах; C1/C2 завершены. Полный допуск Kimi ещё не получен.

- MAIN `85791944750d096ae7d6a86a0e2f40df8f74d80c`, входной HEAD #608 `e5bc5441816794004be860a574b62b30c042873e`. #611/#612 MERGED. Exact cleanup candidate: 29 зеркал + 5 собственных Skill-файлов, семь README/MANIFEST переходят на canonical routes; исторические оригиналы в Git. Владелец разрешил cleanup и подтвердил сохранение проверенного pre-cleanup export на внешнем SSD.
- Kimi READONLY report: 60/60 export identities; пять Skills не использованы (reported), V20/CC context PASS, TRL/general PARTIAL; 92 missing link targets доступны в local pinned Git objects (reported). Девять обязательных документов включены в новый export (53 current + 16 historical, 69/69 CI byte verification), [artifact](https://github.com/alkospacer123/market-pattern-discovery/actions/runs/45962701886/artifacts/15181199045), SHA256 `3aa88b095b246d42ea591917a8bcb99b3e98b403a0de65432b3c7630d20d7344`. Не полный offline repo или cold restore.
- Действующий кандидат: AGENTS/COC/профильные документы/HANDOFF, исторические Skills не обязательны. Исследовательская методика TRL не меняется. Scope/links/CI exact cleanup должны быть проверены перед отдельным Merge #608. Установленные настройки ИИ ещё не менялись.
- Далее C3.3 — синхронизация чистого MAIN и инструкций/вложений/памяти/Skills/plugins; C3.4 — остаточные обязательные evidence gaps [KDR](kimi/KIMI_DEFECTS_AND_REMEDIATION_REGISTER.md), финальный допуск владельца. Не повторять принятые экзамены. Точная экономия квоты не доказана. INSTALLED/LIVE не проверялись.

Поддерживай краткий актуальный снимок, историю — в Journal. Записи не передают полномочия.
