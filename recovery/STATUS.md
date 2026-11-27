# Trading Systems — Recovery & Migration — рабочий статус

[Roadmap](../ROADMAP.md) · [Kimi](kimi/README.md) · [COC](CRITICAL_OPERATIONS_CONTRACT.md) · [Журнал](JOURNAL.md) · [Общие правила](../AGENTS.md)

**27.11.2026 — GPT / GitHub documentation, Draft #608.** I принят; A/B приняты в ограниченном объёме; C1 audit complete; C2 closed by owner. C3 открыт, полный допуск Kimi не получен.

- MAIN при сверке `807d765fab2eb923f4b745caeafa11a27ef6fc53`; [Draft #608](https://github.com/alkospacer123/market-pattern-discovery/pull/608), входной HEAD `8d5ac184eb9ea74770b3a9c3afea9e9204bb7240`. #610 MERGED; #608 на входном HEAD CC docs/Main Admission SUCCESS, R7 SKIPPED. Не переносить CI на новый HEAD.
- Решение владельца: целевая конфигурация без пяти собственных активных Skills; сохранять уникальные требования в существующих канонических документах, без дублирования и новых экзаменов. Перенос оставшихся требований подготовлен: общий audit, полный HANDOFF, профильные V20/CC/TRL требования. Старый ML-запрет сохранён в прежнем scope, не новая исследовательская политика. Покрытие/fallback ещё не приняты.
- 29/29 mirror bytes сохранены (18 current, 11 historical). Kimi READONLY по экспортному HEAD `143dd141aa6566a5fd119b8804e5dfb9d6cbba0d`: 60/60 identities PASS, пять Skills не использованы (reported), V20/CC context PASS, TRL/general PARTIAL; 92 missing link targets доступны в local pinned Git object DB (reported), checkout HEAD иной. GPT подтвердил 9 обязательных source paths/blobs в Draft. Компактный ZIP не самодостаточный; final export включает эти 9 путей и verified pinned Git fallback, не cold restore. Избыточная вставка WF/TRUE OOS/replay из прежнего Skill отменена по замечанию владельца: восстановлена согласованная методология TRL до этой вставки, без новых обязательных этапов; покрытие актуальных требований и конечная приёмка остаются открыты. До отдельного разрешения никаких удалений, отключения, Merge или изменения настроек.
- Профильные HANDOFF получены, original diffs отсутствовали; реконструкция и предыдущие проверки — [Journal](JOURNAL.md). [KDR](kimi/KIMI_DEFECTS_AND_REMEDIATION_REGISTER.md) и обязательные evidence gaps сохраняются. Точная экономия квоты не доказана. INSTALLED/LIVE не проверялись.

Поддерживай краткий актуальный снимок, историю — в Journal. Записи не передают полномочия.
