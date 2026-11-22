# GPT/Codex и Kimi Chat/Code — безопасное продолжение работы

**Иерархия 21.11.2026:** [корневой AGENTS](../AGENTS.md) → [README](../README.md) → [GitHub snapshot](REPOSITORY_CURRENT_STATE.md) → паспорт нужного проекта.

1. Определить один проект: [V20](PROJECT_PASSPORT_V20.md), [CC](PROJECT_PASSPORT_CONTROL_CENTER.md), [TRL](PROJECT_PASSPORT_TRL.md). Читать замороженный релиз/closeout и первоисточники.
2. Проверять актуальный main SHA, версии исходников, датированный installed evidence, тесты и реальные ограничения; `MAIN ≠ INSTALLED ≠ LIVE ≠ RESEARCH ≠ ARCHIVE`. Нет свидетельства — `UNKNOWN`.
3. Выполнять безопасные offline проверки в отдельной ветке. Любая правка — diff, SHA, CI, безопасность, review и только операторский Merge. Не использовать FINAM/DPAPI и реальные задачи Intel.
4. Kimi Chat не означает подключённый Kimi Code. Экзамен: найти правильный исходник/девять патчей V20, CC-07/CC-08, TRL R097, проверить offline тесты, объяснить 2025 не-TRUE-OOS, подготовить PR и handoff GPT↔Kimi.
5. Хранить доказательства старых исследований H1/M15; не удалять их из-за возраста. Старый общий research contract 2025 не действует для V20/TRL. Не объявлять старые PF независимым OOS.
6. Независимый backup и cold restore — только после завершения Kimi/фиксов и с фактической автономной проверкой вне Intel/GitHub/ИИ.
