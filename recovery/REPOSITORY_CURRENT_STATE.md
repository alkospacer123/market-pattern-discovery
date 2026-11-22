> **LATEST GITHUB DECISION 22.11.2026 (после этого исторического среза):** `main=bb8c46c1db89ca2b5311f22c755bb4e51ce8f7d6` после #587 и #588, оба MERGED; #580/#581 CLOSED WITHOUT MERGE, ветки сохранены. Исторический H1 `audit_only` оставлен: удаляющий [#590](https://github.com/alkospacer123/market-pattern-discovery/pull/590) BLOCKED реальными offline зависимостями (два H1 файла), не merged. Стадия I завершена **с сохранением доказанно нужных файлов**, [акт приёмки](R7_STAGE_I_FINAL_ACCEPTANCE_20261122.md). Kimi #589 готовится, фактические Kimi Chat/Code access/exam не доказаны, GitHub ≠ Intel LIVE или cold restore. Нижние таблицы — исторический предыдущий checkpoint, не сегодняшняя PR telemetry.

# GitHub — проверенное состояние после R7 (22.11.2026)

**SOURCE OF TRUTH: GitHub API после Merge.** Проверенный `market-pattern-discovery/main` = `4f118ee1cdeced15406136401faabe4fdc3bb847`; commit родителей `a28f4e06c8c898822c62d516a1a2cf617e22ad29` и `02790ca461afc131f5e480a1dd3f4d0cf35a1283`; итоговый Git tree `3e6139db1387b060fbebc829969eab93c0efa382` **совпадает** с прошедшим CI деревом кандидата #586. Это GitHub-срез, не installed/LIVE и не автономный Recovery.

| Область | Подтверждение |
| --- | --- |
| #583 | Ранее merged: 11 594 исторических A/B/C+BBW Git paths удалены из рабочего дерева; original Git history сохранена |
| [#585](https://github.com/alkospacer123/market-pattern-discovery/pull/585) | MERGED, канонические README/AGENTS, три паспорта, Git main `a28f4e06…` |
| [#586](https://github.com/alkospacer123/market-pattern-discovery/pull/586) | MERGED обычным merge commit `4f118ee1cdeced15406136401faabe4fdc3bb847`; **233 удалено / 6 изменено / 4 добавлено**; runtime шести проектных поддеревьев без изменений |
| [R7 CI](https://github.com/alkospacer123/market-pattern-discovery/actions/runs/44993087919) | 7/7 SUCCESS на точном HEAD `02790ca4…`, не эквивалент текущему LIVE |
| [CC03 Windows-native](https://github.com/alkospacer123/market-pattern-discovery/actions/runs/44993087915) | SUCCESS: 757 PASS/15 designated SKIP, 15/15 non-scope gates; frozen historical scope-audit **EXPECTED FAIL**, не объявлять его PASS |
| [Main Admission](https://github.com/alkospacer123/market-pattern-discovery/actions/runs/44993087924) | SUCCESS на точном HEAD #586 |
| Метаданные | 530 eligible, 527 SHA/UTF-8 verified, 3 >2MB не сканированы; 302 historical literal references, преимущественно provenance |
| Archive refs | `archive/pre-r7-cleanup=f15d565755b996252081ed49ed5a094ee1e8d820`; `archive/pre-root-legacy-20261122=09bca5641cb5bb367e84505ebfc6f8c7f35e2620`; обе защищены Ruleset #27793383 active, без bypass |
| Защищённые каталоги | `V20_TradingSystem_M15/`, `ControlCenter/`, `TradingResearchLab/`, `TradingSystemLab/`, `IntradayLab/`, `audit_only/`; Git tree SHA неизменны относительно HEAD #586 |
| Открытые исторические Draft | [#580](https://github.com/alkospacer123/market-pattern-discovery/pull/580) — уникальная карта R088+экзамен; [#581](https://github.com/alkospacer123/market-pattern-discovery/pull/581) — уникальные scanner/checkpoint tools; обе ветки устарели и **не merge as-is** |

## Каталоги и статус

Три активных логических направления: [V20](PROJECT_PASSPORT_V20.md), [Control Center](PROJECT_PASSPORT_CONTROL_CENTER.md), [TRL](PROJECT_PASSPORT_TRL.md). Не путать frozen H1/M15-исследования с исполняемыми LIVE-проектами: `TradingSystemLab.stage8_robot` и `IntradayLab.core` нужны V20. `research_domains.md` в `main` — совместимый исторический указатель; удалённый root legacy доступен по архивному SHA.

## Ограничения

Исторический тест старой платформы: **45 PASS / 1 known pre-existing FAIL**; он сохранён forensic gate, а не исправлен в архиве. Полный replay неизвестных external consumers, всех ZIP/XLSX/CSV и трёх больших metadata не доказан. `market-pattern-archive` — неполный вспомогательный публичный архив и не финальный disaster recovery. Состояние Intel, FINAM, SLTP, ARMED, реальная версия установленного кода и Kimi Code доступ **не проверены этим GitHub-аудитом**.

Старый срез до R7 сохранён в [Git parent #585](https://github.com/alkospacer123/market-pattern-discovery/blob/a28f4e06c8c898822c62d516a1a2cf617e22ad29/recovery/REPOSITORY_CURRENT_STATE.md), чтобы не переписывать provenance.
